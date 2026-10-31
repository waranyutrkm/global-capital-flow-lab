# พิมพ์เขียวตรรกะการตัดสินใจตายตัว 100% (Deterministic Quant Decision Blueprint)
## ระบบสแกนและจัดสรรกระแสเงินทุนโลก (Global Capital Allocation Engine)

> **มาตรฐานการปฏิบัติงาน:** ปราศจากดุลยพินิจของมนุษย์ (Zero-Discretion), คำนวณจากราคาปิดวันทำการล่าสุด (Causal Close t-1), และทำงานอัตโนมัติผ่าน GitHub Actions

---

### 1. จักรวาลสินทรัพย์ 14 ตัวแทน (80% มูลค่าตลาดทุนโลก)

| หมวดหมู่ทางเศรษฐกิจ | สินทรัพย์หลัก | สินทรัพย์ดาวเทียม / เปรียบเทียบ | บทบาทเชิงกลยุทธ์ |
|---|---|---|---|
| **Core Equities (หุ้นแกนนำ)** | `QQQ` (Nasdaq 100) | `SPY` (S&P 500) | ตัวขับเคลื่อนผลตอบแทนหลัก (Alpha Driver) |
| **Cash Hurdle (ตัวกรองเงินสด)** | `BIL` (0-3M T-Bills) | — | เกณฑ์ขั้นต่ำในการลงทุน (Hurdle Rate) |
| **Haven Pool (หลุมหลบภัย)** | `DBC` (Commodities), `UUP` (USD) | `GLD` (Gold), `TLT` (20Y+ Treasury) | ซับสภาพคล่องเมื่อหุ้นมีความเสี่ยง |
| **Global Context (บริบทโลก)** | `EFA`, `EEM`, `VNQ` | `IEF`, `BND`, `HYG`, `FXY` | สแกนสภาพคล่องทั่วโลก 5 ทวีป |

---

### 2. สูตรทางคณิตศาสตร์ที่ใช้ตัดสินใจ (Deterministic Math)

#### ก. คะแนนโมเมนตัม 3 มิติเวลา (Multi-Horizon Score)
คำนวณสำหรับทุกลำดับสินทรัพย์ $i$ โดยใช้น้ำหนักถ่วงแบบลดหลั่น:
$$\text{Score}_i = 0.40 \times \text{Ret}_{60d}(i) + 0.35 \times \text{Ret}_{120d}(i) + 0.25 \times \text{Ret}_{252d}(i)$$
- **60 วัน (Quarterly):** น้ำหนัก 40% ตัดปัญหาความล้าหลังของ `SMA200` ตอบสนองเร็วกว่า 3 เท่า
- **120 วัน (Half-Year):** น้ำหนัก 35% กรองความผันผวนชั่วคราว
- **252 วัน (Annual):** น้ำหนัก 25% เสาหลักเทรนด์โครงสร้าง

#### ข. ความผันผวนจริงระดับปี (20-Day Annualized Realized Volatility)
$$\sigma_{20d}(i) = \text{std}\left(\frac{P_t - P_{t-1}}{P_{t-1}}\right)_{20\text{ bars}} \times \sqrt{252} \times 100$$

#### ค. สัดส่วนลงทุนควบคุมความเสี่ยง (Volatility-Targeted Sizing)
$$\text{Target Exposure} = \min\left(1.50, \frac{20.0\%}{\sigma_{20d}(\text{Core})}\right)$$

---

### 3. ตรรกะการตัดสินใจตายตัวสำหรับนักลงทุน (Deterministic State Machine)

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

#### ตารางเงื่อนไขและคำสั่งปฏิบัติ (Actionable Rules)

