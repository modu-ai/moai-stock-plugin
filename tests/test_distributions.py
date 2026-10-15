"""Portable archive checks; not authenticated platform installation tests."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('distributions', ROOT / 'scripts/build_distributions.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
ADAPTER_FILES = ('plugin.json', '.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', 'gemini-extension.json', 'GEMINI.md', 'assets/modu-stock-wordmark.png', 'assets/modu-stock-icon.png') + tuple('skills/' + skill + '/agents/openai.yaml' for skill in builder.SKILLS)


def copy_fixture(destination):
    for name in builder.RUNTIME + ADAPTER_FILES:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)


class DistributionTests(unittest.TestCase):
    def test_openai_skill_only_projection_retains_coordinator_definition(self):
        _, _, files = builder.collect(ROOT, 'openai')
        projected = {name: data for name, data in files.items() if name.startswith('skills/')}
        self.assertEqual(builder.local_link_errors(projected), [])
        self.assertIn('skills/goosekr/references/goose-agent.md', projected)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            command = root / 'skills/goose/SKILL.md'
            command.write_text(command.read_text().replace('../goosekr/references/goose-agent.md', '../../agents/goose.md'))
            with self.assertRaises(builder.BuildError):
                builder.collect(root, 'openai')

    def test_four_archives_reproducible_and_reference_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'first', Path(tmp) / 'second'
            a, b = builder.build(ROOT, first), builder.build(ROOT, second)
            self.assertEqual(a, b)
            self.assertFalse(a['host_installation_tested'])
            self.assertEqual(len(a['archives']), 4)
            for item in a['archives']:
                with zipfile.ZipFile(first / item['archive']) as archive:
                    names = archive.namelist()
                    self.assertEqual(len({name.split('/')[0] for name in names}), 1)
                    self.assertTrue(all('..' not in name.split('/') and not name.startswith('/') for name in names))
                    files = {name.split('/', 1)[1]: archive.read(name) for name in names}
                    self.assertEqual(builder.local_link_errors(files), [])
                    manifest = json.loads(files['DISTRIBUTION.json'])
                    self.assertEqual(set(manifest['canonical_skills']), set(builder.SKILLS))
                    if item['platform'] == 'browser-skill':
                        self.assertIn('SKILL.md', files)
                        self.assertEqual(sum(name.endswith('SKILL.md') for name in files), 1)
                        for skill in builder.SKILLS:
                            expected = (ROOT / 'skills' / skill / 'SKILL.md').read_bytes()
                            for sibling in builder.SKILLS:
                                expected = expected.replace(('../' + sibling + '/SKILL.md').encode(), ('../' + sibling + '/GUIDE.md').encode())
                            self.assertEqual(files['workflows/' + skill + '/GUIDE.md'], expected)
                    else:
                        for name in builder.RUNTIME:
                            self.assertEqual(files[name], (ROOT / name).read_bytes())

    def test_allowlist_omits_secrets_git_cache_and_user_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            copy_fixture(root)
            for name in ('.git/config', '.env', 'private/accounts.json', 'skills/stock-report/references/secrets.json', 'skills/stock-report/__pycache__/render.pyc', '.DS_Store'):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('SYNTHETIC_EXCLUDED_CONTENT')
            result = builder.build(root, Path(tmp) / 'out')
            for item in result['archives']:
                with zipfile.ZipFile(Path(tmp) / 'out' / item['archive']) as archive:
                    self.assertFalse(any('SYNTHETIC_EXCLUDED_CONTENT' in archive.read(n).decode('utf-8', errors='ignore') for n in archive.namelist()))
                    self.assertFalse(any('.git/' in n or '__pycache__/' in n or '.env' in n for n in archive.namelist()))

    def test_private_content_in_allowlisted_file_blocks_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            copy_fixture(root)
            target = root / 'skills/stock-report/references/report-standard.md'
            target.write_text(target.read_text() + '\n/Users/example-user/private/report.json\n')
            with self.assertRaises(builder.BuildError):
                builder.build(root, Path(tmp) / 'out')

    def test_symlink_cannot_pull_external_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            copy_fixture(root)
            outside = Path(tmp) / 'outside.md'
            outside.write_text('SYNTHETIC_PRIVATE_FILE')
            target = root / 'skills/stock-report/references/report-standard.md'
            target.unlink()
            target.symlink_to(outside)
            with self.assertRaises(builder.BuildError):
                builder.build(root, Path(tmp) / 'out')

    def test_broken_sibling_reference_and_manifest_services_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            copy_fixture(root)
            target = root / 'skills/stock-analyst/SKILL.md'
            target.write_text(target.read_text() + '\n[missing](../stock-report/references/missing.md)\n')
            with self.assertRaises(builder.BuildError):
                builder.collect(root, 'browser-skill')
            shutil.copyfile(ROOT / 'skills/stock-analyst/SKILL.md', target)
            manifest_path = root / 'gemini-extension.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['mcpServers'] = {}
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(builder.BuildError):
                builder.collect(root, 'gemini-cli')

    def test_extracted_browser_scripts_run_and_relative_assets_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            result = builder.build(ROOT, out)
            filename = next(a['archive'] for a in result['archives'] if a['platform'] == 'browser-skill')
            unpacked = Path(tmp) / 'extracted'
            with zipfile.ZipFile(out / filename) as archive:
                archive.extractall(unpacked)
            bundle = unpacked / 'moai-stock-browser'
            renderer = bundle / 'workflows/stock-report/scripts/render_report.py'
            calculator = bundle / 'workflows/portfolio-review/scripts/portfolio_calc.py'
            self.assertTrue((renderer.parent.parent / 'assets/modu-stock-wordmark.png').is_file())
            for script in (renderer, calculator):
                run = subprocess.run([sys.executable, str(script), '--help'], cwd=unpacked, text=True, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr)
            # Use only the repository's clearly labeled synthetic fixture.
            calculation_output = Path(tmp) / 'calculation.json'
            run = subprocess.run([sys.executable, str(calculator), str(ROOT / 'skills/portfolio-review/tests/synthetic-input.json'), '--output', str(calculation_output)], cwd=unpacked, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(calculation_output.read_text())['totals']['market_value_base'], '1500.000000')
            report_output = Path(tmp) / 'rendered'
            run = subprocess.run([sys.executable, str(renderer), '--input', str(ROOT / 'examples/briefing/report-input.json'), '--output-dir', str(report_output)], cwd=unpacked, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('data:image/png;base64,', (report_output / 'report.html').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
