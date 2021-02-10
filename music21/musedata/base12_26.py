# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         base12_26.py
# Purpose:      Placeholder of Hewlett's base 40 system for 0th and 1st order (base12 and 26).
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2018 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Placeholder dicts for the 0th and 1st order of Hewlett's base40 system (base12 and 26).
'''
import unittest

# ------------------------------------------------------------------------------

# Key => Base12 pitch number
# Value => Music21 Pitch name
base12Equivalent = {0: 'C',
                    1: None,
                    2: 'D',
                    3: None,
                    4: 'E',
                    5: 'F',
                    6: None,
                    7: 'G',
                    8: None,
                    9: 'A',
                    10: None,
                    11: 'B',
                    }

# Key => Music21 Pitch name
# Value => Base12 pitch number
base12Representation = {'C': 0,
                        # empty
                        'D': 2,
                        # empty
                        'E': 4,
                        'F': 5,
                        # empty
                        'G': 7,
                        # empty
                        'A': 9,
                        # empty
                        'B': 11,
                        }

# Key => Base40 delta (difference between two Base40 pitch numbers)
# Value => Corresponding music21 Interval
Base12IntervalTable = {0: 'P1',
                        1: 'm2',
                        2: 'M2',
                        3: 'm3',
                        4: 'M3',
                        5: 'P4',

                        7: 'P5',
                        8: 'm6',
                        9: 'M6',
                        10: 'm7',
                        11: 'M7',
                       }

# ------------------------------------------------------------------------------

# Key => Base26 pitch number
# Value => Music21 Pitch name
base26Equivalent = {0: 'C-',
                    1: 'C',
                    2: 'C#',
                    3: None,
                    4: 'D-',
                    5: 'D',
                    6: 'D#',
                    7: None,
                    8: 'E-',
                    9: 'E',
                    10: 'E#',
                    11: 'F-',
                    12: 'F',
                    13: 'F#',
                    14: None,
                    15: 'G-',
                    16: 'G',
                    17: 'G#',
                    18: None,
                    19: 'A-',
                    20: 'A',
                    21: 'A#',
                    22: None,
                    23: 'B-',
                    24: 'B',
                    25: 'B#',
                    }

# Key => Music21 Pitch name
# Value => Base26 pitch number
base26Representation = {'C-': 0,
                         'C': 1,
                         'C#': 2,
                         # empty
                         'D-': 4,
                         'D': 5,
                         'D#': 6,
                         # empty
                         'E-': 8,
                         'E': 9,
                         'E#': 10,
                         'F-': 11,
                         'F': 12,
                         'F#': 13,
                         # empty
                         'G-': 15,
                         'G': 16,
                         'G#': 17,
                         # empty
                         'A-': 19,
                         'A': 20,
                         'A#': 21,
                         # empty
                         'B-': 23,
                         'B': 24,
                         'B#': 25,
                        }

# Key => Base26 delta (difference between two Base26 pitch numbers)
# Value => Corresponding music21 Interval

Base26IntervalTable = {0: 'P1',

                        3: 'm2',
                        4: 'M2',

                        7: 'm3',
                        8: 'M3',

                        11: 'P4',

                        15: 'P5',

                        18: 'm6',
                        19: 'M6',

                        22: 'm7',
                        23: 'M7',
                       }

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

# -----------------------------------------------------------------------------
