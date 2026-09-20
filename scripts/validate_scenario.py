#!/usr/bin/env python3
"""
Validate Akapulu scenario JSON before it costs you an API call.

Every rule here comes from https://docs.akapulu.com/guides/scenarios/using-json
plus three constraints that are not in the docs and were each found by having a
request rejected. Run it on a file, or pipe JSON in:

    python3 validate_scenario.py scenario.json
    cat scenario.json | python3 validate_scenario.py

Exit code 0 means the JSON is accepted by POST /scenarios/create/.
Exit code 1 prints every problem, with the rule that caught it.
"""
import json
import re
import sys

TOP_KEYS = {"initial_node", "role_instruction", "nodes"}
NODE_KEYS = {"task_instruction", "functions", "respond_immediately",
             "end_after_bot_response", "require_function_call"}
FUNCTION_KEYS = {"name", "description", "type", "transition_to", "allowed_next_nodes",
                 "endpoint_id", "knowledge_base_id", "parameters", "require_reason",
                 "filler_speech"}
FUNCTION_TYPES = {"transition", "http", "rag", "vision"}
NAME_OK = re.compile(r"^[A-Za-z0-9_-]+$")
TEMPLATE = re.compile(r"\{\{([^}]*)\}\}")

MAX_NODES_JSON = 20000
MAX_INSTRUCTION = 4000


def check(scenario):
    """Return a list of problems. Empty list means valid."""
    bad = []

    def fail(rule, detail):
        bad.append((rule, detail))

    if not isinstance(scenario, dict):
        return [("core structure", "nodes_json must be a JSON object")]

    size = len(json.dumps(scenario, separators=(",", ":")))
    if size > MAX_NODES_JSON:
        fail("core structure", f"nodes_json is {size} characters, the cap is {MAX_NODES_JSON}")

    extra = set(scenario) - TOP_KEYS
    if extra:
        fail("core structure",
             f"top-level keys are limited to {sorted(TOP_KEYS)}; found {sorted(extra)}")

    role = scenario.get("role_instruction")
    if "role_instruction" in scenario:
        if not isinstance(role, str) or not role.strip():
            fail("instructions", "role_instruction must be a non-empty string")
        elif len(role) > MAX_INSTRUCTION:
            fail("instructions",
                 f"role_instruction is {len(role)} characters, the cap is {MAX_INSTRUCTION}")

    nodes = scenario.get("nodes")
    if isinstance(nodes, list):
        # GOTCHA 3, and the single most common mistake an LLM makes here.
        fail("nodes shape",
             "nodes is a list. It must be an OBJECT keyed by node name: "
             '{"desk": {"task_instruction": "..."}}, not [{"name": "desk", ...}]')
        return _report(bad)
    if not isinstance(nodes, dict) or not nodes:
        fail("core structure", "nodes must be a non-empty JSON object")
        return _report(bad)

    initial = scenario.get("initial_node")
    if not initial:
        fail("core structure", "initial_node is required")
    elif initial not in nodes:
        fail("core structure",
             f'initial_node "{initial}" does not match any node; nodes are {sorted(nodes)}')

    for node_name, node in nodes.items():
        where = f'node "{node_name}"'
        if not isinstance(node, dict):
            fail("node rules", f"{where} must be a JSON object")
            continue

        unknown = set(node) - NODE_KEYS
        if unknown:
            fail("node rules",
                 f"{where} has keys {sorted(unknown)}; allowed are {sorted(NODE_KEYS)}. "
                 "(A node's name is its key, so do not also put a name field inside it.)")

        task = node.get("task_instruction")
        if not isinstance(task, str) or not task.strip():
            fail("node rules", f"{where} needs a non-empty task_instruction")
        elif len(task) > MAX_INSTRUCTION:
            fail("node rules",
                 f"{where} task_instruction is {len(task)} characters, the cap is {MAX_INSTRUCTION}")

        for flag in ("respond_immediately", "end_after_bot_response", "require_function_call"):
            if flag in node and not isinstance(node[flag], bool):
                fail("node rules", f"{where} {flag} must be true or false")

        functions = node.get("functions")
        if functions is not None and not isinstance(functions, list):
            fail("node rules", f"{where} functions must be a list")
            functions = None

        if node.get("require_function_call") is True and not functions:
            fail("node rules",
                 f"{where} sets require_function_call but has no functions to call")

        seen = set()
        for i, fn in enumerate(functions or []):
            _check_function(fn, i, node_name, nodes, seen, fail)

    for path, value in _walk(scenario):
        if isinstance(value, str):
            _check_templates(value, path, fail)

    return _report(bad)


