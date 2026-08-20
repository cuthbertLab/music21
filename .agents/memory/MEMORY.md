# Memory Index

Project-shared agent memory for music21. One file per fact; see frontmatter for type.

- [Branches never to delete](branches-never-delete.md) — `master` and `m21_\d+` are permanent; never prune them
- [sortedcontainers for streams](sortedcontainers-for-streams.md) — tried twice to make streams always-sorted via SortedList; abandoned, too slow for tiny streams
- [Stream subclass generic defaults](stream-subclass-generic-defaults.md) — how `inherit-generics` should work once PEP 696 default type params land; maybe add typing_extensions
- [BFS-flatten-iterator](bfs-flatten-iterator.md) — lazy breadth-first flatten is writable (maybe for tree first), but must not reuse the flat/flatten name tied to offsetInHierarchy
- [Meter immutability re-apply](meter-immutability-reapply.md) — meter-speed is too stale to merge; re-apply FrozenDuration + immutable MeterTerminal + tuple NumDenom fresh on master
