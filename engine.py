#!/usr/bin/env python3
"""
Global Capital Flow & Allocation Engine (Deterministic Institutional Decision Engine)
=====================================================================================
Standards:
- Zero-Discretion Causal Signal Architecture (t-1 Close)
- Multi-Horizon Momentum Composite + Continuous Realized Volatility Targeting
- Cash Hurdle (BIL) Disqualification Gate
- Inverse-Volatility Haven Rotation

Designed for automated execution via GitHub Actions.
Outputs:
- signals_latest.json
- allocation_orders.csv
"""

import json
import os
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf

# ---------------------------------------------------------
# 1. PARAMETERS & ASSET UNIVERSE CONFIGURATION
# ---------------------------------------------------------
CORE_EQUITIES = ["QQQ", "SPY"]
HAVEN_POOL = ["DBC", "UUP", "GLD", "TLT"]
BENCHMARK_CASH = "BIL"
SATELLITE_ASSETS = ["EFA", "EEM", "VNQ", "IEF", "BND", "HYG", "FXY"]

ALL_TICKERS = list(set(CORE_EQUITIES + HAVEN_POOL + [BENCHMARK_CASH] + SATELLITE_ASSETS))

TARGET_VOLATILITY = 20.0  # Annualized volatility target (%)
VOL_LOOKBACK_DAYS = 20    # Realized volatility window
MOM_WEIGHTS = {
    60: 0.40,   # Quarterly intermediate cycle
    120: 0.35,  # Half-year trend stability
    252: 0.25   # Annual macro structural trend
}
MAX_CORE_LEVERAGE = 1.50  # Cap exposure for synthetic levered ETF
HIGH_LOOKBACK_DAYS = 40   # Donchian High proximity window
DEADBAND_REBALANCE = 0.05 # Minimum 5% delta weight to trigger trade

# ---------------------------------------------------------
# 2. DATA ACQUISITION & FEATURE ENGINEERING
# ---------------------------------------------------------
def fetch_and_calculate_metrics():
    utc_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"[{utc_now}] Fetching 2Y daily data for {len(ALL_TICKERS)} macro ETFs...")
    raw = yf.download(ALL_TICKERS, period="2y", progress=False)["Close"]
    raw = raw.dropna(axis=0, how="all")

    latest_date = raw.index[-1].strftime("%Y-%m-%d")
    latest_prices = raw.iloc[-1]

    # Returns across multi-horizons
    ret20 = (raw.iloc[-1] / raw.iloc[-21] - 1) * 100
    ret60 = (raw.iloc[-1] / raw.iloc[-61] - 1) * 100
    ret120 = (raw.iloc[-1] / raw.iloc[-121] - 1) * 100
    ret252 = (raw.iloc[-1] / raw.iloc[-253] - 1) * 100

    # Composite Multi-Horizon Score
    scores = (
        MOM_WEIGHTS[60] * ret60 +
        MOM_WEIGHTS[120] * ret120 +
        MOM_WEIGHTS[252] * ret252
    )

    # 20-Day Annualized Realized Volatility
    vol20 = raw.pct_change().iloc[-VOL_LOOKBACK_DAYS:].std() * np.sqrt(252) * 100

    # 40-Day Donchian High Proximity
    high40 = raw.iloc[-HIGH_LOOKBACK_DAYS:].max()
    dist_high40 = (latest_prices / high40 - 1) * 100

    # Distance to SMA200 (Diagnostic only)
    sma200 = raw.rolling(200).mean().iloc[-1]
    dist_sma200 = (latest_prices / sma200 - 1) * 100

    metrics_df = pd.DataFrame({
        "Price": latest_prices.round(2),
        "Ret20d": ret20.round(2),
        "Ret60d": ret60.round(2),
        "Ret120d": ret120.round(2),
        "Ret252d": ret252.round(2),
        "Score": scores.round(2),
        "Vol20d": vol20.round(2),
        "DistHigh40": dist_high40.round(2),
        "DistSMA200": dist_sma200.round(2)
    }).sort_values(by="Score", ascending=False)

    return latest_date, metrics_df

