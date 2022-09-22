# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         coverageM21.py
# Purpose:      Starts Coverage w/ default arguments
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2014-15 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import sys

omit_modules = [
    'dist/dist.py',
    'music21/test/*',
    'music21/configure.py',
    'music21/figuredBass/examples.py',
    'music21/alpha/*',
]

# THESE ARE NOT RELEVANT FOR coveralls.io -- edit .coveragerc to change that
exclude_lines = [
    r'\s*import music21\s*',
    r'\s*music21.mainTest\(\)\s*',
    r'.*#\s*pragma:\s*no cover.*',
    r'class TestExternal.*',
    r'class TestSlow.*',
]


def getCoverage(overrideVersion=False):
    # Run this on a middle Python version so that we can
    # check timing of newest vs oldest, AND so that
    # we can quickly see failures on newest and oldest.
    # (The odds of a failure on the middle version are low if
    # the newest and oldest are passing)
    #
    # Note the .minor == 9 -- that makes it only run on 3.9
    # run on Py 3.9 -- to get Py 3.8/3.10 timing...
    #
    # When changing the version, be sure also to change
    # .github/maincheck.yml's line:
    #           if: ${{ matrix.python-version == '3.9' }}
    if overrideVersion or sys.version_info.minor == 9:
        try:
            # noinspection PyPackageRequirements
            import coverage  # type: ignore
            cov = coverage.Coverage(omit=omit_modules)  # , debug='trace')
            for e in exclude_lines:
                cov.exclude(e, which='exclude')
            cov.start()
            import music21  # pylint: disable=unused-import
        except ImportError:
            cov = None
    else:
        cov = None
    return cov

def startCoverage(cov):
    if cov is not None:
        cov.start()

def stopCoverage(cov):
    if cov is not None:
        cov.stop()
        cov.save()
