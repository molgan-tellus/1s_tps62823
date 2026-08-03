# Power board — 3.7 V LiPo, 2–3 A, laddning, I2C-strömmätning, låg energi
Mål: försörja 2× SX1262 (LoRa) + MCU från 3000 mAh LiPo. KiCad 9-projekt, JLCPCB-montering.
Alla aktiva komponenter är lagerverifierade mot JLCPCB:s komponentbibliotek 2026-07-30 (se BOM.md).

## Lärdomar från RAK19007 (WisBlock Base 2nd gen)
- **Linjär laddning** — ingen switchad laddare = ingen laddstörning i RF-bandet.
- **Solcellsingång** (≤6 V, tomgång ≤6,7 V; zenerklampad) diod-OR:ad in på laddarens VIN.
- **GPIO-styrda lastbrytare** per modulgrupp — deras nyckel till <2 µA läckage / <10 µA idle.
- **Batteri**: JST PH 2,0 mm, USB-C med ESD-skydd.

## Arkitektur (som byggd i power_kicad.kicad_sch)
```
USB-C ──polyfuse──ferrit── VBUS ─┬─ SS34 ─┐
Solcell (hålrad J3, ≤6V) ── SS34 ─┼────────┴→ CHG_VIN → TP4056 (1A) → BAT_P
       TVS SMF5.0A på VBUS (USB-data oanvänd)│
                                  │              LiPo (JST PH): CELL_P/CELL_N
                                  │              DW01A + 8205A skydd på CELL_N
                                  │              CELL_P ──10 mΩ shunt── BAT_P
                                  │              INA226: IN+=CELL_P, IN−=BAT_P (ser ladd- OCH urladdström)
                                  │
POWER PATH:  VBUS ── SS54 ──────┬─┴─ SYS ── AO4407A (D=BAT_P, S=SYS, G=VBUS + 100k pulldown)
(USB-prioritet, ~0 µA ur batteri)│
             ┌───────────────────┤
   HT7833 LDO 3,3 V         ferrit GZ3216 → TPS62823 buck 3 A (2,2 MHz, Iq 4 µA)
   (alltid på, Iq 4 µA)          │ EN ← TCA6408A P5 (100k pulldown = av)
   → 3V3_MCU: INA226, TCA6408A,  └→ 3V3 ── lastbrytare ×2 (AO3401A+2N7002, EN ← TCA6408A P3/P4)
     I2C-pullups                       └→ π-filter (GZ2012 + 10µ/100n/100p) → 3V3_RF1 / 3V3_RF2
```

### Nyckelbeslut och varför
- **TPS2121 power mux FÖRKASTAD**: databladet anger Iq = 300 µA typ (400 µA max) från aktiv ingång
  = batteriet i sömn. Skulle spränga <10 µA-budgeten 30×. Den diskreta power-pathen gör samma jobb
  (USB vinner automatiskt, backspärr via body-diod-orientering) med ~0 µA statisk dragning:
  AO4407A drain=BAT_P/source=SYS → body-dioden överbryggar omkopplingsglappet när USB rycks,
  och blockerar SYS→batteri när USB matar.
- **MP2143 FÖRKASTAD (lager)**: bara 206 st hos JLCPCB. **TPS62823DLCR** vald i stället:
  3 A, VIN 2,4–5,5 V, **Iq 4 µA**, 2,2 MHz, 7 276 st. 1 µH-induktor officiellt godkänd av TI
  (SWPA4030S1R0NT, 5,7 A Isat). FB-delare 100k/22,1k + Cff 120 pF → 3,31 V.
- **SX1262 får INTE matas direkt från LiPo** (VDD max 3,7 V; cellen är 4,2 V laddad).
- **Två rails**: TPS62823 (EN-styrd, av i sömn) för tunga laster; HT7833-A (Iq 4 µA, alltid på)
  för MCU + INA226. Under ~3,4 V cell är LDO:n i dropout och följer cellen — OK ned till ~3,0 V.
- **Shunt direkt på cellen** (CELL_P—BAT_P): INA226 är bidirektionell → laddström negativ,
  urladdning positiv. 10 mΩ ger 30 mV @ 3 A (INA226 klarar ±81,9 mV) och ~10 mV fel i
  TP4056-terminering — försumbart. Kelvin-dragning!
