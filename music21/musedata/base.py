#-------------------------------------------------------------------------------
# Name:         musedata.base.py
# Purpose:      music21 classes for dealing with MuseData
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Objects and resources for processing MuseData. 

MuseData conversion from a file or URL to a :class:`~music21.stream.Stream` is available through the music21 converter module's :func:`~music21.converter.parse` function. 

>>> #_DOCS_SHOW from music21 import *
>>> #_DOCS_SHOW abcScore = converter.parse('d:/data/musedata/myScore.stage2')

Low level MuseData conversion is facilitated by the objects in this module and :func:`music21.musedata.translate.museDataToStreamScore`.
'''

import music21
import unittest
import re, codecs

try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)


from music21 import common
from music21 import environment
_MOD = 'musedata.base.py'
environLocal = environment.Environment(_MOD)

# for implementation
# see http://www.ccarh.org/publications/books/beyondmidi/online/musedata/


#-------------------------------------------------------------------------------
# note inclusion of w: for lyrics
reMetadataTag = re.compile('[KQTCXSID][0-9]?:')

rePitchName = re.compile('[A-Gr]')

#reChordSymbol = re.compile('"[^"]*"') # non greedy

#reChord = re.compile('[.*?]') # non greedy



#-------------------------------------------------------------------------------
class MuseDataTokenException(Exception):
    pass

class MuseDataHandlerException(Exception):
    pass

class MuseDataFile(object):
    '''
    
    '''
    def __init__(self, data = ""):
        self.data = data
    
    def __repr__(self):
        return '<music21.musedata.MuseDataFile %d>' % self.id()
    
    def toStream(self):
        return self.stream
    



#-------------------------------------------------------------------------------
# class ABCFile(object):
#     '''
#     ABC File access
# 
#     '''
#     
#     def __init__(self): 
#         pass
# 
#     def open(self, filename): 
#         '''Open a file for reading
#         '''
#         #try:
#         self.file = codecs.open(filename, encoding='utf-8')
#         #exce[t
#         #self.file = open(filename, 'r') 
#         self.filename = filename
# 
#     def openFileLike(self, fileLike):
#         '''Assign a file-like object, such as those provided by StringIO, as an open file object.
# 
#         >>> fileLikeOpen = StringIO.StringIO()
#         '''
#         self.file = fileLike # already 'open'
#     
#     def __repr__(self): 
#         r = "<ABCFile>" 
#         return r 
#     
#     def close(self): 
#         self.file.close() 
#     
#     def read(self): 
#         return self.readstr(self.file.read()) 
#     
#     def readstr(self, str): 
#         '''Read a string and process all Tokens. Returns a ABCHandler instance.
#         '''
#         handler = ABCHandler()
#         # return the handler instanc
#         handler.process(str)
#         return handler
#     
# #     def write(self): 
# #         ws = self.writestr()
# #         self.file.write(ws) 
# #     
# #     def writestr(self): 
# #         pass
# 
# 








#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()

        #t.testNoteParse()






