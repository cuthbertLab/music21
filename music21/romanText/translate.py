#-------------------------------------------------------------------------------
# Name:         romanText/translate.py
# Purpose:      Translation routines for roman numeral analysis text files
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''Translation routines for roman numeral analysis text files, as defined and demonstrated by Dmitri Tymoczko.
'''
import unittest
import music21



from music21.romanText import base as romanTextModule

from music21 import environment
_MOD = 'romanText.translate.py'
environLocal = environment.Environment(_MOD)



def romanTextToStreamScore(rtHandler, inputM21=None):
    '''Given a roman text handler, return or fill a Score Stream.
    '''
    # this could be just a Stream, but b/c we are creating metadata, perhaps better to match presentation of other scores. 

    from music21 import metadata
    from music21 import stream
    from music21 import note
    from music21 import meter
    from music21 import key
    from music21 import chord



    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    # meta data can be first
    md = metadata.Metadata()
    s.insert(0, md)

    p = stream.Part()
    # ts indication are found in header, and also found elsewhere
    tsCurrent = None # store initial time signature
    tsSet = False # store if set to a measure

    for t in rtHandler.tokens:
        if t.isTitle():
            md.title = t.data            
        elif t.isWork():
            md.alternativeTitle = t.data
        elif t.isComposer():
            md.composer = t.data
        elif t.isTimeSignature():
            tsCurrent = meter.TimeSignature(t.data)
            tsSet = False
            environLocal.printDebug(['tsCurrent:', tsCurrent])
            
        elif t.isMeasure():
            # pass this off to measure creation tools
            m = stream.Measure()
            if not tsSet:
                m.timeSignature = ts
                tsSet = True # only set when changed

            if len(t.number) == 1: # if not a range
                m.number = t.number[0]
            else:
                environLocal.printDebug(['cannot yet handle measure tokens defining measure ranges: %s' % t.number])
            for i, a in enumerate(t.atoms):
                pass
                #print a
            #print 
        # need to get time signature here
    
    return s


def romanTextStringToStreamScore(rtString, inputM21=None):
    '''Convenience routine for geting a score from string
    '''
    # create an empty file obj to get handler from string
    rtf = romanTextModule.RTFile()
    rth = rtf.readstr(rtString) # return handler, processes tokens
    s = romanTextToStreamScore(rth, inputM21=inputM21)
    return s


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    

    def testBasicA(self):
        from music21 import romanText
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = romanText.RTFile()
            rth = rtf.readstr(tf) # return handler, processes tokens
            s = romanTextToStreamScore(rth)
            #s.show()

        
        s = romanTextStringToStreamScore(testFiles.swv23)
        self.assertEqual(s.metadata.composer, 'Heinrich Schutz')
        # this is defined as a Piece tag, but shows up here as a title, after
        # being set as an alternate title
        self.assertEqual(s.metadata.title, 'Warum toben die Heiden, Psalmen Davids no. 2, SWV 23')
        

        s = romanTextStringToStreamScore(testFiles.riemenschneider001)
        self.assertEqual(s.metadata.composer, 'J. S. Bach')
        self.assertEqual(s.metadata.title, 'Aus meines Herzens Grunde')

        s = romanTextStringToStreamScore(testFiles.monteverdi_4_12)
        self.assertEqual(s.metadata.composer, 'Claudio Monteverdi')



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
