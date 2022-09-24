# -*- coding: utf-8 -*-
from __future__ import annotations

from music21 import exceptions21
from music21 import corpus

if __name__ == '__main__':
    try:
        # noinspection PyPackageRequirements
        import guppy  # type: ignore
    except ImportError:
        raise exceptions21.Music21Exception('memoryUsage.py requires guppy')

    hp = guppy.hpy()
    hp.setrelheap()
    x = corpus.parse('bwv66.6')
    h = hp.heap()
    print(h)
