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

**Related dead end — `bisect_getElements` (deleted):** a 2022 branch that kept the
plain `list` but replaced the linear scan in `getElementAtOrBefore` /
`getElementBeforeOffset` with a binary search (`bisect_right`/`bisect_left` keyed
on `elementOffset`). Because storage stays a list, it avoids the small-stream
*insertion* overhead that sank sortedcontainers — but it applied bisect
*unconditionally*, with no length gate, so tiny streams just ate the property-build
+ per-probe lambda cost for no gain. To be worth anything it would need to check
length first and only bisect the `classList=None` path (the `classList` path still
does an O(n) filter before bisecting, so it can't speed up anyway). And since a
binary search over a list won't actually beat the linear scan until well over
~1000 elements — a size real music21 streams almost never reach — **we should not
pursue bisect-on-list at all.** If we ever want fast offset lookup on big streams,
get it from the swappable-`.core` plan above (a sortedcontainer or binary-search
tree backend), not by bolting `bisect` onto the list.
