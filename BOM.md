# Dellista — lagerverifierad mot JLCPCB 2026-07-30 (U7 tillagd och verifierad 2026-07-31)
Alla LCSC-nummer nedan är kontrollerade via JLCPCB:s komponent-API samma dag.
"basic" = ingen setup-avgift. Lager rör sig — gör slutkontroll i varukorgen vid beställning.

## Aktiva / nyckelkomponenter (som i schemat)
| Ref | Del | LCSC | Typ | Lager | Kommentar |
|---|---|---|---|---|---|
| U2 | TP4056-42-ESOP8 (TOPPOWER) | C16581 | extended | 80 582 | 1 A linjär laddare; alt C725790 (UMW, 548k st) |
| U3 | DW01A (PUOLOP, SOT-23-6) | C351410 | extended | 39 443 | cellskydd |
| U4 | INA226AIDGSR (TI, VSSOP-10) | C49851 | extended | 43 285 | I2C strömmätning; alt INA219 C87469 |
| U5 | HT7833-A (UMW, SOT-89) | C347195 | extended | 56 043 | LDO 3,3 V Iq 4 µA; alt Holtek C50936 (4k st) |
| U6 | TPS62823DLCR (TI, VSON-8 1,5×2) | C2693497 | extended | 7 276 | buck 3 A, 2,4–5,5 V, Iq 4 µA |
| Q1 | 8205A (UMW, SOT-23-6) | C351449 | extended | 8 199 | dubbel NFET; alt JSMSEMI C2762931 (36k st) |
| Q2 | AO4407A (SO-8) | C2841482 | extended | 206 299 | power-path P-FET, 12 mΩ |
| Q3,Q5 | AO3401A (SOT-23) | C15127 | **basic** | 735 693 | lastbrytare high-side |
| Q4,Q6 | 2N7002 (SOT-23) | C8545 | **basic** | 497 641 | gate-drivare |
| D1 | SMF5.0A (SOD-123FL) | C169426 | extended | 49 840 | TVS VBUS |
| D2,D3 | SS34 (SMA) | C8678 | **basic** | 2,4M | USB/sol → laddare |
| D4 | SS54 (SMA) | C22452 | **basic** | 2,1M | USB-gren power path |
| L1 | SWPA4030S1R0NT 1 µH (Sunlord) | C42193 | extended | 7 769 | Isat 5,7 A; 1 µH TI-godkänd för TPS6282x |
| FB1,FB2 | GZ3216D601TF (1206) | C317622 | extended | 9 053 | 600 Ω@100 MHz, VBUS + buck-VIN |
| FB3,FB4 | GZ2012D601TF (0805) | C1017 | **basic** | 517 626 | π-filter per radio (500 mA räcker: SX1262 ~120 mA topp) |
| R5 | HoJLR2512-3W-10mΩ-1 % | C2903468 | extended | 124 436 | shunt, Kelvin-layout |
| F1 | mSMD200/16 polyfuse (1812) | C5128770 | extended | 1 396 | 2 A hold; alt C561582/C70124 |
| LED1 | KT-0603R röd | C2286 | **basic** | 7,4M | CHRG |
| LED2 | KT-0603G grön | C12624 | **basic** | 418 779 | STDBY |
| J1 | TYPE-C-31-M-12 (HRO) | C165948 | extended | 253 653 | USB-C 16-pin — en av kortets två monterade kontakter |
| J2 | JST PH-2 horis. (2,0 mm) | C173752 | extended | 75 009 | batteri — kortets andra monterade kontakt |
| U7 | TCA6408ARGTR (TI, VQFN-16 3×3) | C181499 | extended | 9 464 | I2C GPIO-expander 0x20: MP0–2, EN_RF1/2, BUCK_EN, VBS; standby 1 µA typ. TSSOP-varianten (C206177) rymdes inte i layouten |
| J3,J4,J7 | **endast hål** (2,54 mm THT) | — | — | — | omonterade, kablar löds direkt; funktion i silkscreen. J3=sol (S+/G), J4=RF-rad (R1/G/R2/G), J7=MCU-rad (3V3, GND, 3VM, GND, SDA, SCL, ALR, INT, VSOL, RST) |

