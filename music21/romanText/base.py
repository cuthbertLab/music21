#-------------------------------------------------------------------------------
# Name:         romanText/base.py
# Purpose:      music21 classes for processing roman numeral analysis text files
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''Objects for processing roman numeral analysis text files, as defined and demonstrated by Dmitri Tymoczko.
'''

import unittest
import re
try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)


import music21

from music21 import common
from music21 import environment
_MOD = 'romanText.base.py'
environLocal = environment.Environment(_MOD)


# alternate endings might end with a,b,c for non 
# zero or more for everything after the first number
reMeasureTag = re.compile('m[0-9]+[a-b]*-*[0-9]*[a-b]*')



#-------------------------------------------------------------------------------
class RTTokenException(Exception):
    pass
class RTHandlerException(Exception):
    pass
class RTFileException(Exception):
    pass



#-------------------------------------------------------------------------------
class RTToken(object):
    '''
    Stores each linear, logical entity of a RomanText.

    A multi-pass parsing procedure is likely necessary, as RomanText permits variety of groupings and markings.

    '''
    def __init__(self, src=u''):
        self.src = src # store source character sequence

    def __repr__(self):
        return '<RomanTextoken %r>' % self.src





class RTHeader(RTToken):

    def __init__(self, src =u''):
        RTToken.__init__(self, src)
        # try to split off tag from data
        self.tag = ''
        self.data = ''
        if ':' in src:
            iFirst = src.find(':') # first index found at
            self.tag = src[:iFirst].strip()
            # add one to skip colon
            self.data = src[iFirst+1:].strip()
        else: # we do not have a clear tag; perhaps store all as data
            self.data = src

    def __repr__(self):
        return '<RTHeader %r>' % self.src


    def isComposer(self):
        '''
        >>> from music21 import *
        >>> rth = romanText.RTHeader('Composer: Claudio Monteverdi')
        >>> rth.isComposer()
        True
        >>> rth.isTitle()
        False
        >>> rth.isWork()
        False
        >>> rth.data 
        'Claudio Monteverdi'
        '''
        if self.tag.lower() in ['composer']:
            return True
        return False

    def isTitle(self):
        if self.tag.lower() in ['title']:
            return True
        return False

    def isAnalyst(self):
        if self.tag.lower() in ['analyst']:
            return True
        return False

    def isProofreader(self):
        if self.tag.lower() in ['proofreader', 'proof reader']:
            return True
        return False

    def isTimeSignature(self):
        if self.tag.lower() in ['timesignature', 'time signature']:
            return True
        return False

    def isWork(self):
        '''The work is not defined as a header tag, but is used to represent all tags, often placed after Composer, for the work or pieces designation. 

        >>> from music21 import *
        >>> rth = romanText.RTHeader('Madrigal: 4.12')
        >>> rth.isTitle()
        False
        >>> rth.isWork()
        True
        >>> rth.tag
        'Madrigal'
        >>> rth.data 
        '4.12'

        '''
        if not self.isComposer() and not self.isTitle() and not self.isAnalyst() and not self.isProofreader() and not self.isTimeSignature():
            return True
        return False



#-------------------------------------------------------------------------------
class RTHandler(object):

    # divide elements of a character stream into objects and handle
    # store in a list, and pass global information to compontns
    def __init__(self):
        # tokens are ABC objects in a linear stream
        # tokens are strongly divided between header and body, so can 
        # divide here
        self._tokensHeader = []
        self._tokensBody = []


    def _splitAtHeader(self, lines):
        '''Divide string into header and non-header.

        >>> from music21 import *
        >>> rth = romanText.RTHandler()
        >>> rth._splitAtHeader(['Title: s', 'Time Signature:', '', 'm1 g: i'])
        (['Title: s', 'Time Signature:', ''], ['m1 g: i'])

        '''
        # iterate over lines and fine the first measure definition
        for i, l in enumerate(lines):
            if reMeasureTag.match(l.strip()) is not None:
                # found a measure definition
                iStartBody = i
                break
        return lines[:iStartBody], lines[iStartBody:]
    
    def _tokenizeHeader(self, lines):
        for l in lines:
            l = l.strip()
            if l == '': continue
            # wrap each line in a header token
            self._tokensHeader.append(RTHeader(l))

    def tokenize(self, src):
        '''Walk the RT string, creating RT objects along the way.
        '''
        # break into lines
        lines = src.split('\n')
        linesHeader, linesBody = self._splitAtHeader(lines)
        #environLocal.printDebug([linesHeader])
        
        # this will fill self._tokensHeader
        self._tokenizeHeader(linesHeader)        

    def process(self, src):
        '''Given an entire specification as a single source string, strSrc. This is usually provided in a file. 
        '''
        self._tokensBody = []
        self.tokenize(src)

    def getBodyTokens(self):
        if len(self._tokensBody) == 0:
            raise RTHandlerException('no body tokens defined')
        return self._tokensBody

    def getHeaderTokens(self):
        if len(self._tokensHeader) == 0:
            raise RTHandlerException('no header tokens defined')
        return self._tokensHeader


#-------------------------------------------------------------------------------
class RTFile(object):
    '''
    Roman Text File access
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
        r = "<RTFile>" 
        return r 
    
    def close(self): 
        self.file.close() 
    
    def read(self, number=None): 
        '''Read a file. Note that this calls readstring, which processes all tokens. 

        If `number` is given, a work number will be extracted if possible. 
        '''
        return self.readstr(self.file.read(), number) 
    
    def readstr(self, strSrc): 
        '''Read a string and process all Tokens. Returns a ABCHandler instance.
        '''
        handler = RTHandler()
        # return the handler instanc
        handler.process(strSrc)
        return handler
    



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    

    def testBasicA(self):
        from music21.romanText import testFiles
        from music21 import romanText

        for fileStr in testFiles.ALL:
            f = romanText.RTFile()
            rth = f.readstr(fileStr) # get a handler from a string

    def testReA(self):
        # gets the index of the end of the measure indication
        g = reMeasureTag.match('m1 g: V b2 i')
        self.assertEqual(g.end(), 2)
        self.assertEqual(g.group(0), 'm1')

        self.assertEqual(reMeasureTag.match('Time Signature: 2/2'), None)

        g = reMeasureTag.match('m3-4=m1-2')
        self.assertEqual(g.end(), 4)
        self.assertEqual(g.start(), 0)
        self.assertEqual(g.group(0), 'm3-4')

        g = reMeasureTag.match('m123-432=m1120-24234')
        self.assertEqual(g.group(0), 'm123-432')

        g = reMeasureTag.match('m231a IV6 b4 C: V')
        self.assertEqual(g.group(0), 'm231a')

        g = reMeasureTag.match('m123b-432b=m1120a-24234a')
        self.assertEqual(g.group(0), 'm123b-432b')





#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()

#------------------------------------------------------------------------------
# eof




