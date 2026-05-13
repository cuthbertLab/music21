from __future__ import annotations

import platform
import sys
from typing import Any
from unittest import TestCase

import pytest  # noqa  # part of dev not running
try:
    from _pytest.doctest import DoctestItem  # noqa
except ImportError:
    class DoctestItem:  # type: ignore[no-redef]
        pass

import music21
from music21.test.testRunner import fix312OrderedDict, stripAddresses

@pytest.fixture(scope='session')
def doctest_namespace() -> dict[str, Any]:
    ns: dict[str, Any] = {}

    all_names: list[str] = list(getattr(music21, '__all__', []))
    for name in all_names:
        ns[name] = getattr(music21, name)

    # let doctests reference "music21" itself too.
    ns['music21'] = music21
    return ns

def pytest_collection_modifyitems(config, items) -> None:
    '''
    Apply music21-style doctest normalizations to pytest-collected doctests.

    This mutates each doctest Example.want in-place, like fixDoctests() does
    for doctest.DocTestSuite.
    '''
    windows: bool = platform.system() == 'Windows'
    is_python312: bool = sys.version_info >= (3, 12)

    kept = []
    for item in items:
        parent = getattr(item, 'parent', None)
        cls = getattr(parent, 'cls', None)
        if cls is not None and issubclass(cls, TestCase) and cls.__name__ != 'Test':
            # filter out TestSlow, TestExternal etc.
            continue
        if (getattr(item, 'dtest', None)
                and item.dtest.name == 'music21.common.decorators.deprecated'):
            # problem in pytest but not in doctest -- must run it once and therefore
            # does not get the "first time run" vs "second time run" behavior.
            continue

        kept.append(item)

    items[:] = kept

    for item in items:
        if not isinstance(item, DoctestItem):
            continue

        dt = item.dtest
        # doctest.DocTest (pytest stores it here)
        # (https://docs.pytest.org/en/stable/_modules/_pytest/doctest.html)

        for example in dt.examples:
            example.want = stripAddresses(example.want, '0x...')

            if is_python312:
                example.want = fix312OrderedDict(example.want, '...')

            if windows:
                example.want = example.want.replace('PosixPath', 'WindowsPath')
