# power_kicad — HW-specifikation

**LiPo-kraftmodul för LoRa-noder** · 55,88 × 20,32 mm · 4 lager · rev A.2 (2026-08-04)

Försörjer en nRF52840 Connect Kit (eller annan MCU) och två SX1262-LoRa-kort från en
3 000 mAh LiPo-cell, med USB-C/sol-laddning, I2C-strömmätning och <15 µA sömnförbrukning.
Samma format och hålbild som Makerdiary nRF52840 Connect Kit — korten kan skruvas ihop.

## Nyckeltal

| Parameter | Värde |
|---|---|
| Kortstorlek | 55,88 × 20,32 mm, 1,0 mm, 4 lager |
| Monteringshål | 4× Ø1,4 mm (Connect Kit-mönster, 17,80 mm isär) |
| Batteri | 1-cells LiPo 3,0–4,2 V, JST PH 2,0 mm |
| Laddning | MCU-styrd 50/86/196/595 mA (MPPT-steg), 4,2 V CC/CV; USB/sol ≤6 V |
| Utgång 3V3 (buck) | 3,31 V, 1,5 A kontinuerligt / 3 A puls, avstängbar (EN) |
| Utgång 3V3_MCU (LDO) | 3,3 V, max 450 mA, alltid på |
| Radioutgångar | 2× filtrerade 3,3 V-matningar, individuellt brytbara |
| Sömnförbrukning | 11–15 µA ur cellen (allt avstängt) |
| Strömmätning | INA226, 16 bit, ±0,1 mA-klass, I2C-adress 0x40 |
| Styrning | TCA6408A I2C-expander (0x20): laddnivå, buck, radiorails, USB-detekt — MCU behöver bara I2C |

## Funktionsblock

### USB-C-ingång (J1)
**Syfte:** 5 V-matning och laddning.
2 A polyfuse, ferrit och TVS (SMF5.0A) skyddar mot kortslutning, ledningsburen störning
och transienter. CC-motstånden (5,1 kΩ) annonserar enhet så USB-C-laddare lämnar 5 V/3 A.
Datalinjerna används inte — kortet är en ren kraftmodul.

### Laddare — TP4056 (U2)
**Syfte:** ladda cellen linjärt (RF-tyst — ingen switchstörning under laddning).
Laddström MCU-vald i fyra steg 50/86/196/595 mA (MPPT-avsnittet nedan), 4,2 V flytspänning,
automatisk terminering vid C/10.
Två statuslysdioder (lyser endast med extern matning, drar aldrig ur batteriet):

| LED | Betydelse |
|---|---|
| Röd (CHRG) | laddning pågår |
| Grön (STDBY) | batteriet fulladdat |

**Exempel:** 3 000 mAh-cell från tom till full ≈ 5,5–6 h via USB-C (595 mA-steget).

### Solcellsingång (J3 — lödhål "S+ / G") + MPPT-steg
**Syfte:** fältladdning utan USB, med mjukvarustyrd panelanpassning.
Panel ≤6 V (tomgång ≤6,7 V OK — 6,8 V-zener klampar felaktiga paneler) diod-OR:as
in på laddaren. Laddström väljs i fyra steg (50/86/196/595 mA) via expanderbitarna
MP0/MP1/MP2 — perturb & observe med INA226 som mätare maximerar skörden i svagt ljus
(gryning/mulet/vinter). Expanderbit P6 (VBS, delad VBUS) talar om när USB är i
→ MCU sätter max. Utan MCU-styrning gäller 50 mA (säkert, men långsam USB-laddning).
**Exempel:** en 5 V/1 W-panel ger ~150–200 mA i sol — täcker en LoRa-nods dygnsbudget
många gånger om.

### Cellskydd — DW01A + 8205A (U3, Q1)
**Syfte:** sista försvarslinjen för cellen. Klipper vid överladdning (4,25 V),
djupurladdning (2,4 V) och överström/kortslutning. Helt transparent i drift.

### Strömmätning — INA226 + 10 mΩ shunt (U4, R5)
**Syfte:** mäta cellens verkliga ström och spänning — laddning såväl som urladdning.
Shunten sitter direkt på cellen: urladdning läses positiv, laddström negativ.
**Obs:** vid USB-drift går lasten förbi shunten (USB→power path→SYS) — INA226 ser då
bara cellens nettoström (≈ laddström), inte systemförbrukningen. Systemström kan
alltså bara mätas i batteridrift.
I2C-adress **0x40**, ALERT-pinne för programmerbara larm (t.ex. lågt batteri).

