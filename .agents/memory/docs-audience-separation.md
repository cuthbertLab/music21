---
name: docs-audience-separation
description: Public docstrings are for library users; maintenance notes and private-symbol references go in code comments
metadata:
  type: feedback
---

Never put maintenance notes ("change one and check the others", refactoring
caveats, cross-references between internal implementations) in music21 public
docstrings, and never reference private (underscore) methods from public
docstrings. Put that material in `#` code comments instead.

**Why:** docstrings render into the published docs and serve library *users*;
comments serve *maintainers*. Myke: "there are different users with different
roles." A user reading the API docs should never see internal plumbing they
cannot call.

**How to apply:** before finishing a doc pass, scan new docstring text for
underscore-prefixed names and maintainer-facing advice; relocate to a comment
just below the docstring. Related style rule: [[docs-no-untaken-paths]].
