# Verticality consolidation plan (v11)

**Goal.** Make a single Verticality *the* concept in music21 — `tree.verticality.Verticality`
today, relocated to a top-level `music21.verticality.Verticality` — easy enough to teach
early, and deprecate the older `voiceLeading.Verticality` (and, later, the
`voiceLeading.VerticalityNTuplet` / `VerticalityTriplet` "tuple" classes).

**Status.** Planning only — no implementation code changed yet. Target release line: **v11**
(current version `11.0.0b6`).

**How it runs.** One PR at a time, via supervised subagents (no heavy workflow orchestration).
Each PR is its own branch+worktree off `master`. **Prerequisites land first**, then the core
implementation, then the late polish — see the Execution plan at the end. The lettered
*Design notes* are reference (the *what*); the Execution plan is the *when*.

---

## Decisions

Settled:

- **Keep** the empty final-barline verticality. Follow-up: harden zero-pitch `Chord` (Design G).
- **No generic predicate-sweep helper.** The docs teach the loop.
- **`VerticalityView`** is the view-class name: snapshot at construction, takes a Stream
  (always `flatten=True`, with `classList`), plus an advanced keyword-only `tree=` override.
- **Everything ships fully typed** (principle 5).
- **Prerequisites first**, each its own small PR: notebook image-stripping infra, the `tree`
  typing/grammar pass, and the GitHub usage survey.
- **No deprecation window or shim for the `tree.verticality.*` path** (advanced/undocumented) —
  just move it — *unless* the usage survey finds external importers.
  `voiceLeading.Verticality` still gets the normal **v11 → v13** window.
- **`VerticalitySequence` replaces the tuples** (Design E) — designed now, built late.
- **Rouen corpus integration is its own task** (regenerate + commit `core.p.gz`).
- **Subagents, one PR at a time** (no Workflow orchestration).

Open (need Michael):

1. Confirm `voiceLeading.Verticality` deprecate/remove versions (**v11 → v13** proposed).
2. Design G: should `root()` on an empty chord return `None` (like `bass()`) or keep raising?

---

## Guiding principles

1. **A Verticality is an easy concept: "everything happening at one vertical moment."**
   That deliberately *includes* non-note objects (keys, clefs, time signatures, barlines)
   that occur at that offset — they genuinely happen there. Pitched-analysis methods
   (`toChord`, `pitchSet`, `getAllVoiceLeadingQuartets`, …) already filter to pitched
   timespans, so carrying the extra objects along is harmless to analysis.
2. **Hide timespans.** `startTimespans` / `overlapTimespans` / `startAndOverlapTimespans`
   and the whole timespan layer are an implementation detail. A learner should be able to
   use Verticalities — iterate them, get a chord, find voice-leading quartets — without
   ever hearing the words "timespan" or "tree." Timespans become an *advanced* topic.
3. **Identify parts from elements, not by index.** No `partNum`-by-position APIs. To get
   an element's part, use `element.getContextByClass(stream.Part)`. To get the
   verticalities of a single part, call `.verticalities()` on that Part.
4. **Don't mutate the score through a Verticality.** Changing the durations of underlying
   elements is an advanced timespans-era operation, documented later — not a Verticality
   method.
5. **Everything ships fully typed.** Every new method, the `VerticalityView`, and every
   `tree.Verticality` addition carries complete type annotations (PEP 695 syntax per repo
   style) and must pass `uv run mypy music21`.

---

## Measure of success: theoryAnalyzer's ease is recreated, minus its baggage

A second goal is to make the kinds of results the old `theoryAnalysis.theoryAnalyzer` (now in
`cuthbertLab/music21-tools`) used to make easy — "find every parallel fifth / hidden octave /
passing tone in this score" — easy again, but **without the baggage** that tied that tool to
Bach-chorale homework.

The key realization: `theoryAnalyzer` was, underneath, a single pattern — *run a
`VoiceLeadingQuartet` (or Verticality / triplet) predicate across the whole score and collect
the hits.* Every `identifyX` was just `testFunction = lambda vlq: vlq.X()` plus a text
sentence. And **almost all those predicates already live on `VoiceLeadingQuartet` today**:

| `theoryAnalyzer` capability | Modern home |
|---|---|
| parallel 5ths / 8ves / unisons | `VoiceLeadingQuartet.parallelFifth()` / `parallelOctave()` / `parallelUnison()` ✅ |
| hidden (direct) 5ths / 8ves | `hiddenFifth()` / `hiddenOctave()` ✅ |
| oblique/similar/parallel/contrary/anti-parallel motion, motion type | `obliqueMotion()` … `antiParallelMotion()`, `motionType()` ✅ |
| improper resolution, leap-not-set-with-step, modal open/close, clausula vera | `isProperResolution()`, `leapNotSetWithStep()`, `modalOpening()`, `opensIncorrectly()`, `clausulaVera()`, `closesIncorrectly()` ✅ |
| harmonic / melodic intervals between parts | trivial over verticalities / part pairs ✅ |
| **passing tones / neighbor tones** | `VerticalityTriplet.hasPassingTone()` / `hasNeighborTone()` — **the one real gap** (Design E) |
| scale degrees, tonic/dominant, "common-practice errors" | out of scope — key/roman-numeral territory, and the most Bach-assuming pieces |

So for voice-leading errors the capability *already exists*; the score-wide sweep is the
~5-line loop in the `findingParallels-noimage` notebook. The job is to make that sweep
ergonomic and teachable — **not** to resurrect the wrapper.

**Baggage we will NOT carry over:**

- **`resultsDict` / `analysisData`** — results were stashed in
  `analyzer.store[score.id]['ResultDict'][dictKey]` keyed by string. Modern: functions
  *return* plain lists of findings.
- **`partNum1` / `partNum2` / `partNumToIdentify`** — index-based part addressing (and
  `'Part ' + str(pn+1)` text). Modern: Part identity via `getContextByClass`, all-pairs by
  default.
- **`color=` side effects** — `identifyX` mutated noteheads. Modern: return findings; the
  caller decides whether to color / `.show()` (and colouring is a *VLQ-element* operation, not
  a verticality one).
- **`VLQTheoryResult.text` English sentences** — a result whose payload is a prebuilt
  sentence. Modern: a finding carries the *objects* (the VLQ, offset, measure, parts); text
  is the caller's concern.
- **Bach-chorale / common-practice assumptions** — `identifyCommonPracticeErrors`,
  `identifyTonicAndDominant`, `opens/closesIncorrectly`, the SATB framing. Keep the neutral
  primitives; leave the stylistic bundles out.

---

## Why this is low-risk

`voiceLeading.Verticality`, `VerticalityNTuplet`, and `VerticalityTriplet` are referenced
**only inside `voiceLeading.py` itself** — no internal consumers anywhere else in music21.
`getChord()` appears in **no** documentation notebook. So the deprecation has essentially no
migration surface to clean up first.

---

## Design notes

The *what*. Lettered for cross-reference, **not** for ordering — see the Execution plan for
sequence.

### A. New Stream API

Add to `stream.Stream`, in `stream/base.py` (the documented, taught-early API), each
delegating into the already-cached `StreamCore.asTimespans()`:

```python
def verticalities(self, *, classList=None) -> VerticalityView:
    '''A re-iterable, reversible view of this stream's Verticalities,
    one per vertical moment.'''
    return VerticalityView(self, classList=classList)

def getVerticalityAt(self, offset: OffsetQLIn, *, classList=None) -> Verticality:
    '''Return the Verticality sounding at the given offset.'''
    return self.asTimespans(flatten=True, classList=classList).getVerticalityAt(offset)
```

`VerticalityView` takes the **Stream itself**, builds the timespan tree **once in `__init__`**,
and stores it as a plain public attribute, so the view is a stable snapshot. Advanced callers
may pass a prebuilt `tree=` (keyword-only) to view a `TimespanTree` they already hold; if
omitted it builds from the stream exactly as below:

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

Snapshot semantics (decided): a held `v = score.verticalities()` iterates the structure as it
was when asked for; re-building the (expensive) tree on a second pass just because the stream
changed would be surprising. Caveat to document, not fix: this freezes *structure* (which notes
sound where) but the timespans still hold the **live Note objects**, so editing a note's pitch
is still visible.

