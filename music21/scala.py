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
Classes and functions for representing data in a Scala scale representation file format as defined here:

http://www.huygens-fokker.org/scala/scl_format.html
'''

import os
import unittest, doctest
import math
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
    >>> sp.parse('100.0 C#')
    100.0
    >>> [sp.parse(x) for x in ['89/84', '55/49', '44/37', '63/50', '4/3', '99/70', '442/295', '27/17', '37/22', '98/55', '15/8', '2/1']]
    [100.09920982..., 199.9798432913..., 299.973903610..., 400.108480470..., 498.044999134..., 600.08832376157..., 699.9976981706..., 800.90959309..., 900.02609638..., 1000.020156708..., 1088.268714730..., 1200.0]
    '''

    # pitch values; if has a period, is cents, otherwise a ratio
    # above the implied base ratio
    # integer values w/ no period or slash: 2 is 2/1

    def __init__(self, sourceString=None):

        self.src = None
        if sourceString is not None:
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
            # http://www.sengpielaudio.com/calculator-centsratio.htm
            self.cents = 1200.0 * math.log((n / d), 2)
        return self.cents




class ScalaScale(object):
    '''Object representation of data stored in a Scale scale file.
    '''
    def __init__(self, sourceString=None, fileName=None):
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
        lines = self.src.split('\n')
        count = 0 # count non-comment lines
        for i, l in enumerate(lines):
            l = l.strip()
            #environLocal.printDebug(['l', l, self.fileName, i])
            if l.startswith('!'):
                if i == 0 and self.fileName is None: # try to get from first l      
                    if '.scl' in l: # its got the file name 
                        self.fileName = l[1:].strip() # remove leading !
                continue # comment
            else:
                count += 1
            if count == 1: # 
                if l != '': # may be empty
                    self.description = l
            elif count == 2:
                if l != '':
                    self.noteCount = int(l)
            else: # remaining counts are pitches
                if l != '':
                    sp = ScalaPitch(l)
                    sp.parse()
                    self.pitchValues.append(sp)
  
    def getCentsAboveTonic(self):
        '''Return a list of cent values above the implied tonic.
        '''
        return [sp.cents for sp in self.pitchValues]    
    

    def getAdjacentCents(self):
        '''Get cents values between adjacent intervals.
        '''
        post = []
        location = 0
        for c in self.getCentsAboveTonic():
            dif = c - location
            #environLocal.printDebug(['getAdjacentCents', 'c', c, 'location', location, 'dif', dif])
            post.append(dif)
            location = c # set new location
        return post

    def setAdjacentCents(self, centList):
        '''Given a list of adjacent cent values, create the necessary ScalaPitch  objects and update the 
        '''
        self.pitchValues = []
        location = 0
        for c in centList:
            sp = ScalaPitch()
            sp.cents = location + c
            location = sp.cents
            self.pitchValues.append(sp)
        self.noteCount = len(self.pitchValues)


    def getFileString(self):
        '''Return a string suitable for writing a Scale file
        '''
        msg = []
        if self.fileName is not None:
            msg.append('! %s' % self.fileName)
        # conventional to add a comment space
        msg.append('!')

        if self.description is not None:
            msg.append(self.description)
        else: # must supply empty line
            msg.append('')

        if self.noteCount is not None:
            msg.append(str(self.noteCount))
        else: # must supply empty line
            msg.append('')
    
        # conventional to add a comment space
        msg.append('!')
        for sp in self.pitchValues:
            msg.append(str(sp.cents))
        # add space
        msg.append('') 

        return '\n'.join(msg)





