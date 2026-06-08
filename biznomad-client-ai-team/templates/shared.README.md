# {{CLIENT_NAME}} Shared Memory

This dir is symlinked into each {{CLIENT_NAME}} Hermes profile as `memories/shared/`.

Each agent owns ONE file here and writes ONLY to that file:
- `ops.md`       → {{SLUG}}-ops writes infra changes + revenue ops decisions
- `social.md`    → {{SLUG}}-social writes campaign briefs + brand decisions
- `marketing.md` → {{SLUG}}-marketing writes ad tests + performance learnings
- `intel.md`    → {{SLUG}}-intel writes competitor + market signals
- `brand.md`     → all four agents read; humans + agents append shared brand facts
- `decisions.md` → human-written quarterly strategy log

Read freely across all files. Write only your own. Conflicts get resolved by
the owner of the file (humans always win over agent writes).
