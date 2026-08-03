#!/usr/bin/env python3
"""Validerad omdragning: kollisionstestar varje segment mot all geometri innan det laggs."""
import math, pcbnew
from pcbnew import VECTOR2I_MM as MM

BRD = "/home/gnu/claude/power_kicad/power_kicad.kicad_pcb"
b = pcbnew.LoadBoard(BRD)
CLR = 0.13

# ---- hinderkarta ----
tracks = []   # (x1,y1,x2,y2,halfw,layer,net)
vias = []     # (x,y,r,net)  - alla kopparlager
pads_smd = [] # (x,y,hx,hy,layer,net)
pads_tht = [] # (x,y,r,net)
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        vias.append((p.x/1e6, p.y/1e6, t.GetWidth()/2e6, n))
    else:
        s, e = t.GetStart(), t.GetEnd()
        tracks.append((s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6, t.GetWidth()/2e6, t.GetLayer(), n))
for fp in b.GetFootprints():
    for p in fp.Pads():
        pos = p.GetPosition(); n = p.GetNetname()
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            pads_tht.append((pos.x/1e6, pos.y/1e6, max(p.GetSize().x, p.GetSize().y)/2e6, n))
        else:
            lyr = pcbnew.F_Cu if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_Cu
            pads_smd.append((pos.x/1e6, pos.y/1e6, p.GetSize().x/2e6, p.GetSize().y/2e6, lyr, n))

def segdist(px,py,x1,y1,x2,y2):
    dx,dy = x2-x1,y2-y1; L2 = dx*dx+dy*dy
    if L2 == 0: return math.hypot(px-x1,py-y1)
    t = max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L2))
    return math.hypot(px-(x1+t*dx), py-(y1+t*dy))
def segseg(a,bseg):
    (x1,y1,x2,y2) = a; (x3,y3,x4,y4) = bseg
    d = min(segdist(x1,y1,x3,y3,x4,y4), segdist(x2,y2,x3,y3,x4,y4),
            segdist(x3,y3,x1,y1,x2,y2), segdist(x4,y4,x1,y1,x2,y2))
    def ccw(ax,ay,bx,by,cx,cy): return (cy-ay)*(bx-ax) > (by-ay)*(cx-ax)
    inter = (ccw(x1,y1,x3,y3,x4,y4) != ccw(x2,y2,x3,y3,x4,y4)) and \
            (ccw(x1,y1,x2,y2,x3,y3) != ccw(x1,y1,x2,y2,x4,y4))
    return 0.0 if inter else d

def seg_ok(x1,y1,x2,y2,layer,w,net,verbose=False):
    hw = w/2
    if not (0.5 < min(x1,x2) and max(x1,x2) < 55.4 and 0.5 < min(y1,y2) and max(y1,y2) < 19.8):
        if verbose: print("   utanfor brada")
        return False
    for (tx1,ty1,tx2,ty2,thw,tl,tn) in tracks:
        if tl != layer or tn == net: continue
        if segseg((x1,y1,x2,y2),(tx1,ty1,tx2,ty2)) < hw+thw+CLR:
            if verbose: print(f"   spar {tn} ({tx1:.1f},{ty1:.1f})-({tx2:.1f},{ty2:.1f})")
            return False
    for (vx,vy,vr,vn) in vias:
        if vn == net: continue
        if segdist(vx,vy,x1,y1,x2,y2) < hw+vr+CLR:
            if verbose: print(f"   via {vn} ({vx:.1f},{vy:.1f})")
            return False
    for (px,py,pr,pn) in pads_tht:
        if pn == net: continue
        if segdist(px,py,x1,y1,x2,y2) < hw+pr+CLR:
            if verbose: print(f"   THT {pn} ({px:.1f},{py:.1f})")
            return False
    for (px,py,phx,phy,pl,pn) in pads_smd:
        if pl != layer or pn == net: continue
        if segdist(px,py,x1,y1,x2,y2) < hw+max(phx,phy)+CLR:
            # grov men saker (cirkular approx)
            if verbose: print(f"   pad {pn} ({px:.1f},{py:.1f})")
            return False
    return True

def via_ok(x,y,net,r=0.25):
    for (vx,vy,vr,vn) in vias:
        if math.hypot(x-vx,y-vy) < r+vr+CLR and vn != net: return False
    for (px,py,pr,pn) in pads_tht:
        if pn != net and math.hypot(x-px,y-py) < r+pr+0.3: return False
    for lyr in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        for (tx1,ty1,tx2,ty2,thw,tl,tn) in tracks:
            if tl != lyr or tn == net: continue
            if segdist(x,y,tx1,ty1,tx2,ty2) < r+thw+CLR: return False
    for (px,py,phx,phy,pl,pn) in pads_smd:
        if pn != net and math.hypot(x-px,y-py) < r+max(phx,phy)+CLR: return False
    return True

added = []
def tr(x1,y1,x2,y2,net,layer,w=0.2):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(MM(x1,y1)); t.SetEnd(MM(x2,y2))
    t.SetLayer(layer); t.SetWidth(pcbnew.FromMM(w)); t.SetNet(b.FindNet(net)); b.Add(t)
    tracks.append((x1,y1,x2,y2,w/2,layer,net)); added.append(net)
def via(x,y,net):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(MM(x,y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3)); v.SetNet(b.FindNet(net)); b.Add(v)
    vias.append((x,y,0.25,net))
