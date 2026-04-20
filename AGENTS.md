
# Code style

- read documentation/source/developerReference/developerGuidelines.ipynb

# Testing

- pytest works but to run the whole suite run music21/test/multiprocessTest.py (or testSingleCoreAll.py if on a single core machine.)
- Run `uv run mypy music21` before making PRs or pushes to open PRs
- All PRs need to be declared AI-assisted.
- 10 or more lines of code written by an agent needs to be declared as AI-assisted in the docstring.  Humans can remove and should remove this note when they do a review.

# Worktrees

- When creating a new worktree, create a new virtual environment with `uv sync`.
