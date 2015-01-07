# -*- coding: utf-8 -*-

"""
Files in this package relate to aiding in composition
"""

__all__ = ['phasing']  # leave off aug30 for now

import sys

if sys.version > '3':
    from music21.composition import phasing
else:
    import phasing # @Reimport


#------------------------------------------------------------------------------
# eof



