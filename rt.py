#!/usr/bin/env python3
"""Routing-toolkit för power_kicad rev A.2-kirurgin.
Hinderkarta + kollisionsvaliderad segment/via-placering + nätgraf-verifiering.
Används som modul: import rt; b = rt.load(); ...; rt.save(b)
Alla koordinater i mm. Clearance 0.13 (netclass 0.127 + marginal), hål-hål 0.5."""
import pcbnew, math, collections

PCB = "/home/gnu/claude/power_kicad/full_tps62823/power_kicad.kicad_pcb"
CLR = 0.13
HOLE_CLR = 0.5
mm = pcbnew.ToMM
MM = pcbnew.FromMM
LAYERS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}

def load():
    return pcbnew.LoadBoard(PCB)

def save(b):
    pcbnew.SaveBoard(PCB, b)

# ---------- geometri ----------
def seg_pt_dist(x1, y1, x2, y2, px, py):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx*dx + dy*dy
    if L2 == 0: return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1)*dx + (py - y1)*dy) / L2))
    return math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))

def seg_rect_dist(x1, y1, x2, y2, cx, cy, hx, hy):
    """Avstånd segment -> axeljusterad rektangel (0 om de skär)."""
    l, r, t, b_ = cx-hx, cx+hx, cy-hy, cy+hy
    def inside(px, py): return l <= px <= r and t <= py <= b_
    if inside(x1, y1) or inside(x2, y2): return 0.0
    edges = [(l,t,r,t),(r,t,r,b_),(r,b_,l,b_),(l,b_,l,t)]
    return min(seg_seg_dist((x1,y1,x2,y2), e) for e in edges)

def seg_seg_dist(a, b_):
    (x1,y1,x2,y2), (x3,y3,x4,y4) = a, b_
    def ccw(ax,ay,bx,by,cx,cy): return (by-ay)*(cx-ax) - (bx-ax)*(cy-ay)
    d1 = ccw(x3,y3,x4,y4,x1,y1); d2 = ccw(x3,y3,x4,y4,x2,y2)
    d3 = ccw(x1,y1,x2,y2,x3,y3); d4 = ccw(x1,y1,x2,y2,x4,y4)
    if ((d1>0)!=(d2>0)) and ((d3>0)!=(d4>0)): return 0.0
    return min(seg_pt_dist(x1,y1,x2,y2,x3,y3), seg_pt_dist(x1,y1,x2,y2,x4,y4),
               seg_pt_dist(x3,y3,x4,y4,x1,y1), seg_pt_dist(x3,y3,x4,y4,x2,y2))