- **TP4056 TEMP=GND** (NTC avstängd), CE=VIN. Laddström MCU-vald i fyra steg (se MPPT-sektionen): 50/86/196/595 mA.
- **Cellskydd**: DW01A + UMW 8205A (SOT-23-6: 1=S1, 2/5=D gemensam, 3=S2, 4=G2, 6=G1).
  2×28 mΩ i serie → 0,17 V fall @ 3 A. OD styr FET mot CELL_N, OC mot GND.

## Sömnbudget (mål <15 µA ur cell)
HT7833 4 µA + DW01A ~3 µA + INA226 power-down ~2 µA + TPS62823 avstängd ~1,5 µA
+ TCA6408A standby ~1 µA (max 3,2) + TP4056 BAT-läckage <2 µA
+ AO4407A/SS54-läckage ~1–3 µA ≈ **11–15 µA**.
Kräver: buck-EN låg, lastbrytare av, INA226 i power-down via I2C, I2C-bussen tyst.

## Samtidig laddning och drift
Laddning (USB eller sol) pågår parallellt med drift — cellen är buffert, INA226 visar nettoström.
- **USB inne**: lasten matas från USB via SS54/power-path, TP4056 laddar ostört → ren terminering.
- **Endast sol**: lasten dras ur cellen medan TP4056 trycker in laddström. Terminering (C/10) nås
  bara vid låg medellast — OK för duty-cyclad LoRa-nod. Mikro-cykling runt 4,2 V är normalt.
- **Panelkollaps**: TP4056 saknar ingångsreglering — svag panel hickar. Uppgradering: CN3065.

## VIN-områden
| Ingång | Område | Begränsas av |
|---|---|---|
| USB-C VBUS | 4,75–5,25 V | USB-spec; TVS SMF5.0A; TP4056 tål 8 V abs max |
| Solcell | ~4,8–6,0 V (tomgång ≤6,7 V) | TP4056 arbetsområde 4–8 V; D5-zener 6,8 V klampar felpaneler; SS34 tappar ~0,3 V |
| Batterirail | 3,0–4,2 V | DW01A klipper 2,4/4,25 V |
| SYS (buck/LDO-VIN) | 3,0 V (cell) – ~4,9 V (USB−SS54) | TPS62823: 2,4–5,5 V ✓ |

## Avstörning med tanke på LoRa (868 MHz)
1. **Linjär laddare** (TP4056) — inga laddspurioser.
2. **Buck TPS62823**: 100 nF 0402 + 22 µF tätt mot VIN/GND (hot-loop mm-kort, samma lager, inga vior);
   GZ3216-ferrit SYS→buck-VIN stoppar ledningsburen störning bakåt; skärmad SWPA4030S-induktor,
   minimal SW-yta; snubber-footprint 2 Ω + 470 pF på SW (DNP tills mätning kräver — ringningen
   100–300 MHz är hotet mot 868 MHz, inte 2,2 MHz-grundtonen); FB-spår kort, bort från SW.
3. **π-filter per radio**: GZ2012-ferrit + 10 µF + 100 nF + 100 pF tätt mot modulens VDD.
   Egen ferrit per SX1262 så TX på den ena inte modulerar den andras RX.
4. **SX1262 i intern DC-DC-mode** för strömbudget; strapping till LDO-mode som fallback.
5. **Layout**: obruten GND-plan, via-stitching runt RF (λ/20 ≈ 1,7 cm), keep-out under antenn,
   buck i motsatt hörn, inga switchspår nära RF. 4 lager rekommenderas (GND på L2).
6. **USB**: ferrit + TVS på VBUS — kabeln är en antenn.
7. **I2C**: 4,7 k pullups mot 3V3_MCU; SDA/SCL bort från RF-zon.
8. **Antenn-ESD (option)**: endast låg-kapacitans-TVS (~0,25 pF) för 50 Ω-anpassningen.

## PCB (power_kicad.kicad_pcb)
- **55,88 × 20,32 mm** (nRF52840 Connect Kit-format), 4 lager, 1,0 mm tjock.
- **Monteringshål som Connect Kit**: 4× Ø1,4 mm, 1,5 mm från kortändar / 1,26 mm från långsidor
  (17,80 mm isär) → korten kan skruvas ihop.
- **Endast två monterade kontakter**: USB-C (J1, vänster kortände) och batteri-JST (J2, långsida).
  Sol (J3), RF-raden (J4) och MCU-raden (J7, 10 hål) är rena 2,54 mm-hål med funktionstext
  i silkscreen — kablar löds direkt. (J8 utgick i rev A.1 — ersatt av expander + testpunkter.)
