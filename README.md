<p align="center">
  <img src="assets/readme/hero.svg" alt="AI Job Search 채용 지원 워크플로" width="100%">
</p>

<p align="center">
  <a href="https://github.com/kasw99/ai-job-search/actions/workflows/ci.yml"><img src="https://github.com/kasw99/ai-job-search/actions/workflows/ci.yml/badge.svg" alt="CI" height="20"></a>
  &nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2A9D8F?style=flat" alt="MIT 라이선스" height="20"></a>
  &nbsp;
  <img src="https://img.shields.io/badge/대한민국-채용_검색-0047A0?style=flat" alt="대한민국 채용 검색" height="20">
</p>

# AI Job Search 한국판

한국 구직자를 위한 AI 기반 채용 검색·지원서 작성 워크플로입니다. 원본
[`ai-job-search`](https://github.com/ai-job-search-dev/ai-job-search)의 프로필 분석, 공고 평가,
맞춤형 이력서·자기소개서 작성, 면접 준비 흐름을 유지하면서 한국어 사용 환경과 국내 채용
검색 조건을 추가했습니다.

> 이 저장소는 원본 프로젝트의 비공식 한국형 포크입니다. Anthropic, 고용24 또는 각 채용
> 플랫폼이 보증하거나 운영하는 서비스가 아닙니다.

## 한국판에서 달라진 점

- 사용자 안내와 주요 결과를 한국어로 제공
- 날짜는 `YYYY-MM-DD`, 금액은 원화(`KRW`) 형식을 기본으로 사용
- 서울·경기·인천 등 국내 지역과 직무, 고용형태, 경력, 학력, 등록일 조건 지원
- 네이버·토스·쿠팡의 기업 공식 채용 페이지를 개인 사용자 기본 검색 소스로 사용
- 잡코리아·사람인·원티드 등의 공개 검색 페이지는 사용자가 허용한 경우에만 선택적으로 사용
- 고용24 API는 승인된 기업회원이 명시적으로 선택한 경우에만 사용
- [`kasw99/job-searcher`](https://github.com/kasw99/job-searcher)를 서브모듈로 연결해 국내 채용
  수집기를 관리

## 채용 소스 정책

| 구분 | 소스 | 기본 사용 | 비고 |
|---|---|:---:|---|
| 기업 공식 채용 | 네이버·토스·쿠팡 | 예 | 개인 사용자 기본 검색 |
| 공개 검색 페이지 | 잡코리아·사람인·원티드 등 | 아니요 | 약관과 robots 정책 확인 후 `--allow-public-pages` 필요 |
| 고용24 Open API | 고용24 | 아니요 | 승인된 기업회원 전용, `--source work24` 필요 |

로그인 자동화, 입사 지원 제출, CAPTCHA 우회 및 접근 차단 우회는 구현하지 않습니다.

## 준비 사항

- [Claude Code](https://claude.com/claude-code) 또는 호환 가능한 코딩 에이전트
- Python 3.10 이상
- Git
- 이력서 PDF 생성까지 사용할 경우 LaTeX 배포판

## 빠른 시작

### 1. 저장소 복제

```bash
git clone --recurse-submodules https://github.com/kasw99/ai-job-search.git
cd ai-job-search
```

이미 서브모듈 없이 복제했다면 다음을 실행합니다.

```bash
git submodule update --init --recursive
```

### 2. 국내 채용 검색 의존성 설치

```bash
python -m pip install -r integrations/job-searcher/requirements.txt
```

### 3. 구직자 프로필 설정

Claude Code를 실행한 뒤 다음 명령을 입력합니다.

```text
/setup
```

기존 이력서나 `documents/` 폴더를 읽히거나, 대화형 질문에 답해 경력·역량·희망 직무·지역을
설정할 수 있습니다.

### 4. 채용공고 검색

Claude Code 안에서는 다음 명령을 사용합니다.

```text
/scrape
```

국내 채용 검색기를 직접 실행할 수도 있습니다.

```bash
python .agents/skills/korea-job-search/cli.py search \
  --query "AI 엔지니어" --jobage 14 --limit 20 --format table
```

기본 검색은 네이버·토스·쿠팡만 사용합니다. 사용 가능한 소스와 접근 방식은 다음 명령으로
확인할 수 있습니다.

```bash
python .agents/skills/korea-job-search/cli.py sources
```

## 주요 워크플로

| 명령 | 기능 |
|---|---|
| `/setup` | 이력서·문서 또는 인터뷰를 바탕으로 구직자 프로필 생성 |
| `/scrape` | 희망 조건에 맞는 채용공고 검색 및 중복 제거 |
| `/rank` | 여러 공고를 적합도 기준으로 평가하고 우선순위 지정 |
| `/apply` | 공고별 맞춤 이력서와 자기소개서 작성·검토 |
| `/interview` | 지원 자료를 기반으로 면접 준비와 모의 면접 진행 |
| `/outcome` | 지원, 면접, 합격·불합격 결과 기록 |

기본 사용 흐름은 다음과 같습니다.

```text
/setup → /scrape → /rank → /apply → /interview → /outcome
```

## 검색 조건 예시

```bash
python .agents/skills/korea-job-search/cli.py search \
  --query "백엔드 개발자" \
  --region 서울 --region 경기 \
  --career experienced \
  --jobage 7 \
  --limit 30 \
  --format json
```

주요 조건에는 검색어, 지역, 직무, 고용형태, 신입·경력, 최소·최대 경력 개월, 학력,
등록 기간과 결과 개수가 포함됩니다.

## 고용24 API — 승인된 기업회원 전용

[고용24 Open API 안내](https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do)에 따라 이용
자격을 갖추고 승인을 받은 기업회원만 사용해야 합니다. 개인 구직자의 기본 검색에는 포함되지
않으며, 고용24를 지정하지 않으면 인증키를 확인하거나 API 요청을 보내지 않습니다.

승인된 기업회원은 다음처럼 명시적으로 선택할 수 있습니다.

```powershell
$env:WORK24_API_KEY="발급받은-키"
python .agents/skills/korea-job-search/cli.py search `
  --source work24 --query "백엔드 개발자" --region 서울 --jobage 14 --format table
```

macOS와 Linux에서는 `export WORK24_API_KEY="발급받은-키"`를 사용합니다. 인증키는 저장소에
커밋하지 마세요.

## 공개 페이지 기반 소스 사용

잡코리아·사람인·원티드 등은 기본 검색에서 제외되어 있습니다. 각 사이트의 최신 이용약관과
robots 정책을 직접 확인하고, 허용되는 개인 구직 목적의 저빈도 조회라고 판단한 경우에만
명시적으로 활성화하세요.

```bash
python .agents/skills/korea-job-search/cli.py search \
  --query "데이터 분석가" \
  --source jobkorea,saramin \
  --allow-public-pages \
  --limit 10 --format table
```

## 개인정보 보호

GitHub의 공개 저장소를 포크하면 포크도 공개됩니다. `/setup`은 이름, 연락처, 학력, 경력,
희망 연봉 등의 개인정보를 Git 추적 파일에 기록할 수 있습니다. 실제 구직에 사용할 때는 이
프로젝트를 별도의 **비공개 저장소**로 복사하고 개인정보나 API 키를 공개 포크에 커밋하지
마세요.

## 프로젝트 구성

```text
.agents/skills/korea-job-search/   국내 채용 통합 검색 명령
.claude/commands/                  setup, scrape, apply 등 워크플로 명령
.claude/skills/                    프로필·공고 평가·지원서 작성 규칙
integrations/job-searcher/         국내 채용 소스 수집기 서브모듈
cv/                                이력서 템플릿
cover_letters/                     자기소개서 템플릿
documents/                         구직자 원본 자료
job_scraper/                       검색 결과와 처리 상태
```

## 원본 프로젝트와 라이선스

- 기반 프로젝트: [`ai-job-search-dev/ai-job-search`](https://github.com/ai-job-search-dev/ai-job-search)
- 국내 채용 수집기 기반: [`itssosunny/job-searcher`](https://github.com/itssosunny/job-searcher)
- 이 포크의 국내 채용 수집기: [`kasw99/job-searcher`](https://github.com/kasw99/job-searcher)

원본 구조와 저작권 고지를 보존하며, 프로젝트는 [MIT 라이선스](LICENSE)를 따릅니다. 원본의
상세한 전체 기능 설명은 [영문 README](https://github.com/ai-job-search-dev/ai-job-search#readme)와
[`SETUP.md`](SETUP.md)를 참고하세요.

<p align="center">
  <img src="assets/mascot/pip_flight_loop.gif" alt="지원서를 전달하는 Pip" width="120"><br>
  <sub>좋은 기회를 찾길 바랍니다.</sub>
</p>
