# Verticality consolidation plan

music21 has two classes called Verticality. This plan makes `tree.verticality.Verticality`
the one people use, moves it to a top-level module, `music21.verticality`, and deprecates the
older `voiceLeading.Verticality`. Later, the `voiceLeading.VerticalityNTuplet` and
`VerticalityTriplet` classes get the same treatment.

Nothing has been implemented yet. The target is v11.

The work would go in as a series of small PRs, each on its own branch off `master`. The
"Order of work" section at the end gives the sequence. The lettered sections before it
describe each change.


## Questions for Michael

1. Deprecate `voiceLeading.Verticality` in v11 and remove it in v13? Yes, or v12 to v14
   if this slips to v12.
2. On an empty chord, `root()` keeps raising. Whether `bass()` should raise too, instead
   of returning `None`, is open and minor (see G).


## Already decided

- Keep the empty Verticality at the final barline (see G).
- No general-purpose helper for "run this test over every Verticality." The docs show
  the loop instead.
- The object returned by `Stream.verticalities()` is called `VerticalityView` (see A).
- Everything new is fully typed and passes mypy.
- `tree.verticality` moves to `music21.verticality` with no deprecation period, unless a
  search of GitHub finds outside code importing it. `voiceLeading.Verticality` gets the
  usual v11 to v13 period.
- `VerticalitySequence` replaces the tuplet classes. It gets designed now and built last.
- Adding the Rouen example to the corpus index is its own task.


## Principles

1. **A Verticality is everything happening at one offset.** That includes keys, clefs,
   time signatures and barlines at that offset, not just notes. Methods that analyze
   pitches (`toChord`, `pitchSet`, `getAllVoiceLeadingQuartets`, ...) already skip the
   unpitched objects, so including them does no harm.
2. **Users shouldn't need to know about timespans.** `startTimespans`, `overlapTimespans`,
   and the rest of the timespan layer are internals. Someone should be able to loop over
   Verticalities, get chords, and find voice-leading quartets without ever reading the word
   "timespan" or "tree." Timespans become an advanced topic.
3. **Find parts from elements, not by number.** No `partNum` arguments. To get an
   element's part, use `element.getContextByClass(stream.Part)`. For one part's
   Verticalities, call `.verticalities()` on that Part.
4. **A Verticality doesn't change the score.** Changing the durations of the notes at an
   offset is an advanced timespans operation to document later, not a Verticality method.
5. **Everything is fully typed**, in PEP 695 style.


## What success looks like: theoryAnalyzer, without its limits

The old `theoryAnalysis.theoryAnalyzer` (now in `cuthbertLab/music21-tools`) made it easy to
ask "where are all the parallel fifths, hidden octaves, and passing tones in this score?"
This plan should make that easy again, without the parts that tied it to Bach-chorale
homework.

Underneath, theoryAnalyzer did one thing over and over: test every `VoiceLeadingQuartet` (or
Verticality, or triplet) in the score and collect the ones that passed. Each `identifyX` was
`lambda vlq: vlq.X()` plus a sentence of text. Almost all of those tests already exist on
`VoiceLeadingQuartet`:

| theoryAnalyzer could find... | Today, use... |
|---|---|
| parallel 5ths, 8ves, unisons | `VoiceLeadingQuartet.parallelFifth()`, `parallelOctave()`, `parallelUnison()` |
| hidden 5ths, 8ves | `hiddenFifth()`, `hiddenOctave()` |
| kinds of motion | `obliqueMotion()` ... `antiParallelMotion()`, `motionType()` |
| improper resolution, unfilled leaps, modal openings and closings | `isProperResolution()`, `leapNotSetWithStep()`, `modalOpening()`, `opensIncorrectly()`, `clausulaVera()`, `closesIncorrectly()` |
| harmonic and melodic intervals between parts | a few lines over Verticalities or pairs of parts |
| passing and neighbor tones | only `VerticalityTriplet.hasPassingTone()` / `hasNeighborTone()`; this is the one real gap (see E) |
| scale degrees, tonic/dominant, "common-practice errors" | out of scope; these belong with keys and Roman numerals and assume Bach the most |

So the voice-leading tests are already there. Running one over a whole score is about five
lines, as in the `findingParallels` notebook. The work is making that loop easy to write and
easy to teach, not bringing back theoryAnalyzer.

What we leave behind:

- **Results stored in a dictionary** (`analyzer.store[score.id]['ResultDict'][dictKey]`).
  Functions should just return a list.
- **Parts by number** (`partNum1`, `partNum2`, `partNumToIdentify`, and text like
  `'Part ' + str(pn+1)`). Use the Part object, and check all pairs of parts by default.
