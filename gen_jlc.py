#!/usr/bin/env python3
"""Bygg JLCPCB-BOM och -CPL från schema/PCB. Kör från projektroten:
  kicad-cli sch export bom power_kicad.kicad_sch -o jlcpcb/bom_raw.csv \
      --fields "Value,Reference,Footprint,LCSC" --labels "Comment,Designator,Footprint,LCSC" \
      --group-by "Value,Footprint" --ref-range-delimiter "" --exclude-dnp
  kicad-cli pcb export pos power_kicad.kicad_pcb -o jlcpcb/pos_raw.csv \
      --format csv --units mm --side both --exclude-dnp
  python3 gen_jlc.py
LCSC-nummer: i första hand symbolens LCSC-fält, annars värdeskartan nedan (passiva)."""
import csv, re, sys

EXCL = {"H1", "H2", "H3", "H4", "J3", "J4", "J7", "R16", "C13", "JP1"}
def excluded(ref):
    return ref in EXCL or re.fullmatch(r"TP\d+", ref)

# värde+kapsel -> LCSC för passiva utan eget fält (samma karta som rev A-BOM:en)
VALMAP = {
 ("100nF", "C_0402_1005Metric"): "C1525",
 ("100nF", "C_0603_1608Metric"): "C14663",
 ("10uF", "C_0805_2012Metric"): "C15850",
 ("22uF", "C_0805_2012Metric"): "C45783",
 ("100pF", "C_0603_1608Metric"): "C1635",
 ("120pF", "C_0603_1608Metric"): "C1643",
 ("1k", "R_0603_1608Metric"): "C21190",
 ("4.7k", "R_0603_1608Metric"): "C23162",
 ("5.1k", "R_0603_1608Metric"): "C23186",
 ("10k", "R_0603_1608Metric"): "C25804",
 ("22.1k", "R_0603_1608Metric"): "C25961",
 ("100k", "R_0603_1608Metric"): "C25803",
 ("150k", "R_0603_1608Metric"): "C22807",
 ("330R", "R_0603_1608Metric"): "C23138",
}

def short_fp(fp):
    return fp.split(":", 1)[-1]

# ---- BOM ----
rows = []
with open("jlcpcb/bom_raw.csv") as f:
    for r in csv.DictReader(f):
        refs = [x.strip() for x in r["Designator"].split(",")]
        refs = [x for x in refs if not excluded(x)]
        if not refs:
            continue
        val, fp = r["Comment"], short_fp(r["Footprint"])
        lcsc = r.get("LCSC", "").strip() or VALMAP.get((val, fp), "")
        if not lcsc:
            print(f"VARNING: LCSC saknas för {val} / {fp} ({','.join(refs)})", file=sys.stderr)
        rows.append([val, ",".join(refs), fp, lcsc])
with open("jlcpcb/BOM.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    w.writerows(rows)
print(f"BOM.csv: {len(rows)} rader")

# ---- CPL ----
out = []
with open("jlcpcb/pos_raw.csv") as f:
    for r in csv.DictReader(f):
        ref = r["Ref"]
        if excluded(ref):
            continue
        out.append([ref, f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm',
                    r["Side"].capitalize(), f'{float(r["Rot"]):.6f}'])
with open("jlcpcb/CPL.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    w.writerows(out)
print(f"CPL.csv: {len(out)} rader")
