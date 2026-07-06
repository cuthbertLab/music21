---
name: issue-1349-romanNumeral-direction
description: Status and direction for RomanNumeral.romanNumeral vs romanNumeralFromChord (GitHub issues #1349 and #1249)
metadata:
  type: project
---

As of 2026-07-06 (branch `fix-1349-raised-67`): the core raised-^6/^7 bug in
GitHub issue #1349 is FIXED — `correctRNAlterationForMinor` gained a
keyword-only `chordHasMajorThird` argument so major-quality chords on raised
^6/^7 in minor keep their sharp (figure `#VI`, `.romanNumeral` `'#VI'`), and
the tsvConverter `localKeyAsRn` workaround was removed. (Naming settled after
two rounds: name the parameter for the chord-level fact it carries, not for
its consequence like "uppercaseNumeral" — the numeral doesn't exist yet when
the function runs.) Myke decided NOT to
flip the `romanNumeralFromChord` default from CAUTIONARY to QUALITY (her 2022
idea in the issue) for now. Still open, to discuss with contributor pablopupo
and Malcolm Sailor on the issue: (2) adding `sixthMinor`/`seventhMinor`
parameters to `romanNumeralFromChord` and possibly flipping its default, and
(4) issue #1249 (secondary-numeral `#vii` prefixing).

**Why:** `.romanNumeral` is the *semantic* root-degree token (alteration
relative to the key's natural scale, read from `frontAlterationAccidental`),
while `.figure` is notational. `harmonicFunction.romanToFunction` and the
tsvConverter DCML export depend on the semantic reading, so the property
should never be deprecated. Known remaining wart: seventh chords on raised
^6/^7 in minor still don't round-trip their figures (e.g. `#VIb753` reparses
with G-flat) — the CAUTIONARY generation convention computes inversion figures
against an "altered key" while parsing measures against the original scale,
and the mismatch differs per degree.

**How to apply:** when returning to items 2+4, the minor-^6/^7 accidental
convention lives in three places that must stay in sync (see the maintenance
comment in `correctRNAlterationForMinor`). The same session renamed
`FigureTuple.aboveBass` to `degFromRefPitch` and `ChordFigureTuple` to
`PitchFigureTuple`, and replaced `figureTupleSolo` with the classmethod
constructor `FigureTuple.fromPitchAndReference(pitchObj, keyObj, refPitch)`
(old name kept as a deprecated v11→v12 alias). Myke is not all-in on
classmethod constructors in general, but preferred one here over a
module-level function whose name read as the verb "figure".
