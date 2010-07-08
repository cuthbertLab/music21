#-------------------------------------------------------------------------------
# Name:         layout.py
# Purpose:      Layout objects 
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Layout objects provide models of various forms of page or other musical layouts. Layout objects may be used like other :class:`~music21.base.Music21Object` and placed on a :class:`~music21.stream.Stream`.
'''


# layout objects suggested by musicxml

# Defaults:
# PageLayout
# SystemLayout
# StaffLayout

# may need to have object to convert between size units

import string, copy, math
import unittest, doctest

import music21


#-------------------------------------------------------------------------------

class SystemLayout(music21.Music21Object):
    '''Parameters for configureing a system's layout.

    SystemLayout objects may be found on Measure or Part Streams.    

    >>> sl = SystemLayout(leftmargin=234, rightmargin=124, distance=3)
    >>> sl.distance
    3
    >>> sl.rightMargin
    124
    >>> sl.leftMargin
    234

    '''
    def __init__(self, *args, **keywords):
        music21.Music21Object.__init__(self)
        
        self.leftMargin = None
        self.rightMargin = None

        # this is probably the distance between adjacent systems
        # musicxml also defines a top-system-distance tag; this may not be
        # necessary to implements, as the top system is defined by context
        self.distance = None


        for key in keywords.keys():
            if key.lower() == 'leftmargin':
                self.leftMargin = keywords[key]
            if key.lower() == 'rightmargin':
                self.rightMargin = keywords[key]
            if key.lower() == 'distance':
                self.distance = keywords[key]









#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testPass(self):
        pass



#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        #a.testNoteBeatPropertyCorpus()