- **Coloring as a side effect.** `identifyX` changed notehead colors. Return the results
  and let the caller color or show them. Coloring belongs to the notes in a quartet, not to
  a Verticality.
- **Results that are English sentences** (`VLQTheoryResult.text`). A result should hold
  the objects (the quartet, offset, measure, parts) and leave wording to the caller.
- **Bach-chorale assumptions** (`identifyCommonPracticeErrors`, `identifyTonicAndDominant`,
  the SATB setup). Keep the neutral tests and leave out the style-specific bundles.


## Why this is safe

`voiceLeading.Verticality`, `VerticalityNTuplet`, and `VerticalityTriplet` are used only
inside `voiceLeading.py`. Nothing else in music21 calls them, and `getChord()` is in no
documentation notebook. So almost nothing needs updating before the deprecation.


## The changes

### A. New Stream methods

Add to `stream.Stream` in `stream/base.py`, since this is everyday, taught-early API. Both
use the already-cached `asTimespans()`:

```python
def verticalities(self, *, classList=None) -> VerticalityView:
    '''
    The Verticalities of this stream, one per offset. Can be looped over more
    than once, and reversed.
    '''
    return VerticalityView(self, classList=classList)

def getVerticalityAt(self, offset: OffsetQLIn, *, classList=None) -> Verticality:
    '''
    The Verticality sounding at offset.
    '''
    return self.asTimespans(flatten=True, classList=classList).getVerticalityAt(offset)
```

`VerticalityView` takes the Stream and builds the timespan tree once, in `__init__`, as a
public attribute. Advanced users can pass in a tree they already have with `tree=`:

```python
class VerticalityView:
    def __init__(self, srcStream: stream.Stream, *, classList=None,
                 tree: TimespanTree | None = None) -> None:
        self.stream = srcStream
        self.classList = classList
        self.tree: TimespanTree = (
            tree if tree is not None
            else srcStream.asTimespans(flatten=True, classList=classList))
    def __iter__(self) -> Iterator[Verticality]:
        return self.tree.iterateVerticalities()
    def __reversed__(self) -> Iterator[Verticality]:
        return self.tree.iterateVerticalities(reverse=True)
```

Because the tree is built once, `v = score.verticalities()` keeps showing the score as it
was when `v` was made, even if notes are later added or moved. Rebuilding the tree on every
loop would be slow and surprising. The docs should mention one exception: the timespans
still point at the real Note objects, so changing a note's pitch does show up.