# ---------------------------------------------------------
# 3. DETERMINISTIC DECISION LOGIC: 2 FORMAL STRATEGIES
# ---------------------------------------------------------
def generate_deterministic_allocation(latest_date, df):
    cash_hurdle_score = df.loc[BENCHMARK_CASH, "Score"]
    
    # -------------------------------------------------------------------------
    # STRATEGY 1: QQQ-Core Vol-Managed + Haven Rotation (Direct QQQ Replacement)
    # -------------------------------------------------------------------------
    # Rule 1: Does QQQ pass Cash Hurdle?
    qqq_score = df.loc["QQQ", "Score"]
    qqq_vol = df.loc["QQQ", "Vol20d"]
    qqq_qualifies = (qqq_score > cash_hurdle_score)

    weights_qqq_strategy = {ticker: 0.0 for ticker in ALL_TICKERS}
    
    if qqq_qualifies:
        raw_qqq_exp = TARGET_VOLATILITY / qqq_vol
        qqq_exposure = float(np.clip(raw_qqq_exp, 0.0, MAX_CORE_LEVERAGE))
        weights_qqq_strategy["QQQ"] = round(qqq_exposure, 4)
        rem_qqq_budget = max(0.0, 1.0 - min(1.0, qqq_exposure))
    else:
        qqq_exposure = 0.0
        weights_qqq_strategy["QQQ"] = 0.0
        rem_qqq_budget = 1.0  # 100% rotated into safe havens

    # Qualifying Havens: Score > Cash Hurdle (BIL)
    valid_havens = [h for h in HAVEN_POOL if df.loc[h, "Score"] > cash_hurdle_score]
    valid_havens_sorted = sorted(valid_havens, key=lambda h: df.loc[h, "Score"], reverse=True)[:2]

    if rem_qqq_budget > 0.001:
        if valid_havens_sorted:
            inv_vols = [1.0 / df.loc[h, "Vol20d"] for h in valid_havens_sorted]
            sum_inv = sum(inv_vols)
            for h, inv_v in zip(valid_havens_sorted, inv_vols):
                weights_qqq_strategy[h] = round((inv_v / sum_inv) * rem_qqq_budget, 4)
        else:
            weights_qqq_strategy[BENCHMARK_CASH] = round(rem_qqq_budget, 4)

    # -------------------------------------------------------------------------
    # STRATEGY 2: Global Macro Alpha Rotation (Best of SPY/QQQ + Havens)
    # -------------------------------------------------------------------------
    valid_equities = [eq for eq in CORE_EQUITIES if df.loc[eq, "Score"] > cash_hurdle_score]
    weights_macro_strategy = {ticker: 0.0 for ticker in ALL_TICKERS}

    if valid_equities:
        selected_core = max(valid_equities, key=lambda eq: df.loc[eq, "Score"])
        core_vol = df.loc[selected_core, "Vol20d"]
        core_exposure = float(np.clip(TARGET_VOLATILITY / core_vol, 0.0, MAX_CORE_LEVERAGE))
        weights_macro_strategy[selected_core] = round(core_exposure, 4)
        rem_macro_budget = max(0.0, 1.0 - min(1.0, core_exposure))
    else:
        selected_core = "NONE (FULL DEFENSE)"
        core_exposure = 0.0
        rem_macro_budget = 1.0

    if rem_macro_budget > 0.001:
        if valid_havens_sorted:
            inv_vols = [1.0 / df.loc[h, "Vol20d"] for h in valid_havens_sorted]
            sum_inv = sum(inv_vols)
            for h, inv_v in zip(valid_havens_sorted, inv_vols):
                weights_macro_strategy[h] = round((inv_v / sum_inv) * rem_macro_budget, 4)
        else:
            weights_macro_strategy[BENCHMARK_CASH] = round(rem_macro_budget, 4)

    # -------------------------------------------------------------------------
    # Actionable Trade Execution Instructions for the Investor
    # -------------------------------------------------------------------------
    qqq_plan = []
    if qqq_exposure > 1.0:
        w_2x = round(qqq_exposure - 1.0, 4)
        w_1x = round(2.0 - qqq_exposure, 4)
        qqq_plan.append({"Instrument": "QQQ (1x Core)", "Weight": f"{w_1x*100:.1f}%", "Action": "ALLOCATE"})
        qqq_plan.append({"Instrument": "QLD (2x Booster)", "Weight": f"{w_2x*100:.1f}%", "Action": "ALLOCATE"})
    elif qqq_exposure > 0:
        qqq_plan.append({"Instrument": "QQQ (1x Core)", "Weight": f"{qqq_exposure*100:.1f}%", "Action": "ALLOCATE"})
    else:
        qqq_plan.append({"Instrument": "QQQ (1x Core)", "Weight": "0.0%", "Action": "EXIT / ZERO EXPOSURE (Score < BIL)"})

    for h in valid_havens_sorted:
        if weights_qqq_strategy[h] > 0:
            qqq_plan.append({
                "Instrument": f"{h} (Haven Rotation)",
                "Weight": f"{weights_qqq_strategy[h]*100:.1f}%",
                "Action": f"BUY / HOLD (Score: {df.loc[h, 'Score']:.2f} > BIL {cash_hurdle_score:.2f})"
            })

    if weights_qqq_strategy[BENCHMARK_CASH] > 0:
        qqq_plan.append({"Instrument": "BIL (Cash T-Bills)", "Weight": f"{weights_qqq_strategy[BENCHMARK_CASH]*100:.1f}%", "Action": "HOLD CASH"})

    output_payload = {
        "as_of_date": latest_date,
        "cash_hurdle_bil_score": cash_hurdle_score,
        "valid_havens": valid_havens_sorted,
        "strategy_qqq_rotation": {
            "regime": "RISK-OFF ROTATION TO HAVENS" if qqq_exposure == 0 else ("EXPANSION" if qqq_exposure >= 1.0 else "CAUTION"),
            "qqq_score": qqq_score,
            "qqq_vol20d": qqq_vol,
            "qqq_exposure": qqq_exposure,
            "target_weights": weights_qqq_strategy,
            "execution_plan": qqq_plan
        },
        "strategy_global_macro": {
            "selected_core": selected_core,
            "core_exposure": core_exposure,
            "target_weights": weights_macro_strategy
        },
        "full_metrics": df.to_dict(orient="index")
    }

    return output_payload, weights_qqq_strategy, weights_macro_strategy

