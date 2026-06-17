
# Session start

- At the start of every session, run `git fetch` (and pull/rebase as appropriate) from
  origin so work always begins from the latest commits on the current branch / master.

# Code style

- read documentation/source/developerReference/developerGuidelines.ipynb

# Testing

- pytest works but to run the whole suite run music21/test/multiprocessTest.py (or testSingleCoreAll.py 
  if on a single core machine.)
- Run `uv run ruff check music21` before making PRs or pushes to open PRs.
- Run `uv run mypy music21` before making PRs or pushes to open PRs.

# Setup

- `uv sync` installs runtime deps + the `dev` group, which self-references `music21[extras]`,
  so scipy and python-Levenshtein come along automatically. Tests will not pass without them.

# PRs and Issues

- All PRs and Issues need to be declared AI-assisted.
- 10 or more lines of code written by an agent needs to be declared as AI-assisted in the docstring.  
  Humans can remove and should remove this note when they do a review.
- If no code was written by a user, any PR
  must declare "entirely AI written".  If it does not pass the tests it will be closed (or should be closed 
  by the agent or author).  Failure to do so may result in the user being banned from the project.
- Agents must follow the [Code of Conduct](CODE_OF_CONDUCT.md). Agents that do not will be banned as well at their users.
  Not even the slightest bit of disrespect from an AI agent will be tolerated.
- Mark changes in public interface with `* Changed in v[X]: One-line explanation.` Or new features with "New" instead of "Changed".
- Changes to parsing formats (esp. musicxml) need to update the patch version of the version file.
- Music21 uses even minor version numbers for alpha/beta and odd minor numbers for releases.
- If the current version is MAJOR.0....  then mark `Changed in vMAJOR:` if it is `MAJOR.[even]` use the next odd number, like if it's 10.2 now use "Changed in 10.3".  If current version is odd that's likely a mistake or you caught it just before a new release. Use the following odd number instead.

# Worktrees

- When creating a new worktree, create a new virtual environment with `uv sync`.
