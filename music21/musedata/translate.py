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




def _musedataRecordListToNoteOrChord(records):
    '''Given a list of MuseDataRecord objects, return a configured
    Note or Chord
    '''
    from music21 import note
    from music21 import chord
    from music21 import tie


    if len(records) == 1:
        post = note.Note()
        # directly assign pitch object; will already have accidental
        post.pitch = records[0].getPitchObject()
    else:
        environLocal.printDebug(['attempting chord creation: records', len(records)])
        # can supply a lost of Pitch objects at creation
        post = chord.Chord([r.getPitchObject() for r in records])

    # if a chord, we are assume that all durations are the same
    post.quarterLength = records[0].getQuarterLength()

    # presently this sets a single tie for a chord; may be different cases
    if records[0].isTied():
        post.tie = tie.Tie() # can be start, end, continue
    return post


def musedataPartToStreamPart(museDataPart, inputM21=None):
    '''
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
    for mIndex, mdm in enumerate(mdmObjs):
        #environLocal.printDebug(['processing:', mdm.src])
        if not mdm.hasNotes():
            continue

        #m = stream.Measure()
        # get a measure object with a left configured bar line
        if mIndex <= len(mdmObjs) - 2:
            mdmNext = mdmObjs[mIndex+1]
        else:
            mdmNext = None

        m = mdm.getMeasureObject()

        # conditions for a final measure definition defining the last bar
        if mdmNext != None and not mdmNext.hasNotes():
            environLocal.printDebug(['got mdmNext not none and not has notes'])
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
        
        for i in range(len(mdrObjs)):
            mdr = mdrObjs[i]
            #environLocal.printDebug(['processing:', mdr.src])

            if mdr.isRest():
                #environLocal.printDebug(['got mdr rest, parent:', mdr.parent])
                # check for pending records first
                if pendingRecords != []:
                    m.append(_musedataRecordListToNoteOrChord(pendingRecords))
                    pendingRecords = []
                # create rest after clearing pending records
                r = note.Rest()
                r.quarterLength = mdr.getQuarterLength()
                m.append(r)
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
                    m.append(_musedataRecordListToNoteOrChord(pendingRecords))
                    pendingRecords = []
                # need to append this record for the current note
                pendingRecords.append(mdr)

        # check for any remaining single notes (if last) or chords
        if pendingRecords != []:
            m.append(_musedataRecordListToNoteOrChord(pendingRecords))

        if barCount == 0 and m.timeSignature != None: # easy case
            # can only do this b/c ts is defined
            if m.barDurationProportion() < 1.0:
                m.padAsAnacrusis()
                environLocal.printDebug(['incompletely filled Measure found on musedata import; interpreting as a anacrusis:', 'padingLeft:', m.paddingLeft])
        p.append(m)
        barCount += 1

    # for now, make beams rather than importing
    p.makeBeams()

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
        
        s.show()
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



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