**Användning (rekommenderad lågenergi-rutin):**
1. Väck ur power-down, trigga one-shot-konvertering, läs, somna om.
2. En mätning/sekund kostar ~1 µA i snitt; kontinuerligt läge kostar 330 µA — undvik i batteridrift.

```
# Kalibrering for 10 mOhm shunt, Current_LSB = 0,1 mA/bit:
CAL = 0.00512 / (0.0001 * 0.01) = 5120  ->  skriv 0x1400 till reg 0x05
strom_mA  = las16(0x04) * 0.1        # register Current
cellspanning_V = las16(0x02) * 1.25e-3   # register Bus Voltage
# Power-down: skriv MODE=000 i reg 0x00; one-shot: MODE=011
```

### Power path (Q2, D4)
**Syfte:** automatisk källväxling utan mikrocontroller och utan tomgångsström.
USB-5V har alltid företräde (matar lasten via Schottky), batteriet tar över blixtsnabbt
via P-FET när kabeln dras ur — FET:ens body-diod överbryggar själva omslaget.
Batteriet kan aldrig mata baklänges in i USB-porten.

### Alltid-på-LDO — HT7833 (U5) → 3V3_MCU
**Syfte:** håller MCU:n (och INA226) vid liv dygnet runt för 4 µA.
450 mA räcker gott till nRF52840 + I2C. Under ~3,4 V cellspänning följer utgången
cellen (dropout) — ofarligt ned till MCU:ns brownout ~3,0 V.

### Buck — TPS62823 (U6) → 3V3
**Syfte:** effektiv 3 A-rail för radiokorten och tunga laster. 2,2 MHz, verkningsgrad
>90 %, egen förbrukning 4 µA. **Avstängd tills expanderbit P5 sätts** (pulldown = av vid uppstart).

### GPIO-expander — TCA6408A (U7), I2C 0x20
**Syfte:** all styrning över I2C — MCU:n behöver bara SDA/SCL (+ valfritt INT/ADC/RESET).
Register: 0x00 Input, 0x01 Output, 0x03 Config. Bitar: P0–P2 = MP0–MP2 (laddnivå),
P3/P4 = EN_RF1/EN_RF2, P5 = BUCK_EN, P6 = VBS (ingång, USB-detekt, ger IRQ på INT).

```
# Init (ordningen ar tvingande - output FORE config):
skriv 0x01 = 0x00        # sakert utgangslage
skriv 0x03 = 0xC0        # P0-P5 utgangar, P6-P7 ingangar
# Exempel: buck pa + radio 1 + 196 mA laddning:
skriv 0x01 = 0x2A        # 0x20(buck) | 0x08(RF1) | 0x02(196 mA)
# USB-detekt: las 0x00, bit 6. Mode-koll: las 0x03 - 0xFF = oinitierad (failsafe rader)
```

Failsafe i hårdvara: vid reset är expandern högohmig och kortets pulldowns ger
50 mA-laddning, buck av, radior av — oavsett firmware. Efter MCU-omstart: kör alltid
init-sekvensen (expandern behåller annars gammalt tillstånd).

### Lastbrytare + π-filter (Q3–Q6, FB3/FB4) → RF1/RF2
**Syfte:** varje radiokort får en egen brytbar och RF-filtrerad 3,3 V-matning.
Ferrit + 10 µF/100 nF/100 pF per utgång hindrar buckens övertoner att nå radion
och hindrar radiornas TX-pulser att störa varandra.
**Exempel:** sätt EN_RF1 hög 5 ms före SX1262-init; dra båda EN låga i sömn → radiodelen
drar exakt 0 µA.

## Anslutningar

**J7 — MCU-rad (10× 2,54 mm-hål, kablas till Connect Kit):**

| Hål | Signal | Riktning | Funktion |
|---|---|---|---|
| 1 | 3V3 | ut | buck-rail, **max 0,5 A ur denna pol** (av tills EN sätts; radiolast tas via J4) |
| 2 | GND | — | |
| 3 | 3V3_MCU | ut | alltid-på-rail → Connect Kit VSYS/3V3 |
| 4 | GND | — | |
| 5 | SDA | I2C | INA226 (0x40), 4,7 kΩ pullup finns på kortet |
| 6 | SCL | I2C | |
| 7 | ALERT | ut | INA226-larm, open-drain, 10 kΩ pullup |
| 8 | INT | ut | expander-IRQ (t.ex. USB in/ur), open-drain, 10 kΩ pullup |
| 9 | VSOL | ut (analog) | 0,4×VIN-källspänning (USB/sol) — **aktiveras med lödbygel JP1**, annars fri pol |
| 10 | RST | in | expander-hårdreset (aktiv låg, 10 kΩ pullup — kan lämnas okopplad) |