- **Zonindelning enligt avstörningsreglerna** (vänster→höger): USB/skydd → laddning →
  cellskydd+shunt+INA226 (Kelvin: U4 intill R5) → power path → buck (C11 0402 tätt mot U6 VIN,
  hot-loop på samma lager) → lastbrytare/π-filter → RF-hål vid bortre änden.
- **Dubbelsidig montering**: ICs/kontakter fram, passiva bak. GND-plan på In1 (solid),
  In2, plus GND-pour fram/bak. Termiska vior under TP4056:s EP.
- Laddström MCU-styrd 50–595 mA (MPPT-steg) — termiskt oproblematiskt på formatet.
- **DRC: 0 fel** (netclass-clearance 0,127 mm, inom JLC 4-lagers 0,09 mm-gräns).
- Genereras av `gen_pcb.py` (placering + automatisk kollisionslösare).
- **Spårdragning KLAR**: Freerouting (autoroute) + handdragna kritiska nät. Kraftnät 0,35 mm
  där utrymmet tillåter, signaler 0,25/0,2 mm. GND via In1-plan + stitching-vior (~35 st).
  SW-noden dragen direkt pad→induktor (0,3/0,4 mm). U6:s AGND/NC strappade till PGND enligt
  datablad. PG lämnad flytande (pullupen R15 struken — nätet hade ingen läsare).
  **Slutlig DRC: 0 fel, 0 okopplade** (clearance 0,127 mm, JLC 4L-min 0,09).
- **Silkscreen-ikoner** (symbol.png, tröskad; källbilden borttagen ur repot 2026-08-03): stor på baksidan under USB, liten vid BATT.

## Projektfiler
- `power_kicad.kicad_sch` — flatschema, 98 komponenter, 50 nät (rev A.1).
  ERC: 0 fel. Netlista maskinverifierad mot PCB:ns pad-nät (`check_nets`-metoden).
- `power_kicad.kicad_sym` — projektbibliotek; pinouter verifierade mot datablad
  (TI TPS62823 SLVSDV6C, UMW 8205A, PUOLOP DW01A, TOPPOWER TP4056, UMW HT78xx-A,
  TI TCA6408A SCPS192D).
- Fält `LCSC` på varje symbol → JLCPCB-BOM-export.
- **JLCPCB-paket klart** i `jlcpcb/`: `power_kicad_gerber.zip` (11 lager + borr),
  `BOM.csv` (42 rader, alla med LCSC-nr; passiva = basic parts), `CPL.csv` (81 delar, båda sidor;
  byggs reproducerbart med `gen_jlc.py`).
  R3 = 24 kΩ basnivå (C23352, basic); laddström väljs av MCU via MPPT-stegen.
  Vid beställning: 4 lager, 1,0 mm, dubbelsidig montering (Standard-assembly krävs för THT J1/J2);
  granska rotationer i JLC:s förhandsvisning (deras vinkelkonvention avviker per kapsel);
  slutlig lagerkoll i varukorgen.

## Designgranskning 2026-07-30 — svagheter funna och åtgärdade
**Åtgärdat:**
1. **Buckens ingångskondensator satt fel** — C11 låg 3 mm från U6:s VIN-pinne med ~11 mm
   slingväg (bröt egen designregel). Flyttad till (42,1, 3,55), direkt norr om U6, kort stub
   till VIN-korridoren.
2. **Kraftspår underdimensionerade** — autorouterns 0,2–0,25 mm räcker inte för 3 A.
   Alla kraftnät breddade till ≥0,3 mm (0,35–0,5 där utrymme finns); endast verkliga
   trängselpunkter kvar på 0,2–0,25. DRC-driven iterativ breddning/krympning.
3. **Ärlig strömderating**: kontinuerligt 1,5 A på 3V3 (spår + 8205A-värme: 2×28 mΩ ger
   0,5 W @3 A i SOT-23-6), 3 A endast som kortpuls. Räcker med 5× marginal för
   2×SX1262 + MCU (~0,3 A).
4. **HT7833-A Iq verifierad** i UMW-databladet: 2 µA typ (bättre än antagna 4 µA).

