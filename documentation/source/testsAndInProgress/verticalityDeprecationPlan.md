# Strategy plan: consolidate on one Verticality concept (v11)

**Goal.** Make a single Verticality *the* concept in music21 — `tree.verticality.Verticality`
today, relocated to a top-level `music21.verticality.Verticality` — easy enough to teach
early, and deprecate the older `voiceLeading.Verticality` (and, later, the
`voiceLeading.VerticalityNTuplet` / `VerticalityTriplet` "tuple" classes).

**Status of this document.** Planning only — no code has been changed yet except where noted
as already-done elsewhere. Target release line: **v11** for new API and the start of
deprecations (current version `11.0.0b6`).

**How the phases run.** **Phase 1** is the planning/design (everything in this section).
**Phase 2** is the prerequisites that must land first — type the `tree` package (2A) and
investigate real-world usage (2B). **Phases 3+** are the implementation, in the execution
checklist near the end.

---

# Phase 1 — Planning

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
   style) and must pass `uv run mypy music21`. This is non-negotiable, and it is also why the
   `tree` package needs a typing pass *first* — see Phase 2A.

---

## Measure of success: theoryAnalyzer's ease is recreated, minus its baggage

A second goal of this work is to make the kinds of results the old
`theoryAnalysis.theoryAnalyzer` (now in `cuthbertLab/music21-tools`) used to make easy —
"find every parallel fifth / hidden octave / passing tone in this score" — easy again, but
**without the design baggage** that tied that tool to Bach-chorale homework.

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
| **passing tones / neighbor tones** | `VerticalityTriplet.hasPassingTone()` / `hasNeighborTone()` — **the one real gap** (Part E) |
| scale degrees, tonic/dominant, "common-practice errors" | out of scope — key/roman-numeral territory, and the most Bach-assuming pieces |

So for voice-leading errors the capability *already exists*; the score-wide sweep is the
~5-line loop in the `findingParallels-noimage` notebook (`for v in score.verticalities(): for vlq in
v.getAllVoiceLeadingQuartets(): …`). The job is to make that sweep ergonomic and teachable —
**not** to resurrect the wrapper.

**Baggage we will NOT carry over:**

- **`resultsDict` / `analysisData`** — results were stashed in
  `analyzer.store[score.id]['ResultDict'][dictKey]` keyed by string. Modern: functions
  *return* plain lists of findings.
- **`partNum1` / `partNum2` / `partNumToIdentify`** — index-based part addressing (and
  `'Part ' + str(pn+1)` text). Modern: Part identity via `getContextByClass`, all-pairs by
  default.
- **`color=` side effects** — `identifyX` mutated noteheads. Modern: return findings; the
  caller decides whether to color / `.show()` (and per an earlier decision, colouring is a
  *VLQ-element* operation, not a verticality one).
- **`VLQTheoryResult.text` English sentences** — a result whose payload is a prebuilt
  sentence. Modern: a finding carries the *objects* (the VLQ, offset, measure, parts); text
  is the caller's concern.
- **Bach-chorale / common-practice assumptions** — `identifyCommonPracticeErrors`,
  `identifyTonicAndDominant`, `opens/closesIncorrectly`, the SATB framing. Keep the neutral
  primitives; leave the stylistic bundles out.

Decided: **we do not add a generic predicate-sweep helper.** The docs teach the loop
(`for v in score.verticalities(): for vlq in v.getAllVoiceLeadingQuartets(): …`) — it's
already short and clear, and a wrapper would just be new surface to maintain and document.

---

## Why this is low-risk

`voiceLeading.Verticality`, `VerticalityNTuplet`, and `VerticalityTriplet` are referenced
**only inside `voiceLeading.py` itself** — there are no internal consumers anywhere else in
music21. `getChord()` appears in **no** documentation notebook. So the deprecation has
essentially no migration surface to clean up first.

---

## Part A — new top-level Stream API

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

`VerticalityView` (decided name) takes the **Stream itself**, not a tree — that hides the
tree from the caller. It builds the timespan tree **once, in `__init__`**, and stores it as a
plain public attribute, so the view is a stable snapshot: re-iterating gives the same result
even if the stream is edited afterward.

