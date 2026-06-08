#!/usr/bin/env bash
#
# bootstrap.sh — set up Biznomad's Claude Code skills + plugins on a new machine.
#
#   Usage:
#     # 1. clone this repo into place (or run this script from anywhere — it self-clones)
#     git clone https://github.com/Biznomad/claude-skills.git ~/.claude/skills
#     bash ~/.claude/skills/bootstrap.sh
#
#   What it does (idempotent — safe to re-run):
#     1. Ensures ~/.claude/skills is the cloned repo (clones/pulls if needed)
#     2. Re-adds every plugin marketplace this machine uses
#     3. Re-installs every plugin (superpowers, gsd, document-skills, etc.)
#     4. Optionally reinstalls the gstack toolkit
#     5. Prints manual follow-ups it can't safely automate
#
set -uo pipefail

REPO_URL="https://github.com/Biznomad/claude-skills.git"
SKILLS_DIR="${HOME}/.claude/skills"

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
ok()    { printf '  \033[0;32m✓\033[0m %s\n' "$*"; }
warn()  { printf '  \033[0;33m!\033[0m %s\n' "$*"; }
step()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# 0. Locate the REAL claude binary (the user's shell aliases `claude`)
# ---------------------------------------------------------------------------
CLAUDE=""
for c in \
  /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe \
  /opt/homebrew/bin/claude \
  /usr/local/bin/claude \
  "$(command -v claude 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ]; then CLAUDE="$c"; break; fi
done
if [ -z "$CLAUDE" ]; then
  warn "Couldn't find the claude binary. Install Claude Code first:"
  warn "  npm install -g @anthropic-ai/claude-code"
  exit 1
fi
bold "Using claude: $CLAUDE  ($("$CLAUDE" --version 2>/dev/null))"

# ---------------------------------------------------------------------------
# 1. Skills repo into place
# ---------------------------------------------------------------------------
step "Syncing skills repo → $SKILLS_DIR"
if [ -d "$SKILLS_DIR/.git" ]; then
  git -C "$SKILLS_DIR" pull --ff-only && ok "pulled latest"
elif [ -d "$SKILLS_DIR" ] && [ -n "$(ls -A "$SKILLS_DIR" 2>/dev/null)" ]; then
  warn "$SKILLS_DIR exists but is not this git repo — leaving it untouched."
  warn "Move it aside and re-run, or 'git pull' it yourself."
else
  git clone "$REPO_URL" "$SKILLS_DIR" && ok "cloned"
fi

# ---------------------------------------------------------------------------
# 2. Plugin marketplaces  (source = github owner/repo OR git URL)
# ---------------------------------------------------------------------------
step "Adding plugin marketplaces"
MARKETPLACES=(
  "anthropics/claude-plugins-official"
  "anthropics/skills"
  "alirezarezvani/claude-skills"
  "https://github.com/daymade/claude-code-skills.git"
  "mrgoonie/claudekit-skills"
  "thedotmack/claude-mem"
  "mbailey/voicemode"
)
for m in "${MARKETPLACES[@]}"; do
  if "$CLAUDE" plugin marketplace add "$m" >/dev/null 2>&1; then
    ok "marketplace: $m"
  else
    warn "marketplace already present or failed: $m"
  fi
done

# ---------------------------------------------------------------------------
# 3. Plugins  (plugin@marketplace)
# ---------------------------------------------------------------------------
step "Installing plugins (user scope)"
PLUGINS=(
  "superpowers@claude-plugins-official"
  "playwright@claude-plugins-official"
  "slack@claude-plugins-official"
  "github@claude-plugins-official"
  "code-review@claude-plugins-official"
  "feature-dev@claude-plugins-official"
  "document-skills@anthropic-agent-skills"
  "example-skills@anthropic-agent-skills"
  "marketing-skills@claude-code-skills"
  "engineering-skills@claude-code-skills"
  "product-skills@claude-code-skills"
  "github-ops@daymade-skills"
  "markdown-tools@daymade-skills"
  "mermaid-tools@daymade-skills"
  "skill-creator@daymade-skills"
  "debugging-tools@claudekit-skills"
  "claude-mem@thedotmack"
  "voicemode@voicemode"
)
for p in "${PLUGINS[@]}"; do
  if "$CLAUDE" plugin install "$p" --scope user >/dev/null 2>&1; then
    ok "installed: $p"
  else
    warn "already installed or failed: $p"
  fi
done

# ---------------------------------------------------------------------------
# 4. gstack toolkit (478 MB, lives inside the skills dir, has its own git)
# ---------------------------------------------------------------------------
step "gstack toolkit"
if [ -d "$SKILLS_DIR/gstack/.git" ]; then
  ok "gstack already present"
elif [ "${INSTALL_GSTACK:-ask}" = "no" ]; then
  warn "skipped (INSTALL_GSTACK=no)"
else
  read -r -p "  Clone gstack (~480MB) into skills dir? [y/N] " a
  if [[ "${a:-N}" =~ ^[Yy]$ ]]; then
    git clone https://github.com/garrytan/gstack.git "$SKILLS_DIR/gstack" \
      && ok "gstack cloned (run its own installer if it has one)"
  else
    warn "skipped gstack"
  fi
fi

# ---------------------------------------------------------------------------
# 5. Manual follow-ups this script can't safely automate
# ---------------------------------------------------------------------------
step "Manual follow-ups"
cat <<'NOTES'
  These were intentionally excluded from the git repo:

  • .agents-symlinked skills (42 of them)
      The repo skips skills that were symlinks into ~/.agents/skills.
      If you use that skill set, restore ~/.agents/skills on this machine
      (rsync it from the source machine, or reinstall whatever populated it).

  • email-marketing-bible
      Embedded third-party repo. Reinstall it from its own source if needed.

  • codex-bridge plugin (local directory marketplace)
      It pointed at /Users/<you>/Projects/MCP-Servers/codex-bridge on the
      source machine. Clone that project here, then:
        claude plugin marketplace add ~/Projects/MCP-Servers/codex-bridge
        claude plugin install codex-bridge@codex-bridge --scope user

  Verify everything loaded:
        claude plugin list
        ls ~/.claude/skills | wc -l

  Restart Claude Code (or run /plugin) to pick up newly installed plugins.
NOTES

bold "Done."
