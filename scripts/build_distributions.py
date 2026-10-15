#!/usr/bin/env python3
"""Build the self-contained Goose skill ZIP from an explicit runtime allowlist."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('goosekr', 'stock-analyst', 'stock-report', 'peer-compare', 'earnings-review',
           'event-impact', 'watchlist-review', 'fact-check', 'portfolio-review', 'market-close')
RUNTIME = ('SKILL.md', 'VERSION', 'agents/openai.yaml') + tuple('workflows/' + name + '/GUIDE.md' for name in MODULES) + (
    'workflows/market-close/references/scheduling.md',
    'workflows/market-close/references/close-template.json',
    'workflows/goosekr/references/goose-agent.md',
    'workflows/stock-report/references/agent-team.md',
    'workflows/stock-report/references/report-input.md',
    'workflows/stock-report/references/report-standard.md',
    'workflows/stock-report/references/research-contract.md',
    'workflows/stock-report/references/workflow-map.json',
    'workflows/stock-report/scripts/render_report.py',
    'workflows/stock-report/assets/report.css',
    'workflows/stock-report/assets/modu-stock-wordmark.png',
    'workflows/stock-report/assets/modu-stock-icon.png',
    'workflows/portfolio-review/references/portfolio-input.md',
    'workflows/portfolio-review/scripts/portfolio_calc.py',
)
FORBIDDEN_PARTS = {'.git', '.env', '.aws', '.ssh', '.codex', '.agents', '__pycache__', 'private', 'node_modules', '.DS_Store'}
TEXT_SUFFIXES = {'.md', '.json', '.yaml', '.yml', '.py', '.css', '.txt', '.toml', '.html', '.svg'}
PRIVATE_CONTENT = (
    re.compile(r'/(?:Users|home)/[A-Za-z0-9._-]+/'),
    re.compile(r'[A-Za-z]:\\Users\\[^\\\s]+\\'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{32,})\b'),
)


class BuildError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BuildError(message)


def safe_name(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name,
            'Unsafe archive path')
    require(not any(p in FORBIDDEN_PARTS or p.startswith('.env') for p in path.parts),
            'Private/cache file cannot be packaged')
    require(path.suffix not in {'.pyc', '.pyo', '.pem', '.key'}, 'Secret or compiled file cannot be packaged')
    return name


def read_allowed(root, relative):
    safe_name(relative)
    path = root / relative
    require(path.is_file(), 'Missing required runtime file: ' + relative)
    require(not path.is_symlink(), 'Symlink cannot be packaged: ' + relative)
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        raise BuildError('Runtime path leaves package root: ' + relative) from None
    data = path.read_bytes()
    if path.suffix in TEXT_SUFFIXES:
        content = data.decode('utf-8')
        require(not any(p.search(content) for p in PRIVATE_CONTENT),
                'Private path or credential-like content in ' + relative)
    return data


def assert_no_services(value):
    if isinstance(value, dict):
        require(not any(key in value for key in ('mcpServers', 'hooks', 'lspServers', 'settings', 'userConfig')),
                'Distribution manifests must not add servers, hooks, or credentials')
        for item in value.values():
            assert_no_services(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_services(item)


def local_link_errors(files):
    errors = []
    for name, content in files.items():
        if not name.endswith('.md'):
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content.decode('utf-8')):
            target = target.strip().strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path)))
            if resolved.startswith('../') or resolved not in files:
                errors.append(name + ' -> ' + target)
    return errors


def collect(root):
    skill = root / 'skills/goose'
    version = read_allowed(skill, 'VERSION').decode().strip()
    require(re.fullmatch(r'\d+\.\d+\.\d+', version), 'Invalid skill version')
    require({p.parent.name for p in (root / 'skills').glob('*/SKILL.md')} == {'goose'},
            'Only Goose may be externally discovered')
    require(len(list(skill.rglob('SKILL.md'))) == 1, 'Nested installable skills are forbidden')
    files = {name: read_allowed(skill, name) for name in RUNTIME}
    require(not local_link_errors(files), 'Missing bundled reference: ' + '; '.join(local_link_errors(files)))
    require(sum(map(len, files.values())) < 100 * 1024 * 1024, 'Skill exceeds 100 MB')
    provenance = {'schema_version': 2, 'name': 'goose', 'version': version,
                  'installed_skills': ['goose'], 'internal_modules': list(MODULES),
                  'validation_scope': 'Archive structure, references and scripts only; host execution is separately tested.',
                  'files': [{'path': name, 'sha256': hashlib.sha256(data).hexdigest()} for name, data in sorted(files.items())]}
    files['DISTRIBUTION.json'] = (json.dumps(provenance, ensure_ascii=False, indent=2) + '\n').encode()
    return version, files


def build(root, out):
    version, files = collect(root)
    out.mkdir(parents=True, exist_ok=True)
    path = out / ('goose-' + version + '.zip')
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(safe_name('goose/' + name), date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    result = {'status': 'structural_build_valid', 'version': version, 'installed_skills': 1,
              'internal_modules': len(MODULES), 'host_execution_tested': False,
              'archive': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'files': len(files)}
    (out / 'build-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    try:
        print(json.dumps(build(ROOT, args.output_dir), ensure_ascii=False, indent=2))
        return 0
    except (BuildError, OSError, ValueError, KeyError) as error:
        print('Skill build failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