```python
class VerticalityView:
    def __init__(self, srcStream: stream.Stream, *, classList=None) -> None:
        self.stream = srcStream
        self.classList = classList
        self.tree: TimespanTree = srcStream.asTimespans(flatten=True, classList=classList)
    def __iter__(self) -> Iterator[Verticality]:
        return self.tree.iterateVerticalities()
    def __reversed__(self) -> Iterator[Verticality]:
        return self.tree.iterateVerticalities(reverse=True)
```

Snapshot semantics (decided): capture once in `__init__`, public `.tree`/`.stream`/
`.classList`. A held `v = score.verticalities()` should iterate the structure as it was when
asked for, and re-building the (expensive) tree on a second pass just because the stream
changed would be surprising. Caveat to document, not fix: this freezes *structure* (which
notes sound where) but the timespans still hold the **live Note objects**, so editing a
note's pitch is still visible.

Name — DECIDED: **`VerticalityView`** (not `Verticalities`). In music21 a `…Iterator`
(`StreamIterator`, `OffsetIterator`, `RecursiveIterator`, `corpus.chorales.Iterator`) is a
stateful object that does its *own* `__next__` over an internal cursor and is usually indexable
(`Sequence`, `__getitem__`/`__len__`, `reset()`). `VerticalityView` has none of that — no
`__next__`, no cursor, no indexing; it just hands back fresh generators off `self.tree`. So
`VerticalityIterator` would over-promise that contract, which is why `View` is the truthful
name. (Python's own views — `dict.keys()`, `memoryview` — are *live* rather than snapshots, so
the docstring should say "snapshot at construction." `VerticalityIterator` would only be honest
if we built the full `StreamIterator`-style object — `__next__` + `__getitem__` + `reset` — which
is more surface than a snapshot needs; the tree already gives random access by offset via
`getVerticalityAt`.)

Decisions baked in:

- **Name: `Stream.verticalities()`** (preferred) rather than `iterateVerticalities()`.
  Friendlier and matches the "easy concept" goal. (The tree keeps its existing
  `iterateVerticalities()` name; `Stream.verticalities()` is the public friendly door. We
  can add `Stream.iterateVerticalities` as a hidden alias only if real demand appears.)
- **The view takes a Stream, always `flatten=True`, with `classList`** (your call). `Part`
  is a Stream, so `part.verticalities()` gives a single part's slices for free. Anyone with a
  raw `TimespanTree` already has the tree's own `iterateVerticalities()`.
- **No `reverse=` kwarg — use `reversed()`.** Python's `reversed()` builtin dispatches to
  `__reversed__` (note the *d* — there is no `__reverse__` dunder). `VerticalityView`
  implements `__iter__` (forward) and `__reversed__` (delegating to the tree's
  `iterateVerticalities(reverse=True)`), so both `for v in score.verticalities()` and
  `for v in reversed(score.verticalities())` read idiomatically, and the view is re-iterable
  (a plain generator is single-shot). The tree keeps its `reverse=` kwarg internally.
- **`classList=None` default** — include keys/clefs/barlines, per principle 1. Anyone who
  wants strictly pitched slices passes `classList=(note.NotRest,)`.
- **Cost** — the view builds the tree once at construction and holds it, so re-iteration is
  free; `asTimespans` also caches on the stream. The yielded Verticalities keep their tree
  backref, so `getAllVoiceLeadingQuartets()` etc. still work.
- **Placement** — `base.py`, not StreamCore, because this is everyday/taught-early API
  (unlike `asTimespans`/`asTree`, which stay in core).

### The empty final-barline moment — DECIDED: keep it

With `classList=None`, the last "moment" is the final barline: an **empty** Verticality
(`pitchSet == set()`, `toChord()` returns an empty `Chord`, and `toChord().isConsonant()`
returns `False` — see B2). **Decision (Michael): keep it.** Faithful to "every vertical
moment," and suppressing would also hide a real mid-piece key/clef change that lands between
notes. The only worry is downstream `Chord` handling of zero pitches — see Part G.

---

## Part B — changes to `tree.verticality.Verticality`

### B1. Make it iterable (replaces `objects`)
Add `__iter__` (and probably `__len__` / `__contains__`) yielding the sounding elements,
so users write `for el in verticality:` instead of touching `startAndOverlapTimespans`:

```python
def __iter__(self):
    yield from (ts.element for ts in self.startAndOverlapTimespans)
```

