#!/usr/bin/env python3
"""Rev A.2-faser. Kör: python3 phases.py <fas>  — en fas per process (pcbnew-regeln).
Delete-faser och build-faser separata. Alla add går genom kollisionsassert."""
import sys
sys.path.insert(0, "/tmp/claude-1000/-home-gnu-claude-power-kicad/05b5c210-c31e-46bb-98d1-43a926853f28/scratchpad")
import rt, math

def near(x, y, px, py, tol=0.06):
    return math.hypot(x-px, y-py) < tol

def del_items(b, netn, pred):
    doomed = []
    for t in b.GetTracks():
        if t.GetNetname() != netn: continue
        if pred(t): doomed.append(t)
    for t in doomed: b.Remove(t)
    return len(doomed)

def seg_at(b, t, lay=None):
    if t.GetClass() == "PCB_VIA": return None
    if lay and b.GetLayerName(t.GetLayer()) != lay: return None
    s, e = t.GetStart(), t.GetEnd()
    return (rt.mm(s.x), rt.mm(s.y), rt.mm(e.x), rt.mm(e.y))

def poly(m, b, nc, lay, w, pts):
    for i in range(len(pts)-1):
        m.add_seg(b, nc, lay, pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], w)

# ---------------- faser ----------------
def evict_del(b):
    # RST_EXP + VSOL_J: riv allt på In2 (vägg/gren resp diagonal) i EN pass.
    # Behåll: RST F-webb + B-lane + via (37.36,1.06); VSOL F-svans + via (28.36,3.38).
    doomed = [t for t in b.GetTracks()
              if t.GetNetname() in ("RST_EXP", "VSOL_J")
              and t.GetClass() != "PCB_VIA"
              and b.GetLayerName(t.GetLayer()) == "In2.Cu"]
    for t in doomed: b.Remove(t)
    print(f"evict: {len(doomed)} In2-segment borttagna")

def cellp_del(b):
    print("cellp_del:", rt.delete_net_copper(b, "CELL_P"))

def batp_del(b):
    print("batp_del:", rt.delete_net_copper(b, "BAT_P"))

def cell_n(b):
    m = rt.Map(b); nc = rt.netcode(b, "CELL_N")
    # In2-huvudkorridor 1.0 mm: J2.2 -> västände
    poly(m, b, nc, "In2.Cu", 1.0, [(53.3,8.2),(52.4,7.95),(45.3,7.95),(43.9,5.3),(39.9,4.4),(31.9,3.89)])
    # dubbelvior västände
    # en uppdimensionerad via (0.9/0.45) — via2-zonen är full (PROG-B-web, BUCK_EN-In1, D5/SOLAR_P-F)
    m.add_via(b, nc, 31.9, 3.89, dia=0.9, drill=0.45)
    # C3.2-tap på B (originalvägens korridor, breddad)
    m.add_seg(b, nc, "B.Cu", 31.9, 3.89, 31.43, 4.4, 0.4)
    m.add_seg(b, nc, "B.Cu", 31.43, 4.4, 29.58, 4.4, 0.4)
    # F väst: via -> Q1.1. G1/PGC-fickan medger bara 0,2 på mittensegmenten (4 mm flaskhals,
    # dokumenteras: ~10 mΩ, ΔT ~25 °C @1,5 A — mot rev A.1:s 15 mm 0,2 på 0,5oz-In1)
    m.add_seg(b, nc, "F.Cu", 31.9, 3.89, 31.25, 3.2, 0.3)
    m.add_seg(b, nc, "F.Cu", 31.25, 3.2, 30.0, 3.2, 0.2)
    m.add_seg(b, nc, "F.Cu", 30.0, 3.2, 28.38, 4.83, 0.2)
    m.add_seg(b, nc, "F.Cu", 28.38, 4.83, 26.5, 5.4, 0.2)
    m.add_seg(b, nc, "F.Cu", 26.5, 5.4, 25.66, 6.05, 0.3)
    # U3.6-tap
    m.add_seg(b, nc, "F.Cu", 25.66, 6.05, 23.14, 6.05, 0.3)
    comps = rt.net_check(b, "CELL_N")
    assert len(comps) == 1 and len(list(comps.values())[0]) == 4, f"CELL_N: {comps}"
    print("cell_n OK:", comps)

