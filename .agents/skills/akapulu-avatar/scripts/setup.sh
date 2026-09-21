#!/usr/bin/env bash
# Put your Akapulu key in .env and check that it works.
set -euo pipefail
# the site root is whichever parent holds .agents/ — not a fixed number of "..",
# which silently wrote .env inside the skill folder where nothing could find it.
d="$(cd "$(dirname "$0")" && pwd)"
while [ "$d" != "/" ] && [ ! -d "$d/.agents" ]; do d="$(dirname "$d")"; done
[ -d "$d/.agents" ] || { echo "Could not find your site folder (no .agents/ above me)."; exit 1; }
cd "$d"

if [ -f .env ] && grep -q '^AKAPULU_API_KEY=.\+' .env && ! grep -q '^AKAPULU_API_KEY=YOUR_' .env; then
  echo "Found a key in .env."
else
  echo "You need an Akapulu API key."
  echo "  1. Sign up free at https://akapulu.com"
  echo "  2. Open Settings and create an API key"
  echo
  read -r -p "Paste it here (it is written to .env, which git ignores): " key
  [ -n "$key" ] || { echo "Nothing pasted. Run this again when you have the key."; exit 1; }
  touch .env
  grep -v '^AKAPULU_API_KEY=' .env > .env.tmp 2>/dev/null || true
  mv .env.tmp .env 2>/dev/null || true
  echo "AKAPULU_API_KEY=$key" >> .env
  echo "Written to .env."
fi

echo
python3 .agents/skills/akapulu-avatar/scripts/akapulu_api.py check
echo
echo "Ready. Open this folder in Codex and say:"
echo "  build me an avatar assistant from this site"