This is the principle-2 win: it removes the single most common reason to reach into the
timespan layer.

### B2. Add `isConsonant()`
One-line convenience for now (`return self.toChord().isConsonant()`); a later optimization
could test consonance without materializing a chord.

Edge case: on an **empty** verticality (e.g. the final barline) `toChord()` is an empty
`Chord`, and `chord.Chord([]).isConsonant()` returns **`False`**. Arguably an empty moment is
"neither," but `False` is what falls out today. A future native implementation could
special-case empty → `False` (or `None`) explicitly; for the one-line version we accept the
inherited `False`.

### B3. Keep as-is
`toChord()`, `.offset`, `pitchSet`, `pitchClassSet`, `beatStrength`, `measureNumber`,
`nextVerticality` / `previousVerticality`, `nextStartOffset`, `timeToNextEvent`,
`bassTimespan`, `makeElement()`, `getAllVoiceLeadingQuartets()`, `getPairedMotion()`.

---

## Part C — `getAllVoiceLeadingQuartets` / `getPairedMotion`: flip `includeRests` default

**Change `includeRests=True` → `includeRests=False`** in both
`Verticality.getAllVoiceLeadingQuartets` and `Verticality.getPairedMotion`. A rest is not a
voice in motion; `True` was only ever harmless because the common idiom builds a note-only
tree. The `tree` package has always been perpetual-beta, so changing the default is allowed.

Doctests/notebooks to update (outputs change):

- `music21/tree/verticality.py:982` — `getAllVoiceLeadingQuartets()` example (drops the
  rest-bearing quartet).
- `music21/tree/verticality.py:1108` — `getPairedMotion()` example (the docstring already
  calls out a rest at 21.0–22.0).
- `documentation/source/usersGuide/usersGuide_61_trees.ipynb` — cells calling the bare
  methods.
- `documentation/source/testsAndInProgress/devTest_timespans.ipynb` — same.

---

## Part D — fate of every `voiceLeading.Verticality` member

| `voiceLeading.Verticality` member | Plan | Replacement / notes |
|---|---|---|
| `getChord()` | **Cut** | `toChord()`; unused in any doc |
| `isConsonant()` | **Port** (B2) | `toChord().isConsonant()` for now |
| `objects` (property) | **Replace** | iterate the Verticality (B1) |
| `getObjectsByClass(classes, partNums)` | **Drop** | iterate + filter by class in user code |
| `getObjectsByPart(partNum, …)` | **Drop** | `element.getContextByClass(Part)`; or `part.verticalities()` |
| `getVerticalityOffset(leftAlign=)` | **Drop** | `.offset` (left-aligned); `leftAlign=False` was unused |
| `getStream()` | **Drop** | buggy (`# probably wrong!`); use `chordify()` / `makeElement()` |
| `makeAllSmallestDuration()` | **Drop** | advanced timespans topic; `makeElement(ql)` for a non-destructive chord |
| `makeAllLargestDuration()` | **Drop** | same |
| `getShortestDuration()` / `getLongestDuration()` | **Drop** | one-liners; `timeToNextEvent` for the usual need |
| `changeDurationOfAllObjects(ql)` | **Drop** | advanced timespans topic (see below) |
| `color` (property) | **Drop** | we'd color the elements of a *VLQ*, not a whole verticality |
| `lyric` (property) | **Drop** | demonstrate manually later |

### Duration-mutation note
The five duration methods all predate `chordify()` doing duration correctly. None belongs on
Verticality. **Document "changing the durations of the elements at a vertical moment" as an
advanced topic in a later TimeSpans section of the User's Guide**, rather than as API. The
modern non-destructive equivalent is `verticality.makeElement(quarterLength)`.

---

## Part E — `VerticalitySequence` replaces the `Tuplet` classes (plan now, build late)

`VerticalityNTuplet` / `VerticalityTriplet` are a sliding window of N consecutive
verticalities plus two analysis predicates (`hasPassingTone` / `hasNeighborTone`). We plan
their replacement **now**, alongside the main work, even though the build is a late phase.

**Structural half — already done.** `TimespanTree.iterateVerticalitiesNwise(n)` yields
`VerticalitySequence` objects (a thin wrapper over N verticalities, with `__len__` /
`__getitem__` / `unwrap`). That *is* the modern `VerticalityNTuplet`. So we also add
`Stream.verticalitiesNwise(n=3)` (sugar over the cached tree, mirroring `Stream.verticalities()`)
so users never touch the tree.

