---
name: running-tests
description: >-
  How to correctly run music21's tests and doctests -- with pytest for a module,
  and with the project's own runners for the whole suite. Use this whenever you
  need to run, verify, or judge the pass/fail of tests or doctests in this repo:
  confirming a change works, checking that doctests still pass, running a single
  module's tests, or sanity-checking before a PR or push. Especially consult it
  before concluding that a doctest "fails" (the repo's pytest plugin normalizes
  object addresses and injects the doctest namespace, so raw doctest.testmod
  produces FALSE failures), and before concluding that a green pytest run means
  CI will be green.
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

```bash
# everyday full run, on n-1 cores
uv run python music21/test/multiprocessTest.py

# exactly what GitHub Actions runs (~1 minute); use before pushing to a PR
uv run python -c 'from music21.test.testSingleCoreAll import ciMain as ci; ci()'
```

The two runners see slightly different sets of modules -- `multiprocessTest`
walks the package tree for modules reachable from `import music21`, while
`testSingleCoreAll` gathers module files from disk. Run both before a release.

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

## What tests may do

- Exactly one `Test(unittest.TestCase)` class per module, methods named
  `test...`. It must produce no output, open no windows, play nothing, and not
  require packages outside the music21 ecosystem.
- Anything that produces external output goes in `TestExternal`; anything slow
  goes in `TestSlow`. Both are excluded from the normal run.
- Tests should be fast: a major new module may add a few seconds, a small
  addition should add milliseconds.
- Regression cases for a bug fix belong in `Test`, never in a doctest. See the
  `writing-docs` skill.

## The other gates before a PR or a push

```bash
uv run ruff check music21
uv run mypy music21
uv run pylint -j4 music21 --rcfile=.pylintrc   # catches what the first two miss
```

Coverage is expected to rise with each contribution
(https://coveralls.io/github/cuthbertLab/music21). CI measures it on a single
pinned Python -- the **middle** supported version, see
`coverageM21.getCoverage`. `# pragma: no cover` exists for genuinely
untriggerable code and is otherwise discouraged.