def _check_function(fn, i, node_name, nodes, seen, fail):
    where = f'node "{node_name}" function #{i + 1}'
    if not isinstance(fn, dict):
        fail("function rules", f"{where} must be a JSON object")
        return

    name = fn.get("name")
    if name:
        where = f'node "{node_name}" function "{name}"'
    unknown = set(fn) - FUNCTION_KEYS
    if unknown:
        fail("function rules",
             f"{where} has keys {sorted(unknown)}; allowed are {sorted(FUNCTION_KEYS)}")

    if not isinstance(name, str) or not name:
        fail("function rules", f"{where} needs a name")
    else:
        if name != name.strip():
            fail("function rules", f'{where} name has leading or trailing whitespace')
        if not NAME_OK.match(name.strip()):
            fail("function rules",
                 f'{where} name may only use letters, numbers, underscore and hyphen')
        if name in seen:
            fail("function rules", f'{where} name is used twice in the same node')
        seen.add(name)

    if not fn.get("description"):
        fail("function rules",
             f"{where} needs a description. It is the only thing the model reads "
             "to decide when to call this tool, so write when to use it, not what it is")

    ftype = fn.get("type", "transition")
    if ftype not in FUNCTION_TYPES:
        fail("function rules",
             f'{where} type "{ftype}" is not one of {sorted(FUNCTION_TYPES)}')
        return

    target = fn.get("transition_to")
    if target is not None:
        if not isinstance(target, str) or target != target.strip():
            fail("transition rules", f"{where} transition_to must be a string with no stray spaces")
        elif target not in nodes:
            fail("transition rules",
                 f'{where} transitions to "{target}", which is not a node; nodes are {sorted(nodes)}')

    if ftype == "transition" and not target:
        fail("transition rules", f"{where} is a transition and must define transition_to")
    if "require_reason" in fn:
        if ftype != "transition":
            fail("transition rules", f"{where} require_reason is only valid on transition functions")
        elif not isinstance(fn["require_reason"], bool):
            fail("transition rules", f"{where} require_reason must be true or false")

    if ftype == "rag" and not fn.get("knowledge_base_id"):
        fail("rag rules",
             f"{where} is a rag tool and must carry knowledge_base_id. "
             "Create the knowledge base first, then put its real id here")

    if ftype == "http" and not fn.get("endpoint_id"):
        fail("http rules", f"{where} is an http tool and must carry endpoint_id")

    allowed = fn.get("allowed_next_nodes")
    if allowed is not None:
        if ftype != "http":
            fail("http rules", f"{where} allowed_next_nodes is only valid on http functions")
        elif not isinstance(allowed, list) or not allowed:
            fail("http rules", f"{where} allowed_next_nodes must be a non-empty list")
        else:
            if target:
                fail("http rules",
                     f"{where} cannot set both transition_to and allowed_next_nodes")
            if len(set(allowed)) != len(allowed):
                fail("http rules", f"{where} allowed_next_nodes has duplicates")
            for entry in allowed:
                if not isinstance(entry, str) or not entry.strip():
                    fail("http rules", f"{where} allowed_next_nodes entries must be non-empty strings")
                elif entry not in nodes:
                    fail("http rules",
                         f'{where} allowed_next_nodes entry "{entry}" is not a node')

    if "filler_speech" in fn and not isinstance(fn["filler_speech"], bool):
        fail("function rules", f"{where} filler_speech must be true or false")


def _check_templates(text, path, fail):
    for token in TEMPLATE.findall(text):
        if token.startswith("llm.") and token.count(".") != 1:
            # GOTCHA 1: the whole token, description included, is checked for exactly
            # one period. A description written as a sentence fails.
            fail("template variables",
                 f"{path}: {{{{{token[:60]}...}}}} has {token.count('.')} periods. "
                 "An llm token may contain exactly one, and the description counts. "
                 "Write the description as one comma-spliced clause with no full stops")
        if path.endswith("role_instruction") or path.endswith("task_instruction"):
            if token.startswith(("secret.", "llm.")):
                fail("instructions",
                     f"{path} uses a {token.split('.')[0]} template variable, which is not allowed there")


def _walk(obj, path="nodes_json"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def _report(bad):
    return bad


def check_hosted_links(links):
    """stt_keywords is capped at 5 per link. A sixth returns 400."""
    bad = []
    for i, link in enumerate(links or []):
        where = f"hosted_links[{i}]"
        if not link.get("avatar_id"):
            bad.append(("hosted links",
                        f"{where} needs avatar_id. There is no API that lists avatars: "
                        "copy the UUID from the URL of an avatar page at akapulu.com/catalog"))
        kw = link.get("stt_keywords") or []
        if len(kw) > 5:
            bad.append(("hosted links",
                        f"{where} has {len(kw)} stt_keywords, the cap is 5"))
    return bad


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as handle:
            raw = handle.read()
        source = sys.argv[1]
    else:
        raw = sys.stdin.read()
        source = "stdin"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as err:
        print(f"invalid JSON in {source}: {err}")
        return 1

    # Accept either a bare nodes_json or a full create-scenario request body.
    links = None
    if isinstance(data, dict) and "nodes_json" in data:
        links = data.get("hosted_links")
        data = data["nodes_json"]

    problems = check(data) + (check_hosted_links(links) if links else [])

    if not problems:
        nodes = data.get("nodes", {}) if isinstance(data, dict) else {}
        tools = sum(len(n.get("functions") or []) for n in nodes.values() if isinstance(n, dict))
        size = len(json.dumps(data, separators=(",", ":")))
        print(f"{source}: valid. {len(nodes)} node(s), {tools} tool(s), "
              f"{size} of {MAX_NODES_JSON} characters.")
        return 0

    print(f"{source}: {len(problems)} problem(s).\n")
    for rule, detail in problems:
        print(f"  [{rule}] {detail}")
    print("\nSchema: https://docs.akapulu.com/guides/scenarios/using-json")
    return 1


if __name__ == "__main__":
    sys.exit(main())