**Analytical half — the real port.** Move passing/neighbor-tone detection onto
`VerticalitySequence` (a 3-element sequence) as `hasPassingTone()` / `hasNeighborTone()`,
**shedding the same baggage as Part D**:

- no `partNumToIdentify` — work per *part identity*, or return, for each voice that has one, a
  finding object carrying the offending note + its part;
- no in-place coloring;
- keep `unaccentedOnly` as a real, useful option.

`VerticalitySequence` (or a small free function `verticality.nonChordTones(seq)`) becomes the
one home. Then `VerticalityNTuplet` / `VerticalityTriplet` get `@common.deprecated` pointing
there.

**Why now:** Phase 2B found a real external user of exactly this layer (`hasPassingTone` /
`hasNeighborTone` via the old `theoryAnalyzer`), so the replacement must be a genuine
migration path, not a delete. Planning it here keeps the `VerticalitySequence` API decisions
consistent with the `Verticality` / `VerticalityView` ones (return findings, identify parts by
element, fully typed). Build lands in the late phase (after relocation), but the design is
settled alongside everything else.

---

## Part F — deprecation mechanics

Two different situations, two different policies:

- **`voiceLeading.Verticality`** (and its tuples) — a long-documented public class with real
  history. Use `@common.deprecated('v11', 'v13', '…use music21.verticality.Verticality…')` on
  its `__init__` (and the dropped methods someone might still call on an old instance), so
  construction emits a `Music21DeprecationWarning`. Removal no earlier than **v13** (one
  release line of warning). Tighten its docstring to point at the concrete replacements.
- **The `tree.verticality.*` path** — advanced and barely documented; the `tree` package has
  always been perpetual-beta. So relocating `Verticality` to `music21.verticality` gets **no
  deprecation window** by default: we just move it and update the ~4 internal references. The
  *only* thing that changes this is **Phase 2B** reporting external code that imports
  `tree.verticality.*` directly — then, and only then, we leave a short-lived back-compat shim.

### At most two `Verticality` names at once (not three)
Because the `tree` path carries no deprecation window, there's never a third live name. While
`voiceLeading.Verticality` is deprecated (v11→v13), the canonical class moves straight to
`music21.verticality.Verticality`. That is also why the canonical class **cannot** live in
`voiceLeading.py`: the deprecated `voiceLeading.Verticality` keeps that name and module during
its window, and two classes named `Verticality` can't share one file.

---

## Part G — harden zero-pitch (empty) `Chord` behavior

Because we keep the empty final-barline moment, and because emphasizing verticalities will
surface empty chords far more often than today, we should make sure `chord.Chord([])` behaves
sanely and is covered by tests. Current state (probed):

- **Cope fine** → `isConsonant()` → `False`, `bass()` → `None`, `third`/`fifth` → `None`,
  `quality` → `'other'`, `isTriad()` → `False`, `commonName`/`pitchedCommonName` →
  `'empty chord'`, `orderedPitchClasses` → `[]`, `intervalVector` → all-zero,
  `closedPosition()` → empty chord.
- **Raises** → `root()` raises `ChordException('no pitches in chord')` — **inconsistent with
  `bass()` returning `None`.**

Action: decide whether `root()` on an empty chord should return `None` (consistent with
`bass()`) or keep raising; either way, add explicit tests for zero-pitch chords across the
common accessors so the verticality emphasis doesn't expose surprises. (Note `isConsonant()`
on empty returning `False` from B2 is part of this same surface.)

---

## Part H — relocate Verticality to a top-level `music21.verticality` module

Move `Verticality` (and `VerticalityView`, `VerticalitySequence`) out of `tree/` into a
top-level `music21/verticality.py`, so most users meet "a vertical slice of music" without
ever entering tree-land. **Gated on Phase 2** (the `tree` typing pass 2A and the usage survey
2B) and on the additive work above.

Why it's more feasible than it first looks — the actual coupling is mild (verified):

- `tree/spans.py` mentions `Verticality` **only in docstrings**; it imports nothing from
  `tree` at all (just `copy`, `typing`, `common.types`, `environment`, `exceptions21`). So
  `spans` is a leaf, and `verticality → tree.spans` (the one real module-level dependency) is
  a safe one-way edge.
