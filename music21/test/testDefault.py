# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         testDefault.py
# Purpose:      Controller for all tests in music21 in the default Environment.
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import sys
from music21.test import testSingleCoreAll as test

# ------------------------------------------------------------------------------
if __name__ == '__main__':

    if len(sys.argv) >= 2:
        test.main(sys.argv[1:], restoreEnvironmentDefaults=True)
    else:
        test.main(restoreEnvironmentDefaults=True)


