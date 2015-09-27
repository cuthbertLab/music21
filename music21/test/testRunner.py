# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         testRunner.py
# Purpose:      Music21 testing suite
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2006-2015 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
The testRunner module contains the all important "mainTest" function that runs tests
in a given module.  Except for the one instance of "defaultImports", everything here
can run on any system, not just music21.
'''
from __future__ import (division, print_function, absolute_import)

import __future__

import doctest
import inspect
import re
import sys
import unittest
from music21.ext import six


defaultImports = ('music21',)


###### monkey patch doctest...

def _msc_extract_future_flags(globs):
    '''
    Pretend like no matter what, the PY2 code has
    all __future__ flags set.
    '''
    flags = 0
    for fname in __future__.all_feature_names:
        if fname in ('absolute_import', 
                     'print_function',
                     'division',
                     ):
            flags |= getattr(__future__, fname).compiler_flag
    return flags

if six.PY2:
    doctest._extract_future_flags = _msc_extract_future_flags
    
    naive_single_quote_re = re.compile(r"(^|.)'((\\'|[^'])*?)'")
    naive_double_quote_re = re.compile(r'(^|.)"((\\"|[^"])*?)"')
    
    suquoteConv = lambda m: (m.group(1) if m.group(1) != "u" else "") + "'" + m.group(2) + "'"
    duquoteConv = lambda m: (m.group(1) if m.group(1) != "u" else "") + '"' + m.group(2) + '"'

    sbquoteConv = lambda m: (m.group(1) if m.group(1) != "b" else "") + "'" + m.group(2) + "'"
    dbquoteConv = lambda m: (m.group(1) if m.group(1) != "b" else "") + '"' + m.group(2) + '"'
    
#ALL_OUTPUT = []

class Py3In2OutputChecker(doctest.OutputChecker):
    '''
    In music21, we write all doctests for passing
    under Python 3.  The differences between it and
    Py2 mean that we need to find certain differences
    and remove them.
    
    First version: removes bytes from the expected output (want) and unicode from received (got)
    '''
    def check_output(self, want, got, optionflags):
        '''
        cannot use super with Py2 since we have old-style classes going on.
        '''
        if six.PY3:
            return super(Py3In2OutputChecker, self).check_output(want, got, optionflags)
        else:
            #x = [want, got]
            
            want = naive_single_quote_re.sub(sbquoteConv, want) # bytes in WANT disappear
            want = naive_double_quote_re.sub(dbquoteConv, want) # bytes in WANT disappear

            got = naive_single_quote_re.sub(suquoteConv, got) # unicode in GOT disappears
            got = naive_double_quote_re.sub(duquoteConv, got) # unicode in GOT disappears
            
            #x.extend([want, got])
            #ALL_OUTPUT.append(x)
            return doctest.OutputChecker.check_output(self, want, got, optionflags)

###### test related functions

def addDocAttrTestsToSuite(suite, 
                           moduleVariableLists, 
                           outerFilename=None, 
                           globs=False, 
                           optionflags=(
                                        doctest.ELLIPSIS |
                                        doctest.NORMALIZE_WHITESPACE
                                        )):
    '''
    takes a suite, such as a doctest.DocTestSuite and the list of variables
    in a module and adds from those classes that have a _DOC_ATTR dictionary
    (which documents the properties in the class) any doctests to the suite.
    
    >>> import doctest
    >>> s1 = doctest.DocTestSuite(chord)
    >>> s1TestsBefore = len(s1._tests)
    >>> allLocals = [getattr(chord, x) for x in dir(chord)]
    >>> test.testRunner.addDocAttrTestsToSuite(s1, allLocals)
    >>> s1TestsAfter = len(s1._tests)
    >>> s1TestsAfter - s1TestsBefore
    1
    >>> t = s1._tests[-1]
    >>> t
    isRest ()
    
    >>> 'hi'
    'hi'
    '''
    dtp = doctest.DocTestParser()
    if globs is False:
        globs = __import__(defaultImports[0]).__dict__.copy()
    for lvk in moduleVariableLists:
        if not (inspect.isclass(lvk)):
            continue
        docattr = getattr(lvk, '_DOC_ATTR', None)
        if docattr is None:
            continue
        for dockey in docattr:
            documentation = docattr[dockey]
            #print(documentation)
            dt = dtp.get_doctest(documentation, globs, dockey, outerFilename, 0)
            if len(dt.examples) == 0:
                continue
            dtc = doctest.DocTestCase(dt, 
                                      optionflags=optionflags,
                                      checker=Py3In2OutputChecker()
                                      )
            #print(dtc)
            suite.addTest(dtc)


def fixTestsForPy2and3(doctestSuite):
    '''
    Fix doctests so that they work in both python2 and python3, namely
    unicode/byte characters and added module names to exceptions.
    
    >>> import doctest
    >>> s1 = doctest.DocTestSuite(chord)
    >>> test.testRunner.fixTestsForPy2and3(s1)
    '''
    for dtc in doctestSuite: # Suite to DocTestCase -- undocumented.
        if not hasattr(dtc, '_dt_test'):
            continue
        dt = dtc._dt_test # DocTest
        for example in dt.examples: # fix Traceback exception differences Py2 to Py3
            if six.PY3:
                if example.exc_msg is not None and len(example.exc_msg) > 0:
                    example.exc_msg = "..." + example.exc_msg
                elif (example.want is not None and
                        example.want.startswith('u\'')):
                    # probably a unicode example:
                    # simplistic, since (u'hi', u'bye')
                    # won't be caught, but saves a lot of anguish
                    example.want = example.want[1:]
            elif six.PY2:
                if (example.want is not None and
                        example.want.startswith('b\'')):
                    # probably a unicode example:
                    # simplistic, since (b'hi', b'bye')
                    # won't be caught, but saves a lot of anguish
                    example.want = example.want[1:]
            # this probably should not go here, but we are already iterating over
            # examples
            example.want = stripAddresses(example.want, '0x...')

ADDRESS = re.compile('0x[0-9A-Fa-f]+')
    
def stripAddresses(textString, replacement = "ADDRESS"):
    '''
    Function that changes all memory addresses (pointers) in the given
    textString with (replacement).  This is useful for testing
    that a function gives an expected result even if the result
    contains references to memory locations.  So for instance:


    >>> test.testRunner.stripAddresses("{0.0} <music21.clef.TrebleClef object at 0x02A87AD0>")
    '{0.0} <music21.clef.TrebleClef object at ADDRESS>'

    while this is left alone:

    >>> test.testRunner.stripAddresses("{0.0} <music21.humdrum.MiscTandem *>I humdrum control>")
    '{0.0} <music21.humdrum.MiscTandem *>I humdrum control>'


    For doctests, can strip to '...' to make it work fine with doctest.ELLIPSIS
    
    >>> test.testRunner.stripAddresses("{0.0} <music21.base.Music21Object object at 0x102a0ff10>", '0x...')
    '{0.0} <music21.base.Music21Object object at 0x...>'

    :rtype: str
    '''
    return ADDRESS.sub(replacement, textString)


#-------------------------------------------------------------------------------



def mainTest(*testClasses, **kwargs):
    '''
    Takes as its arguments modules (or a string 'noDocTest' or 'verbose')
    and runs all of these modules through a unittest suite

    Unless 'noDocTest' is passed as a module, a docTest
    is also performed on `__main__`, hence the name "mainTest".

    If 'moduleRelative' (a string) is passed as a module, then
    global variables are preserved.

    Run example (put at end of your modules):

    ::

        import unittest
        class Test(unittest.TestCase):
            def testHello(self):
                hello = "Hello"
                self.assertEqual("Hello", hello)

        import music21
        if __name__ == '__main__':
            music21.mainTest(Test)


    This module tries to fix up some differences between python2 and python3 so
    that the same doctests can work.
    '''
    
    runAllTests = True

    # default -- is fail fast.
    failFast = bool(kwargs.get('failFast', True))
    if failFast:
        optionflags = (
            doctest.ELLIPSIS |
            doctest.NORMALIZE_WHITESPACE |
            doctest.REPORT_ONLY_FIRST_FAILURE
            )
    else:
        optionflags = (
            doctest.ELLIPSIS |
            doctest.NORMALIZE_WHITESPACE
            )
    
    globs = None
    if ('noDocTest' in testClasses or 'noDocTest' in sys.argv
        or 'nodoctest' in sys.argv or bool(kwargs.get('noDocTest', False))):
        skipDoctest = True
    else:
        skipDoctest = False

    # start with doc tests, then add unit tests
    if skipDoctest:
        # create a test suite for storage
        s1 = unittest.TestSuite()
    else:
        # create test suite derived from doc tests
        # here we use '__main__' instead of a module
        if ('moduleRelative' in testClasses or 
                'moduleRelative' in sys.argv or 
                bool(kwargs.get('moduleRelative', False))):
            pass
        else:
            for di in defaultImports:
                globs = __import__(di).__dict__.copy()
        try:
            s1 = doctest.DocTestSuite(
                '__main__',
                globs=globs,
                optionflags=optionflags,
                checker=Py3In2OutputChecker()
                )
        except ValueError as ve: # no docstrings
            print("Problem in docstrings [usually a missing r value before " + 
                  "the quotes:] {0}".format(str(ve)))
            s1 = unittest.TestSuite()


    verbosity = 1
    if ('verbose' in testClasses or 
            'verbose' in sys.argv or 
            bool(kwargs.get('verbose', False))):
        verbosity = 2 # this seems to hide most display

    displayNames = False
    if ('list' in sys.argv or 
            'display' in sys.argv or 
            bool(kwargs.get('display', False)) or 
            bool(kwargs.get('list', False))):
        displayNames = True
        runAllTests = False

    runThisTest = None
    if len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg not in ('list', 'display', 'verbose', 'nodoctest'):
            # run a test directly named in this module
            runThisTest = sys.argv[1]
    if bool(kwargs.get('runTest', False)):
        runThisTest = kwargs.get('runTest', False)

    # -f, --failfast
    if ('onlyDocTest' in sys.argv or 
            'onlyDocTest' in testClasses or 
            bool(kwargs.get('onlyDocTest', False))
            ):
        testClasses = [] # remove cases
    for t in testClasses:
        if not isinstance(t, six.string_types):
            if displayNames is True:
                for tName in unittest.defaultTestLoader.getTestCaseNames(t):
                    print('Unit Test Method: %s' % tName)
            if runThisTest is not None:
                tObj = t() # call class
                # search all names for case-insensitive match
                for name in dir(tObj):
                    if (name.lower() == runThisTest.lower() or
                           name.lower() == ('test' + runThisTest.lower()) or
                           name.lower() == ('xtest' + runThisTest.lower())):
                        runThisTest = name
                        break
                if hasattr(tObj, runThisTest):
                    print('Running Named Test Method: %s' % runThisTest)
                    getattr(tObj, runThisTest)()
                    runAllTests = False
                    break
                else:
                    print('Could not find named test method: %s, running all tests' % runThisTest)

            # normally operation collects all tests
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(t)
            s1.addTests(s2)

    ### Add _DOC_ATTR tests...
    if not skipDoctest:
        stacks = inspect.stack()
        if len(stacks) > 1:
            outerFrameTuple = stacks[1]
        else:
            outerFrameTuple = stacks[0]
        outerFrame = outerFrameTuple[0]
        outerFilename = outerFrameTuple[1]
        localVariables = list(outerFrame.f_locals.values())
        addDocAttrTestsToSuite(s1, localVariables, outerFilename, globs, optionflags)

    if runAllTests is True:
        fixTestsForPy2and3(s1)
                                    
        runner = unittest.TextTestRunner()
        runner.verbosity = verbosity
        unused_testResult = runner.run(s1)
        
        
if __name__ == '__main__':
    mainTest()
    #from pprint import pprint
    #pprint(ALL_OUTPUT)
        
