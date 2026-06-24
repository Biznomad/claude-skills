#!/usr/bin/env bash
#
# bootstrap.sh — set up Biznomad's Claude Code skills + plugins on a new machine.
#
#   Usage (idempotent — safe to re-run):
#     curl -fsSL https://raw.githubusercontent.com/Biznomad/claude-skills/master/bootstrap.sh | bash
#   or:
#     git clone https://github.com/Biznomad/claude-skills.git ~/biznomad-skills
#     bash ~/biznomad-skills/bootstrap.sh
#
#   What it does:
#     1. Clones/pulls the skills repo to ~/biznomad-skills
#     2. Symlinks every real skill (has SKILL.md) into ~/.claude/skills/
#     3. Re-adds every plugin marketplace
#     4. Re-installs every plugin (superpowers, gsd, etc.)
#     5. Installs gstack if missing
#     6. Prints manual follow-ups it can't safely automate
#
set -uo pipefail

REPO_URL="https://github.com/Biznomad/claude-skills.git"
REPO_DIR="${HOME}/biznomad-skills"
SKILLS_DIR="${HOME}/.claude/skills"

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
ok()    { printf '  \033[0;32m✓\033[0m %s\n' "$*"; }
warn()  { printf '  \033[0;33m!\033[0m %s\n' "$*"; }
step()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# 0. Locate the REAL claude binary
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
# 1. Clone or update the skills repo into ~/biznomad-skills
# ---------------------------------------------------------------------------
step "Syncing skills repo → $REPO_DIR"
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only && ok "pulled latest"
else
  git clone "$REPO_URL" "$REPO_DIR" && ok "cloned"
fi

# ---------------------------------------------------------------------------
# 2. Symlink every real skill into ~/.claude/skills/
#    A "real" skill is a directory (or resolved symlink) that contains SKILL.md.
#    Skips skills already present in ~/.claude/skills/ (idempotent).
# ---------------------------------------------------------------------------
step "Symlinking skills → $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
installed=0
skipped=0
for entry in "$REPO_DIR"/*/; do
  skill=$(basename "$entry")
  # Resolve the entry (follow symlinks so we can check SKILL.md inside)
  resolved=$(realpath "$entry" 2>/dev/null || true)
  [ -z "$resolved" ] && { warn "broken symlink: $skill (skipping)"; continue; }
  # Must be a directory with a readable SKILL.md
  [ -f "$resolved/SKILL.md" ] || continue
  target="$SKILLS_DIR/$skill"
  if [ -e "$target" ] || [ -L "$target" ]; then
    ((skipped++))
  else
    ln -s "$resolved" "$target"
    ok "linked: $skill"
    ((installed++))
  fi
done
ok "$installed new skills linked, $skipped already present"

# ---------------------------------------------------------------------------
# 3. Plugin marketplaces
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
    warn "already present or failed: $m"
  fi
done

# ---------------------------------------------------------------------------
# 4. Plugins
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
# 5. gstack toolkit
# ---------------------------------------------------------------------------
step "gstack toolkit"
GSTACK_DIR="${SKILLS_DIR}/gstack"
if [ -d "$GSTACK_DIR/.git" ]; then
  git -C "$GSTACK_DIR" pull --ff-only && ok "gstack updated" || warn "gstack pull failed (check manually)"
elif [ "${INSTALL_GSTACK:-ask}" = "no" ]; then
  warn "skipped (INSTALL_GSTACK=no)"
else
  read -r -p "  Clone gstack (~480MB) into $GSTACK_DIR? [y/N] " a
  if [[ "${a:-N}" =~ ^[Yy]$ ]]; then
    git clone https://github.com/garrytan/gstack.git "$GSTACK_DIR" \
      && cd "$GSTACK_DIR" && ./setup \
      && ok "gstack installed"
  else
    warn "skipped gstack"
  fi
fi

# ---------------------------------------------------------------------------
# 6. Manual follow-ups
# ---------------------------------------------------------------------------
step "Manual follow-ups"
cat <<'NOTES'
  These require manual steps:

  • ~/.agents/skills (installed by Claude Code plugin system)
      Skills in the repo that symlink to ~/.agents/skills are resolved
      automatically if that directory exists. Install plugins (step 4 above)
      to populate it.

  • cua-driver
      Points to /Applications/CuaDriver.app — install CuaDriver on this machine.

  • codex-bridge plugin (local directory marketplace)
      Clone the project, then:
        claude plugin marketplace add ~/Projects/MCP-Servers/codex-bridge
        claude plugin install codex-bridge@codex-bridge --scope user

  To update all skills in future:
        git -C ~/biznomad-skills pull

  To verify:
        ls ~/.claude/skills | wc -l
        claude plugin list

  Restart Claude Code to pick up newly linked skills.
NOTES

bold "Done. $(ls "$SKILLS_DIR" | wc -l | tr -d ' ') skills now in $SKILLS_DIR"
