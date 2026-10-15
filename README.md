<p align="center">
  <img src="assets/modu-stock-wordmark.png" alt="모두의 주식 · Stock for Everyone" width="240">
</p>

<h1 align="center">모두의 주식 · MoAI 애널리스트</h1>

<p align="center"><strong>기업을 깊게 읽고, 근거를 연결하고, 나의 보유자산까지 살펴봅니다.</strong></p>

<p align="center">
  <img alt="상태: 개발 중" src="https://img.shields.io/badge/%EC%83%81%ED%83%9C-%EA%B0%9C%EB%B0%9C%20%EC%A4%91-902531?style=flat-square">
  <img alt="자료 수집: 웹 기반" src="https://img.shields.io/badge/%EC%9E%90%EB%A3%8C%20%EC%88%98%EC%A7%91-%EC%9B%B9%20%EA%B8%B0%EB%B0%98-59636B?style=flat-square">
  <img alt="MCP: 다음 버전" src="https://img.shields.io/badge/MCP-%EB%8B%A4%EC%9D%8C%20%EB%B2%84%EC%A0%84-8A8A86?style=flat-square">
</p>

<p align="center">
  <a href="https://moai-stock.goos.chatgpt.site"><strong>SK하이닉스 보고서 미리 보기 →</strong></a>
  &nbsp;·&nbsp;
  <a href="https://moai-stock.goos.chatgpt.site/quickstart">설치 퀵스타트</a> &nbsp;·&nbsp; <a href="ROADMAP.md">다음 버전 로드맵</a>
</p>

**모두의 주식 · 원문 기반 AI 애널리스트**는 종목 하나의 질문을 출처가 연결된 보고서로 바꿉니다. DART 공시와 주석, 회사 IR, 원뉴스와 산업자료를 직접 읽고 수치와 반대 근거를 대조합니다. 확인된 사실·전망·해석을 구분하며, 결론을 바꿀 조건까지 MoAI 오피니언으로 설명합니다. **Goose 진입점 + goosekr 총괄 + 기존 호환 진입점 + 전문 업무 7개**, 총 10개 스킬로 구성됩니다.

현재 버전은 **0.1.4 개발 미리보기**입니다. 공개 저장소와 플랫폼별 패키지를 제공하며 로컬 계산·HTML 생성·패키지 구조를 검증했습니다. 2026-10-16 버전 0.1.1을 Chrome에서 ChatGPT 웹의 압축 업로드·설치 및 Claude 웹의 GitHub 마켓플레이스 동기화·설치를 확인했습니다. 두 환경 모두 스킬 8개가 인식됐습니다. 자연어 분석·HTML 생성 검증은 설치 검증과 구분합니다.

## 이렇게 요청해 보세요

사용자는 내부 스킬 이름을 외울 필요 없이 목적을 말합니다.

| 요청 예시 | 담당 업무 |
|---|---|
| “SK하이닉스를 공시와 뉴스로 깊게 분석해줘.” | 종목 심층 분석·HTML 보고서 |
| “삼성전자와 마이크론의 수익성과 사업을 같은 기준으로 비교해줘.” | 동종기업 비교 |
| “이번 실적에서 일회성 이익과 실제 현금흐름을 구분해줘.” | 실적 해설 |
| “이 공시가 회사에 어떤 영향을 주는지 후속 내용까지 확인해줘.” | 공시·뉴스 영향 분석 |
| “지난 보고서 이후 근거가 달라졌는지 점검해줘.” | 관심종목 재점검 |
| “HBM 비중이 높으면 무조건 수익성이 좋아진다는 주장을 검증해줘.” | 투자 주장 팩트체크 |
| “보유 수량·평단가·현금을 기준으로 집중도와 비중 조정 대안을 살펴줘.” | 보유자산 상담·시나리오 |

## 먼저 결과물을 만나보세요