class ScalaFile(object):
    '''
    Scala File access

    '''
    
    def __init__(self, data=None): 
        self.fileName = None
        self.file = None
        # store data source if provided
        self.data = data

    def open(self, fp, mode='r'): 
        '''Open a file for reading
        '''
        self.file = codecs.open(fp, mode, encoding='utf-8')
        self.fileName = os.path.basename(fp)

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
    
    def read(self): 
        '''Read a file. Note that this calls readstring, which processes all tokens. 

        If `number` is given, a work number will be extracted if possible. 
        '''
        return self.readstr(self.file.read()) 

    def readstr(self, strSrc): 
        '''Read a string and process all Tokens. Returns a ABCHandler instance.
        '''
        ss = ScalaScale(strSrc, self.fileName)
        ss.parse()
        self.data = ss
        return ss

    def write(self): 
        ws = self.writestr()
        self.file.write(ws) 
    
    def writestr(self): 
        if isinstance(self.data, ScalaScale):
            return self.data.getFileString()
        # handle Scale or other objects
        




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

    def testScalaScaleA(self):
        msg = '''! slendro5_2.scl
!
A slendro type pentatonic which is based on intervals of 7, no. 2               
 5
!
 7/6
 4/3
 3/2
 7/4
 2/1
'''
        ss = ScalaScale(msg)
        ss.parse()
        self.assertEqual(ss.noteCount, 5)
        self.assertEqual(ss.fileName, 'slendro5_2.scl')
        self.assertEqual(len(ss.pitchValues), 5)
        self.assertEqual([str(x.cents) for x in ss.pitchValues], ['266.870905604', '498.044999135', '701.955000865', '968.825906469', '1200.0'])

        self.assertEqual([str(x) for x in ss.getCentsAboveTonic()], ['266.870905604', '498.044999135', '701.955000865', '968.825906469', '1200.0'])
        # sent values between scale degrees
        self.assertEqual([str(x) for x in ss.getAdjacentCents()], ['266.870905604', '231.174093531', '203.910001731', '266.870905604', '231.174093531'] )


    def testScalaScaleB(self):
        msg = '''! fj-12tet.scl
!  
Franck Jedrzejewski continued fractions approx. of 12-tet 
 12
!  
89/84
55/49
44/37
63/50
4/3
99/70
442/295
27/17
37/22
98/55
15/8
2/1

'''
        ss = ScalaScale(msg)
        ss.parse()
        self.assertEqual(ss.noteCount, 12)
        self.assertEqual(ss.fileName, 'fj-12tet.scl')
        self.assertEqual(ss.description, 'Franck Jedrzejewski continued fractions approx. of 12-tet')

        self.assertEqual([str(x) for x in ss.getCentsAboveTonic()], ['100.099209825', '199.979843291', '299.97390361', '400.10848047', '498.044999135', '600.088323762', '699.997698171', '800.909593096', '900.02609639', '1000.02015671', '1088.26871473', '1200.0'])

        self.assertEqual([str(x) for x in ss.getAdjacentCents()], ['100.099209825', '99.8806334662', '99.9940603187', '100.13457686', '97.9365186644', '102.043324627', '99.9093744091', '100.911894925', '99.1165032942', '99.9940603187', '88.2485580216', '111.73128527'])

        # test loading a new scala object from adjacent sets
        ss2 = ScalaScale()
        ss2.setAdjacentCents(ss.getAdjacentCents())
        
        self.assertEqual([str(x) for x in ss2.getCentsAboveTonic()], ['100.099209825', '199.979843291', '299.97390361', '400.10848047', '498.044999135', '600.088323762', '699.997698171', '800.909593096', '900.02609639', '1000.02015671', '1088.26871473', '1200.0'])


    def testScalaFileA(self):
        
        msg = '''! arist_chromenh.scl
!
Aristoxenos' Chromatic/Enharmonic, 3 + 9 + 18 parts
 7
!
 50.00000
 200.00000
 500.00000
 700.00000
 750.00000
 900.00000
 2/1
'''
        sf = ScalaFile()
        ss = sf.readstr(msg)
        self.assertEqual(ss.noteCount, 7)
        
        # all but last will be the same
        #print ss.getFileString()
        self.assertEqual(ss.getFileString()[:1], msg[:1])




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof






