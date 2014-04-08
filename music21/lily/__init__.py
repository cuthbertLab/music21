# -*- coding: utf-8 -*-

__all__ = ["translate", "lilyObjects"]

import sys

if sys.version > '3':
    from . import translate
    from . import lilyObjects
else:
    import translate # @Reimport
    import lilyObjects # @Reimport
#------------------------------------------------------------------------------
# eof

