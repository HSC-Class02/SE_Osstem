# SE_Osstem — OpenDART Financial Analysis Agent

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97%20%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C가기-66734A?style=for-the-badge&logo=github&logoColor=white)](https://hsc-class02.github.io/SE_Osstem/dashboard/)

> DART(OpenDART)에서 오스템임플란트의 사업보고서·반기보고서·분기보고서를 수집하고, 주요 재무수치와 재무비율을 계산하여 GitHub Pages 대시보드로 제공하는 자동화 프로젝트입니다.

## 1. 프로젝트 구성

- **기업:** 오스템임플란트 (종목코드 048260 / DART 고유번호 00341916)
- **수집 시작:** 2010년
- **보고서:** 사업보고서(A001), 반기보고서(A002), 분기보고서(A003)
- **표준 재무 API:** OpenDART `fnlttSinglAcntAll`
- **자동화:** 매월 1일 KST 00:00 실행 + GitHub Actions 수동 실행 지원
- **Dashboard:** GitHub Pages
- **Raw filing archive:** `data/reports/` (워크플로우 설정상 원문 ZIP 보관)

## 2. 대시보드

예정 주소: **https://hsc-class02.github.io/SE_Osstem/dashboard/**

대시보드에는 다음을 포함합니다.

1. 매출액·영업이익 추이 그래프
2. 영업이익률·순이익률 그래프
3. ROA·ROE·유동비율 그래프
4. **Annual** 테이블
5. **Half-year** 테이블
6. **Quarterly** 테이블
7. 국내 Peer Firms 테이블

## 3. 분석 수치

첨부된 「재무제표 및 재무비율 실무 가이드」의 주요 항목을 기준으로 다음을 수집·계산합니다.

### 손익 / 규모
- 매출액
- 매출총이익
- 영업이익
- 세전이익
- 당기순이익
- 지배주주순이익
- EBITDA
- 총자산 / 총부채 / 자본총계

### 현금흐름
- 영업활동현금흐름(CFO)
- 투자활동현금흐름(CFI)
- 재무활동현금흐름(CFF)
- CAPEX
- FCF
- 순차입금

### 재무비율
- 매출총이익률
- 영업이익률
- 순이익률
- EBITDA 마진
- ROA
- ROE
- 유동비율
- 부채비율
- 자기자본비율
- 차입금의존도
- 이자보상배율
- 순차입금/EBITDA
- 총자산회전율
- DSO / DIO

> 비율 정의는 재무제표 표시 방식과 기업별 계정 구성에 따라 달라질 수 있으므로, 원문 공시와 함께 확인하는 것을 전제로 합니다.

## 4. 2010~2014 데이터 처리

OpenDART의 표준화된 단일회사 전체 재무제표 API는 2015년 이후 자료 제공을 전제로 하므로, 2010~2014년은 **공시검색 API(A001/A002/A003) → 원문 문서 API → 원문 ZIP 보관 → 보수적인 HTML/XML 표 파싱** 경로를 사용합니다.

파싱되지 않는 구형 문서는 임의의 숫자로 채우지 않고 `data/processed/legacy_parse_log.csv`에 상태를 기록하고 원문 ZIP을 보관합니다.

## 5. GitHub Actions 설정

### DART API Key

1. OpenDART에서 인증키를 발급합니다.
2. GitHub 저장소 → **Settings → Secrets and variables → Actions**로 이동합니다.
3. **New repository secret** 선택
4. Name: `DART_API_KEY`
5. Secret: 발급받은 40자리 API 인증키
6. 저장

**API 키를 코드·README·CSV·commit에 직접 입력하지 마세요.**

### 첫 실행

`Actions → Update OpenDART data and dashboard → Run workflow`를 눌러 수동으로 먼저 실행하세요.

정상 실행되면:

- `data/processed/financials.csv`
- `data/processed/analysis.csv`
- `data/processed/financials.json`
- `data/processed/analysis.json`
- `data/processed/filings.csv`
- `dashboard/index.html`
- `data/reports/연도/*.zip`

등이 업데이트됩니다.

## 6. GitHub Pages 설정

워크플로우에는 GitHub Pages 배포 설정이 포함되어 있습니다.

저장소에서 **Settings → Pages → Build and deployment → Source: GitHub Actions**로 설정하세요.

배포 후 주소는 일반적으로 다음 형태입니다.

`https://hsc-class02.github.io/SE_Osstem/dashboard/`

## 7. Repository About 링크

저장소 오른쪽 **About → Edit**에서 Website에 다음 주소를 입력하세요.

`https://hsc-class02.github.io/SE_Osstem/dashboard/`

README 상단 배지는 위 주소를 자동으로 연결하도록 작성되어 있습니다.

## 8. 국내 Peer Firms

국내 치과·임플란트 산업 비교 대상으로 다음 기업을 기본 등록했습니다.

| 기업 | 주요 비교 영역 |
|---|---|
| 덴티움 | 치과용 임플란트 및 치과 의료기기 |
| 디오 | 치과용 임플란트·디지털 덴티스트리 |
| 덴티스 | 치과용 임플란트·의료기기 |
| 메가젠임플란트 | 치과용 임플란트·디지털 덴티스트리 |
| 네오바이오텍 | 치과용 임플란트 |

Peer firms는 동일한 회계기준·사업범위를 가진다는 의미가 아니라, 국내 치과·임플란트 산업의 비교 대상으로 정리한 것입니다.

## 9. 폴더 구조

```text
SE_Osstem/
├─ .github/
│  └─ workflows/
│     ├─ update.yml
│     └─ pages.yml
├─ dashboard/
│  └─ index.html
├─ data/
│  ├─ raw/
│  ├─ reports/
│  └─ processed/
├─ scripts/
│  ├─ fetch_dart.py
│  ├─ analyze_financials.py
│  └─ build_dashboard.py
├─ config.json
├─ requirements.txt
└─ README.md
```

## 10. 출처

- [OpenDART](https://opendart.fss.or.kr/)
- [OpenDART 개발가이드](https://opendart.fss.or.kr/guide/main.do)
- [DART 공시검색 API](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001)
- [DART 단일회사 전체 재무제표 API](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020)
