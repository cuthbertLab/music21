# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testDefault.py
# Purpose:      Controller for all tests in music21 in the default Environment.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import sys
from music21.test import testSingleCoreAll as test

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    if len(sys.argv) >= 2:
        test.main(sys.argv[1:], restoreEnvironmentDefaults=True)
    else:
        test.main(restoreEnvironmentDefaults=True)



#------------------------------------------------------------------------------
# eof

