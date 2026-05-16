
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

# Worktrees

- When creating a new worktree, create a new virtual environment with `uv sync`.
