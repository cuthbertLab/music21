#-------------------------------------------------------------------------------
# Name:         romanText/translate.py
# Purpose:      Translation routines for roman numeral analysis text files
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''Translation routines for roman numeral analysis text files, as defined and demonstrated by Dmitri Tymoczko.
'''
import unittest
import music21
import copy


from music21.romanText import base as romanTextModule

from music21 import environment
_MOD = 'romanText.translate.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class TranslateRomanTextException(Exception):
    pass



def romanTextToStreamScore(rtHandler, inputM21=None):
    '''Given a roman text handler, return or fill a Score Stream.
    '''
    # this could be just a Stream, but b/c we are creating metadata, perhaps better to match presentation of other scores. 

    from music21 import metadata
    from music21 import stream
    from music21 import note
    from music21 import meter
    from music21 import key
    from music21 import roman
    from music21 import tie


    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    # metadata can be first
    md = metadata.Metadata()
    s.insert(0, md)

    p = stream.Part()
    # ts indication are found in header, and also found elsewhere
    tsCurrent = None # store initial time signature
    tsSet = False # store if set to a measure
    lastMeasureNumber = 0
    previousRn = None
    kCurrent = None # key is set inside of measure

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
            if t.variantNumber is not None:
                environLocal.printDebug(['skipping variant: %s' % t])
                continue
            # if this measure number is more than 1 greater than the last
            # defined measure number, and the previous chord is not None, 
            # then fill with copies of the last-defined measure
            if ((t.number[0] > lastMeasureNumber + 1) and 
                (previousRn is not None)):
                for i in range(lastMeasureNumber + 1, t.number[0]):
                    mFill = stream.Measure()
                    mFill.number = i
                    newRn = copy.deepcopy(previousRn)
                    newRn.lyric = ""
                    # set to entire bar duration and tie 
                    newRn.duration = copy.deepcopy(tsCurrent.barDuration)
                    if previousRn.tie == None:
                        previousRn.tie = tie.Tie('start')
                    else:
                        previousRn.tie.type = 'continue'
                    # set to stop for now; may extend on next iteration
                    newRn.tie = tie.Tie('stop')
                    previousRn = newRn
                    mFill.append(newRn)
                    p.append(mFill)
                lastMeasureNumber = t.number[0] - 1
            # create a new measure or copy a past measure
            if len(t.number) == 1: # if not a range
                if not t.isCopyDefinition:
                    m = stream.Measure()
                else: # copy from a past location; need to change key
                    targetNumber, targetRepeat = t.getCopyTarget()
                    if len(targetNumber) > 1: # this is an encoding error
                        raise TranslateRomanTextException('a single measure cannot define a copy operation for multiple measures')
                    # TODO: ignoring repeat letters
                    target = targetNumber[0]
                    for mPast in p.getElementsByClass('Measure'):
                        if mPast.number == target:
                            m = copy.deepcopy(mPast)
                            # update all keys
                            for rnPast in m.getElementsByClass('RomanNumeral'):
                                if kCurrent is None: # should not happen
                                    raise TranslateRomanTextException('attempting to copy a measure but no past key definitions are found')
                                rnPast.setKeyOrScale(kCurrent)
                            break
                m.number = t.number[0]
                lastMeasureNumber = t.number[0]
            else: # TODO: copy a range of measure; 
                # the key provided needs to be the current key
                lastMeasureNumber = t.number[1]
                environLocal.printDebug(['cannot yet handle measure tokens defining measure ranges: %s' % t.number])

            if not tsSet:
                m.timeSignature = tsCurrent
                tsSet = True # only set when changed

            o = 0.0 # start offsets at zero
            previousChordInMeasure = None
            for i, a in enumerate(t.atoms):
                if isinstance(a, romanTextModule.RTKey):
                    kCurrent = a.getKey()

                if isinstance(a, romanTextModule.RTBeat):
                    # set new offset based on beat
                    o = a.getOffset(tsCurrent)
                    if (previousChordInMeasure is None and 
                        previousRn is not None):
                        # setting a new beat before giving any chords
                        firstChord = copy.deepcopy(previousRn)
                        firstChord.quarterLength = o
                        firstChord.lyric = ""
                        if previousRn.tie == None:
                            previousRn.tie = tie.Tie('start')
                        else:
                            previousRn.tie.type = 'continue'    
                        firstChord.tie = tie.Tie('stop')
                        previousRn = firstChord
                        previousChordInMeasure = firstChord
                        m.insert(0, firstChord)
                        
                if isinstance(a, romanTextModule.RTChord):
                    # probably best to find duration
                    if previousChordInMeasure is None:
                        pass # use default duration
                    else: # update duration of previous chord in Measure
                        oPrevious = previousChordInMeasure.getOffsetBySite(m)
                        previousChordInMeasure.quarterLength = o - oPrevious
                    # use source to evaluation roman 
                    try:
                        rn = roman.RomanNumeral(a.src, kCurrent)
                    except:
                        environLocal.printDebug('cannot create RN from: %s' % a.src)
                        rn = note.Note() # create placeholder 
                    rn.addLyric(a.src)
                    m.insert(o, rn)
                    previousChordInMeasure = rn
                    previousRn = rn
            # may need to adjust duration of last chord added
            previousRn.quarterLength = tsCurrent.barDuration.quarterLength - o
            p.append(m)
    p.makeBeams()
    s.insert(0,p)
    return s


def romanTextStringToStreamScore(rtString, inputM21=None):
    '''Convenience routine for geting a score from string, not a handler
    '''
    # create an empty file obj to get handler from string
    rtf = romanTextModule.RTFile()
    rth = rtf.readstr(rtString) # return handler, processes tokens
    s = romanTextToStreamScore(rth, inputM21=inputM21)
    return s


#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
 
    def testExternalA(self):
        from music21 import romanText
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = romanText.RTFile()
            rth = rtf.readstr(tf) # return handler, processes tokens
            s = romanTextToStreamScore(rth)
            s.show()


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

        s = romanTextStringToStreamScore(testFiles.monteverdi_3_13)
        self.assertEqual(s.metadata.composer, 'Claudio Monteverdi')

    def testBasicB(self):
        from music21 import romanText
        from music21.romanText import testFiles

        s = romanTextStringToStreamScore(testFiles.riemenschneider001)
        #s.show()

    def testMeasureCopying(self):
        from music21 import romanText
        from music21.romanText import testFiles

        s = romanTextStringToStreamScore(testFiles.swv23)
        mStream = s.parts[0].getElementsByClass('Measure')
        # the first four measures should all have the same content
        rn1 = mStream[1].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.pitches), '[D5, F#5, A5]')
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[1].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')

        # make sure that m2, m3, m4 have the same values
        rn1 = mStream[2].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[2].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')

        rn1 = mStream[3].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[3].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()

#------------------------------------------------------------------------------
# eof
