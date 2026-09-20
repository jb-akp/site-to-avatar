# Agent instructions

This repo turns a website into a talking AI avatar that knows that website.

Read `.claude/skills/akapulu-avatar/SKILL.md` and follow it. The short version:

1. Read the site. Everything the avatar knows comes from the site's own content.
2. Write `akapulu/knowledge.txt` (UTF-8 text, 130 KB max) and `akapulu/scenario.json`.
3. Run `python3 scripts/validate_scenario.py akapulu/scenario.json` before any API call.
4. With a key in `.env`: create the knowledge base, upload the text, wait for `completed`,
   put the real id in the `rag` tool, then create the scenario and mint the hosted link.
5. Ask the user for the avatar UUID from https://akapulu.com/catalog. There is no API for it.

Never put the API key in browser code. Never invent an id. Never invent a fact the site does not
state. Every API path ends in a slash.
