#!/usr/bin/env python3
"""Textual .kicad_pcb surgery: remove PG_3V3 copper + R15 + my VIN attempts,
clear U6 pad8 net, shift J4 +0.5mm, then dump all copper near U6."""
import re, sys

BRD = "/home/gnu/claude/power_kicad/power_kicad.kicad_pcb"
txt = open(BRD).read()

def find_blocks(s, opener):
    """yield (start, end) of balanced blocks beginning with opener at line start"""
    out = []
    i = 0
    while True:
        i = s.find(opener, i)
        if i < 0: break
        depth = 0
        j = i
        while j < len(s):
            if s[j] == '(': depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    out.append((i, j+1)); break
            j += 1
        i = j
    return out

# net ids
nets = dict(re.findall(r'\(net\s+(\d+)\s+"([^"]+)"\)', txt))
id2name = {k: v for k, v in nets.items()}
name2id = {v: k for k, v in nets.items()}
pg_id = name2id.get("PG_3V3")
vin_id = name2id.get("VIN_BK")
print("PG net id:", pg_id, "VIN id:", vin_id)

remove_spans = []
# 1) PG_3V3 segments + vias
for op in ("\t(segment", "\t(via"):
    for a, b in find_blocks(txt, op):
        blk = txt[a:b]
        if pg_id and re.search(r'\(net %s\)' % pg_id, blk):
            remove_spans.append((a, b))
# 2) mina VIN-forsok: segment med start/end i {(43.14,5.15),(43.7,5.15),(43.7,2.6),(38.93,2.6)}
MYPTS = {"43.14 5.15", "43.7 5.15", "43.7 2.6", "38.93 2.6"}
for a, b in find_blocks(txt, "\t(segment"):
    blk = txt[a:b]
    if vin_id and re.search(r'\(net %s\)' % vin_id, blk):
        pts = re.findall(r'\((?:start|end)\s+([\d.]+ [\d.]+)\)', blk)
        if any(p in MYPTS for p in pts):
            remove_spans.append((a, b))
# 3) R15-footprint
for a, b in find_blocks(txt, "\t(footprint"):
    blk = txt[a:b]
    if '"Reference" "R15"' in blk:
        remove_spans.append((a, b))
# apply removals (sorted desc)
remove_spans = sorted(set(remove_spans), reverse=True)
for a, b in remove_spans:
    # ta med foljande radbrytning
    e = b
    while e < len(txt) and txt[e] in "\n\t": e += 1
    txt = txt[:a] + txt[e:]
print("removed blocks:", len(remove_spans))

# 4) U6 pad8: ta bort natet
for a, b in find_blocks(txt, "\t(footprint"):
    blk = txt[a:b]
    if '"Reference" "U6"' in blk:
        pads = find_blocks(blk, "\t\t(pad")
        for pa, pb in pads:
            pblk = blk[pa:pb]
            if pblk.startswith('\t\t(pad "8"'):
                newp = re.sub(r'\n\t*\(net \d+ "[^"]*"\)', '', pblk)
                blk = blk[:pa] + newp + blk[pb:]
        txt = txt[:a] + blk + txt[b:]
        break
print("U6 pad8 net cleared")

# 5) J4 +0.5mm (footprint at + alla pads foljer med automatiskt, at ar relativ)
for a, b in find_blocks(txt, "\t(footprint"):
    blk = txt[a:b]
    if '"Reference" "J4"' in blk:
        m = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)(\s+[\d.]+)?\)', blk)
        old = m.group(0)
        newat = f"(at {float(m.group(1))+0.5:g} {m.group(2)}{m.group(3) or ''})"
        blk = blk.replace(old, newat, 1)
        txt = txt[:a] + blk + txt[b:]
        print("J4:", old, "->", newat)
        break
# silk R1/G/R2/G +0.5 (gr_text at y<1.5)
for a, b in reversed(find_blocks(txt, "\t(gr_text")):
    blk = txt[a:b]
    m = re.search(r'\(at\s+([\d.]+)\s+(0\.[\d]+|1\.[0-4][\d]*)\s*(\d+)?\)', blk)
    if m and re.search(r'\(gr_text\s+"(R1|R2|G)"', blk):
        newat = f"(at {float(m.group(1))+0.5:g} {m.group(2)}{' '+m.group(3) if m.group(3) else ''})"
        blk2 = blk.replace(m.group(0), newat, 1)
        txt = txt[:a] + blk2 + txt[b:]

open(BRD, "w").write(txt)
print("saved")

# ---- dump copper region x 35-48, y 0-11 ----
print("\n=== KOPPAR x35-48 y0-11 ===")
for a, b in find_blocks(txt, "\t(segment"):
    blk = txt[a:b]
    s = re.search(r'\(start\s+([\d.]+)\s+([\d.]+)\)', blk)
    e = re.search(r'\(end\s+([\d.]+)\s+([\d.]+)\)', blk)
    l = re.search(r'\(layer\s+"([^"]+)"\)', blk)
    n = re.search(r'\(net\s+(\d+)\)', blk)
    w = re.search(r'\(width\s+([\d.]+)\)', blk)
    x1,y1,x2,y2 = float(s.group(1)),float(s.group(2)),float(e.group(1)),float(e.group(2))
    if (35 <= x1 <= 48 or 35 <= x2 <= 48) and (y1 <= 11 or y2 <= 11):
        print(f"SEG {id2name.get(n.group(1),'?'):9s} {l.group(1):7s} ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f}) w{w.group(1)}")
for a, b in find_blocks(txt, "\t(via"):
    blk = txt[a:b]
    p = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)\)', blk)
    n = re.search(r'\(net\s+(\d+)\)', blk)
    x, y = float(p.group(1)), float(p.group(2))
    if 35 <= x <= 48 and y <= 11:
        print(f"VIA {id2name.get(n.group(1),'?'):9s} ({x:.2f},{y:.2f})")