Name — DECIDED: **`VerticalityView`** (not `Verticalities`, not `VerticalityIterator`). In
music21 a `…Iterator` (`StreamIterator`, `OffsetIterator`, `RecursiveIterator`,
`corpus.chorales.Iterator`) does its *own* `__next__` over an internal cursor and is usually an
indexable `Sequence`. `VerticalityView` has none of that — no `__next__`, no cursor, no
indexing; it just hands back fresh generators off `self.tree`. So `Iterator` would over-promise.
(Python's own views — `dict.keys()`, `memoryview` — are *live*, so the docstring should say
"snapshot at construction.")

Other decisions baked in:

- **Name `Stream.verticalities()`** (not `iterateVerticalities()`); the tree keeps its
  `iterateVerticalities()`. A hidden `Stream.iterateVerticalities` alias only if demand appears.
- **Takes a Stream, always `flatten=True`, with `classList`.** `Part` is a Stream, so
  `part.verticalities()` gives a single part's slices for free.
- **No `reverse=` kwarg — use `reversed()`** (dispatches to `__reversed__`; a bare generator
  isn't reversible, the view is).
- **`classList=None` default** — include keys/clefs/barlines (principle 1). Pitched-only:
  `classList=(note.NotRest,)`.
- **Placement** — `base.py`, not StreamCore (everyday/taught-early API).

The empty final-barline moment — DECIDED: **keep it.** With `classList=None` the last moment is
the final barline: an **empty** Verticality (`pitchSet == set()`, `toChord()` an empty `Chord`,
`isConsonant()` → `False` — Design G). Faithful to "every vertical moment," and suppressing
would also hide a real mid-piece key/clef change that lands between notes.

### B. `tree.verticality.Verticality` changes

- **B1 — make it iterable** (replaces `objects`): `__iter__` (and probably `__len__` /
  `__contains__`) yielding the sounding elements, so users write `for el in verticality:`
  instead of touching `startAndOverlapTimespans`. The single biggest reason to reach into the
  timespan layer, gone.
- **B2 — add `isConsonant()`**: one-line `return self.toChord().isConsonant()` for now (a
  later optimization could skip materializing a chord). On an empty verticality this returns
  `False` (see Design G).
- **B3 — keep as-is**: `toChord()`, `.offset`, `pitchSet`, `pitchClassSet`, `beatStrength`,
  `measureNumber`, `nextVerticality`/`previousVerticality`, `nextStartOffset`,
  `timeToNextEvent`, `bassTimespan`, `makeElement()`, `getAllVoiceLeadingQuartets()`,
  `getPairedMotion()`.

### C. `getAllVoiceLeadingQuartets` / `getPairedMotion`: flip `includeRests` default

**`includeRests=True` → `includeRests=False`** in both. A rest is not a voice in motion; `True`
was only ever harmless because the common idiom builds a note-only tree. The `tree` package has
always been perpetual-beta, so the default change is allowed. Doctests/notebooks whose output
changes: `tree/verticality.py:982` and `:1108`; `usersGuide_61_trees.ipynb`;
`devTest_timespans.ipynb`.

### D. Fate of every `voiceLeading.Verticality` member

| member | Plan | Replacement / notes |
|---|---|---|
| `getChord()` | **Cut** | `toChord()`; unused in any doc |
| `isConsonant()` | **Port** (B2) | `toChord().isConsonant()` for now |
| `objects` (property) | **Replace** | iterate the Verticality (B1) |
| `getObjectsByClass(classes, partNums)` | **Drop** | iterate + filter by class |
| `getObjectsByPart(partNum, …)` | **Drop** | `element.getContextByClass(Part)`; or `part.verticalities()` |
| `getVerticalityOffset(leftAlign=)` | **Drop** | `.offset`; `leftAlign=False` was unused |
| `getStream()` | **Drop** | buggy (`# probably wrong!`); use `chordify()` / `makeElement()` |
| `makeAllSmallestDuration()` / `makeAllLargestDuration()` | **Drop** | advanced timespans topic; `makeElement(ql)` |
| `getShortestDuration()` / `getLongestDuration()` | **Drop** | one-liners; `timeToNextEvent` |
| `changeDurationOfAllObjects(ql)` | **Drop** | advanced timespans topic |
| `color` / `lyric` (properties) | **Drop** | color/lyric the elements of a VLQ, not a verticality |

The five duration methods predate `chordify()` doing duration correctly; none belongs on
Verticality. Document "changing the durations of the elements at a vertical moment" as an
*advanced* TimeSpans topic later; the non-destructive equivalent is
`verticality.makeElement(quarterLength)`.

### E. `VerticalitySequence` replaces the `Tuplet` classes

`VerticalityNTuplet` / `VerticalityTriplet` are a sliding window of N verticalities plus
`hasPassingTone` / `hasNeighborTone`. Plan their replacement **now** (build late):

- **Structural half — already done.** `TimespanTree.iterateVerticalitiesNwise(n)` yields
  `VerticalitySequence` objects (thin wrapper over N verticalities, with `__len__` /
  `__getitem__` / `unwrap`) — that *is* the modern `VerticalityNTuplet`. Add
  `Stream.verticalitiesNwise(n=3)` sugar so users never touch the tree.
- **Analytical half — the real port.** Move passing/neighbor-tone detection onto
  `VerticalitySequence` (a 3-element sequence) as `hasPassingTone()` / `hasNeighborTone()`,
  shedding the same baggage as Design D: no `partNumToIdentify` (work per part identity / return
  findings), no coloring, keep `unaccentedOnly`. Then `@common.deprecated` the tuple classes
  pointing here.

The survey (Execution Pre-3) found a real external user of exactly this layer via the removed
`theoryAnalyzer`, so this must be a genuine migration path, not a delete. Planning it now keeps
the `VerticalitySequence` API consistent with the `Verticality` / `VerticalityView` decisions.

### F. Deprecation mechanics

Two situations, two policies:

- **`voiceLeading.Verticality`** (and its tuples) — long-documented public class. Use
  `@common.deprecated('v11', 'v13', '…use music21.verticality.Verticality…')` on `__init__`
  (and the dropped methods someone might still call on an old instance). Removal no earlier than
  **v13**. Tighten its docstring to point at the concrete replacements.
- **The `tree.verticality.*` path** — advanced, barely documented, perpetual-beta. Relocating
  to `music21.verticality` gets **no deprecation window** by default: move it, update the ~4
  internal references. *Only if* the usage survey (Pre-3) finds external `tree.verticality.*`
  importers do we add a short-lived shim.

**At most two `Verticality` names at once (not three):** because the `tree` path carries no
window, while `voiceLeading.Verticality` is deprecated (v11→v13) the canonical class moves
straight to `music21.verticality.Verticality`. That is also why the canonical class **cannot**
live in `voiceLeading.py` — the deprecated `voiceLeading.Verticality` keeps that name during its
window, and two classes named `Verticality` can't share one file.

### G. Harden zero-pitch (empty) `Chord` behavior

Keeping the empty final-barline moment means verticalities will surface empty chords far more
often than today. Current state (probed):

- **Cope fine** → `isConsonant()` → `False`, `bass()` → `None`, `third`/`fifth` → `None`,
  `quality` → `'other'`, `isTriad()` → `False`, `commonName`/`pitchedCommonName` →
  `'empty chord'`, `orderedPitchClasses` → `[]`, `intervalVector` → all-zero,
  `closedPosition()` → empty chord.
- **Raises** → `root()` raises `ChordException('no pitches in chord')` — inconsistent with
  `bass()` returning `None`.

Actions:

- Decide `root()`-on-empty: return `None` (consistent with `bass()`) or keep raising.
- Add explicit zero-pitch-`Chord` tests across the common accessors.
- **Document, very briefly, at the end of the *ambiguous* methods** what a zero-pitch chord
  returns — where the answer isn't self-evident: `isConsonant()` (→ `False`) and whatever we
  decide for `root()`. **Not** the obvious ones (`isTriad()` is obviously `False` for an empty
  chord — no note needed). One line each, only where a reader would wonder.

### H. Relocate Verticality to a top-level `music21.verticality` module

Move `Verticality` (and `VerticalityView`, `VerticalitySequence`) out of `tree/` into
`music21/verticality.py`, so most users meet "a vertical slice of music" without entering
tree-land. The coupling is mild (verified):

- `tree/spans.py` mentions `Verticality` **only in docstrings**; it imports nothing from `tree`
  (just `copy`, `typing`, `common.types`, `environment`, `exceptions21`), so it's a leaf and
  `verticality → tree.spans` is a safe one-way edge.
- The only genuine cycle is `tree/trees.py` ↔ verticality (`getVerticalityAt` returns a
  `Verticality`), and **that already exists today, in one place** — relocating adds none.

So it's a file relocation plus ~4 internal-reference updates, not an import untangle:

- **Default: no shim — we don't expect to need one.** Only if Pre-3 turns up external
  `tree.verticality.*` importers do we leave a thin `tree/verticality.py`
  (`from music21.verticality import *`) for a release line.
- Lazy-import where load order bites (the file already lazy-imports `timespanTree`, `stream`,
  `voiceLeading`, `tree.analysis`).
- Add `music21/verticality.py` to the module list / docs reference pages.

Honest caveat: this hides the tree from the user's *vocabulary*, not from the code — a
`Verticality` still structurally holds `tree.spans` timespans. The win is discoverability and
pairing with `voiceLeading`, plus sidestepping the `voiceLeading.py` name clash.

### I. Verticality / finding-parallels User's Guide chapter (late)

Promote the in-progress `findingParallels-noimage` notebook into a real User's Guide chapter in
the house tone, and **integrate the `theoryExercises/Rouen` example** (dense with parallels —
fun to hunt) alongside the subtle single Bach case. Deliberately late — on top of the finished
API and the relocated `music21.verticality`, not racing ahead.

---

## Execution plan (one PR at a time, via supervised subagents)

### Prerequisites — land first, each its own small PR off `master`

- **Pre-1 — Notebook image-stripping infra.** Extract the `stripNotebookImages.py` clean filter,
  the `testsAndInProgress/.gitattributes`, the `documenting.rst` sentence, and the AGENTS.md note
  into their own PR off `master`. Standalone, generally useful, needed before the notebook work.
- **Pre-2 — Type & clean up the `tree` package.** Several small PRs: start with a
  grammar/punctuation-only pass over `music21/tree/` (zero logic), then type module by module
  (`spans` leaf first). Green under `ruff` / `mypy` / `pylint`; doctests unchanged.
- **Pre-3 — GitHub usage survey.** Decide whether the relocation needs a shim and confirm the
  `voiceLeading.Verticality` removal is safe. Findings so far: zero external callers of the
  duration methods; one external user of the tuples but only via the removed `theoryAnalyzer`.
  Still to run (the decisive one): external importers of `tree.verticality` /
  `from music21.tree.verticality import` / `.iterateVerticalities` / `.getVerticalityAt`. Empty
  → relocate with no shim. (Caveats: `gh search code` has no regex and under-counts private
  repos / notebooks; "zero" is strong evidence, not proof.)

### Core implementation — one PR at a time

- **1 — Additive API** (Design A, B, G): `VerticalityView` + `Stream.verticalities()` /
  `getVerticalityAt()` / `verticalitiesNwise(n=3)`; `tree.Verticality.__iter__` (+ `__len__` /
  `__contains__`) + `isConsonant()`; zero-pitch `Chord` tests + the brief doc notes; decide
  `root()`-on-empty. Fully typed, with doctests. *(New in v11.)* Then rewrite the
  `findingParallels-noimage` loop to `for v in score.verticalities():`.
- **2 — `includeRests` flip** (Design C): change the default; update the 2 doctests + 2 notebooks.
- **3 — Deprecate `voiceLeading.Verticality`** (Design D, F): `@common.deprecated`, redirect
  docstring, cut/replace members per the fate table.
- **4 — Relocate Verticality to `music21.verticality`** (Design H; needs Pre-2 & Pre-3): move the
  class + `VerticalityView` + `VerticalitySequence`, update references and docs; shim only if
  Pre-3 found importers.

### Late

- **5 — Finish Rouen corpus integration:** regenerate `music21/corpus/_metadataCache/core.p.gz`
  so `theoryExercises/Rouen` is indexed (and `corpus.search('Rouen')` works); fix any
  corpus-count assertion (the floors in `corpus/testCorpus.py`, the range doctest at
  `corpora.py:615` — verify, likely already in range); commit the regenerated `core.p.gz`.
- **6 — User's Guide chapter** (Design I): promote `findingParallels-noimage` + integrate Rouen.
- **7 — Tuples → `VerticalitySequence`** (Design E): port `hasPassingTone` / `hasNeighborTone`
  (shedding `partNum`/coloring), then deprecate the tuple classes pointing there; remove after
  the window.
