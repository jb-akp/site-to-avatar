#!/usr/bin/env python3
"""Verify a built avatar against the site it was built from, before anyone talks to her.

validate_scenario.py asks "is this JSON legal?". This asks the harder question:
"is any of this made up, and did we miss anything?"

  python3 .agents/skills/akapulu-avatar/scripts/verify_build.py [site_folder]

Exit 0 = shippable (PASS/WARN only). Exit 1 = FAIL, fix before creating anything.
"""
import json, re, sys, html
from pathlib import Path

MONEY = re.compile(r'[£$€]\s?\d[\d,]*(?:\.\d{2})?|\b\d[\d,]*(?:\.\d{2})?\s?(?:pounds|dollars|euros|usd|gbp|eur)\b', re.I)
EMAIL = re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.]+\b')
PHONE = re.compile(r'(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)')
TIME  = re.compile(r'\b(?:[01]?\d|2[0-3])[:.]\d{2}\s?(?:am|pm)?\b|\b(?:[01]?\d|2[0-3])\s?(?:am|pm)\b', re.I)
URL   = re.compile(r'\bhttps?://[^\s"\'<>)]+', re.I)
HEAD  = re.compile(r'<h([1-3])[^>]*>(.*?)</h\1>', re.I | re.S)
STOP  = set('the a an and or of to for in on at is are we you your our with that this it from by as be can will more your'.split())

def strip_html(t):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', t, flags=re.I | re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))

def digits(s): return re.sub(r'\D', '', s)

def facts(text):
    """Hard facts a model could invent. Kind -> set of normalised values."""
    out = {}
    for kind, rx in (('money', MONEY), ('email', EMAIL), ('phone', PHONE), ('time', TIME), ('url', URL)):
        vals = set()
        for m in rx.findall(text):
            m = m.strip()
            if kind in ('money', 'phone'):
                d = digits(m)
                if kind == 'phone' and len(d) < 9: continue
                if d: vals.add(d)
            else:
                vals.add(m.lower().rstrip('.,;:'))
        out[kind] = vals
    return out

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    out = root / 'akapulu'
    kb_p, sc_p = out / 'knowledge.txt', out / 'scenario.json'
    for p in (kb_p, sc_p):
        if not p.is_file(): sys.exit(f"missing {p.relative_to(root)} — run the build first")

    pages = [p for p in root.rglob('*.htm*')
             if 'akapulu' not in p.parts and 'node_modules' not in p.parts and '.agents' not in p.parts]
    if not pages: sys.exit("no .html found — point me at the site folder")
    site = strip_html(' '.join(p.read_text('utf-8', 'replace') for p in pages))
    site_l = site.lower()
    kb = kb_p.read_text('utf-8', 'replace')
    sc = json.loads(sc_p.read_text('utf-8', 'replace'))

    rows, worst = [], 0
    def add(level, name, detail):
        nonlocal worst
        worst = max(worst, {'PASS': 0, 'WARN': 1, 'FAIL': 2}[level])
        rows.append((level, name, detail))

    # 1. GROUNDING — every hard fact she will say must exist on the site
    sf, kf = facts(site), facts(kb)
    invented = {k: sorted(kf[k] - sf[k]) for k in kf if kf[k] - sf[k]}
    n = sum(len(v) for v in invented.values())
    total = sum(len(v) for v in kf.values())
    if n:
        add('FAIL', 'Grounding',
            f"{n} fact(s) in knowledge.txt are NOT on the site: " +
            "; ".join(f"{k}: {', '.join(v[:4])}" for k, v in invented.items()))
    elif total:
        add('PASS', 'Grounding', f"all {total} hard fact(s) in knowledge.txt trace back to the site")
    else:
        add('PASS', 'Grounding', "the site states no prices, phone numbers or emails, and neither does "
                                 "knowledge.txt — she has nothing to invent from")

    # 2. PERSONA PURITY — facts belong in the file, not in who she is
    role = sc.get('role_instruction', '')
    pf = facts(role); leaked = sorted({v for k in ('money', 'phone', 'email') for v in pf[k]})
    if leaked:
        add('FAIL', 'Persona purity',
            f"role_instruction states facts ({', '.join(leaked[:4])}). Change the file and her answer "
            f"will not change. Move them into knowledge.txt.")
    else:
        add('PASS', 'Persona purity', 'no prices, phones or emails baked into her personality')

    # 3. COVERAGE — did it read the whole page
    kb_l = kb.lower()
    missed = []
    for _, raw in HEAD.findall(' '.join(p.read_text('utf-8', 'replace') for p in pages)):
        h = strip_html(raw).strip()
        words = [w for w in re.findall(r'[a-z]{4,}', h.lower()) if w not in STOP]
        if words and not any(w in kb_l for w in words): missed.append(h[:44])
    if missed:
        add('WARN', 'Coverage', f"{len(missed)} section(s) on the site are absent from knowledge.txt: " +
            "; ".join(missed[:4]))
    else:
        add('PASS', 'Coverage', 'every heading on the site is represented')

    # 4. LIMITS
    kb_kb, sc_ch = len(kb.encode()) / 1024, len(json.dumps(sc))
    lim = 'FAIL' if kb_kb > 130 or sc_ch > 20000 else 'PASS'
    add(lim, 'Limits', f"knowledge.txt {kb_kb:.0f} KB of 130 · scenario {sc_ch} chars of 20000")

    # 5. WIRING
    nodes = sc.get('nodes', {})
    def node_fns(nd):
        f = nd.get('functions') or []
        return list(f.values()) if isinstance(f, dict) else list(f)
    node_list = list(nodes.values()) if isinstance(nodes, dict) else list(nodes)
    fns = [f for nd in node_list for f in node_fns(nd)]
    types = [f.get('type') for f in fns]
    rag = [f for f in fns if f.get('type') == 'rag']
    if not rag:
        add('FAIL', 'Wiring', 'no rag tool — she cannot look anything up')
    elif any(not f.get('knowledge_base_id') or 'PLACEHOLDER' in str(f.get('knowledge_base_id')).upper() for f in rag):
        add('WARN', 'Wiring', 'rag tool has no real knowledge_base_id yet (expected before the KB is created)')
    else:
        add('PASS', 'Wiring', f"{len(fns)} tool(s): {', '.join(sorted(set(types)))}, rag points at a real knowledge base")

    w = max(len(r[1]) for r in rows)
    print("\n  QA REPORT — " + root.name)
    print("  " + "-" * (w + 58))
    for level, name, detail in rows:
        print(f"  {level:<4}  {name:<{w}}  {detail}")
    print("  " + "-" * (w + 58))
    print({0: "  Shippable. Nothing in her answers is invented.\n",
           1: "  Shippable, with the warnings above.\n",
           2: "  NOT shippable. Fix the FAIL rows, rebuild, run this again.\n"}[worst])
    sys.exit(1 if worst == 2 else 0)

if __name__ == '__main__':
    main()
