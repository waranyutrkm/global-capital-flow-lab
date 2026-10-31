# Global Capital Flow & Allocation Engine (Global Flow Lab)
> **Deterministic Institutional Quant Terminal & Automated Macro Allocation System**  
> ครอบคลุม 80% มูลค่าตลาดทุนโลก ($300T) · ไม่พึ่งพาเส้น SMA200 ล้าหลัง · ตรวจสอบผ่าน Rolling Windows 226 หน้าต่าง (2007–2026)

[![Global Capital Flow Engine](https://github.com/waranyutrkm/global-capital-flow-lab/actions/workflows/sync_signals.yml/badge.svg)](https://github.com/waranyutrkm/global-capital-flow-lab/actions/workflows/sync_signals.yml)
[![Live Dashboard](https://img.shields.io/badge/Live_Dashboard-GitHub_Pages-06b6d4?style=flat&logo=github)](https://waranyutrkm.github.io/global-capital-flow-lab/)
[![Design Standard](https://img.shields.io/badge/Design-Obsidian_Quant_Terminal-10b981?style=flat)](DESIGN.md)

---

## 1. ภาพรวมระบบ (System Overview)

`global-capital-flow-lab` คือระบบวิเคราะห์และจัดสรรเงินทุนระดับมหภาคแบบ **100% Deterministic (ตรรกะตายตัว ปราศจากดุลยพินิจของมนุษย์)** ออกแบบมาเพื่อตอบคำถามสำคัญของนักลงทุนระดับสถาบัน:

> **"ตอนนี้เงินโลกกำลังหนีไปไหน และควรปรับพอร์ตตามอย่างไร?"**

ระบบติดตาม 14 ตัวแทนสินทรัพย์หลัก (ETFs) ที่ครอบคลุม **80% ของมูลค่าตลาดทุนโลก (~$300 Trillion)** ครอบคลุม 4 เสาหลัก:
1. **ตราสารทุนโลก (Global Equities - 35%):** `SPY` (S&P 500 Core), `QQQ` (Tech Growth), `EFA` (Developed ex-US), `EEM` (Emerging Markets)
2. **ตราสารหนี้ & เครดิต (Fixed Income - 40%):** `TLT` (20Y+ Treasury), `IEF` (7-10Y Benchmark), `BND` (Total Bond), `HYG` (High Yield Credit)
3. **สินค้าโภคภัณฑ์ & ทรัพย์สินจริง (Real Assets - 10%):** `DBC` (Commodities/Energy), `GLD` (Physical Gold), `VNQ` (Real Estate REITs)
4. **เงินสด & ค่าเงินสำรอง (Currencies & Liquidity - 15%):** `BIL` (0-3M T-Bills / Cash Hurdle), `UUP` (US Dollar Index), `FXY` (Japanese Yen)

---

## 2. ทำไมต้องเลิกใช้เส้น `SMA200`? (The SMA200 Flaw)

การใช้เส้นค่าเฉลี่ย 200 วัน (`SMA200`) เป็นตัวตัดขาดทุนแบบเปิด/ปิด (Binary 0/1 Cutoff) ก่อให้เกิดปัญหาใหญ่ 3 ประการ:
1. **ความล้าหลังระดับ 10 เดือน (~200 วันทำการ):** กว่าราคาจะตัดหลุดเส้น สินทรัพย์ร่วงลงไปแล้ว 12%–18% สั่งขายที่ก้นเหว (Selling into Exhaustion)
2. **Whipsaw รุนแรงตอนตลาดเด้งกลับ (V-Shape):** ตอนตลาดฟื้นตัว ราคาจะพุ่งขึ้นไปแล้ว 15%–20% กว่าจะตัดกลับขึ้นเหนือเส้น ทำให้ตกรอบการเด้งคืนทุนที่ดีที่สุด
3. **ผลตอบแทนตกต่ำลงชัดเจน:** จากการทดสอบในงานวิจัย การใส่ตัวกรอง `SMA200` บน QQQ ทำให้ **CAGR ลดลงจาก 16.17% เหลือเพียง 12.48% (แพ้ Buy & Hold ถึง 3.7pp ต่อปี!)**

#### ตัวอย่างสภาพตลาดจริง (30 ต.ค. 2026):
- `QQQ` ยังอยู่เหนือเส้น `SMA200` (+1.79%)
- แต่ความเป็นจริง: ราคาร่วงลงมาแล้ว **-9.11%** จากจุดสูงสุด 40 วัน, ผลตอบแทน 20 วันติดลบ **-7.88%**, และความผันผวนพุ่งขึ้นแตะ **22.64%**
- หากใช้ `SMA200` พอร์ตจะนั่งเฉยๆ รับแรงกระแทกเต็ม 100% แต่โมเดลใหม่ของระบบตรวจพบการรั่วไหลและสั่งลด Exposure ออกล่วงหน้าเรียบร้อยแล้ว

---

## 3. สถาปัตยกรรมคัดกรองโมเมนตัมหลายมิติเวลา (Multi-Horizon Architecture)

### ก. สูตรคะแนนโมเมนตัม 3 มิติเวลา (Multi-Horizon Score)
$$\text{Score}_i = 0.40 \times \text{Ret}_{60d}(i) + 0.35 \times \text{Ret}_{120d}(i) + 0.25 \times \text{Ret}_{252d}(i)$$
- **60 วัน (น้ำหนัก 40%):** ตอบสนองเร็วกว่า `SMA200` ถึง 3 เท่า จับรอบหมุนเงินไตรมาสได้ทันท่วงที โดยไม่โดน Day Noise หลอก
- **120 วัน (น้ำหนัก 35%) & 252 วัน (น้ำหนัก 25%):** กรองความผันผวนชั่วคราว ยืนยันเทรนด์โครงสร้างระดับปี

### ข. การปรับขนาดพอร์ตด้วยความผันผวนจริง (Continuous Realized Volatility Targeting)
$$\text{Target Exposure} = \min\left(1.50, \frac{20.0\%}{\sigma_{20d}(\text{Core})}\right)$$
- ปรับสัดส่วนเป็นเส้นโค้งต่อเนื่องตาม Moreira & Muir (2017)
- ตลาดนิ่งขยายได้ถึง 1.50x (ถือ `QQQ 1x` 50% + `QLD 2x` 50% โดยไม่ต้องใช้ Margin ปราศจาก Margin Call)
- ตลาดเริ่มผันผวน (เช่น Vol 22.64% วันนี้) ระบบรินลดน้ำหนักลงเหลือ 0.88x ทันทีในสัปดาห์แรก

---

## 4. แผนผังการตัดสินใจตายตัวสำหรับนักลงทุน (Deterministic State Machine)

```
[ทุกวันเสาร์ 07:00 น. เวลาไทย (หลังตลาดสหรัฐฯ ปิดวันศุกร์)]
                           │
                           ▼
              ตรวจสอบ Score(QQQ) vs Score(BIL)
              ────────────────────────────────
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
     Score(QQQ) > Score(BIL)       Score(QQQ) <= Score(BIL)
    [สภาวะที่ 1: หุ้นแข็งแกร่ง]       [สภาวะที่ 2: วิกฤต / หุ้นรั่วไหล]
            │                             │
            ▼                             ▼
   คำนวณ Exposure QQQ            ตัดสิทธิ์ QQQ ออกจากพอร์ตทันที
  = min(1.5, 20% / Vol20D)       Weight(QQQ) = 0.0% (Exit/ห้ามถือ)
            │                             │
    ┌───────┴───────┐                     ▼
    ▼               ▼             หมุนเงิน 100% สู่ Top Havens
Exp >= 1.0       Exp < 1.0         ที่ Score > BIL ด้วย Inverse-Vol:
(ตลาดนิ่ง)      (ตลาดผันผวน)          Weight_k ∝ (1 / Vol20D_k)
    │               │                     │
    ▼               ▼                     ▼
ถือ QQQ+QLD     ถือ QQQ ตามสัดส่วน        ตัวอย่างวันนี้:
เต็มเพดาน       เงินที่เหลือไป Havens      DBC = 28.7%, UUP = 71.3%
```

---

## 5. ผลการทดสอบเชิงประจักษ์ (Quantitative Results)

### ก. ผลตอบแทนรอบเต็ม (2007–2026)

| กลยุทธ์ | CAGR (%/ปี) | Sharpe Ratio | Max Drawdown (MDD) | OOS CAGR (2017–2026) | OOS MDD |
|---|---|---|---|---|---|
| **ซื้อและถือ QQQ (Buy & Hold)** | 16.17% | 0.72 | -53.4% | 20.99% | -35.1% |
| **โมเดลกลยุทธ์ (A vt20 cap 1.5)** | **18.01%** | **0.85** | **-34.7%** | **21.89%** | **-27.3%** |
| กลยุทธ์ไม่ใช้ Leverage (vt25 cap 1.0) | 16.63% | 0.83 | -37.1% | 19.63% | -30.9% |
| กองทุนรวมไทย (ไม่มี Lev, THB, ER 1%) | 14.60% | 0.65 | **-32.2%** | 17.39% | **-32.3%** |

### ข. สถิติ Rolling Windows 226 หน้าต่าง (เลื่อนจุดเริ่มทุกเดือน 1–10 ปี)
- **หน้าต่าง 3 ปี (202 หน้าต่าง):** ชนะ QQQ ด้าน CAGR 68% และ **โอกาสขาดทุนของกลยุทธ์เป็น 0%** (เทียบกับ QQQ ขาดทุน 3%)
- **หน้าต่าง 5 ปี (178 หน้าต่าง):** ชนะ QQQ ด้าน CAGR **78%** ของทุกช่วงเวลา
- **หน้าต่าง 10 ปี (118 หน้าต่าง):** ชนะ QQQ ด้าน CAGR **86%** ของทุกช่วงเวลา และ **MDD ดีกว่า QQQ ถึง 99%**
- **การตัด Lost Decade:** ผลตอบแทนระดับแย่สุด 10% แรก (p10) ของกลยุทธ์อยู่ที่ **16.8% ต่อปี เทียบกับ QQQ ที่ 13.3% ต่อปี (+3.5pp)**

---

## 6. โครงสร้างไฟล์ใน Repository

```
.
├── .github/
│   └── workflows/
│       └── sync_signals.yml       # GitHub Actions รันคำนวณและอัปเดตอัตโนมัติ
├── index.html                     # Interactive Constellation Map & Dashboard
├── engine.py                      # 100% Deterministic Quant Decision Engine
├── signals_latest.json            # ผลการคำนวณและสัญญาณพอร์ตล่าสุด
├── allocation_orders.csv          # ตารางคำสั่งซื้อขายต่อนักลงทุน (Actionable Sheet)
├── GLOBAL_FLOW_DETERMINISTIC_RULES_TH.md # พิมพ์เขียวกฎการตัดสินใจฉบับสมบูรณ์
├── DESIGN.md                      # Obsidian Quant Terminal Design Tokens
├── AGENTS.md                      # กฎข้อบังคับการออกแบบ (Zero-Emoji & WCAG 2.2 AA)
└── requirements.txt               # yfinance, pandas, numpy
```

---

## 7. วิธีเปิดใช้งานและรันบนเครื่อง Local

```bash
# 1. โคลนคลังโค้ด
git clone https://github.com/waranyutrkm/global-capital-flow-lab.git
cd global-capital-flow-lab

# 2. ติดตั้ง Dependencies
pip install -r requirements.txt

# 3. รันการคำนวณหาสัญญาณและใบสั่งซื้อขายล่าสุด
python engine.py

# 4. เปิด Interactive Dashboard
open index.html
```

---

## 8. License & Institutional Disclaimer

จัดทำขึ้นเพื่อการศึกษาและการวิจัยเชิงปริมาณ (Quantitative Research) ภายใต้ใบอนุญาต MIT License ไม่ใช่คำแนะนำการลงทุนส่วนบุคคล การลงทุนในสินทรัพย์มีความเสี่ยง ผู้ลงทุนควรทำความเข้าใจข้อกำหนดความเสี่ยงและกฎการกระจายความเสี่ยงอย่างรอบคอบ
