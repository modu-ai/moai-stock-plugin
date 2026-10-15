<div align="center">
<img src="assets/modu-stock-wordmark.png" alt="모두의 주식" width="320">

# Goose · 개인 맞춤 AI 애널리스트

**설치는 스킬 하나. 조사부터 상담과 HTML 보고서까지.**

[빠른 설치 안내](https://moai-stock.goos.chatgpt.site/quickstart) · [세션 2 심화 실습](https://moai-stock.goos.chatgpt.site/learn) · [샘플 보고서](https://moai-stock.goos.chatgpt.site/) · [Goose ZIP 다운로드](dist/goose-0.3.0.zip)
</div>

## 빠르게 시작하기

1. **goose-0.3.0.zip**을 다운로드합니다. 압축을 풀거나 내부 파일을 따로 올리지 않습니다.
2. ChatGPT 또는 Claude의 **스킬 업로드**에 ZIP을 추가합니다. 계정·워크스페이스에서 스킬 업로드를 지원해야 합니다. 서비스별 화면은 퀵스타트를 참고하세요.
3. Goose를 활성화하고 요청합니다.

```text
$goose 삼성전자 종목을 분석해줘
```

`$` 호출이 없는 환경에서는 “Goose, 삼성전자 종목을 분석해 주세요”라고 요청합니다. 기존 0.1.x 플러그인과 중복 실행하지 않도록 새 통합 스킬을 선택하고, 이전 플러그인을 비활성화하세요. ZIP 업데이트는 수동입니다. 새 버전을 받아 업로드하고 실행 결과의 VERSION 확인을 요청합니다.

**마켓플레이스 등록이나 GitHub 연결은 설치에 필요하지 않습니다.** 이 저장소는 소스·버전 관리 용도입니다. 0.2.0부터 공식 배포 단위는 Goose 통합 스킬 ZIP 하나입니다. 이전 플랫폼별 ZIP과 매니페스트는 이전 버전과의 비교·복구용으로 남아 있으며 새 설치 경로가 아닙니다.

## Goose가 하는 일

Goose는 사용자의 목적을 이해하고 필요한 업무만 연결하는 총괄입니다. 결과를 바꿀 맥락이 부족하면 한 번에 1~3개 질문으로 심층 인터뷰합니다. 사용자가 이미 답한 내용은 반복해서 묻지 않습니다.

| 내부 서브 스킬 | 역할 |
|---|---|
| stock-report | 기업 심층 분석과 최종 HTML 편집 |
| peer-compare | 동종기업 비교 |
| earnings-review | 실적·주석·현금흐름 해설 |
| event-impact | 공시·뉴스의 사업 영향 |
| watchlist-review | 기존 관심 판단의 변화 점검 |
| fact-check | 수치·주장·원문·반대 근거 검증 |
| portfolio-review | 보유자산 손익·집중도·상담과 대안 |

내부 goosekr 총괄 및 stock-analyst 호환 지침까지 모두 Goose 안에 포함됩니다. 서브 스킬은 필요할 때 읽는 GUIDE이며 별도 설치 스킬이 아닙니다. 실제 서브 에이전트가 지원되면 Goose 총괄과 전문 역할에 위임하고, 지원되지 않으면 한 대화에서 역할별로 순차 수행한 사실을 밝힙니다. 설치가 새로운 도구나 네이티브 에이전트 기능을 만들어 주지는 않습니다.

```text
사용자 요청 → Goose → 필요 시 심층 인터뷰 → 전문 업무 배정
           → 공시·뉴스·산업 원문 조사 → fact-check → 수정·편집 → HTML과 근거 파일
```

## 요청 예시

```text
$goose 삼성전자와 SK하이닉스의 수익성과 현금흐름을 같은 기간으로 비교해줘
$goose 이번 실적에서 본업과 일회성 손익을 나눠 설명해줘
$goose 이 뉴스의 원문과 후속 공시를 찾아 사실과 전망을 구분해줘
$goose 이 보고서의 숫자와 결론을 fact-check 해줘
$goose 내 자산 운영 목표와 기간을 인터뷰한 뒤 보유자산 점검을 도와줘
```

개인 계좌 자료는 외부 검색으로 보내지 않습니다. 목표·기간·현금 필요·감내 손실 없이 적정 비중을 만들어 내지 않습니다. 현재가와 환율은 출처·시점을 확인하고 미확보 값은 추정해 채우지 않습니다.

## 보고서 기준

- DART 본문·주석·검토자료, 회사 IR, 원뉴스, 산업·경쟁 자료의 직접 열람 범위와 출처를 기록합니다.
- 사실·전망·해석을 구분하고, 긍정 근거와 가장 강한 반대 근거를 함께 검토합니다.
- 모두의 주식 글자 로고, 회색 전자잉크 스타일, 고운바탕 제목·프리텐다드 본문 CDN을 사용합니다.
- 종목 전체 보고서는 결론 먼저, MoAI 오피니언 12문단·각 최소 5문장입니다. 분량 채우기가 아닌 논지·근거·반론·판단 변경 조건을 검토합니다.
- 관심종목 편입·관망·편입 보류는 조사 우선순위입니다. 매수·매도 또는 개인 계좌 비중과 구분합니다. 봉차트는 제외합니다.
- HTML에 입력 JSON·출처 장부·구조 검증 결과를 내장합니다. 구조 통과를 사실·편집 품질 인증으로 표시하지 않습니다.

[설치 후 보고서 품질 비교와 수정](docs/report-quality-review.md)

## 파일 구성과 개발

```text
skills/goose/
  SKILL.md                 # 유일한 설치 진입점
  VERSION
  agents/openai.yaml
  workflows/
    goosekr/               # 총괄·인터뷰·팀 역할
    stock-report/          # HTML 생성기·CSS·로고·조사 계약
    fact-check/            # 팩트체크
    portfolio-review/      # 보유자산 계산기
    ...                    # 나머지 전문 업무 GUIDE
```

```sh
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -v
python3 skills/goose/workflows/stock-report/tests/renderer-test.py
python3 -m unittest discover -s skills/goose/workflows/portfolio-review/tests -v
python3 scripts/build_distributions.py
```

명시적인 파일 목록으로 ZIP을 만들고 비밀·개인 입력·캐시를 제외합니다. Python 3.9 이상 표준 라이브러리만 사용하며 HTML 글꼴 로딩에 CDN 인터넷 연결이 필요합니다. 원문 조사는 실행 환경의 웹 검색·열람 기능을 이용합니다. MCP·금융 API·실계좌 주문은 현재 제공하지 않으며 추후 로드맵입니다.

## 설치와 실행 확인 범위

0.1.4 플러그인은 ChatGPT와 Claude에서 설치·버전 인식을 확인했고 ChatGPT에서 Goose 총괄 1개와 인터뷰 질문 3개 실행을 확인했습니다. 이 결과를 0.3.0 통합 스킬의 설치·조사 완료로 간주하지 않습니다. 현재 서비스별 ZIP 설치 검증 결과는 [플랫폼 안내](docs/platforms.md)에 구분해 기록합니다.

공식 안내: [ChatGPT Skills](https://help.openai.com/en/articles/20001066-skills-in-chatgpt) · [Claude Custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)

## 증시 마감과 예약 실습

Goose 0.3.0은 market-close 내부 지침과 재사용 입력 템플릿을 포함합니다. 국내·미국 정규장 지표, 뉴스, 반대 근거를 확인하고 HTML을 생성합니다. 예약은 각 호스트의 일정 기능으로 따로 등록하며 휴장·시차·자료 지연을 점검합니다. [실습과 실제 생성본](https://moai-stock.goos.chatgpt.site/learn/market-close)을 제공합니다.

0.2.0은 ChatGPT의 가상 계좌 계산·HTML 생성 및 Claude 지침 열람·스크립트 도움말 실행을 확인했습니다. 0.3.0은 로컬 구조·계산·생성과 패키징 검증 범위이며 서비스 재설치·실제 예약 실행은 별도 확인이 필요합니다.
