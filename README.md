# claude-skills

Personal Claude Code skills (agent skills invoked by description or slash command).

## Layout

- **Most skills are real directories** here — a `SKILL.md` plus scripts/references.
- **41 skills are snapshots** copied from a local canonical store at `~/.agents/skills/`
  (managed by the `agents` tool). They are committed as real copies because git
  cannot track symlinks — the repo is self-contained and clones cleanly anywhere.
  Refresh them with `./sync-from-agents.sh` (see below).
- **Third-party toolkits are excluded** via `.gitignore`: `gstack/` (→ `garrytan/gstack`)
  and `email-marketing-bible/` (→ `CosmoBlk/email-marketing-bible`) carry their own
  upstreams. `node_modules/`, venvs, `__pycache__`, and binary media are also ignored.

## Refreshing the snapshotted skills

After editing skills in `~/.agents/skills/`, pull the changes into this repo:

```bash
./sync-from-agents.sh
git add -A && git commit -m "Refresh skills from ~/.agents/skills" && git push
```

## Setup on a new machine

See [`bootstrap.sh`](bootstrap.sh).

## Adding a new skill

Create `<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`,
optional `allowed-tools`). Commit it. If it should mirror `~/.agents/skills/`,
add it there too and use `sync-from-agents.sh` to keep them in sync.
