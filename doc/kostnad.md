# Kostnadsuppskattning — 5 bestyckade kort (rev A.1)

Underlag 2026-07-31: komponentpriser, lager och basic/extended-status hämtade live från
JLCPCB-API:t för samtliga 42 BOM-rader. PCB/assembly/frakt är erfarenhetsuppskattningar —
exakta belopp syns först i JLC:s varukorg.

## Kalkyl

| Post | Belopp | Kommentar |
|---|---|---|
| Komponenter, 5 kort | $33 | verkliga JLC-styckpriser, alla 42 rader i lager |
| Extended-laddavgifter | $63 | 21 extended-rader × $3 (oberoende av antal kort) |
| PCB 4 lager, 5 st, 55,9×20,3 mm, 1,0 mm | $8–25 | ≈$10 med JLC:s standardstackup (JLC7628) |
| Standard-assembly, dubbelsidig | $45–65 | setup + 2 stenciler + ~400 lödpunkter/kort |
| THT-handlödning | ~$5 | J1-skärmflikar, J2 JST |
| Frakt till Sverige | $15–25 | |
| **Summa exkl. moms** | **≈ $170–190** | |
| **Inkl. 25 % moms (IOSS i kassan)** | **≈ $215–240** | **≈ 2 100–2 500 kr** |

## Noteringar

- **Laddavgifterna dominerar** ($63, fast kostnad). Marginalkostnad per extra kort ≈ $10–12:
  **10 kort kostar bara ~400–500 kr mer än 5** — värt att överväga, första batchen är
  prototyp och kort kan offras på mätningar/omlödningar.
- Dyraste komponenter per styck: TPS62823 $1,19 · INA226 $0,86 · TCA6408A $0,81.
  Allt annat är ören.
- **Lager vid kontroll 2026-07-31** (tunnaste raderna — kolla igen i varukorgen):
  | LCSC | Del | Lager |
  |---|---|---|
  | C5128770 | säkring mSMD200 (F1) | **1 096** ← tunnast |
  | C2693497 | TPS62823DLCR (U6) | 7 276 |
  | C42193 | SWPA4030S 1 µH (L1) | 7 565 |
  | C351449 | 8205A (Q1) | 8 149 |
  | C317622 | GZ3216-ferrit (FB1/FB2) | 9 005 |
  | C181499 | TCA6408ARGTR (U7) | 9 464 |
- Assembly-posten kan slå ±$20 beroende på hur JLC prissätter dubbelsidigheten;
  ekonomi-assembly går inte (dubbelsidig + THT kräver Standard).
- Beställningsval: 4 lager, 1,0 mm, Standard-assembly dubbelsidig; granska rotationer
  i förhandsvisningen. Se `STATUS.md` för hela beställnings- och valideringsflödet.
