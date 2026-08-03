#!/usr/bin/env python3
"""Generate power_kicad KiCad 9 project: schematic + symbol lib + project file.
Connectivity via net labels placed exactly on pin endpoints. Layout: block strips."""
import uuid, json, os

OUT = os.path.dirname(os.path.abspath(__file__))
PROJ = "power_kicad"
NS = uuid.UUID("12345678-1234-5678-1234-567812345678")
def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))
ROOT = uid("root")

# ---------------- symbol definitions ----------------
# pins: (number, name, side, slot, etype)  side: L,R,T,B ; slot: grid index (2.54mm units, centered)
# geometry: box half-width hw, half-height hh (mm). Pin stub 2.54.
SYMS = {}
def sym(name, ref, hw, hh, pins, desc=""):
    SYMS[name] = dict(ref=ref, hw=hw, hh=hh, pins=pins, desc=desc)

# 2-pin vertical passives: pin1 top, pin2 bottom
for n, r in [("R","R"),("C","C"),("L","L"),("FB","FB"),("FUSE","F"),("SHUNT","R")]:
    sym(n, r, 1.27, 2.54, [("1","1","T",0),("2","2","B",0)])
# 2-pin horizontal: diodes/LED: pin2=A left, pin1=K right
for n in ["D_SCHOTTKY","D_TVS","LED"]:
    sym(n, "D", 2.54, 1.905, [("2","A","L",0),("1","K","R",0)])

sym("PFET_SOT23","Q",3.81,3.81,[("1","G","L",0),("2","S","B",0),("3","D","T",0)],"AO3401A P-FET")
sym("NFET_SOT23","Q",3.81,3.81,[("1","G","L",0),("2","S","B",0),("3","D","T",0)],"2N7002 N-FET")
sym("NFET_DUAL","Q",6.35,5.08,[("5","G1","L",1),("4","S1","B",-1),("3","D1","T",-1),
    ("2","G2","L",-1),("1","S2","B",1),("6","D2","T",1)],"2N7002DW dual N-FET")
sym("PFET_SO8","Q",5.08,5.08,[("4","G","L",0),
    ("1","S","B",-1),("2","S","B",0),("3","S","B",1),
    ("5","D","T",-2),("6","D","T",-1),("7","D","T",1),("8","D","T",2)],"AO4407A P-FET SO-8")
sym("M8205A","Q",6.35,5.08,[("1","S1","L",1),("6","G1","L",-1),
    ("3","S2","R",1),("4","G2","R",-1),("2","D","T",-1),("5","D","T",1)],"Dual NFET common drain")
sym("TP4056","U",7.62,7.62,[("4","VCC","L",2),("8","CE","L",1),("1","TEMP","L",0),
    ("2","PROG","L",-1),("3","GND","L",-2),
    ("5","BAT","R",2),("6","STDBY","R",0),("7","CHRG","R",-1),("9","EP","B",0)],"1A Li-Ion charger")
sym("DW01A","U",6.35,5.08,[("5","VCC","L",1),("6","GND","L",-1),
    ("1","OD","R",1),("2","VM","R",0),("3","OC","R",-1),("4","TD","B",0)],"Battery protection")
sym("TPS62823","U",7.62,6.35,[("7","VIN","L",2),("1","EN","L",1),("2","FB","L",-1),
    ("3","AGND","B",-1),("5","PGND","B",1),
    ("6","SW","R",2),("8","PG","R",1),("4","NC","R",-1)],"3A buck 2.4-5.5V")
sym("HT7833","U",6.35,3.81,[("2","VIN","L",1),("3","VOUT","R",1),("1","GND","B",0)],"3.3V LDO 4uA Iq")
sym("INA226","U",8.89,8.89,[("6","VS","L",3),("10","IN+","L",1),("9","IN-","L",0),
    ("8","VBUS","L",-1),("7","GND","L",-3),
    ("4","SDA","R",2),("5","SCL","R",1),("3","ALERT","R",0),("2","A0","R",-2),("1","A1","R",-3)],
    "I2C current monitor")
sym("USB_C","J",8.89,16.51,[
    ("A4","VBUS","R",5),("B4","VBUS","R",4),("A9","VBUS","R",3),("B9","VBUS","R",2),
    ("A5","CC1","R",1),("B5","CC2","R",0),
    ("A6","D+","R",-1),("B6","D+","R",-2),("A7","D-","R",-3),("B7","D-","R",-4),
    ("A8","SBU1","R",-5),("B8","SBU2","R",-6),
    ("A1","GND","B",-2),("A12","GND","B",-1),("B1","GND","B",1),("B12","GND","B",2),
    ("S1","SHIELD","B",3)],"USB-C 16P")
