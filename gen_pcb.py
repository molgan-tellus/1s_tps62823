#!/usr/bin/env python3
"""Generate power_kicad.kicad_pcb: 55.88x20.32mm, 4-layer, Makerdiary Connect Kit
hole pattern, zoned placement per DESIGN.md. Passives on back (double-sided assembly)."""
import re, sys
import pcbnew
from pcbnew import VECTOR2I_MM as MM

OUT = "/home/gnu/claude/power_kicad/power_kicad.kicad_pcb"
NETFILE = "/tmp/claude-1000/-home-gnu-claude-power-kicad/5116e7c5-9054-4e7f-b100-211dafa61912/scratchpad/net.net"
FPBASE = "/usr/share/kicad/footprints"
W, H = 55.88, 20.32

# ---- parse netlist: ref -> footprint, (ref,pin) -> net ----
txt = open(NETFILE).read()
comp_fp = {}
for m in re.finditer(r'\(comp \(ref "([^"]+)"\).*?\(footprint "([^"]+)"\)', txt, re.S):
    comp_fp[m.group(1)] = m.group(2)
pin_net = {}
netnames = set()
hs = [(m.start(), m.group(1)) for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)', txt)]
for i, (pos, name) in enumerate(hs):
    end = hs[i+1][0] if i+1 < len(hs) else len(txt)
    nm = name.lstrip("/")
    netnames.add(nm)
    for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', txt[pos:end]):
        pin_net[(r, p)] = nm

# ---- placement: ref -> (x, y, rot, side)  side F/B ----
# FIXED: connectors, ICs, buck hot-loop. Movable passives legalized automatically.
FIXED = {"J1","J2","J3","J4","J7","U2","U3","U4","U6","Q1","Q2","Q3","Q5",
         "L1","R5","C10","C11","FB3","FB4","LED1","LED2","D2","D3"}
