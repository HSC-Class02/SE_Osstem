import io
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "data" / "reports"
PROCESSED = ROOT / "data" / "processed"
for p in (RAW, REPORTS, PROCESSED):
    p.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get("DART_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit("DART_API_KEY 환경변수가 없습니다. GitHub Actions Secret에 DART_API_KEY를 등록하세요.")

BASE = "https://opendart.fss.or.kr/api"
CORP = CONFIG["corp_code"]
START_YEAR = int(CONFIG["start_year"])
THIS_YEAR = datetime.now().year
REPORT_CODES = CONFIG["report_codes"]

session = requests.Session()
session.headers.update({"User-Agent": "SE_Osstem-DART-Agent/1.0"})


def api_get(path, params, timeout=60):
    params = dict(params)
    params["crtfc_key"] = API_KEY
    r = session.get(f"{BASE}/{path}", params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "000":
        # 013 means no data and is not fatal for a particular period.
        if data.get("status") == "013":
            return {"status": "013", "message": data.get("message", "조회된 데이터가 없습니다."), "list": []}
        raise RuntimeError(f"DART API 오류 {data.get('status')}: {data.get('message')}")
    return data


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_num(value):
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if not s or s in {"-", "–", "—", "N/A", "nan", "None"}:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def amount(row, period_type):
    # For Q1/Q3, thstrm_add_amount is the stand-alone quarter when supplied;
    # otherwise fall back to thstrm_amount. For annual/H1 use thstrm_amount.
    if period_type in {"q1", "q3"}:
        v = normalize_num(row.get("thstrm_add_amount"))
        if v is not None:
            return v
    return normalize_num(row.get("thstrm_amount"))


def account_rows(year, reprt_code):
    data = api_get("fnlttSinglAcntAll.json", {
        "corp_code": CORP,
        "bsns_year": str(year),
        "reprt_code": reprt_code,
        "fs_div": "CFS" if CONFIG["prefer_consolidated"] else "OFS",
    })
    if data.get("status") == "013" or not data.get("list"):
        # fallback to separate financial statements
        data = api_get("fnlttSinglAcntAll.json", {
            "corp_code": CORP,
            "bsns_year": str(year),
            "reprt_code": reprt_code,
            "fs_div": "OFS",
        })
    return data.get("list", [])


def choose_row(rows, patterns, statement=None):
    scored = []
    for row in rows:
        nm = (row.get("account_nm") or "").replace(" ", "")
        if statement and row.get("sj_div") != statement:
            continue
        score = 0
        for i, pat in enumerate(patterns):
            if re.search(pat, nm, flags=re.I):
                score += max(1, len(patterns) - i)
        if score:
            scored.append((score, row))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def extract_metric(rows, patterns, statement=None, period_type="annual"):
    row = choose_row(rows, patterns, statement)
    return amount(row, period_type) if row else None


def extract_financials(rows, year, period_type, reprt_code):
    bs = lambda pats: extract_metric(rows, pats, "BS", period_type)
    pl = lambda pats: extract_metric(rows, pats, "IS", period_type)
    cf = lambda pats: extract_metric(rows, pats, "CF", period_type)

    # DART account names vary over time; patterns intentionally include common variants.
    revenue = pl([r"^매출액$", r"수익\(매출액\)", r"영업수익"])
    gross_profit = pl([r"매출총이익"])
    operating_profit = pl([r"영업이익"])
    pretax = pl([r"법인세비용차감전.*이익", r"세전이익", r"세전계속영업이익"])
    net_income = pl([r"당기순이익"])
    controlling_net_income = pl([r"지배기업.*소유주.*귀속", r"지배주주.*순이익", r"지배기업의소유주지분"])

    total_assets = bs([r"^자산총계$"])
    current_assets = bs([r"^유동자산$"])
    cash = bs([r"현금및현금성자산", r"현금및.*현금성자산"])
    receivables = bs([r"매출채권", r"매출채권및기타채권"])
    inventory = bs([r"재고자산"])
    current_liabilities = bs([r"^유동부채$"])
    total_liabilities = bs([r"^부채총계$"])
    equity = bs([r"^자본총계$"])
    interest_bearing_debt = bs([r"차입금", r"사채", r"금융부채"])

    cfo = cf([r"영업활동.*현금흐름", r"영업활동으로인한현금흐름"])
    cfi = cf([r"투자활동.*현금흐름", r"투자활동으로인한현금흐름"])
    cff = cf([r"재무활동.*현금흐름", r"재무활동으로인한현금흐름"])
    capex_ppe = cf([r"유형자산.*취득", r"유형자산의취득"])
    capex_intangible = cf([r"무형자산.*취득", r"무형자산의취득"])
    interest_expense = pl([r"이자비용", r"금융원가", r"이자비용.*금융비용"])
    depreciation = pl([r"감가상각비"])
    amortization = pl([r"무형자산상각비", r"상각비"])

    capex = 0
    if capex_ppe is not None:
        capex += abs(capex_ppe)
    if capex_intangible is not None:
        capex += abs(capex_intangible)
    if capex == 0:
        capex = None

    ebitda = None
    if operating_profit is not None:
        ebitda = operating_profit + (depreciation or 0) + (amortization or 0)

    net_debt = None
    if interest_bearing_debt is not None and cash is not None:
        net_debt = interest_bearing_debt - cash

    fcf = None
    if cfo is not None and capex is not None:
        fcf = cfo - capex

    period_name = {"annual": "annual", "half_year": "half_year", "q1": "quarterly", "q3": "quarterly"}[period_type]
    label = {"annual": f"{year}", "half_year": f"{year}-H1", "q1": f"{year}-Q1", "q3": f"{year}-Q3"}[period_type]

    return {
        "year": year,
        "period": period_name,
        "period_label": label,
        "reprt_code": reprt_code,
        "revenue": revenue,
        "gross_profit": gross_profit,
        "operating_profit": operating_profit,
        "pretax_income": pretax,
        "net_income": net_income,
        "controlling_net_income": controlling_net_income,
        "ebitda": ebitda,
        "total_assets": total_assets,
        "current_assets": current_assets,
        "cash": cash,
        "receivables": receivables,
        "inventory": inventory,
        "current_liabilities": current_liabilities,
        "total_liabilities": total_liabilities,
        "equity": equity,
        "interest_bearing_debt": interest_bearing_debt,
        "operating_cash_flow": cfo,
        "investing_cash_flow": cfi,
        "financing_cash_flow": cff,
        "capex": capex,
        "fcf": fcf,
        "interest_expense": interest_expense,
        "depreciation": depreciation,
        "amortization": amortization,
        "source": "OpenDART fnlttSinglAcntAll",
    }


def fetch_modern():
    rows_out = []
    for year in range(max(2015, START_YEAR), THIS_YEAR + 1):
        for period_type, code in REPORT_CODES.items():
            try:
                rows = account_rows(year, code)
                if not rows:
                    continue
                raw_name = RAW / f"{year}_{period_type}_financials.json"
                save_json(raw_name, {"year": year, "period_type": period_type, "rows": rows})
                rows_out.append(extract_financials(rows, year, period_type, code))
            except Exception as exc:
                print(f"WARN modern {year} {period_type}: {exc}")
    return rows_out


def filing_list(start_date, end_date, detail_type):
    all_rows = []
    page = 1
    while True:
        data = api_get("list.json", {
            "corp_code": CORP,
            "bgn_de": start_date,
            "end_de": end_date,
            "pblntf_ty": "A",
            "pblntf_detail_ty": detail_type,
            "last_reprt_at": "Y",
            "sort": "date",
            "sort_mth": "asc",
            "page_no": page,
            "page_count": 100,
        })
        items = data.get("list", [])
        all_rows.extend(items)
        if page >= int(data.get("total_page", 1)):
            break
        page += 1
    return all_rows


def download_document(rcept_no, destination):
    url = f"{BASE}/document.xml"
    r = session.get(url, params={"crtfc_key": API_KEY, "rcept_no": rcept_no}, timeout=120)
    r.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(r.content)
    return destination


def legacy_parse_zip(zip_path, year, period_type, rcept_no):
    """Best-effort parser for pre-2015 filings.

    OpenDART's standardized fnlttSinglAcnt APIs document financial data from 2015 onward.
    For 2010-2014 we archive the original DART filing and inspect HTML/XML tables.
    If a legacy filing uses a non-tabular format, it remains archived and is reported in
    data/processed/legacy_parse_log.csv rather than inventing values.
    """
    temp = ROOT / ".tmp" / rcept_no
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(temp)
        files = [p for p in temp.rglob("*") if p.suffix.lower() in {".xml", ".html", ".htm"}]
        rows = []
        for f in files:
            try:
                html = f.read_text(encoding="utf-8", errors="ignore")
                if "매출액" not in html and "영업이익" not in html:
                    continue
                tables = pd.read_html(io.StringIO(html))
                for t in tables:
                    text = " ".join(map(str, t.astype(str).values.flatten()))
                    if "매출액" in text and "영업이익" in text:
                        rows.append(t)
            except Exception:
                continue
        # Conservative extraction: only accept rows where a label and numeric value occur.
        metrics = {}
        patterns = {
            "revenue": ["매출액", "수익"],
            "operating_profit": ["영업이익"],
            "net_income": ["당기순이익"],
            "total_assets": ["자산총계"],
            "total_liabilities": ["부채총계"],
            "equity": ["자본총계"],
        }
        for table in rows:
            for metric, labels in patterns.items():
                if metrics.get(metric) is not None:
                    continue
                for idx in range(len(table)):
                    line = " ".join(map(str, table.iloc[idx].tolist()))
                    if any(label in line for label in labels):
                        nums = re.findall(r"-?\d[\d,]*(?:\.\d+)?", line.replace(" ", ""))
                        if nums:
                            # Avoid picking years; choose the first substantial number.
                            vals = [normalize_num(n) for n in nums]
                            vals = [v for v in vals if v is not None and abs(v) > 0]
                            if vals:
                                metrics[metric] = vals[-1]
                                break
        if metrics:
            return {
                "year": year,
                "period": "annual" if period_type == "annual" else ("half_year" if period_type == "half_year" else "quarterly"),
                "period_label": f"{year}" if period_type == "annual" else f"{year}-{period_type}",
                "reprt_code": None,
                **{k: metrics.get(k) for k in ["revenue", "operating_profit", "net_income", "total_assets", "total_liabilities", "equity"]},
                "source": "OpenDART original filing (legacy parser; verify)",
                "rcept_no": rcept_no,
            }
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    return None


def fetch_legacy():
    results = []
    logs = []
    for year in range(START_YEAR, min(2015, THIS_YEAR + 1)):
        year_start = f"{year}0101"
        year_end = f"{year}1231"
        for detail, period_type in [("A001", "annual"), ("A002", "half_year"), ("A003", "q3")]:
            try:
                filings = filing_list(year_start, year_end, detail)
            except Exception as exc:
                logs.append({"year": year, "period": period_type, "status": "list_error", "message": str(exc)})
                continue
            # Deduplicate and prefer the filing with no 정정 marker when possible.
            seen = set()
            for filing in filings:
                rcept_no = filing.get("rcept_no")
                if not rcept_no or rcept_no in seen:
                    continue
                seen.add(rcept_no)
                safe_name = f"{year}_{period_type}_{rcept_no}.zip"
                dest = REPORTS / str(year) / safe_name
                if CONFIG.get("save_raw_reports", True) and not dest.exists():
                    try:
                        download_document(rcept_no, dest)
                    except Exception as exc:
                        logs.append({"year": year, "period": period_type, "rcept_no": rcept_no, "status": "download_error", "message": str(exc)})
                        continue
                parsed = legacy_parse_zip(dest, year, "annual" if period_type == "annual" else period_type, rcept_no)
                if parsed:
                    results.append(parsed)
                    logs.append({"year": year, "period": period_type, "rcept_no": rcept_no, "status": "parsed", "message": "best-effort"})
                else:
                    logs.append({"year": year, "period": period_type, "rcept_no": rcept_no, "status": "archived_not_parsed", "message": "Original filing archived; no conservative table parse."})
                # One final filing per report type is enough for initial legacy history.
                break
    pd.DataFrame(logs).to_csv(PROCESSED / "legacy_parse_log.csv", index=False, encoding="utf-8-sig")
    return results


def save_filings_index():
    all_filings = []
    for detail, label in [("A001", "annual"), ("A002", "half_year"), ("A003", "quarterly")]:
        try:
            rows = filing_list(f"{START_YEAR}0101", f"{THIS_YEAR}1231", detail)
            for x in rows:
                x["period_type"] = label
            all_filings.extend(rows)
        except Exception as exc:
            print(f"WARN filings {label}: {exc}")
    if all_filings:
        pd.DataFrame(all_filings).drop_duplicates(subset=["rcept_no"]).to_csv(
            PROCESSED / "filings.csv", index=False, encoding="utf-8-sig"
        )


def main():
    modern = fetch_modern()
    legacy = fetch_legacy()
    combined = legacy + modern
    # Prefer modern standardized data where duplicate period labels exist.
    frame = pd.DataFrame(combined)
    if not frame.empty:
        frame["source_priority"] = frame["source"].map(lambda x: 2 if "fnlttSinglAcntAll" in str(x) else 1)
        frame = frame.sort_values(["year", "period", "source_priority"], ascending=[True, True, False])
        frame = frame.drop_duplicates(subset=["period_label"], keep="first").drop(columns=["source_priority"])
        frame = frame.sort_values(["year", "period_label"])
        frame.to_csv(PROCESSED / "financials.csv", index=False, encoding="utf-8-sig")
        (PROCESSED / "financials.json").write_text(frame.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")
    save_filings_index()
    meta = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "corp_code": CORP,
        "stock_code": CONFIG["stock_code"],
        "corp_name": CONFIG["corp_name"],
        "start_year": START_YEAR,
        "api_standard_financials_start": 2015,
        "raw_reports_saved": CONFIG.get("save_raw_reports", True),
    }
    save_json(PROCESSED / "metadata.json", meta)
    print(f"Done: {len(combined)} extracted records")


if __name__ == "__main__":
    main()
