#!/usr/bin/env python3
"""Synthetic fixtures only: no investment or company facts in this test suite."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'render_report.py'
spec = importlib.util.spec_from_file_location('renderer', SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def fixture(name='가상회사 A', ticker='SYNTHETIC-A'):
    paragraph = {'type': 'paragraph', 'text': '실제 기업에 관한 주장이 아닌 합성 시험 문장입니다.', 'source_ids': ['synthetic'], 'status': 'inference'}
    provenance = {'source_ids': ['synthetic'], 'status': 'unverified'}
    context = {'period': '합성 기간 1–3', 'unit': '가상 단위', 'basis': '테스트 전용'}
    chart = {'type': 'chart', 'kind': 'bar', 'title': '합성 손익', 'categories': ['P1', 'P2', 'P3'],
             'series': [{'label': '합성 값', 'values': [-10, None, 30]}], **context, **provenance}
    opinion_paragraph = {'sentences': ['실제 기업의 투자 판단이 아닌 합성 문장입니다.'] * 5, 'source_ids': ['synthetic'], 'status': 'inference'}
    return {'schema_version': 1, 'company': {'name': name, 'ticker': ticker, 'market': 'SYNTHETIC'},
            'as_of': '합성 기준일', 'subtitle': '렌더러 시험용이며 투자 자료가 아닙니다.', 'status': 'draft',
            'limitations': ['모든 입력은 테스트를 위해 만든 가상 자료입니다.'],
            'sources': [{'id': 'synthetic', 'title': 'Synthetic test fixture', 'publisher': 'Test suite',
                         'published_at': 'not applicable — synthetic', 'period': 'synthetic only',
                         'accessed_at': 'not accessed — synthetic', 'url': 'https://example.com/synthetic',
                         'read_scope': 'No actual web source was read; synthetic test fixture only.',
                         'findings': 'No real-world factual claim.', 'status': 'unverified', 'verification': 'not_published',
                         'attempts': 'Not applicable to a synthetic test.', 'impact': 'Not for investment use.'}],
            'kpis': [{'label': '합성 결측 지표', 'value': None, 'definition': '결측 처리 시험', **context, **provenance}],
            'summary': [copy.deepcopy(paragraph)],
            'sections': [{'title': '합성 섹션 ' + str(i + 1), 'blocks': [copy.deepcopy(paragraph)] + ([chart] if i == 0 else [])} for i in range(9)],
            'opinion': {'decision': '관망', 'confidence': '낮음', 'lead': copy.deepcopy(paragraph),
                        'grounds': copy.deepcopy(paragraph), 'conditions': copy.deepcopy(paragraph),
                        'paragraphs': [copy.deepcopy(opinion_paragraph) for _ in range(12)]}}


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def test_portable_cli_preserves_original_and_records_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name, ticker in [('가상회사 A', 'SYNTHETIC-A'), ('Synthetic Company B', 'SYNTHETIC-B')]:
                source = base / (ticker + '.json')
                raw = json.dumps(fixture(name, ticker), ensure_ascii=False, indent=2).encode('utf-8')
                source.write_bytes(raw)
                output = base / ticker
                result = subprocess.run([sys.executable, str(SCRIPT), '--input', str(source), '--output-dir', str(output)], cwd=tmp, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((output / 'report-input.json').read_bytes(), raw)
                rendered = (output / 'report.html').read_text()
                self.assertIn(name, rendered)
                self.assertNotIn('SK하이닉스', rendered)
                self.assertNotIn('<script', rendered)
                self.assertIn('data:image/png;base64,', rendered)
                evidence = json.loads((output / 'render-validation.json').read_text())
                self.assertFalse(evidence['research_verified_by_renderer'])
                self.assertEqual(evidence['opinion_sentence_counts'], [5] * 12)

    def test_html_and_svg_text_are_escaped(self):
        injection = '<script>alert("x")</script><img src=x onerror=alert(1)>'
        self.data['company']['name'] = injection
        self.data['opinion']['paragraphs'][0]['sentences'][0] = injection + '.'
        self.data['sections'][0]['blocks'][1]['categories'][0] = injection
        rendered = renderer.render_html(self.data)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('<img src=x', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_rejects_unsafe_source_protocol_and_url_credentials(self):
        for url in ['javascript:alert(1)', 'data:text/html,bad', '//example.com', 'https://user:secret@example.com', 'https://example.com\\evil', 'https://example.com/\n']:
            with self.subTest(url=url):
                self.data['sources'][0]['url'] = url
                with self.assertRaises(renderer.ValidationError):
                    renderer.validate(self.data)

    def test_unknown_and_missing_source_references_rejected(self):
        for refs in [[], ['missing'], ['synthetic', 'synthetic']]:
            with self.subTest(refs=refs):
                self.data['summary'][0]['source_ids'] = refs
                with self.assertRaises(renderer.ValidationError):
                    renderer.validate(self.data)

    def test_provenance_metadata_required(self):
        for key in ['publisher', 'read_scope', 'period', 'accessed_at', 'findings', 'attempts']:
            data = fixture()
            del data['sources'][0][key]
            with self.subTest(key=key), self.assertRaises(renderer.ValidationError):
                renderer.validate(data)

    def test_cannot_upgrade_unread_source_to_verified(self):
        self.data['summary'][0]['status'] = 'verified'
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)
        self.data = fixture()
        self.data['status'] = 'verified'
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)
        rendered = renderer.render_html(fixture())
        self.assertIn('초안 · 미검증', rendered)
        self.assertIn('미확인 자료', rendered)
        self.assertNotIn('PASS', rendered)

    def test_chart_period_unit_and_kpi_value_required(self):
        for key in ['unit', 'period', 'basis']:
            for where in ['chart', 'kpi']:
                data = fixture()
                obj = data['kpis'][0] if where == 'kpi' else data['sections'][0]['blocks'][1]
                del obj[key]
                with self.subTest(key=key, where=where), self.assertRaises(renderer.ValidationError):
                    renderer.validate(data)
        del self.data['kpis'][0]['value']
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)

    def test_negative_bar_is_below_baseline_and_null_not_zero(self):
        chart = self.data['sections'][0]['blocks'][1]
        fragment = renderer.chart(chart, 1)
        svg = ElementTree.fromstring(re.search(r'<svg.*?</svg>', fragment).group())
        baseline = float(next(e for e in svg.findall('line') if e.get('class') == 'zero-baseline').get('y1'))
        bars = svg.findall('rect')
        self.assertEqual(len(bars), 2)
        self.assertAlmostEqual(float(bars[0].get('y')), baseline, places=2)
        self.assertGreater(float(bars[0].get('height')), 0)
        self.assertLess(float(bars[1].get('y')), baseline)
        self.assertIn('<td>미확인</td>', fragment)
        self.assertIn('<strong>미확인<small>', renderer.render_html(self.data))

    def test_line_does_not_bridge_missing_point(self):
        chart = self.data['sections'][0]['blocks'][1]
        chart['kind'] = 'line'
        fragment = renderer.chart(chart, 1)
        self.assertNotIn('<polyline', fragment)
        self.assertEqual(fragment.count('<circle'), 2)

    def test_zero_null_and_extreme_scales_have_finite_svg_geometry(self):
        for values in [[0, 0, 0], [None, None, None], [-1e308, 0, 1e308], [.0000001, .0000002, .0000003]]:
            chart = self.data['sections'][0]['blocks'][1]
            chart['series'][0]['values'] = values
            renderer.validate(self.data)
            fragment = renderer.chart(chart, 1)
            self.assertNotRegex(fragment, r'="(?:nan|inf|-inf)"')
            if values == [0, 0, 0]:
                self.assertEqual(fragment.count('height="0.00"'), 3)
            if values == [None, None, None]:
                self.assertNotIn('<rect', fragment)
                self.assertIn('표시할 수치가 아직 확인되지 않았습니다.', fragment)

    def test_sentence_array_avoids_decimal_url_false_counts(self):
        paragraph = self.data['opinion']['paragraphs'][0]
        paragraph['sentences'] = ['1.25라는 소수도 한 문장입니다.', 'https://example.com/source 의 자료도 한 문장입니다.', '이것도 한 문장입니다.', '네 번째 문장입니다.', '다섯 번째 문장입니다.']
        self.assertEqual(renderer.validate(self.data)['opinion_sentence_counts'][0], 5)
        paragraph['sentences'].pop()
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            for raw in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
                path.write_text(raw)
                with self.assertRaises(renderer.ValidationError):
                    renderer.read_input(path)
        self.data['kpis'][0]['value'] = True
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)

    def test_null_decision_requires_reason_and_selects_no_grade(self):
        self.data['opinion']['decision'] = None
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)
        self.data['opinion']['decision_reason'] = '핵심 지표가 미확인 상태이므로 판단을 유보합니다.'
        rendered = renderer.render_html(self.data)
        self.assertIn('판단 유보 — 근거 부족', rendered)
        self.assertIn('핵심 지표가 미확인 상태이므로 판단을 유보합니다.', rendered)
        scale = re.search(r'<div class="opinion-scale">(.*?)</div>', rendered).group(1)
        self.assertNotIn('selected', scale)
        for decision in renderer.DECISIONS:
            self.assertIn(decision, scale)
        del self.data['opinion']['decision']
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)

    def test_prior_record_is_not_presented_as_current_direct_read(self):
        source = self.data['sources'][0]
        source['status'] = 'read'
        source['verification'] = 'prior_record'
        rendered = renderer.render_html(self.data)
        self.assertIn('기존 열람 기록 대조', rendered)
        self.assertNotIn('이번 실행 직접 열람', rendered)
        source['verification'] = 'direct_read'
        self.assertIn('이번 실행 직접 열람', renderer.render_html(self.data))
        for verification in ('blocked', 'not_published'):
            source['verification'] = verification
            with self.assertRaises(renderer.ValidationError):
                renderer.validate(self.data)
        del source['verification']
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)

    def test_qualified_claim_keeps_caveat_and_original_claim_metadata(self):
        claim = self.data['summary'][0]
        claim['status'] = 'qualified'
        claim['original_claim'] = {'kind': 'forecast', 'status': 'qualified', 'reason': '합성 조건부 전망'}
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)
        claim['qualification'] = '합성 전망이며 확정 실적이 아닙니다.'
        rendered = renderer.render_html(self.data)
        self.assertIn('조건부 근거', rendered)
        self.assertIn('합성 전망이며 확정 실적이 아닙니다.', rendered)
        self.assertIn('href="#source-synthetic">[1]</a>', rendered)
        self.assertNotIn('href="#source-synthetic">[synthetic]</a>', rendered)
        self.assertEqual(claim['original_claim']['status'], 'qualified')

    def test_generic_portfolio_needs_no_fake_company_or_opinion(self):
        data = fixture()
        data['document_type'] = 'portfolio'
        data['document'] = {'title': '가상 포트폴리오 점검', 'subtitle': '시험용 자산 구성', 'context_label': '합성 보유 항목 2개'}
        for key in ('company', 'subtitle', 'opinion', 'summary', 'kpis'):
            del data[key]
        data['sections'] = data['sections'][:2]
        data['sections'][0]['blocks'].insert(0, {'type': 'heading', 'text': '업종별 집중도 <검토>'})
        rendered = renderer.render_html(data)
        self.assertIn('<h1>가상 포트폴리오 점검</h1>', rendered)
        self.assertIn('<h3>업종별 집중도 &lt;검토&gt;</h3>', rendered)
        self.assertNotIn('MoAI 오피니언', rendered)
        self.assertNotIn('가상회사 A', rendered)
        hero = re.search(r'<section class="report-hero">(.*?)</section>', rendered).group(1)
        self.assertNotIn('생성기', hero)
        self.assertNotIn('입력 선언', hero)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'input.json'
            source.write_text(json.dumps(data, ensure_ascii=False))
            output = Path(tmp) / 'portfolio'
            result = subprocess.run([sys.executable, str(SCRIPT), '--input', str(source), '--output-dir', str(output)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads((output / 'source-ledger.json').read_text())
            self.assertEqual(ledger['document']['title'], data['document']['title'])
            self.assertNotIn('company', ledger)

    def test_document_variants_allow_flexible_sections_and_optional_short_opinion(self):
        for document_type in ('comparison', 'earnings', 'event', 'portfolio', 'fact_check', 'briefing'):
            data = fixture()
            data['document_type'] = document_type
            data['sections'] = data['sections'][:1]
            data['opinion']['paragraphs'] = []
            rendered = renderer.render_html(data)
            self.assertIn('02. MoAI 오피니언', rendered)
            data['opinion']['paragraphs'] = [{'sentences': ['간결한 해석입니다.'], 'source_ids': ['synthetic'], 'status': 'inference'}]
            self.assertEqual(renderer.validate(data)['opinion_sentence_counts'], [1])
            self.assertIn('간결한 해석입니다.', renderer.render_html(data))
            data['sections'] = [copy.deepcopy(data['sections'][0]) for _ in range(12)]
            self.assertIn('13. MoAI 오피니언', renderer.render_html(data))
            data['sections'].append(copy.deepcopy(data['sections'][0]))
            with self.assertRaises(renderer.ValidationError):
                renderer.validate(data)

    def test_deep_defaults_remain_strict(self):
        for changed in ('company', 'opinion', 'sections', 'paragraphs'):
            data = fixture()
            if changed in ('company', 'opinion'):
                del data[changed]
            elif changed == 'sections':
                data['sections'] = data['sections'][:1]
            else:
                data['opinion']['paragraphs'] = []
            with self.subTest(changed=changed), self.assertRaises(renderer.ValidationError):
                renderer.validate(data)
        data = fixture()
        data['document_type'] = 'candlestick'
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(data)

    def test_local_sources_render_without_fake_external_url(self):
        source = self.data['sources'][0]
        for source_type in ('user_input', 'local_calculation'):
            source.update({'source_type': source_type, 'url': None, 'artifact_ref': 'synthetic-holdings-01',
                           'verification': 'direct_read', 'status': 'read'})
            rendered = renderer.render_html(self.data)
            self.assertIn('자료 식별명: synthetic-holdings-01', rendered)
            self.assertIn(renderer.LOCAL_SOURCE_TYPES[source_type], rendered)
            self.assertNotIn('https://example.com/synthetic', rendered)
            self.assertNotIn('href="None"', rendered)
            with tempfile.TemporaryDirectory() as tmp:
                source_path = Path(tmp) / 'input.json'
                source_path.write_text(json.dumps(self.data, ensure_ascii=False))
                output = Path(tmp) / 'report'
                result = subprocess.run([sys.executable, str(SCRIPT), '--input', str(source_path), '--output-dir', str(output)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                saved = json.loads((output / 'source-ledger.json').read_text())['sources'][0]
                self.assertIsNone(saved['url'])
                self.assertEqual(saved['artifact_ref'], 'synthetic-holdings-01')
                self.assertEqual(saved['verification'], 'direct_read')

    def test_local_reference_rejects_paths_urls_and_missing_scope(self):
        source = self.data['sources'][0]
        source.update({'source_type': 'user_input', 'url': None, 'artifact_ref': 'holdings-input-01'})
        for invalid in ('/Users/private/holdings.csv', '../holdings.csv', 'inputs/holdings.csv', 'C:\\Users\\private.csv', '~/private.csv', 'file:///private.csv', 'https://example.com/private', 'data:text/html,bad', '한글 경로', None):
            source['artifact_ref'] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(renderer.ValidationError):
                renderer.validate(self.data)
        source['artifact_ref'] = 'holdings-input-01'
        del source['read_scope']
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)
        self.data = fixture()
        self.data['sources'][0]['url'] = None
        self.data['sources'][0]['artifact_ref'] = 'pretend-news'
        with self.assertRaises(renderer.ValidationError):
            renderer.validate(self.data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
