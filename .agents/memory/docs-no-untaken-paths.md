---
name: docs-no-untaken-paths
description: Docstrings and doctests describe what the code does, never the designs it avoided
metadata:
  type: feedback
---

When writing docstrings and doctests for music21, do not spend words (or
doctest lines) explaining what the code *doesn't* do or contrasting with
rejected alternatives — e.g. cut "not literally 'mod 7', which would make it
0" from a description that already states the value is always 1-7. Myke: "we
don't spend doctest time reinforcing paths we didn't take."

**Why:** every sentence in a docstring is maintained forever and read by users
who never saw the alternative; contrast-with-the-wrong-design is
reviewer-facing noise, like comments justifying a change.

**How to apply:** state the positive contract with examples of real values. If
a name is misleading (like `GenericInterval.mod7`, which actually returns
simple-interval values 1-7), document the actual behavior — don't argue with
the name in prose. Related style rule: [[docs-audience-separation]].