**Kända begränsningar (rev A, dokumenterade — ej blockerande):**
- AO4407A power-path-FET har VGS = −3,0 V vid urladdad cell → förhöjd RDS(on) i
  batterivägens sista del; body-dioden garanterar funktion. Rev B: FET med lägre Vth.
- Ingen hårdvaru-SoC (batteriprocent) — MCU:n coulomb-räknar via INA226.
- CPL-rotationer måste verifieras i JLCPCB:s förhandsvisning (deras konvention).
- Ingen ESD-krets på J7/J4-kablaget — håll kablarna korta.
- Lastbrytarnas inrush (10 µF hårdladdning) tas av buckens strömgräns — mjukstart saknas.
- Fysisk prototyp ej ännu validerad — första batchen är per definition prototyp.
- PROG-noden (TP4056 pin 2) är efter MPPT-tillägget dragen till fyra motstånd över kortet
  (~30–40 mm total spårlängd, uppskattat ~10 pF parasitkapacitans). TP4056:s PROG-pinne är
  känslig för stor kapacitans — bedöms OK men bör verifieras med oscilloskop i prototypen
  (jämn CC-ström utan oscillation på alla fyra nivåer).

## MPPT-steg och solskydd (tillagt efter granskningen)
**Fattigmans-MPPT**: TP4056:s PROG-nod har fyra parallellkopplingsbara ben som MCU:n
styr via 2N7002-FET:ar (Q7 dual + Q9) — perturb & observe i mjukvara med INA226 som
återkoppling (laddström = negativ cellström):

| Nivå | MP2 MP1 MP0 | Rprog eff. | Laddström | Läge |
|---|---|---|---|---|
| 0 | 0 0 0 | 24 k (R3) | ~50 mA | gryning, mulen vinter |
| 1 | 0 0 1 | ∥33 k (R22) | ~86 mA | RAK-panelen (0,45 W) i sol |
| 2 | 0 1 0 | ∥8,2 k (R23) | ~196 mA | 1 W-panel |
| 3 | 1 0 0 | ∥2,2 k (R24) | ~595 mA | stor panel / USB |
| kombos | — | — | upp till ~742 mA | MCU väljer; >670 endast puls |

- **VBUS-känsel**: 100 k/150 k-delare (R28/R29) → VBS ≈ 3,0 V vid USB → MCU sätter max direkt.
  VBS läses digitalt på TCA6408A P6 (rev A.1); J8-hålraden är ersatt av expandern + testpunkter.
- Pulldowns (100 k) ger säker basnivå 50 mA utan MCU; USB-laddning utan firmware blir
  långsam (50 mA) — dokumenterad avvägning.
- Algoritm: stega upp, vänta ~1 s, läs INA226; ström ökade → behåll; föll/hickar → backa.
  Sluta störa i CV-fas (cellspänning > 4,1 V). TP4056:s termiska reglering ligger kvar
  som skyddsnät (vänta mellan steg så den inte feltolkas som panelkollaps).
- **D5**: 6,8 V/1 W zener (1SMA4736A) över solingången — klampar felaktiga paneler
  (9–12 V-typer); rätt paneler (≤6 V, tomgång ≤6,7 V) berörs inte. TP4056 tål 8 V,
  så zenern är försäkring, inte förutsättning.
- Solspec uppdaterad: panel ≤6 V nominellt (tomgång ~6,7 V OK).
- Layouten efter MPPT-tillägget är **helt omrutad från noll** (Freerouting 0 incomplete)
  + efterbehandling; slutlig DRC 0 fel, 0 okopplade.

## GPIO-expander TCA6408A (rev A.1, tillagt 2026-07-31)
All styrning (laddnivå, radiorails, buck) flyttad från direkta MCU-GPIO till en
**TCA6408ARGTR** (TI, VQFN-16 3×3 mm, LCSC C181499, I2C-adress **0x20**, ADDR=GND) på 3V3_MCU.
(TSSOP-16-varianten förkastades under layouten: enda kandidatytan genomborras av J7:s
hålrad — footprint-kroppen kolliderade med tre genomgående hål. VQFN 3×3 ryms på
baksidan vid (21,6, 5,4), mitt bland MP-FET:arna; EP löds mot GND-pour.)
MCU-behovet krymper från 10 signaler till 2 obligatoriska (SDA/SCL) + 4 valfria
(INT, ALERT, VSOL-ADC, RESET). J8-hålraden utgick; J7 fick ny pinout (se nedan).

### Bitallokering
| Bit | Signal | Riktning | Bit | Signal | Riktning |
|---|---|---|---|---|---|
| P0 | MP0 | ut | P4 | EN_RF2 | ut |
| P1 | MP1 | ut | P5 | BUCK_EN | ut |
| P2 | MP2 | ut | P6 | VBS | **in** |
| P3 | EN_RF1 | ut | P7 | reserv | in, **bunden till GND** |

### Registerstyrning (register: 0x00 Input, 0x01 Output, 0x02 Polaritet, 0x03 Config)
- **Init (ordningen tvingande)**: skriv Output=0x00 FÖRE Config=0xC0. Output-registret
  defaultar till 0xFF — omvänd ordning driver allt högt (buck+radior+742 mA) i ett slag.
- Laddnivåer (mask 0x07): 0x00=50 mA, 0x01=86, 0x02=196, 0x04=595, 0x07=742 (endast puls).
- Buck: bit 0x20 (måste sättas FÖRE EN_RF — railsen matas från bucken; PG är okopplad,
  vänta ~1 ms efter buck-på). Radio 1: 0x08, radio 2: 0x10.
- Exempel drift: buck + radio 1 + 196 mA = 0x2A.
- **Läge/mode-detektering**: Config=0xFF ⇒ power-on-default (failsafe råder);
  reg 0x01 = senast kommenderat; reg 0x00 = faktiska pinnivåer (bit 6 = VBS/USB-detekt;
  avvikelse output↔input avslöjar kortslutning).

### Failsafe och kända fällor (analyserade före bygget)
- Vid POR är alla P-portar hi-Z → kortets 100 k-pulldowns (R14/R18/R20/R25–R27) ger
  50 mA laddning, buck av, radior av — failsafen är oförändrat ren hårdvara.
- **Expandern resetar INTE med MCU:n** (watchdog/brownout): boot-rutinen måste ovillkorligen
  skriva säkert tillstånd som första åtgärd. RESET-pinnen är dragen till J7-10 (RST_EXP)
  med 10 k pullup (R30) — värd-MCU:n KAN hårdreseta den, men måste inte.
- Brownout-risk: expandern behåller register ned till 1,65 V — radior kan stå på under
  MCU-bootloop vid låg cell tills firmware släcker. Mitigering: init-disciplin + RST_EXP.
- I2C-bussen saknar timeout (INA226+TCA6408A): firmware gör 9-puls SCL-recovery före init.
- **Mellannivå på P-port kostar upp till +80 µA standby** (ΔICCP): därför P7→GND, och
  VBS (~VCC−0,3 V vid USB) är ofarlig eftersom den bara är hög när kortet matas externt.
- Standby verifierad i TI-databladet: 1 µA typ / 3,2 µA max (2,3–3,6 V) — ryms i budgeten.

### VSOL: källspänningsmätning via lödbygel (JP1)
150 k/100 k-delare (R32/R33) från **CHG_VIN** → VSOL → **JP1 (lödbygel, öppen som default)**
→ J7-9 (VSOL_J). Byglad: MCU-ADC mäter USB (~1,88 V) eller solpanel (0,4×V, max ~2,6 V
zenerklampat) — skiljer källa, ser panelkollaps innan laddströmmen viker. Obyglad: polen fri,
delaren belastar bara CHG_VIN (≈27 µA vid 6 V sol, 0 µA i mörker/utan källa — aldrig cellen).

### J7 ny pinout (rev A.1)
1:3V3 · 2:GND · 3:3V3_MCU · 4:GND · 5:SDA · 6:SCL · 7:ALERT · 8:INT_EXP · 9:VSOL_J · 10:RST_EXP

### Testpunkter (fri koppar, Ø1,0 mm)
TP1–TP3: MP0/MP1/MP2 · TP4/TP5: EN_RF1/EN_RF2 · TP6: BUCK_EN · TP7: PROG (kort stubb,
kapacitanskänslig nod — primär valideringspunkt) · TP8: VBS · TP9: VSOL · TP10: SYS · TP11: GND

## Designgranskning 2026-07-31 (rev A.1) — nya fynd
Full omgranskning av netlistan, all delarmatte och alla pinouter. Konstruktionen håller;
tre odokumenterade svagheter hittades (inget blockerar beställning):

