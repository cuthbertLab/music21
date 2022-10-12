# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:          timeGraphsImportStar.py
# Purpose:       time how long it takes to import music21, and report biggest offenders
#
# Authors:       Michael Scott Asato Cuthbert
#                Christopher Ariza
#
# Copyright:    Copyright © 2009-2020 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
# pragma: no cover
from __future__ import annotations

import cProfile
import pstats

def main():
    MIN_FRACTION_TO_REPORT = 0.03

    with cProfile.Profile() as pr:
        import music21

    print(f'Profile of {music21.__version__}')
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats('music21', MIN_FRACTION_TO_REPORT)


if __name__ == '__main__':
    main()
