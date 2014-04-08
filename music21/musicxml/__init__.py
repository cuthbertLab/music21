# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/__init__.py
# Purpose:      Access to musicxml library
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

_all_ = ['mxObjects', 'm21ToString', 'toMxObjects', 'fromMxObjects', 'xmlHandler']

import sys

if sys.version > '3':
    python3 = True
else:
    python3 = False

if python3:
    from . import mxObjects
    from . import m21ToString
    from . import toMxObjects
    from . import fromMxObjects
    from . import xmlHandler
else:
    import mxObjects # @Reimport
    import m21ToString # @Reimport
    import toMxObjects # @Reimport
    import fromMxObjects # @Reimport
    import xmlHandler # @Reimport
#------------------------------------------------------------------------------
# eof

