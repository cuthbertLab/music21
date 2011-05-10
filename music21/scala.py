#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         scala.py
# Purpose:      reading and translation of the Scala scale format
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Classes and functions for representing data in a Scala scale representation file
'''

import os
import unittest, doctest
try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)



import music21 

from music21 import common
from music21 import environment
_MOD = "pitch.py"
environLocal = environment.Environment(_MOD)





class ScalaPitch(object):
    '''Representation of a scala pitch notation

    >>> from music21 import *
    >>> sp = ScalaPitch(' 1066.667 cents')
    >>> print sp.parse()
    1066.667

    >>> sp = ScalaPitch(' 2/1')
    >>> sp.parse()
    1200.0

    >>> [sp.parse(x) for x in [' 5/4', '5/3', '9/4', '16/3', '7/1']]
    [300.0, 800.0, 1500.0, 5200.0, 7200.0]

    >>> [sp.parse(x) for x in ['2187/2048','9/8', '32/27', '81/64', '4/3', '729/512', '3/2', '6561/4096', '27/16', ' 16/9', '243/128', '2/1']]
    [81.4453125, 150.0, 222.222..., 318.75, 400.0, 508.59375, 600.0, 722.16796875, 825.0, 933.33333..., 1078.125, 1200.0]

    '''



    # pitch values; if has a period, is cents, otherwise a ratio
    # above the implied base ratio
    # integer values w/ no period or slash: 2 is 2/1

    def __init__(self, sourceString=None):

        self.src = None
        self._setSrc(sourceString)

        # resole all values into cents shifts
        self.cents = None

    def _setSrc(self, raw):
        raw = raw.strip()
        # get decimals and fractions
        raw, junk = common.getNumFromStr(raw, numbers='0123456789./')
        self.src = raw.strip()

    def parse(self, sourceString=None):
        '''Parse the source string and set self.cents.
        '''
        if sourceString is not None:
            self._setSrc(sourceString)

        if '.' in self.src: # cents
            self.cents = float(self.src)
        else: # its a ratio
            if '/' in self.src:
                n, d = self.src.split('/')
                n, d = float(n), float(d)
            else:
                n = float(self.src)
                d = 1.0
            # use ratio applied to octave
            self.cents = ((n / d) * 1200.0) - 1200.0
        return self.cents

class ScalaScale(object):
    
    def __init__(self, sourceString=None, fileName='none'):
        self.src = sourceString
        self.fileName = fileName # store source file anme

        # added in parsing:
        self.description = None
        
        # lower limit is 0, as degree 0, or the 1/1 ratio, is implied
        # assumes octave equivalence?
        self.noteCount = None # number of lines w/ pitch values will follow        
        self.pitchValues = []


    def parse(self):
        '''Parse a scala file delivered as a long string with line breaks
        '''
        self.src = fileString
        lines = self.src.split('\n')
        
    






class ScalaFile(object):
    '''
    Scala File access

    '''
    
    def __init__(self): 
        pass

    def open(self, filename): 
        '''Open a file for reading
        '''
        self.file = codecs.open(filename, encoding='utf-8')
        self.filename = filename

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an open file object.

        >>> fileLikeOpen = StringIO.StringIO()
        '''
        self.file = fileLike # already 'open'
    
    def __repr__(self): 
        r = "<ScalaFile>" 
        return r 
    
    def close(self): 
        self.file.close() 
    
    def read(self, number=None): 
        '''Read a file. Note that this calls readstring, which processes all tokens. 

        If `number` is given, a work number will be extracted if possible. 
        '''
        return self.readstr(self.file.read()) 

    def readstr(self, strSrc): 
        '''Read a string and process all Tokens. Returns a ABCHandler instance.
        '''
        handler = ABCHandler()
        # return the handler instance
        handler.process(strSrc)
        return handler
    





#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testSingle(self):
        a = Pitch()
        a.name = 'c#'
        a.show()



class Test(unittest.TestCase):
    
    def runTest(self):
        pass






#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof






