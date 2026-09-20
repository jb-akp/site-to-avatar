# site-to-avatar

Point an AI coding agent at a website. Get a talking avatar that knows that website, on a link
you can put in the corner of any page.

No SDK, no backend, no framework. The avatar's knowledge comes out of the site's own content, so
it answers about your prices and your hours, and says it will check with the team when the site
does not cover something.

Built by [James Bradford](https://www.youtube.com/@JamesAkapulu), co-founder of
[Akapulu Labs](https://akapulu.com). This is the repo from the video.

## What it actually does

You say one thing:

> build me an avatar assistant from this site

and the agent reads the site, then writes two files:

| File | What it is |
|---|---|
| `akapulu/knowledge.txt` | Everything the site says, as plain text. This is what she knows. |
| `akapulu/scenario.json` | Who she is, how she speaks, and her two tools. This is how she behaves. |

It checks that JSON against every rule in the Akapulu docs **before** spending anything, then
creates the knowledge base, uploads the text, waits for it to embed, and mints a live link.

The one thing you do by hand is pick her face, because that is the only part with no API.

## AI-assisted setup

Clone this repo, open the folder in **Codex** or **Claude Code**, and say:

> install this skill and set me up

The agent reads `AGENTS.md` (Codex) or `CLAUDE.md` (Claude Code) and takes it from there.

## Five-minute setup, by hand

```bash
git clone https://github.com/jb-akp/site-to-avatar.git
cd site-to-avatar
./scripts/setup.sh          # asks for your Akapulu key, writes .env, verifies it
```

Then open the folder in your agent, point it at a site, and say the sentence above.

**No key yet?** You still get most of it. The skill always writes both files first, and they work
on their own: paste `scenario.json` into JSON mode on a new scenario at akapulu.com, and upload
`knowledge.txt` at akapulu.com/knowledge-bases. Nothing in steps one to four costs anything or
needs an account.

## Try it without building anything

`example/` holds the two files the skill produced from a dental practice site. Read
`example/knowledge.txt` and you will see exactly what the avatar knows, and why she will not
quote you a price.

## What is actually free

Akapulu's free plan gives you **10 credits in total**, a **3 minute cap** on any one call, and a
**watermark** on the avatar. That is enough to build this, test it properly, and show someone.
It is not enough to run a business on. Pricing is at [akapulu.com](https://akapulu.com).

The agent side costs whatever your Codex or Claude subscription costs. If you use an OpenAI API
key instead of a ChatGPT login, reading a site and writing these two files is cents, not dollars.

## Useful commands

```bash
python3 scripts/validate_scenario.py akapulu/scenario.json   # check JSON before you spend
python3 scripts/akapulu_api.py check                          # is my key working
python3 scripts/akapulu_api.py kb-create "My Business"
python3 scripts/akapulu_api.py doc-upload <kb_id> akapulu/knowledge.txt
python3 scripts/akapulu_api.py doc-wait <kb_id>
python3 scripts/akapulu_api.py scenario-create akapulu/scenario.json \
    --name "Front desk" --avatar <uuid> --keyword Clara
```

`validate_scenario.py` is worth running on its own even if you hand-write your JSON. It enforces
every documented rule plus three that are not in the docs, each of which was found the hard way.

## Project structure

```
.agents/skills/akapulu-avatar/    the skill, for Codex
.claude/skills/akapulu-avatar/    the same skill, for Claude Code
  SKILL.md                        the workflow
  references/scenario-schema.md   the JSON shape and every validation rule
  references/api.md               endpoints, and what has no API at all
  references/gotchas.md           the three undocumented constraints
scripts/validate_scenario.py      the validator, runs offline, no key needed
scripts/akapulu_api.py            the REST client
scripts/setup.sh                  key setup
prompts/                          build the site · add the images · add the button
example/                          a real generated knowledge file and scenario
```

## Two things worth knowing before you build

**The persona says how she speaks. The file says what she knows.** Put a fact in her persona and
she answers from memory without opening the file, and then editing the file changes nothing. Keep
every fact in `knowledge.txt` and she has to look it up.

**Her answers are only as good as your site.** She reads what is published. If your prices are
not on your site, she will not have them, and she will say so rather than guess. That is the
right behaviour, and it is worth seeing once before you show anyone.

## Licence

MIT.
