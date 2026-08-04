# STATUS — power_kicad rev A.2 (2026-08-02) — BESTÄLLD

## Beställning 2026-08-02 (JLCPCB)
Rev A.2 beställd med bestyckning: 4 lager, 1,0 mm, ENIG, 1 oz/0,5 oz, min-via 0,2 mm
(→ high-precision: TG155 + 4-wire-test + plugged vias, auto), Standard assembly dubbelsidig,
kantramar av JLCPCB, Confirm Production File + Confirm Parts Placement = Yes.
**BOM-intervallbuggen fixad före beställning**: kicad-cli komprimerade referenslistor till
`R17-R20`-intervall som JLC inte tolkar → `--ref-range-delimiter ""` tillagd i gen_jlc.py-
kedjan; BOM↔CPL maskinverifierade 81↔81. Zip innehåller även BOM/CPL.
**Under leveranstiden**: firmware-förberedelse (se nedan). Placement-bekräftelsen är klar —
se nästa avsnitt.

## Placement-bekräftelse 2026-08-03 (KLAR — produktion godkänd)
JLC:s Part Placement-preview granskad (screenshots + korrespondens i `jlcpcb_order/jlcpcb_respons/`):
BOM 42/42 rader matchade, 81 placeringar, inga unselected. **10 delar felroterade i previewn**
(rotationskonventionen i CPL:n, som väntat): D1/D4 (katod fel håll), U7 (90° fel), Q7 samt
U2, U3, Q1, Q2, U4, U6 (pin 1 diagonalt fel). Korrigeringsmail (`jlcpcb_order/jlcpcb_respons/support_mail.txt`)
skickat 2026-08-03 ~12:00, **maskinverifierat mot .kicad_pcb** (pin 1-/katodpaddarnas absoluta
positioner via pcbnew, mappade till previewns vy; alla 21 polariserade delar täckta — även de
11 som skulle lämnas orörda). JLC:s korrigerade preview (`top/bottom_correction.png` + `large/`)
granskad i zoom: **alla 10 rätt, keep-as-is-delarna orörda**. F1 (MSMD200/16, C5128770) visades
utan kropp i första previewn — bekräftad monterad (bara saknad preview-modell hos JLC).
**Layouten bekräftad ("Yes, please proceed") 2026-08-03 → produktion.**

## Rev A.2: omrutning av kraftvägar + äkta Kelvin
PCB-djupgranskningen fann att "beställningsklar" inte höll: Kelvin bruten (~5× INA226-fel),
batterivägar i 0,2 mm på 0,5 oz-innerlager (~0,4 A-klass mot dokumenterade 1,5 A), hela 3V3
på en enda via, och RST_EXP/VSOL_J som klöv In2-planet. Allt omrutat med kollisionsvaliderad
kirurgi (scratchpad-verktygen rt.py/phases.py; ~25 nya/flyttade vior, 5 nät helt ombyggda,
2 nät omdragna, ~15 GND-fixar). Detaljer i doc/DESIGN.md §Rev A.2.

**Verifierat:** DRC 0 fel / 0 okopplade · netlista↔PCB (enda diff: DNP-paddarna R16.1/C13.2
+ U6.8 PG som förut) · alla ombyggda nät 1 sammanhängande komponent · clearance 0,127 intakt ·
ERC 0 · gerber+borr-zip REGENERERAD (kopparn ändrad!) · renders omgjorda · BOM/CPL opåverkade
(42/81 rader, C14/C15=22 µF sedan schemagranskningen).

**Nya dokumenterade gränser:** batteriväg ~1,2–1,5 A kontinuerligt (flaskhals 4 mm 0,2 mm
på CELL_N-F, ΔT ~25–30 °C @1,5 A); **J7-1 max 0,5 A** (In1-matning). Kelvin-restfel ~2–3 %
(padintern spridning) — kalibrera mot känd last vid prototypen.

