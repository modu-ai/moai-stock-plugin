# 플랫폼별 패키지와 검증 범위

공통 업무 원본은 `skills/`의 8개 스킬입니다. 플랫폼마다 분석 내용을 따로 관리하지 않고 얇은 manifest·실행 맥락·업로드 묶음만 추가합니다. 서버·MCP·API 키·자동 실행 훅은 추가하지 않습니다. 공식 문서 확인일은 2026-10-16입니다.

| 대상 | 준비된 형식 | 현재 확인 범위 |
|---|---|---|
| 기존 ChatGPT/Codex 경로 | 루트 `plugin.json` + 공통 `skills/` | 기존 패키지를 유지. 이번 어댑터 검증으로 계정 설치를 증명하지 않음 |
| Claude Code | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `skills/` | 로컬 공식 validator 실행. 실제 설치·자연어 분석은 별도 |
| Claude 웹·Desktop | 사용자 플러그인 파일 또는 브라우저용 통합 스킬 ZIP | 문서상 설치 경로와 패키지 구조 확인. 계정 업로드·실행 미검증 |
| Gemini CLI | `gemini-extension.json`, `GEMINI.md`, 공통 `skills/` | 로컬 공식 validator·참조 및 압축해제 스크립트 실행 검증. 확장 설치·모델 실행 미검증 |
| Gemini 웹 Skills | 단일 `moai-stock-browser` 폴더의 `SKILL.md`와 모든 참조 파일 | 공식 업로드 형식에 맞춘 묶음. 계정별 제공 여부·업로드·모델 실행 미검증 |

## Claude