1. **INT/ALERT-latchen är en 330 µA-fälla i sömn** (allvarligast). USB-urkoppling flippar
   VBS (P6) → TCA6408A latchar INT låg och håller den tills input-registret läses; R31 (10 k)
   läcker då 3,3 V/10 k ≈ 330 µA ur cellen — 20× sömnbudgeten. Samma mekanism för INA226:s
   ALERT genom R11. **Firmware-krav: läs alltid TCA6408A reg 0x00 vid varje uppvak (även
   spuriöst), och aktivera inte INA226-alertlatchning i onödan.** Måste ingå i
   sömnströmsvalideringen (mät EFTER en USB-i/ur-cykel).
2. **Systemets verkliga strömtak är DW01A:s ~2,4–2,7 A, inte buckens 3 A.** Överströmströskeln
   150 mV över 8205A:ns 2×28 mΩ löser ut efter ~10 ms — längre "3 A-puls" stänger batterivägen.
   Irrelevant för avsedd last (~0,3 A) men den ärliga systemgränsen.
3. **D5-zenern (1 W) skyddar bara mot små felpaneler.** 12 V-panel med Isc ≥ 300 mA klampad
   vid 6,8 V ger >2 W → zenern dör öppen och TP4056 ser panelens tomgång mot sitt 8 V abs-max.
   Backvänd panel driver hela Isc genom D5 i framriktning. Skrivningen "klampar felpaneler"
   gäller 9 V-småpaneler, inte generellt.

Mindre (noterade, accepterade): buck i dropout under ~3,5 V cell (3V3 följer cellen, TX-effekt
sjunker); USB-strömbudget förhandlas ej (595 mA-steget kan sänka svag port — byglad VSOL_J ser
spänningsfallet); INA226 utanför VS-spec (2,7 V-min) vid cell 2,75–3,0 V p.g.a. LDO-dropout,
innan DW01A klipper vid 2,4 V; D1-TVS sitter efter FB1 i stället för närmast kontakten.

## Rev A.2 (2026-08-02) — omrutning av kraftvägar + äkta Kelvin
PCB-djupgranskning (alla lager, path-trace pad-till-pad) fann att autoroutern+breddningspasset
lämnat fyra allvarliga brister. Allt åtgärdat med kollisionsvaliderad kirurgi (rt.py/phases.py-
metoden, aldrig gen_pcb.py); slut-DRC 0 fel / 0 okopplade, netlista maskinverifierad.

**Åtgärdat:**
1. **INA226-Kelvin var bruten** (huvudströmmen passerade genom U4:s sense-pads → ~5× mätfel).
   Nu: CELL_P-huvudväg 0,5 mm In2-korridor J2→R5 som inte rör U4; dedikerade sense-spår
   från tap i R5-padkopparn via In1 till U4.10/U4.8 (v3-via) och U4.9 (F-väg). Restfel ~2–3 %
   (padintern spridning) — kalibrera i firmware vid prototypen.
2. **Batterivägen var ~0,4 A-klassad** (15 mm 0,2 mm på 0,5 oz-In1 + singelvia per nät).
   Nu: CELL_N 1,0 mm In2-korridor + 0,9/0,45-via; CELL_P 0,5 mm In2; BAT_P 0,5 mm till Q2.
   **Ärlig systemgräns: ~1,2–1,5 A kontinuerligt** — kvarvarande flaskhals är 4 mm 0,2 mm F
   i G1/PGC-fickan på CELL_N (ΔT ~25–30 °C @1,5 A) + 2512-shuntens omgivning. 2,4 A endast puls.
3. **3V3 hängde på EN via** (utgångskondensatorerna bakom 13 mm 0,2 mm-kedja). Nu: bond-via
   vid buck-ut till C14/C15-webben, C12 (Cff) nordlänkad över FB3, R12/R17/R19-webben egen via.
   **J7-1-matningen går på In1 (0,25/0,4 mm): max 0,5 A på J7-1** (hw_spec uppdaterad).
4. **In2-vandrarna RST_EXP/VSOL_J** (33+18 mm plan-klyvning inkl. x=37-väggen) helt omdragna:
   RST via In2-östkanten (mellan H2/H4), VSOL via In2/B-tunnel x=38,4. In1 under bucken läkt
   (CELL_N-diagonalen + 3V3-runs borta); GND öst↔väst-bryggad med 3 verifierade vior;
   VM:s danglande In1-stub städad.