**Kvar till rev B:** SW-snubberstub + RF1-under-L1 (båda verbatim-återställda; kräver
komponentflytt), In1-väst-splitten, silk-läsbarhetspasset.

## Schemagranskning + åtgärder 2026-08-02
Fjärde granskningen (input range + sanity check av hela nätlistan; detaljer i
doc/DESIGN.md §Schemagranskning 2026-08-02). Nätlistan höll — all delarmatte omräknad OK.
**Åtgärdat:**
1. J3-etiketten `<=5.5V` → `<=6V` (gen_sch.py + schema + PCB:s dolda value-fält +
   doc/hw_spec.md:s gränsvärdestabell) — harmoniserad med panelspecen ≤6 V/tomgång 6,7 V.
2. C14/C15 buck-ut 10 µF → 22 µF (C45783, basic, lagerverifierad 2026-08-02) för
   DC-bias-marginal mot databladets 22 µF typ. Samma footprint — ingen layoutändring.
3. `gen_sch.py`-sökvägar rättade (OUT pekade på omslagskatalogen, expected_nets.json
   på död scratchpad) — skriptet är nu säkert att köra från projektroten.
Verifierat efter åtgärd: ERC 0, DRC 0 fel / 0 okopplade, clearance 0,127 intakt,
BOM/CPL regenererade (42/81 rader; enda diff: C14/C15 bytte 10 µF→22 µF-grupp).
**Gerber-zippen är opåverkad** (inga Fab-lager i zippen; ändringarna rör bara dolda
Fab-fält) — fortfarande beställningsklar.
**Noterat utan åtgärd:** D5-zenertolerans kan ge svag ledning vid panel-tomgång 6,7 V
(ofarligt); soltermineringens undre hörn tajt (→ mätplan); π-filterplacering bekräftad
korrekt (filter vid källan + avkoppling vid modulens VDD — krav på modulsidan).
*(Släpet i hw_spec .odt/.pdf åtgärdat 2026-08-04: regenererade från doc/hw_spec.md
med pandoc → odt, soffice → pdf, i samband med nya §MCU-styrning.)*

## Layoutgranskning + åtgärder 2026-08-01 (incheckade)
Tredje granskningen (lager + silkscreen). **Åtgärdat på brädan och i regenererad gerber-zip:**
1. **J7 pinne 8–10 var felmärkta i silk** (`EN RF1 RF2` = gamla rev A-pinouten; näten är
   INT_EXP/VSOL_J/RST_EXP) → nu `INT VSL RST`. Felet låg i den beställningsklara zippen!
2. Två GND-vior 0,34 mm c-c vid (26,2, 16,0) — borrisk → den ena borttagen, zoner omfyllda.
3. Zippen innehöll kvarglömd `power_kicad.drl` från rev A (2026-07-30) utöver PTH/NPTH → utgår.
DRC efter åtgärd: 0 fel, 0 okopplade; clearance 0,127 intakt. BOM/CPL oförändrade.

**Kvarvarande fynd (accepterade för rev A.1, ej blockerande):**
- **In1-planet är kluvet i två halvor** (snitt x≈24–28; 75 innerlagersegment från
  expander-reworken) + In2 8 öar — "obruten GND-plan"-regeln bruten. Elektriskt helt via
  pourer/vior men EMC-kompromiss: beakta vid RF-validering, åtgärda i rev B (lyft
  innerlagerspåren till F/B).
- 102 silk-texter under 0,8 mm (refs 0,6/0,1; etiketter 0,45–0,55/0,11 — JLC vill ha
  ≥1,0/0,15) + 61 silk-överlapp + 60 silk-över-koppar → refs blir delvis oläsliga i fab.
  Funktionsetiketterna är läsbara men små. Danglande stubbar: VM 4,5 mm (In1),
  RST_EXP 6,1 mm (In2) + 7 mikrostubbar.