Claude Code는 플러그인 루트의 `.claude-plugin/plugin.json`과 `skills/` 구조를 읽습니다. 이 저장소의 마켓플레이스 항목은 `source:"./"`로 같은 루트 플러그인을 가리킵니다. [공식 manifest 규약](https://code.claude.com/docs/en/plugins-reference), [마켓플레이스 규약](https://code.claude.com/docs/en/plugin-marketplaces).

저장소 배포 후 사용할 설치 경로:

```text
/plugin marketplace add modu-ai/moai-stock-plugin
/plugin install moai-stock-plugin@modu-ai-stock
```

개발 검증은 플러그인 루트에서 `claude plugin validate .` 및 `claude plugin validate .claude-plugin/plugin.json`으로 수행합니다. 검증은 manifest를 확인하는 단계이며 계정 설치나 분석 성공과 다릅니다.

Claude 웹은 Customize의 Plugins에서 사용자 플러그인 파일을 추가할 수 있습니다. 스킬 파일로 가져오는 경우에는 단일 이름 폴더 아래 `SKILL.md`와 자원을 둔 ZIP을 사용합니다. 웹 대화에 네이티브 하위 에이전트가 없으면 공통 역할을 순차 수행합니다. [공식 플러그인 안내](https://support.claude.com/en/articles/13837440-use-plugins-in-claude), [사용자 스킬 포장 규약](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).

## Gemini CLI

확장 루트의 `gemini-extension.json`이 `GEMINI.md`를 연결하고 기존 `skills/`를 유지합니다. 로컬 Gemini CLI에서 `gemini extensions validate .`의 성공을 확인했습니다. 설치가 필요할 때 사용하는 공식 명령 형식은 아래와 같습니다. 이 문서 작성 과정에서 실제 설치는 수행하지 않았습니다. [공식 확장 규약](https://geminicli.com/docs/extensions/reference/), [공식 스킬 탐색 규약](https://geminicli.com/docs/cli/skills/).

```sh
gemini extensions install https://github.com/modu-ai/moai-stock-plugin
```

압축 파일을 이용한다면 먼저 풀고 `gemini extensions install ./moai-stock-plugin`으로 해당 폴더를 지정합니다. CLI의 현재 도구·권한·스킬 활성화 동의에 따라 실행 범위가 달라집니다. `GEMINI.md`는 없는 도구나 병렬 실행을 가정하지 않고 순차 수행 경로를 안내합니다.

## Gemini 웹과 브라우저용 통합 스킬

공식 Gemini 안내는 `SKILL.md`가 주 폴더에 있는 폴더·ZIP 업로드와 참조 파일을 지원합니다. 개인 계정부터 점진 제공되므로 해당 계정의 Skills 메뉴를 확인해야 합니다. 현재 스크립트의 외부 웹 요청은 지원되지 않고, Skills와 Canvas·Deep Research의 동시 사용도 지원되지 않는다고 안내합니다. 이 플러그인의 계산·렌더 스크립트는 외부 요청이 없으며 심층 조사는 원문 대조 방법을 뜻합니다. [스킬 생성·업로드 규약](https://support.google.com/gemini/answer/17094296?hl=en), [기능 제약 안내](https://support.google.com/gemini/answer/18560919?hl=en).

브라우저 패키지는 하나의 `moai-stock-browser` 스킬입니다. 내부 8개 업무 지침은 참조용 `GUIDE.md`로 변환하여 중첩 스킬 자동 등록에 의존하지 않습니다. 형제 경로와 계산기·로고·CSS의 상대 위치를 유지하므로 한 업무 ZIP에 공유 자료가 빠지는 문제를 피합니다. 원본은 계속 공통 `skills/`에서만 수정합니다.

```text
moai-stock-browser/
  SKILL.md
  DISTRIBUTION.json
  workflows/
    stock-analyst/GUIDE.md
    stock-report/GUIDE.md
    stock-report/references/...
    stock-report/scripts/render_report.py
    stock-report/assets/...
    portfolio-review/GUIDE.md
    portfolio-review/scripts/portfolio_calc.py
    ...나머지 업무 지침
```

## 아카이브 생성과 검증

기존 Codex의 로컬 CLI 도움말에서는 마켓플레이스 추가에 `codex plugin marketplace add owner/repo`, 플러그인 추가에 `codex plugin add name@marketplace`를 사용합니다. `install` 하위 명령으로 바꾸어 안내하지 않습니다. 현재 설치 검증은 수행하지 않았으며, 파일 형식과 명령 도움말 확인을 실제 등록·설치 성공으로 취급하지 않습니다.

플러그인 루트에서:

```sh
python3 scripts/build_distributions.py
python3 tests/test_distributions.py
```

`dist/`에 버전이 포함된 Claude·Gemini CLI·브라우저 스킬 ZIP과 `build-validation.json`을 만듭니다. 각 ZIP은 하나의 최상위 폴더를 포함합니다. `dist/.gitignore`가 생성 파일의 기본 커밋을 막으며 릴리스 자산 업로드는 별도의 배포 단계입니다. 빌드는 네트워크 호출이나 계정 설정 변경을 수행하지 않습니다.

명시적 런타임 허용 목록으로 원본을 선택하므로 `.git`, 캐시, 환경 파일, 개인 계좌 자료, 예시 출력은 포함하지 않습니다. 허용 파일 안의 개인 홈 경로·대표 비밀키 형식도 검사하고 파일 심볼릭 링크 및 묶음 밖으로 향하는 참조는 거부합니다. 이는 알려진 누출 방지 검사이며 모든 가능한 비밀을 찾아내는 보안 인증은 아닙니다. `DISTRIBUTION.json`에는 원본 상대경로와 파일 해시가 들어갑니다.

로컬 테스트는 세 패키지의 반복 생성 동일성, 내부 참조 완결성, 금지 파일 제외·경로 차단, 압축해제한 계산기의 합성 입력 계산, 렌더러의 합성 브리핑 HTML 생성을 확인합니다. 공식 서비스의 로그인·업로드·스킬 선택·원문 검색·모델 분석·화면 표시는 별도 수용 테스트로 남습니다. 설치 지원 형식을 준비한 것과 모든 플랫폼에서 실제 사용 검증을 마친 것을 구분합니다.