P = {
 "J1": (4.4, 10.16, 270, "F"),   # USB-C, port mot -X
 "LED1": (8.6, 17.6, 0, "F"), "LED2": (12.2, 17.6, 0, "F"),
 "U2": (14.5, 7.5, 0, "F"),
 "D2": (14.3, 12.7, 0, "F"), "D3": (21.7, 12.7, 0, "F"),
 "J3": (13.0, 1.8, 90, "F"),     # sol: 2 hal, kabel lods
 "J2": (53.3, 10.2, 90, "F"),    # batteri, hoger kortande, kabel ut +X
 "U3": (22.0, 7.0, 0, "F"), "Q1": (26.8, 7.0, 0, "F"),
 "Q2": (33.0, 6.8, 0, "F"),
 "R5": (29.8, 13.2, 0, "F"), "U4": (37.2, 13.2, 0, "F"),
 "C11": (40.0, 3.7, 90, "F"), "C10": (40.0, 7.0, 90, "F"),
 "U6": (42.6, 5.4, 0, "F"), "L1": (46.6, 6.4, 0, "F"),
 "Q3": (43.0, 10.8, 0, "F"), "FB3": (46.6, 11.4, 90, "F"),
 "Q5": (43.0, 15.0, 0, "F"), "FB4": (46.6, 15.4, 90, "F"),
 "J4": (44.5, 1.9, 90, "F"),     # RF1 G RF2 G, slut pa ovre halraden
 "J7": (16.0, 18.4, 90, "F"),
 # ---- baksida (startpunkter, legaliseras) ----
 "R1": (6.5, 2.8, 0, "B"), "R2": (6.5, 17.4, 0, "B"),
 "F1": (10.8, 16.4, 0, "B"), "FB1": (16.5, 16.4, 0, "B"), "D1": (21.4, 16.4, 0, "B"),
 "C1": (12.0, 12.0, 0, "B"), "R3": (12.0, 9.0, 0, "B"), "R4": (15.3, 9.0, 0, "B"),
 "R21": (18.6, 9.0, 0, "B"), "C2": (18.0, 12.0, 0, "B"),
 "R6": (25.5, 4.4, 0, "B"), "C3": (28.8, 4.4, 0, "B"), "R7": (32.1, 4.4, 0, "B"),
 "R8": (26.0, 8.0, 0, "B"),
 "U5": (24.0, 13.0, 0, "B"),     # LDO pa baksidan (latt last)
 "C8": (28.7, 13.0, 0, "B"), "C9": (32.4, 13.0, 0, "B"),
 "D4": (33.0, 8.0, 0, "B"),      # SS54 pa baksidan
 "C6": (30.0, 16.6, 0, "B"), "R9": (33.3, 16.6, 0, "B"), "R10": (36.6, 16.6, 0, "B"),
 "R11": (39.9, 16.6, 0, "B"),
 "C4": (36.2, 11.0, 0, "B"), "C5": (36.2, 14.6, 0, "B"),
 "FB2": (36.0, 4.0, 90, "B"), "R14": (40.0, 7.4, 0, "B"),
 "R12": (39.8, 9.6, 0, "B"), "R13": (43.1, 9.6, 0, "B"), "C12": (46.4, 9.6, 0, "B"),
 "R15": (49.7, 9.6, 0, "B"),
 "R16": (41.0, 2.2, 0, "B"), "C13": (44.3, 2.2, 0, "B"),
 "C14": (47.7, 2.2, 0, "B"), "C15": (51.2, 2.2, 0, "B"), "C16": (51.8, 5.3, 90, "B"),
 "Q4": (44.6, 12.4, 0, "B"), "R17": (40.8, 12.2, 0, "B"), "R18": (41.0, 14.4, 0, "B"),
 "Q6": (44.6, 16.4, 0, "B"), "R19": (40.6, 16.4, 0, "B"), "R20": (48.9, 16.4, 0, "B"),
 "C17": (47.5, 5.9, 0, "B"), "C18": (50.9, 7.4, 0, "B"), "C19": (47.5, 7.9, 0, "B"),
 "C20": (48.0, 12.2, 0, "B"), "C21": (51.3, 13.9, 0, "B"), "C22": (48.0, 14.2, 0, "B"),
}
# back-side keepouts (THT pins from front connectors pierce through)
BACK_KEEPOUT = [(11.5, 0.0, 17.1, 3.2), (43.4, 0.7, 53.2, 3.1),   # J3-hal, J4-rad
                (52.2, 8.1, 54.4, 12.3),                          # J2 pins
                (14.6, 17.6, 40.5, 20.32), (0.0, 4.4, 9.9, 15.9)] # J7 rad, J1 skal

board = pcbnew.CreateEmptyBoard()
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(4)
ds.SetBoardThickness(pcbnew.FromMM(1.0))
try:  # 0.15mm clearance: VSON-8 0.5mm pitch har 0.15mm mellan pads; JLC 4L klarar 0.09
    ds.m_NetSettings.GetDefaultNetclass().SetClearance(pcbnew.FromMM(0.15))
except Exception as e:
    print("netclass clearance not set:", e)

# nets
netinfo = {}
for nm in sorted(netnames):
    ni = pcbnew.NETINFO_ITEM(board, nm)
    board.Add(ni)
    netinfo[nm] = ni

# outline
def edge_rect():
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(MM(*pts[i])); seg.SetEnd(MM(*pts[(i+1) % 4]))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)
edge_rect()

# mounting holes (Makerdiary pattern): NPTH 1.4mm, no courtyard
for hn, (hx, hy) in enumerate([(1.5, 1.26), (1.5, 19.06), (54.38, 1.26), (54.38, 19.06)], 1):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(f"H{hn}")
    fp.SetPosition(MM(hx, hy))
    pad = pcbnew.PAD(fp)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.4), pcbnew.FromMM(1.4)))
    pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.4), pcbnew.FromMM(1.4)))
    pad.SetPosition(MM(hx, hy))
    pad.SetLayerSet(pad.UnplatedHoleMask())
    fp.Add(pad)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    board.Add(fp)

