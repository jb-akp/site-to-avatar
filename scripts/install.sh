#!/usr/bin/env bash
# Copy the akapulu-avatar skill into your own project, so Codex finds it.
#   ./scripts/install.sh ~/path/to/your-site
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
target="${1:-}"

if [ -z "$target" ]; then
  echo "Where is your website? Give me the folder:"
  echo "  ./scripts/install.sh ~/Desktop/my-site"
  exit 1
fi
target="$(cd "$target" 2>/dev/null && pwd)" || { echo "No such folder: ${1}"; exit 1; }
[ "$target" = "$here" ] && { echo "That is this repo. Point at your website's folder instead."; exit 1; }

mkdir -p "$target/.agents"
cp -R "$here/.agents/skills" "$target/.agents/"
cp "$here/AGENTS.md" "$target/AGENTS.md"

if [ ! -f "$target/.env" ]; then
  if [ -f "$here/.env" ] && grep -q '^AKAPULU_API_KEY=.\+' "$here/.env"; then
    grep '^AKAPULU_API_KEY=' "$here/.env" > "$target/.env"
  else
    printf '# Get a free key at https://akapulu.com -> Settings -> API keys\nAKAPULU_API_KEY=\n' > "$target/.env"
  fi
fi
grep -qs '^\.env$' "$target/.gitignore" || printf '\n.env\nakapulu/\n' >> "$target/.gitignore"

echo "Installed into $target"
echo "  .agents/skills/akapulu-avatar/           the skill"
echo "  .agents/skills/akapulu-avatar/scripts/   the validator and the API client"
echo "  AGENTS.md                                so Codex reads the skill on open"
echo
if grep -q '^AKAPULU_API_KEY=.\+' "$target/.env" 2>/dev/null; then
  echo "Your key came across too."
else
  echo "Next: open .env in that folder and paste your Akapulu key after AKAPULU_API_KEY="
  echo "  (free key at https://akapulu.com -> Settings -> API keys)"
fi
echo
echo "Then open $target in Codex and say:"
echo "  build me an avatar assistant from this site"
