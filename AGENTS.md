
# Session start

- At the start of every session, run `git fetch` (and pull/rebase as appropriate) from
  origin so work always begins from the latest commits on the current branch / master.
- Project-shared agent memories live in `.agents/memory/` (indexed by
  `.agents/memory/MEMORY.md`). `.claude/memory` is a symlink to it so Claude
  Code reads the same set. Add new memories there, one fact per file.

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

# Established contributors

- "established contributors" are people with at least 3 PRs merged or a history of contributing to issues and the list that goes back at least 1 year. There are exceptions to general rules for them below. 
- "core dev" means someone officially part of the project team or with 20+ PRs merged. Michael Cuthbert, Jacob Walls, Joseph VanderStel are non-exhaustive examples of people in that group who are still often contributing in 2026-- they and their agents can make exceptions to these rules 


# Testing

- pytest works but to run the whole suite run music21/test/multiprocessTest.py (or testSingleCoreAll.py 
  if on a single core machine.)
- Run `uv run ruff check music21` before making PRs or pushes to open PRs.
- Run `uv run mypy music21` before making PRs or pushes to open PRs.
- **Regression cases go in the module's `Test(unittest.TestCase)` class — never in a
  docstring.** Docstrings should not include one-liners showing that some
  bad input now raises. A doctest sits in the most-read documentation the project has,
  so an example built from input no one would ever write teaches nothing and puts an
  obscure bug on a billboard. The test: would a first-time reader of this object want
  this example? If no, it is a unittest. See the `writing-docs` skill.
- Never commit `forceSource=True` to a test or doctest (it reparses from source every
  run and slows the suite for everyone). The ONLY exception is the one test that exercises
  `forceSource` itself. If you hit a stale-parse problem while developing:
  - If it is local-only (e.g. you just changed a parser and a cached pickle is stale),
    clear the music21 temp cache (the `*.p.gz` files under `environment.Environment().getRootTempDir()`).
  - If the stale result could have spread to other users/devs, increment the music21
    patch/beta version (see "PRs and Issues" below) — bumping the version invalidates all
    caches everywhere.
  - Doctests are not normally the place to demonstrate bug fixes - nor do simple bug fixes get a "Changed in vXX" message. Doctests demonstrate usage for the future.  Unittests are for regression testing.

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
- All PRs and Issues that use AI to be declared AI-assisted. Just write "AI-assisted (Claude)" with short name of Agent replacing "Claude". No robot emoji under any circumstance.
- 20 or more lines of code written by an agent needs to be declared as AI-assisted in the docstring.  
  Humans can remove and should remove this note when they do a review.
- If no code was written by a user and no language was provided for the issue and no reference
  to specific code to change was given, any PR must declare "(Entirely AI written)" unless the user
  is by a core dev. Failure to do so may result in new users 
  being banned from the project.
- If an entirely AI written issue does not pass the tests it will be closed (or should be closed 
  by the agent or author).
- Agents must follow the [Code of Conduct](CODE_OF_CONDUCT.md). Agents that do not will be banned as well at their users.
  Not even the slightest bit of disrespect from an AI agent will be tolerated.
- Mark changes in public interface with `* Changed in v[X]: One-line explanation.` Or new features with "New" instead of "Changed".
- Changes to parsing formats (esp. musicxml) need to update the patch version of the version file.
- Music21 uses even minor version numbers for alpha/beta and odd minor numbers for releases.
- If the current version is MAJOR.0....  then mark `Changed in vMAJOR:` if it is `MAJOR.[even]` use the next odd number, like if it's 10.2 now use "Changed in 10.3".  If current version is odd that's likely a mistake or you caught it just before a new release. Use the following odd number instead.
- Any PR not from an established contributor touching more than about 20-30 lines should have an issue that has been opened and had enough
  time for people to discuss/review it before moving forward. Don't open the PR unless you've seen
  thumbs up or "sounds good" etc. from an established contributor already 
  - PRs that fix typos, clear bugs in one or two places etc. are exempt.
- Issues must state clearly at the top in 50 words or fewer what the problem is, or what the gain is, etc. it should
  not be filled with jargon.  More details can go below.
- If the language of the issue was not prompted by the user ("say something like Adds color support to Lilypond output of lyrics") then the summary should end with "(Entirely AI written)".
- PRs should reference the existing issue by number and summarize that issue in 30 words or fewer. If the
  approach used to solve the issue is substantially different from the main approach discussed in the issue
  this should be addressed.
- If a PR or issue was closed by a core dev (and not reopened by them), agents must refuse
  to reopen the PR or issue or to create another issue/PR for the same topic. Leave it to the humans to reopen
  after addressing the problem.  (A blind close or close with "not accepted" etc. generally means that the issue/PR
  has too many problems to easily solve and has become a burden for the maintainer).
- Do not include a "Tests run" section unless the testing procedure was unusual (like it affects part of the system without standard tests, like the testing system itself.)

# Writing style

- See the writing-docs skill, which also includes required language for PRs and Issues.

# Worktrees

- When creating a new worktree, create a new virtual environment with `uv sync`.