# footprints
missing = []
for ref, (x, y, rot, side) in P.items():
    if ref not in comp_fp:
        missing.append(ref); continue
    lib, name = comp_fp[ref].split(":")
    fp = pcbnew.FootprintLoad(f"{FPBASE}/{lib}.pretty", name)
    if fp is None:
        missing.append(f"{ref}:{comp_fp[ref]}"); continue
    fp.SetReference(ref)
    fp.SetValue("")
    board.Add(fp)
    if side == "B":
        fp.Flip(MM(x, y), False)
    fp.SetPosition(MM(x, y))
    fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        key = (ref, pad.GetNumber())
        if key in pin_net:
            pad.SetNet(netinfo[pin_net[key]])
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.6), pcbnew.FromMM(0.6)))
    fp.Reference().SetTextThickness(pcbnew.FromMM(0.1))
if missing:
    print("MISSING:", missing); sys.exit(1)

# check all netlist comps placed
unplaced = set(comp_fp) - set(P)
if unplaced:
    print("UNPLACED:", sorted(unplaced)); sys.exit(1)

# ---- legalizer: push movable parts apart until no courtyard overlaps ----
GAP = 0.3   # required courtyard gap, mm
def boxes():
    out = {}
    for fp in board.GetFootprints():
        r = fp.GetReference()
        if r not in P: continue
        side = P[r][3]
        lyr = pcbnew.F_CrtYd if side == "F" else pcbnew.B_CrtYd
        bb = fp.GetCourtyard(lyr).BBox()
        if bb.GetWidth() == 0: bb = fp.GetBoundingBox(False)
        out[r] = [bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6, side]
    return out
def overlap(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0]) + GAP
    oy = min(a[3], b[3]) - max(a[1], b[1]) + GAP
    return (ox, oy) if (ox > 0 and oy > 0) else None
fps = {fp.GetReference(): fp for fp in board.GetFootprints() if fp.GetReference() in P}
import random
random.seed(1)
for it in range(400):
    bx = boxes()
    moved = False
    refs = sorted(bx)
    for i, ra in enumerate(refs):
        for rb in refs[i+1:]:
            a, b = bx[ra], bx[rb]
            if a[4] != b[4]: continue
            ov = overlap(a, b)
            if not ov: continue
            ox, oy = ov
            # push along axis of least overlap; move the movable one(s)
            mv = [r for r in (ra, rb) if r not in FIXED]
            if not mv: print(f"FIXED-FIXED overlap {ra}/{rb} {ox:.2f}x{oy:.2f}"); continue
            for r in mv:
                other = b if r == ra else a
                mine = a if r == ra else b
                fp = fps[r]
                pos = fp.GetPosition()
                dx = dy = 0.0
                if ox < oy:
                    dx = (ox/len(mv) + 0.02) * (1 if (mine[0]+mine[2]) > (other[0]+other[2]) else -1)
                else:
                    dy = (oy/len(mv) + 0.02) * (1 if (mine[1]+mine[3]) > (other[1]+other[3]) else -1)
                fp.SetPosition(pcbnew.VECTOR2I(pos.x + pcbnew.FromMM(dx), pos.y + pcbnew.FromMM(dy)))
                moved = True
    # clamp inside board and out of back keepouts
    bx = boxes()
    for r, bb in bx.items():
        if r in FIXED: continue
        fp = fps[r]
        pos = fp.GetPosition()
        dx = dy = 0.0
        if bb[0] < 0.9: dx = 0.9 - bb[0]
        if bb[2] > W-0.9: dx = (W-0.9) - bb[2]
        if bb[1] < 0.9: dy = 0.9 - bb[1]
        if bb[3] > H-0.9: dy = (H-0.9) - bb[3]
        if bb[4] == "B":
            for kx0, ky0, kx1, ky1 in BACK_KEEPOUT:
                ox = min(bb[2], kx1) - max(bb[0], kx0)
                oy = min(bb[3], ky1) - max(bb[1], ky0)
                if ox > 0 and oy > 0:
                    if ox < oy: dx += ox * (1 if (bb[0]+bb[2]) > (kx0+kx1) else -1)
                    else: dy += oy * (1 if (bb[1]+bb[3]) > (ky0+ky1) else -1)
        if dx or dy:
            fp.SetPosition(pcbnew.VECTOR2I(pos.x + pcbnew.FromMM(dx), pos.y + pcbnew.FromMM(dy)))
            moved = True
    if not moved:
        print(f"legalized after {it} iterations"); break