for n in [2,3,4,8,10]:
    sym(f"CONN_1x{n:02d}","J",3.81,max(2.54,(n*2.54)/2),
        [(str(i+1),str(i+1),"R",(n-1)/2.0-i) for i in range(n)],"Pin header")
# TCA6408A VQFN-16 (RGT), pinout verifierad mot TI SCPS192D (UQFN/VQFN-kolumnen):
# 1=RESET 2-5=P0-P3 6=GND 7-10=P4-P7 11=INT 12=SCL 13=SDA 14=VCCP 15=VCCI 16=ADDR 17=EP
sym("TCA6408A","U",8.89,12.7,[
    ("15","VCCI","L",4),("14","VCCP","L",3),("12","SCL","L",2),("13","SDA","L",1),
    ("1","RESET","L",-1),("16","ADDR","L",-2),("6","GND","L",-3),("17","EP","L",-4),
    ("2","P0","R",4),("3","P1","R",3),("4","P2","R",2),("5","P3","R",1),
    ("7","P4","R",0),("8","P5","R",-1),("9","P6","R",-2),("10","P7","R",-3),
    ("11","INT","R",-4)],"8-bit I2C GPIO-expander")
sym("TP","TP",1.27,1.27,[("1","1","L",0)],"Testpunkt (fri koppar)")
sym("JUMPER","JP",2.54,1.27,[("1","1","L",0),("2","2","R",0)],"Lodbygel")

# ---------------- instances ----------------
# (ref, sym, value, footprint, lcsc, {pin: net}, dnp)
FP = {
 "R0603":"Resistor_SMD:R_0603_1608Metric","C0805":"Capacitor_SMD:C_0805_2012Metric",
 "C0603":"Capacitor_SMD:C_0603_1608Metric","C0402":"Capacitor_SMD:C_0402_1005Metric",
 "R2512":"Resistor_SMD:R_2512_6332Metric","LED":"LED_SMD:LED_0603_1608Metric",
 "SMA":"Diode_SMD:D_SMA","SOD123F":"Diode_SMD:D_SOD-123F",
 "SOT23":"Package_TO_SOT_SMD:SOT-23","SOT236":"Package_TO_SOT_SMD:SOT-23-6",
 "SOT89":"Package_TO_SOT_SMD:SOT-89-3","SO8":"Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
 "ESOP8":"Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm",
 "VSSOP10":"Package_SO:VSSOP-10_3x3mm_P0.5mm","VSON8":"Package_SON:VSON-8_1.5x2mm_P0.5mm",
 "SWPA4030":"Inductor_SMD:L_Sunlord_SWPA4030S","FUSE1812":"Fuse:Fuse_1812_4532Metric",
 "L0805":"Inductor_SMD:L_0805_2012Metric","L1206":"Inductor_SMD:L_1206_3216Metric",
 "USBC":"Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
 "JSTPH":"Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
}
def HDR(n): return f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical"