def rst(b):
    m = rt.Map(b); nc = rt.netcode(b, "RST_EXP")
    # Helt på In2 (J7-10 är THT): östlane y18.4 -> östkantvertikal x54.4 (mellan H2/H4)
    # -> canyon y3.3 -> brant diag till gamla vian (37.36,1.06). Inga nya vior.
    poly(m, b, nc, "In2.Cu", 0.2, [(38.86,18.4),(51.6,18.4),(54.45,16.9),(54.45,3.3),(53.0,3.3),(42.4,3.3),(42.0,2.95),(41.2,2.95),(39.8,1.6),(37.75,1.35),(37.36,1.06)])
    comps = rt.net_check(b, "RST_EXP")
    assert len(comps) == 1, f"RST_EXP: {comps}"
    print("rst OK:", comps)

def vsol(b):
    m = rt.Map(b); nc = rt.netcode(b, "VSOL_J")
    # In2: J7-9 (THT når In2 direkt) -> gamla vertikal-alignmenten -> hoppvia (38.2,14.9)
    poly(m, b, nc, "In2.Cu", 0.2, [(36.32,18.4),(36.32,15.3),(37.3,14.95),(38.2,14.9)])
    m.add_via(b, nc, 38.2, 14.9)
    # B: vertikal x38.4 genom C5/R12-glappet ner till (38.3,10.45)
    poly(m, b, nc, "B.Cu", 0.2, [(38.2,14.9),(38.4,14.4),(38.4,10.7),(38.3,10.45)])
    m.add_via(b, nc, 38.3, 10.45)
    # In2: diagonal sydväst, norr om G1-vian, till gamla vian (28.36,3.38) -> F-svans -> JP1.2
    poly(m, b, nc, "In2.Cu", 0.2, [(38.3,10.45),(32.0,5.2),(30.4,4.5),(29.2,4.0),(28.36,3.38)])
    comps = rt.net_check(b, "VSOL_J")
    assert len(comps) == 1, f"VSOL_J: {comps}"
    print("vsol OK:", comps)

