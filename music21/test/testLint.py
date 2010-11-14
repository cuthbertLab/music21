#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         testLint.py
# Purpose:      Controller for all lint based testing.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


# this requires pylint to be installed and available from the command line


import os, sys

from music21 import common
from music21.test import test


# see feature list here:
# http://www.logilab.org/card/pylintfeatures

# C0301:	Line too long (%s/%s) Used when a line is longer than a given number of characters.
# 
# C0302:	Too many lines in module (%s) Used when a module has too much lines, reducing its readibility.

# C0103:	Invalid name "%s" (should match %s) Used when the name doesn't match the regular expression associated to its type (constant, variable, class...).
# 

# C0324:	Comma not followed by a space Used when a comma (",") is not followed by a space.

# W0621:	
# Redefining name %r from outer scope (line %s) Used when a variable's name hide a name defined in the outer scope.


# W0511:	Used when a warning note as FIXME or XXX is detected.


# W0404:	Reimport %r (imported line %s) Used when a module is reimported multiple times.
# we do this all the time in unit tests

# R0201:	Method could be a function Used when a method doesn't use its bound instance, and so could be written as a function.

# R0904:	Too many public methods (%s/%s) Used when class has too many public methods, try to reduce this to get a more simple (and so easier to use) class.

#E1101:	%s %r has no %r member Used when a variable is accessed for an unexistant member.

# R0914:	Too many local variables (%s/%s) Used when a function or method has too many local variables.
# many of our test use many local variables

#R0903:	Too few public methods (%s/%s) Used when class has too few public methods, so be sure it's really worth it.

#R0911:	Too many return statements (%s/%s) Used when a function or method has too many return statement, making it hard to follow.


def main(fnAccept=None):
    '''
    `fnAccept` is a list of one or more files to test.
    '''

    mg = test.ModuleGather()

    # only accept a few file names for now
    if fnAccept in [None, []]:
        fnAccept = ['note.py']

        #fnAccept = ['stream.py', 'note.py', 'chord.py']

    disable = ['C0301', 'C0302', 'C0103', 'C0324', 'W0621', 'W0511', 
               'W0404', 'R0201', 'R0904', 'E1101', 'R0914', 'R0903',
               'R0911', 'R0902', ]

    cmd = ['pylint -f colorized']
    for id in disable:
        cmd.append('--disable=%s' % id)

    # add entire package
    for fp in mg.modulePaths:
        dir, fn = os.path.split(fp)
        fnNoExt = fn.replace('.py', '')
        if fn in fnAccept or fnNoExt in fnAccept:
            cmdFile = cmd + [fp]
            print(' '.join(cmdFile))
            if common.getPlatform() != 'win':
                os.system(' '.join(cmdFile))


if __name__ == '__main__':
    
    main(sys.argv[1:])



#     if len(sys.argv) >= 2:
#         test.main(sys.argv[1:], restoreEnvironmentDefaults=True)
#     else:
#         test.main(restoreEnvironmentDefaults=True)
# 

#------------------------------------------------------------------------------
# eof

