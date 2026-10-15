#!/usr/bin/env python3
"""Offline synthetic demonstrations; no real holdings, live prices, or news."""
from decimal import Decimal
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RENDERER = ROOT / 'skills/goose/workflows/stock-report/scripts/render_report.py'
CALCULATOR = ROOT / 'skills/goose/workflows/portfolio-review/scripts/portfolio_calc.py'


class LinkCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if 'id' in attributes:
            self.ids.add(attributes['id'])
        if tag == 'a':
            self.links.append(attributes.get('href', ''))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def number(value):
    if value is None:
        return None
    value = Decimal(value)
    return int(value) if value == value.to_integral_value() else float(value)


def paragraph(text, sources=('synthetic-input',), status='verified'):
    return {'type': 'paragraph', 'text': text, 'source_ids': list(sources), 'status': status}


def source(sid, title, kind, alias, scope, findings):
    return {'id': sid, 'title': title, 'publisher': '플러그인 합성 예시 작성자',
            'source_type': kind, 'url': None, 'artifact_ref': alias,
            'published_at': '2026-10-16 · 합성 예시 고정 기준일',
            'period': '가상 입력 스냅샷', 'accessed_at': '재생성 시 로컬 예시 파일 읽기',
            'status': 'read', 'verification': 'direct_read', 'read_scope': scope, 'findings': findings}


def build_portfolio():
    folder = HERE / 'portfolio'
    input_path = folder / 'portfolio-input.json'
    calculation_path = folder / 'calculation.json'
    subprocess.run([sys.executable, str(CALCULATOR), str(input_path), '--output', str(calculation_path)], check=True)
    original = json.loads(input_path.read_text(encoding='utf-8'))
    result = json.loads(calculation_path.read_text(encoding='utf-8'))
    # Independent arithmetic over this intentionally all-KRW synthetic fixture.
    assert all(h['cost_currency'] == h['price_currency'] == 'KRW' for h in original['holdings'])
    assert all(c['currency'] == 'KRW' for c in original['cash'])
    stock_cost = sum(Decimal(h['quantity']) * Decimal(h['average_cost']) for h in original['holdings'])
    stock_value = sum(Decimal(h['quantity']) * Decimal(h['current_price']) for h in original['holdings'])
    cash = sum(Decimal(c['amount']) for c in original['cash'])
    assert Decimal(result['totals']['cost_basis_base']) == stock_cost
    assert Decimal(result['totals']['market_value_base']) == stock_value + cash
    assert Decimal(result['totals']['unrealized_pnl_base']) == stock_value - stock_cost
    assert result['rebalance']['status'] == 'not_requested'
    money_context = {'period': original['as_of'] + ' · 가상 기준', 'basis': '제공된 합성 자산 범위', 'unit': '원',
                     'source_ids': ['synthetic-calculation'], 'status': 'verified'}
    totals = result['totals']
    kpis = []
    for label, key, definition, unit in [
        ('가상 자산 평가액', 'market_value_base', '가상 주식 평가액과 현금을 합산한 값', '원'),
        ('가상 주식 매입원가', 'cost_basis_base', '수량 × 주당 평균 매입가; 현금 제외', '원'),
        ('가상 미실현 손익', 'unrealized_pnl_base', '주식 평가액 − 주식 매입원가', '원'),
        ('가상 미실현 손익률', 'unrealized_pnl_percent', '미실현 손익 ÷ 주식 매입원가; 세금·배당 제외', '%')]:
        kpis.append({**money_context, 'label': label, 'value': number(totals[key]), 'definition': definition, 'unit': unit})
    rows = [[h['ticker'], number(h['quantity']), number(h['cost_basis_base']), number(h['market_value_base']), number(h['unrealized_pnl_base'])] for h in result['holdings']]
    distribution_rows = [[h['ticker'], number(h['market_value_base']), number(h['allocation_percent'])] for h in result['holdings']]
    distribution_rows += [['가상 현금', number(c['market_value_base']), number(c['allocation_percent'])] for c in result['cash']]
    source_input = source('synthetic-input', '합성 보유 자산 입력', 'user_input', 'synthetic-portfolio-input', '가상 보유 종목·수량·평균 매입가·가정 가격·현금 전체', '모든 종목·가격은 작성된 가정입니다. 실제 계좌나 현재 시세를 뜻하지 않습니다.')
    source_calc = source('synthetic-calculation', '합성 입력을 이용한 실제 계산 결과', 'local_calculation', 'synthetic-portfolio-calculation', 'portfolio_calc의 총액·개별 손익·비중·집중도·범위 경고', '계산기를 실행하고 입력에서 별도로 합산한 원가·평가액·손익과 대조했습니다. 입력 가격의 현실성이나 투자 판단을 검증하지 않았습니다.')
    source_calc['input_source_ids'] = ['synthetic-input']
    source_calc['input_sha256'] = hashlib.sha256(input_path.read_bytes()).hexdigest()
    report = {'schema_version': 1, 'document_type': 'portfolio',
              'document': {'title': '가상 데이터 · 포트폴리오 점검', 'subtitle': '보유 현황과 손익, 집중도를 한 흐름으로 읽습니다', 'context_label': '합성 종목 3개와 가상 현금 · 실제 계좌 아님'},
              'as_of': original['as_of'] + ' · 합성 예시', 'status': 'limited',
              'limitations': ['모든 종목·수량·매입가·평가가격은 합성 데이터입니다. 실제 시세를 조회하지 않았습니다.', '제공 범위는 partial입니다. 전체 재산·부채·생활비·투자 목적을 확인하지 않았습니다.', '목표 비중과 매매 시나리오는 입력되지 않아 제안하거나 계산하지 않았습니다.'],
              'sources': [source_input, source_calc], 'kpis': kpis,
              'summary': [paragraph('이 페이지는 가상 보유 자산을 읽고 계산 결과를 보고서에 연결하는 예시입니다. 실제 투자자의 계좌나 시장 상황을 설명하지 않습니다.'), paragraph(f"가상 평가액은 {number(totals['market_value_base']):,}원이며 현금을 포함합니다. 가상 미실현 손익 {number(totals['unrealized_pnl_base']):,}원의 분모에는 주식 매입원가만 사용합니다.", ('synthetic-calculation',))],
              'sections': [
                  {'title': '제공 범위와 계산 기준', 'blocks': [paragraph('가상의 세 종목은 모두 원화 기준입니다. 주당 평균 매입가와 수량으로 원가를 계산하고 가정 가격으로 평가액을 계산했습니다. 현금은 자산 평가액에 포함하지만 주식 손익률의 분모에는 포함하지 않습니다.', ('synthetic-input', 'synthetic-calculation'))]},
                  {'title': '보유 현황과 미실현 손익', 'blocks': [
                      {'type': 'table', 'title': '가상 보유 종목별 계산', **money_context, 'unit': '수량: 주 / 금액: 원', 'headers': ['가상 종목', '수량', '매입원가', '평가액', '미실현 손익'], 'rows': rows},
                      {'type': 'chart', 'kind': 'bar', 'title': '가상 종목별 미실현 손익', **money_context, 'categories': [h['ticker'] for h in result['holdings']], 'series': [{'label': '가상 미실현 손익', 'values': [number(h['unrealized_pnl_base']) for h in result['holdings']]}]}]},
                  {'title': '현금을 포함한 자산 비중', 'blocks': [
                      {'type': 'table', 'title': '제공된 가상 자산의 평가 비중', **money_context, 'unit': '평가액: 원 / 비중: %', 'headers': ['가상 항목', '평가액', '비중'], 'rows': distribution_rows},
                      {'type': 'chart', 'kind': 'bar', 'title': '가상 업종별 집중도', **money_context, 'unit': '%', 'categories': [g['name'] for g in result['sector_concentration']['groups']], 'series': [{'label': '제공 범위의 현금 포함 평가액 대비 비중', 'values': [number(g['weight_percent']) for g in result['sector_concentration']['groups']]}]},
                      paragraph('같은 가상 업종에 속한 자산은 함께 묶어 표시했습니다. 이 비중만으로 적정 배분이나 실제 위험 수준을 판단하지 않습니다.', ('synthetic-input', 'synthetic-calculation'), 'inference')]},
                  {'title': '다음 분석에 필요한 조건', 'blocks': [
                      {'type': 'heading', 'text': '목적과 제약을 먼저 확인합니다'},
                      paragraph('투자 기간, 예정 인출, 손실 감내 범위와 목표 비중이 입력되지 않았습니다. 이번 예시는 현황 계산에서 멈추며 매수·매도 의견이나 목표 배분을 만들지 않습니다. 실제 상담에서는 사용자가 제공한 목적과 제약을 확인한 뒤 별도로 검토해야 합니다.', ('synthetic-input', 'synthetic-calculation'), 'inference')]}
              ]}
    report_path = folder / 'report-input.json'
    write(report_path, report)
    return report_path, {'example': 'portfolio', 'arithmetic_checks': 4, 'real_world_inputs': False,
                         'computed_market_value': totals['market_value_base'], 'computed_unrealized_pnl': totals['unrealized_pnl_base']}


