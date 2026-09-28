# GitHub 업로드 및 배포 순서

## 1. 압축 해제

`SE_Osstem_agent.zip`의 파일을 `HSC-Class02/SE_Osstem` 저장소 루트에 업로드합니다.

## 2. DART Secret 등록

Repository → Settings → Secrets and variables → Actions → New repository secret

- Name: `DART_API_KEY`
- Secret: OpenDART 40자리 인증키

## 3. Pages 활성화

Repository → Settings → Pages → Build and deployment → Source를 **GitHub Actions**로 선택합니다.

## 4. 첫 데이터 수집

Actions → `Update OpenDART data and dashboard` → `Run workflow`

첫 실행이 성공한 후 GitHub Pages URL을 확인합니다.

## 5. About 링크

Repository 오른쪽 About → Edit → Website에 다음 URL 입력:

`https://hsc-class02.github.io/SE_Osstem/dashboard/`

## 6. 매월 자동 업데이트

`update.yml`은 `0 15 1 * *`으로 설정되어 있습니다. GitHub Actions의 cron은 UTC이므로 **한국시간(KST) 매월 1일 00:00**에 실행됩니다.

## 7. 워크플로우 오류 예방 체크

- Secret 이름이 정확히 `DART_API_KEY`인지 확인
- Pages Source가 GitHub Actions인지 확인
- Actions 권한에서 workflow가 repository contents를 write할 수 있는지 확인
- 저장소 기본 브랜치가 `main`이라면 그대로 사용
- GitHub Pages 첫 배포 전에는 URL이 아직 만들어지지 않을 수 있음
