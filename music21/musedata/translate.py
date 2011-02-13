#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         musedata.translate.py
# Purpose:      Translate MuseData into music21 objects
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Functions for translating music21 objects and 
:class:`~music21.musedata.base.MuseDataHandler` instances. Mostly, 
these functions are for advanced, low level usage. For basic importing of MuseData
files from a file or URL to a :class:`~music21.stream.Stream`, use the music21 
converter module's :func:`~music21.converter.parse` function. 
'''


import music21
import unittest

from music21.musedata import base as museDataModule

from music21 import environment
_MOD = 'musedata.translate.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class MuseDataTranslateException(Exception):
    pass


def _musedataBeamToBeams(beamSymbol):
    '''Given a musedata beam symbol, converter to a music21 Beams object representation. 

    >>> from music21.musedata import translate
    >>> translate._musedataBeamToBeams('[[')
    <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
    >>> translate._musedataBeamToBeams('===')
    <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>/<music21.beam.Beam 3/continue>>

    >>> translate._musedataBeamToBeams(r']/') # must escape backslash
    <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/partial/right>>

    '''
    from music21 import beam

    beamsObj = beam.Beams()

    # assume that we are starting with 8th, even if given as a space
    for char in beamSymbol:
        direction = None
        if char == '[':
            type='start'
        elif char == ']':
            type='stop'
        elif char == '=':
            type='continue'
        elif char == '/': # forward is right
            type='partial'
            direction='right'
        elif char == '\\' or char == r'\\': # backward is left
            type='partial'
            direction='left'
        else:
            raise MuseDataTranslateException('cannot interpreter beams char:' % char)

        # will automatically increment number        
        # note that this does not permit defining 16th and not defining 8th
        beamsObj.append(type, direction)

    return beamsObj


def _musedataRecordListToNoteOrChord(records, previousElement=None):
    '''Given a list of MuseDataRecord objects, return a configured
    :class:`~music21.note.Note` or :class:`~music21.chord.Chord`.

    Optionally pass a previous element, which may be music21 Note, Chord, or Rest; this is used to determine tie status
    '''
    from music21 import note
    from music21 import chord
    from music21 import tie

    if len(records) == 1:
        post = note.Note()
        # directly assign pitch object; will already have accidental
        post.pitch = records[0].getPitchObject()
    else:
        #environLocal.printDebug(['attempting chord creation: records', len(records)])
        # can supply a lost of Pitch objects at creation
        post = chord.Chord([r.getPitchObject() for r in records])

    # if a chord, we are assume that all durations are the same
    post.quarterLength = records[0].getQuarterLength()

    # see if there are nay lyrics; not sure what to do if lyrics are defined
    # for multiple chord tones
    lyricList = records[0].getLyrics()
    if lyricList is not None:
        # cyclicalling addLyric will auto increment lyric number assinged
        for lyric in lyricList:
            post.addLyric(lyric)

    # see if there are any beams; again, get from first record only
    beamsChars = records[0].getBeams()
    if beamsChars is not None:
        post.beams = _musedataBeamToBeams(beamsChars)
 
    # presently this sets a single tie for a chord; may be different cases
    if records[0].isTied():
        post.tie = tie.Tie('start') # can be start or continue;
        if previousElement != None and previousElement.tie != None:
            # if previous is a start or a continue; this has to be a continue
            # as musedata does not mark the end of a tie
            if previousElement.tie.type in ['start', 'continue']:
                post.tie = tie.Tie('continue') 
    else: # if no tie indication in the musedata record
        if previousElement != None and previousElement.tie != None:
            if previousElement.tie.type in ['start', 'continue']:
                post.tie = tie.Tie('stop') # can be start, end, continue
    return post



def _processPending(hasVoices, pendingRecords, eLast, m, vActive):
    e = _musedataRecordListToNoteOrChord(pendingRecords, eLast)
    if hasVoices:
        vActive.append(e)
    else:
        m.append(e)
    return e

def musedataPartToStreamPart(museDataPart, inputM21=None):
    '''Translate a musedata part to a :class:`~music21.stream.Part`.
    '''
    from music21 import stream
    from music21 import meter
    from music21 import key
    from music21 import note

    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    p = stream.Part()
    p.id = museDataPart.getPartName()

    # create and store objects
    mdmObjs = museDataPart.getMeasures()

    #environLocal.printDebug(['first measure parent', mdmObjs[0].parent])

    barCount = 0
    # get each measure
    # store last Note/Chord/Rest for tie comparisons; span measures
    eLast = None
    for mIndex, mdm in enumerate(mdmObjs):
        #environLocal.printDebug(['processing:', mdm.src])
        if not mdm.hasNotes():
            continue

        if mdm.hasVoices():
            hasVoices = True
            vActive = stream.Voice()
        else:
            hasVoices = False
            vActive = None

        #m = stream.Measure()
        # get a measure object with a left configured bar line
        if mIndex <= len(mdmObjs) - 2:
            mdmNext = mdmObjs[mIndex+1]
        else:
            mdmNext = None

        m = mdm.getMeasureObject()

        # conditions for a final measure definition defining the last bar
        if mdmNext != None and not mdmNext.hasNotes():
            #environLocal.printDebug(['got mdmNext not none and not has notes'])
            # get bar from next measure definition
            m.rightBarline = mdmNext.getBarObject()

        if barCount == 0: # only for first
            # the parent of the measure is the part
            c = mdm.parent.getClefObject()
            if c != None:
                m.clef = mdm.parent.getClefObject()
            m.timeSignature = mdm.parent.getTimeSignatureObject()
            m.keySignature = mdm.parent.getKeySignature()

        # get all records; may be notes or note components
        mdrObjs = mdm.getRecords()
        # store pairs of pitches and durations for chording after a
        # new note has been found
        pendingRecords = [] 

        # get notes in each record        
        for i in range(len(mdrObjs)):
            mdr = mdrObjs[i]
            #environLocal.printDebug(['processing:', mdr.src])

            if mdr.isBack():
                # the current use of back assumes tt back assumes tt we always
                # return to the start of the measure; this may not be the case
                if pendingRecords != []:
                    eLast = _processPending(hasVoices, pendingRecords, eLast, m, vActive)
                    pendingRecords = []

                # every time we encounter a back, we need to store
                # our existing voice and create a new one
                m.insert(0, vActive)
                vActive = stream.Voice()

            if mdr.isRest():
                #environLocal.printDebug(['got mdr rest, parent:', mdr.parent])
                # check for pending records first
                if pendingRecords != []:
                    eLast = _processPending(hasVoices, pendingRecords, eLast, m, vActive)
#                     e = _musedataRecordListToNoteOrChord(pendingRecords,
#                         eLast)
#                     if hasVoices:
#                         vActive.append(e)
#                     else:
#                         m.append(e)
#                     eLast = e
                    pendingRecords = []
                # create rest after clearing pending records
                r = note.Rest()
                r.quarterLength = mdr.getQuarterLength()
                if hasVoices:
                    vActive.append(r)
                else:
                    m.append(r)
                eLast = r
                continue
            # a note is note as chord, but may have chord tones
            # attached to it that follow
            elif mdr.isChord():
                # simply append if a chord; do not clear or change pending
                pendingRecords.append(mdr)

            elif mdr.isNote():
                # either this is a note alone, or this is the first
                # note found that is not a chord; if first not a chord
                # need to append immediately
                if pendingRecords != []:
                    # this could be a Chord or Note
                    eLast = _processPending(hasVoices, pendingRecords, eLast, m, vActive)
#                     e = _musedataRecordListToNoteOrChord(pendingRecords, eLast)
#                     if hasVoices:
#                         vActive.append(e)
#                     else:
#                         m.append(e)
#                     eLast = e
                    pendingRecords = []
                # need to append this record for the current note
                pendingRecords.append(mdr)

        # check for any remaining single notes (if last) or chords
        if pendingRecords != []:
#             e = _musedataRecordListToNoteOrChord(pendingRecords, eLast)
#             if hasVoices:
#                 vActive.append(e)
#             else:
#                 m.append(e)
#             eLast = e
            eLast = _processPending(hasVoices, pendingRecords, eLast, m, vActive)

        # may be bending elements in a voice to append to a measure
        if vActive is not None and len(vActive) > 0:
            m.insert(0, vActive)

        if barCount == 0 and m.timeSignature != None: # easy case
            # can only do this b/c ts is defined
            if m.barDurationProportion() < 1.0:
                m.padAsAnacrusis()
                environLocal.printDebug(['incompletely filled Measure found on musedata import; interpreting as a anacrusis:', 'padingLeft:', m.paddingLeft])
        p.append(m)
        barCount += 1

    # for now, make all imports a c-score on import; 
    tInterval = museDataPart.getTranspositionIntervalObject()
    #environLocal.printDebug(['got transposition interval', p.id, tInterval])
    if tInterval is not None:
        p.flat.transpose(tInterval, 
                        classFilterList=['Note', 'Chord', 'KeySignature'],
                        inPlace=True)
        # need to call make accidentals to correct new issues
        p.makeAccidentals()

    if museDataPart.stage == 1:
        # cannot yet get stage 1 clef data
        p.getElementsByClass('Measure')[0].clef = p.flat.bestClef()
        p.makeBeams()
        # will call overridden method on Part
        p.makeAccidentals()
    # assume that beams and clefs are defined in all stage 2
   
    s.insert(0, p)
    return s


def museDataWorkToStreamScore(museDataWork, inputM21=None):
    '''Given an museDataWork object, build into a multi-part :class:`~music21.stream.Score` with metadata.

    This assumes that this MuseDataHandler defines a single work (with 1 or fewer reference numbers). 
    
    if the optional parameter inputM21 is given a music21 Stream subclass, it will use that object
    as the outermost object.  However, inner parts will always be made :class:`~music21.stream.Part` objects.
    '''
    from music21 import stream
    from music21 import metadata

    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    # each musedata part has complete metadata, so must get first
    mdpObjs = museDataWork.getParts()

    md = metadata.Metadata()
    s.insert(0, md)

    md.title = mdpObjs[0].getWorkTitle()
    md.movementNumber = mdpObjs[0].getMovementNumber()
    md.movementName = mdpObjs[0].getMovementTitle()

    # not obvious where composer is stored
    #md.composer = mdpObjs[0].getWorkNumber()
    #md.localeOfComposition = mdpObjs[0].getWorkNumber()
    md.number = mdpObjs[0].getWorkNumber()

    for mdPart in mdpObjs:
        musedataPartToStreamPart(mdPart, s)
    return s




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testBasic(self):
        from music21 import musedata
        from music21.musedata import testFiles


        mdw = musedata.MuseDataWork()
        mdw.addString(testFiles.bach_cantata5_mvmt3)
        
        s = museDataWorkToStreamScore(mdw)
        #post = s.musicxml
        
        #s.show()
        self.assertEqual(len(s.parts), 3)

        self.assertEqual(s.parts[0].id, 'Viola Solo')
        self.assertEqual(s.parts[1].id, 'TENORE')
        self.assertEqual(s.parts[2].id, 'Continuo')

        self.assertEqual(len(s.parts[0].flat.notes), 1062)
        self.assertEqual(len(s.parts[1].flat.notes), 596)
        self.assertEqual(len(s.parts[2].flat.notes), 626)


        # try stage 1
        mdw = musedata.MuseDataWork()
        mdw.addString(testFiles.bachContrapunctus1_part1)
        mdw.addString(testFiles.bachContrapunctus1_part2)

        s = museDataWorkToStreamScore(mdw)
        self.assertEqual(len(s.parts[0].flat.notes), 291)
        self.assertEqual(len(s.parts[1].flat.notes), 293)

        post = s.musicxml
      



    def testGetMetaData(self):

        from music21 import musedata
        from music21.musedata import testFiles



    def testGetLyrics(self):
        
        from music21 import musedata
        from music21 import corpus

        s = corpus.parseWork('hwv56', '1-08')
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(s.parts[0].id, 'Contr\'alto')
        self.assertEqual(s.parts[1].id, 'Bassi')

        self.assertEqual(len(s.parts[0].flat.notes), 34)
        self.assertEqual(len(s.parts[1].flat.notes), 9)

        self.assertEqual(s.parts[0].flat.notes[2].lyric, 'Be-')
        self.assertEqual(s.parts[0].flat.notes[3].lyric, 'hold,')

        #s.show()


    def testGetBeams(self):
        from music21 import corpus

        # try single character conversion
        post = _musedataBeamToBeams('=')
        self.assertEqual(str(post), '<music21.beam.Beams <music21.beam.Beam 1/continue>>')

        post = _musedataBeamToBeams(']\\')
        self.assertEqual(str(post), '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/partial/left>>')

        post = _musedataBeamToBeams(']/')
        self.assertEqual(str(post), '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/partial/right>>')


        s = corpus.parseWork('hwv56', '1-18')
        self.assertEqual(len(s.parts), 5)
        # the fourth part is vocal, and has no beams defined
        self.assertEqual(str(s.parts[3].getElementsByClass(
            'Measure')[3].notes[0].beams), '<music21.beam.Beams >')
        self.assertEqual(str(s.parts[3].getElementsByClass(
            'Measure')[3].notes[0].lyric), 'sud-')

        # the bottom part has 8ths beamed two to a bar
        self.assertEqual(str(s.parts[4].getElementsByClass(
            'Measure')[3].notes[0].beams), '<music21.beam.Beams <music21.beam.Beam 1/start>>')
        self.assertEqual(str(s.parts[4].getElementsByClass(
            'Measure')[3].notes[1].beams), '<music21.beam.Beams <music21.beam.Beam 1/continue>>')
        self.assertEqual(str(s.parts[4].getElementsByClass(
            'Measure')[3].notes[2].beams), '<music21.beam.Beams <music21.beam.Beam 1/continue>>')
        self.assertEqual(str(s.parts[4].getElementsByClass(
            'Measure')[3].notes[3].beams), '<music21.beam.Beams <music21.beam.Beam 1/stop>>')

        #s.show()
        # test that stage1 files continue to have makeBeams called
        s = corpus.parseWork('bwv1080', '16')
        # measure two has 9/16 beamed in three beats of 16ths
        self.assertEqual(len(s.parts), 2)

        #s.parts[0].getElementsByClass('Measure')[1].show()

        self.assertEqual(str(s.parts[0].getElementsByClass(
            'Measure')[1].notes[0].beams), '<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>')
        self.assertEqual(str(s.parts[0].getElementsByClass(
            'Measure')[1].notes[1].beams), '<music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>')
        self.assertEqual(str(s.parts[0].getElementsByClass(
            'Measure')[1].notes[2].beams), '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>')



    def testAccidentals(self):
        from music21 import corpus
        s = corpus.parseWork('bwv1080', '16')
        self.assertEqual(len(s.parts[0].getKeySignatures()), 1)
        self.assertEqual(str(s.parts[0].getKeySignatures()[0]), 'sharps -1, mode None')

        notes = s.parts[0].flat.notes
        self.assertEqual(str(notes[2].accidental), '<accidental sharp>')
        self.assertEqual(notes[2].accidental.displayStatus, True)

        # from key signature
        # this value recently changed; from None to True; not sure if this
        # is correct
        self.assertEqual(str(notes[16].accidental), '<accidental flat>')
        self.assertEqual(notes[16].accidental.displayStatus, True)

        # cautionary from within measure
        notes = s.parts[1].measure(13).flat.notes
        self.assertEqual(str(notes[8].accidental), '<accidental natural>')
        self.assertEqual(notes[8].accidental.displayStatus, True)

        #s.show()



    def testTransposingInstruments(self):
        import os
        from music21 import converter, common
        fpDir = os.path.join(common.getSourceFilePath(), 'musedata', 'testPrimitive', 'test01')
        s = converter.parse(fpDir)
        p = s.parts['Clarinet in A']
        self.assertEqual(str(p.getElementsByClass('Measure')[0].keySignature), 'sharps 3, mode None')
        self.assertEqual(str(p.flat.notes[0]), '<music21.note.Note A>')

        #s.show()


    def testBackBasic(self):
        

        import os
        from music21 import converter, common
        fpDir = os.path.join(common.getSourceFilePath(), 'musedata', 'testPrimitive', 'test02')
        s = converter.parse(fpDir)
        # note: this is a multi-staff work, but presently gets encoded
        # as multiple voices
        measures = s.parts[0].measures(1,5)
        self.assertEqual(len(measures[0].flat.notes), 6)
        self.assertEqual(len(measures[1].flat.notes), 12)
        self.assertEqual(len(measures[2].flat.notes), 5)
        self.assertEqual(len(measures[3].flat.notes), 8)
        self.assertEqual(len(measures[4].flat.notes), 7)

        #s.show()


        # alternative test
        # note: this encoding has many parts in a single staff
        # not sure how to translate
        fpDir = os.path.join(common.getSourceFilePath(), 'musedata', 'testPrimitive', 'test03')
        s = converter.parse(fpDir)
        #s.show()



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        #t.testGetLyrics()
        #t.testGetBeams()
        #t.testAccidentals()
        #t.testTransposingInstruments()
        t.testBackBasic()

#------------------------------------------------------------------------------
# eof

