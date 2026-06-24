#!/usr/bin/env bash
#
# sync-from-agents.sh — refresh skills that are snapshotted from ~/.agents/skills/
#
# 41 skills in this repo are real COPIES of skills that live canonically in
# ~/.agents/skills/ (managed by the `agents` tool). They used to be symlinks,
# but symlinks can't be tracked by git, so they were dereferenced into copies
# so this public repo is self-contained.
#
# Run this AFTER editing those skills in ~/.agents/skills/ to pull the changes
# into the repo. Only refreshes skills already present here (conservative —
# brand-new skills in .agents are not auto-added). Safe to re-run; idempotent.
#
#   ./sync-from-agents.sh
#   git add -A && git commit -m "Refresh skills from ~/.agents/skills" && git push
#
set -euo pipefail

AGENTS_DIR="${HOME}/.agents/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$AGENTS_DIR" ]; then
  echo "Source not found: $AGENTS_DIR (is the agents tool installed on this machine?)" >&2
  exit 1
fi

count=0
for src in "$AGENTS_DIR"/*/; do
  name="$(basename "$src")"
  if [ -e "$REPO_DIR/$name" ]; then
    rm -rf "$REPO_DIR/$name"
    cp -RL "$src" "$REPO_DIR/$name"
    count=$((count + 1))
  fi
done

echo "Refreshed $count skills from $AGENTS_DIR"
echo "Next: git status  →  git add -A && git commit && git push"