# ---------------------------------------------------------
# 4. ORDER GENERATION & HISTORICAL TIME SERIES PERSISTENCE
# ---------------------------------------------------------
# 4. HISTORICAL ALLOCATION TIME SERIES (2008–2026 FULL HISTORY)
# ---------------------------------------------------------
EQUITY_SLEEVE = ['SPY', 'QQQ', 'EFA', 'EEM', 'VNQ']
CREDIT_SLEEVE = ['HYG', 'BND', 'IEF']
COMMODITY_SLEEVE = ['DBC', 'GLD']
HAVEN_SLEEVE = ['UUP', 'TLT', 'BIL', 'FXY']

def generate_historical_allocations(raw_data):
    """
    Generates weekly historical allocation time series and sleeve-level breadth
    across the entire mutual history (2008–2026).
    """
    returns_1d = raw_data.pct_change(fill_method=None)
    ret60 = raw_data.pct_change(60, fill_method=None) * 100
    ret120 = raw_data.pct_change(120, fill_method=None) * 100
    ret252 = raw_data.pct_change(252, fill_method=None) * 100
    vol20 = returns_1d.rolling(20).std() * np.sqrt(252) * 100

    scores = (
        MOM_WEIGHTS[60] * ret60 +
        MOM_WEIGHTS[120] * ret120 +
        MOM_WEIGHTS[252] * ret252
    )

    weekly_dates = raw_data.resample('W-FRI').last().dropna(how='all').index
    valid_dates = [d for d in weekly_dates if d >= pd.Timestamp('2008-06-01') and d in raw_data.index]
    records = []

    for dt in valid_dates:
        dt_str = dt.strftime('%Y-%m-%d')
        bil_score = scores.loc[dt, 'BIL']
        qqq_score = scores.loc[dt, 'QQQ']
        qqq_vol = max(8.0, vol20.loc[dt, 'QQQ']) if not np.isnan(vol20.loc[dt, 'QQQ']) else 20.0

        # Sleeve-Level Multi-Horizon Cash-Hurdle Breadth (MCHB)
        eq_b = sum(scores.loc[dt, t] > bil_score for t in EQUITY_SLEEVE) / len(EQUITY_SLEEVE) * 100
        cr_b = sum(scores.loc[dt, t] > bil_score for t in CREDIT_SLEEVE) / len(CREDIT_SLEEVE) * 100
        co_b = sum(scores.loc[dt, t] > bil_score for t in COMMODITY_SLEEVE) / len(COMMODITY_SLEEVE) * 100
        ha_b = sum(scores.loc[dt, t] > bil_score for t in HAVEN_SLEEVE) / len(HAVEN_SLEEVE) * 100
        flow_b = sum(scores.loc[dt, t] > bil_score for t in ALL_TICKERS) / len(ALL_TICKERS) * 100

        w = {'QQQ': 0.0, 'UUP': 0.0, 'DBC': 0.0, 'GLD': 0.0, 'TLT': 0.0, 'BIL': 0.0}

        if qqq_score > bil_score:
            raw_exp = TARGET_VOLATILITY / qqq_vol
            exp = float(np.clip(raw_exp, 0.0, MAX_CORE_LEVERAGE))
            w['QQQ'] = round(exp, 4)
            rem = max(0.0, 1.0 - min(1.0, exp))
            regime = 'EQUITY EXPANSION' if exp >= 1.0 else 'EQUITY CAUTION'
        else:
            exp = 0.0
            rem = 1.0
            regime = 'RISK-OFF HAVEN ROTATION'

        havens = ['DBC', 'UUP', 'GLD', 'TLT']
        valid_h = [h for h in havens if scores.loc[dt, h] > bil_score]
        valid_h = sorted(valid_h, key=lambda h: scores.loc[dt, h], reverse=True)[:2]

        if rem > 0.001:
            if valid_h:
                inv_vols = [1.0 / max(4.0, vol20.loc[dt, h] if not np.isnan(vol20.loc[dt, h]) else 15.0) for h in valid_h]
                sum_inv = sum(inv_vols)
                for h, inv_v in zip(valid_h, inv_vols):
                    w[h] = round((inv_v / sum_inv) * rem, 4)
            else:
                w['BIL'] = round(rem, 4)
                if exp == 0:
                    regime = 'FULL CASH DEFENSE'

        records.append({
            'date': dt_str,
            'regime': regime,
            'QQQ': round(w['QQQ'] * 100, 1),
            'UUP': round(w['UUP'] * 100, 1),
            'DBC': round(w['DBC'] * 100, 1),
            'GLD': round(w['GLD'] * 100, 1),
            'TLT': round(w['TLT'] * 100, 1),
            'BIL': round(w['BIL'] * 100, 1),
            'equity_breadth': round(float(eq_b), 1),
            'credit_breadth': round(float(cr_b), 1),
            'commodity_breadth': round(float(co_b), 1),
            'haven_breadth': round(float(ha_b), 1),
            'net_flow_breadth': round(float(flow_b), 1)
        })
    return records


