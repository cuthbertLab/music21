# Strategy plan: consolidate on `tree.verticality.Verticality`

**Goal.** Make `tree.verticality.Verticality` the one Verticality concept in music21,
easy enough to teach early, and deprecate the older
`voiceLeading.Verticality` (and, in a later phase, the
`voiceLeading.VerticalityNTuplet` / `VerticalityTriplet` "tuple" classes).

**Status of this document.** Planning only — no code has been changed yet except where
noted as already-done elsewhere. Target release line: **v11** for new API and the start
of deprecations (current version `11.0.0b6`).

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
def verticalities(self, *, classList=None):
    '''A re-iterable, reversible view of this stream's Verticalities,
    one per vertical moment.'''
    tree = self.asTimespans(flatten=True, classList=classList)
    return _VerticalitiesView(tree)   # __iter__ -> forward, __reversed__ -> reverse

def getVerticalityAt(self, offset, *, classList=None):
    '''Return the Verticality sounding at the given offset.'''
    return self.asTimespans(flatten=True, classList=classList).getVerticalityAt(offset)
```

Decisions baked in:

- **Name: `Stream.verticalities()`** (preferred) rather than `iterateVerticalities()`.
  Friendlier and matches the "easy concept" goal. (The tree keeps its existing
  `iterateVerticalities()` name; `Stream.verticalities()` is the public friendly door. We
  can add `Stream.iterateVerticalities` as a hidden alias only if real demand appears.)
- **No `reverse=` kwarg — use `reversed()`.** Python's `reversed()` builtin dispatches to
  `__reversed__` (note the *d* — there is no `__reverse__` dunder). A bare generator can't
  be reversed (`TypeError: 'generator' object is not reversible`), so `verticalities()`
  returns a tiny lazy view object implementing `__iter__` (forward) and `__reversed__`
  (delegating to the tree's `iterateVerticalities(reverse=True)`). Then both
  `for v in score.verticalities()` and `for v in reversed(score.verticalities())` read
  idiomatically, and the view is re-iterable (a plain generator is single-shot). The tree
  keeps its `reverse=` kwarg internally.
- **`classList=None` default** — include keys/clefs/barlines, per principle 1. Anyone who
  wants strictly pitched slices passes `classList=(note.NotRest,)`.
- **Caching** — `asTimespans` caches on the stream, so repeat calls are free; the yielded
  Verticalities keep their tree backref, so `getAllVoiceLeadingQuartets()` etc. still work.
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

## Part E — `VerticalityNTuplet` / `VerticalityTriplet` (the "tuples") — Phase 2

Out of scope for the first pass; recorded so we don't forget. Structural replacement already
exists: `TimespanTree.iterateVerticalitiesNwise()` + `VerticalitySequence`. The two analysis
predicates `hasPassingTone()` / `hasNeighborTone()` have **no** equivalent yet and would need
porting (likely onto `VerticalitySequence` or a small free function) before these can be
deprecated. Separate plan.

The GitHub survey (Part H) found a real external user of exactly this layer
(`hasPassingTone` / `hasNeighborTone` via the old `theoryAnalyzer`), so when we do tackle
the tuples we should provide a genuine passing/neighbor-tone migration path, not just delete.

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

## Part H — real-world usage evidence (GitHub code search)

music21 is a dependency (often transitively) of thousands of repos, so removals must be
evidence-driven. Findings (`gh search code`, then filtering out vendored music21 source —
i.e. any `…/music21/voiceLeading.py`, doc-build, or fork path):

- **Duration-mutation methods** (`changeDurationOfAllObjects`, `makeAllSmallestDuration`,
  `makeAllLargestDuration`): **zero external callers.** Every hit is a vendored copy of
  music21's own source. A call-pattern search (`.changeDurationOfAllObjects`) plus path
  filtering returns 0 external. → effectively dead public API; safe to drop on the normal
  deprecation schedule with low risk.
- **`voiceLeading.Verticality` + the tuples + `hasPassingTone`/`hasNeighborTone`:** one real
  external user found — `avnerdorman/BachChorales63chords` (a notebook leaning on
  `voiceLeading.Verticality`, `VoiceLeadingQuartet`, `VerticalityNTuplet`/`Triplet`,
  `hasPassingTone`/`hasNeighborTone`) — **but entirely via the old `theoryAnalyzer`, which is
  already removed from current music21.** That user is therefore already pinned to an old
  version and does not constrain us; it does confirm a genuine audience for passing/neighbor
  analysis (see Part E).

Caveats: `gh search code` uses GitHub's legacy API — **no regex** (a `/…/` query returns
nothing), and it indexes only public default branches, so it under-counts (private repos,
Colab/Kaggle notebooks, course materials are invisible). "Zero external" is strong evidence,
not proof. It does index vendored `site-packages`, which is what makes the 0-external-callers
result credible.

---

## Part F — deprecation mechanics

- Use `@common.deprecated('v11', 'v13', '…use tree.verticality.Verticality…')` on
  `voiceLeading.Verticality.__init__` (and the dropped methods that someone might still call
  on an old instance), so construction emits a `Music21DeprecationWarning`.
- The class docstring already says "DEPRECATED in favor of tree.verticality.Verticality";
  tighten it to point at the concrete replacements above and remove the "not every feature
  replicated" hedge once B1/B2 land.
- Removal no earlier than **v13** (one release line of warning), per usual music21 policy.
  The Part H evidence supports the standard window — the duration methods could even go
  sooner, but there's no reason to rush them ahead of the rest of `vl.Verticality`.

### Why the new Verticality will never live in `voiceLeading.py`
Because the deprecated `voiceLeading.Verticality` has to keep its name and module for one or
two release lines while we steer people to `tree.verticality.Verticality`, the new class
**cannot** also live in `voiceLeading.py` — two classes named `Verticality` in one module is
a non-starter. So the canonical class stays in `tree/` (or, if we ever relocate it for
discoverability, into a standalone `music21/verticality.py` — never back into
`voiceLeading.py`).

---

## Execution checklist (suggested order)

**Phase 1 — additive, no behavior loss**
- [ ] `tree.Verticality.__iter__` (+ `__len__` / `__contains__`) and `isConsonant()`, with doctests.
- [ ] `Stream.verticalities()` (returning a re-iterable, `__reversed__`-able view) and
      `Stream.getVerticalityAt()` in `base.py`, with doctests. *(New in v11.)*
- [ ] Add zero-pitch `Chord` tests; decide `root()`-on-empty behavior (Part G).
- [ ] Rewrite the `findingParallels-noimage` notebook loop to `for v in score.verticalities():`.

**Phase 2 — the `includeRests` flip**
- [ ] Change the default in `getAllVoiceLeadingQuartets` + `getPairedMotion`; update the 2
      doctests and 2 notebooks listed in Part C.

**Phase 3 — deprecate `voiceLeading.Verticality`**
- [ ] Add `@common.deprecated(...)`; redirect docstring; confirm no remaining internal uses
      (currently none outside `voiceLeading.py`).

**Phase 4 — later**
- [ ] Plan + execute the `VerticalityNTuplet` / `VerticalityTriplet` deprecation (Part E).
- [ ] Remove deprecated members once the warning window elapses.

---

## Decisions

Decided:

- **Keep** the empty final-barline verticality (Michael). Follow-up captured in Part G
  (harden zero-pitch `Chord`).
- **No generic predicate-sweep helper** (Michael). The docs teach the loop instead.

Still needing Michael:

1. Confirm **`verticalities()`** as the Stream method name (vs `iterateVerticalities()`).
2. Confirm deprecate/remove versions (**v11 → v13** proposed).
3. Part G: should `root()` on an empty chord return `None` (like `bass()`) or keep raising?
