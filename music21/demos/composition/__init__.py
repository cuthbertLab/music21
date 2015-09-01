# -*- coding: utf-8 -*-

"""
Files in this package relate to aiding in composition
"""

__all__ = ['phasing', 'seeger']  # leave off aug30 for now

import sys

if sys.version > '3':
    from music21.demos.composition import phasing
    from music21.demos.composition import seeger
else:
    import phasing # @Reimport
    import seeger # @Reimport

#------------------------------------------------------------------------------
# eof



