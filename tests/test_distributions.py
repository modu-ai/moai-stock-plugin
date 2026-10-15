"""Single skill portability, containment and real extracted script tests."""
import hashlib
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

def copy_fixture(root):
    for name in builder.RUNTIME:
        target = root / 'skills/goose' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'skills/goose' / name, target)

class DistributionTests(unittest.TestCase):
    def test_one_skill_all_modules_reproducible_and_reference_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = builder.build(ROOT, Path(tmp) / 'a')
            b = builder.build(ROOT, Path(tmp) / 'b')
            self.assertEqual(a, b)
            with zipfile.ZipFile(Path(tmp) / 'a' / a['archive']) as z:
                files = {n.removeprefix('goose/'): z.read(n) for n in z.namelist()}
                self.assertTrue(all(n.startswith('goose/') for n in z.namelist()))
                self.assertEqual(sum(n.endswith('SKILL.md') for n in files), 1)
                self.assertEqual(builder.local_link_errors(files), [])
                self.assertFalse(any('plugin.json' in n or 'marketplace' in n for n in files))
                meta = json.loads(files['DISTRIBUTION.json'])
                self.assertEqual(meta['installed_skills'], ['goose'])
                self.assertIn('fact-check', meta['internal_modules'])
                self.assertNotIn('claim-check', meta['internal_modules'])
                for item in meta['files']:
                    self.assertEqual(hashlib.sha256(files[item['path']]).hexdigest(), item['sha256'])

    def test_allowlist_omits_private_inputs_and_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_fixture(root)
            extra = root / 'skills/goose/private/account.json'
            extra.parent.mkdir(); extra.write_text('SYNTHETIC_SECRET')
            _, files = builder.collect(root)
            self.assertFalse(any('SYNTHETIC_SECRET' in b.decode(errors='ignore') for b in files.values()))
            self.assertNotIn('private/account.json', files)

    def test_nested_skill_discovery_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); copy_fixture(root)
            (root / 'skills/goose/workflows/fact-check/SKILL.md').write_text('nested')
            with self.assertRaises(builder.BuildError): builder.collect(root)

    def test_reference_cannot_depend_on_plugin_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); copy_fixture(root)
            p = root / 'skills/goose/SKILL.md'
            p.write_text(p.read_text() + '\n[root dependency](../../agents/goose.md)\n')
            with self.assertRaises(builder.BuildError): builder.collect(root)

    def test_private_path_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); copy_fixture(root)
            p = root / 'skills/goose/workflows/fact-check/GUIDE.md'
            p.write_text('/Users/example-user/private/account.json')
            with self.assertRaises(builder.BuildError): builder.collect(root)
            p.unlink(); outside = root / 'outside'; outside.write_text('secret'); p.symlink_to(outside)
            with self.assertRaises(builder.BuildError): builder.collect(root)

    def test_extracted_scripts_run_from_unrelated_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); result = builder.build(ROOT, root / 'dist')
            with zipfile.ZipFile(root / 'dist' / result['archive']) as z: z.extractall(root / 'extracted')
            skill = root / 'extracted/goose'
            renderer = skill / 'workflows/stock-report/scripts/render_report.py'
            calculator = skill / 'workflows/portfolio-review/scripts/portfolio_calc.py'
            report = subprocess.run([sys.executable, str(renderer), '--input', str(ROOT / 'examples/briefing/report-input.json'), '--output-dir', str(root / 'report')], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertIn('data:image/png;base64,', (root / 'report/report.html').read_text())
            calc = subprocess.run([sys.executable, str(calculator), str(ROOT / 'skills/goose/workflows/portfolio-review/tests/synthetic-input.json'), '--output', str(root / 'calculation.json')], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(calc.returncode, 0, calc.stderr)
            self.assertEqual(json.loads((root / 'calculation.json').read_text())['totals']['market_value_base'], '1500.000000')

if __name__ == '__main__': unittest.main(verbosity=2)
