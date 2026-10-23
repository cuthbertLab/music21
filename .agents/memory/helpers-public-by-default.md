---
name: helpers-public-by-default
description: Reusable music-theory helpers go public with docs and examples; but a one-caller helper that would cost runtime gets inlined
metadata:
  type: feedback
---

When a new helper computes something a user could reuse, make it a public, documented
function with doctest examples, not `_private`. Before writing it, search the codebase
(scale, key, chord, interval, pitch, roman) for something that already does it or
nearly does, and build on that.

But be smart about runtime: never rebuild an expensive object per item. A
`scale.MajorScale` costs ~80 us to build and ~110 us per degree lookup. If a helper has
one caller and standing alone would force per-call setup or awkward context parameters,
inline it and hoist the setup out of the loop.

**Why:** the point of music21 is giving people helpful tools for music theory, but a
slow public helper in a hot path is worse than none. (Myke, 2026-09-29: a public
`chordDegreeFromPitch` that built a MajorScale per pitch and took a `chordDegrees`
collection was inlined into `chordSymbolFigureFromChord` with the scale built once.)

**How to apply:** default to public for genuinely reusable theory tools; inline when
there is one caller and the standalone signature would be slow or contrived.
Related: [[docs-audience-separation]].