def cell_p(b):
    m = rt.Map(b); nc = rt.netcode(b, "CELL_P")
    # In2-korridor 0.5: J2.1 -> dip runt EN_RF1-vian -> västände x29.9
    poly(m, b, nc, "In2.Cu", 0.5, [(53.3,10.2),(52.6,12.05),(41.5,12.05),(40.6,12.9),(39.4,12.9),(38.6,12.05),(29.9,12.05)])
    # transition: In2-stub öster om SCL-väggen -> stor via (0.9/0.45) -> F-ben in i R5.1
    poly(m, b, nc, "In2.Cu", 0.5, [(29.9,12.05),(29.6,13.3),(28.9,14.37)])
    m.add_via(b, nc, 28.9, 14.37, dia=0.9, drill=0.45)
    m.add_seg(b, nc, "F.Cu", 28.9, 14.37, 26.84, 13.2, 0.5)
    # Kelvin-sense: tap i R5.1-padkopparn -> F-lane österut y~13.1 -> v1 (30.7,13.35) -> In1 -> v2 -> pad10
    m.add_seg(b, nc, "F.Cu", 27.6, 13.05, 30.2, 13.3, 0.2)
    m.add_via(b, nc, 30.46, 13.35)
    m.add_seg(b, nc, "F.Cu", 30.2, 13.3, 30.46, 13.35, 0.2)
    poly(m, b, nc, "In1.Cu", 0.2, [(30.46,13.35),(33.5,11.7),(39.0,11.55)])
    # v3: enda sense-vian vid U4 — matar pad8 (öst-gren) OCH pad10 (väst-gren på F)
    m.add_seg(b, nc, "In1.Cu", 39.0, 11.55, 37.7, 13.18, 0.2)
    m.add_via(b, nc, 37.7, 13.18)
    m.add_seg(b, nc, "F.Cu", 37.7, 13.18, 38.2, 13.2, 0.2)
    m.add_seg(b, nc, "F.Cu", 38.2, 13.2, 38.72, 13.2, 0.2)
    poly(m, b, nc, "F.Cu", 0.2, [(37.7,13.18),(37.4,13.3),(36.08,13.3),(36.08,12.2),(38.9,12.2)])
    # R6.1-tap (3 µA): rev A.1:s norrkantsväg återupplivad — In2-gren från korridoren,
    # F-vertikal i D5-gapet, norrkantslane y0.7, gamla vian (27.58,2.6) + gamla B-vägen
    m.add_seg(b, nc, "In2.Cu", 33.3, 12.05, 34.2, 10.35, 0.3)
    m.add_via(b, nc, 34.2, 10.35)
    poly(m, b, nc, "F.Cu", 0.5, [(34.2,10.35),(33.44,9.6),(33.44,1.4),(33.0,0.7)])
    m.add_seg(b, nc, "F.Cu", 33.0, 0.7, 29.55, 0.7, 0.25)
    poly(m, b, nc, "F.Cu", 0.25, [(29.55,0.7),(29.55,2.05),(28.46,2.6),(27.58,2.6)])
    m.add_via(b, nc, 27.58, 2.6)
    poly(m, b, nc, "B.Cu", 0.2, [(27.58,2.6),(26.72,1.73),(26.21,1.73),(25.81,2.13),(25.81,3.15),(24.61,4.4)])
    comps = rt.net_check(b, "CELL_P")
    assert len(comps) == 1 and len(list(comps.values())[0]) == 5, f"CELL_P: {comps}"
    print("cell_p OK:", comps)

def bat_p(b):
    m = rt.Map(b); nc = rt.netcode(b, "BAT_P")
    # R5.2 -> Q2 D-kolumn 0.5
    poly(m, b, nc, "F.Cu", 0.5, [(32.76,13.2),(33.4,12.0),(35.48,10.6),(35.48,8.71)])
    poly(m, b, nc, "F.Cu", 0.5, [(35.48,8.71),(35.48,4.89)])   # längs padkolumnen
    # laddväg R5.2 -> U2.5 0.3 (gamla korridoren + dodge under R5.1; 0,74 A max)
    poly(m, b, nc, "F.Cu", 0.3, [(32.76,13.2),(31.4,14.3),(30.84,15.12),(28.0,15.12)])
    m.add_seg(b, nc, "F.Cu", 28.0, 15.12, 25.4, 15.12, 0.2)   # R5.1-passagen medger bara 0.2
    poly(m, b, nc, "F.Cu", 0.3, [(25.4,15.12),(19.86,15.12)])
    poly(m, b, nc, "F.Cu", 0.2, [(19.86,15.12),(19.05,14.25),(18.05,13.7),(18.0,13.4)])  # knä: MP0-via + D3-pad kniper
    poly(m, b, nc, "F.Cu", 0.25, [(18.0,13.4),(18.0,11.6)])   # D2/D3-kanjonen (0,9 mm bred)
    poly(m, b, nc, "F.Cu", 0.3, [(18.0,11.6),(17.7,10.1),(16.98,9.4)])
    # C2.1-tap: via väster om vägen
    m.add_seg(b, nc, "F.Cu", 17.86, 10.95, 17.3, 11.3, 0.25)
    m.add_via(b, nc, 17.3, 11.3)
    m.add_seg(b, nc, "B.Cu", 17.3, 11.3, 17.05, 12.0, 0.3)
    # sense: R5.2-pad -> norr -> via v4 -> In1 -> via v5 -> F -> pad9 västerifrån (belly)
    # sense: F-stub -> In1-tunnel söder om CELL_P-lanen -> v5 -> F-entré i pad9
    poly(m, b, nc, "F.Cu", 0.2, [(32.76,13.2),(31.5,13.95),(30.86,14.4)])
    m.add_via(b, nc, 30.86, 14.4)
    poly(m, b, nc, "In1.Cu", 0.2, [(30.86,14.4),(36.0,13.9),(36.72,12.78)])
    m.add_via(b, nc, 36.72, 12.75)
    poly(m, b, nc, "F.Cu", 0.2, [(36.72,12.75),(36.85,12.585),(38.75,12.585),(38.85,12.7)])
    comps = rt.net_check(b, "BAT_P")
    assert len(comps) == 1 and len(list(comps.values())[0]) == 8, f"BAT_P: {comps}"
    print("bat_p OK:", comps)

