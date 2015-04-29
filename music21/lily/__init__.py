# -*- coding: utf-8 -*-

__all__ = ["translate", "lilyObjects"]

import sys

if sys.version > '3':
    from music21.lily import translate
    from music21.lily import lilyObjects
else:
    import translate # @Reimport
    import lilyObjects # @Reimport
#------------------------------------------------------------------------------
# eof

