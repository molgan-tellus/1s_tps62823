#!/usr/bin/env python3
"""Import freerouting SES into the board: wires -> PCB_TRACK, vias -> PCB_VIA.
SES resolution: (resolution um 10) => mm = units/10000; y negated."""
import re, sys
import pcbnew

BRD = "/home/gnu/claude/power_kicad/power_kicad.kicad_pcb"
SES = "/tmp/claude-1000/-home-gnu-claude-power-kicad/5116e7c5-9054-4e7f-b100-211dafa61912/scratchpad/board.ses"

txt = open(SES).read()

def tokenize(s):
    return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)

def parse(tokens, i=0):
    out = []
    while i < len(tokens):
        t = tokens[i]
        if t == '(':
            node, i = parse(tokens, i + 1)
            out.append(node)
        elif t == ')':
            return out, i + 1
        else:
            out.append(t.strip('"'))
            i += 1
    return out, i

tree, _ = parse(tokenize(txt))
tree = tree[0]  # (session ...)

def find_all(node, tag):
    res = []
    if isinstance(node, list) and node and node[0] == tag:
        res.append(node)
    if isinstance(node, list):
        for ch in node:
            res.extend(find_all(ch, tag))
    return res

b = pcbnew.LoadBoard(BRD)
LAYERS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu,
          "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}
nets = {b.GetNetInfo().GetNetItem(i).GetNetname(): b.GetNetInfo().GetNetItem(i)
        for i in range(b.GetNetInfo().GetNetCount())}

def mm(v):  # ses units -> mm
    return float(v) / 10000.0

nwires = nvias = 0
for net in find_all(tree, "net"):
    name = net[1]
    ni = nets.get(name) or nets.get("/" + name) or nets.get(name.lstrip("/"))
    if ni is None:
        print("WARN unknown net", name); continue
    for wire in find_all(net, "wire"):
        for path in find_all(wire, "path"):
            layer = LAYERS.get(path[1])
            if layer is None:
                print("WARN layer", path[1]); continue
            width = mm(path[2])
            coords = [float(v) for v in path[3:] if not isinstance(v, list)]
            pts = [(mm_x, -mm_y) for mm_x, mm_y in
                   ((float(coords[k])/10000.0, float(coords[k+1])/10000.0)
                    for k in range(0, len(coords)-1, 2))]
            for a, c in zip(pts, pts[1:]):
                if a == c: continue
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I_MM(a[0], a[1]))
                t.SetEnd(pcbnew.VECTOR2I_MM(c[0], c[1]))
                t.SetLayer(layer)
                t.SetWidth(pcbnew.FromMM(width))
                t.SetNet(ni)
                b.Add(t)
                nwires += 1
    for via in find_all(net, "via"):
        # (via "Via[0-3]_600:300_um" x y)
        m = re.search(r'_(\d+):(\d+)_um', via[1])
        dia, drill = (float(m.group(1))/1000.0, float(m.group(2))/1000.0) if m else (0.6, 0.3)
        x, y = mm(via[2]), -mm(via[3])
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(pcbnew.FromMM(dia))
        v.SetDrill(pcbnew.FromMM(drill))
        v.SetNet(ni)
        b.Add(v)
        nvias += 1

print(f"imported {nwires} track segments, {nvias} vias")

# widen power tracks (autorouter used default width)
POWER = {"VBUS_RAW", "VBUS_F", "VBUS", "CHG_VIN", "BAT_P", "CELL_P", "CELL_N",
         "SYS", "VIN_BK", "SW_BK", "3V3", "SW_RF1", "SW_RF2", "3V3_RF1", "3V3_RF2", "DD"}
n = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK" and t.GetNetname().lstrip("/") in POWER:
        t.SetWidth(pcbnew.FromMM(0.5)); n += 1
print("widened", n, "power segments")

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(BRD)
print("saved", BRD)