**Endast pol 5+6 (I2C) är obligatoriska att koppla** — buck, radiorails och laddnivå styrs via expandern.

**Övriga:** J1 USB-C · J2 batteri (JST PH, enda kontakten utöver USB) ·
J3 sol (hål: S+/G) · J4 radiomatning (hål: R1/G/R2/G).

**Testpunkter (fri koppar, Ø1,0 mm):** MP0/MP1/MP2, EN_RF1/EN_RF2, BUCK_EN, PROG,
VBS, VSOL, SYS, GND — alla expanderutgångar och nyckelnoder mätbara med oscilloskop/multimeter.

## MCU-styrning — firmwarekrav

Reglerna nedan kommer ur designgranskningarna (detaljer i `DESIGN.md`) och är
**krav, inte rekommendationer** — sömnströmmen och mätnoggrannheten hänger på dem.

### 1. Init-sekvens (tvingande ordning)
1. **9-puls SCL-recovery** före första transaktionen: I2C-bussen saknar timeout
   (INA226 + TCA6408A), så en MCU-reset mitt i en transaktion kan lämna SDA låst.
   Toggla SCL 9 gånger med SDA släppt, skicka sedan STOP.
2. Skriv expanderns **Output (0x01) = 0x00 FÖRE Config (0x03) = 0xC0** — annars
   glitchar utgångarna höga när riktningen byts (buck/radior kan blinka till).
3. Sanity-koll: läs reg 0x03 — `0xFF` betyder att expandern är i reset (failsafe
   råder: 50 mA-laddning, allt av) och init-sekvensen måste köras.
4. Efter varje MCU-omstart: kör alltid om sekvensen — expandern behåller annars
   sitt gamla tillstånd.

### 2. Läs input-registren vid VARJE uppvak (330 µA-fällan)
USB-i/urkoppling flippar VBS (P6) → TCA6408A **latchar INT låg** tills reg 0x00
läses. Så länge INT ligger låg läcker pullup-motståndet R31 (10 kΩ) 3,3 V/10 k ≈
**330 µA ur cellen — 20× hela sömnbudgeten**. Samma mekanism gäller INA226:s
ALERT-latch (R11).

- Läs **TCA6408A reg 0x00** vid varje uppvak, även spuriösa.
- Aktivera inte INA226:s alert-latchning i onödan; läs Mask/Enable (0x06) om larm använts.
- **Sömnströmsvalidering:** mät EFTER en USB-i/ur-cykel, annars missas fällan.

### 3. Sekvensering av laster
Buck (P5) **före** radio-EN (P3/P4) med ≥1 ms mellanrum — buckens PG-pinne är
okopplad, så mjukvarufördröjningen är enda garantin för att railen står stabil.
Därefter ~5 ms innan SX1262-init. I sömn: allt av i omvänd ordning (radior → buck).

### 4. MPPT — perturb & observe (soldrift)
1. VBS = 1 (USB i)? → sätt 595 mA-steget direkt, ingen P&O.
2. Annars: stega MP0–MP2 ett steg, **vänta ~1 s** (TP4056 + panel sätter sig),
   läs INA226 — **laddström läses negativ**.
3. Ökade skörden → fortsätt åt samma håll; annars backa ett steg.
4. Kör om var ~1–10 min i soldrift (moln/skuggtransienter); vid panelkollaps
   (byglad JP1: VSOL-ADC:n viker) → gå ner till 50 mA-steget.

### 5. Kalibrering och mätgränser
- Kelvin-restfel **~2–3 %** (padintern spridning i shuntlödytorna) — engångskalibrera
  strömmen mot känd last vid prototypen, lagra korrektionsfaktorn i firmware.
- INA226 är under sin VS-spec (2,7 V min) vid cellspänning 2,75–3,0 V (LDO-dropout) —
  lita inte blint på mätvärden nära urladdningsgränsen.
- Vid USB-drift ser shunten bara cellens nettoström (≈ laddström), inte systemlasten.

### 6. Minimalt setup-exempel (Arduino-stil)
Inkoppling: batteri i J2, J7-5/6 → MCU:ns SDA/SCL, J7-3 (3V3_MCU) → MCU:ns matning.
Mer behövs inte — exemplet startar buck + radio 1 och läser cellströmmen:

```cpp
#include <Wire.h>
#define EXP 0x20                      // TCA6408A
#define INA 0x40                      // INA226

void wr8(uint8_t a, uint8_t r, uint8_t v) {
  Wire.beginTransmission(a); Wire.write(r); Wire.write(v); Wire.endTransmission();
}
void wr16(uint8_t a, uint8_t r, uint16_t v) {
  Wire.beginTransmission(a); Wire.write(r); Wire.write(v >> 8); Wire.write(v & 0xFF);
  Wire.endTransmission();
}
uint16_t rd16(uint8_t a, uint8_t r) {
  Wire.beginTransmission(a); Wire.write(r); Wire.endTransmission(false);
  Wire.requestFrom(a, (uint8_t)2);
  return (Wire.read() << 8) | Wire.read();
}

void setup() {
  Wire.begin();
  // 1. SCL-recovery utelamnad har (krav i skarp firmware, se punkt 1)
  wr8(EXP, 0x01, 0x00);               // 2. output FORE config
  wr8(EXP, 0x03, 0xC0);               //    P0-P5 utgangar, P6-P7 ingangar
  wr16(INA, 0x05, 0x1400);            // 3. INA226-kalibrering: 10 mOhm, 0,1 mA/bit
  wr8(EXP, 0x01, 0x20);               // 4. buck pa ...
  delay(2);                           //    ... >=1 ms (PG okopplad)
  wr8(EXP, 0x01, 0x2A);               // 5. + radio 1 + 196 mA laddniva
  delay(5);                           // 6. darefter SX1262-init
}

void loop() {
  int16_t raw = (int16_t)rd16(INA, 0x04);
  float cell_mA = raw * 0.1f;         // urladdning positiv, laddning negativ
  rd16(EXP, 0x00);                    // slapp INT-latchen (330 uA-fallan)
  delay(1000);
  // Somn: wr8(EXP, 0x01, 0x00) + INA226 MODE=000 + MCU deep sleep
}
```

## Typisk driftcykel (LoRa-nod)

```
1. Uppstart:  3V3_MCU ar redan pa -> MCU bootar -> expander-init (0x01=0x00, 0x03=0xC0)
2. MCU:  skriv 0x01=0x20 (buck pa) -> vanta 1 ms -> 0x01|=0x08 (RF1) -> 5 ms -> SX1262-init
3. Mat:  INA226 one-shot fore/efter sandning -> logga energibudget
4. Sand LoRa-paket (~120 mA i 50-500 ms)
5. Somn: skriv 0x01=0x00 (radior+buck av, 50 mA-laddniva), INA226 power-down, MCU deep sleep
         -> hela systemet: 11-15 uA + MCU:ns egen somstrom
```

**Batterilivslängd (3 000 mAh, 1 sändning/10 min):** sömn ~13 µA + sändningar ~25 µA
i snitt ≈ **7–8 år teoretiskt** — i praktiken begränsar cellens självurladdning (~2–3 %/mån).

## Gränsvärden — läs innan inkoppling

| Regel | Skäl |
|---|---|
| Solpanel max 6 V (tomgång ~6,7 V ok) | TP4056:s arbetsområde; 6,8 V-klampen är försäkring, inte marginal |
| Batteri ENDAST i J2 (JST) | batteri i RF-hålen matar 4,2 V baklänges in i 3,3 V-railen |
| SX1262 får aldrig matas direkt från cellen | VDD max 3,7 V — använd alltid RF-utgångarna |
| Summalast 3V3: 1,2–1,5 A kontinuerligt (2,4 A puls), 3V3_MCU max 450 mA, J7-1 max 0,5 A | batterivägens spår (rev A.2), cellskyddets värme resp. LDO-gräns |
| Verkligt strömtak ~2,4–2,7 A — inte buckens 3 A | DW01A:s överströmströskel (150 mV över 8205A) löser ut efter ~10 ms och stänger batterivägen |
| Vid USB-drift i värme (>50 °C): max ~1 A last + laddning samtidigt | F1-polyfusens hold-ström sjunker ~2 A→1,5 A vid 60 °C; 1,5 A-lastlöftet gäller fullt ut bara batteridrift |
| Cellen under ~3,0 V → ladda snarast | skyddet klipper hårt vid 2,4 V |