- The only genuine circular reference is `tree/trees.py` ↔ verticality (`getVerticalityAt`
  returns a `Verticality`), and **that cycle already exists today, in one place** — relocating
  doesn't add a new one.

So the move is a file relocation plus updating ~4 internal references, **not** an import
untangling. Mechanics:

- **Default: no shim — we don't expect to need one.** The `tree.verticality.*` path is
  advanced/undocumented, so the plan is to just move the module and update internal references.
  *Only if* Phase 2B turns up external code importing `tree.verticality.*` directly do we add a
  thin, short-lived `tree/verticality.py` shim (`from music21.verticality import *`).
- Lazy-import where load order bites (the file already lazy-imports `timespanTree`, `stream`,
  `voiceLeading`, `tree.analysis`).
- Add `music21/verticality.py` to the module list / docs reference pages.

Honest caveat (unchanged): this hides the tree from the user's *vocabulary*, not from the
code — a `Verticality` still structurally holds `tree.spans` timespans. That's fine; the win
is conceptual discoverability and pairing with `voiceLeading`, plus sidestepping the
`voiceLeading.py` name clash.

---

## Part I — Verticality / finding-parallels User's Guide chapter (late)

Promote the in-progress `findingParallels-noimage` notebook into a real User's Guide chapter
that teaches Verticalities and the voice-leading loop in the house tone, and **integrate the
`theoryExercises/Rouen` example** (dense with parallels — fun to hunt) alongside the subtle
single Bach case. This is deliberately **late** — it should sit on top of the finished
`Stream.verticalities()` API and the relocated `music21.verticality`, not race ahead of them.
Until then the notebook stays as an in-progress tutorial.

---

# Phase 2 — Prerequisites (land before any implementation)

## 2A — type and clean up the `tree` package

Before *any* implementation, the `tree` package gets its own self-contained subproject: add
full type annotations, fix docstring grammar/wording, and tidy the code. Rationale:

- Everything we add (`VerticalityView`, `Stream.verticalities()`, the `tree.Verticality`
  additions) must be fully typed (principle 5), and it is far easier to type new code against
  a `tree` whose own signatures are already typed than to fight an untyped substrate.
- The eventual relocation of `Verticality` out of `tree` (Part H) is only sane once the module
  it leaves behind — and the `spans`/`trees`/`timespanTree` it still depends on — are clean
  and typed.

A normal, low-drama PR (or a few), separate from the verticality consolidation, and a natural
on-ramp. **No Verticality moves until it lands.**

## 2B — investigate real-world usage on GitHub

music21 is a dependency (often transitively) of thousands of repos, so removals and moves must
be evidence-driven. This survey **decides whether the `tree.verticality.*` relocation needs any
back-compat shim** (Parts F/H) and confirms the `voiceLeading.Verticality` removal is safe.

Findings so far (`gh search code`, then filtering out vendored music21 source — i.e. any
`…/music21/voiceLeading.py`, doc-build, or fork path):

- **Duration-mutation methods** (`changeDurationOfAllObjects`, `makeAllSmallestDuration`,
  `makeAllLargestDuration`): **zero external callers.** Every hit is a vendored copy of
  music21's own source. A call-pattern search (`.changeDurationOfAllObjects`) plus path
  filtering returns 0 external. → effectively dead public API; safe to drop.
- **`voiceLeading.Verticality` + the tuples + `hasPassingTone`/`hasNeighborTone`:** one real
  external user found — `avnerdorman/BachChorales63chords` (a notebook leaning on
  `voiceLeading.Verticality`, `VoiceLeadingQuartet`, `VerticalityNTuplet`/`Triplet`,
  `hasPassingTone`/`hasNeighborTone`) — **but entirely via the old `theoryAnalyzer`, which is
  already removed from current music21.** That user is therefore already pinned to an old
  version and does not constrain us; it does confirm a genuine audience for passing/neighbor
  analysis (see Part E).
- **Still to run (the decisive search):** external importers of `tree.verticality` —
  `from music21.tree.verticality import`, `tree.verticality.Verticality`,
  `.iterateVerticalities`, `.getVerticalityAt`. If that comes back empty, Part H relocates with
  **no shim**; if not, we add a short-lived shim for those names.