def sys_fix(b):
    m = rt.Map(b); nc = rt.netcode(b, "SYS")
    m.add_seg(b, nc, "F.Cu", 30.52, 6.17, 32.15, 6.3, 0.5)
    m.add_via(b, nc, 32.15, 6.3)
    poly(m, b, nc, "B.Cu", 0.5, [(32.15,6.3),(35.2,5.5),(36.0,5.18)])
    comps = rt.net_check(b, "SYS")
    assert len(comps) == 1, f"SYS: {comps}"
    print("sys OK")

def v3_fix(b):
    m = rt.Map(b); nc = rt.netcode(b, "3V3")
    # bond-via F->B vid buck-ut, ansluter C14/C15-webben (fickan rymmer en 0.6/0.3)
    m.add_seg(b, nc, "F.Cu", 48.1, 6.4, 48.1, 3.55, 0.5)
    m.add_seg(b, nc, "F.Cu", 48.1, 3.55, 48.9, 3.1, 0.5)
    m.add_via(b, nc, 48.9, 3.1)
    m.add_seg(b, nc, "B.Cu", 48.9, 3.1, 49.0, 3.1, 0.4)
    # J7-1-matning: In1 sydlane — 0.25 i slitsen mellan VBUS-väggen (0.5 bred, y16.73)
    # och J7-annuli; breddas till 0.4 öster om väggens slut (x24.5)
    poly(m, b, nc, "In1.Cu", 0.25, [(16.0,18.4),(16.5,17.8),(16.9,17.25),(24.9,17.25)])
    poly(m, b, nc, "In1.Cu", 0.4, [(24.9,17.25),(25.5,17.05),(41.3,17.05),(41.72,16.9)])
    m.add_via(b, nc, 41.72, 16.9)
    m.add_seg(b, nc, "F.Cu", 41.72, 16.9, 42.1, 15.9, 0.4)
    # C12.1 (Cff) blev föräldralös när gamla B-kedjan revs — ny via + F-länk till x48.1-runnet
    m.add_via(b, nc, 45.35, 10.44)
    m.add_seg(b, nc, "B.Cu", 45.35, 10.44, 45.7, 10.44, 0.25)
    poly(m, b, nc, "F.Cu", 0.25, [(45.35,10.44),(45.6,9.6),(47.6,9.6),(48.1,9.55)])
    # R12/R17/R19-gruppen (B-sidans FB/pullup-web) förlorade sin enda via — ny länk
    m.add_via(b, nc, 40.93, 15.89)
    m.add_seg(b, nc, "B.Cu", 40.93, 15.89, 39.67, 14.96, 0.25)
    m.add_seg(b, nc, "F.Cu", 40.93, 15.89, 42.06, 15.95, 0.25)
    comps = rt.net_check(b, "3V3")
    assert len(comps) == 1 and len(list(comps.values())[0]) == 11, f"3V3: {comps}"
    print("3v3 OK")

