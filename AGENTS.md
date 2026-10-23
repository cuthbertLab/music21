
# Session start

- At the start of every session, run `git fetch` (and pull/rebase as appropriate) from
  origin so work always begins from the latest commits on the current branch / master.

# Code style

- read documentation/source/developerReference/developerGuidelines.ipynb
- music21 targets Python 3.12+, so use PEP 695 syntax: the `type` statement for
  type aliases (`type OffsetQL = float|Fraction`) and the bracket form for
  generic classes (`class Stream[M21ObjType: base.Music21Object]:`).
- f-strings: even though Python 3.12 (PEP 701) lets a nested string reuse the
  f-string's own quote character, we deliberately do **not** do that — reusing
  the same quote inside an f-string is harder to read. Keep using the *other*
  quote for nested strings, e.g. `f'the value is {d["key"]}'`, not
  `f"the value is {d["key"]}"`. This is pinned in `pyproject.toml` via
  `[tool.ruff.format] nested-string-quote-style = "alternating"`.

# Testing

- pytest works but to run the whole suite run music21/test/multiprocessTest.py (or testSingleCoreAll.py 
  if on a single core machine.)
- Run `uv run ruff check music21` before making PRs or pushes to open PRs.
- Run `uv run mypy music21` before making PRs or pushes to open PRs.
- Never commit `forceSource=True` to a test or doctest (it re-parses from source every
  run and slows the suite for everyone). The ONLY exception is the one test that exercises
  `forceSource` itself. If you hit a stale-parse problem while developing:
  - If it is local-only (e.g. you just changed a parser and a cached pickle is stale),
    clear the music21 temp cache (the `*.p.gz` files under `environment.Environment().getRootTempDir()`).
  - If the stale result could have spread to other users/devs, increment the music21
    patch/beta version (see "PRs and Issues" below) — bumping the version invalidates all
    caches everywhere.

# Setup

- `uv sync` installs runtime deps + the `dev` group, which self-references `music21[extras]`,
  so scipy and python-Levenshtein come along automatically. Tests will not pass without them.

# Python version support

- `music21` supports at least the last two released versions of Python and up to whatever
  Python version Google Colab runs (unless it gets EOL). Policy can change as features are added.
- The coverage CI run is intentionally pinned to the **middle** supported
  Python version. See `coverageM21.getCoverage`.

# PRs and Issues

- GitHub runs PR checks against your branch **merged with the latest `master`**, not the
  branch alone. So before opening a PR (or pushing updates to one), merge the latest commits
  from `master` into the branch — unless told otherwise, or when updating an older version
  branch such as `m21_9`. When a CI check fails but passes locally, "is my branch behind
  `master`?" should be one of the first things to check: fetch and merge `master`, then the
  newer types/code on `master` will reproduce the failure locally.
- All PRs and Issues need to be declared AI-assisted.
- 10 or more lines of code written by an agent needs to be declared as AI-assisted in the docstring.  
  Humans can remove and should remove this note when they do a review.
- If no code was written by a user, any PR must declare "entirely AI written" unless the user
  is a longtime contributor to music21.
  If it does not pass the tests it will be closed (or should be closed 
  by the agent or author).  Failure to do so may result in the user being banned from the project.
- Agents must follow the [Code of Conduct](CODE_OF_CONDUCT.md). Agents that do not will be banned as well at their users.
  Not even the slightest bit of disrespect from an AI agent will be tolerated.
- Mark changes in public interface with `* Changed in v[X]: One-line explanation.` Or new features with "New" instead of "Changed".
- Changes to parsing formats (esp. musicxml) need to update the patch version of the version file.
- Music21 uses even minor version numbers for alpha/beta and odd minor numbers for releases.
- If the current version is MAJOR.0....  then mark `Changed in vMAJOR:` if it is `MAJOR.[even]` use the next odd number, like if it's 10.2 now use "Changed in 10.3".  If current version is odd that's likely a mistake or you caught it just before a new release. Use the following odd number instead.

# Worktrees

- When creating a new worktree, create a new virtual environment with `uv sync`.