BLOCKS = [
 ("USB-C 5V IN + SKYDD", [
  ("J1","USB_C","USB-C 5V",FP["USBC"],"C165948",
    {"A4":"VBUS_RAW","B4":"VBUS_RAW","A9":"VBUS_RAW","B9":"VBUS_RAW",
     "A5":"CC1","B5":"CC2","A6":None,"B6":None,"A7":None,"B7":None,
     "A8":None,"B8":None,"A1":"GND","A12":"GND","B1":"GND","B12":"GND","S1":"GND"}),
  ("F1","FUSE","mSMD200 2A",FP["FUSE1812"],"C5128770",{"1":"VBUS_RAW","2":"VBUS_F"}),
  ("FB1","FB","600R@100MHz 3A",FP["L1206"],"C317622",{"1":"VBUS_F","2":"VBUS"}),
  ("D1","D_TVS","SMF5.0A",FP["SOD123F"],"C169426",{"1":"VBUS","2":"GND"}),
  ("R1","R","5.1k",FP["R0603"],"",{"1":"CC1","2":"GND"}),
  ("R2","R","5.1k",FP["R0603"],"",{"1":"CC2","2":"GND"}),
 ]),
 ("LADDNING TP4056 (USB + SOL)", [
  ("D2","D_SCHOTTKY","SS34",FP["SMA"],"C8678",{"2":"VBUS","1":"CHG_VIN"}),
  ("J3","CONN_1x02","SOLCELL <=6V HAL",HDR(2),"",{"1":"SOLAR_P","2":"GND"}),
  ("D3","D_SCHOTTKY","SS34",FP["SMA"],"C8678",{"2":"SOLAR_P","1":"CHG_VIN"}),
  ("D5","D_TVS","6.8V zener",FP["SMA"],"C382952",{"1":"SOLAR_P","2":"GND"}),
  ("C1","C","10uF",FP["C0805"],"",{"1":"CHG_VIN","2":"GND"}),
  ("U2","TP4056","TP4056",FP["ESOP8"],"C16581",
    {"1":"GND","2":"PROG","3":"GND","4":"CHG_VIN","5":"BAT_P","6":"STDBY","7":"CHRG","8":"CHG_VIN","9":"GND"}),
  ("R3","R","24k",FP["R0603"],"C23352",{"1":"PROG","2":"GND"}),
  ("LED1","LED","ROD CHRG",FP["LED"],"C2286",{"2":"CHG_VIN","1":"LED1K"}),
  ("R4","R","1k",FP["R0603"],"",{"1":"LED1K","2":"CHRG"}),
  ("LED2","LED","GRON STDBY",FP["LED"],"C12624",{"2":"CHG_VIN","1":"LED2K"}),
  ("R21","R","1k",FP["R0603"],"",{"1":"LED2K","2":"STDBY"}),
  ("C2","C","10uF",FP["C0805"],"",{"1":"BAT_P","2":"GND"}),
  ("R22","R","33k",FP["R0603"],"C4216",{"1":"PROG","2":"PGA"}),
  ("R23","R","8.2k",FP["R0603"],"C25981",{"1":"PROG","2":"PGB"}),
  ("R24","R","2.2k",FP["R0603"],"C4190",{"1":"PROG","2":"PGC"}),
  ("Q7","NFET_DUAL","2N7002DW-7-F","Package_TO_SOT_SMD:SOT-363_SC-70-6","C83571",
    {"5":"MP0","4":"GND","3":"PGA","2":"MP1","1":"GND","6":"PGB"}),
  ("Q9","NFET_SOT23","2N7002",FP["SOT23"],"C8545",{"1":"MP2","2":"GND","3":"PGC"}),
  ("R25","R","100k",FP["R0603"],"",{"1":"MP0","2":"GND"}),
  ("R26","R","100k",FP["R0603"],"",{"1":"MP1","2":"GND"}),
  ("R27","R","100k",FP["R0603"],"",{"1":"MP2","2":"GND"}),
  ("R28","R","100k",FP["R0603"],"",{"1":"VBUS","2":"VBS"}),
  ("R29","R","150k",FP["R0603"],"C22807",{"1":"VBS","2":"GND"}),
 ]),
 ("BATTERI + CELLSKYDD + SHUNT", [
  ("J2","CONN_1x02","LIPO 3000mAh",FP["JSTPH"],"C173752",{"1":"CELL_P","2":"CELL_N"}),
  ("R5","SHUNT","10mR 1% 3W",FP["R2512"],"C2903468",{"1":"CELL_P","2":"BAT_P"}),
  ("R6","R","330R",FP["R0603"],"",{"1":"CELL_P","2":"DW_VCC"}),
  ("C3","C","100nF",FP["C0603"],"",{"1":"DW_VCC","2":"CELL_N"}),
  ("U3","DW01A","DW01A",FP["SOT236"],"C351410",
    {"5":"DW_VCC","6":"CELL_N","1":"G1","2":"VM","3":"G2","4":None}),
  ("R7","R","1k",FP["R0603"],"",{"1":"VM","2":"GND"}),
  ("Q1","M8205A","8205A",FP["SOT236"],"C351449",
    {"1":"CELL_N","6":"G1","3":"GND","4":"G2","2":"DD","5":"DD"}),
 ]),
 ("POWER PATH (USB-PRIORITET, IDEAL-DIOD-BETEENDE)", [
  ("D4","D_SCHOTTKY","SS54",FP["SMA"],"C22452",{"2":"VBUS","1":"SYS"}),
  ("Q2","PFET_SO8","AO4407A",FP["SO8"],"C2841482",
    {"1":"SYS","2":"SYS","3":"SYS","4":"VBUS","5":"BAT_P","6":"BAT_P","7":"BAT_P","8":"BAT_P"}),
  ("R8","R","100k",FP["R0603"],"",{"1":"VBUS","2":"GND"}),
  ("C4","C","22uF",FP["C0805"],"",{"1":"SYS","2":"GND"}),
  ("C5","C","22uF",FP["C0805"],"",{"1":"SYS","2":"GND"}),
 ]),
 ("STROMMATNING INA226 (I2C)", [
  ("U4","INA226","INA226",FP["VSSOP10"],"C49851",
    {"6":"3V3_MCU","10":"CELL_P","9":"BAT_P","8":"CELL_P","7":"GND",
     "4":"SDA","5":"SCL","3":"ALERT","2":"GND","1":"GND"}),
  ("R9","R","4.7k",FP["R0603"],"",{"1":"3V3_MCU","2":"SDA"}),
  ("R10","R","4.7k",FP["R0603"],"",{"1":"3V3_MCU","2":"SCL"}),
  ("R11","R","10k",FP["R0603"],"",{"1":"3V3_MCU","2":"ALERT"}),
  ("C6","C","100nF",FP["C0603"],"",{"1":"3V3_MCU","2":"GND"}),
 ]),
 ("ALLTID-PA LDO 3V3_MCU", [
  ("U5","HT7833","HT7833-A",FP["SOT89"],"C347195",{"2":"SYS","3":"3V3_MCU","1":"GND"}),
  ("C8","C","10uF",FP["C0805"],"",{"1":"SYS","2":"GND"}),
  ("C9","C","10uF",FP["C0805"],"",{"1":"3V3_MCU","2":"GND"}),
 ]),
 ("BUCK 3V3 3A TPS62823 + AVSTORNING", [
  ("FB2","FB","600R@100MHz 3A",FP["L1206"],"C317622",{"1":"SYS","2":"VIN_BK"}),
  ("C10","C","22uF",FP["C0805"],"",{"1":"VIN_BK","2":"GND"}),
  ("C11","C","100nF",FP["C0402"],"",{"1":"VIN_BK","2":"GND"}),
  ("U6","TPS62823","TPS62823DLCR",FP["VSON8"],"C2693497",
    {"7":"VIN_BK","1":"BUCK_EN","2":"FB_BK","3":"GND","5":"GND","6":"SW_BK","8":None,"4":"GND"}),
  ("L1","L","1uH SWPA4030S",FP["SWPA4030"],"C42193",{"1":"SW_BK","2":"3V3"}),
  ("R12","R","100k",FP["R0603"],"",{"1":"3V3","2":"FB_BK"}),
  ("R13","R","22.1k",FP["R0603"],"",{"1":"FB_BK","2":"GND"}),
  ("C12","C","120pF",FP["C0603"],"",{"1":"3V3","2":"FB_BK"}),
  ("R14","R","100k",FP["R0603"],"",{"1":"BUCK_EN","2":"GND"}),
  ("R16","R","2R SNUB DNP",FP["R0603"],"",{"1":"SW_BK","2":"SNUB"},True),
  ("C13","C","470pF DNP",FP["C0603"],"",{"1":"SNUB","2":"GND"},True),
  ("C14","C","22uF",FP["C0805"],"",{"1":"3V3","2":"GND"}),
  ("C15","C","22uF",FP["C0805"],"",{"1":"3V3","2":"GND"}),
  ("C16","C","100nF",FP["C0603"],"",{"1":"3V3","2":"GND"}),
 ]),
 ("LASTBRYTARE + PI-FILTER RADIO 1 (SX1262)", [
  ("Q3","PFET_SOT23","AO3401A",FP["SOT23"],"C15127",{"1":"G_RF1","2":"3V3","3":"SW_RF1"}),
  ("R17","R","100k",FP["R0603"],"",{"1":"3V3","2":"G_RF1"}),
  ("Q4","NFET_SOT23","2N7002",FP["SOT23"],"C8545",{"1":"EN_RF1","2":"GND","3":"G_RF1"}),
  ("R18","R","100k",FP["R0603"],"",{"1":"EN_RF1","2":"GND"}),
  ("FB3","FB","600R@100MHz",FP["L0805"],"C1017",{"1":"SW_RF1","2":"3V3_RF1"}),
  ("C17","C","10uF",FP["C0805"],"",{"1":"3V3_RF1","2":"GND"}),
  ("C18","C","100nF",FP["C0603"],"",{"1":"3V3_RF1","2":"GND"}),
  ("C19","C","100pF",FP["C0603"],"",{"1":"3V3_RF1","2":"GND"}),
  ("J4","CONN_1x04","RF-HAL: RF1 G RF2 G",HDR(4),"",{"1":"3V3_RF1","2":"GND","3":"3V3_RF2","4":"GND"}),
 ]),
 ("LASTBRYTARE + PI-FILTER RADIO 2 (SX1262)", [
  ("Q5","PFET_SOT23","AO3401A",FP["SOT23"],"C15127",{"1":"G_RF2","2":"3V3","3":"SW_RF2"}),
  ("R19","R","100k",FP["R0603"],"",{"1":"3V3","2":"G_RF2"}),
  ("Q6","NFET_SOT23","2N7002",FP["SOT23"],"C8545",{"1":"EN_RF2","2":"GND","3":"G_RF2"}),
  ("R20","R","100k",FP["R0603"],"",{"1":"EN_RF2","2":"GND"}),
  ("FB4","FB","600R@100MHz",FP["L0805"],"C1017",{"1":"SW_RF2","2":"3V3_RF2"}),
  ("C20","C","10uF",FP["C0805"],"",{"1":"3V3_RF2","2":"GND"}),
  ("C21","C","100nF",FP["C0603"],"",{"1":"3V3_RF2","2":"GND"}),
  ("C22","C","100pF",FP["C0603"],"",{"1":"3V3_RF2","2":"GND"}),
 ]),
 ("GPIO-EXPANDER TCA6408A (I2C 0x20): MPPT + EN + VBS, VSOL-DELARE", [
  ("U7","TCA6408A","TCA6408ARGTR","Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm","C181499",
    {"15":"3V3_MCU","14":"3V3_MCU","12":"SCL","13":"SDA","1":"RST_EXP","16":"GND",
     "6":"GND","17":"GND","2":"MP0","3":"MP1","4":"MP2","5":"EN_RF1",
     "7":"EN_RF2","8":"BUCK_EN","9":"VBS","10":"GND","11":"INT_EXP"}),
  ("C7","C","100nF",FP["C0603"],"",{"1":"3V3_MCU","2":"GND"}),
  ("R30","R","10k",FP["R0603"],"",{"1":"3V3_MCU","2":"RST_EXP"}),
  ("R31","R","10k",FP["R0603"],"",{"1":"3V3_MCU","2":"INT_EXP"}),
  ("R32","R","150k",FP["R0603"],"C22807",{"1":"CHG_VIN","2":"VSOL"}),
  ("R33","R","100k",FP["R0603"],"",{"1":"VSOL","2":"GND"}),
  ("JP1","JUMPER","VSOL-BYGEL","Jumper:SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm","",
    {"1":"VSOL","2":"VSOL_J"}),
 ]),
 ("TESTPUNKTER (FRI KOPPAR)", [
  ("TP1","TP","MP0","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"MP0"}),
  ("TP2","TP","MP1","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"MP1"}),
  ("TP3","TP","MP2","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"MP2"}),
  ("TP4","TP","EN_RF1","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"EN_RF1"}),
  ("TP5","TP","EN_RF2","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"EN_RF2"}),
  ("TP6","TP","BUCK_EN","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"BUCK_EN"}),
  ("TP7","TP","PROG","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"PROG"}),
  ("TP8","TP","VBS","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"VBS"}),
  ("TP9","TP","VSOL","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"VSOL"}),
  ("TP10","TP","SYS","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"SYS"}),
  ("TP11","TP","GND","TestPoint:TestPoint_Pad_D1.0mm","",{"1":"GND"}),
 ]),
 ("MCU-ANSLUTNING (nRF52840 CONNECT KIT: 3V3 + I2C + IRQ + VSOL)", [
  ("J7","CONN_1x10","MCU CTRL",HDR(10),"",
    {"1":"3V3","2":"GND","3":"3V3_MCU","4":"GND","5":"SDA","6":"SCL",
     "7":"ALERT","8":"INT_EXP","9":"VSOL_J","10":"RST_EXP"}),
 ]),
]

# ---------------- geometry helpers ----------------
def pin_offset(sdef, side, slot):
    hw, hh = sdef["hw"], sdef["hh"]
    if side == "L": return (-(hw+2.54), slot*2.54, 0)
    if side == "R": return (hw+2.54, slot*2.54, 180)
    if side == "T": return (slot*2.54, hh+2.54, 270)
    return (slot*2.54, -(hh+2.54), 90)

def fmt(v): return f"{v:.4f}".rstrip("0").rstrip(".")

# ---------------- lib symbol s-expr ----------------
def lib_symbol_sexpr(name, prefix):
    s = SYMS[name]
    hw, hh = s["hw"], s["hh"]
    p = []
    p.append(f'    (symbol "{prefix}{name}" (pin_names (offset 0.254)) (exclude_from_sim no) (in_bom yes) (on_board yes)')
    props = [("Reference", s["ref"], False), ("Value", name, False),
             ("Footprint", "", True), ("Datasheet", "", True), ("Description", s["desc"], True)]
    for i,(k,v,hide) in enumerate(props):
        h = " (hide yes)" if hide else ""
        p.append(f'      (property "{k}" "{v}" (at 0 {fmt(hh+2.54+i*2.54)} 0) (effects (font (size 1.27 1.27)){h}))')
    p.append(f'      (symbol "{name}_0_1"')
    p.append(f'        (rectangle (start {fmt(-hw)} {fmt(hh)}) (end {fmt(hw)} {fmt(-hh)}) (stroke (width 0.254) (type default)) (fill (type background)))')
    p.append('      )')
    p.append(f'      (symbol "{name}_1_1"')
    for (num, pname, side, slot) in s["pins"]:
        x, y, ang = pin_offset(s, side, slot)
        p.append(f'        (pin passive line (at {fmt(x)} {fmt(y)} {ang}) (length 2.54) (name "{pname}" (effects (font (size 1.02 1.02)))) (number "{num}" (effects (font (size 1.02 1.02)))))')
    p.append('      )')
    p.append('    )')
    return "\n".join(p)

# ---------------- placement ----------------
SLOT_W, ROW_H, MARGIN_X, MARGIN_Y, MAX_X = 33.02, 55.88, 25.4, 20.32, 810
placed = {}   # ref -> (x, y, inst)
texts = []
x, y = MARGIN_X, MARGIN_Y
for title, insts in BLOCKS:
    if x != MARGIN_X:
        x = MARGIN_X; y += ROW_H
    texts.append((title, x, y - 5.08))
    for inst in insts:
        ref, sname = inst[0], inst[1]
        need = SLOT_W
        if x + need > MAX_X:
            x = MARGIN_X; y += ROW_H
        sdef = SYMS[sname]
        cx = round((x + SLOT_W/2)/1.27)*1.27
        cy = round((y + ROW_H/2 - 7.62)/1.27)*1.27
        placed[ref] = (cx, cy, inst)
        x += need
    x = MARGIN_X; y += ROW_H

# ---------------- schematic ----------------
sch = []
sch.append(f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")')
sch.append(f'  (uuid "{ROOT}")')
sch.append('  (paper "A1")')
sch.append(f'  (title_block (title "LiPo power board - 2x SX1262 + MCU") (date "2026-07-31") (rev "A.1") (company "") (comment 1 "3000mAh LiPo, USB-C + sol, TP4056, INA226, TPS62823 3A") )')
sch.append('  (lib_symbols')
for name in SYMS:
    sch.append(lib_symbol_sexpr(name, f"{PROJ}:"))
sch.append('  )')

expected = {}  # net -> set of "ref.pin"
for title, tx, ty in texts:
    sch.append(f'  (text "{title}" (exclude_from_sim no) (at {fmt(tx)} {fmt(ty)} 0) (effects (font (size 2.54 2.54) (bold yes)) (justify left bottom)) (uuid "{uid("txt",title)}"))')

for ref, (X, Y, inst) in placed.items():
    sname, value, fp, lcsc, netmap = inst[1], inst[2], inst[3], inst[4], inst[5]
    dnp = len(inst) > 6 and inst[6]
    sdef = SYMS[sname]
    sch.append(f'  (symbol (lib_id "{PROJ}:{sname}") (at {fmt(X)} {fmt(Y)} 0) (unit 1)')
    sch.append(f'    (exclude_from_sim no) (in_bom {"no" if dnp else "yes"}) (on_board yes) (dnp {"yes" if dnp else "no"})')
    sch.append(f'    (uuid "{uid("sym",ref)}")')
    sch.append(f'    (property "Reference" "{ref}" (at {fmt(X+2.54)} {fmt(Y-sdef["hh"]-3.81)} 0) (effects (font (size 1.27 1.27)) (justify left)))')
    sch.append(f'    (property "Value" "{value}" (at {fmt(X+2.54)} {fmt(Y-sdef["hh"]-1.9)} 0) (effects (font (size 1.02 1.02)) (justify left)))')
    sch.append(f'    (property "Footprint" "{fp}" (at {fmt(X)} {fmt(Y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    sch.append(f'    (property "Datasheet" "" (at {fmt(X)} {fmt(Y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    sch.append(f'    (property "LCSC" "{lcsc}" (at {fmt(X)} {fmt(Y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    for (num, pname, side, slot) in sdef["pins"]:
        sch.append(f'    (pin "{num}" (uuid "{uid("pin",ref,num)}"))')
    sch.append(f'    (instances (project "{PROJ}" (path "/{ROOT}" (reference "{ref}") (unit 1))))')
    sch.append('  )')
    # labels / no-connects on pin endpoints
    for (num, pname, side, slot) in sdef["pins"]:
        px, py, ang = pin_offset(sdef, side, slot)
        ax, ay = X + px, Y - py
        net = netmap.get(num, None)
        if net is None:
            sch.append(f'  (no_connect (at {fmt(ax)} {fmt(ay)}) (uuid "{uid("nc",ref,num)}"))')
        else:
            rot = {0:0, 180:0, 270:90, 90:90}[ang]
            just = {"L":"right bottom","R":"left bottom","T":"left bottom","B":"right bottom"}[side]
            sch.append(f'  (label "{net}" (at {fmt(ax)} {fmt(ay)} {rot}) (effects (font (size 1.02 1.02)) (justify {just})) (uuid "{uid("lbl",ref,num)}"))')
            if not dnp:
                expected.setdefault(net, set()).add(f"{ref}.{num}")

sch.append(f'  (sheet_instances (path "/" (page "1")))')
sch.append(')')

os.makedirs(OUT, exist_ok=True)
with open(f"{OUT}/{PROJ}.kicad_sch", "w") as f:
    f.write("\n".join(sch) + "\n")

# standalone symbol lib
lib = ['(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") (generator_version "9.0")']
for name in SYMS:
    lib.append(lib_symbol_sexpr(name, ""))
lib.append(')')
with open(f"{OUT}/{PROJ}.kicad_sym", "w") as f:
    f.write("\n".join(lib) + "\n")

with open(f"{OUT}/sym-lib-table", "w") as f:
    f.write(f'(sym_lib_table (version 7)\n  (lib (name "{PROJ}")(type "KiCad")(uri "${{KIPRJMOD}}/{PROJ}.kicad_sym")(options "")(descr "project symbols"))\n)\n')

pro = {"meta":{"filename":f"{PROJ}.kicad_pro","version":3},
 "board":{"design_settings":{},"layer_presets":[],"viewports":[]},
 "libraries":{"pinned_footprint_libs":[],"pinned_symbol_libs":[]},
 "net_settings":{"classes":[{"name":"Default","clearance":0.127,"track_width":0.25,
   "via_diameter":0.6,"via_drill":0.3,"microvia_diameter":0.3,"microvia_drill":0.1,
   "diff_pair_width":0.2,"diff_pair_gap":0.25,"diff_pair_via_gap":0.25,
   "bus_width":12,"line_style":0,"pcb_color":"rgba(0, 0, 0, 0.000)","schematic_color":"rgba(0, 0, 0, 0.000)","wire_width":6}]},
 "schematic":{"annotate_start_num":0,"drawing":{},"legacy_lib_dir":"","legacy_lib_list":[]},
 "sheets":[[ROOT,"Root"]],"text_variables":{}}
if not os.path.exists(f"{OUT}/{PROJ}.kicad_pro"):
    with open(f"{OUT}/{PROJ}.kicad_pro", "w") as f:
        json.dump(pro, f, indent=2)

with open(f"{OUT}/expected_nets.json", "w") as f:
    json.dump({k: sorted(v) for k, v in expected.items()}, f, indent=1)

print(f"OK: {len(placed)} components, {len(expected)} nets")
