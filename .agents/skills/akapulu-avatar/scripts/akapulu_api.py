#!/usr/bin/env python3
"""
Akapulu REST client for the akapulu-avatar skill.

The key is read from the nearest .env and never printed, logged, or put in a URL.
Every path ends in a slash: without one Akapulu answers 301, and a redirected POST
becomes a GET, so the request "succeeds" and does nothing.

  python3 akapulu_api.py check
  python3 akapulu_api.py kb-create   "Harbour Lane Dental" --description "site content"
  python3 akapulu_api.py doc-upload  <kb_id> knowledge.txt --name "site content"
  python3 akapulu_api.py doc-wait    <kb_id>
  python3 akapulu_api.py scenario-create scenario.json --name Clara \
        --avatar <uuid> --label "Front desk" --keyword Clara
  python3 akapulu_api.py scenario-get <id>
  python3 akapulu_api.py delete scenario <id> | delete kb <id>
"""
import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = "https://akapulu.com/api"
CATALOG = "https://akapulu.com/catalog"


def load_key():
    """Nearest .env walking up from cwd, then the environment."""
    here = Path.cwd().resolve()
    for folder in [here, *here.parents]:
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line.startswith("AKAPULU_API_KEY="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value and not value.startswith("YOUR_"):
                        return value
    value = os.environ.get("AKAPULU_API_KEY", "").strip()
    return value or None


def die(message, code=1):
    print(message, file=sys.stderr)
    sys.exit(code)


def key_or_die():
    key = load_key()
    if not key:
        die("No AKAPULU_API_KEY found in the nearest .env or the environment.\n"
            "Run .agents/skills/akapulu-avatar/scripts/setup.sh, or add this line to .env:\n"
            "  AKAPULU_API_KEY=your-key-here\n"
            "Get one at https://akapulu.com (the free plan is enough to finish the tutorial).")
    return key


def request(method, path, key, body=None, multipart=None, timeout=120):
    if not path.endswith("/"):
        path += "/"                       # a redirected POST silently becomes a GET
    url = BASE + path
    headers = {"Authorization": f"Bearer {key}"}
    data = None

    if multipart is not None:
        boundary = uuid.uuid4().hex
        chunks = []
        for name, value in multipart.get("fields", {}).items():
            chunks.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
                .encode("utf-8"))
        for name, filepath in multipart.get("files", {}).items():
            filepath = Path(filepath)
            ctype = mimetypes.guess_type(filepath.name)[0] or "text/plain"
            chunks.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                f'filename="{filepath.name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode("utf-8"))
            chunks.append(filepath.read_bytes())
            chunks.append(b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
        data = b"".join(chunks)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": raw[:400]}
        # Branch on error_code, never on the English sentence.
        code = payload.get("error_code", "")
        message = payload.get("error") or payload.get("detail") or raw[:400]
        if err.code == 401 or code == "AUTH_INVALID":
            die("Akapulu rejected the API key (401). Check AKAPULU_API_KEY in .env.")
        die(f"{method} {path} failed with HTTP {err.code}"
            f"{' [' + code + ']' if code else ''}: {message}")
    except urllib.error.URLError as err:
        die(f"Could not reach {url}: {err.reason}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def cmd_check(args):
    key = key_or_die()
    result = request("GET", "/scenarios/", key)
    count = len(result.get("scenarios", []))
    print(f"Key works. The account has {count} scenario(s).")


def cmd_kb_create(args):
    key = key_or_die()
    result = request("POST", "/knowledge-bases/create/", key,
                     {"name": args.name, "description": args.description or ""})
    kb_id = result.get("id") or result.get("knowledge_base", {}).get("id")
    if not kb_id:
        die(f"No knowledge base id in the response: {json.dumps(result)[:300]}")
    print(kb_id)


def cmd_doc_upload(args):
    key = key_or_die()
    path = Path(args.file)
    if not path.is_file():
        die(f"No such file: {path}")
    size = path.stat().st_size
    if size > 130 * 1024:
        die(f"{path.name} is {size / 1024:.0f} KB. The cap is 130 KB of UTF-8 text. "
            "Trim the file, or split it across two documents in the same knowledge base.")
    result = request("POST", f"/knowledge-bases/{args.kb_id}/documents/create/", key,
                     multipart={"fields": {"name": args.name,
                                           "description": args.description or ""},
                                "files": {"file": str(path)}})
    doc_id = result.get("id") or result.get("document", {}).get("id", "")
    print(f"{doc_id}  ({size / 1024:.1f} KB, status pending)")


def cmd_doc_wait(args):
    key = key_or_die()
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        result = request("GET", f"/knowledge-bases/{args.kb_id}/documents/", key)
        docs = result.get("documents", result if isinstance(result, list) else [])
        states = [d.get("status") for d in docs]
        if states and all(s == "completed" for s in states):
            print(f"{len(states)} document(s) completed.")
            return
        if "failed" in states:
            die(f"A document failed to embed: {json.dumps(docs)[:300]}")
        time.sleep(args.interval)
    die(f"Documents were still pending after {args.timeout}s. "
        "Embedding usually takes 15 to 20 seconds; check the knowledge base in the dashboard.")


def cmd_scenario_create(args):
    key = key_or_die()
    nodes_json = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if "nodes_json" in nodes_json:
        nodes_json = nodes_json["nodes_json"]

    body = {"name": args.name, "nodes_json": nodes_json}
    if args.model:
        body["llm_model"] = args.model
    if args.avatar:
        if len(args.keyword) > 5:
            die(f"{len(args.keyword)} stt_keywords given; the cap is 5 per hosted link.")
        body["hosted_links"] = [{"avatar_id": args.avatar,
                                 "label": args.label or args.name,
                                 "stt_keywords": args.keyword}]
    result = request("POST", "/scenarios/create/", key, body)
    scenario_id = result.get("id") or result.get("scenario", {}).get("id", "")
    links = result.get("hosted_links") or result.get("scenario", {}).get("hosted_links") or []
    print(json.dumps({"scenario_id": scenario_id,
                      "url": (links[0].get("url") if links else None)}, indent=2))


def cmd_scenario_get(args):
    key = key_or_die()
    print(json.dumps(request("GET", f"/scenarios/{args.id}/", key), indent=2))


def cmd_delete(args):
    key = key_or_die()
    path = "/scenarios/delete/" if args.kind == "scenario" else "/knowledge-bases/delete/"
    print(json.dumps(request("POST", path, key, {"ids": [args.id]}), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="verify the key").set_defaults(func=cmd_check)

    p = sub.add_parser("kb-create", help="create a knowledge base")
    p.add_argument("name")
    p.add_argument("--description", default="")
    p.set_defaults(func=cmd_kb_create)

    p = sub.add_parser("doc-upload", help="upload a UTF-8 text file (130 KB max)")
    p.add_argument("kb_id")
    p.add_argument("file")
    p.add_argument("--name", default="knowledge")
    p.add_argument("--description", default="")
    p.set_defaults(func=cmd_doc_upload)

    p = sub.add_parser("doc-wait", help="poll until every document is completed")
    p.add_argument("kb_id")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--interval", type=int, default=5)
    p.set_defaults(func=cmd_doc_wait)

    p = sub.add_parser("scenario-create", help="create a scenario and mint a hosted link")
    p.add_argument("file", help="scenario JSON")
    p.add_argument("--name", required=True)
    p.add_argument("--avatar", help=f"avatar UUID from {CATALOG}")
    p.add_argument("--label", default="")
    p.add_argument("--keyword", action="append", default=[], help="stt keyword, max 5")
    p.add_argument("--model", default="", help="llm_model, defaults to gpt-4.1-mini")
    p.set_defaults(func=cmd_scenario_create)

    p = sub.add_parser("scenario-get", help="fetch a scenario")
    p.add_argument("id")
    p.set_defaults(func=cmd_scenario_get)

    p = sub.add_parser("delete", help="delete a scenario or a knowledge base")
    p.add_argument("kind", choices=["scenario", "kb"])
    p.add_argument("id")
    p.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