| ลำดับเงื่อนไข | สภาวะตลาด | คำสั่งต่อนักลงทุน (Execution Order) | เครื่องมือที่ใช้จริงในพอร์ต |
|---|---|---|---|
| **เคสที่ 1: กระทิงเสถียร** | `Score(QQQ) > BIL` และ $\sigma_{20d} \le 13.3\%$ | **ถือหุ้นเต็มเพดาน 150%** | ถือ `QQQ` 50% + `QLD (2x QQQ)` 50% |
| **เคสที่ 2: กระทิงผันผวน** | `Score(QQQ) > BIL` และ $13.3\% < \sigma_{20d} < 20.0\%$ | **ถือหุ้นตามสัดส่วน $w = 20\% / \sigma$** | ส่วนที่เหลือ ($1 - w$) ซื้อ Top Haven หรือถือ `BIL` |
| **เคสที่ 3: หุ้นอ่อนแรง** | `Score(QQQ) > BIL` แต่ $\sigma_{20d} \ge 20.0\%$ | **ลดหุ้นลงต่ำกว่า 100%** | ถือ `QQQ` ตามขนาด Vol, เงินส่วนใหญ่ไป Havens |
| **เคสที่ 4: ตลาดหลุดเกณฑ์ (ปัจจุบัน)** | `Score(QQQ) <= Score(BIL)` | **ขายล้างหุ้น QQQ ออกทั้งหมด (0%)** | **หมุนเงิน 100% ไปซื้อ `DBC` 28.7% + `UUP` 71.3%** |
| **เคสที่ 5: วิกฤตล้างโลก (Cash Only)** | ทุกสินทรัพย์ในจักรวาล `Score <= Score(BIL)` | **ถือเงินสด 100%** | ย้ายเงินทั้งหมดเข้า `BIL` (พันธบัตร 0-3 เดือน) |

---

### 4. ตัวอย่างการตัดสินใจจริง ณ สภาพตลาดปัจจุบัน (30 ต.ค. 2026)

- `Score(BIL)` = **1.88 คะแนน** (เกณฑ์เงินสด)
- `Score(QQQ)` = **-0.08 คะแนน** (น้อยกว่า BIL &rarr; **เข้าเคสที่ 4: ห้ามถือ QQQ เด็ดขาด**)
- Top Havens ที่ชนะเงินสด:
  1. `DBC` (Commodities/Energy): Score 22.70, Vol 11.62%
  2. `UUP` (US Dollar Index): Score 5.02, Vol 4.67%
- การถ่วงน้ำหนัก Inverse-Volatility:
  - น้ำหนัก `UUP` = $\frac{1/4.67}{1/4.67 + 1/11.62} = \mathbf{71.33\%}$
  - น้ำหนัก `DBC` = $\frac{1/11.62}{1/4.67 + 1/11.62} = \mathbf{28.67\%}$

**คำสั่งสำหรับนักลงทุนวันจันทร์:** ขาย QQQ ทั้งหมด, ซื้อ UUP 71.3% และซื้อ DBC 28.7% พอร์ตจะไม่โดน Drawdown ของ Tech Sell-off แต่จะได้ผลตอบแทนจากดอลลาร์และสินค้าโภคภัณฑ์แทน

---

### 5. กลไกการรันอัตโนมัติบน GitHub (Automated Architecture)

ระบบถูกฝังไฟล์และรันอัตโนมัติ 100% ด้วย 3 องค์ประกอบใน Repository:

1. **Engine Script (`engine_global_flow_decisions.py`):**
   - ดึงข้อมูล Adjusted Close อัตโนมัติ ปราศจาก Look-ahead bias
   - คำนวณคะแนน Multi-horizon, Vol-target, และสัดส่วนพอร์ต
   - ผลิตไฟล์ `signals_latest.json` และ `allocation_orders.csv`
2. **GitHub Actions Workflow (`.github/workflows/global_capital_flow.yml`):**
   - รันอัตโนมัติทุกวันทำการเวลา 21:30 UTC (หลังตลาดสหรัฐฯ ปิด)
   - Commit & Push ผลการคำนวณล่าสุดขึ้น GitHub โดยอัตโนมัติ
3. **Interactive Visual Dashboard (`global_flow_scanner_preview.html`):**
   - นำข้อมูลจาก JSON ไปวาดแผนที่การไหลของเงินทุนโลกแบบ Motion Graphic