F, I1, I2, B_ = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu

def find_lane(x1, x2, ys, layer, net, w=0.2):
    for y in ys:
        if seg_ok(x1,y,x2,y,layer,w,net): return y
    return None

# ============ FIXAR ============
report = []

# 1) PROG: saknad lank (14.45,7.6)-(14.45,5.72)
if seg_ok(14.45,7.6, 14.45,5.72, B_, 0.2, "PROG"):
    tr(14.45,7.6, 14.45,5.72, "PROG", B_); report.append("PROG-lank OK")
else:
    seg_ok(14.45,7.6, 14.45,5.72, B_, 0.2, "PROG", True); report.append("PROG-lank MISSLYCKAD")

# 2) PROG ostgren: vertikalen x38.2 korsar VIN_BK y2.28 - hitta fri x
done = False
for xv in (39.5, 39.3, 39.7, 37.6, 37.3):
    if seg_ok(29.13,0.65, xv,0.65, B_, 0.2, "PROG") and seg_ok(xv,0.65, xv,4.2, B_, 0.2, "PROG") and seg_ok(xv,4.2, 38.53,4.2, B_, 0.2, "PROG"):
        # ta bort gamla x38.2-benen
        for t in list(b.GetTracks()):
            if t.GetClass()=="PCB_TRACK" and t.GetNetname()=="PROG":
                s,e = t.GetStart(), t.GetEnd()
                pts = {(round(s.x/1e6,2),round(s.y/1e6,2)),(round(e.x/1e6,2),round(e.y/1e6,2))}
                if any(abs(px-38.2)<0.05 for px,py in pts): b.Remove(t)
        tr(29.13,0.65, xv,0.65, "PROG", B_); tr(xv,0.65, xv,4.2, "PROG", B_); tr(xv,4.2, 38.53,4.2, "PROG", B_)
        report.append(f"PROG-ost via x{xv} OK"); done = True; break
if not done: report.append("PROG-ost MISSLYCKAD")

# 3) MP0-vertikal korsar LED1K: hitta fri x for vertikalen y13.05->6.3
done = False
for xv in (10.5, 10.3, 9.9, 9.7, 10.7):
    if seg_ok(xv,13.05, xv,6.3, B_, 0.2, "MP0") and seg_ok(10.15,13.05, xv,13.05, B_, 0.2, "MP0") and seg_ok(xv,6.3, 12.8,6.3, B_, 0.2, "MP0"):
        for t in list(b.GetTracks()):
            if t.GetClass()=="PCB_TRACK" and t.GetNetname()=="MP0":
                s,e = t.GetStart(), t.GetEnd()
                pts = {(round(s.x/1e6,2),round(s.y/1e6,2)),(round(e.x/1e6,2),round(e.y/1e6,2))}
                if (10.15,13.05) in pts and (10.15,6.3) in pts: b.Remove(t)
                elif (10.15,6.3) in pts and (12.8,6.3) in pts: b.Remove(t)
        tr(10.15,13.05, xv,13.05, "MP0", B_); tr(xv,13.05, xv,6.3, "MP0", B_); tr(xv,6.3, 12.8,6.3, "MP0", B_)
        report.append(f"MP0-vertikal x{xv} OK"); done = True; break
if not done: report.append("MP0 MISSLYCKAD (provar In-lager senare)")

# 4) MP2 In2-lane korsar CHG_VIN-In2: hitta fri y for horisontalen x7.3->16.2
for t in list(b.GetTracks()):
    if t.GetClass()=="PCB_TRACK" and t.GetNetname()=="MP2" and t.GetLayer()==I2:
        b.Remove(t)
tracks = [tt for tt in tracks if not (tt[6]=="MP2" and tt[5]==I2)]
done = False
for y in (8.6, 8.9, 8.3, 9.2, 6.3, 5.9):
    if seg_ok(7.3,2.0, 7.3,y, I2, 0.2, "MP2") and seg_ok(7.3,y, 16.2,y, I2, 0.2, "MP2") and seg_ok(16.2,y, 16.2,7.6, I2, 0.2, "MP2"):
        tr(7.3,2.0, 7.3,y, "MP2", I2); tr(7.3,y, 16.2,y, "MP2", I2); tr(16.2,y, 16.2,7.6, "MP2", I2)
        report.append(f"MP2-In2 lane y{y} OK"); done = True; break
if not done: report.append("MP2-In2 MISSLYCKAD")

# 5) VBS In2-diagonal korsar VM-via (22.0,7.0): bryt runt
for t in list(b.GetTracks()):
    if t.GetClass()=="PCB_TRACK" and t.GetNetname()=="VBS" and t.GetLayer()==I2:
        b.Remove(t)
tracks = [tt for tt in tracks if not (tt[6]=="VBS" and tt[5]==I2)]
done = False
for (mx,my) in ((22.8,8.2),(23.3,8.8),(21.5,6.0),(24.0,9.5)):
    if seg_ok(15.3,14.6, mx,my, I2, 0.2, "VBS") and seg_ok(mx,my, 26.82,1.9, I2, 0.2, "VBS"):
        tr(15.3,14.6, mx,my, "VBS", I2); tr(mx,my, 26.82,1.9, "VBS", I2)
        report.append(f"VBS-In2 via ({mx},{my}) OK"); done = True; break
if not done: report.append("VBS-In2 MISSLYCKAD")

b.Save(BRD)
print("\n".join(report))
