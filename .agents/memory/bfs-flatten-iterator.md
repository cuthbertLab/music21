---
name: bfs-flatten-iterator
description: Idea to flatten a Stream via a lazy breadth-first iterator instead of building a new Stream — viable, but must not reuse the flat/flatten name
metadata:
  type: project
---

We once tried (the deleted `flatIterator` branch, Aug 2022) to turn
`Stream.flatten()` / the old `.flat` into a **lazy iterator** instead of
constructing a brand-new flattened Stream — a `FlatIterator` that yields elements
in order without materializing the container.

**Why it stalled:** the offsets. A flattened element's offset (relative to the
whole hierarchy) differs from its offset inside its own container. A materialized
flat Stream stores those recomputed `offsetInHierarchy` values; a lazy iterator
can't hold an offset independent of the site the element actually lives in. Making
that work was too hard, and the branch had to route around it
(`getElementsByOffset` → `getElementsByOffsetInHierarchy`). So *that* exact attempt
is shelved.

**But this is NOT a rejected idea** — call it the **BFS-flatten-iterator**. A lazy
breadth-first (or `iterateByOffset`) iterator that walks the hierarchy in order is
genuinely writable and could speed up flattening, *as long as it does not try to
set `offsetInHierarchy`*. The hard constraint:

- **Do not name it `flat` or `flatten()`.** Those names are too tightly bound to
  the `offsetInHierarchy` contract; reusing them would re-create the blocker above.
  Give the new thing its own name (`breadthFirstIterator` / `iterateByOffset`).

**How to apply:** when we need fast ordered traversal without the offset rewrite —
likely first in `tree/` — write a standalone `breadthFirstIterator` that skips
`offsetInHierarchy`, then potentially have `flatten()` build on it internally.
Treat the original `FlatIterator` as a fun leetcode-style exercise, not a design.
Temper expectations: a plain Python sort is already fast for under ~1000 elements
(the same small-N caveat that sank [[sortedcontainers-for-streams]]), so the
speedup may only matter on large flat scores.
