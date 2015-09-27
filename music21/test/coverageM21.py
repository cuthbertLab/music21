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
                '*/ext/*',
                'dist/dist.py',
                'installer.py',
                '*/documentation/upload.py',
                '*/documentation/make.py',
    #            '*/test/*',
    #            '*/demos/*',  # maybe remove someday...
                'music21/configure.py',
                '*/figuredBass/examples.py',
                '*/trecento/tonality.py'
                ]
exclude_lines = [
                r'\s*import music21\s*',
                r'\s*music21.mainTest\(\)\s*',
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
