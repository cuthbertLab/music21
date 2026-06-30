---
name: sortedcontainers-for-streams
description: Why we tried (and abandoned) backing Stream storage with the sortedcontainers library
metadata:
  type: project
---

We twice prototyped replacing `StreamCore`'s hand-rolled sorted-insertion
bookkeeping with the `sortedcontainers.SortedList` library, on two now-deleted
branches:

- `sortedcontainers` — the full version. `StreamCore._elements` /
  `_endElements` became `SortedList[ElementStore]`, where
  `ElementStore = NamedTuple(sortTuple, element)` (added to `sorting.py`) pairs
  each element with its `SortTuple` key so ordering is intrinsic to the
  container. This let the entire `isSorted` flag machinery be deleted — no
  `clearIsSorted`, no `ignoreSort` param, no `storeSorted` logic, no lazy
  sort-on-access — shrinking `stream/base.py` by ~189 lines.
- `sorted_container_tree` — a narrower probe applying `SortedList` only to the
  interval-tree internals (`tree/core2.py`) as a lower-risk place to validate the
  approach first.

**The gain:** music21 streams would always be sorted by construction, removing a
whole class of "is this sorted yet?" state and the bugs that hide in it.

**Why we abandoned it:** `SortedList` is far too slow for *tiny* streams — the
overwhelmingly common case (e.g. a measure with 4 notes). The library's
B-tree-ish machinery only pays off at sizes music21 streams rarely reach, and the
per-insert constant-factor overhead is a net loss for small containers. The plain
`list` + append-at-end fast path beats it for real scores.

**How to apply:** don't reach for `sortedcontainers` (or a similar balanced-tree
container) to make streams always-sorted — it's already been tried twice and lost
on small-stream speed. If revisiting, benchmark the 2–8 element case first, not
just large streams. Both branches were deleted; the good ideas live here.

**Longer-term idea (Myke):** once `StreamCore` lives on `Stream` as `Stream.core`
(the deferred composition refactor), make two *swappable* `stream/core.py`
StreamCore implementations behind one shared abstract interface — the default
`list`-based `.core` for small streams, and a tree/B-tree or sortedcontainer
`.core` that a large stream can swap in. Each backing store is then best-suited to
its workload (tiny measures vs. huge flat scores) instead of forcing one container
to win both cases — which is exactly the trade-off that sank the all-or-nothing
attempts above.
