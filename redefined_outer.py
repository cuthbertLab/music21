# pylint: disable=missing-module-docstring,missing-class-docstring,too-few-public-methods
# pylint: disable=missing-function-docstring
from __future__ import annotations
import typing as t


class Cls:
    def func(self, dd: defaultdict):
        # This import makes the definition work.
        from collections import defaultdict

        obj = defaultdict()
        obj.update(dd)
        return obj


if t.TYPE_CHECKING:
    # This import makes the annotations work.
    from collections import defaultdict
