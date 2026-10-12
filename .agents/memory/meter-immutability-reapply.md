---
name: meter-immutability-reapply
description: Plan to re-apply the meter-speed immutability rewrite fresh on master instead of merging the stale branch
metadata:
  type: project
---

The `origin/meter-speed` branch (16 commits, Oct 2022) is a two-part meter rewrite:

1. **Representation change** — meter's internal form goes from strings (`'1/4'`,
   `f'1/{d}'`) to tuples: `NumDenom = tuple[int, int]` (i.e. `(1, 4)`), with
   `NumDenomTuple` / `MeterOptions` aliases in `meter/tools.py`.
2. **Immutability** — `MeterTerminal` / `MeterSequence` become slotted and
   immutable (`SlottedObjectMixin` / `common.FrozenObject`, `FrozenDuration`,
   `_durationFromNumeratorDenominator` cached with `lru_cache`). Immutable meter
   terminals can be shared/cached with no defensive copies.

**Why not just merge master in (decided 2026-06-30):** the branch is 879 commits
behind. Merging `master` produced deep *semantic* conflicts — 31 hunks in
`meter/core.py`, 8 in `meter/tools.py` — because master independently evolved the
*string-based, mutable* code for a year+ (added typing like `-> None`, a `weight`
property, parse fast-paths, and a public→private rename `addTerminal` →
`_addTerminal`). Almost every hunk is two different implementations of the same
method, and the str→tuple change ripples into callers. Resolving that merge would
mean finishing+rebasing the rewrite through hundreds of collisions — not worth it.

**How to apply:** treat `origin/meter-speed` as a *reference*, not a mergeable
branch. Start a clean branch off current `master` and re-apply only the wanted
pieces as a fresh, reviewable change: `FrozenDuration`, slotted/immutable
`MeterTerminal` & `MeterSequence`, and the tuple `NumDenom` internal
representation. Note `common.FrozenObject` is **already in master** (typed for
3.12+), so only the meter-specific immutability needs porting. Validate against the
full `music21/meter` test suite and fix downstream callers. Keep `origin/meter-speed`
until the re-apply lands; delete it afterward.
