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

from music21.ext import six

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

# THESE ARE NOT RELEVANT FOR coveralls.io -- edit .coveragerc
exclude_lines = [
                r'\s*import music21\s*',
                r'\s*music21.mainTest\(\)\s*',
                r'.*#\s*pragma:\s*no cover.*',
                r'class TestExternal.*',
                ]

def getCoverage():    
    if six.PY2:
        try:
            import coverage
            cov = coverage.coverage(omit=omit_modules)
            for e in exclude_lines:
                cov.exclude(e, which='exclude')
            cov.start()
        except ImportError:
            cov = None
    else:
        cov = None # coverage is extremely slow on Python 3.4 for some reason
            # in any case we only need to run it once.
    return cov

def stopCoverage(cov):
    if cov is not None:
        cov.stop()
        cov.save()