Why `VerticalityView` and not `VerticalityIterator`: in music21, an `...Iterator`
(`StreamIterator`, `OffsetIterator`, `corpus.chorales.Iterator`) has its own `__next__`, keeps
a position, and can usually be indexed. `VerticalityView` does none of that; it just hands out
a new generator each time. (Python's own views, like `dict.keys()`, update live, so the
docstring should say this one doesn't.)

Other details:

- The method is `Stream.verticalities()`, not `iterateVerticalities()`. The tree keeps its
  own `iterateVerticalities()`.
- It always flattens. Since a `Part` is a Stream, `part.verticalities()` gives one part's
  Verticalities with no extra work.
- No `reverse=` argument; `reversed()` works.
- `classList=None` by default, so keys, clefs, and barlines are included (principle 1). For
  notes and chords only, pass `classList=(note.NotRest,)`.

With `classList=None`, the last Verticality is the final barline, and it is empty: `pitchSet`
is `set()`, `toChord()` gives an empty `Chord`, and `isConsonant()` is `False` (see G). That
is true to "every offset," and leaving it out would also hide a key or clef change that falls
between notes in mid-piece.

### B. Changes to `tree.verticality.Verticality`

- **B1. Make it iterable**, replacing `objects`: add `__iter__` (and probably `__len__` and
  `__contains__`) over the elements sounding at that offset, so users write
  `for el in verticality:` instead of reading `startAndOverlapTimespans`. That is the most
  common reason people reach into timespans today.
- **B2. Add `isConsonant()`**, for now just `return self.toChord().isConsonant()`. It
  returns `False` on an empty Verticality (see G).
- **B3. Keep everything else**: `toChord()`, `.offset`, `pitchSet`, `pitchClassSet`,
  `beatStrength`, `measureNumber`, `nextVerticality` / `previousVerticality`,
  `nextStartOffset`, `timeToNextEvent`, `bassTimespan`, `makeElement()`,
  `getAllVoiceLeadingQuartets()`, `getPairedMotion()`.

### C. `includeRests` defaults to False

In `getAllVoiceLeadingQuartets` and `getPairedMotion`, change the default from
`includeRests=True` to `False`. A rest is not a voice moving. `True` has only been harmless
because people usually build the tree from notes only. The `tree` package has always been
beta, so changing the default is allowed. Output changes in `tree/verticality.py` (two
doctests), `usersGuide_61_trees.ipynb`, and `devTest_timespans.ipynb`.

### D. What happens to each `voiceLeading.Verticality` member

| member | plan | instead |
|---|---|---|
| `getChord()` | remove | `toChord()` |
| `isConsonant()` | move over (B2) | |
| `objects` | replace | loop over the Verticality (B1) |
| `getObjectsByClass(classes, partNums)` | remove | loop and check class |
| `getObjectsByPart(partNum, ...)` | remove | `element.getContextByClass(Part)`, or `part.verticalities()` |
| `getVerticalityOffset(leftAlign=)` | remove | `.offset` (`leftAlign=False` was never used) |
| `getStream()` | remove | already marked `# probably wrong!`; use `chordify()` or `makeElement()` |
| `makeAllSmallestDuration()`, `makeAllLargestDuration()` | remove | `makeElement(ql)` |
| `getShortestDuration()`, `getLongestDuration()` | remove | `timeToNextEvent` |
| `changeDurationOfAllObjects(ql)` | remove | an advanced timespans topic, later |
| `color`, `lyric` | remove | color or label the notes of a quartet instead |

The five duration methods date from before `chordify()` handled durations correctly, and
none of them belongs on a Verticality.

### E. `VerticalitySequence` replaces the tuplet classes

`VerticalityNTuplet` and `VerticalityTriplet` are a run of N Verticalities plus
`hasPassingTone()` and `hasNeighborTone()`. Design the replacement now and build it last.

- **The run of N Verticalities already exists.** `TimespanTree.iterateVerticalitiesNwise(n)`
  gives `VerticalitySequence` objects (with `__len__`, `__getitem__`, `unwrap`). Add
  `Stream.verticalitiesNwise(n=3)` so users never need the tree.
- **The analysis needs moving.** Put `hasPassingTone()` and `hasNeighborTone()` on a
  three-Verticality `VerticalitySequence`, dropping the same things as in D: no
  `partNumToIdentify` and no coloring; keep `unaccentedOnly`. Then deprecate the tuplet
  classes with a pointer here.

The GitHub search turned up one outside user of the tuplet classes (through the old
theoryAnalyzer), so they need a real replacement, not just removal.

### F. How the deprecation works

- **`voiceLeading.Verticality` and the tuplet classes** have been public and documented for
  years. Put `@common.deprecated('v11', 'v13', '...use music21.verticality.Verticality...')`
  on `__init__`, and on removed methods someone might still call on an old object. Remove
  no earlier than v13. Point the docstring at the replacements.
- **The `tree.verticality` module** is advanced, barely documented, and beta. Move it to
  `music21.verticality` without a deprecation period and update the four or so references
  inside music21. Leave a stand-in at the old path only if the GitHub search finds outside
  code importing it.

This way there are never more than two classes named Verticality at a time. It is also why
the new home can't be `voiceLeading.py`: the deprecated `voiceLeading.Verticality` keeps
that name until v13.

### G. Empty chords

Keeping the empty final Verticality means empty chords will show up much more often. What
they do now:

- **Fine already:** `isConsonant()` is `False`, `bass()` is `None`, `third` and `fifth` are
  `None`, `quality` is `'other'`, `isTriad()` is `False`, `commonName` is `'empty chord'`,
  `orderedPitchClasses` is `[]`, `intervalVector` is all zeros, and `closedPosition()` is an
  empty chord.
- **Raises:** `root()` raises `ChordException('no pitches in chord')`, unlike `bass()`.

To do:

- `root()` keeps raising. Maybe make `bass()` raise too (question 2 above), which would
  match its type hint: it already says it returns a `Pitch`, never `None`. About five places in music21 check
  `bass() is None` and would need changing (`chord/__init__.py`, `harmony.py`,
  `features/native.py`).
- Add tests for empty chords across the common methods.
- Add one line to the docs of methods where the empty-chord answer isn't obvious:
  `isConsonant()` and `root()`. Not `isTriad()` and the like.

### H. Move Verticality to `music21.verticality`

Move `Verticality`, `VerticalityView`, and `VerticalitySequence` out of `tree/` into
`music21/verticality.py`, so people meet "everything at one offset" without having to learn
about trees. This is easier than it sounds:

- `tree/spans.py` mentions `Verticality` only in docstrings and imports nothing from `tree`,
  so `verticality` can import from it with no circular import.
- The only circular import is between `tree/trees.py` and verticality (`getVerticalityAt`
  returns a `Verticality`), and that one exists already. The move adds none.

So it is a file move plus about four reference updates:

- No stand-in at the old path unless the GitHub search finds outside importers. If it does,
  a short `tree/verticality.py` with `from music21.verticality import *` for one release line.
- Import lazily where load order requires it; the file already does so for `timespanTree`,
  `stream`, `voiceLeading`, and `tree.analysis`.
- Add `music21/verticality.py` to the module list and the reference docs.

A `Verticality` will still hold timespans from `tree.spans` internally. The move changes what
users see and where they look for it, and keeps it next to `voiceLeading`.

### I. A User's Guide chapter on finding parallels

Turn the `findingParallels` notebook into a User's Guide chapter in the usual tone, and add
the `theoryExercises/Rouen` example, which is full of parallels, alongside the one subtle Bach
example. This comes last, once the new methods and `music21.verticality` exist.


## Order of work

Each step is its own PR off `master`.

### First: groundwork

- **Type and tidy the `tree` package.** Several small PRs: first a grammar and punctuation
  pass over `music21/tree/` with no code changes, then type it module by module, starting
  with `spans`. Must pass ruff, mypy, and pylint with doctests unchanged.
- **Finish the GitHub search.** This decides whether the move in H needs a stand-in, and
  checks that removing `voiceLeading.Verticality` is safe. So far: nobody outside music21
  calls the duration methods, and one project uses the tuplet classes, through the old
  theoryAnalyzer. Still to search for: `tree.verticality`, `from music21.tree.verticality
  import`, `.iterateVerticalities`, and `.getVerticalityAt`. If none turn up, no stand-in.
  (`gh search code` has no regex and misses private repos and notebooks, so "none found"
  is good evidence but not proof.)

### Then: the main changes

1. New methods (A, B, G): `VerticalityView`, `Stream.verticalities()`,
   `getVerticalityAt()`, `verticalitiesNwise(n=3)`; `__iter__`, `__len__`, `__contains__`,
   and `isConsonant()` on Verticality; empty-chord tests and doc lines; the `bass()`
   decision. Fully typed, with doctests, marked New in v11. Then change the
   `findingParallels` loop to `for v in score.verticalities():`.
2. `includeRests` default (C), with the two doctests and two notebooks.
3. Deprecate `voiceLeading.Verticality` (D, F).
4. Move to `music21.verticality` (H), after the `tree` typing and the GitHub search.

### Last

1. Add Rouen to the corpus index: regenerate `music21/corpus/_metadataCache/core.p.gz` so
   `corpus.search('Rouen')` finds it, check the corpus-count tests (`corpus/testCorpus.py`
   and the range doctest in `corpora.py`, probably still fine), and commit the new
   `core.p.gz`.
2. The User's Guide chapter (I).
3. Tuplet classes to `VerticalitySequence` (E): move `hasPassingTone()` and
   `hasNeighborTone()`, then deprecate the tuplet classes.


## Later, once `tree` is typed

These came up while typing `tree/`. Each would simplify the code and speed it up, but none
is easy, so they wait until the typing is done.

- **Make an AVL node's `payload` required.** Nodes would get their payload when created,
  via `createNodeAtPosition(position, payload)`, and `ElementTree._insertCore` could skip a
  second lookup with `getNodeByPosition`, which is a real speedup. The hard part is
  `OffsetTree`: several elements (a chord's notes, say) can share an offset, so it appends to
  a list on a node that may already exist. `createNodeAtPosition` would have to return the
  node it created or found, and the plain position-only tree (`OffsetNode(40, None)`) still
  needs an empty state. Worth its own PR.
- **A shared base class for `ElementNode` and `OffsetNode`**, so their single payload versus
  list payload is clear in the types, probably along with a find-or-create method like
  `createNodeAtPositionIfNotExists` for the change above.
- **A second type parameter on `AVLTree` for its node type**, so `rootNode` and `nodeClass`
  agree: `class AVLTree[PayloadType, NodeType: AVLNode]`, with `nodeClass: type[NodeType]`
  and `rootNode: NodeType | None`. Tested and works: no casts needed on `rootNode`, and mypy
  catches a wrong `nodeClass`. Two catches: the bound has to be plain `AVLNode` (mypy won't
  let a bound use `PayloadType`), and `OffsetTree` switches the node class from
  `ElementNode` to `OffsetNode`, so carrying `NodeType` through that hierarchy takes care.
  Best done while typing `trees.py`, where it removes casts.
