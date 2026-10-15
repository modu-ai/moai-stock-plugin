#!/usr/bin/env python3
"""Build offline, allowlisted platform adapters from the canonical skills."""
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
SKILLS = ('goose', 'goosekr', 'stock-analyst', 'stock-report', 'peer-compare', 'earnings-review',
          'event-impact', 'watchlist-review', 'claim-check', 'portfolio-review')
RUNTIME = ('agents/goose.md',) + tuple('skills/' + skill + '/SKILL.md' for skill in SKILLS) + (
    'skills/stock-report/references/agent-team.md',
    'skills/stock-report/references/report-input.md',
    'skills/stock-report/references/report-standard.md',
    'skills/stock-report/references/research-contract.md',
    'skills/stock-report/references/workflow-map.json',
    'skills/stock-report/scripts/render_report.py',
    'skills/stock-report/assets/report.css',
    'skills/stock-report/assets/modu-stock-wordmark.png',
    'skills/portfolio-review/references/portfolio-input.md',
    'skills/portfolio-review/scripts/portfolio_calc.py',
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


def browser_entry():
    lines = [
        '---', 'name: moai-stock-browser',
        'description: 한국어 주식·기업 분석과 보유자산 점검을 원문 근거로 수행하고 전자잉크 스타일 보고서를 작성합니다. 종목 분석, 기업 비교, 실적, 사건, 관심종목 재점검, 팩트체크, 포트폴리오 상담에 사용합니다.',
        '---', '', '# 모두의 주식 — 브라우저용 통합 스킬', '',
        '이 스킬은 일곱 전문 업무와 Goose 진입·총괄·호환 지침을 하나의 자기완결 묶음으로 제공합니다. 사용자의 자연어 요청을 먼저 분류하고 필요한 지침만 읽습니다. 아래 GUIDE.md는 이 통합 스킬의 참조 자료이며 별도의 설치된 스킬이나 실행 도구가 아닙니다.', '',
        '1. [총괄 진입점](workflows/goosekr/GUIDE.md)과 [실행 지도](workflows/stock-report/references/workflow-map.json)를 읽습니다.',
        '2. 선택한 업무 지침과 상대경로로 연결된 조사·역할·보고서 계약을 적용합니다. 각 상대경로의 기준은 해당 GUIDE.md가 있는 업무 폴더입니다.',
        '3. 네이티브 하위 에이전트 도구가 없으면 조사→분석→반대 근거 점검→편집을 순차 수행하고 실제 실행 방식으로 기록합니다. 여러 에이전트가 실행됐다고 꾸미지 않습니다.',
        '4. 검색·원문 열람·파일 작성·Python 실행 기능은 현재 환경에서 제공되는 것만 사용합니다. 제공되지 않는 도구를 지침이 생성해 주지는 않습니다.',
        '5. 계산기와 HTML 렌더러는 외부 통신 없는 Python 3 표준 라이브러리 코드입니다. Gemini 웹에서는 외부 요청을 수행하는 스크립트를 만들거나 실행하지 않습니다. 원문 조사는 환경의 허용된 검색·열람 기능으로 수행하고 없으면 확인 불가 범위를 표시합니다.',
        '6. Gemini 웹의 이 스킬과 Canvas·Deep Research 기능을 동시에 사용할 수 있다고 주장하지 않습니다. 여기서 심층 조사는 원문을 읽고 비교하는 방법을 뜻합니다.',
        '7. 사용자 계좌 입력과 결과는 사용자가 지정한 작업 공간에만 저장하고 외부 검색으로 보내지 않습니다. 거래·정기 감시·배포를 자동 실행하지 않습니다.',
        '8. Python 실행이 없으면 승인 스타일의 HTML 또는 Markdown 결과를 가능한 범위에서 작성합니다. 실제 실행하지 않은 계산이나 렌더 검사를 통과했다고 표시하지 않습니다.', '',
        '## 업무 지침', '',
    ]
    lines.extend('- [' + name + '](workflows/' + name + '/GUIDE.md)' for name in SKILLS)
    lines += ['', '## 공통 도구', '',
              '- [보고서 입력 계약](workflows/stock-report/references/report-input.md)',
              '- [HTML 렌더러](workflows/stock-report/scripts/render_report.py)',
              '- [보유자산 입력 계약](workflows/portfolio-review/references/portfolio-input.md)',
              '- [보유자산 계산기](workflows/portfolio-review/scripts/portfolio_calc.py)', '',
              '설치 형식과 참고 파일은 준비되어 있지만 계정별 설치·실행 여부는 별도 확인이 필요합니다.', '']
    return '\n'.join(lines).encode('utf-8')


def collect(root, platform):
    identity = json.loads(read_allowed(root, 'plugin.json'))
    require(identity['name'] == 'moai-stock-plugin', 'Unexpected plugin name')
    version = identity['version']
    require(re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?', version), 'Unsafe or invalid version')
    present = {p.parent.name for p in (root / 'skills').glob('*/SKILL.md')}
    require(present == set(SKILLS), 'Canonical skill inventory differs from canonical distribution contract')
    files = {name: read_allowed(root, name) for name in RUNTIME}
    mapping = {name: name for name in RUNTIME}
    if platform == 'openai':
        for name in ('plugin.json', 'assets/modu-stock-wordmark.png', 'assets/modu-stock-icon.png'):
            files[name] = read_allowed(root, name)
        for skill in SKILLS:
            name = 'skills/' + skill + '/agents/openai.yaml'
            files[name] = read_allowed(root, name)
        interface = identity['extensions']['com.openai']['interface']
        require(len(interface['shortDescription']) <= 30, 'OpenAI subtitle exceeds 30 characters')
        prompts = interface['defaultPrompt']
        require(isinstance(prompts, str) or isinstance(prompts, list) and len(prompts) <= 3, 'OpenAI defaultPrompt limit')
        prefix = 'moai-stock-plugin'
    elif platform == 'claude':
        for name in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', 'assets/modu-stock-icon.png'):
            files[name] = read_allowed(root, name)
            if name.endswith('.json'):
                assert_no_services(json.loads(files[name]))
        manifest = json.loads(files['.claude-plugin/plugin.json'])
        marketplace = json.loads(files['.claude-plugin/marketplace.json'])
        require(manifest['name'] == identity['name'] and manifest['version'] == version, 'Claude identity/version mismatch')
        require(marketplace['plugins'][0]['source'] == './' and marketplace['plugins'][0]['name'] == identity['name'], 'Marketplace source/name must resolve to this plugin root')
        prefix = 'moai-stock-plugin'
    elif platform == 'gemini-cli':
        for name in ('gemini-extension.json', 'GEMINI.md'):
            files[name] = read_allowed(root, name)
        manifest = json.loads(files['gemini-extension.json'])
        assert_no_services(manifest)
        require(manifest['name'] == identity['name'] and manifest['version'] == version, 'Gemini identity/version mismatch')
        require(manifest.get('contextFileName') == 'GEMINI.md', 'Gemini context must be bundled GEMINI.md')
        prefix = 'moai-stock-plugin'
    elif platform == 'browser-skill':
        renamed, mapping = {}, {}
        for name, data in files.items():
            target = name if name.startswith('agents/') else 'workflows/' + name.removeprefix('skills/')
            if target.endswith('/SKILL.md'):
                target = target[:-len('SKILL.md')] + 'GUIDE.md'
            # Repository-only test commands are not a browser execution dependency.
            if target.endswith('.md'):
                data = data.decode('utf-8').replace('python3 tests/renderer-test.py\n', '').replace('python3 -m unittest discover -s tests -v\n', '').encode('utf-8')
                for skill in SKILLS:
                    data = data.replace(('../' + skill + '/SKILL.md').encode(), ('../' + skill + '/GUIDE.md').encode())
            renamed[target] = data
            mapping[target] = name
        files = renamed
        files['SKILL.md'] = browser_entry()
        prefix = 'moai-stock-browser'
    else:
        raise BuildError('Unknown platform')
    errors = local_link_errors(files)
    require(not errors, 'Missing bundled reference: ' + '; '.join(errors))
    require(sum(map(len, files.values())) < 100 * 1024 * 1024, 'Skill exceeds 100 MB upload limit')
    provenance = {'schema_version': 1, 'platform_adapter': platform, 'version': version,
                  'validation_scope': 'Archive structure and references only; host installation/execution is not asserted.',
                  'canonical_skills': list(SKILLS), 'files': [
                      {'path': name, 'source_path': mapping.get(name, name if name != 'SKILL.md' else 'generated browser entry'),
                       'sha256': hashlib.sha256(data).hexdigest()} for name, data in sorted(files.items())]}
    files['DISTRIBUTION.json'] = (json.dumps(provenance, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    return version, prefix, files


def build(root, out):
    builds = []
    # Validate every platform before writing archives.
    prepared = [(platform, *collect(root, platform)) for platform in ('openai', 'claude', 'gemini-cli', 'browser-skill')]
    out.mkdir(parents=True, exist_ok=True)
    for platform, version, prefix, files in prepared:
        path = out / ('moai-stock-' + platform + '-' + version + '.zip')
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(files.items()):
                entry = zipfile.ZipInfo(safe_name(prefix + '/' + name), date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, data)
        builds.append({'platform': platform, 'archive': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'files': len(files), 'uncompressed_bytes': sum(map(len, files.values()))})
    report = {'status': 'structural_build_valid', 'host_installation_tested': False, 'host_execution_tested': False, 'archives': builds}
    (out / 'build-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args(argv)
    try:
        result = build(ROOT, args.output_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (BuildError, OSError, ValueError, KeyError) as error:
        print('Distribution build failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
