---
name: bump-version
description: >-
  When and how to bump music21's version number. Use this whenever a change
  warrants a new version — especially any change to a parsing format or parser
  (musicxml, abc, MIDI, noteworthy/NWC, humdrum, etc.), since those invalidate
  the pickled-stream cache — as well as new features and bug fixes. Covers which
  digit to change, the even/odd minor and beta-suffix conventions, the TWO files
  to edit, and the `Changed in`/`New in` docstring markers.
---

# Bumping music21's version

The version lives in **`music21/_version.py`** as
`__version__ = 'MAJOR.MINOR.PATCHsuffix'` (e.g. `'11.0.0b2'`). The
`__version_info__` tuple is derived from it automatically — only edit the
string.

## Two files to change, always together

1. `music21/_version.py` — the `__version__` string.
2. `music21/base.py` — the single version doctest:
   ```
   >>> music21.VERSION_STR
   '11.0.0b2'
   ```
   This test exists specifically to force you to remember the bump. If you change
   `_version.py` without it, the doctest fails.

Verify both with:
```bash
uv run pytest --doctest-modules music21/base.py music21/_version.py
```
(or `uv run python -c "import music21; print(music21.VERSION_STR)"`).

## When to bump

- **Parsing-format / parser changes (most common reason).** Any change to how a
  format is read or written — musicxml, abc, MIDI, noteworthy/NWC, humdrum,
  etc. — should bump the version, even a refactor, because the version is baked
  into the **pickled-stream cache** (cached parsed files). Bumping invalidates
  stale pickles so users don't get results from the old parser. This is the rule
  in AGENTS.md ("Changes to parsing formats … need to update the patch version").
- **New feature** → bump (see digit rules below); mark it in docstrings with
  `* New in vX: …`.
- **Bug fix** → bump the patch; if it changes public behavior, mark
  `* Changed in vX: …`.
- **Pure internal refactor with no behavioral/pickle impact** → usually no bump.

## Which part to change

music21 follows semver-ish rules (see the `_version.py` docstring for the full
rationale):

- **MAJOR (X)** — breaks old features. Rare.
- **MINOR (Y)** — new features. **Even Y = alpha/beta, odd Y = release.**
  `X.0` (e.g. `11.0`) are development releases that can still change until `X.1`.
- **PATCH (Z)** — bug fixes and parsing/pickle-invalidating changes.
- **beta suffix (`bN`)** — successive pre-release builds of the same
  `MAJOR.MINOR.PATCH`. To cut another beta without otherwise changing the
  number, increment it: `11.0.0b1` → `11.0.0b2`. (This is what a
  parser change during a `…b1` cycle does.)

## `Changed in` / `New in` docstring markers

When a bump accompanies a public-interface change, annotate the affected
method/class docstring:
- `* Changed in vX: one-line explanation.`
- `* New in vX: one-line explanation.`

Pick `X` from the AGENTS.md rule: if the current version is `MAJOR.0…`, use
`Changed in vMAJOR`; if it's `MAJOR.[even]`, use the **next odd** minor (e.g. at
`10.2`, write `Changed in 10.3`); if it's already odd, use the following odd
number. (Humans remove the AI-assisted note on review; leave the version marker.)

## Checklist

1. Edit `__version__` in `music21/_version.py`.
2. Edit the `VERSION_STR` doctest in `music21/base.py` to match.
3. Add/update `Changed in` / `New in` markers on any changed public API.
4. `uv run pytest --doctest-modules music21/base.py music21/_version.py`.