else:
    print("WARNING: legalizer hit iteration limit")
# final overlap report
bx = boxes()
bad = 0
refs = sorted(bx)
for i, ra in enumerate(refs):
    for rb in refs[i+1:]:
        if bx[ra][4] != bx[rb][4]: continue
        if overlap(bx[ra], bx[rb]):
            print("STILL OVERLAP:", ra, rb); bad += 1
print(f"remaining overlaps: {bad}")

# GND zones: In1 (solid plan), In2, F, B
def add_zone(layer, prio):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(netinfo["GND"])
    pts = [(-0.5, -0.5), (W+0.5, -0.5), (W+0.5, H+0.5), (-0.5, H+0.5)]
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for px, py in pts: chain.Append(MM(px, py))
    chain.SetClosed(True)
    z.Outline().AddOutline(chain)
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(pcbnew.FromMM(0.25))
    z.SetMinThickness(pcbnew.FromMM(0.2))
    z.SetThermalReliefGap(pcbnew.FromMM(0.3))
    z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    board.Add(z)
    return z
zin1 = add_zone(pcbnew.In1_Cu, 0)
zin1.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
add_zone(pcbnew.In2_Cu, 0)
zf = add_zone(pcbnew.F_Cu, 0)
zf.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
add_zone(pcbnew.B_Cu, 0)

# ---- halrader: endast hal, ingen montering + silkscreen-funktionstext ----
for r in ("J3", "J4", "J7"):
    f = fps[r]
    f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
def silk(txt, x, y, ang=0, size=0.55):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetPosition(MM(x, y)); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
    t.SetTextThickness(pcbnew.FromMM(0.11)); t.SetTextAngleDegrees(ang)
    board.Add(t)
J7_LBL = ["3V3", "GND", "3VM", "GND", "SDA", "SCL", "ALR", "EN", "RF1", "RF2"]
for i, lbl in enumerate(J7_LBL):
    silk(lbl, 16.0 + 2.54*i, 16.9, 90, 0.5)
silk("S+", 13.0, 3.2); silk("G", 15.54, 3.2); silk("SOL", 14.3, 0.7)
for i, lbl in enumerate(["R1", "G", "R2", "G"]):
    silk(lbl, 44.5 + 2.54*i, 0.75, 0, 0.45)
silk("BATT", 52.6, 15.6); silk("USB-C", 4.4, 17.0)

# TP4056 EP thermal vias (EP=GND) + LDO area
def gnd_via(x, y, drill=0.3, dia=0.6):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(MM(x, y))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetWidth(pcbnew.FromMM(dia))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(netinfo["GND"])
    board.Add(v)
ux, uy = P["U2"][0], P["U2"][1]
for dx in (-0.7, 0.7):
    for dy in (-0.7, 0.7):
        gnd_via(ux + dx, uy + dy)

# save, reload (attaches project context), then fill — ZONE_FILLER segfaults headless otherwise
board.Save(OUT)
b2 = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(b2)
filler.Fill(b2.Zones())
b2.Save(OUT)
print(f"OK: saved {OUT}, {len(P)} footprints placed, zones filled")