## Läget just nu
- **Rev A.2 beställd 2026-08-02, produktion godkänd 2026-08-03** — inväntar leverans.
  Allt incheckat (commit `59e9f96` = det beställda läget).
- Verifierat läge: ERC 0, DRC 0 fel / 0 okopplade, netlista↔PCB verifierad (enda diff:
  DNP-paddarna R16.1/C13.2 + U6.8 PG, avsiktligt). Netclass-clearance 0,127 mm intakt.
- Full designgranskning 2026-07-31: **konstruktionen håller** — alla pinouter verifierade
  mot datablad, all delarmatte omräknad (laddsteg 50/86/196/595/742 mA, VBS 3,0 V,
  VSOL 0,4×källa, buck-FB 3,31 V), power-path-logiken korrekt i alla fyra matningsfall.
  Datablad för alla BOM-delar cachade i `doc/datasheets/` (`<MPN>_<LCSC-nr>.pdf`).
- **EJ fysiskt prototypad.**

## Granskningsfynd att komma ihåg (detaljer i doc/DESIGN.md §Designgranskning 2026-07-31)
1. **330 µA-fällan (viktigast)**: TCA6408A INT latchar låg vid USB-i/urkoppling (VBS flippar)
   tills reg 0x00 läses → R31 läcker 330 µA i sömn. Samma för INA226 ALERT/R11.
   → **Firmware-krav: läs alltid input-registret vid uppvak.** Sömnströmsmätningen måste
   göras EFTER en USB-i/ur-cykel för att fånga detta.
2. **Verkligt strömtak ~2,4–2,7 A** (DW01A 150 mV över 8205A), inte buckens 3 A.
3. **D5-zenern (1 W) klarar bara små felpaneler** — stor 12 V-panel eller backvänd panel
   bränner den. Panelspec ≤6 V gäller på riktigt.

Mindre (accepterade): buck-dropout under ~3,5 V cell; USB-strömbudget oförhandlad
(byglad VSOL_J ser portsag); INA226 under VS-spec vid cell 2,75–3,0 V; D1-TVS efter ferriten.

## Att göra härnäst (i ordning)
1. **Firmware-förberedelse** (under leveranstiden):
   - Init-ordning TCA6408A: 9-puls SCL-recovery → skriv Output=0x00 **FÖRE** Config=0xC0.
   - Läs reg 0x00 vid varje uppvak (330 µA-fällan).
   - Buck (0x20) FÖRE radio-EN (0x08/0x10), ~1 ms mellanrum; PG är okopplad.
   - MPPT-P&O: stega, vänta ~1 s, läs INA226 (laddström = negativ); backa vid fall.
2. **Prototypvalidering vid leverans** (mätplan i CLAUDE.md/doc/DESIGN.md):
   - TP7/PROG med oscilloskop på alla fyra MPPT-nivåer (kapacitanskänslig nod).
   - Sömnström <15 µA — inklusive efter USB-i/ur-cykel (fynd 1).
   - Power path-omslag (USB i/ur under last), laddterminering, RF-rails renhet.
   - Kelvin-restfel ~2–3 %: kalibrera INA226 mot känd last.
3. **Rev B-kandidater** (utöver doc/DESIGN.md:s lista och §Rev A.2:s "Kvar till rev B"):
   power-path-FET med lägre Vth, ev. hårdvaru-SoC, kraftigare solklamp om felpaneler
   är ett verkligt scenario, In1-planets klyvning, silk-läsbarhetspasset
   (funktionsetiketter ≥0,8 mm, isära TP1–TP3/TP9/R32-klustret).

## Kom-ihåg för arbetssättet
- Kör **ALDRIG** om `gen_pcb.py` (raderar handrutad routing). `gen_sch.py` är säker.
- Efter varje verktygskörning: `jq '.net_settings.classes[0].clearance' power_kicad.kicad_pro`
  ska ge 0,127.
- Alla nya komponenter måste lagerverifieras via JLCPCB-API:t före användning (se CLAUDE.md).
