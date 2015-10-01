# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musedata.translate.py
# Purpose:      Translate MuseData into music21 objects
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
**N.B. in Dec. 2014 MuseData access was removed from music21 because the rights conflicted with
access computationally from music21.  This module is retained for anyone who has such access,
however it is completely untested now and errors cannot and will not be fixed.**


Functions for translating music21 objects and 
:class:`~music21.musedata.base.MuseDataHandler` instances. Mostly, 
these functions are for advanced, low level usage. For basic importing of MuseData
files from a file or URL to a :class:`~music21.stream.Stream`, use the music21 
converter module's :func:`~music21.converter.parse` function. 
'''

import unittest

from music21 import environment
from music21 import exceptions21
_MOD = 'musedata.translate.py'
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class MuseDataTranslateException(exceptions21.Music21Exception):
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
            beamType='start'
        elif char == ']':
            beamType='stop'
        elif char == '=':
            beamType='continue'
        elif char == '/': # forward is right
            beamType='partial'
            direction='right'
        elif char == '\\' or char == r'\\': # backward is left
            beamType='partial'
            direction='left'
        else:
            #MuseDataTranslateException('cannot interprete beams char: %s' % char)
            environLocal.printDebug(['cannot interprete beams char:',  char])
            continue
        # will automatically increment number        
        # note that this does not permit defining 16th and not defining 8th
        beamsObj.append(beamType, direction)

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
 
    # get accents and expressions; assumes all on first
    # returns an empty list of None
    dynamicObjs = [] # stored in stream, not Note

    for a in records[0].getArticulationObjects():
        post.articulations.append(a)
    for e in records[0].getExpressionObjects():
        post.expressions.append(e)

    for d in records[0].getDynamicObjects():
        dynamicObjs.append(d)

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
    return post, dynamicObjs



def _processPending(hasVoices, pendingRecords, eLast, m, vActive):
    e, dynamicObjs = _musedataRecordListToNoteOrChord(pendingRecords, eLast)
    # place dynamics at same position as element
    if hasVoices:
        vActive._appendCore(e)
        for d in dynamicObjs:
            vActive._insertCore(e.getOffsetBySite(vActive), d)
    else:
        m._appendCore(e)
        for d in dynamicObjs:
            m._insertCore(e.getOffsetBySite(m), d)
    return e

def musedataPartToStreamPart(museDataPart, inputM21=None):
    '''Translate a musedata part to a :class:`~music21.stream.Part`.
    '''
    from music21 import stream
    from music21 import note
    from music21 import tempo

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

        if barCount == 0: # only for when no bars are defined
            # the parent of the measure is the part
            c = mdm.parent.getClefObject()
            if c != None:
                m.clef = mdm.parent.getClefObject()
            m.timeSignature = mdm.parent.getTimeSignatureObject()
            m.keySignature = mdm.parent.getKeySignature()
            # look for a tempo indication
            directive = mdm.parent.getDirective()
            if directive is not None:
                tt = tempo.TempoText(directive)
                # if this appears to be a tempo indication, than get metro
                if tt.isCommonTempoText():
                    mm = tt.getMetronomeMark()
                    m.insert(0, mm)

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
                    pendingRecords = []
                # create rest after clearing pending records
                r = note.Rest()
                r.quarterLength = mdr.getQuarterLength()
                if hasVoices:
                    vActive._appendCore(r)
                else:
                    m._appendCore(r)
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
                    pendingRecords = []
                # need to append this record for the current note
                pendingRecords.append(mdr)

        # check for any remaining single notes (if last) or chords
        if pendingRecords != []:
            eLast = _processPending(hasVoices, pendingRecords, eLast, m, vActive)

        # may be bending elements in a voice to append to a measure
        if vActive is not None and vActive:
            vActive.elementsChanged()
            m._insertCore(0, vActive)

        m.elementsChanged()

        if barCount == 0 and m.timeSignature != None: # easy case
            # can only do this b/c ts is defined
            if m.barDurationProportion() < 1.0:
                m.padAsAnacrusis()
                #environLocal.printDebug(['incompletely filled Measure found on musedata import; interpreting as a anacrusis:', 'padingLeft:', m.paddingLeft])
        p._appendCore(m)
        barCount += 1

    p.elementsChanged()
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
        p.makeBeams(inPlace=True)
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
        import os
        from music21 import common
        #from music21.musicxml import m21ToString

        fp1 = os.path.join(common.getSourceFilePath(), 'musedata', 'testPrimitive', 'test01', '01.md')
        mdw = musedata.MuseDataWork()
        mdw.addFile(fp1)
        
        s = museDataWorkToStreamScore(mdw)
        #post = s.musicxml
        
        #s.show()
        self.assertEqual(len(s.parts), 1)

        self.assertEqual(s.parts[0].id, 'Clarinet in A')
 
        self.assertEqual(len(s.parts[0].flat.notesAndRests), 54)
 

#         # try stage 1
#         mdw = musedata.MuseDataWork()
#         mdw.addString(testFiles.bachContrapunctus1_part1)
#         mdw.addString(testFiles.bachContrapunctus1_part2)
# 
#         s = museDataWorkToStreamScore(mdw)
#         self.assertEqual(len(s.parts[0].flat.notesAndRests), 291)
#         self.assertEqual(len(s.parts[1].flat.notesAndRests), 293)
# 
#         unused_raw = m21ToString.fromMusic21Object(s)
             

#    def testGetMetaData(self):
#
#        from music21 import musedata
#        from music21.musedata import testFiles



#     def testGetLyrics(self):
#         from music21 import corpus
# 
#         s = corpus.parse('hwv56', '1-08')
#         self.assertEqual(len(s.parts), 2)
#         self.assertEqual(s.parts[0].id, 'Contr\'alto')
#         self.assertEqual(s.parts[1].id, 'Bassi')
# 
#         self.assertEqual(len(s.parts[0].flat.notesAndRests), 34)
#         self.assertEqual(len(s.parts[1].flat.notesAndRests), 9)
# 
#         # note that hyphens are stripped on import
#         self.assertEqual(s.parts[0].flat.notesAndRests[2].lyric, 'Be')
#         self.assertEqual(s.parts[0].flat.notesAndRests[3].lyric, 'hold,')

        #s.show()


    def testGetBeams(self):
        # try single character conversion
        post = _musedataBeamToBeams('=')
        self.assertEqual(str(post), '<music21.beam.Beams <music21.beam.Beam 1/continue>>')

        post = _musedataBeamToBeams(']\\')
        self.assertEqual(str(post), '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/partial/left>>')

        post = _musedataBeamToBeams(']/')
        self.assertEqual(str(post), '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/partial/right>>')


#         s = corpus.parse('hwv56', '1-18')
#         self.assertEqual(len(s.parts), 5)
#         # the fourth part is vocal, and has no beams defined
#         self.assertEqual(str(s.parts[3].getElementsByClass(
#             'Measure')[3].notesAndRests[0].beams), '<music21.beam.Beams >')
#         self.assertEqual(str(s.parts[3].getElementsByClass(
#             'Measure')[3].notesAndRests[0].lyric), 'sud')
# 
#         # the bottom part has 8ths beamed two to a bar
#         self.assertEqual(str(s.parts[4].getElementsByClass(
#             'Measure')[3].notesAndRests[0].beams), '<music21.beam.Beams <music21.beam.Beam 1/start>>')
#         self.assertEqual(str(s.parts[4].getElementsByClass(
#             'Measure')[3].notesAndRests[1].beams), '<music21.beam.Beams <music21.beam.Beam 1/continue>>')
#         self.assertEqual(str(s.parts[4].getElementsByClass(
#             'Measure')[3].notesAndRests[2].beams), '<music21.beam.Beams <music21.beam.Beam 1/continue>>')
#         self.assertEqual(str(s.parts[4].getElementsByClass(
#             'Measure')[3].notesAndRests[3].beams), '<music21.beam.Beams <music21.beam.Beam 1/stop>>')
# 
#         #s.show()
#         # test that stage1 files continue to have makeBeams called
#         s = corpus.parse('bwv1080', '16')
#         # measure two has 9/16 beamed in three beats of 16ths
#         self.assertEqual(len(s.parts), 2)
# 
#         #s.parts[0].getElementsByClass('Measure')[1].show()
# 
#         self.assertEqual(str(s.parts[0].getElementsByClass(
#             'Measure')[1].notesAndRests[0].beams), '<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>')
#         self.assertEqual(str(s.parts[0].getElementsByClass(
#             'Measure')[1].notesAndRests[1].beams), '<music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>')
#         self.assertEqual(str(s.parts[0].getElementsByClass(
#             'Measure')[1].notesAndRests[2].beams), '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>')



    def testAccidentals(self):
        '''
        testing a piece with 1 flat to make sure that sharps appear but normal B-flats do not.
        '''
        pass
#         s = corpus.parse('bwv1080', '16')
#         self.assertEqual(len(s.parts[0].getKeySignatures()), 1)
#         self.assertEqual(str(s.parts[0].getKeySignatures()[0]), '<music21.key.KeySignature of 1 flat>')
# 
#         notes = s.parts[0].flat.notesAndRests
#         self.assertEqual(str(notes[2].accidental), '<accidental sharp>')
#         self.assertEqual(notes[2].accidental.displayStatus, True)
# 
#         # from key signature
#         # B-, thus no flat should appear.
#         self.assertEqual(str(notes[16].accidental), '<accidental flat>')
#         self.assertEqual(notes[16].accidental.displayStatus, False)
# 
#         # cautionary from within measure, the C follows a C#
#         notes = s.parts[1].measure(13).flat.notesAndRests
#         self.assertEqual(str(notes[8].accidental), '<accidental natural>')
#         self.assertEqual(notes[8].accidental.displayStatus, True)

        #s.show()



#     def testTransposingInstruments(self):
#         import os
#         from music21 import converter, common
#         fpDir = os.path.join(common.getSourceFilePath(), 'musedata', 'testPrimitive', 'test01')
#         s = converter.parse(fpDir)
#         p = s.parts['Clarinet in A']
#         self.assertEqual(str(p.getElementsByClass('Measure')[0].keySignature), '<music21.key.KeySignature of 3 sharps>')
#         self.assertEqual(str(p.flat.notesAndRests[0]), '<music21.note.Note A>')

        #s.show()


    def testBackBasic(self):
        import os
        from music21 import converter, common
        fpDir = os.path.join(common.getSourceFilePath(), 'musedata', 'testPrimitive', 'test01')
        s = converter.parse(fpDir)
        # note: this is a multi-staff work, but presently gets encoded
        # as multiple voices
        measures = s.parts[0].measures(1,5)
        self.assertEqual(len(measures[0].flat.notesAndRests), 2)
        self.assertEqual(len(measures[1].flat.notesAndRests), 5)
        self.assertEqual(len(measures[2].flat.notesAndRests), 5)
        self.assertEqual(len(measures[3].flat.notesAndRests), 6)
        self.assertEqual(len(measures[4].flat.notesAndRests), 4)

        #s.show()


        #s.show()



#     def testMuseDataStage1A(self):
#         from music21 import corpus
#         s = corpus.parse('k168', 1)
# 
#         self.assertEqual(len(s.parts), 4)
#         self.assertEqual(str(s.parts[0].flat.getElementsByClass('TimeSignature')[0]), '<music21.meter.TimeSignature 4/4>')
#     
#         self.assertEqual([n.offset for n in s.parts[0].getElementsByClass('Measure')[0].notes], [0.0, 3.0, 3.5, 3.75])
# 
#         self.assertEqual([n.nameWithOctave for n in s.parts[0].getElementsByClass('Measure')[0].notes], ['F5', 'F5', 'E5', 'D5'])
# 
#         self.assertEqual([n.offset for n in s.parts[1].getElementsByClass('Measure')[0].notes], [1.0, 2.0, 3.0])

#     def testMuseDataStage1B(self):
#         from music21 import corpus
#         s = corpus.parse('k169', 3)
#         
#         self.assertEqual(len(s.parts), 4)
#         self.assertEqual(str(s.parts[0].flat.getElementsByClass('TimeSignature')[0]), '<music21.meter.TimeSignature 3/4>')
#     
#         self.assertEqual([n.offset for n in s.parts[0].getElementsByClass('Measure')[0].notes], [0.0, 2.0])
# 
#         self.assertEqual([n.nameWithOctave for n in s.parts[0].getElementsByClass('Measure')[0].notes], ['A4', 'B4'])
# 
#         self.assertEqual([n.offset for n in s.parts[2].getElementsByClass('Measure')[0].notes], [0.0, 1.0, 2.0])



#     def testMuseDataImportTempoA(self):
#         from music21 import corpus
#         # a small file
#         s = corpus.parse('movement2-09.md')
#         self.assertEqual(len(s.parts), 5)
#         # the tempo is found in the 4th part here
#         self.assertEqual(str(
#             s.parts[3].flat.getElementsByClass('TempoIndication')[0]), 
#             '<music21.tempo.MetronomeMark Largo e piano Quarter=46>')
#         #s.show()
# 
#         s = corpus.parse('movement2-07.md')
#         self.assertEqual(str(
#             s.flat.getElementsByClass('TempoIndication')[0]), 
#             '<music21.tempo.MetronomeMark Largo Quarter=46>')

#     def testMuseDataImportDynamicsA(self):
#         # note: this is importing a large work, but this seems to presently
#         # be the only one with dynamics
#         
#         # TODO: Turn back on when a smaller work is found...
#         from music21 import corpus
#         s = corpus.parse('symphony94', 3)
#         sFlat = s.flat
#         #s.show()
#         self.assertEqual(len(sFlat.getElementsByClass('Dynamic')), 79)
# 
# 
#     def testMuseDataImportErrorA(self):
#         from music21 import corpus
#         # this files was crashing in the handling of an error in beam notation
#         s = corpus.parse('haydn/opus55no1/movement2.md')
#         self.assertEqual(len(s.flat.getElementsByClass('Note')), 1735)
# 
#         #s.show('t')
# 
#     def testMuseDataImportErrorB(self):
#         # this file has a malformed END repeated twice
#         from music21 import corpus
#         s = corpus.parse('haydn/opus71no1/movement1.zip')
#         self.assertEqual(len(s.flat.getElementsByClass('Note')), 2792)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [museDataWorkToStreamScore]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