Caveats: `gh search code` uses GitHub's legacy API — **no regex** (a `/…/` query returns
nothing), and it indexes only public default branches, so it under-counts (private repos,
Colab/Kaggle notebooks, course materials are invisible). "Zero external" is strong evidence,
not proof. It does index vendored `site-packages`, which is what makes the 0-external-callers
result credible.

---

## Execution checklist (suggested order)

**Phase 3 — additive, no behavior loss** (all fully typed; needs Phase 2A)
- [ ] `tree.Verticality.__iter__` (+ `__len__` / `__contains__`) and `isConsonant()`, with doctests.
- [ ] `VerticalityView` (takes a Stream) + `Stream.verticalities()` and
      `Stream.getVerticalityAt()` in `base.py`, with doctests. *(New in v11.)*
- [ ] `Stream.verticalitiesNwise(n=3)` sugar over the cached tree (mirrors `verticalities()`).
- [ ] Add zero-pitch `Chord` tests; decide `root()`-on-empty behavior (Part G).
- [ ] Rewrite the `findingParallels-noimage` notebook loop to `for v in score.verticalities():`.

**Phase 4 — the `includeRests` flip**
- [ ] Change the default in `getAllVoiceLeadingQuartets` + `getPairedMotion`; update the 2
      doctests and 2 notebooks listed in Part C.

**Phase 5 — deprecate `voiceLeading.Verticality`**
- [ ] Add `@common.deprecated(...)`; redirect docstring; confirm no remaining internal uses
      (currently none outside `voiceLeading.py`).

**Phase 6 — relocate Verticality to `music21.verticality`** (Part H; needs Phase 2)
- [ ] Move the class + `VerticalityView` + `VerticalitySequence`; update internal references
      and docs. Add a `tree/verticality.py` shim *only if* 2B found external importers.

**Phase 7 — finish integrating the `Rouen` corpus example** (independent; can land early)
- [ ] Regenerate `music21/corpus/_metadataCache/core.p.gz` so `theoryExercises/Rouen` is
      indexed (and `corpus.search('Rouen')` works); bump any corpus-count assertion that needs
      it (the floors in `corpus/testCorpus.py`, the range doctest at `corpora.py:615` — verify,
      likely already in range); commit the regenerated `core.p.gz`.

**Phase 8 — late: User's Guide chapter**
- [ ] Promote `findingParallels-noimage` into a User's Guide chapter + integrate
      `theoryExercises/Rouen` (Part I) — on top of the finished API, not before.

**Phase 9 — late: the tuples → `VerticalitySequence`**
- [ ] Port `hasPassingTone` / `hasNeighborTone` onto `VerticalitySequence` (Part E), shedding
      `partNum`/coloring; then `@common.deprecated` the `VerticalityNTuplet` / `VerticalityTriplet`
      classes pointing there.
- [ ] Remove deprecated members once the warning window elapses.

---

## Decisions

Decided:

- **Keep** the empty final-barline verticality (Michael). Follow-up captured in Part G
  (harden zero-pitch `Chord`).
- **No generic predicate-sweep helper** (Michael). The docs teach the loop instead.
- **`VerticalityView`** is the view class name; it takes a Stream, always `flatten=True`,
  with `classList`; snapshot at construction.
- **Everything ships fully typed** (principle 5).
- **Phase 2 prerequisites first**: 2A type + clean up the `tree` package, 2B survey GitHub
  usage. The Verticality relocation (Part H) comes after.
- **No deprecation window for the `tree.verticality.*` path** (advanced/undocumented) — just
  move it, no shim expected — *unless* Phase 2B finds external code importing it directly.
  `voiceLeading.Verticality` still gets the normal v11→v13 window.
- **`VerticalitySequence` is the planned replacement for the tuples** (Part E) — designed now
  (shed `partNum`/coloring; add `Stream.verticalitiesNwise`), built in the late phase.
- **Rouen corpus integration is its own task** (Phase 7): regenerate + commit `core.p.gz`,
  fix any corpus-count assertion.

Still needing Michael:

1. Confirm `voiceLeading.Verticality` deprecate/remove versions (**v11 → v13** proposed).
2. Part G: should `root()` on an empty chord return `None` (like `bass()`) or keep raising?
