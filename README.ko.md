# AI Job Search 한국어판

이 포크는 원본 `ai-job-search`의 지원서 작성·평가·면접 준비 흐름을 유지하면서,
한국어 기본 응답과 대한민국 채용 검색 소스를 추가합니다.

## 한국형 변경점

- 사용자에게 보이는 안내·평가·초안은 기본적으로 한국어로 작성
- 날짜는 `YYYY-MM-DD`, 금액은 원화(`KRW`)를 기본으로 표시
- 서울·경기·인천 등 한국 지역명과 고용24 지역코드 지원
- 직무 키워드, 고용형태, 신입/경력, 학력, 경력 개월, 등록일 조건 지원
- 네이버·토스·쿠팡의 기업 자체 채용 소스를 개인 사용자 기본 검색으로 사용
- 고용24 공식 Open API는 승인된 기업회원이 `--source work24`로 명시한 경우에만 사용
- `itssosunny/job-searcher`를 서브모듈로 연결해 소스별 코드를 중복하지 않음
- 잡코리아·사람인·원티드 같은 공개 페이지 수집기는 기본 비활성화하고 명시적 선택 시에만 사용

## 빠른 시작

```bash
git clone --recurse-submodules <이-포크의-URL>
cd ai-job-search
python -m pip install -r integrations/job-searcher/requirements.txt
```

그다음 Claude Code에서 `/setup`을 실행해 프로필과 희망 직무·지역을 입력하고 `/scrape`로
채용공고를 찾습니다. 원본의 전체 준비 절차는 [SETUP.md](SETUP.md)를 참고하세요.

## 고용24 공식 API — 승인된 기업회원 전용

고용24 [Open API 안내](https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do)에 따라
기업회원으로 이용 신청과 승인을 받은 계정만 사용할 수 있습니다. 개인 구직자의 기본
검색에는 포함되지 않으며, 자격과 승인 목적을 확인한 기업회원만 명시적으로 선택합니다.

```powershell
$env:WORK24_API_KEY="발급받은-키"
python .agents/skills/korea-job-search/cli.py search --source work24 --query "백엔드 개발자" --region 서울 --jobage 14 --format table
```

macOS/Linux에서는 `export WORK24_API_KEY="..."`를 사용합니다. 키는 저장소나 `.env`에
커밋하지 마세요. 공식 명세상 영리법인(개인사업자 포함)은 채용정보 API를 사용할 수
없으므로, 발급받은 키의 승인 목적과 약관을 준수해야 합니다.

고용24를 지정하지 않으면 키를 확인하거나 고용24에 요청하지 않습니다.

## 검색 조건 예시

```bash
python .agents/skills/korea-job-search/cli.py search \
  --query "AI 엔지니어" --jobage 14 --limit 20 --format json
```

지원 소스와 접근 방식은 `python .agents/skills/korea-job-search/cli.py sources`로 확인할 수 있습니다.

## 공개 페이지 기반 소스

`job-searcher`에는 잡코리아·사람인·원티드 등 공개 검색 페이지 수집기도 포함되어 있습니다.
이 포크는 해당 소스를 기본 실행하지 않습니다. 각 사이트의 최신 약관과 robots 정책을 확인한 뒤,
개인 구직 목적의 저빈도 조회에 적합하다고 판단한 경우에만 `--allow-public-pages`를 사용하세요.

```bash
python .agents/skills/korea-job-search/cli.py search -q "데이터 분석가" \
  --source jobkorea,saramin --allow-public-pages --limit 10 --format table
```

로그인, 저장, 지원 제출, CAPTCHA 우회, 차단 우회는 구현하지 않습니다.

## 개인정보 주의

GitHub의 공개 저장소를 포크하면 포크도 공개됩니다. `/setup`은 이름·연락처·경력 등 개인정보를
추적 파일에 쓸 수 있습니다. 실제 구직 자료는 원본 안내처럼 별도의 비공개 저장소에 두는 편이
안전합니다.

## 라이선스와 원본

- 기반 프로젝트: [ai-job-search-dev/ai-job-search](https://github.com/ai-job-search-dev/ai-job-search)
- 한국 채용 수집기: [itssosunny/job-searcher](https://github.com/itssosunny/job-searcher)
- 두 프로젝트 모두 MIT 라이선스이며 각 저작권·라이선스 고지를 그대로 보존합니다.