## Filer och tillverkning
KiCad 9-projekt (`power_kicad.kicad_pro`), ERC/DRC 0 fel. JLCPCB-paket i `jlcpcb/`:
gerber-zip, BOM (alla rader med LCSC-nr, basic parts där möjligt) och CPL.
4 lager, dubbelsidig montering. Design- och komponentmotiveringar: `DESIGN.md`, `BOM.md`.

## Kända begränsningar (rev A.2)
- 3 A endast som kortpuls — kontinuerligt gäller 1,2–1,5 A (batterivägens spår +
  cellskyddets värmeutveckling); hårt tak ~2,4–2,7 A där DW01A klipper.
- Batteriprocent (SoC) beräknas i MCU-mjukvara; ingen hårdvarumätare.
- Buck i dropout under ~3,5 V cellspänning — 3V3 följer cellen, TX-effekten sjunker.
- Power-path-FET:en får förhöjt motstånd under ~3,2 V cellspänning (funktion garanterad av body-diod).
- INA226 under VS-spec vid cell 2,75–3,0 V (se §MCU-styrning punkt 5).
- Rev A.2 är maskinverifierad (ERC/DRC/netlista) och beställd, men ännu inte fysiskt prototypad.

## Detta kort vs. färdigköpt (Adafruit / SparkFun / Pololu)

### Närmaste kommersiella alternativ

| Färdigt kort | Vad det ger | Vad som saknas mot detta kort |
|---|---|---|
| SparkFun Battery Babysitter (BQ24075 + BQ27441) | laddning + riktig bränslemätare | ingen solingång, ingen 3 A-buck, inga brytbara/filtrerade radiorails; mätaren drar ström kontinuerligt |
| Adafruit Universal USB/Solar Charger (bq24074) | laddning USB+sol, power path | ingen strömmätning, ingen 3,3 V-utgång alls — kräver separat regulator |
| Adafruit INA219/INA226-breakout | strömmätning I2C | bara mätning; alltid-på-LED på kortet |
| Pololu S7V8F3 m.fl. regulatorer | fin spänningsomvandling | bara regulator; 1 A; ingen laddning/mätning/brytning |

En färdigköpt motsvarighet till hela funktionen blir alltså **3–4 staplade breakouts + kablage**
(~400–600 kr per nod) — och även då utan individuellt brytbara, RF-filtrerade radiomatningar.

### Välj DETTA kort när…
- **Sömnströmmen är affärskritisk.** Breakout-kombon landar typiskt på 50–500 µA
  (power-LED:ar, alltid-på-mätare, regulatorers tomgång). Detta kort: 10–15 µA — det är
  skillnaden mellan månader och år på en cell.
- **Två LoRa-radior ska samsas.** Individuella lastbrytare + π-filter per radio finns inte
  att köpa färdigt; det är kortets mest unika funktion.
- **Formatet spelar roll.** En modul i Connect Kit-format med samma skruvhål ersätter en
  hög breakouts med kablage — mekaniskt robust i fält.
- **Volym.** Vid 10+ enheter är detta billigare per nod (~150–250 kr) än breakout-kombon,
  och varje exemplar är identiskt och maskinmonterat.
- **Kontroll.** Öppet KiCad-projekt: varje komponent vald med skäl (dokumenterat i
  DESIGN.md), reproducerbart, modifierbart.

### Köp färdigt när…
- **Du behöver 1–2 exemplar nu.** Färdiga kort kostar 150–300 kr styck och finns på hyllan;
  detta kort kostar ~2 000–2 400 kr för minsta batchen (5 st) och tar 1–2 veckor.
- **Kraven är enklare.** Bara "ladda + 3,3 V" utan sömnkrav → Adafruit bq24074 + en
  Pololu-regulator löser det på en kväll, beprövat och färdigtestat.
- **Riskaptiten är låg.** Adafruit/SparkFun-kort är massproducerade, community-testade och
  har guider/bibliotek. Detta kort är rev A.2 — designen är maskinverifierad (ERC/DRC/netlista)
  men **ingen fysisk prototyp har ännu validerats**; räkna med att första batchen är just
  en prototypbatch.
- **Bränslemätning i %** behövs (State-of-Charge). INA226 mäter ström/spänning exakt, men
  coulomb-räkning i mjukvara får MCU:n stå för — BQ27441 på Battery Babysitter gör det i hårdvara.

**Summering:** för en enstaka hobbynod — köp färdigt. För en flotta LoRa-noder som ska leva
år på batteri med två radior — det är exakt nischen detta kort byggdes för, och där finns
inget färdigt alternativ som matchar sömnströmmen, formatet och radiohanteringen.
