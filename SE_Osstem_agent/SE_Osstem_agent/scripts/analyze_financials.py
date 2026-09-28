import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "financials.csv"
OUT = ROOT / "data" / "processed"

if not INPUT.exists():
    raise SystemExit("financials.csv가 없습니다. 먼저 fetch_dart.py를 실행하세요.")

df = pd.read_csv(INPUT)
num_cols = [c for c in df.columns if c not in {"period", "period_label", "source"}]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

def div(a, b):
    return (a / b * 100) if pd.notna(a) and pd.notna(b) and b != 0 else None

def ratio(a, b):
    return (a / b) if pd.notna(a) and pd.notna(b) and b != 0 else None

def avg_prev(curr, prev):
    if pd.notna(curr) and pd.notna(prev):
        return (curr + prev) / 2
    return curr

# Compute selected ratios per period. For ROA/ROE and turnover, previous period is used where available.
df = df.sort_values("period_label").reset_index(drop=True)
prev_assets = df["total_assets"].shift(1)
prev_equity = df["equity"].shift(1)
prev_receivables = df["receivables"].shift(1)
prev_inventory = df["inventory"].shift(1)

# Margins
df["gross_margin"] = [div(a, b) for a, b in zip(df["gross_profit"], df["revenue"])]
df["operating_margin"] = [div(a, b) for a, b in zip(df["operating_profit"], df["revenue"])]
df["net_margin"] = [div(a, b) for a, b in zip(df["net_income"], df["revenue"])]
df["ebitda_margin"] = [div(a, b) for a, b in zip(df["ebitda"], df["revenue"])]

# Net debt first
df["net_debt"] = df["interest_bearing_debt"] - df["cash"]

# Liquidity / leverage
df["current_ratio"] = [div(a, b) for a, b in zip(df["current_assets"], df["current_liabilities"])]
df["debt_ratio"] = [div(a, b) for a, b in zip(df["total_liabilities"], df["equity"])]
df["equity_ratio"] = [div(a, b) for a, b in zip(df["equity"], df["total_assets"])]
df["interest_bearing_debt_ratio"] = [div(a, b) for a, b in zip(df["interest_bearing_debt"], df["total_assets"])]
df["interest_coverage"] = [ratio(a, b) for a, b in zip(df["operating_profit"], df["interest_expense"])]
df["net_debt_ebitda"] = [ratio(a, b) for a, b in zip(df["net_debt"], df["ebitda"])]

# Cash / efficiency
df["fcf_margin"] = [div(a, b) for a, b in zip(df["fcf"], df["revenue"])]
turnover = []
roa = []
roe = []
for i, row in df.iterrows():
    aa = avg_prev(row.get("total_assets"), prev_assets.iloc[i])
    ee = avg_prev(row.get("equity"), prev_equity.iloc[i])
    rr = avg_prev(row.get("receivables"), prev_receivables.iloc[i])
    ii = avg_prev(row.get("inventory"), prev_inventory.iloc[i])
    turnover.append(ratio(row.get("revenue"), aa))
    roa.append(div(row.get("net_income"), aa))
    roe.append(div(row.get("net_income"), ee))
df["asset_turnover"] = turnover
df["roa"] = roa
df["roe"] = roe

# DSO / DIO are meaningful primarily for annual and full-period figures; use period-specific revenue/COGS if available.
df["dso"] = [ratio(r, rev) * 365 if pd.notna(r) and pd.notna(rev) and rev != 0 else None for r, rev in zip(df["receivables"], df["revenue"])]
df["dio"] = [ratio(inv, rev) * 365 if pd.notna(inv) and pd.notna(rev) and rev != 0 else None for inv, rev in zip(df["inventory"], df["revenue"])]

# Recompute net debt if missing.
if "net_debt" not in df:
    df["net_debt"] = df["interest_bearing_debt"] - df["cash"]
    df["net_debt_ebitda"] = [ratio(a, b) for a, b in zip(df["net_debt"], df["ebitda"])]

# Growth versus immediately previous record (useful for dashboard, not a substitute for YoY comparison across report types).
df["revenue_growth"] = df["revenue"].pct_change() * 100
df["operating_profit_growth"] = df["operating_profit"].pct_change() * 100

# Keep JSON numeric NaN out.
df = df.where(pd.notna(df), None)
df.to_csv(OUT / "analysis.csv", index=False, encoding="utf-8-sig")
(OUT / "analysis.json").write_text(df.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")
print(f"Analyzed {len(df)} periods")
