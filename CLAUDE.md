# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektet
LiPo-kraftmodul (rev A.1) för LoRa-noder: 55,88×20,32 mm, 4 lager, nRF52840 Connect Kit-format.
TP4056-laddning (USB-C/sol, MPPT-steg 50/86/196/595 mA), 6,8 V-zenerklamp,
DW01A+8205A cellskydd, INA226 (I2C 0x40), diskret power path, HT7833 alltid-på-LDO,
TPS62823 3 A buck, 2× brytbara π-filtrerade radiorails. Sömn 11–15 µA.
Rev A.1: all styrning via TCA6408A GPIO-expander (U7, I2C 0x20) — MP0–2, EN_RF1/2, BUCK_EN,
VBS-läsning; J8 utgick, ersatt av TP1–TP11 (fri koppar) + VSOL-delare med lödbygel JP1 → J7-9.
**Status: ERC 0, DRC 0, 0 okopplade. Beställningsklar, EJ fysiskt prototypad.**
Läs `STATUS.md` (aktuellt läge, granskningsfynd, nästa steg) och `doc/DESIGN.md`
(alla designbeslut + kända begränsningar) först; `BOM.md` listar LCSC-verifierade delar.
`doc/hw_spec.md` (+ .odt/.pdf) är den användarvända specen — uppdatera vid funktionsändringar.

## Katalogstruktur
- **Roten** — KiCad-filerna (`power_kicad.*`), genererings-/engångsskripten och
  arbetsdokumenten `STATUS.md` och `BOM.md`.
- **`doc/`** — dokumentation: `DESIGN.md` (designbeslut), `hw_spec.md` + genererade
  `power_kicad_hw_spec.odt/.pdf`, `kostnad.md`, `Genomgången klar hela.txt`,
  3D-renders (`render_*.png`), JLC-preview-skärmdumpar (`jlpcb_a/b.png`).
- **`jlcpcb/`** — tillverkningsfiler: `power_kicad_gerber.zip`, `BOM.csv`, `CPL.csv`
  + råexporter (se §Tillverkningsfiler; den uppzippade `power_kicad_gerber/` är gitignorerad).
- **`jlcpcb_order/`** — orderunderlag för rev A.2-beställningen: markerade preview-bilder
  samt `jlcpcb_respons/` (JLC:s placement-preview, korrigerade previews, `support_mail.txt`).
- **`power_kicad-backups/`** — KiCads autobackuper (gitignorerade, liksom `fp-info-cache`
  och `.kicad_prl`).

## Hårda regler
- **Alla komponenter måste vara lagerverifierade hos JLCPCB före användning.** Kolla via API:t:
  `curl -s -H "Content-Type: application/json" -X POST "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList" -d '{"currentPage":1,"pageSize":8,"keyword":"<sök>"}'`
  Föredra basic parts. Datablad: `https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/<filnamn>.pdf`
  (lcsc.com-datasheet-URL:er blockeras — byt domän till wmsc).
- **Verifiera pinouter mot datablad** innan symboler skapas — kinesiska kloner avviker
  (t.ex. UMW 8205A SOT-23-6 ≠ TSSOP-varianten).
- Netclass-clearance 0,127 mm ligger i `power_kicad.kicad_pro` — kontrollera efter varje
  verktygskörning (`jq '.net_settings.classes[0].clearance' power_kicad.kicad_pro`);
  KiCad ignorerar netclassen om pro-filen är strukturellt minimal.

## Genereringskedja
Schemat genereras av `gen_sch.py` (netlist-spec i `BLOCKS`), PCB:n byggdes av `gen_pcb.py`
men har därefter handjusterats — **kör ALDRIG om gen_pcb.py, det raderar routingen**
(dess `NETFILE` pekar dessutom på en raderad scratchpad från originalsessionen).
gen_sch.py är säker att köra om (skriver inte över befintlig .kicad_pro).

```bash
python3 gen_sch.py                         # regenerera schema efter BLOCKS-ändring
kicad-cli sch erc power_kicad.kicad_sch --severity-error --exit-code-violations -o /dev/null
kicad-cli sch export netlist power_kicad.kicad_sch -o net.net
kicad-cli pcb drc power_kicad.kicad_pcb --format json --severity-error -o drc.json
```

