import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "analysis.json"
DASH = ROOT / "dashboard"
DASH.mkdir(exist_ok=True)

if DATA.exists():
    records = json.loads(DATA.read_text(encoding="utf-8"))
else:
    records = []

payload = json.dumps(records, ensure_ascii=False)
html = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>SE_Osstem | OpenDART Financial Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root{{--olive:#66734a;--olive-dark:#465133;--cream:#f7f1e4;--paper:#fffdf8;--line:#ded7c8;--text:#283026;--muted:#70776b;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--cream);color:var(--text);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}} a{{color:inherit}} .wrap{{max-width:1400px;margin:auto;padding:28px}} header{{background:var(--olive);color:#fff;padding:28px;border-radius:22px;display:flex;justify-content:space-between;gap:20px;align-items:end;box-shadow:0 10px 35px #66734a22}} h1{{font-family:Georgia,serif;font-size:42px;margin:0 0 8px}} .sub{{opacity:.85}} .pill{{background:#fff;color:var(--olive-dark);padding:10px 14px;border-radius:999px;font-weight:700;text-decoration:none;display:inline-block}} .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}} .card,.panel{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 5px 18px #00000008}} .label{{font-size:13px;color:var(--muted)}} .value{{font-size:25px;font-weight:800;margin-top:7px}} .charts{{display:grid;grid-template-columns:1.6fr 1fr;gap:16px}} .panel h2{{font-family:Georgia,serif;margin:0 0 16px;font-size:22px}} canvas{{width:100%!important;height:330px!important}} .section{{margin-top:20px}} .table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:14px}} table{{border-collapse:collapse;width:100%;min-width:1000px;background:#fff}} th,td{{padding:10px 12px;border-bottom:1px solid #eee8dc;text-align:right;white-space:nowrap}} th:first-child,td:first-child{{text-align:left;position:sticky;left:0;background:inherit}} th{{background:#f0eadc;color:#505a48;font-size:12px}} tr:hover td{{background:#faf7ef}} .note{{font-size:12px;color:var(--muted);line-height:1.6}} .peer td:first-child{{font-weight:700}} footer{{margin-top:26px;color:var(--muted);font-size:12px;line-height:1.7}} @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}.charts{{grid-template-columns:1fr}}header{{display:block}}}} @media(max-width:600px){{.wrap{{padding:14px}}.cards{{grid-template-columns:1fr}}h1{{font-size:32px}}}}
</style>
</head>
<body><div class="wrap">
<header><div><div style="letter-spacing:.08em;text-transform:uppercase;font-size:12px">OpenDART × GitHub Automated Analysis</div><h1>오스템임플란트 재무 대시보드</h1><div class="sub">2010년 이후 사업·반기·분기보고서 기반 · 매월 1일 자동 업데이트</div></div><a class="pill" href="https://opendart.fss.or.kr/" target="_blank">OpenDART 원문</a></header>
<div id="cards" class="cards"></div>
<section class="charts"><div class="panel"><h2>매출 · 영업이익 추이</h2><canvas id="trend"></canvas></div><div class="panel"><h2>수익성 지표</h2><canvas id="margin"></canvas></div></section>
<section class="section panel"><h2>핵심 재무비율 추이</h2><canvas id="ratios"></canvas></section>
<div id="tables"></div>
<section class="section panel"><h2>국내 Peer Firms</h2><div class="table-wrap"><table class="peer"><thead><tr><th>기업</th><th>주요 사업/비교 이유</th><th>비고</th></tr></thead><tbody>
<tr><td>덴티움</td><td>치과용 임플란트 및 치과 의료기기</td><td>국내 임플란트 주요 비교 기업</td></tr>
<tr><td>디오</td><td>치과용 임플란트·디지털 덴티스트리</td><td>국내 임플란트 산업 비교 기업</td></tr>
<tr><td>덴티스</td><td>치과용 임플란트·의료기기</td><td>국내 치과 의료기기 비교 기업</td></tr>
<tr><td>신흥</td><td>치과 재료·장비·임플란트 관련 사업</td><td>국내 치과 산업 비교 기업</td></tr>
<tr><td>바텍</td><td>치과용 영상진단장비</td><td>치과 의료기기 인접 비교 기업</td></tr>
</tbody></table></div><p class="note">Peer 목록은 국내 치과·임플란트 산업에서 비교 대상으로 자주 언급되는 기업을 정리한 것으로, 동일 사업 범위나 회계 기준이 항상 일치하는 것은 아닙니다.</p></section>
<footer>Data source: Financial Supervisory Service OpenDART. Standardized single-company financial statements are available through the OpenDART financial-information APIs from 2015 onward; the pipeline archives and best-effort parses pre-2015 original filings separately. Values and ratios should be checked against the underlying filing before investment or credit decisions.</footer>
</div>
<script>
const DATA = {payload};
const annual=DATA.filter(x=>x.period==='annual'), half=DATA.filter(x=>x.period==='half_year'), q=DATA.filter(x=>x.period==='quarterly');
const latest=annual.at(-1) || DATA.at(-1) || {{}};
function fmt(v, digits=0){{ if(v===null||v===undefined||Number.isNaN(Number(v))) return '-'; return Number(v).toLocaleString('ko-KR',{{maximumFractionDigits:digits}}); }}
function eok(v){{ return v==null?'-':fmt(v/100000000,0)+'억'; }}
const cards=[['최근 연간 매출액',eok(latest.revenue)],['최근 연간 영업이익',eok(latest.operating_profit)],['영업이익률',latest.operating_margin==null?'-':fmt(latest.operating_margin,1)+'%'],['최근 FCF',eok(latest.fcf)]];
document.getElementById('cards').innerHTML=cards.map(x=>`<div class="card"><div class="label">${{x[0]}}</div><div class="value">${{x[1]}}</div></div>`).join('');
function labels(a){{return a.map(x=>x.period_label)}}
new Chart(document.getElementById('trend'),{{type:'bar',data:{{labels:labels(annual),datasets:[{{label:'매출액',data:annual.map(x=>x.revenue/1e8),borderWidth:0}},{{label:'영업이익',data:annual.map(x=>x.operating_profit/1e8),borderWidth:0}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{title:{{display:true,text:'억원'}}}}}}}}}});
new Chart(document.getElementById('margin'),{{type:'line',data:{{labels:labels(annual),datasets:[{{label:'영업이익률',data:annual.map(x=>x.operating_margin),tension:.25}},{{label:'순이익률',data:annual.map(x=>x.net_margin),tension:.25}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{title:{{display:true,text:'%'}}}}}}}}}});
new Chart(document.getElementById('ratios'),{{type:'line',data:{{labels:labels(annual),datasets:[{{label:'ROA',data:annual.map(x=>x.roa),tension:.25}},{{label:'ROE',data:annual.map(x=>x.roe),tension:.25}},{{label:'유동비율',data:annual.map(x=>x.current_ratio),tension:.25}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{title:{{display:true,text:'% / 배'}}}}}}}}}});
function table(title, rows){{
 const cols=[['period_label','기간'],['revenue','매출액'],['gross_profit','매출총이익'],['operating_profit','영업이익'],['pretax_income','세전이익'],['net_income','당기순이익'],['controlling_net_income','지배주주순이익'],['ebitda','EBITDA'],['total_assets','총자산'],['total_liabilities','총부채'],['equity','자본총계'],['operating_cash_flow','영업활동현금흐름'],['investing_cash_flow','투자활동현금흐름'],['financing_cash_flow','재무활동현금흐름'],['capex','CAPEX'],['fcf','FCF'],['net_debt','순차입금'],['operating_margin','영업이익률'],['net_margin','순이익률'],['roa','ROA'],['roe','ROE'],['current_ratio','유동비율'],['debt_ratio','부채비율'],['equity_ratio','자기자본비율'],['interest_coverage','이자보상배율'],['net_debt_ebitda','순차입금/EBITDA']];
 let h=cols.map(c=>`<th>${{c[1]}}</th>`).join(''); let b=rows.map(r=>`<tr>${{cols.map(([k,n])=>`<td>${{k==='period_label'?r[k]:(k.includes('margin')||k==='roa'||k==='roe'||k.endsWith('ratio')||k==='current_ratio'||k==='debt_ratio'||k==='equity_ratio')?(r[k]==null?'-':fmt(r[k],1)+'%'):fmt(r[k]/1e8,0)+'억'}}</td>`).join('')}}</tr>`).join('');
 return `<section class="section panel"><h2>${{title}}</h2><div class="table-wrap"><table><thead><tr>${{h}}</tr></thead><tbody>${{b}}</tbody></table></div></section>`;
}}
document.getElementById('tables').innerHTML=table('Annual · 연간',annual.slice().reverse())+table('Half-year · 반기',half.slice().reverse())+table('Quarterly · 분기',q.slice().reverse());
</script></body></html>'''
(DASH/'index.html').write_text(html, encoding='utf-8')
print(f"Dashboard written: {DASH/'index.html'}")