def main():
    utc_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"[{utc_now}] Fetching maximum mutual history (from 2007-05-30) for {len(ALL_TICKERS)} macro ETFs...")
    raw = yf.download(ALL_TICKERS, start="2007-05-30", progress=False)["Close"]
    raw = raw.dropna(axis=0, how="all")

    latest_date, metrics_df = fetch_and_calculate_metrics()
    payload, w_qqq, w_macro = generate_deterministic_allocation(latest_date, metrics_df)
    hist_records = generate_historical_allocations(raw)
    if hist_records:
        hist_records[-1]['QQQ'] = round(w_qqq['QQQ'] * 100, 1)
        hist_records[-1]['UUP'] = round(w_qqq['UUP'] * 100, 1)
        hist_records[-1]['DBC'] = round(w_qqq['DBC'] * 100, 1)
        hist_records[-1]['GLD'] = round(w_qqq['GLD'] * 100, 1)
        hist_records[-1]['TLT'] = round(w_qqq['TLT'] * 100, 1)
        hist_records[-1]['BIL'] = round(w_qqq['BIL'] * 100, 1)
        hist_records[-1]['regime'] = payload['strategy_qqq_rotation']['regime']

    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "signals_latest.json")
    csv_path = os.path.join(output_dir, "allocation_orders.csv")
    hist_json_path = os.path.join(output_dir, "historical_allocations.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    with open(hist_json_path, "w", encoding="utf-8") as f:
        json.dump(hist_records, f, indent=2)

    orders = []
    for ticker in ALL_TICKERS:
        orders.append({
            "Ticker": ticker,
            "Score": metrics_df.loc[ticker, "Score"],
            "Vol20d": metrics_df.loc[ticker, "Vol20d"],
            "QQQ_Strategy_Weight": f"{w_qqq[ticker]*100:.2f}%",
            "Macro_Strategy_Weight": f"{w_macro[ticker]*100:.2f}%",
            "Cash_Hurdle_Verdict": "PASS (SCORE > BIL)" if metrics_df.loc[ticker, "Score"] > payload["cash_hurdle_bil_score"] else "FAIL (SCORE <= BIL)"
        })
    orders_df = pd.DataFrame(orders).sort_values(by="Score", ascending=False)
    orders_df.to_csv(csv_path, index=False)

    print("\n" + "="*75)
    print(f"DETERMINISTIC QUANT ALLOCATION REPORT (AS-OF: {latest_date})")
    print("="*75)
    print(f"Benchmark Cash Hurdle (BIL): {payload['cash_hurdle_bil_score']} pts")
    print(f"Active Haven Assets:         {payload['valid_havens']}")
    print("\n[STRATEGY 1: QQQ VOL-MANAGED + HAVEN ROTATION (BEAT QQQ)]")
    print(f"  Regime Status:             {payload['strategy_qqq_rotation']['regime']}")
    print(f"  QQQ Score vs BIL:          {payload['strategy_qqq_rotation']['qqq_score']:.2f} vs {payload['cash_hurdle_bil_score']:.2f} (REJECTED)")
    print(f"  QQQ 20D Realized Vol:      {payload['strategy_qqq_rotation']['qqq_vol20d']:.2f}%")
    print("  ACTIONABLE TRADES FOR INVESTOR:")
    for item in payload['strategy_qqq_rotation']['execution_plan']:
        print(f"    - {item['Instrument']:<28} : {item['Weight']:<8} | {item['Action']}")

    print("\n[STRATEGY 2: GLOBAL MACRO ALPHA CORE]")
    print(f"  Selected Core Equity:      {payload['strategy_global_macro']['selected_core']} (Exposure: {payload['strategy_global_macro']['core_exposure']*100:.1f}%)")
    print("="*75)
    print(f"Outputs written successfully to:\n  - {json_path}\n  - {csv_path}\n  - {hist_json_path}")

if __name__ == "__main__":
    main()