## pcbnew-scripting: fallgropar (dyrköpta)
- `ZONE_FILLER.Fill()` segfaultar på `CreateEmptyBoard()`-brädor: **spara → `LoadBoard` → fyll → spara**.
- API:t segfaultar slumpvis vid långa sessioner: kör varje logiskt steg i **egen python-process**;
  textuell redigering av `.kicad_pcb` (s-expressions, balanserad parentesmatchning) är
  deterministiskt alternativ.
- `pcbnew.PCB_FIELD(fp, 0, ...)` skriver över **referensfältet** (id 0 = Reference) — använd aldrig id 0.
- `ImportSpecctraSES` returnerar False tyst — använd egen SES-parser (se `import_ses.py`).
- DSN-export kräver referens på ALLA footprints (även monteringshål).
- Efter zonändringar: fyll om zoner FÖRE DRC-driven spårkrympning — krympning mot ofylld-zon-DRC
  förstörde en gång alla kraftspårsbredder.

## Routing-arbetsflöde (bevisat)
1. Freerouting 2.1.0 (`freerouting21.jar`, Java 21; 2.2.4 kräver Java 25):
   `java -Djava.awt.headless=true -jar freerouting21.jar -de b.dsn -do b.ses -mp 50 --gui.enabled=false`
2. **Full-strip + omrutning från noll slår inkrementell inrutning** — vid komponentändringar:
   ta bort ALL koppar, ruta om, importera allt, kör efterbehandlingspipelinen.
3. Pipeline efter import: golv 0,3 mm på kraftnät → DRC-driven krympning (endast exakta träffar,
   radie ≤0,25, båda parterna) → zonfyllning → GND-ö-pass (hitta isolerade pour-regioner,
   via i ön eller pad-till-pad-stub) → slutlig DRC.
4. Handrouting: dumpa ALLTID exakt lokal geometri (alla lager + pads + vior) först — gissade
   koordinater kolliderar alltid.

### Engångsskript (mallar, kör INTE om som de är)
`import_ses.py`, `smart_route.py` och `surgery.py` innehåller hårdkodade sökvägar
(döda scratchpad-paths) och koordinater från specifika fixar. Deras *mönster* är återanvändbara:
- `import_ses.py` — SES-parser (tokenize/parse) + kraftnätsbreddning + zonfyllning. Uppdatera `SES`-sökvägen.
- `smart_route.py` — kollisionsvaliderad handrouting: bygger hinderkarta (spår/vior/pads),
  `seg_ok`/`via_ok` testar varje segment mot clearance 0,13 mm innan det läggs, `find_lane`
  provar kandidatkoordinater. Byt ut fixlistan längst ner.
- `surgery.py` — textuell s-expressionskirurgi på `.kicad_pcb`: `find_blocks` (balanserad
  parentesmatchning) för att ta bort segment/vior/footprints per nät-id, ändra pad-nät,
  flytta footprints. Byt ut åtgärdslistan.

## Tillverkningsfiler (`jlcpcb/`)
Efter varje brädändring: regenerera gerber+borr+zip och BOM/CPL **från projektroten** (inte scratchpad).
BOM/CPL byggs reproducerbart med `gen_jlc.py` — råexport-kommandona står i dess docstring:
`kicad-cli sch export bom` → `jlcpcb/bom_raw.csv`, `kicad-cli pcb export pos` → `jlcpcb/pos_raw.csv`,
sedan `python3 gen_jlc.py` → `BOM.csv`/`CPL.csv`. LCSC-nummer tas från symbolens LCSC-fält,
annars `VALMAP` (passiva); skriptet varnar om nummer saknas. Exkluderas ur bestyckning:
H1–H4, J3, J4, J7, R16, C13, JP1, TP1–TP11 (`EXCL` + `TP\d+`). Beställning: 4 lager, 1,0 mm,
Standard-assembly dubbelsidig; granska rotationer i JLC:s förhandsvisning.

## Nästa steg
Aktuell att-göra-lista, granskningsfynd (bl.a. 330 µA-fällan) och firmware-krav
underhålls i `STATUS.md` — uppdatera den filen vid sessionens slut, inte denna sektion.