## Passiva (generiska basic-delar, värden ur schemat)
| Värde | Antal | Kapsel | Användning |
|---|---|---|---|
| 5,1 k | 2 | 0603 | USB-C CC1/CC2 |
| 1 k | 3 | 0603 | LED-serier ×2, DW01A VM |
| 330 R | 1 | 0603 | DW01A VCC-filter |
| 100 k | 6 | 0603 | gate-pull ×2, EN-pulldown ×3, VBUS-bleed |
| 4,7 k | 2 | 0603 | I2C pullups |
| 10 k | 3 | 0603 | ALERT pullup + RST_EXP/INT_EXP pullups (R30/R31) |
| 100 k + 22,1 k | 1+1 | 0603 | buck FB-delare → 3,31 V |
| 2 R | 1 | 0603 | snubber (DNP) |
| 22 µF X5R | 5 | 0805 | SYS ×2, buck in, buck ut ×2 (C14/C15 uppgraderade från 10 µF 2026-08-02) |
| 10 µF X5R | 6 | 0805 | laddare ×2, LDO in/ut, π-filter ×2 |
| 100 nF | 7 | 0603 | avkoppling |
| 100 nF | 1 | 0402 | buck hot-loop (närmast VIN!) |
| 120 pF | 1 | 0603 | buck Cff |
| 470 pF | 1 | 0603 | snubber (DNP) |
| 100 pF C0G | 2 | 0603 | π-filter HF |

## Förkastade under lagerkontrollen
| Del | Skäl |
|---|---|
| TPS2121 (C485916) | i lager, men Iq 300 µA från batteri i sömn — dödar lågenergibudgeten |
| MP2143 | bara 206 st hos JLCPCB |
| LM66200 | max 1,5 A |
| MP2315S/TPS563201 | VIN min 4,5 V — startar inte på en cell |
| JST ZH (C722913) | i lager, men footprint saknas i KiCad-stdbibliotek — PH valdes för sol |

## Struket under layouten
| Del | Skäl |
|---|---|
| USBLC6-2SC6 (C7519) | USB-data används inte — ren kraftmodul |
| R15 (PG-pullup) | PG-nätet hade ingen läsare; pinnen lämnas flytande enligt datablad |
| JST för sol/RF | ersatta med lödhål — endast USB-C + batteri-JST monteras |

## MPPT-steg + solskydd (tillagda)
| Ref | Del | LCSC | Typ | Kommentar |
|---|---|---|---|---|
| Q7 | 2N7002DW-7-F (Diodes, SOT-363) | C83571 | extended | dubbel NFET, steg A+B |
| Q9 | 2N7002 (SOT-23) | C8545 | **basic** | steg C |
| R3 | 24 k (ersätter 1,8 k) | C23352 | **basic** | basnivå 50 mA |
| R22/R23/R24 | 33 k / 8,2 k / 2,2 k | C4216/C25981/C4190 | **basic** | stegben |
| R25–R28 | 100 k ×4 | C25803 | **basic** | pulldowns + VBUS-delare topp |
| R29 | 150 k | C22807 | **basic** | VBUS-delare botten (VBS ≈ 3,0 V) |
| D5 | 1SMA4736A 6,8 V/1 W zener | C382952 | extended | solingångsklamp |
| ~~J8~~ | ~~4 hål 2,54 mm~~ | — | — | **utgick i rev A.1** — ersatt av U7-expandern + testpunkter |

## GPIO-expander + VSOL (rev A.1, 2026-07-31)
| Ref | Del | LCSC | Typ | Kommentar |
|---|---|---|---|---|
| U7 | TCA6408ARGTR (VQFN-16 3×3) | C181499 | extended | se aktiva-tabellen |
| C7 | 100 nF 0603 | C14663 | **basic** | avkoppling U7 (VCCI+VCCP på 3V3_MCU) |
| R30,R31 | 10 k 0603 | C25804 | **basic** | pullup RESET resp. INT (open-drain) |
| R32 | 150 k 0603 | C22807 | **basic** | VSOL-delare topp (från CHG_VIN) |
| R33 | 100 k 0603 | C25803 | **basic** | VSOL-delare botten (0,4×VIN, max ~2,6 V) |
| JP1 | lödbygel, öppen | — | — | VSOL → J7-9; fri koppar, ingen montering |
| TP1–TP11 | testpunkter Ø1,0 mm | — | — | fri koppar: MP0/1/2, EN_RF1/2, BUCK_EN, PROG, VBS, VSOL, SYS, GND — ej i BOM/CPL |
