# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         abcFormat.translate.py
# Purpose:      Translate ABC and music21 objects
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Dylan Nagler
#
# Copyright:    Copyright © 2010-2013 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Functions for translating music21 objects and
:class:`~music21.abcFormat.ABCHandler` instances.
Mostly, these functions are for advanced, low level usage.
For basic importing of ABC files from a file or URL to a
:class:`~music21.stream.Stream`, use the music21 converter
module's :func:`~music21.converter.parse` function.


'''

import copy
import unittest

from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import meter
from music21 import stream
from music21 import tie
from music21 import articulations
from music21 import note
from music21 import chord
from music21 import spanner

_MOD = 'abcFormat.translate.py'
environLocal = environment.Environment(_MOD)



def abcToStreamPart(abcHandler, inputM21=None, spannerBundle=None):
    '''
    Handler conversion of a single Part of a multi-part score.
    Results are added into the provided inputM21 object
    or a newly created Part object

    The part object is then returned.
    '''
    from music21 import abcFormat

    if inputM21 is None:
        p = stream.Part()
    else:
        p = inputM21

    if spannerBundle is None:
        #environLocal.printDebug(['mxToMeasure()', 'creating SpannerBundle'])
        spannerBundle = spanner.SpannerBundle()


    # need to call on entire handlers, as looks for special criterial,
    # like that at least 2 regular bars are used, not just double bars
    if abcHandler.definesMeasures():
        # first, split into a list of Measures; if there is only metadata and
        # one measure, that means that no measures are defined
        barHandlers = abcHandler.splitByMeasure()
        #environLocal.printDebug(['barHandlers', len(barHandlers)])
        # merge loading meta data with each bar that preceedes it
        mergedHandlers = abcFormat.mergeLeadingMetaData(barHandlers)
        #environLocal.printDebug(['mergedHandlers', len(mergedHandlers)])
    else: # simply stick in a single list
        mergedHandlers = [abcHandler]

    # if only one merged handler, do not create measures
    if len(mergedHandlers) <= 1:
        useMeasures = False
    else:
        useMeasures = True

    # each unit in merged handlers defines possible a Measure (w/ or w/o metadata), trailing meta data, or a single collection of metadata and note data

    barCount = 0
    measureNumber = 1
    # merged handler are ABCHandlerBar objects, defining attributes for barlines

    for mh in mergedHandlers:
        # if use measures and the handler has notes; otherwise add to part
        #environLocal.printDebug(['abcToStreamPart', 'handler', 'left:', mh.leftBarToken, 'right:', mh.rightBarToken, 'len(mh)', len(mh)])

        if useMeasures and mh.hasNotes():
            #environLocal.printDebug(['abcToStreamPart', 'useMeasures', useMeasures, 'mh.hasNotes()', mh.hasNotes()])
            dst = stream.Measure()
            # bar tokens are already extracted form token list and are available
            # as attributes on the handler object
            # may return None for a regular barline

            if mh.leftBarToken is not None:
                # this may be Repeat Bar subclass
                bLeft = mh.leftBarToken.getBarObject()
                if bLeft != None:
                    dst.leftBarline = bLeft
                if mh.leftBarToken.isRepeatBracket():
                    # get any open spanners of RepeatBracket type
                    rbSpanners = spannerBundle.getByClass('RepeatBracket').getByCompleteStatus(False)
                    # this indication is most likely an opening, as ABC does
                    # not encode second ending ending boundaries
                    # we can still check thought:
                    if len(rbSpanners) == 0:
                        # add this measure as a componnt
                        rb = spanner.RepeatBracket(dst)
                        # set number, returned here
                        rb.number = mh.leftBarToken.isRepeatBracket()
                        # only append if created; otherwise, already stored
                        spannerBundle.append(rb)
                    else: # close it here
                        rb = rbSpanners[0] # get RepeatBracket
                        rb.addSpannedElements(dst)
                        rb.completeStatus = True
                        # this returns 1 or 2 depending on the repeat
                    # in ABC, second repeats close immediately; that is
                    # they never span more than one measure
                    if mh.leftBarToken.isRepeatBracket() == 2:
                        rb.completeStatus = True

            if mh.rightBarToken is not None:
                bRight = mh.rightBarToken.getBarObject()
                if bRight != None:
                    dst.rightBarline = bRight
                # above returns bars and repeats; we need to look if we just
                # have repeats
                if mh.rightBarToken.isRepeat():
                    # if we have a right bar repeat, and a spanner repeat
                    # bracket is open (even if just assigned above) we need
                    # to close it now.
                    # presently, now r bar conditions start a repeat bracket
                    rbSpanners = spannerBundle.getByClass('RepeatBracket').getByCompleteStatus(False)
                    if len(rbSpanners) > 0:
                        rb = rbSpanners[0] # get RepeatBracket
                        rb.addSpannedElements(dst)
                        rb.completeStatus = True
                        # this returns 1 or 2 depending on the repeat
                        # do not need to append; already in bundle
            barCount += 1
        else:
            dst = p # store directly in a part instance

        #environLocal.printDebug([mh, 'dst', dst])
        #ql = 0 # might not be zero if there is a pickup
        
        postTransposition, clefSet = parseTokens(mh, dst, p, useMeasures)

        # append measure to part; in the case of trailing meta data
        # dst may be part, even though useMeasures is True
        if useMeasures and 'Measure' in dst.classes:
            # check for incomplete bars
            # must have a time signature in this bar, or defined recently
            # could use getTimeSignatures() on Stream

            if barCount == 1 and dst.timeSignature != None: # easy case
                # can only do this b/c ts is defined
                if dst.barDurationProportion() < 1.0:
                    dst.padAsAnacrusis()
                    dst.number = 0
                    #environLocal.printDebug(['incompletely filled Measure found on abc import; interpreting as a anacrusis:', 'padingLeft:', dst.paddingLeft])
            else:
                dst.number = measureNumber
                measureNumber += 1
            p._appendCore(dst)

    try:
        reBar(p, inPlace=True)
    except (ABCTranslateException, meter.MeterException, ZeroDivisionError):
        pass
    # clefs are not typically defined, but if so, are set to the first measure
    # following the meta data, or in the open stream
    if not clefSet:
        if useMeasures:  # assume at start of measures
            p.getElementsByClass('Measure')[0].clef = p.flat.bestClef()
        else:
            p._insertCore(0, p.bestClef())

    if postTransposition != 0:
        p.transpose(postTransposition, inPlace=True)

    if useMeasures and len(p.flat.getTimeSignatures(searchContext=False,
            returnDefault=False)) > 0:
        # call make beams for now; later, import beams
        #environLocal.printDebug(['abcToStreamPart: calling makeBeams'])
        try:
            p.makeBeams(inPlace=True)
        except meter.MeterException as e:
            environLocal.warn("Error in beaming...ignoring: %s" % str(e))

    # copy spanners into topmost container; here, a part
    rm = []
    for sp in spannerBundle.getByCompleteStatus(True):
        p._insertCore(0, sp)
        rm.append(sp)
    # remove from original spanner bundle
    for sp in rm:
        spannerBundle.remove(sp)
    p.elementsChanged()
    return p

def parseTokens(mh, dst, p, useMeasures):        
    # in case need to transpose due to clef indication
    from music21 import abcFormat

    postTransposition = 0
    clefSet = False
    for t in mh.tokens:
        if isinstance(t, abcFormat.ABCMetadata):
            if t.isMeter():
                ts = t.getTimeSignatureObject()
                if ts != None: # can be None
                # should append at the right position
                    if useMeasures: # assume at start of measures
                        dst.timeSignature = ts
                    else:
                        dst._appendCore(ts)
            elif t.isKey():
                ks = t.getKeySignatureObject()
                if useMeasures:  # assume at start of measures
                    dst.keySignature = ks
                else:
                    dst._appendCore(ks)
                # check for clef information sometimes stored in key
                clefObj, transposition = t.getClefObject()
                if clefObj != None:
                    clefSet = False
                    #environLocal.printDebug(['found clef in key token:', t, clefObj, transposition])
                    if useMeasures:  # assume at start of measures
                        dst.clef = clefObj
                    else:
                        dst._appendCore(clefObj)
                    postTransposition = transposition
            elif t.isTempo():
                mmObj = t.getMetronomeMarkObject()
                dst._appendCore(mmObj)

        # as ABCChord is subclass of ABCNote, handle first
        elif isinstance(t, abcFormat.ABCChord):
            # may have more than notes?
            pitchNameList = []
            accStatusList = [] # accidental display status list
            for tSub in t.subTokens:
                # notes are contained as subtokens are already parsed
                if isinstance(tSub, abcFormat.ABCNote):
                    pitchNameList.append(tSub.pitchName)
                    accStatusList.append(tSub.accidentalDisplayStatus)
            c = chord.Chord(pitchNameList)
            c.quarterLength = t.quarterLength
            # adjust accidental display for each contained pitch
            for pIndex in range(len(c.pitches)):
                if c.pitches[pIndex].accidental == None:
                    continue
                c.pitches[pIndex].accidental.displayStatus = accStatusList[pIndex]
            dst._appendCore(c)

            #ql += t.quarterLength

        elif isinstance(t, abcFormat.ABCNote):
            if t.isRest:
                n = note.Rest()
            else:
                n = note.Note(t.pitchName)
                if n.pitch.accidental != None:
                    n.pitch.accidental.displayStatus = t.accidentalDisplayStatus

            n.quarterLength = t.quarterLength

            # start or end a tie at note n
            if t.tie is not None:
                if t.tie == "start":
                    n.tie = tie.Tie(t.tie)
                    n.tie.style = "normal"
                elif t.tie == "stop":
                    n.tie = tie.Tie(t.tie)
            ### Was: Extremely Slow for large Opus files... why?
            ### Answer: some pieces didn't close all their spanners, so
            ###         everything was in a Slur/Diminuendo, etc.
            for span in t.applicableSpanners:
                span.addSpannedElements(n)

            if t.inGrace:
                n = n.getGrace()

            n.articulations = []
            while len(t.artic) > 0:
                tmp = t.artic.pop()
                if tmp == "staccato":
                    n.articulations.append(articulations.Staccato())
                if tmp == "upbow":
                    n.articulations.append(articulations.UpBow())
                if tmp == "downbow":
                    n.articulations.append(articulations.DownBow())
                if tmp == "accent":
                    n.articulations.append(articulations.Accent())
                if tmp == "strongaccent":
                    n.articulations.append(articulations.StrongAccent())
                if tmp == "tenuto":
                    n.articulations.append(articulations.Tenuto())

            dst._appendCore(n)
        elif isinstance(t, abcFormat.ABCSlurStart):
            p._appendCore(t.slurObj)
        elif isinstance(t, abcFormat.ABCCrescStart):
            p._appendCore(t.crescObj)
        elif isinstance(t, abcFormat.ABCDimStart):
            p._appendCore(t.dimObj)
    dst.elementsChanged()
    return postTransposition, clefSet

def abcToStreamScore(abcHandler, inputM21=None):
    '''Given an abcHandler object, build into a multi-part :class:`~music21.stream.Score` with metadata.

    This assumes that this ABCHandler defines a single work (with 1 or fewer reference numbers).

    if the optional parameter inputM21 is given a music21 Stream subclass, it will use that object
    as the outermost object.  However, inner parts will always be made :class:`~music21.stream.Part` objects.
    '''
    from music21 import abcFormat
    from music21 import metadata

    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    # meta data can be first
    md = metadata.Metadata()
    s.insert(0, md)

    # get title from large-scale metadata
    titleCount = 0
    for t in abcHandler.tokens:
        if isinstance(t, abcFormat.ABCMetadata):
            if t.isTitle():
                if titleCount == 0: # first
                    md.title = t.data
                    #environLocal.printDebug(['got metadata title', md.title])
                    titleCount += 1
                # all other titles go in alternative field
                else:
                    md.alternativeTitle = t.data
                    #environLocal.printDebug(['got alternative title', md.alternativeTitle])
                    titleCount += 1
            elif t.isComposer():
                md.composer = t.data

            elif t.isOrigin():
                md.localeOfComposition = t.data
                #environLocal.printDebug(['got local of composition', md.localOfComposition])

            elif t.isReferenceNumber():
                md.number = int(t.data) # convert to int?
                #environLocal.printDebug(['got work number', md.number])


    partHandlers = []
    tokenCollections = abcHandler.splitByVoice()
    if len(tokenCollections) == 1:
        partHandlers.append(tokenCollections[0])
    else:
        # add metadata -- stored in tokenCollections[0] -- to each Part (stored in tokenCollections[i])
        for i in range(1, len(tokenCollections)):
            # concatenate abc handler instances
            newABCHandler = tokenCollections[0] + tokenCollections[i]
            #dummy = [t.src for t in newABCHandler.tokens]
            #print dummy
            partHandlers.append(newABCHandler)

    # find if this token list defines measures
    # this should probably operate at the level of tunes, not the entire
    # token list

    partList = []
    for partHandler in partHandlers:
        p = abcToStreamPart(partHandler)
        partList.append(p)

    for p in partList:
        s._insertCore(0, p)
    s.elementsChanged()
    return s




def abcToStreamOpus(abcHandler, inputM21=None, number=None):
    '''Convert a multi-work stream into one or more complete works packed into a an Opus Stream.

    If a `number` argument is given, and a work is defined by
    that number, that work is returned.
    '''
    if inputM21 == None:
        opus = stream.Opus()
    else:
        opus = inputM21

    #environLocal.printDebug(['abcToStreamOpus: got number', number])

    # returns a dictionary of numerical key
    if abcHandler.definesReferenceNumbers():
        abcDict = abcHandler.splitByReferenceNumber()
        if number != None and number in abcDict:
            # get number from dictionary; set to new score
            opus = abcToStreamScore(abcDict[number]) # return a score, not an opus
        else: # build entire opus into an opus stream
            scoreList = []
            for key in sorted(abcDict.keys()):
                # do not need to set work number, as that will be gathered
                # with meta data in abcToStreamScore
                try:
                    scoreList.append(abcToStreamScore(abcDict[key]))
                except IndexError:
                    environLocal.warn("Failure for piece number %d" % key)
            for scoreDocument in scoreList:
                opus._appendCore(scoreDocument)
            opus.elementsChanged()

    else: # just return single entry in opus object
        opus.append(abcToStreamScore(abcHandler))
    return opus

def reBar(music21Part, inPlace=True):
    """
    Re-bar overflow measures using the last known time signature.

    >>> irl2 = corpus.parse("irl", number=2)
    >>> irl2.metadata.title
    'Aililiu na Gamhna, S.35'
    >>> music21Part = irl2[1]


    The whole part is in 2/4 time, but there are some measures expressed in 4/4 time
    without an explicit time signature change, an error in abc parsing due to the
    omission of barlines. The method will split those measures such that they conform
    to the last time signature, in this case 2/4. The default is to reBar in place.
    The measure numbers are updated accordingly. 
    
    (NOTE: reBar is called automatically in abcToStreamPart, hence not demonstrated below...)

    The key signature and clef are assumed to be the same in the second measure after the
    split, so both are omitted. If the time signature is not the same in the second measure,
    the new time signature is indicated, and the measure following returns to the last time
    signature, except in the case that a new time signature is indicated.

    >>> music21Part.measure(15).show("text")
    {0.0} <music21.note.Note A>
    {1.0} <music21.note.Note A>
    >>> music21Part.measure(16).show("text")
    {0.0} <music21.note.Note A>
    {0.5} <music21.note.Note B->
    {1.0} <music21.note.Note A>
    {1.5} <music21.note.Note G>

    An example where the time signature wouldn't be the same. This score is
    mistakenly marked as 4/4, but has some measures that are longer.

    >>> irl15 = corpus.parse("irl", number=15)
    >>> irl15.metadata.title
    'Esternowe, S. 60'
    >>> music21Part2 = irl15.parts[0] # 4/4 time signature
    >>> music21Part2.measure(1).show("text")
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note A>
    {1.5} <music21.note.Note G>
    {2.0} <music21.note.Note E>
    {2.5} <music21.note.Note G>
    >>> music21Part2.measure(1)[-1].duration.quarterLength
    1.5

    >>> music21Part2.measure(2).show("text")
    {0.0} <music21.meter.TimeSignature 1/8>
    {0.0} <music21.note.Note E>
    """
    if not inPlace:
        music21Part = copy.deepcopy(music21Part)
    lastTimeSignature = None
    measureNumberOffset = 0 # amount to shift current measure numbers
    allMeasures = music21Part.getElementsByClass(stream.Measure)
    for measureIndex in range(len(allMeasures)):
        music21Measure = allMeasures[measureIndex]
        if music21Measure.timeSignature is not None:
            lastTimeSignature = music21Measure.timeSignature

        if lastTimeSignature is None:
            raise ABCTranslateException("No time signature found in this Part")

        tsEnd = lastTimeSignature.barDuration.quarterLength
        mEnd = common.opFrac(music21Measure.highestTime)
        music21Measure.number += measureNumberOffset
        if mEnd > tsEnd:
            m1, m2 = music21Measure.splitAtQuarterLength(tsEnd)
            m2.timeSignature = None
            if lastTimeSignature.barDuration.quarterLength != m2.highestTime:
                try:
                    m2.timeSignature = m2.bestTimeSignature()
                except exceptions21.StreamException as e:
                    raise ABCTranslateException("Problem with measure %d (%r): %s" % (music21Measure.number, music21Measure, e))
                if measureIndex != len(allMeasures) - 1:
                    if allMeasures[measureIndex+1].timeSignature is None:
                        allMeasures[measureIndex+1].timeSignature = lastTimeSignature
            m2.keySignature = None # suppress the key signature
            m2.clef = None # suppress the clef
            m2.number = m1.number + 1
            measureNumberOffset += 1
            music21Part.insert(common.opFrac(m1.offsetRational + m1.highestTime), m2)
        
        #elif (mEnd + music21Measure.paddingLeft) < tsEnd and measureIndex != len(allMeasures) - 1:
        #    The first and last measures are allowed to be incomplete
        #    music21Measure.timeSignature = music21Measure.bestTimeSignature()
        #    if allMeasures[measureIndex+1].timeSignature is None:
        #        allMeasures[measureIndex+1].timeSignature = lastTimeSignature
        #

    if not inPlace:
        return music21Part

class ABCTranslateException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import abcFormat
        #from music21.abcFormat import testFiles

        for tf in [
#             testFiles.fyrareprisarn,
#             testFiles.mysteryReel,
#             testFiles.aleIsDear,
#             testFiles.testPrimitive,
#            testFiles.fullRiggedShip,
#            testFiles.kitchGirl,
            #testFiles.morrisonsJig,
#            testFiles.hectorTheHero,
#             testFiles.williamAndNancy,
#            testFiles.theAleWifesDaughter,
#            testFiles.theBeggerBoy,
#            testFiles.theAleWifesDaughter,
#            testFiles.draughtOfAle,

#            testFiles.testPrimitiveTuplet,
#            testFiles.testPrimitivePolyphonic,

            ]:
            af = abcFormat.ABCFile()
            ah = af.readstr(tf) # return handler, processes tokens
            s = abcToStreamScore(ah)
            s.show()
            #s.show('midi')



    def testGetMetaData(self):
        '''
        NB -- only title is checked. not meter or key
        '''

        from music21 import abcFormat
        from music21.abcFormat import testFiles

        for (tf, titleEncoded, unused_meterEncoded, unused_keyEncoded) in [
            (testFiles.fyrareprisarn, 'Fyrareprisarn', '3/4', 'F'),
            (testFiles.mysteryReel, 'Mystery Reel', 'C|', 'G'),
            (testFiles.aleIsDear, 'The Ale is Dear', '4/4', 'D', ),
            (testFiles.kitchGirl, 'Kitchen Girl', '4/4', 'D'),
            (testFiles.williamAndNancy, 'William and Nancy', '6/8', 'G'),
            ]:

            af = abcFormat.ABCFile()
            ah = af.readstr(tf) # returns an ABCHandler object
            s = abcToStreamScore(ah)

            self.assertEqual(s.metadata.title, titleEncoded)


    def testChords(self):

        from music21 import abcFormat
        from music21.abcFormat import testFiles

        tf = testFiles.aleIsDear
        af = abcFormat.ABCFile()
        s = abcToStreamScore(af.readstr(tf))
        #s.show()
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].flat.notesAndRests), 111)
        self.assertEqual(len(s.parts[1].flat.notesAndRests), 127)

        # chords are defined in second part here
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Chord')), 32)

        # check pitches in chords; sharps are applied due to key signature
        match = [p.nameWithOctave for p in s.parts[1].flat.getElementsByClass(
                'Chord')[4].pitches]
        self.assertEqual(match, ['F#4', 'D4', 'B3'])

        match = [p.nameWithOctave for p in s.parts[1].flat.getElementsByClass(
                'Chord')[3].pitches]
        self.assertEqual(match, ['E4', 'C#4', 'A3'])

        #s.show()
        #s.show('midi')



    def testMultiVoice(self):

        from music21 import abcFormat
        from music21.abcFormat import testFiles

        tf = testFiles.testPrimitivePolyphonic

        af = abcFormat.ABCFile()
        s = abcToStreamScore(af.readstr(tf))

        self.assertEqual(len(s.parts), 3)
        # must flatten b/c  there are measures
        self.assertEqual(len(s.parts[0].flat.notesAndRests), 6)
        self.assertEqual(len(s.parts[1].flat.notesAndRests), 17)
        self.assertEqual(len(s.parts[2].flat.notesAndRests), 6)

        #s.show()
        #s.show('midi')


    def testTuplets(self):

        from music21 import abcFormat
        from music21.abcFormat import testFiles

        tf = testFiles.testPrimitiveTuplet
        af = abcFormat.ABCFile()
        s = abcToStreamScore(af.readstr(tf))
        match = []
        # match strings for better comparison
        for n in s.flat.notesAndRests:
            match.append(n.quarterLength)
        shouldFind = [
            1./3, 1./3, 1./3, 
            1./5, 1./5, 1./5, 1./5, 1./5,
            1./6, 1./6, 1./6, 1./6, 1./6, 1./6,
            1./7, 1./7, 1./7, 1./7, 1./7, 1./7, 1./7, 
            2./3, 2./3, 2./3, 2./3, 2./3, 2./3,
            1./12, 1./12, 1./12, 1./12, 1./12, 1./12, 
            1./12, 1./12, 1./12, 1./12, 1./12, 1./12, 
            2.0
            ]
        self.assertEqual(match, [common.opFrac(x) for x in shouldFind])


    def testAnacrusisPadding(self):
        from music21 import abcFormat
        from music21.abcFormat import testFiles

        # 2 quarter pickup in 3/4
        ah = abcFormat.ABCHandler()
        ah.process(testFiles.hectorTheHero)
        s = abcToStreamScore(ah)
        m1 = s.parts[0].getElementsByClass('Measure')[0]
        #s.show()
        # ts is 3/4
        self.assertEqual(m1.barDuration.quarterLength, 3.0)
        # filled with two quarter notes
        self.assertEqual(m1.duration.quarterLength, 2.0)
        #m1.show('t')
        # notes are shown as being on beat 2 and 3
        #environLocal.printDebug(['m1.notesAndRests.activeSite', m1.notesAndRests.activeSite])
        #environLocal.printDebug(['m1.notesAndRests[0].activeSite', m1.notesAndRests[0].activeSite])

        #self.assertEqual(m1.notesAndRests.activeSite)
        self.assertEqual(m1.notesAndRests[0]._getMeasureOffset(), 1.0)
        self.assertEqual(m1.notesAndRests[0].beat, 2.0)
        self.assertEqual(m1.notesAndRests[1]._getMeasureOffset(), 2.0)
        self.assertEqual(m1.notesAndRests[1].beat, 3.0)


        # two 16th pickup in 4/4
        ah = abcFormat.ABCHandler()
        ah.process(testFiles.theAleWifesDaughter)
        s = abcToStreamScore(ah)
        m1 = s.parts[0].getElementsByClass('Measure')[0]

        # ts is 3/4
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        # filled with two 16th
        self.assertEqual(m1.duration.quarterLength, 0.5)
        # notes are shown as being on beat 2 and 3
        self.assertEqual(m1.notesAndRests[0]._getMeasureOffset(), 3.5)
        self.assertEqual(m1.notesAndRests[0].beat, 4.5)
        self.assertEqual(m1.notesAndRests[1]._getMeasureOffset(), 3.75)
        self.assertEqual(m1.notesAndRests[1].beat, 4.75)


    def testOpusImport(self):
        from music21 import corpus
        from music21 import abcFormat

        # replace w/ ballad80, smaller or erk5
        fp = corpus.getWork('essenFolksong/teste')
        self.assertTrue(fp.endswith('essenFolksong/teste.abc') or fp.endswith(r'essenFolksong\teste.abc'))

        af = abcFormat.ABCFile()
        af.open(fp) # return handler, processes tokens
        ah = af.read()
        af.close()

        op = abcToStreamOpus(ah)
        #op.scores[3].show()
        self.assertEqual(len(op), 8)

    def testLyrics(self):
        # TODO

        from music21 import abcFormat
        from music21.abcFormat import testFiles

        tf = testFiles.sicutRosa
        af = abcFormat.ABCFile()
        s = abcToStreamScore(af.readstr(tf))
        assert s is not None

        #s.show()
#         self.assertEqual(len(s.parts), 3)
#         self.assertEqual(len(s.parts[0].notesAndRests), 6)
#         self.assertEqual(len(s.parts[1].notesAndRests), 20)
#         self.assertEqual(len(s.parts[2].notesAndRests), 6)
#
        #s.show()
        #s.show('midi')



    def testMultiWorkImported(self):

        from music21 import corpus
        # defines multiple works, will return an opus
        o = corpus.parse('josquin/milleRegrets')
        self.assertEqual(len(o), 4)
        # each score in the opus is a Stream that contains a Part and metadata
        p1 = o.getScoreByNumber(1).parts[0]
        self.assertEqual(p1.offset, 0.0)
        self.assertEqual(len(p1.flat.notesAndRests), 88)

        p2 = o.getScoreByNumber(2).parts[0]
        self.assertEqual(p2.offset, 0.0)
        self.assertEqual(len(p2.flat.notesAndRests), 80)

        p3 = o.getScoreByNumber(3).parts[0]
        self.assertEqual(p3.offset, 0.0)
        self.assertEqual(len(p3.flat.notesAndRests), 82)

        p4 = o.getScoreByNumber(4).parts[0]
        self.assertEqual(p4.offset, 0.0)
        self.assertEqual(len(p4.flat.notesAndRests), 78)


        sMerged = o.mergeScores()
        self.assertEqual(sMerged.metadata.title, 'Mille regrets')
        self.assertEqual(sMerged.metadata.composer, 'Josquin des Prez')
        self.assertEqual(len(sMerged.parts), 4)


        self.assertEqual(sMerged.parts[0].getElementsByClass('Clef')[0].sign, 'G')
        self.assertEqual(sMerged.parts[1].getElementsByClass('Clef')[0].sign, 'G')
        self.assertEqual(sMerged.parts[2].getElementsByClass('Clef')[0].sign, 'G')
        self.assertEqual(sMerged.parts[2].getElementsByClass('Clef')[0].octaveChange, -1)
        self.assertEqual(sMerged.parts[3].getElementsByClass('Clef')[0].sign, 'F')

        #sMerged.show()


    def testLocaleOfCompositionImport(self):

        from music21 import corpus
        # defines multiple works, will return an opus
        o = corpus.parse('essenFolksong/teste')
        self.assertEqual(len(o), 8)

        s = o.getScoreByNumber(4)
        self.assertEqual(s.metadata.localeOfComposition, 'Asien, Ostasien, China, Sichuan')

        s = o.getScoreByNumber(7)
        self.assertEqual(s.metadata.localeOfComposition, 'Amerika, Mittelamerika, Mexiko')


    def testRepeatBracketsA(self):
        from music21.abcFormat import testFiles
        from music21 import converter
        s = converter.parse(testFiles.morrisonsJig)
        #s.show()
        # one start, one end
        #s.parts[0].show('t')
        self.assertEqual(len(s.flat.getElementsByClass('Repeat')), 2)
        #s.show()

        # this has a 1 note pickup
        # has three repeat bars; first one is implied
        s = converter.parse(testFiles.draughtOfAle)
        self.assertEqual(len(s.flat.getElementsByClass('Repeat')), 3)
        self.assertEqual(s.parts[0].getElementsByClass(
            'Measure')[0].notes[0].pitch.nameWithOctave, 'D4')

        # new problem case:
        s = converter.parse(testFiles.hectorTheHero)
        # first measure has 2 pickup notes
        self.assertEqual(len(s.parts[0].getElementsByClass('Measure')[0].notes), 2)


    def testRepeatBracketsB(self):
        from music21.abcFormat import testFiles
        from music21 import converter
        from music21 import corpus
        s = converter.parse(testFiles.morrisonsJig)
        # TODO: get
        self.assertEqual(len(s.flat.getElementsByClass('RepeatBracket')), 2)
        #s.show()
        # four repeat brackets here; 2 at beginning, 2 at end
        s = converter.parse(testFiles.hectorTheHero)
        self.assertEqual(len(s.flat.getElementsByClass('RepeatBracket')), 4)

        s = corpus.parse('JollyTinkersReel')
        self.assertEqual(len(s.flat.getElementsByClass('RepeatBracket')), 4)


    def testMetronomeMarkA(self):
        from music21.abcFormat import testFiles
        from music21 import converter
        s = converter.parse(testFiles.fullRiggedShip)
        mmStream = s.flat.getElementsByClass('TempoIndication')
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(str(mmStream[0]), '<music21.tempo.MetronomeMark Quarter=100.0>')

        s = converter.parse(testFiles.aleIsDear)
        mmStream = s.flat.getElementsByClass('TempoIndication')
        # this is a two-part pieces, and this is being added for each part
        # not sure if this is a problem
        self.assertEqual(len(mmStream), 2)
        self.assertEqual(str(mmStream[0]), '<music21.tempo.MetronomeMark Quarter=211.0>')

        s = converter.parse(testFiles.theBeggerBoy)
        mmStream = s.flat.getElementsByClass('TempoIndication')
        # this is a two-part pieces, and this is being added for each part
        # not sure if this is a problem
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(str(mmStream[0]), '<music21.tempo.MetronomeMark maestoso Quarter=90.0>')

        #s.show()

    def testTranslateA(self):
        # this tests a few files in this collection, some of which are hard to
        # parse
        from music21 import corpus
        for fn in (
            'ToCashellImGoingJig.abc',
            'SundayIsMyWeddingDayJig.abc',
            'SinkHimDoddieHighlandFling.abc',
            'RandyWifeOfGreenlawReel.abc',
            'PassionFlowerHornpipe.abc',
            'NightingaleClog.abc',
            'MountainRangerHornpipe.abc',
            'LadiesPandelettsReel.abc',
            'JauntingCarHornpipe.abc',
            'GoodMorrowToYourNightCapJig.abc',
            'ChandlersHornpipe.abc',
            'AlistairMaclalastairStrathspey.abc',
            ):
            s = corpus.parse(fn)
            assert s is not None
            #s.show()

    def xtestTranslateB(self):
        '''
        Dylan -- this could be too slow to make it a test!

        Numbers 637 and 749 fail
        '''

        from music21 import corpus
        for fn in ['airdsAirs/book4.abc']:
            s = corpus.parse(fn)
            assert s is not None

            #s.show()

    def testTranslateBrokenDuration(self):
        from music21 import corpus
        unused = corpus.parse('han2.abc', number=445)


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

