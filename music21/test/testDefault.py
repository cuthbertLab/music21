#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         testDefault.py
# Purpose:      Controller for all tests in music21 in the default Environment.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import sys
from music21.test import test


#-------------------------------------------------------------------------------
if __name__ == '__main__':

    if len(sys.argv) >= 2:
        test.main(sys.argv[1:], restoreEnvironmentDefaults=True)
    else:
        test.main(restoreEnvironmentDefaults=True)



#------------------------------------------------------------------------------
# eof