**Medvetet kvarlämnat (rev B — kräver komponentflytt):**
- SW-snubberstubben (7 mm + via till DNP-R16 på B) — återställd verbatim; FB/PGB/SNUB-
  labyrinten på B medger ingen kortare väg utan att flytta R16/C13 till F intill SW-paden.
- 3V3_RF1:s F-vertikal under L1-kroppen — återställd verbatim; FB-delarens B-web + C12/C20
  omöjliggör alternativ descent. Rev B: flytta FB3/J4 eller C12.
- In1:s södra strip (J7-matningen) + väst-splitten (x≈24–28, BUCK_EN/MP1/PROG-webben).

## Schemagranskning 2026-08-02 — input range + sanity check
Full omräkning av delarmatte och VIN-områden; nätlistan höll. Två åtgärder, två noteringar:

**Åtgärdat (schema + PCB-value-fält + BOM/CPL regenererade; gerber-zip opåverkad —
zippen saknar Fab-lager och ändringarna rör bara dolda Fab-fält):**
1. **J3-etiketten harmoniserad till `<=6V`** (var `<=5.5V`, en kvarleva från före
   MPPT-granskningens panelspec ≤6 V nominellt / tomgång ≤6,7 V). hw_spec.md:s
   gränsvärdestabell rättad likaså.
2. **C14/C15 (buck-ut) 10 µF → 22 µF** (C45783, redan i BOM som SYS/buck-in, basic,
   3,8 M i lager). 2×10 µF gav ~14–16 µF effektivt efter DC-bias vid 3,31 V mot
   databladets typiska 22 µF; 2×22 µF ger ~25–30 µF — lasttransientmätningen blir
   bekräftelse i stället för öppen fråga. Samma footprint, ingen layoutändring.

**Noterat (ingen åtgärd):**
- **D5-zenern (1SMA4736A ±5 %: Vz 6,46–7,14 V) kan leda svagt vid tillåten panel-tomgång
  6,7 V** — panelen dras bara ned längs IV-kurvan. Förklarar om TP9/VSOL visar ~6,5 V
  i stället för förväntad tomgång; inte ett fel.
- **Soltermineringens undre hörn är tajt**: 4,8 V panel − ~0,35 V SS34 ≈ 4,45 V CHG_VIN,
  mot TP4056:s behov ~VBAT+0,3 V för ren CV vid 4,2 V. MPPT-stegningen mildrar (lägre
  ström → lägre diodfall); full terminering i svagt ljus sker nära cellens flyt.
  → Prototypmätplan: verifiera terminering med svag panel.
- **π-filtrens placering bekräftad korrekt** (fråga under granskningen): filter vid källan
  (dämpar SW-ringning innan kabeln kan stråla; per-rail-ferrit isolerar radiorna vid
  splitten) + avkoppling vid lasten. Kravet på modulsidan: 100 nF + 100 pF vid SX1262:ans
  VDD-pinne — färdiga moduler (E22/RA-01SH-klass) har det ombord; naken SX1262 på egen
  bärare måste få egen avkoppling. Kablar J4→modul korta (<5 cm), varje rail tvinnad med
  sin GND-granne (J4-ordningen `R1 G R2 G` är gjord för det).

## Layoutgranskning 2026-08-01 (rev A.1) — lager + silkscreen
Åtgärdat direkt (textuell/pcbnew-kirurgi, gerber-zip regenererad): J7 pinne 8–10-silken bar
gamla rev A-namnen `EN RF1 RF2` → rättad till `INT VSL RST` (INT_EXP/VSOL_J/RST_EXP);
GND-via-par 0,34 mm c-c → ena borttagen; kvarglömd rev A-borrfil ur zippen.

**Känd begränsning (rev B-punkt): In1-GND-planet är inte obrutet.** Rev A.1-omrutningen lade
75 signalsegment på In1 (PGB/BUCK_EN/MP1/PROG/EN_RF1/INT_EXP m.fl.) som klyver planet i två
halvor med snitt vid x≈24–28 (vänster 298 mm², höger 363 mm²) plus 6 småöar; In2 likaså 8 öar.
Returströmmar mellan korthalvorna går via ytterpourer/stitching-vior i stället för planet.
Rev B: ruta om innerlagersignalerna på F/B så In1 blir helt. Även: silk-texterna ligger under
JLC:s läsbarhetsrekommendation (refs 0,6 mm; bör vara ≥1,0/0,15 där plats finns).
