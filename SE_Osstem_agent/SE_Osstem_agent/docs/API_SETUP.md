# DART API Key 입력 방법

## GitHub Actions

API Key는 소스코드에 입력하지 않고 GitHub Secret으로 등록합니다.

1. OpenDART에서 인증키 발급
2. Repository → Settings → Secrets and variables → Actions
3. `New repository secret`
4. Name: `DART_API_KEY`
5. Value: 발급받은 40자리 키
6. Save

워크플로우에서는 다음처럼 전달됩니다.

```yaml
env:
  DART_API_KEY: ${{ secrets.DART_API_KEY }}
```

Python에서는:

```python
import os
API_KEY = os.environ["DART_API_KEY"]
```

## 로컬 테스트

Windows PowerShell:

```powershell
$env:DART_API_KEY="여기에_40자리_키"
python scripts/fetch_dart.py
python scripts/analyze_financials.py
python scripts/build_dashboard.py
```

macOS/Linux:

```bash
export DART_API_KEY="여기에_40자리_키"
python scripts/fetch_dart.py
python scripts/analyze_financials.py
python scripts/build_dashboard.py
```

**중요:** API Key를 `config.json`, `.py`, README, CSV 등에 직접 붙여 넣고 Git에 commit하지 마세요.