def gndvia_move(b):
    # flytta stitching-vian (30.1,16.6) som blockerar In1-sydlanen
    n = 0
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND":
            p = t.GetPosition()
            if near(rt.mm(p.x), rt.mm(p.y), 30.1, 16.6, 0.1):
                b.Remove(t); n += 1
    print(f"gndvia_move: {n} borttagen (ersätts i stitchfasen)")

def sys_r6(b):
    # riv SYS:s U5-västmatning på B (blockerar R6-tappen)
    import math
    TGT = [((22.14,12.35),(26.96,12.35)), ((26.96,12.04),(26.96,12.35)), ((28.30,10.70),(26.96,12.04))]
    def near2(p, q): return math.hypot(p[0]-q[0], p[1]-q[1]) < 0.08
    doomed = []
    for t in b.GetTracks():
        if t.GetNetname() != "SYS" or t.GetClass() == "PCB_VIA": continue
        if b.GetLayerName(t.GetLayer()) != "B.Cu": continue
        s, e = t.GetStart(), t.GetEnd()
        a = (rt.mm(s.x), rt.mm(s.y)); c = (rt.mm(e.x), rt.mm(e.y))
        for (p, q) in TGT:
            if (near2(a,p) and near2(c,q)) or (near2(a,q) and near2(c,p)):
                doomed.append(t); break
    assert len(doomed) == 3, f"hittade {len(doomed)} SYS-segment"
    for t in doomed: b.Remove(t)
    print("sys_r6: 3 segment rivna")

def sys_r6b(b):
    m = rt.Map(b); nc = rt.netcode(b, "SYS")
    # ny U5-matning: via öster om PROG-väggen -> In1-slitsen y11.5 -> via -> U5.2
    # östtransition via BEFINTLIG SYS-via (29.6,10.8); In1-slalom mellan PROG/EN/BUCK-vakterna
    poly(m, b, nc, "In1.Cu", 0.2, [(29.6,10.8),(29.2,11.35),(25.5,11.35),(24.9,11.5),(24.43,11.56),(23.82,11.42),(23.15,11.04)])
    m.add_via(b, nc, 23.15, 11.04)
    poly(m, b, nc, "B.Cu", 0.25, [(23.15,11.04),(23.15,12.2),(22.14,12.35)])
    # C8.1 miste sin gamla nod — länka till TP10-padden (SYS-nät)
    poly(m, b, nc, "B.Cu", 0.25, [(27.61,13.0),(28.0,11.6),(28.3,11.15),(28.3,10.7)])
    comps = rt.net_check(b, "SYS")
    assert len(comps) == 1, f"SYS: {comps}"
    print("sys_r6b OK")

def rst2(b):
    # jogga RST-canyonen runt 3V3-bondfickan (x 44-50): riv långsegmentet, ny väg norr om C14/C15
    doomed = []
    for t in b.GetTracks():
        if t.GetNetname() != "RST_EXP" or t.GetClass() == "PCB_VIA": continue
        s, e = t.GetStart(), t.GetEnd()
        pts = {(round(rt.mm(s.x),1), round(rt.mm(s.y),1)), (round(rt.mm(e.x),1), round(rt.mm(e.y),1))}
        if pts == {(53.0,3.3),(42.4,3.3)}: doomed.append(t)
    assert doomed, "hittade inte RST-canyonsegmentet"
    for t in doomed: b.Remove(t)
    print("rst2: canyonsegment rivet")

def rst2b(b):
    m = rt.Map(b); nc = rt.netcode(b, "RST_EXP")
    poly(m, b, nc, "In2.Cu", 0.2, [(53.0,3.3),(49.55,3.3),(49.0,3.85),(49.0,4.85),(45.6,4.85),(45.1,4.35),(45.1,3.5),(44.6,3.2),(42.4,3.3)])
    comps = rt.net_check(b, "RST_EXP")
    assert len(comps) == 1, f"RST_EXP: {comps}"
    print("rst2b OK")

