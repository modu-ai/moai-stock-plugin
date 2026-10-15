---
name: stock-report
description: 특정 상장기업을 공시·뉴스·산업 원문으로 심층 조사하여 출처와 반론을 포함한 HTML 보고서 및 MoAI 오피니언을 작성합니다.
---

# 종목 심층 분석과 최종 보고서

[조사 계약](references/research-contract.md), [역할 계약](references/agent-team.md), [보고서 기준](references/report-standard.md)을 읽습니다. 입력은 대상기업·기준일·요청범위이며 전 단계 산출물이 있으면 함께 받습니다.

- standalone: 공시·재무, 뉴스, 산업·경쟁 조사 역할을 구성합니다. earnings-review, event-impact, peer-compare를 필요한 범위의 leaf로 연결하고 공통 원장을 통합합니다. claim-check로 독립 검토 후 수정합니다.
- render: 전달된 원장·검토 결과로 편집합니다. 해결되지 않은 중요 주장이나 새 문장이 생기면 해당 주장만 재검토에 돌립니다. 보고서 생성 과정이 조사 완료 상태를 임의로 올리지 않습니다.
- leaf: 담당 보고서 또는 편집 결과만 반환하고 총괄 스킬을 재호출하지 않습니다.

[입력 형식](references/report-input.md)에 맞춰 구조화 데이터를 만들고 scripts/render_report.py를 사용합니다. 결과를 별도 기업/기준일 경로에 저장합니다. 보고서의 숫자·판단·날짜는 입력에서 가져오며 과거 사례를 그대로 재사용하지 않습니다. Markdown 원문·HTML·구조화 입력·출처/계산·검토 기록을 함께 전달합니다.
