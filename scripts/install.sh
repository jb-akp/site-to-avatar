#!/usr/bin/env bash
# Copy the akapulu-avatar skill into your own project, so your coding agent finds it.
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

mkdir -p "$target/.agents" "$target/.claude"
cp -R "$here/.agents/skills" "$target/.agents/"
cp -R "$here/.claude/skills" "$target/.claude/"
cp -R "$here/scripts" "$target/"
rm -f "$target/scripts/install.sh"
cp "$here/AGENTS.md" "$target/AGENTS.md"
cp "$here/CLAUDE.md" "$target/CLAUDE.md"

if [ -f "$here/.env" ] && [ ! -f "$target/.env" ]; then
  grep '^AKAPULU_API_KEY=' "$here/.env" > "$target/.env" 2>/dev/null || true
fi
grep -qs '^\.env$' "$target/.gitignore" || printf '\n.env\nakapulu/\n' >> "$target/.gitignore"

echo "Installed into $target"
echo "  .agents/skills/akapulu-avatar/   the skill, for Codex"
echo "  .claude/skills/akapulu-avatar/   the same skill, for Claude Code"
echo "  scripts/                         the validator and the API client"
echo
[ -f "$target/.env" ] && echo "Your key came across too." || echo "Next: run ./scripts/setup.sh in that folder to add your Akapulu key."
echo
echo "Then open $target in Codex or Claude Code and say:"
echo "  build me an avatar assistant from this site"