def rf1(b):
    # FB-delarens B-web + C12/C20-fästningen medger ingen alternativ väg utan komponentflytt
    # (rev B-punkt). Återställ rev A.1-vägen verbatim (fanns med DRC 0).
    m = rt.Map(b); nc = rt.netcode(b, "3V3_RF1")
    m.add_seg(b, nc, "F.Cu", 46.6, 4.58, 46.6, 10.34, 0.2)
    m.add_seg(b, nc, "F.Cu", 45.0, 2.98, 46.6, 4.58, 0.5)
    m.add_seg(b, nc, "F.Cu", 45.0, 1.9, 45.0, 2.98, 0.5)
    comps = rt.net_check(b, "3V3_RF1")
    assert len(comps) == 1, f"3V3_RF1: {comps}"
    print("rf1 OK (verbatim-återställd)")

def swstub_del(b):
    import math
    doomed = []
    for t in b.GetTracks():
        if t.GetNetname() != "SW_BK": continue
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            if math.hypot(rt.mm(p.x)-38.93, rt.mm(p.y)-2.28) < 0.1: doomed.append(t)
        else:
            s, e = t.GetStart(), t.GetEnd()
            xs = {round(rt.mm(s.x),1), round(rt.mm(e.x),1)}
            if b.GetLayerName(t.GetLayer()) == "F.Cu" and xs == {42.2, 38.9}: doomed.append(t)
            elif b.GetLayerName(t.GetLayer()) == "B.Cu": doomed.append(t)
    for t in doomed: b.Remove(t)
    print(f"swstub_del: {len(doomed)} objekt rivna")

def swstub_add(b):
    # SNUB/PGB/R16-labyrinten tillåter ingen kortare väg — återställ rev A.1-stubben verbatim
    # (dokumenteras som kvarstående rev B-punkt)
    m = rt.Map(b); nc = rt.netcode(b, "SW_BK")
    m.add_seg(b, nc, "F.Cu", 42.18, 2.28, 38.93, 2.28, 0.5)
    m.add_via(b, nc, 38.93, 2.28)
    m.add_seg(b, nc, "B.Cu", 38.93, 2.28, 39.81, 2.28, 0.5)
    m.add_seg(b, nc, "B.Cu", 39.81, 2.28, 40.0, 2.09, 0.5)
    comps = rt.net_check(b, "SW_BK")
    assert len(comps) == 1, f"SW_BK: {comps}"
    print("swstub_add OK (verbatim-återställd)")

def stitch(b):
    m = rt.Map(b); nc = rt.netcode(b, "GND")
    cands = [(44.0,17.6),(47.5,14.5),(51.0,10.5),(53.5,13.5),(46.5,17.9),(54.6,5.5),
             (50.2,2.5),(43.5,3.9),(24.5,15.8),(28.4,13.6),(30.3,16.3),(26.9,10.9)]
    placed = 0
    for (x, y) in cands:
        if m.via_ok(nc, x, y):
            m.add_via(b, nc, x, y); placed += 1
        else:
            print(f"  hoppar ({x},{y})")
    print(f"stitch: {placed}/{len(cands)} vior placerade")

PHASES = dict(evict_del=evict_del, cellp_del=cellp_del, batp_del=batp_del,
              rf1=rf1, swstub_del=swstub_del, swstub_add=swstub_add, stitch=stitch,
              cell_n=cell_n, rst=rst, vsol=vsol, cell_p=cell_p, bat_p=bat_p,
              sys_fix=sys_fix, v3_fix=v3_fix, gndvia_move=gndvia_move,
              rst2=rst2, rst2b=rst2b, sys_r6=sys_r6, sys_r6b=sys_r6b)

if __name__ == "__main__":
    rt.b_layname = lambda b, t: b.GetLayerName(t.GetLayer())
    ph = sys.argv[1]
    b = rt.load()
    PHASES[ph](b)
    rt.save(b)
    print(f"SPARAT ({ph})")
