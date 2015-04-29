# -*- coding: utf-8 -*-
__all__ = ["species"]

import sys

if sys.version > '3':
    from music21.counterpoint import species
else:
    import species # @Reimport
#------------------------------------------------------------------------------
# eof

