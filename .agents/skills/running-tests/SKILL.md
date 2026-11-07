---
name: running-tests
description: >-
  How to run music21's tests and doctests and judge pass/fail: pytest for one
  module, the project's own runners for the whole suite. Read it before running
  tests, and before calling any doctest failure real.
---

# Running music21 tests and doctests

Every function, method and class needs documentation and at least one passing
test. See `documentation/source/developerReference/testing.ipynb` for the
project's own account of testing; this skill covers how to run what is there.

## One module: pytest with explicit file paths

```bash
uv run pytest music21/abcFormat/__init__.py music21/abcFormat/translate.py
```

`pyproject.toml` `[tool.pytest.ini_options]` already wires up everything:

```
addopts = ['--doctest-modules', '-p', 'music21.test.pytest_plugin']
doctest_optionflags = ['NORMALIZE_WHITESPACE', 'ELLIPSIS']
```

So do not pass `--doctest-modules` yourself -- doctests in every `.py` are
collected automatically, and `music21/test/pytest_plugin.py` is loaded.

Pass explicit file paths so the in-module `Test(unittest.TestCase)` classes run
too. `python_files = ['test_*.py', '*_test.py', 'tests.py']`, so for a module
that keeps its `Test` class inside `__init__.py` / `translate.py` (e.g.
`abcFormat`), pointing pytest at the directory collects ONLY doctests and
silently skips the unittest classes:

- `uv run pytest music21/abcFormat/` -> ~43 items (doctests only)
- `uv run pytest music21/abcFormat/__init__.py music21/abcFormat/translate.py`
  -> ~82 items (doctests **and** `Test` methods)

Modules whose tests live in a `tests.py` are already picked up by the directory
form; the gotcha is specifically a `Test` class in a non-`tests.py` file.

A module also runs its own tests directly, via the `mainTest` call at the foot
of each file:

```bash
uv run python -m music21.note              # whole module
uv run python music21/note.py testHello    # one test method
```

## Why the plugin matters (and why not to use raw doctest)

`music21/test/pytest_plugin.py` does three things that make doctests behave as
the project intends:

- It runs `stripAddresses(example.want, '0x...')` (from
  `music21.test.testRunner`) on every doctest, so a docstring that hardcodes
  `<music21.abcFormat.ABCHandler object at 0x10b0cf5f8>` is normalized and DOES
  pass. The literal hex address in the docstring is expected and fine.
- It injects the `music21.__all__` names plus `music21` itself into the doctest
  namespace, so examples reference `meter`, `key`, `corpus` without importing.
- It keeps only `Test` classes, dropping `TestSlow` and `TestExternal`.

Judge doctest pass/fail **through pytest**. Do NOT use `doctest.testmod(...)` or
`doctest.DocTestSuite(...)` directly: that path applies neither the address
normalizer nor the namespace injection, so it manufactures false failures on any
docstring printing a `<... object at 0x...>` repr or relying on injected names.
An object-address example failing on its own is the tell that doctests were run
the wrong way -- rerun through pytest.

## Whole suite: the project's runners, not pytest

pytest is for a module. For the whole suite use the runners, and note that a
green pytest run does not mean CI will be green -- they gather and order modules
differently.

Use `multiprocessTest` -- it runs on n-1 cores and finishes in about 10 seconds,
against roughly 45 for the single-core runner:

```bash
uv run python music21/test/multiprocessTest.py
```

That gap is the whole story when someone is waiting on the answer. Reach for
`testSingleCoreAll` only for what `multiprocessTest` cannot tell you: it is what
GitHub Actions runs, so it is the one to check before a release, when chasing a
CI failure that will not reproduce, or on a single-core machine.

```bash
uv run python -c 'from music21.test.testSingleCoreAll import ciMain as ci; ci()'
```

The two runners see slightly different sets of modules -- `multiprocessTest`
walks the package tree for modules reachable from `import music21`, while
`testSingleCoreAll` gathers module files from disk.

Module **order** differs between the two runners and again from pytest.
`multiprocessTest` goes in reverse-alphabetical order (with the known-slow
modules hoisted to the front on machines with more than 4 cores);
`testSingleCoreAll` re-sorts through `common.misc.sortModules`, by file mtime,
most recently modified first, falling back to reverse-alphabetical when mtimes
tie as they do on a fresh clone; pytest walks alphabetically. So a test that
depends on module order can pass in one runner and fail in another -- and
editing a file locally sorts it to the front of the CI runner, changing the
order again.

That makes leaked module-level state the usual cause of "passes alone, fails in
the suite." A doctest in `duration.py` once set
`humdrum.spineParser.flavors['JRP'] = True` and never restored it; `flavors` is
a module-level dict, so every later humdrum test in the same process parsed in
the wrong flavor. Under pytest's alphabetical order `duration` runs before
`humdrum` and the failure appeared; under CI's order it did not.

**So: a doctest that mutates module-level state must restore it**, using
`#_DOCS_HIDE` so the bookkeeping stays out of the published docs:

```
>>> saved_JRP_flavor = humdrum.spineParser.flavors['JRP']  #_DOCS_HIDE
>>> humdrum.spineParser.flavors['JRP'] = True
...
>>> humdrum.spineParser.flavors['JRP'] = saved_JRP_flavor  #_DOCS_HIDE
```

When a test fails only in a full run, re-run it alone. If it then passes,
suspect state left behind by an earlier module rather than the test itself.

## Speed budget

Aim for about 3 seconds for a module's tests, and never add more than 15 — that is time
every contributor waits on every full run. `corpus.parse()` is nearly always the culprit:
build a small stream by hand instead, or parse `bwv66.6`, which is short and still full
of interesting cases (pickup measures, and so on).

## Tests that open windows

Nothing in `Test` or in a doctest may open a window, play audio, or launch another
program. Those go in a sibling class, run only when named explicitly:

```python
class TestExternal(unittest.TestCase):
    ...

if __name__ == '__main__':
    import music21
    music21.mainTest(Test, TestExternal)
```

Because they have those side effects, skip `TestExternal` when running a file directly.

## What tests may do

Exactly one `Test(unittest.TestCase)` class per module, methods named `test...`.
It must produce no output and require nothing outside the music21 ecosystem.
Anything slow goes in a `TestSlow` sibling, excluded from the normal run like
`TestExternal`.

Regression cases for a bug fix belong in `Test`, never in a doctest. See the
`writing-docs` skill.

## The other gates before a PR or a push

```bash
uv run ruff check music21
uv run mypy music21
uv run pylint -j4 music21 --rcfile=.pylintrc   # optional: run only if major refactoring since it was last run.
```

Coverage is expected to rise with each contribution
(https://coveralls.io/github/cuthbertLab/music21). CI measures it on one pinned
Python, a middle supported version, so failures on the newest and oldest return
first. `# pragma: no cover` exists for genuinely untriggerable code and is
otherwise discouraged.