def main():
    portfolio_input, portfolio_evidence = build_portfolio()
    notes = json.loads((HERE / 'briefing/synthetic-notes.json').read_text(encoding='utf-8'))
    briefing = json.loads((HERE / 'briefing/report-input.json').read_text(encoding='utf-8'))
    briefing_text = [block.get('text') for section in briefing['sections'] for block in section['blocks']]
    assert all(note in briefing_text for note in notes['notes']), 'Briefing must retain its actual synthetic source notes.'
    inputs = [portfolio_input, HERE / 'briefing' / 'report-input.json']
    for input_path in inputs:
        subprocess.run([sys.executable, str(RENDERER), '--input', str(input_path), '--output-dir', str(input_path.parent / 'output')], check=True)
        rendered = (input_path.parent / 'output/report.html').read_text(encoding='utf-8')
        assert '가상 데이터' in rendered
        assert 'file://' not in rendered and '/Users/' not in rendered
        assert '<script' not in rendered
        assert (input_path.parent / 'output/report-input.json').read_bytes() == input_path.read_bytes()
        parser = LinkCheck()
        parser.feed(rendered)
        for href in parser.links:
            if href.startswith('#'):
                assert href[1:] in parser.ids, 'Missing internal anchor: ' + href
            elif not href.startswith(('https:', 'http:')):
                assert (input_path.parent / 'output' / href).is_file(), 'Missing linked output: ' + href
    write(HERE / 'validation.json', {'status': 'local_generation_checks_passed', 'scope': 'Synthetic input arithmetic, renderer structural checks, byte-preserved inputs; no browser/PDF or investment assessment.',
                                   'portfolio': portfolio_evidence, 'briefing': {'example': 'briefing', 'real_world_inputs': False}, 'html_link_checks': '2 documents: internal anchors and local downloads exist', 'network_fetches': 0})
    print('Synthetic portfolio and briefing examples regenerated; arithmetic and structural checks passed.')


if __name__ == '__main__':
    main()
