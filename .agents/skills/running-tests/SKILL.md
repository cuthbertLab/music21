---
name: running-tests
description: >-
  How to correctly run music21's tests and doctests with pytest. Use this
  whenever you need to run, verify, or judge the pass/fail of tests or doctests
  in this repo — confirming a change works, checking that doctests still pass,
  running a single module's tests, or sanity-checking before a PR or push.
  Especially consult this before concluding that a doctest "fails": the repo's
  pytest plugin normalizes object addresses and injects the doctest namespace,
  and running doctests any other way (e.g. raw doctest.testmod) produces FALSE
  failures.
---

# Running music21 tests and doctests

The reliable way to run tests/doctests for a music21 module is plain pytest with
explicit file paths:

```bash
uv run pytest music21/abcFormat/__init__.py music21/abcFormat/translate.py
```

`pyproject.toml` `[tool.pytest.ini_options]` already wires up everything that
makes this work:

```
addopts = ['--doctest-modules', '-p', 'music21.test.pytest_plugin']
doctest_optionflags = ['NORMALIZE_WHITESPACE', 'ELLIPSIS']
```

So you do not pass `--doctest-modules` yourself — doctests in every `.py` are
collected automatically, and `music21/test/pytest_plugin.py` is loaded.

## Why the plugin matters (and why not to use raw doctest)

The plugin does two things that make doctests pass the way the project intends:

- It runs `stripAddresses(example.want, '0x...')` (from
  `music21.test.testRunner`) on every doctest, so docstrings that hardcode a
  repr like `<music21.abcFormat.ABCHandler object at 0x10b0cf5f8>` are
  normalized and DO pass. The literal hex address in the docstring is expected
  and fine.
- It injects the `music21.__all__` names plus `music21` itself into the doctest
  namespace, so examples can reference `meter`, `key`, `corpus`, etc. without
  importing them.

This is why you must judge doctest pass/fail **through pytest**. Do NOT use
`doctest.testmod(...)` or `doctest.DocTestSuite(...)` directly to decide whether
doctests pass: that path applies neither the address normalizer nor the
namespace injection, so it manufactures false failures on any docstring that
prints a `<... object at 0x...>` repr or relies on the injected names. If you
ever see only an object-address example "failing," that is the tell that you
ran doctests the wrong way — rerun through pytest.

## Pass explicit file paths, not a bare directory

Use explicit file paths so the in-module `Test(unittest.TestCase)` classes run
too, not just doctests. `python_files = ['test_*.py', '*_test.py', 'tests.py']`,
so for a module that keeps its `Test` class inside `__init__.py` /
`translate.py` (e.g. `abcFormat`), pointing pytest at the directory
(`uv run pytest music21/abcFormat/`) collects ONLY its doctests and silently
skips the unittest classes.

Concretely, for `abcFormat`:
- `uv run pytest music21/abcFormat/` → ~43 items (doctests only)
- `uv run pytest music21/abcFormat/__init__.py music21/abcFormat/translate.py`
  → ~82 items (doctests **and** `Test` methods)

Both apply the address normalizer; only the explicit-paths form also runs the
unittest classes. When a module's tests live in a `tests.py` file (much of
music21's house style), the directory form already picks those up — the gotcha
is specifically modules that keep `Test` inside a non-`tests.py` file.

## Whole suite and the other gates

- Full suite: `python music21/test/multiprocessTest.py` (or
  `music21/test/testSingleCoreAll.py` on a single-core machine).
- Before a PR or a push to an open PR, also run the lint and type gates:
  `uv run ruff check music21` and `uv run mypy music21`.
