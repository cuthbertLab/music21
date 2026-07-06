# Memory Index

Project-shared agent memory for music21. One file per fact; see frontmatter for type.

- [Branches never to delete](branches-never-delete.md) — `master` and `m21_\d+` are permanent; never prune them
- [sortedcontainers for streams](sortedcontainers-for-streams.md) — tried twice to make streams always-sorted via SortedList; abandoned, too slow for tiny streams
- [Stream subclass generic defaults](stream-subclass-generic-defaults.md) — how `inherit-generics` should work once PEP 696 default type params land; maybe add typing_extensions
- [BFS-flatten-iterator](bfs-flatten-iterator.md) — lazy breadth-first flatten is writable (maybe for tree first), but must not reuse the flat/flatten name tied to offsetInHierarchy
- [Docs: audience separation](docs-audience-separation.md) — maintenance notes and private-method references go in code comments, never public docstrings
- [Docs: no untaken paths](docs-no-untaken-paths.md) — docstrings state what the code does, never contrast with rejected designs
- [Issue #1349 romanNumeral direction](issue-1349-romanNumeral-direction.md) — raised-^6/^7 fix landed; CAUTIONARY default kept; items 2+4 open with pablopupo/Malcolm
