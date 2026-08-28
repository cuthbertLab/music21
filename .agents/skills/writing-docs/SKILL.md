---
name: writing-docs
description: >-
  House style for music21 prose: docstrings, comments, and `Changed in`/`New in`
  markers. Read before writing any of them. Sets the length target, the voice,
  and where a bug fix's test belongs.
---

# Writing docs and comments

## Length

Aim for about 40% of the length an LLM writes by default. Cut qualifiers,
restatements, and the sentence that explains the sentence before it. A comment
earning its place says something the code cannot.

## Prose

Assume the reader is skimming and looking for an excuse to stop. Give them
something to catch on.

**Examples are music.** `key.KeySignature(-3)` is E-flat major, so say E-flat
major. Reach into the corpus rather than inventing `foo`: `bwv66.6` and
`luca/gloria` are in hundreds of docstrings because a reader can hear them.

**Lead with the thing itself.** "Returns the pitches sounding at an offset," not
"This method can be used to obtain the pitches that are sounding."

**Vary sentence length.** Three medium declaratives in a row is where the eye
slides off the page. A short one lands.

**Cut throat-clearing.** "It is important to note that," "Note that in general,"
"This allows the user to." Start at the verb.

**Personality is house style, not a lapse.** `Cannot determine sharps for
quarter-tone keys! silly!` and "it'd wig me out if I ever didn't see them in
reverse alphabetical order" are both shipping music21. Dry, specific, short. A
joke needing a second sentence to land is one sentence too long.

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

## Doctest mechanics

In doctests, no need to run `from music21 import *` that happens automatically (In Jupyter notebooks for the user's guide, the first line should begin `>>> from music21 import *`, so readers remember they need it)

Examples always qualify by module: `note.Note('C4')`, never a bare `Note`.

`OMIT_FROM_DOCS`, alone on a line, hides everything after it: cases worth checking that
no reader wants to meet.

`#_DOCS_HIDE` at the end of a line runs it without showing it; `#_DOCS_SHOW` at the
start of a line shows it without running it. Together they let a doctest look
nondeterministic and still have a fixed answer:

```
>>> import random
>>> randomNumber = 12  #_DOCS_HIDE
>>> #_DOCS_SHOW randomNumber = random.randint(0, 127)
>>> p = pitch.Pitch()
>>> p.ps = randomNumber
>>> p
<music21.pitch.Pitch C1>
```

Link with ``:class:`~music21.note.Note` `` and ``:meth:`~music21.note.Note.addLyric` ``.

## Examples

Give steps that have meaningful intermediate output descriptive names instead of chaining — so readers can understand what the intermediate values are:

```
>>> bachScore = corpus.parse('bwv66.6')
>>> excerpt = bachScore.measures(4, 6)
>>> chordReduction = excerpt.chordify()
```

Pick examples musicians care about: semitones to frequency, not Celsius to Fahrenheit;
scramble "Chaminade", not "puppy". If you cannot think of a reason a musician would call the method, it may not belong in music21.

Describe what a parameter is and does in English if it is not obvious; type alone is not
documentation.

No dull repetition in docs. A bit of humor is welcome in docs; the docs are written
for humans who will close the window if they are dull.  If seven methods do essentially the same thing, give extensive docs the first time and then later methods can refer back to the first method. Don't repeat the same docs over and over.

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

## Writing and Comment style
- When writing comments in code, assume a strong code reader — anything inferable from the code is noise (docs that paraphrase names of functions or variable names esp.); focus on high level issues and gotchas that might bite again if not documented.
- Say how to use code, not prior bugs or how code used to work or what was removed. That's for commit messages. Don't document where code is called from except for "keep in sync" lines across Py/TS.
- Don't hijack a docstring for your addition. Original purpose line stays primary + one short line for the new bit. Prefer not documenting a small feature over making it seem like the primary reason for the code.
- Examples of usage are usually better than long descriptions.
- Avoid jargon not already found in the codebase; use plain descriptive English.
- Rare paths should get little weight: in both code and docs. Use try/except over if/else when the except clause is rare. In docs, state the 90% path first and point exceptional cases to code that handle it.
- When wording is dictated to the agent to substitute for original wording, use it. Do not add parentheticals. Only fix obvious typos.
- No weapon-metaphors or overly militaristic language. Avoid "blast radius", "rearm", "landmine",
     "detonate" in issues/PR/code.  Trigger or fire events is so commonly used that they're okay.