**[공개 샘플 보고서 열기](https://moai-stock.goos.chatgpt.site)** — SK하이닉스 사례의 구성과 읽기 경험을 확인할 수 있습니다. 날짜가 명시된 보고서 예시이며 실시간 분석 서비스나 플러그인 설치 화면은 아닙니다.

[포트폴리오·브리핑 예시와 재생성 안내](examples/README.md)에서 공통 템플릿을 확인할 수 있습니다. 보유자산 기능의 [가상 입력](examples/portfolio/portfolio-input.json)과 [계산 결과](examples/portfolio/calculation.json)도 함께 제공합니다. 실제 계좌·실제 시세를 담지 않은 합성 예시입니다.

## 보고서와 페이지 템플릿

HTML 생성기는 일곱 `document_type`을 지원합니다.

| 유형 | 구성 |
|---|---|
| `deep_report` | 기업별 심층 보고서: 아홉 분석 장과 마지막 MoAI 오피니언 |
| `comparison` | 비교표와 차이의 원인을 담은 기업 비교 |
| `earnings` | 실적·이익의 질·현금흐름 해설 |
| `event` | 사건 사실·영향 경로·조건·반론 |
| `portfolio` | 보유 현황·집중도·상담 시나리오 |
| `fact_check` | 주장별 근거·반증·판정 |
| `briefing` | 필요한 섹션을 조합한 짧은 브리핑 페이지 |

일반 문서는 1~12개 섹션을 목적에 맞게 구성하고 오피니언을 생략할 수 있습니다. 심층 보고서만 10개 장과 12개 산문 문단을 사용하며 각 오피니언 문단은 최소 다섯 문장을 요구합니다. 보유자산 상담에 가상 회사명이나 억지로 긴 종목 보고서 형식을 넣지 않습니다.

승인된 ‘모두의 주식’ 글자 로고, 무채색 전자잉크 배경, 버건디 강조를 포함합니다. 제목은 **고운바탕**, 일반 본문과 MoAI 오피니언은 **Pretendard**, 본문 행간은 **1.6배**입니다. CSS·로고·재무 SVG는 HTML에 내장하고 글꼴만 CDN으로 읽습니다. 인터넷이 없으면 대체 글꼴이 적용됩니다. 폰트 CDN에는 일반적인 외부 글꼴 요청이 발생하지만 보고서·보유자산 데이터를 보내는 코드는 없습니다.

MoAI 오피니언은 결론 요약 뒤에 상세 해석을 배치합니다. `관심종목 편입 / 관망 / 편입 보류`는 조사·관찰 우선순위이며 매수·매도나 실제 관심목록 변경을 실행하지 않습니다. 근거가 부족하면 판단을 유보합니다. 봉차트·기술적 주가 분석은 현재 범위에서 제외합니다.

## 설치와 사용 준비

**[캡처와 함께 빠르게 설치하기 →](https://moai-stock.goos.chatgpt.site/quickstart)**

공통 스킬 원본은 하나로 유지하고 서비스별 설치 형식을 제공합니다. 공식 안내 확인일은 2026-10-16이며 요금제·관리자 정책·기능 제공 상태에 따라 메뉴가 다를 수 있습니다.

| 서비스 | 설치 경로 |
|---|---|
| ChatGPT 웹 | 기본: 워크스페이스 관리자의 Admin Console → Plugins → Add → Import marketplace. 관리자 메뉴가 없으면 플러그인 ZIP 업로드를 사용합니다. ZIP 실제 설치 확인. |
| Codex | 아래 명령으로 GitHub 마켓플레이스와 플러그인을 추가합니다. 앱에서는 지원되는 플러그인 관리 화면을 이용합니다. |
| Claude | 사용자 지정 → 플러그인 → 추가 → 마켓플레이스 추가 → 저장소에서 추가 → GitHub URL → 동기화 → 플러그인 추가. 실제 웹 설치 확인. |
| Gemini | 웹의 Skills 업로드에서 브라우저 통합 스킬 ZIP을 추가합니다. Gemini CLI는 저장소에서 확장을 설치합니다. |

**Codex CLI**

```sh
codex plugin marketplace add modu-ai/moai-stock-plugin
codex plugin add moai-stock-plugin@moai-stock-marketplace
```

**Claude Code**

```text
/plugin marketplace add modu-ai/moai-stock-plugin
/plugin install moai-stock-plugin@modu-ai-stock
```

**Gemini CLI**

```sh
gemini extensions install https://github.com/modu-ai/moai-stock-plugin
```

**GitHub 마켓플레이스 연결이 기본입니다.** 업데이트를 받을 수 있도록 기본 브랜치를 연결하고 동기화 상태와 설치 버전을 확인합니다. 등록이 지원되지 않는 계정의 ChatGPT·Claude용 ZIP은 [퀵스타트 다운로드](https://moai-stock.goos.chatgpt.site/quickstart#downloads)에서 받습니다. GitHub의 **Code → Download ZIP은 전체 개발 소스**이므로 브라우저 스킬 업로드용 파일과 구분합니다. 파일을 추가한 뒤 “모두의 주식으로 SK하이닉스를 공시와 뉴스에 근거해 분석해줘”라고 요청합니다.

[플랫폼별 조건·공식 출처·검증 범위](docs/platforms.md)를 함께 확인하세요. Claude Chat의 하위 에이전트 실행, Gemini Skills와 Deep Research·Canvas의 동시 사용 등은 호스트 제약을 따릅니다. 웹 검색이나 Python 실행이 제공되지 않으면 해당 작업의 제한을 표시합니다.

<details>
<summary><strong>로컬 실행과 입력 형식 보기</strong></summary>

호스트에는 웹 검색·원문 열람, 파일 읽기·쓰기, Python 실행 기능이 필요합니다. 개별 호스트의 권한·요금제·기능 제공 여부는 별도로 확인해야 합니다. 로컬 생성기와 계산기는 **Python 3 표준 라이브러리만** 사용하며 추가 Python 패키지가 필요하지 않습니다.

패키지 루트에서:

```sh
python3 scripts/validate_package.py
python3 skills/stock-report/tests/renderer-test.py
python3 -m unittest discover -s skills/portfolio-review/tests -v
```

보고서 구조화 입력은 [입력 규약](skills/stock-report/references/report-input.md)에 따라 작성합니다. 생성기는 자료를 조사하거나 주장 자체를 사실로 인증하지 않습니다.

```sh
python3 skills/stock-report/scripts/render_report.py --input /path/to/report-input.json --validate-only
python3 skills/stock-report/scripts/render_report.py --input /path/to/report-input.json --output-dir /path/to/new-report
```

보유자산 계산은 [보유자산 입력 규약](skills/portfolio-review/references/portfolio-input.md)을 사용합니다.

```sh
python3 skills/portfolio-review/scripts/portfolio_calc.py /path/to/holdings.json --output /path/to/calculation.json
```

보유 수량·주당 평단가·확인된 가격·통화·현금을 받아 손익과 비중을 계산합니다. 누락 가격을 0으로 바꾸지 않습니다. 환율은 출처가 확인된 제공값만 사용합니다. 사용자 목표가 없으면 목표 비중을 자동 생성하지 않으며, 목표가 있을 때 금액 차이와 정수주 조정의 산술적 예시를 계산합니다. 실제 매수일 환율·배당·실현손익이 없으면 총투자수익률이라고 부르지 않습니다.

</details>

## 자료를 읽는 방식

DART·회사 IR·네이버 증권·원뉴스·산업자료에서 **원문을 직접 읽고 → 기간과 단위를 맞추고 → 반대 근거를 검토하고 → 판단 조건을 설명**합니다. 한국어 역할명으로 실제 작업 상태를 알리며 자료를 확인한 범위를 넘겨 완료했다고 말하지 않습니다.

<details>
<summary><strong>출처·검증 원칙 자세히 보기</strong></summary>

현재 자료 수집은 **실행 환경의 웹 검색·브라우저 원문 열람**을 사용합니다. DART 본문·표·주석·검토 및 감사 첨부, 회사 IR, 공식 산업자료, 네이버 증권의 접근 가능한 재무·리서치·뉴스를 확인하고 원 언론까지 추적합니다. 검색 결과 제목이나 메뉴 추출만으로 원문 확인을 대신하지 않습니다.

이 패키지에 DART·시세 MCP 서버, API 키, 뉴스 크롤러, 자동 주문 연결은 들어 있지 않습니다. API·MCP 연동은 [다음 버전 로드맵](ROADMAP.md)의 항목입니다. 현재 웹 경로에서 접근이 막히면 가능한 대체 원문을 찾고, 남은 제한과 판단 영향을 기록합니다.

[조사 계약](skills/stock-report/references/research-contract.md)과 [역할 계약](skills/stock-report/references/agent-team.md)에 따라 출처 장부와 주장 연결을 유지합니다. 같은 회사의 보도자료와 SEC 제출이 일치한다고 독립 검증을 받았다고 표현하지 않습니다. 증권사 보고서는 독립 분석의 반대 가정·누락 변수를 확인하는 비교 자료로 사용합니다. 과거 열람 기록과 이번 실행의 직접 열람은 구분합니다.

</details>

<details>
<summary><strong>총괄 1개와 업무 7개의 연결 구조 보기</strong></summary>

| 스킬 | 역할 |
|---|---|
| [stock-analyst](skills/stock-analyst/SKILL.md) | 자연어 의도를 해석하고 필요한 업무·입력·검토 단계를 연결하는 총괄 |
| [stock-report](skills/stock-report/SKILL.md) | 심층 조사 통합과 보고서 편집·생성 |
| [peer-compare](skills/peer-compare/SKILL.md) | 기간·통화·사업 범위를 맞춘 기업 비교 |
| [earnings-review](skills/earnings-review/SKILL.md) | 실적·주석·현금흐름·검토 및 감사 상태 분석 |
| [event-impact](skills/event-impact/SKILL.md) | 원뉴스·공시와 정정·집행·완료 사건 추적 |
| [watchlist-review](skills/watchlist-review/SKILL.md) | 이전 근거와 현재 근거·판단 조건의 차이 분석 |
| [claim-check](skills/claim-check/SKILL.md) | 핵심 주장·수치·반론의 독립 대조 |
| [portfolio-review](skills/portfolio-review/SKILL.md) | 보유 현황 계산과 목적·제약에 따른 조건부 상담 |

[실행 지도](skills/stock-report/references/workflow-map.json)는 일곱 업무 흐름의 의존관계를 담은 **선언형 DAG 지침**입니다. 자동 스케줄러나 네이티브 스킬 체이닝 런타임 엔진을 구현한 파일은 아닙니다. 호스트가 제공하는 에이전트·스킬 실행 기능을 이용하거나 에이전트가 지침을 읽고 같은 입력·출력 계약으로 수행합니다. 하위 작업은 지정 단계만 반환하고 총괄을 재귀 호출하지 않습니다. 조건부 생략과 미해결 입력은 이유를 남기며 완료로 위장하지 않습니다.

역할을 보여줄 때는 공시·재무 분석, 뉴스 조사, 산업·경쟁사 분석, 팩트체크, 보고서 편집 같은 한국어 이름을 사용합니다. 화면의 네이티브 작업 카드가 한국어 이름을 그대로 표시하는지는 호스트의 지원에 달려 있습니다. 실제 수행한 작업만 상태로 알립니다.

</details>

<details>
<summary><strong>테스트 범위와 아직 확인하지 않은 것 보기</strong></summary>

포함된 테스트는 합성 데이터로 실행합니다. 결과 수는 테스트 실행 출력에서 확인하며 고정된 통과 숫자를 문서에 적지 않습니다.

- 패키지 검증: 주요 매니페스트 필드, 현재 스킬 집합, 제한된 YAML 메타데이터, 상대 참조의 존재·패키지 내부 경로, 업무 DAG의 누락 의존성·순환, MCP 설정 미포함을 확인합니다. 공식 플러그인 스키마 전체 인증은 아닙니다.
- 보고서 검증: CLI 입력 보존, 문서 유형별 구조, 출처 연결·상태, 로컬 근거 표시, 위험한 URL·HTML 이스케이프, 결측·음수 차트, 비유한 숫자 거부, 산문 문장 배열을 검사합니다. 실제 기업 내용의 진실성·최신성은 별도 조사·검토 책임입니다.
- 계산 검증: 손익·현금 포함 비중·환율·원가 누락·중복·0 분모·오래된 가격·발행사 매핑·목표 비중·정수주·비용 후 현금을 확인합니다. 실제 계좌 연결이나 주문 테스트는 없습니다.
- 실제 브라우저 화면, CDN 글꼴, 좁은 화면, PDF 페이지 나눔은 생성된 결과마다 별도 확인합니다. Python 테스트만 통과했다고 모든 화면이나 PDF를 검증했다고 주장하지 않습니다.
- ChatGPT 웹 파일 업로드 설치와 Claude 웹 GitHub 마켓플레이스 설치는 실제 확인했습니다. 데스크톱·CLI·Gemini의 계정 설치와 각 호스트의 전체 분석 실행은 별도 검증 대상입니다.

</details>

## 개인정보와 배포 원칙

개인 보유명세·원가·잔고·계좌번호·인증정보를 외부 웹 검색, 원격 도구, 공개 저장소, 예시, 로그에 전달하지 않습니다. 시세 조회에는 필요한 공개 종목 식별자만 사용합니다. 사용자 파일과 로컬 계산은 공개 URL을 꾸며내지 않고 작업 내 자료 별칭으로 연결합니다. 보유 정보가 포함된 결과는 사용자의 로컬 작업 공간에서 다룹니다.

보고서 검토 → 플러그인 제작·실행 검토 → 마지막 배포 순서를 따릅니다. GitHub 주소를 이용한 마켓플레이스 배포가 목표이며 ZIP 다운로드는 GitHub 등록이 불가능한 계정의 보조 경로로 제공합니다. 퀵스타트는 ChatGPT 웹과 Claude 웹 설치만 다룹니다. 공개 게시·설치 완료 여부는 실제 확인된 상태로 별도 보고합니다.

## 공개 샘플과 마켓플레이스 준비

[SK하이닉스 공개 샘플 보고서](https://moai-stock.goos.chatgpt.site)는 로그인 없이 볼 수 있는 날짜가 명시된 보고서 예시입니다. 이 페이지는 플러그인 설치나 실시간 종목 분석을 실행하는 서비스가 아닙니다.

저장소 루트의 `.agents/plugins/marketplace.json`은 현재 폴더의 플러그인을 가리키는 GitHub 마켓플레이스 카탈로그입니다. Claude 웹의 GitHub 동기화·설치를 확인했으며 ChatGPT 관리자 가져오기는 공식 문서에 따른 안내로 실제 계정 검증과 구분합니다. 공식 패키지 구조는 [OpenAI 플러그인 제작 문서](https://developers.openai.com/plugins/build/plugins), Git 배포 경로는 [배포 문서](https://developers.openai.com/plugins/deploy/desktop-only)를 참조합니다.

## 공식 디렉터리 제출

Claude와 OpenAI 모두 공식 제출 경로를 제공합니다. 제출·심사·공개는 GitHub 마켓플레이스 개인 설치와 별개입니다. 현재 공식 디렉터리 등록 완료를 주장하지 않습니다. [제출 경로와 확인 범위](docs/submission-options.md)를 참고하세요.

## Goose에게 짧게 요청하기

**Goose — 황금알을 낳는 개인 맞춤 인공지능 애널리스트.** 황금알은 원문에서 얻은 검증된 통찰을 뜻합니다.

```text
$goose 삼성전자 종목을 분석해줘
$goose 삼성전자와 SK하이닉스를 같은 기준으로 비교하고 HTML로 정리해줘
$goose 내 가상 보유자산의 손익·집중도를 점검하고 목표에 맞는 대안을 비교해줘
```

goose 진입 스킬은 goosekr 총괄로 요청을 전달합니다. 총괄은 실행 지도에 따라 필요한 전문 업무만 연결하고 검증 후 보고서를 작성합니다. 기존 stock-analyst 호출도 같은 총괄로 연결됩니다. `$` 호출이 없는 환경에서는 설치된 스킬을 선택하거나 Goose를 자연어로 부릅니다. 실제 스킬을 읽었는지 결과의 실행 기록에서 확인합니다. 현재 0.1.4의 패키지 구조 검증과 계정별 실제 호출 검증은 별개입니다.

[세션 2 심화 실습](https://moai-stock.goos.chatgpt.site/learn)에서 일곱 업무의 요청문·협업 흐름·결과 확인 방법을 확인하세요.

[설치 후 보고서 품질 비교와 수정](docs/report-quality-review.md) · [Goose 에이전트 정의](agents/goose.md)
