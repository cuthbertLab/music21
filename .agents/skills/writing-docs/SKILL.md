---
name: writing-docs
description: >-
  House style for docstrings, code comments, and `Changed in`/`New in` version
  markers in music21. Use whenever you write or edit a docstring or comment, add
  a version marker, or decide where a bug fix's test belongs. Covers the length
  target, the rule against narrating bugs you just fixed, and why regression
  cases go in unittests rather than doctests.
---

# Writing docs and comments

## Length

Aim for about 40% of the length an LLM writes by default. Cut qualifiers,
restatements, and the sentence that explains the sentence before it. A comment
earning its place says something the code cannot.

## Say what is, not what was or what not to do

Describe current behavior. Do not narrate the bug you just fixed, the old
spelling of an API, or when upstream changed something.

```python
# yes
# ligature brackets; manual beams are plain [ and ]
return self.backslash + '[ '

# no
# \[ used to be emitted for beams, which was wrong -- LilyPond renamed
# this in 2.16 and it silently produced nothing
```

The commit message is where a fixed bug belongs: why it was wrong, how it was
found, what it broke. That costs nothing until someone runs `git log`, and
`git blame` leads them there from the line itself.

The exception is a mistake that is likely to recur — a genuine trap that the
next person would otherwise walk into. Rare. Prefer stating the rule positively
even then.

## Version markers

`* Changed in v[X]: one line.` or `* New in v[X].` Only for user-facing changes
to the public interface: a signature, a return type, an output format. Keep to
what a reader must act on; drop the before-picture.

```
* Changed in v11: `stringOutput()` always returns a `str`, never None.
* Changed in v11: emits `\tuplet`; the arguments are now actual, normal.
* New in v11.
```

A plain bug fix — code now does what it always claimed — gets no marker and no
doctest. It goes in the commit message.

See the `bump-version` skill for which digit to change and the odd/even
convention.

## Doctests are not regression tests

Doctests are documentation that happens to be verified. Every example must earn
its place by teaching the reader something about how to use the object.

Regression cases go in the module's `Test(unittest.TestCase)` class, where a
comment or the method name can name the issue:

```python
def testMetronomeMarkWrittenInStream(self):
    # https://github.com/cuthbertLab/music21/issues/1852
    ...
```

So: a fix for a crash on an edge case, a check that some input no longer
produces invalid output, an assertion tied to an issue number — unittest. An
example a user would want to read — doctest.

The trap is the one-line `Traceback` example proving that bad input now raises.
It looks like documentation and costs almost nothing to add, but the input comes
from the bug rather than from anything a user would write, so it teaches nothing
while making an obscure corner one of the first things a reader meets. It is a
unittest.

Naming the guarded bug **is** appropriate in a unittest; that is what the test
is for. The rule against narrating old bugs applies to docstrings and to
comments in shipping code, not to tests.