# ---------- hinderkarta ----------
class Map:
    def __init__(self, b):
        self.b = b
        self.items = []   # (lay|'HOLE', netcode, x1,y1,x2,y2, halfwidth, tag)
        self.holes = []   # (x, y, r, tag)
        for t in b.GetTracks():
            n = t.GetNetCode()
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition(); x, y = mm(p.x), mm(p.y)
                r = mm(t.GetWidth(pcbnew.F_Cu))/2
                for lay in LAYERS:
                    self.items.append((lay, n, x, y, x, y, r, f"via:{t.GetNetname()}"))
                self.holes.append((x, y, mm(t.GetDrill())/2, f"via:{t.GetNetname()}"))
            else:
                s, e = t.GetStart(), t.GetEnd()
                self.items.append((self.b.GetLayerName(t.GetLayer()), n,
                                   mm(s.x), mm(s.y), mm(e.x), mm(e.y),
                                   mm(t.GetWidth())/2, f"seg:{t.GetNetname()}"))
        self.rects = []   # (lay, netcode, cx, cy, hx, hy, tag) — axeljusterade pad-rektanglar
        for f in b.GetFootprints():
            for p in f.Pads():
                pos = p.GetPosition(); x, y = mm(pos.x), mm(pos.y)
                sz = p.GetSize(pcbnew.F_Cu)
                sx, sy = mm(sz.x), mm(sz.y)
                ang = (p.GetOrientation().AsDegrees() % 180 + 180) % 180
                if 45 <= ang < 135: sx, sy = sy, sx   # 90-graders rotation
                hx, hy = sx/2, sy/2
                tag = f"pad:{f.GetReference()}.{p.GetNumber()}:{p.GetNetname()}"
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    for lay in LAYERS:
                        self.rects.append((lay, p.GetNetCode(), x, y, hx, hy, tag))
                    d = p.GetDrillSize()
                    self.holes.append((x, y, max(mm(d.x), mm(d.y))/2, tag))
                else:
                    lay = "B.Cu" if f.IsFlipped() else "F.Cu"
                    self.rects.append((lay, p.GetNetCode(), x, y, hx, hy, tag))
        bb = b.GetBoardEdgesBoundingBox()
        self.edge = (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))

    def seg_ok(self, netcode, lay, x1, y1, x2, y2, w, verbose=False):
        el, et, er, eb = self.edge
        hw = w/2 + 0.31   # kantclearance
        for (px, py) in ((x1,y1),(x2,y2)):
            if px < el+hw or px > er-hw or py < et+hw or py > eb-hw:
                if verbose: print(f"  KANT ({px},{py})")
                return False
        for it in self.items:
            ilay, inet, ax1, ay1, ax2, ay2, ihw, tag = it
            if ilay != lay or inet == netcode: continue
            d = seg_seg_dist((x1,y1,x2,y2), (ax1,ay1,ax2,ay2))
            if d < w/2 + ihw + CLR:
                if verbose: print(f"  KROCK {tag} d={d:.3f} behov={w/2+ihw+CLR:.3f}")
                return False
        for rc in self.rects:
            rlay, rnet, cx, cy, hx, hy, tag = rc
            if rlay != lay or rnet == netcode: continue
            d = seg_rect_dist(x1, y1, x2, y2, cx, cy, hx, hy)
            if d < w/2 + CLR:
                if verbose: print(f"  PADKROCK {tag} d={d:.3f} behov={w/2+CLR:.3f}")
                return False
        return True

    def via_ok(self, netcode, x, y, dia=0.6, drill=0.3, verbose=False):
        for lay in LAYERS:
            for it in self.items:
                ilay, inet, ax1, ay1, ax2, ay2, ihw, tag = it
                if ilay != lay or inet == netcode: continue
                d = seg_pt_dist(ax1, ay1, ax2, ay2, x, y)
                if d < dia/2 + ihw + CLR:
                    if verbose: print(f"  KROCK {lay} {tag} d={d:.3f}")
                    return False
            for rc in self.rects:
                rlay, rnet, cx, cy, hx, hy, tag = rc
                if rlay != lay or rnet == netcode: continue
                d = seg_rect_dist(x, y, x, y, cx, cy, hx, hy)
                if d < dia/2 + CLR:
                    if verbose: print(f"  PADKROCK {lay} {tag} d={d:.3f}")
                    return False
        for (hx, hy, hr, tag) in self.holes:
            if math.hypot(hx-x, hy-y) < hr + drill/2 + HOLE_CLR:
                if verbose: print(f"  HÅLKROCK {tag}")
                return False
        return True

    def add_seg(self, b, netcode, lay, x1, y1, x2, y2, w):
        assert self.seg_ok(netcode, lay, x1, y1, x2, y2, w, verbose=True), \
            f"seg_ok misslyckades {lay} ({x1},{y1})->({x2},{y2}) w{w}"
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        t.SetWidth(MM(w)); t.SetLayer(LAYERS[lay]); t.SetNetCode(netcode)
        b.Add(t)
        self.items.append((lay, netcode, x1, y1, x2, y2, w/2, "ny"))

    def add_via(self, b, netcode, x, y, dia=0.6, drill=0.3):
        assert self.via_ok(netcode, x, y, dia, drill, verbose=True), f"via_ok misslyckades ({x},{y})"
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(dia)); v.SetDrill(MM(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(netcode)
        b.Add(v)
        for lay in LAYERS:
            self.items.append((lay, netcode, x, y, x, y, dia/2, "nyvia"))
        self.holes.append((x, y, drill/2, "nyvia"))

# ---------- nät-operationer ----------
def netcode(b, name):
    return b.GetNetsByName()[name].GetNetCode()

def delete_net_copper(b, name):
    doomed = [t for t in b.GetTracks() if t.GetNetname() == name]
    for t in doomed: b.Remove(t)
    return len(doomed)

def net_check(b, name):
    """Pads på nätet grupperade i connectivity-komponenter (zoner ej medräknade).
    Rätt svar för icke-GND-nät: EN komponent med alla pads."""
    TOL = 0.06
    segs, vias, pads = [], [], []
    for t in b.GetTracks():
        if t.GetNetname() != name: continue
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); vias.append((mm(p.x), mm(p.y)))
        else:
            s, e = t.GetStart(), t.GetEnd()
            segs.append(((mm(s.x), mm(s.y)), (mm(e.x), mm(e.y)), b.GetLayerName(t.GetLayer())))
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == name:
                pos = p.GetPosition()
                tht = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                lay = None if tht else ("B.Cu" if f.IsFlipped() else "F.Cu")
                r = max(mm(p.GetSize(pcbnew.F_Cu).x), mm(p.GetSize(pcbnew.F_Cu).y))/2
                pads.append((f"{f.GetReference()}.{p.GetNumber()}", mm(pos.x), mm(pos.y), lay, r))
    import math as m
    def near(a, b_, tol=TOL): return m.hypot(a[0]-b_[0], a[1]-b_[1]) < tol
    N = len(segs) + len(pads)   # noder: segment sedan pads
    parent = list(range(N))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def union(i, j): parent[find(i)] = find(j)
    for i in range(len(segs)):
        for j in range(i+1, len(segs)):
            if segs[i][2] != segs[j][2]: continue
            if any(near(a, c) for a in segs[i][:2] for c in segs[j][:2]):
                union(i, j); continue
            # T-korsning/överlapp: ändpunkt PÅ det andra segmentet
            (ax1, ay1), (ax2, ay2), _ = segs[j]
            if any(seg_pt_dist(ax1, ay1, ax2, ay2, e[0], e[1]) < 0.15 for e in segs[i][:2]):
                union(i, j); continue
            (bx1, by1), (bx2, by2), _ = segs[i]
            if any(seg_pt_dist(bx1, by1, bx2, by2, e[0], e[1]) < 0.15 for e in segs[j][:2]):
                union(i, j)
    for (vx, vy) in vias:
        conn = [i for i in range(len(segs)) if any(near((vx,vy), e) for e in segs[i][:2])]
        for a in conn[1:]: union(conn[0], a)
    for k, (pname, px, py, lay, r) in enumerate(pads):
        for i in range(len(segs)):
            if lay is not None and segs[i][2] != lay: continue
            if any(m.hypot(px-e[0], py-e[1]) < r + 0.05 for e in segs[i][:2]):
                union(len(segs)+k, i); continue
            # segment som passerar genom padkopparn
            (sx1, sy1), (sx2, sy2), _ = segs[i]
            if seg_pt_dist(sx1, sy1, sx2, sy2, px, py) < r*0.75:
                union(len(segs)+k, i)
    comp = collections.defaultdict(list)
    for k, (pname, *_ ) in enumerate(pads):
        comp[find(len(segs)+k)].append(pname)
    return dict(comp)
