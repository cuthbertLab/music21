# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         coverageM21.py
# Purpose:      Starts Coverage w/ default arguments
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-15 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
import sys

omit_modules = [
                'music21/ext/*',
                'dist/dist.py',
                'installer.py',
                'music21/documentation/upload.py',
                'music21/documentation/make.py',
                'music21/test/*',
                'music21/demos/*',  # maybe remove someday...
                'music21/configure.py',
                'music21/figuredBass/examples.py',
                'music21/alpha/*', #trecento/tonality.py'
                ]

# THESE ARE NOT RELEVANT FOR coveralls.io -- edit .coveragerc to change that
exclude_lines = [
                r'\s*import music21\s*',
                r'\s*music21.mainTest\(\)\s*',
                r'.*#\s*pragma:\s*no cover.*',
                r'class TestExternal.*',
                ]

def getCoverage(overrideVersion=False):
    if overrideVersion or sys.version_info.minor == 5: 
        # run on Py 3.5 -- to get Py 3.4 and 3.6 timing...
        try:
            import coverage
            cov = coverage.coverage(omit=omit_modules)
            for e in exclude_lines:
                cov.exclude(e, which='exclude')
            cov.start()
        except ImportError:
            cov = None
    else:
        cov = None
    return cov

def stopCoverage(cov):
    if cov is not None:
        cov.stop()
        cov.save()
