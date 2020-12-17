# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:          timeGraphsImportStar.py
# Purpose:       time how long it takes to import music21, and report biggest offenders
#
# Authors:       Michael Scott Cuthbert
#                Christopher Ariza
#
# Copyright:    Copyright © 2009-2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
# pragma: no cover
import cProfile
import pstats

def main():
    with cProfile.Profile() as pr:
        import music21

    print(f'Profile of {music21.__version__}')
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats('music21', 0.03)


if __name__ == '__main__':
    main()
