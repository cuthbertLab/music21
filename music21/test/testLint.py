# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testLint.py
# Purpose:      Controller for all lint based testing.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2010, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

# this requires pylint to be installed and available from the command line


import sys

from music21.test import testSingleCoreAll as test

try:
    from pylint.lint import Run as pylintRun
except ImportError:
    pylintRun = None



# see feature list here:
# http://docs.pylint.org/features.html

# W0511:	Used when a warning note as FIXME or XXX is detected.
# W0404:	Reimport %r (imported line %s) Used when a module is reimported multiple times.
# we do this all the time in unit tests
# R0201:	Method could be a function Used when a method doesn't use its bound instance, and so could be written as a function.
# R0904:	Too many public methods (%s/%s) Used when class has too many public methods, try to reduce this to get a more simple (and so easier to use) class.
# E1101:	%s %r has no %r member Used when a variable is accessed for an unexistant member.
# R0914:	Too many local variables (%s/%s) Used when a function or method has too many local variables.
# many of our test use many local variables
# R0903:	Too few public methods (%s/%s) Used when class has too few public methods, so be sure it's really worth it.
# R0911:	Too many return statements (%s/%s) Used when a function or method has too many return statement, making it hard to follow.


def main(fnAccept=None):
    '''
    `fnAccept` is a list of one or more files to test.  Otherwise runs all.
    '''
    if pylintRun is None:
        print("make sure that 'sudo pip install pylint' is there. exiting.")
        return 

    mg = test.ModuleGather()

    fnPathReject = [
                    'demos/',
                    'alpha/',
                    'test/',
                    'mxObjects.py',
                    'fromMxObjects.py',
                    'toMxObjects.py',
                    'xmlHandler.py',
                    '/ext/',
                    #'bar.py',  # used to crash pylint...
                    #'repeat.py', # used to hang pylint...
                    #'spanner.py', # used to hang pylint...
                    ]
    disable = [
                'cyclic-import', # we use these inside functions when there's a deep problem.
                'unnecessary-pass', # nice, but not really a problem...
                'locally-disabled', # test for this later, but hopefully will know what they're doing

                'duplicate-code', # needs to ignore strings -- keeps getting doctests...

                'arguments-differ', # someday...
                'abstract-class-instantiated', # this trips on the fractions.Fraction() class.
                'redefined-builtin', # remove when Eclipse tags are parsed @ReservedAssignment = pylint: disable=W0622
                'fixme', # known...
                'superfluous-parens', # next...
                'too-many-statements', # someday
                'no-member', # important, but too many false positives
                'too-many-arguments', # definitely! but takes too long to get a fix now...
                'too-many-public-methods', # maybe, look 
                'too-many-branches', # yes, someday
                'too-many-locals',   # no
                'too-many-lines',    # yes, someday.
                'bad-whitespace',    # maybe later, but "bad" isn't something I necessarily agree with
                'bad-continuation',  # never remove -- this is a good thing many times.
                'line-too-long',     # maybe later
                'too-many-return-statements', # we'll see
                'unpacking-non-sequence', # gets it wrong too often.
                'too-many-instance-attributes', # maybe later
                
                'invalid-name',      # these are good music21 names; fix the regexp instead...
                'no-self-use',       # maybe later
                'too-few-public-methods', # never remove or set to 1
                'trailing-whitespace',  # should ignore blank lines with tabs
                'missing-docstring',    # gets too many well-documented properties
                'star-args', # no problem with them...
                'protected-access', # this is an important one, but for now we do a lot of
                           # x = copy.deepcopy(self); x._volume = ... which is not a problem...
                'unused-argument',
                'import-self', # fix is either to get rid of it or move away many tests...
               ]

    goodnameRx = {'argument-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'attr-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'class-rgx': r'[A-Z_][A-Za-z0-9_]{2,30}$',
                  'function-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'method-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'module-rgx': r'(([a-z_][a-zA-Z0-9_]*)|([A-Z][a-zA-Z0-9]+))$',
                  'variable-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  }

    cmd = ['--output-format=parseable',
           r'--dummy-variables-rgx="_$|dummy|unused|i$|j$|junk|counter"', 
           '--docstring-min-length=3',
           '--max-args=7',  # should be 5 later, but baby steps
           '--bad-names="foo,shit,fuck,stuff"', # definitely allow "bar" for barlines
           '--reports=n'
           ]
    for gn, gnv in goodnameRx.items():
        cmd.append('--' + gn + '="' + gnv + '"')

    #print(cmd)
    
    for pyLintId in disable:
        cmd.append('--disable=%s' % pyLintId)

    # add entire package
    acceptable = []
    for fp in mg.modulePaths:
        rejectIt = False
        for rejectPath in fnPathReject:
            if rejectPath in fp:
                rejectIt = True
                break
        if rejectIt:
            continue
        acceptable.append(fp)

    cmdFile = cmd + acceptable
    #print(' '.join(cmdFile))
    #print(fp)
    pylintRun(cmdFile, exit=False)


if __name__ == '__main__':
    main(sys.argv[1:])



#     if len(sys.argv) >= 2:
#         test.main(sys.argv[1:], restoreEnvironmentDefaults=True)
#     else:
#         test.main(restoreEnvironmentDefaults=True)
# 

#------------------------------------------------------------------------------
# eof

