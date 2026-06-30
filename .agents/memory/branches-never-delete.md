---
name: branches-never-delete
description: Local/remote git branches that must never be deleted during branch cleanup
metadata:
  type: project
---

These music21 branches are kept long-term and must **never** be deleted during
any branch-cleanup or housekeeping pass:

- `master` — the main branch.
- `m21_<N>` — version-maintenance branches, e.g. `m21_9`, `m21_10`, and any
  future `m21_<N>` (matched by the regex `m21_\d+`). Used to back-port fixes to
  released minor versions.

**Why:** these are permanent release/maintenance lines, not feature work, so
they have no "merge into master and delete" lifecycle. Deleting one loses the
maintenance history for that release series.

**How to apply:** when asked to review/prune branches, exclude these from the
candidate list automatically and never propose deleting them. Any other branch
is fair game for the normal merge-or-close evaluation. (Note: working branches
like `no-cover-defaultlist` or `makeAccidentals-deque` may be excluded from a
given review because the user already knows them, but that is per-request — only
`master` and `m21_\d+` are the permanent never-delete set.)
