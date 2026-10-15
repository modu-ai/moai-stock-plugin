# 합성 데이터로 확인하는 공통 리포트 템플릿

이 폴더에는 실제 보유 자산·기업·현재 시세·뉴스가 없습니다. 모든 종목과 입력은 시연용 합성 데이터이며 투자 판단 자료가 아닙니다. 승인된 전자잉크 테마·글자 로고·서체를 서로 다른 문서 구조에 적용하는 예시입니다.

## 결과 열기

- [가상 포트폴리오 점검 HTML](portfolio/output/report.html): 가상 종목 3개와 현금을 실제 계산기에 입력하여 원가·평가액·손익·업종 집중도를 계산하고 연결했습니다. 목표 비중이나 거래 시나리오를 만들지 않습니다.
- [가상 리서치 브리핑 HTML](briefing/output/report.html): 합성 메모 두 건을 짧은 분석 구조로 표시합니다. 실제 기업 근거가 없으므로 판단 카드는 유보 상태입니다.

HTML에 로고·스타일·차트를 내장합니다. 열 때 CDN 서체를 읽을 수 있지만 재생성 과정은 네트워크를 호출하지 않습니다. 개인정보나 원본 입력을 외부에 보내는 기능은 없습니다. 브라우저·PDF 출력은 별도 확인 대상입니다.

## 재생성

플러그인 루트에서 실행합니다. Python 3 표준 라이브러리만 필요합니다.

```sh
python3 examples/rebuild_examples.py
```

위 명령은 다음을 순서대로 처리합니다.

1. `portfolio/portfolio-input.json`을 실제 `portfolio_calc.py`로 계산하여 `portfolio/calculation.json`에 저장합니다.
2. 입력에서 원가·평가액·손익을 별도로 합산하고 계산 결과와 대조합니다. 목표 시나리오가 요청되지 않았는지도 확인합니다.
3. 계산 결과에서 KPI·표·차트를 구성한 `portfolio/report-input.json`을 만듭니다.
4. 브리핑 원문 메모가 보고서 입력의 문단에 보존됐는지 확인합니다.
5. 두 입력을 공통 렌더러로 변환하고 각각 `output/`에 HTML·입력 복사본·자료 장부·구조 검증 기록을 저장합니다.
6. `validation.json`에 검증 범위를 남깁니다. 이 검사는 사실 검증·투자 판단·브라우저 렌더 품질을 인증하지 않습니다.

개별 실행:

```sh
python3 skills/portfolio-review/scripts/portfolio_calc.py examples/portfolio/portfolio-input.json --output examples/portfolio/calculation.json
python3 skills/stock-report/scripts/render_report.py --input examples/portfolio/report-input.json --output-dir examples/portfolio/output
python3 skills/stock-report/scripts/render_report.py --input examples/briefing/report-input.json --output-dir examples/briefing/output
```

계산 입력을 수정했다면 전체 재생성 명령을 사용해야 보고서 값까지 갱신됩니다. 이 예시 재생성기는 원화 기준의 완전한 합성 평가값과 목표 미제공 상태를 전제로 합니다. 결측·외화·목표 시나리오는 계산기 테스트와 별도 보고서 입력으로 검증합니다. 실제 계좌 내용을 이 공개 예시 폴더에 넣지 않습니다.

## 보존한 근거

| 파일 | 내용 |
|---|---|
| `portfolio/portfolio-input.json` | 가상 수량·평단·평가가격·현금 |
| `portfolio/calculation.json` | 실제 계산기의 십진 문자열 결과·비중·한계 |
| `portfolio/report-input.json` | 계산 결과를 참조하는 렌더러 입력 |
| `briefing/synthetic-notes.json` | 합성 리서치 메모 원문 |
| `briefing/report-input.json` | 브리핑 구조와 판단 유보 카드 |
| 각 `output/report-input.json` | 렌더링에 사용한 입력의 바이트 동일 복사본 |
| 각 `output/source-ledger.json` | 로컬 자료 식별명과 확인 범위 |
| 각 `output/render-validation.json` | 구조·출처 연결·문장 수 검사와 입력 해시 |
| `validation.json` | 예시 재생성·계산 대조 범위 |

사용자 입력형 자료는 `source_type:user_input`, 계산 결과는 `source_type:local_calculation`입니다. 두 유형 모두 `url:null`과 문서용 `artifact_ref` 별칭을 사용합니다. 실제 파일 경로를 외부 링크로 만들지 않으며 `verification`과 직접 확인 범위를 별도로 남깁니다. 자료가 합성이라는 표시를 삭제하거나 `read` 상태를 실제 시장 자료의 검증으로 해석하지 않습니다.
