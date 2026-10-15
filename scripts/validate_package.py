#!/usr/bin/env python3
"""Local package integrity checks; not a host install or official schema certification."""
import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

SKILLS = {"stock-analyst", "stock-report", "peer-compare", "earnings-review",
          "event-impact", "watchlist-review", "claim-check", "portfolio-review"}
WORKFLOWS = {"company_report", "peer_comparison", "earnings", "event",
             "watchlist_update", "claim_verification", "portfolio_consultation"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite JSON: {value}")))


def small_yaml(text):
    """Parse this package's mapping/scalar YAML subset, rejecting unsupported forms."""
    root, stack = {}, [(-1, {})]
    stack[0] = (-1, root)
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        require("\t" not in line, "YAML tabs unsupported")
        match = re.fullmatch(r"( *)([a-zA-Z_][\w-]*):(?: *(.*))?", line)
        require(match is not None, "unsupported YAML: expected plain mapping/scalar line")
        spaces, key, raw = match.groups()
        indent, raw = len(spaces), (raw or "").strip()
        while stack[-1][0] >= indent:
            stack.pop()
        require(indent == stack[-1][0] + (1 if stack[-1][0] == -1 else 2), "YAML indentation must use two spaces")
        parent = stack[-1][1]
        require(key not in parent, f"duplicate YAML key: {key}")
        if not raw:
            parent[key] = {}
            stack.append((indent, parent[key]))
        elif raw.startswith('"'):
            parent[key] = json.loads(raw)
        elif raw.startswith("'"):
            require(raw.endswith("'"), "unterminated YAML string")
            parent[key] = raw[1:-1].replace("''", "'")
        else:
            require(raw[0] not in "[{}]|>&*!", "unsupported YAML value")
            parent[key] = True if raw == "true" else False if raw == "false" else raw
    return root


def contained(root, path):
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes package: {path}") from None
    require(resolved.exists(), f"missing package path: {path}")
    return resolved


def validate(root):
    root = root.resolve()
    require(root.is_dir(), "package root is missing")
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        contained(root, path)
        lower = path.name.lower()
        require(lower not in (".mcp.json", "mcp.json", "mcp.yaml", "mcp.yml"), "MCP config is outside current version scope")
        require(not any(part.lower() in ("mcp", "mcp-servers") for part in path.relative_to(root).parts), "MCP server folder is outside current version scope")

    def no_mcp_configuration(value):
        if isinstance(value, dict):
            for key, item in value.items():
                normalized = re.sub(r"[^a-z]", "", key.lower())
                require(normalized not in {"mcp", "mcpservers", "mcpserver", "mcpconfig"}, "MCP configuration is not shipped in this version")
                no_mcp_configuration(item)
        elif isinstance(value, list):
            for item in value:
                no_mcp_configuration(item)

    for path in files:
        if path.suffix == ".json":
            no_mcp_configuration(load_json(path))
    manifest = load_json(root / "plugin.json")
    require(manifest.get("name") == "moai-stock-plugin", "unexpected manifest name")
    require(manifest.get("repository") == "https://github.com/modu-ai/moai-stock-plugin", "unexpected repository identity")
    require(bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", manifest.get("version", ""))), "invalid manifest version")
    require(bool(manifest.get("description")), "manifest description required")
    interface = manifest.get("extensions", {}).get("com.openai", {}).get("interface", {})
    require(bool(interface.get("displayName")), "displayName required")
    logo = interface.get("logo")
    require(isinstance(logo, str) and not urlsplit(logo).scheme and not Path(logo).is_absolute(), "local package logo required")
    contained(root, root / logo)

    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    require({path.parent.name for path in skill_files} == SKILLS, "expected eight current skill directories")
    reference_count = 0
    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
        require(match is not None, f"missing skill frontmatter: {path.parent.name}")
        metadata = small_yaml(match.group(1))
        require(metadata.get("name") == path.parent.name, f"skill name mismatch: {path.parent.name}")
        require(isinstance(metadata.get("description"), str) and bool(metadata["description"].strip()), "skill description required")
        agent_path = contained(root, path.parent / "agents/openai.yaml")
        agent = small_yaml(agent_path.read_text(encoding="utf-8"))
        for field in ("display_name", "short_description", "default_prompt"):
            require(isinstance(agent.get("interface", {}).get(field), str) and bool(agent["interface"][field]), f"missing agent interface {field}")
        require(agent.get("policy", {}).get("allow_implicit_invocation") is True, "natural-language invocation policy required")
        for relative in re.findall(r"(?<![\w/])((?:scripts|references|assets)/[\w./-]+\.(?:py|md|json|png|css))", text):
            contained(root, path.parent / relative)
            reference_count += 1

    for path in files:
        if path.suffix != ".md":
            continue
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            target = target.strip().strip("<>")
            url = urlsplit(target)
            if url.scheme or target.startswith("#"):
                continue
            require(not target.startswith("//"), "protocol-relative references are unsupported")
            relative = unquote(url.path)
            require(not Path(relative).is_absolute(), "absolute local reference is not portable")
            contained(root, path.parent / relative)
            reference_count += 1

    workflow = load_json(root / "skills/stock-report/references/workflow-map.json")
    require(workflow.get("entry_skill") == "stock-analyst", "unexpected workflow entry")
    require(workflow.get("kind") == "declarative_agent_workflow" and workflow.get("host_api") is False,
            "workflow must disclose declarative, non-host-API status")
    flows = workflow.get("workflows", {})
    require(set(flows) == WORKFLOWS, "expected seven workflow types")
    node_count = 0
    for name, flow in flows.items():
        nodes = flow.get("nodes")
        require(isinstance(nodes, list) and bool(nodes), f"{name}: nodes required")
        require(all(isinstance(node, dict) and isinstance(node.get("id"), str) and node["id"] for node in nodes), f"{name}: invalid node")
        ids = [node["id"] for node in nodes]
        require(len(ids) == len(set(ids)), f"{name}: duplicate node ids")
        by_id = {node["id"]: node for node in nodes}
        for node in nodes:
            require(node.get("skill") in SKILLS - {"stock-analyst"}, f"{name}: unknown or recursive entry skill")
            require(node.get("mode") in ("leaf", "render"), f"{name}: invalid invocation mode")
            require(isinstance(node.get("phase"), str) and node["phase"], f"{name}: phase required")
            needs = node.get("needs")
            require(isinstance(needs, list) and all(isinstance(dep, str) for dep in needs), f"{name}: needs must be string array")
            require(len(needs) == len(set(needs)) and set(needs) <= set(ids), f"{name}: missing/duplicate dependency")
        visiting, visited = set(), set()

        def walk(node_id):
            require(node_id not in visiting, f"{name}: dependency cycle")
            if node_id in visited:
                return
            visiting.add(node_id)
            for dependency in by_id[node_id]["needs"]:
                walk(dependency)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in ids:
            walk(node_id)
        node_count += len(nodes)
    return {"status": "pass", "skills": len(skill_files), "workflows": len(flows), "workflow_nodes": node_count,
            "local_references_checked": reference_count, "files_checked": len(files),
            "scope": "Local manifest fields, restricted YAML metadata, local references, source containment, DAG dependencies and no-MCP configuration.",
            "not_verified": ["Official plugin schema certification", "Cloud or desktop native install", "Host skill discovery and routing",
                             "Live research accuracy", "Browser rendering", "GitHub publication or marketplace availability"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = validate(args.root)
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
