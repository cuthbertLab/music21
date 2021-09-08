# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         makeNotation.py
# Purpose:      functionality for manipulating streams
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Jacob Walls
#               Evan Lynch
#
# Copyright:    Copyright © 2008-2021 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------

import copy
import unittest
from typing import List, Generator, Optional, Set, Union
from fractions import Fraction  # typing only

from music21 import beam
from music21 import clef
from music21 import common
from music21 import chord
from music21 import defaults
from music21 import environment
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch

from music21.common.numberTools import opFrac

from music21.exceptions21 import StreamException

environLocal = environment.Environment(__file__)


# -----------------------------------------------------------------------------


def makeBeams(
    s: 'music21.stream.Stream',
    *,
    inPlace=False,
    setStemDirections=True,
    failOnNoTimeSignature=False,
):
    # noinspection PyShadowingNames
    '''
    Return a new Measure, or Stream of Measures, with beams applied to all
    notes. Measures with Voices will process voices independently.

    Note that `makeBeams()` is automatically called in show('musicxml') and
    other formats if there is no beaming information in the piece (see
    `haveBeamsBeenMade`).

    If `inPlace` is True, this is done in-place; if `inPlace` is False,
    this returns a modified deep copy.

    .. note: Before Version 1.6, `inPlace` default was `True`; now `False`
             like most `inPlace` options in music21.  Also, in 1.8, no tuplets are made
             automatically.  Use makeTupletBrackets()

    See :meth:`~music21.meter.TimeSignature.getBeams` for the algorithm used.

    >>> aMeasure = stream.Measure()
    >>> aMeasure.timeSignature = meter.TimeSignature('4/4')
    >>> aNote = note.Note()
    >>> aNote.quarterLength = 0.25
    >>> aMeasure.repeatAppend(aNote, 16)
    >>> bMeasure = aMeasure.makeBeams(inPlace=False)

    >>> for i in range(4):
    ...   print(f'{i} {bMeasure.notes[i].beams!r}')
    0 <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
    1 <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>
    2 <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/start>>
    3 <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>


    This was formerly a bug -- we could not have a partial-left beam at the start of a
    beam group.  Now merges across the archetypeSpan

    >>> aMeasure = stream.Measure()
    >>> aMeasure.timeSignature = meter.TimeSignature('4/4')
    >>> for i in range(4):
    ...     aMeasure.append(note.Rest(quarterLength=0.25))
    ...     aMeasure.repeatAppend(note.Note('C4', quarterLength=0.25), 3)
    >>> bMeasure = aMeasure.makeBeams(inPlace=False).notes
    >>> for i in range(6):
    ...   print(f'{i} {bMeasure[i].beams!r}')
    0 <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
    1 <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>
    2 <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>
    3 <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
    4 <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>
    5 <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>

    Grace notes no longer interfere with beaming:

    >>> m = stream.Measure()
    >>> m.timeSignature = meter.TimeSignature('3/4')
    >>> m.repeatAppend(note.Note(quarterLength=0.25), 4)
    >>> m.repeatAppend(note.Rest(), 2)
    >>> gn = note.Note(duration=duration.GraceDuration())
    >>> m.insert(0.25, gn)
    >>> m.makeBeams(inPlace=True)
    >>> [n.beams for n in m.notes]
    [<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>,
    <music21.beam.Beams>,
    <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>,
    <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/start>>,
    <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>]

    OMIT_FROM_DOCS
    TODO: inPlace=False does not work in many cases  ?? still an issue? 2017
    '''
    from music21 import stream

    # environLocal.printDebug(['calling Stream.makeBeams()'])
    if not inPlace:  # make a copy
        returnObj: stream.Stream = s.coreCopyAsDerivation('makeBeams')
    else:
        returnObj: stream.Stream = s

    # if s.isClass(Measure):
    mColl: List[stream.Measure]
    if isinstance(s, stream.Measure):
        returnObj: stream.Measure
        mColl = [returnObj]  # store a list of measures for processing
    else:
        mColl = list(returnObj.getElementsByClass('Measure'))  # a list of measures
        if not mColl:
            raise stream.StreamException(
                'cannot process a stream that is neither a Measure nor has no Measures')

    lastTimeSignature = None

    m: stream.Measure
    for m in mColl:
        # this means that the first of a stream of time signatures will
        # be used
        lastTimeSignature = m.timeSignature or m.getContextByClass(meter.TimeSignature)
        if lastTimeSignature is None:
            if failOnNoTimeSignature:
                raise stream.StreamException(
                    'cannot process beams in a Measure without a time signature')
            continue
        noteGroups = []
        if m.hasVoices():
            for v in m.voices:
                noteGroups.append(v.notesAndRests.stream())
        else:
            noteGroups.append(m.notesAndRests.stream())

        # environLocal.printDebug([
        #    'noteGroups', noteGroups, 'len(noteGroups[0])',
        #    len(noteGroups[0])])

        for noteStream in noteGroups:
            if len(noteStream) <= 1:
                continue  # nothing to beam
            durList = []
            for n in noteStream:
                if n.duration.isGrace:
                    noteStream.remove(n)
                    continue
                durList.append(n.duration)
            # environLocal.printDebug([
            #    'beaming with ts', lastTimeSignature, 'measure', m, durList,
            #    noteStream[0], noteStream[1]])

            # error check; call before sending to time signature, as, if this
            # fails, it represents a problem that happens before time signature
            # processing
            summed = sum([d.quarterLength for d in durList])
            # note, this ^^ is faster than a generator expression

            # the double call below corrects for tiny errors in adding
            # floats and Fractions in the sum() call -- the first opFrac makes it
            # impossible to have 4.00000000001, but returns Fraction(4, 1). The
            # second call converts Fraction(4, 1) to 4.0
            durSum = opFrac(opFrac(summed))

            barQL = lastTimeSignature.barDuration.quarterLength

            if durSum > barQL:
                # environLocal.printDebug([
                #    'attempting makeBeams with a bar that contains durations
                #    that sum greater than bar duration (%s > %s)' %
                #    (durSum, barQL)])
                continue

            # getBeams
            offset = 0.0
            if m.paddingLeft != 0.0:
                offset = opFrac(m.paddingLeft)
            elif m.paddingRight != 0.0:
                pass
            # Incomplete measure without any padding set: assume paddingLeft
            elif noteStream.highestTime < barQL:
                offset = barQL - noteStream.highestTime

            beamsList = lastTimeSignature.getBeams(noteStream, measureStartOffset=offset)

            for i, n in enumerate(noteStream):
                thisBeams = beamsList[i]
                if thisBeams is not None:
                    n.beams = thisBeams
                else:
                    n.beams = beam.Beams()

    del mColl  # remove Stream no longer needed
    if setStemDirections:
        setStemDirectionForBeamGroups(returnObj)

    returnObj.streamStatus.beams = True
    if inPlace is not True:
        return returnObj


def makeMeasures(
    s,
    *,
    meterStream=None,
    refStreamOrTimeRange=None,
    searchContext=False,
    innerBarline=None,
    finalBarline='final',
    bestClef=False,
    inPlace=False,
):
    '''
    Takes a stream and places all of its elements into
    measures (:class:`~music21.stream.Measure` objects)
    based on the :class:`~music21.meter.TimeSignature` objects
    placed within
    the stream. If no TimeSignatures are found in the
    stream, a default of 4/4 is used.

    If `inPlace` is True, the original Stream is modified and lost
    if `inPlace` is False, this returns a modified deep copy.

    Many advanced features are available:

    (1) If a `meterStream` is given, the TimeSignatures in this
    stream are used instead of any found in the Stream.
    Alternatively, a single TimeSignature object
    can be provided in lieu of the stream. This feature lets you
    test out how a group of notes might be interpreted as measures
    in a number of different metrical schemes.

    (2) If `refStreamOrTimeRange` is provided, this Stream or List
    is used to give the span that you want to make measures as
    necessary to fill empty rests at the ends or beginnings of
    Streams, etc.  Say for instance you'd like to make a complete
    score from a short ossia section, then you might use another
    Part from the Score as a `refStreamOrTimeRange` to make sure
    that the appropriate measures of rests are added at either side.

    (3) If `innerBarline` is not None, the specified Barline object
    or string-specification of Barline style will be used to create
    Barline objects between every created Measure. The default is None.

    (4) If `finalBarline` is not None, the specified Barline object or
    string-specification of Barline style will be used to create a Barline
    objects at the end of the last Measure. The default is 'final'.

    The `searchContext` parameter determines whether or not context
    searches are used to find Clef and other notation objects.

    Here is a simple example of makeMeasures:

    A single measure of 4/4 is created from a Stream
    containing only three quarter notes:

    >>> sSrc = stream.Stream()
    >>> sSrc.append(note.Note('C4', type='quarter'))
    >>> sSrc.append(note.Note('D4', type='quarter'))
    >>> sSrc.append(note.Note('E4', type='quarter'))
    >>> sMeasures = sSrc.makeMeasures()
    >>> sMeasures.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.bar.Barline type=final>

    Notice that the last measure is incomplete -- makeMeasures
    does not fill up incomplete measures.

    We can also check that the measure created has
    the correct TimeSignature:

    >>> sMeasures[0].timeSignature
    <music21.meter.TimeSignature 4/4>

    Now let's redo this work in 2/4 by putting a TimeSignature
    of 2/4 at the beginning of the stream and rerunning
    makeMeasures. Now we will have two measures, each with
    correct measure numbers:

    >>> sSrc.insert(0.0, meter.TimeSignature('2/4'))
    >>> sMeasuresTwoFour = sSrc.makeMeasures()
    >>> sMeasuresTwoFour.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
    {2.0} <music21.stream.Measure 2 offset=2.0>
        {0.0} <music21.note.Note E>
        {1.0} <music21.bar.Barline type=final>

    Let us put 10 quarter notes in a Part.

    >>> sSrc = stream.Part()
    >>> n = note.Note('E-4')
    >>> n.quarterLength = 1
    >>> sSrc.repeatAppend(n, 10)

    After we run makeMeasures, we will have
    3 measures of 4/4 in a new Part object. This experiment
    demonstrates that running makeMeasures does not
    change the type of Stream you are using:

    >>> sMeasures = sSrc.makeMeasures()
    >>> len(sMeasures.getElementsByClass('Measure'))
    3
    >>> sMeasures.__class__.__name__
    'Part'

    Demonstrate what `makeMeasures` will do with `inPlace` = True:

    >>> sScr = stream.Score()
    >>> sPart = stream.Part()
    >>> sPart.insert(0, clef.TrebleClef())
    >>> sPart.insert(0, meter.TimeSignature('3/4'))
    >>> sPart.append(note.Note('C4', quarterLength = 3.0))
    >>> sPart.append(note.Note('D4', quarterLength = 3.0))
    >>> sScr.insert(0, sPart)
    >>> sScr.makeMeasures(inPlace=True)
    >>> sScr.show('text')
    {0.0} <music21.stream.Part 0x...>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note C>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.note.Note D>
            {3.0} <music21.bar.Barline type=final>

    If after running makeMeasures you run makeTies, it will also split
    long notes into smaller notes with ties.  Lyrics and articulations
    are attached to the first note.  Expressions (fermatas,
    etc.) will soon be attached to the last note but this is not yet done:

    >>> p1 = stream.Part()
    >>> p1.append(meter.TimeSignature('3/4'))
    >>> longNote = note.Note('D#4')
    >>> longNote.quarterLength = 7.5
    >>> longNote.articulations = [articulations.Staccato()]
    >>> longNote.lyric = 'hi'
    >>> p1.append(longNote)
    >>> partWithMeasures = p1.makeMeasures()
    >>> partWithMeasures is not p1
    True
    >>> dummy = partWithMeasures.makeTies(inPlace=True)
    >>> partWithMeasures.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note D#>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.note.Note D#>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.0} <music21.note.Note D#>
        {1.5} <music21.bar.Barline type=final>

    >>> allNotes = partWithMeasures.flatten().notes
    >>> allNotes[0].articulations
    []

    >>> allNotes[1].articulations
    []

    >>> allNotes[2].articulations
    [<music21.articulations.Staccato>]

    >>> [allNotes[0].lyric, allNotes[1].lyric, allNotes[2].lyric]
    ['hi', None, None]

    Changed in v6 -- all but first attribute are keyword only

    Changed in v7 -- now safe to call `makeMeasures` directly on a score containing parts
    '''
    from music21 import spanner
    from music21 import stream

    mStart = None

    # environLocal.printDebug(['calling Stream.makeMeasures()'])

    # must take a flat representation, as we need to be able to
    # position components, and sub-streams might hide elements that
    # should be contained

    if s.hasPartLikeStreams():
        # can't flatten, because it would destroy parts
        if inPlace:
            returnObj = s
        else:
            returnObj = copy.deepcopy(s)
        for substream in returnObj.getElementsByClass('Stream'):
            substream.makeMeasures(meterStream=meterStream,
                                   refStreamOrTimeRange=refStreamOrTimeRange,
                                   searchContext=searchContext,
                                   innerBarline=innerBarline,
                                   finalBarline=finalBarline,
                                   bestClef=bestClef,
                                   inPlace=True,  # copy already made
                                   )
        if inPlace:
            return
        else:
            return returnObj
    else:
        if s.hasVoices():
            # cannot make flat if there are voices, as would destroy stream partitions
            # parts containing voices are less likely to occur since MIDI parsing changes in v7
            srcObj = s
        else:
            srcObj = s.flatten()
        if not srcObj.isSorted:
            srcObj = srcObj.sorted()
        if not inPlace:
            srcObj = copy.deepcopy(srcObj)
        voiceCount = len(srcObj.voices)

    # environLocal.printDebug([
    #    'Stream.makeMeasures(): passed in meterStream', meterStream,
    #    meterStream[0]])

    # may need to look in activeSite if no time signatures are found
    if meterStream is None:
        # get from this Stream, or search the contexts
        meterStream = srcObj.flatten().getTimeSignatures(
            returnDefault=True,
            searchContext=False,
            sortByCreationTime=False
        )
        # environLocal.printDebug([
        #    'Stream.makeMeasures(): found meterStream', meterStream[0]])
    elif isinstance(meterStream, meter.TimeSignature):
        # if meterStream is a TimeSignature, use it
        ts = meterStream
        meterStream = stream.Stream()
        meterStream.insert(0, ts)
    else:  # check that the meterStream is a Stream!
        if not isinstance(meterStream, stream.Stream):
            raise stream.StreamException(
                'meterStream is neither a Stream nor a TimeSignature!')

    # environLocal.printDebug([
    #    'makeMeasures(): meterStream', 'meterStream[0]', meterStream[0],
    #    'meterStream[0].offset',  meterStream[0].offset,
    #    'meterStream.elements[0].activeSite',
    #    meterStream.elements[0].activeSite])

    # need a SpannerBundle to store any found spanners and place
    # at the part level
    spannerBundleAccum = spanner.SpannerBundle()

    # MSC: Q 2020 -- why is making a clef something to do in this routine?
    #
    # get a clef for the entire stream; this will use bestClef
    # presently, this only gets the first clef
    # may need to store a clefStream and access changes in clefs
    # as is done with meterStream
    # clefList = srcObj.getClefs(searchActiveSite=True,
    #                searchContext=searchContext,
    #                returnDefault=True)
    # clefObj = clefList[0]
    # del clefList
    clefObj = srcObj.clef or srcObj.getContextByClass('Clef')
    if clefObj is None:
        clefObj = srcObj.getElementsByClass('Clef').getElementsByOffset(0).first()
        # only return clefs that have offset = 0.0
        if not clefObj:
            clefObj = clef.bestClef(srcObj, recurse=True)

    # environLocal.printDebug([
    #    'makeMeasures(): first clef found after copying and flattening',
    #    clefObj])

    # for each element in stream, need to find max and min offset
    # assume that flat/sorted options will be set before processing
    # list of start, start+dur, element
    offsetMapList = srcObj.offsetMap()
    # environLocal.printDebug(['makeMeasures(): offset map', offsetMap])
    # offsetMapList.sort() not necessary; just get min and max
    if offsetMapList:
        oMax = max([x.endTime for x in offsetMapList])
    else:
        oMax = 0

    # if a ref stream is provided, get highest time from there
    # only if it is greater than the highest time yet encountered
    if refStreamOrTimeRange is not None:
        if isinstance(refStreamOrTimeRange, stream.Stream):
            refStreamHighestTime = refStreamOrTimeRange.highestTime
        else:  # assume it's a list
            refStreamHighestTime = max(refStreamOrTimeRange)
        if refStreamHighestTime > oMax:
            oMax = refStreamHighestTime

    # create a stream of measures to contain the offsets range defined
    # create as many measures as needed to fit in oMax
    post = s.__class__()
    post.derivation.origin = s
    post.derivation.method = 'makeMeasures'

    o = 0.0  # initial position of first measure is assumed to be zero
    measureCount = 0
    lastTimeSignature = None
    while True:
        m = stream.Measure()
        m.number = measureCount + 1
        # environLocal.printDebug([
        #    'handling measure', m, m.number, 'current offset value', o,
        #    meterStream._reprTextLine()])
        # get active time signature at this offset
        # make a copy and it to the meter
        thisTimeSignature = meterStream.getElementAtOrBefore(o)
        # environLocal.printDebug([
        #    'm.number', m.number, 'meterStream.getElementAtOrBefore(o)',
        #    meterStream.getElementAtOrBefore(o), 'lastTimeSignature',
        #    lastTimeSignature, 'thisTimeSignature', thisTimeSignature ])

        if thisTimeSignature is None and lastTimeSignature is None:
            raise stream.StreamException(
                'failed to find TimeSignature in meterStream; '
                + 'cannot process Measures')
        if (thisTimeSignature is not lastTimeSignature
                and thisTimeSignature is not None):
            lastTimeSignature = thisTimeSignature
            # this seems redundant
            # lastTimeSignature = meterStream.getElementAtOrBefore(o)
            m.timeSignature = copy.deepcopy(thisTimeSignature)
            # environLocal.printDebug(['assigned time sig', m.timeSignature])

        # only add a clef for the first measure when automatically
        # creating Measures; this clef is from getClefs, called above
        if measureCount == 0:
            m.clef = clefObj
            if voiceCount > 0 and s.keySignature is not None:
                m.insert(0, copy.deepcopy(s.keySignature))
            # environLocal.printDebug(
            #    ['assigned clef to measure', measureCount, m.clef])

        # add voices if necessary (voiceCount > 0)
        for voiceIndex in range(voiceCount):
            v = stream.Voice()
            v.id = voiceIndex  # id is voice index, starting at 0
            m.coreInsert(0, v)
        if voiceCount:
            m.coreElementsChanged()

        # avoid an infinite loop
        if thisTimeSignature.barDuration.quarterLength == 0:
            raise stream.StreamException(
                f'time signature {thisTimeSignature!r} has no duration')
        post.coreInsert(o, m)  # insert measure
        # increment by meter length
        o += thisTimeSignature.barDuration.quarterLength
        if o >= oMax:  # may be zero
            break  # if length of this measure exceeds last offset
        else:
            measureCount += 1

    post.coreElementsChanged()

    # cache information about each measure (we used to do this once per element...
    postLen = len(post)
    postMeasureList = []
    lastTimeSignature = None
    for i in range(postLen):
        m = post[i]
        if m.timeSignature is not None:
            lastTimeSignature = m.timeSignature
        # get start and end offsets for each measure
        # seems like should be able to use m.duration.quarterLengths
        mStart = post.elementOffset(m)
        mEnd = mStart + lastTimeSignature.barDuration.quarterLength
        # if elements start fits within this measure, break and use
        # offset cannot start on end
        postMeasureList.append({'measure': m,
                                'mStart': mStart,
                                'mEnd': mEnd})

    # populate measures with elements
    for oneOffsetMap in offsetMapList:
        e, start, end, voiceIndex = oneOffsetMap

        # environLocal.printDebug(['makeMeasures()', start, end, e, voiceIndex])
        # iterate through all measures, finding a measure that
        # can contain this element

        # collect all spanners and move to outer Stream
        if isinstance(e, spanner.Spanner):
            spannerBundleAccum.append(e)
            continue

        match = False
        lastTimeSignature = None

        m = None
        for i in range(postLen):
            postMeasureInfo = postMeasureList[i]
            mStart = postMeasureInfo['mStart']
            mEnd = postMeasureInfo['mEnd']
            m = postMeasureInfo['measure']

            if mStart <= start < mEnd:
                match = True
                # environLocal.printDebug([
                #    'found measure match', i, mStart, mEnd, start, end, e])
                break

        if not match:
            if start == end == oMax:
                post.storeAtEnd(e)
                continue
            else:
                raise stream.StreamException(
                    f'cannot place element {e} with start/end {start}/{end} within any measures')

        # find offset in the temporal context of this measure
        # i is the index of the measure that this element starts at
        # mStart, mEnd are correct
        oNew = start - mStart  # remove measure offset from element offset

        # insert element at this offset in the measure
        # not copying elements here!

        # in the case of a Clef, and possibly other measure attributes,
        # the element may have already been placed in this measure
        # we need to only exclude elements that are placed in the special
        # first position
        if m.clef is e:
            continue
        # do not accept another time signature at the zero position: this
        # is handled above
        if oNew == 0 and isinstance(e, meter.TimeSignature):
            continue

        # environLocal.printDebug(['makeMeasures()', 'inserting', oNew, e])
        # NOTE: cannot use coreInsert here for some reason
        if voiceIndex is None:
            m.insert(oNew, e)
        else:  # insert into voice specified by the voice index
            m.voices[voiceIndex].insert(oNew, e)

    # add found spanners to higher-level; could insert at zero
    for sp in spannerBundleAccum:
        post.append(sp)

    # clean up temporary streams to avoid extra site accumulation
    del srcObj

    # set barlines if necessary
    lastIndex = len(post.getElementsByClass('Measure')) - 1
    for i, m in enumerate(post.getElementsByClass('Measure')):
        if i != lastIndex:
            if innerBarline not in ['regular', None]:
                m.rightBarline = innerBarline
        else:
            if finalBarline not in ['regular', None]:
                m.rightBarline = finalBarline
        if bestClef:
            m.clef = clef.bestClef(m, recurse=True)

    if not inPlace:
        post.setDerivationMethod('makeMeasures', recurse=True)
        return post  # returns a new stream populated w/ new measure streams
    else:  # clear the stored elements list of this Stream and repopulate
        # with Measures created above
        s._elements = []
        s._endElements = []
        s.coreElementsChanged()
        if post.isSorted:
            postSorted = post
        else:
            postSorted = post.sorted()

        for e in postSorted:
            # may need to handle spanners; already have s as site
            s.insert(post.elementOffset(e), e)


def makeRests(
    s,
    *,
    refStreamOrTimeRange=None,
    fillGaps=False,
    timeRangeFromBarDuration=False,
    inPlace=False,
    hideRests=False,
):
    '''
    Given a Stream with an offset not equal to zero,
    fill with one Rest preceding this offset.
    This can be called on any Stream,
    a Measure alone, or a Measure that contains
    Voices. This method recurses into Parts, Measures, and Voices,
    since users are unlikely to want "loose" rests outside
    of sub-containers.

    If `refStreamOrTimeRange` is provided as a Stream, this
    Stream is used to get min and max offsets. If a list is provided,
    the list assumed to provide minimum and maximum offsets. Rests will
    be added to fill all time defined within refStream.

    If `fillGaps` is True, this will create rests in any
    time regions that have no active elements.

    If `timeRangeFromBarDuration` is True, and the calling Stream
    is a Measure with a TimeSignature (or a Part containing them),
    the time range will be determined
    by taking the :meth:`~music21.stream.Measure.barDuration` and subtracting
    :attr:`~music21.stream.Measure.paddingLeft` and
    :attr:`~music21.stream.Measure.paddingRight`.
    This keyword takes priority over `refStreamOrTimeRange`.
    If both are provided, `timeRangeFromBarDuration`
    prevails, unless no TimeSignature can be found, in which case, the function
    falls back to `refStreamOrTimeRange`.

    If `inPlace` is True, this is done in-place; if `inPlace` is False,
    this returns a modified deepcopy.

    >>> a = stream.Stream()
    >>> a.insert(20, note.Note())
    >>> len(a)
    1
    >>> a.lowestOffset
    20.0
    >>> a.show('text')
    {20.0} <music21.note.Note C>

    Now make some rests...

    >>> b = a.makeRests(inPlace=False)
    >>> len(b)
    2
    >>> b.lowestOffset
    0.0
    >>> b.show('text')
    {0.0} <music21.note.Rest 20ql>
    {20.0} <music21.note.Note C>
    >>> b[0].duration.quarterLength
    20.0

    Same thing, but this time, with gaps, and hidden rests...

    >>> a = stream.Stream()
    >>> a.insert(20, note.Note('C4'))
    >>> a.insert(30, note.Note('D4'))
    >>> len(a)
    2
    >>> a.lowestOffset
    20.0
    >>> a.show('text')
    {20.0} <music21.note.Note C>
    {30.0} <music21.note.Note D>
    >>> b = a.makeRests(fillGaps=True, inPlace=False, hideRests=True)
    >>> len(b)
    4
    >>> b.lowestOffset
    0.0
    >>> b.show('text')
    {0.0} <music21.note.Rest 20ql>
    {20.0} <music21.note.Note C>
    {21.0} <music21.note.Rest 9ql>
    {30.0} <music21.note.Note D>
    >>> b[0].style.hideObjectOnPrint
    True

    Now with measures:

    >>> a = stream.Part()
    >>> a.insert(4, note.Note('C4'))
    >>> a.insert(8, note.Note('D4'))
    >>> len(a)
    2
    >>> a.lowestOffset
    4.0
    >>> a.insert(0, meter.TimeSignature('4/4'))
    >>> a.makeMeasures(inPlace=True)
    >>> a.show('text', addEndTimes=True)
    {0.0 - 0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0 - 0.0} <music21.clef.TrebleClef>
        {0.0 - 0.0} <music21.meter.TimeSignature 4/4>
    {4.0 - 5.0} <music21.stream.Measure 2 offset=4.0>
        {0.0 - 1.0} <music21.note.Note C>
    {8.0 - 9.0} <music21.stream.Measure 3 offset=8.0>
        {0.0 - 1.0} <music21.note.Note D>
        {1.0 - 1.0} <music21.bar.Barline type=final>
    >>> a.makeRests(fillGaps=True, inPlace=True)
    >>> a.show('text', addEndTimes=True)
    {0.0 - 4.0} <music21.stream.Measure 1 offset=0.0>
        {0.0 - 0.0} <music21.clef.TrebleClef>
        {0.0 - 0.0} <music21.meter.TimeSignature 4/4>
        {0.0 - 4.0} <music21.note.Rest whole>
    {4.0 - 8.0} <music21.stream.Measure 2 offset=4.0>
        {0.0 - 1.0} <music21.note.Note C>
        {1.0 - 4.0} <music21.note.Rest dotted-half>
    {8.0 - 12.0} <music21.stream.Measure 3 offset=8.0>
        {0.0 - 1.0} <music21.note.Note D>
        {1.0 - 4.0} <music21.note.Rest dotted-half>
        {4.0 - 4.0} <music21.bar.Barline type=final>

    Changed in v6 -- all but first attribute are keyword only

    Changed in v7:

      - `inPlace` defaults False
      - Recurses into parts, measures, voices
      - Gave priority to `timeRangeFromBarDuration` over `refStreamOrTimeRange`
    '''
    from music21 import stream

    if not inPlace:  # make a copy
        returnObj = s.coreCopyAsDerivation('makeRests')
    else:
        returnObj = s

    if returnObj.iter().parts:
        for inner_part in returnObj.iter().parts:
            inner_part.makeRests(
                inPlace=True,
                fillGaps=fillGaps,
                hideRests=hideRests,
                refStreamOrTimeRange=refStreamOrTimeRange,
                timeRangeFromBarDuration=timeRangeFromBarDuration,
            )
        return returnObj

    def oHighTargetForMeasure(
        m: Optional[stream.Measure] = None,
        ts: Optional[meter.TimeSignature] = None
    ) -> Union[float, Fraction]:
        """
        Needed for timeRangeFromBarDuration.
        Returns 0.0 if no meter can be found.
        """
        post: Union[float, Fraction] = 0.0
        if ts is not None:
            post = ts.barDuration.quarterLength
        elif m is not None:
            # More expensive context search
            post = m.barDuration.quarterLength
        if m is not None:
            post -= m.paddingLeft
            post -= m.paddingRight
        return max(post, 0.0)

    oLowTarget = 0.0
    oHighTarget = 0.0
    if timeRangeFromBarDuration:
        if isinstance(returnObj, stream.Measure):
            oHighTarget = oHighTargetForMeasure(m=returnObj)
        elif isinstance(returnObj, stream.Voice):
            if isinstance(refStreamOrTimeRange, stream.Measure):
                oHighTarget = oHighTargetForMeasure(m=refStreamOrTimeRange)
            elif isinstance(refStreamOrTimeRange, meter.TimeSignature):
                maybe_measure: Optional[stream.Measure] = None
                if isinstance(returnObj.activeSite, stream.Measure):
                    maybe_measure = returnObj.activeSite
                oHighTarget = oHighTargetForMeasure(m=maybe_measure, ts=refStreamOrTimeRange)
        elif returnObj.hasMeasures():
            # This could be optimized to save some context searches,
            # but at the cost of readability.
            oHighTarget = sum(
                m.barDuration.quarterLength for m in returnObj.getElementsByClass(stream.Measure)
            )

    # If the above search didn't run or still yielded 0.0, use refStreamOrTimeRange
    if oHighTarget == 0.0:
        if refStreamOrTimeRange is None:  # use local
            oHighTarget = returnObj.highestTime
        elif isinstance(refStreamOrTimeRange, stream.Stream):
            oLowTarget = refStreamOrTimeRange.lowestOffset
            oHighTarget = refStreamOrTimeRange.highestTime
        # treat as a list
        elif common.isIterable(refStreamOrTimeRange):
            oLowTarget = min(refStreamOrTimeRange)
            oHighTarget = max(refStreamOrTimeRange)

    if returnObj.hasVoices():
        bundle = list(returnObj.voices)
    elif returnObj.hasMeasures():
        bundle = returnObj.getElementsByClass('Measure')
    else:
        bundle = [returnObj]

    lastTimeSignature: Optional[meter.TimeSignature] = None
    # bundle components may be voices, measures, or a flat Stream
    for component in bundle:
        oLow = component.lowestOffset
        oHigh = component.highestTime
        lastTimeSignature = component.timeSignature or lastTimeSignature
        if isinstance(component, stream.Measure):
            ts_or_measure = lastTimeSignature or component
            if timeRangeFromBarDuration:
                oHighTarget = oHighTargetForMeasure(component, lastTimeSignature)
            # process voices
            for inner_voice in component.voices:
                inner_voice.makeRests(inPlace=True,
                                      fillGaps=fillGaps,
                                      hideRests=hideRests,
                                      refStreamOrTimeRange=ts_or_measure,
                                      timeRangeFromBarDuration=timeRangeFromBarDuration,
                                      )
            # Refresh these variables given that inner voices were altered
            oLow = component.lowestOffset
            oHigh = component.highestTime
            # adjust oHigh to not exceed measure
            oHighTarget = min(ts_or_measure.barDuration.quarterLength, oHighTarget)

        # create rest from start to end
        qLen = oLow - oLowTarget
        if qLen > 0:
            r = note.Rest()
            r.duration.quarterLength = qLen
            r.style.hideObjectOnPrint = hideRests
            # environLocal.printDebug(['makeRests(): add rests', r, r.duration])
            # place at oLowTarget to reach to oLow
            component.insert(oLowTarget, r)

        # create rest from end to highest
        qLen = oHighTarget - oHigh
        if qLen > 0:
            r = note.Rest()
            r.duration.quarterLength = qLen
            r.style.hideObjectOnPrint = hideRests
            # place at oHigh to reach to oHighTarget
            component.insert(oHigh, r)

        if fillGaps:
            gapStream = component.findGaps()
            if gapStream is not None:
                for e in gapStream:
                    r = note.Rest()
                    r.duration.quarterLength = e.duration.quarterLength
                    r.style.hideObjectOnPrint = hideRests
                    component.insert(e.offset, r)

    if returnObj.hasMeasures():
        # split rests at measure boundaries
        returnObj.makeTies(classFilterList=(note.Rest,), inPlace=True)

        # reposition measures
        accumulatedTime = 0.0
        for m in returnObj.getElementsByClass(stream.Measure):
            returnObj.setElementOffset(m, accumulatedTime)
            accumulatedTime += m.highestTime

    if inPlace is not True:
        return returnObj

def makeTies(
    s,
    *,
    meterStream=None,
    inPlace=False,
    displayTiedAccidentals=False,
    classFilterList=(note.GeneralNote,),
):
    # noinspection PyShadowingNames
    '''
    Given a stream containing measures, examine each element in the
    Stream. If the element's duration extends beyond the measure's boundary,
    create a tied entity, placing the split Note in the next Measure.

    Note that this method assumes that there is appropriate space in the
    next Measure: this will not shift Note objects, but instead allocate
    them evenly over barlines. Generally, makeMeasures is called prior to
    calling this method.

    If `inPlace` is True, this is done in-place;
    if `inPlace` is False, this returns a modified deep copy.

    Put a 12-quarter-note-long note into a Stream w/ 4/4 as the duration.

    >>> d = stream.Stream()
    >>> d.insert(0, meter.TimeSignature('4/4'))
    >>> n = note.Note('C4')
    >>> n.quarterLength = 12
    >>> d.insert(0, n)
    >>> d.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C>

    After running makeMeasures, we get nice measures, a clef, but only one
    way-too-long note in Measure 1:

    >>> x = d.makeMeasures()
    >>> x.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
    {4.0} <music21.stream.Measure 2 offset=4.0>
    <BLANKLINE>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.bar.Barline type=final>
    >>> n2 = x.measure(1).notes[0]
    >>> n2.duration.quarterLength
    12.0
    >>> n2 is n
    False

    But after running makeTies, all is good:

    >>> x.makeTies(inPlace=True)
    >>> x.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note C>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.note.Note C>
        {4.0} <music21.bar.Barline type=final>
    >>> m = x.measure(1).notes[0]
    >>> m.duration.quarterLength
    4.0
    >>> m is n
    False
    >>> m.tie
    <music21.tie.Tie start>
    >>> x.measure(2).notes[0].tie
    <music21.tie.Tie continue>
    >>> x.measure(3).notes[0].tie
    <music21.tie.Tie stop>

    Same experiment, but with rests:

    >>> d = stream.Stream()
    >>> d.insert(0, meter.TimeSignature('4/4'))
    >>> r = note.Rest()
    >>> r.quarterLength = 12
    >>> d.insert(0, r)
    >>> x = d.makeMeasures()
    >>> x.makeTies(inPlace=True)
    >>> x.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Rest whole>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Rest whole>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.note.Rest whole>
        {4.0} <music21.bar.Barline type=final>

    Notes: uses base.Music21Object.splitAtQuarterLength() once it has figured out
    what to split.

    Changed in v. 4 -- inPlace = False by default.

    Changed in v6 -- all but first attribute are keyword only

    Added in v. 7 -- `classFilterList` acts as a filter on what elements will
    be operated on (i.e. have durations split and/or ties made.)
    The default `(note.GeneralNote,)` includes Notes, Chords, and Rests.

    Here will we split and make ties only on Notes, leaving the too-long
    rest in measure 1 alone.

    >>> p = stream.Part()
    >>> p.append(meter.TimeSignature('2/4'))
    >>> p.insert(0.0, note.Rest(quarterLength=3.0))
    >>> p.insert(3.0, note.Note(quarterLength=3.0))
    >>> p.makeMeasures(inPlace=True)
    >>> p.makeTies(classFilterList=[note.Note], inPlace=True)
    >>> p.show('text', addEndTimes=True)
    {0.0 - 3.0} <music21.stream.Measure 1 offset=0.0>
        {0.0 - 0.0} <music21.clef.TrebleClef>
        {0.0 - 0.0} <music21.meter.TimeSignature 2/4>
        {0.0 - 3.0} <music21.note.Rest dotted-half>
    {2.0 - 4.0} <music21.stream.Measure 2 offset=2.0>
        {1.0 - 2.0} <music21.note.Note C>
    {4.0 - 6.0} <music21.stream.Measure 3 offset=4.0>
        {0.0 - 2.0} <music21.note.Note C>
        {2.0 - 2.0} <music21.bar.Barline type=final>
    >>> p.measure(3).notes[0].tie
    <music21.tie.Tie stop>

    OMIT_FROM_DOCS

    configure ".previous" and ".next" attributes

    Previously a note tied from one voice could not make ties into a note
    in the next measure outside of voices.  Fixed May 2017

    >>> p = stream.Part()
    >>> m1 = stream.Measure(number=1)
    >>> m2 = stream.Measure(number=2)
    >>> m1.append(meter.TimeSignature('1/4'))
    >>> v1 = stream.Voice(id='v1')
    >>> v2 = stream.Voice(id=2)  # also test problems with int voice ids
    >>> n1 = note.Note('C4')
    >>> n1.tie = tie.Tie('start')
    >>> n2 = note.Note('D--4')
    >>> n2.tie = tie.Tie('start')
    >>> v1.append(n1)
    >>> v2.append(n2)
    >>> n3 = note.Note('C4')
    >>> n3.tie = tie.Tie('stop')
    >>> m2.append(n3)
    >>> m1.insert(0, v1)
    >>> m1.insert(0, v2)
    >>> p.append([m1, m2])
    >>> p2 = p.makeTies()

    test same thing with needed makeTies:

    >>> p = stream.Part()
    >>> m1 = stream.Measure(number=1)
    >>> m2 = stream.Measure(number=2)
    >>> m1.append(meter.TimeSignature('1/4'))
    >>> v1 = stream.Voice(id='v1')
    >>> v2 = stream.Voice(id=2)  # also test problems with int voice ids
    >>> n1 = note.Note('C4', quarterLength=2)
    >>> n2 = note.Note('B4')
    >>> v1.append(n1)
    >>> v2.append(n2)
    >>> m1.insert(0, v1)
    >>> m1.insert(0, v2)
    >>> p.append(m1)
    >>> p.insert(1.0, m2)
    >>> p2 = p.makeTies()
    >>> p2.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.meter.TimeSignature 1/4>
        {0.0} <music21.stream.Voice v1>
            {0.0} <music21.note.Note C>
        {0.0} <music21.stream.Voice 2>
            {0.0} <music21.note.Note B>
    {1.0} <music21.stream.Measure 2 offset=1.0>
        {0.0} <music21.note.Note C>

    >>> for n in p2.recurse().notes:
    ...     print(n, n.tie)
    <music21.note.Note C> <music21.tie.Tie start>
    <music21.note.Note B> None
    <music21.note.Note C> <music21.tie.Tie stop>

    Be helpful and wrap `classFilterList` in a list if need be.

    >>> m = stream.Measure([note.Note(quarterLength=8.0)])
    >>> m.insert(0, meter.TimeSignature('4/4'))
    >>> p = stream.Part([m])
    >>> p.makeTies(inPlace=True, classFilterList='Note')
    >>> len(p.getElementsByClass('Measure'))
    2
    >>> p.recurse().last().tie
    <music21.tie.Tie stop>
    '''
    from music21 import stream

    # environLocal.printDebug(['calling Stream.makeTies()'])

    if not inPlace:  # make a copy
        returnObj = s.coreCopyAsDerivation('makeTies')
    else:
        returnObj = s
    if not returnObj:
        raise stream.StreamException('cannot process an empty stream')

    if not common.isIterable(classFilterList):
        classFilterList = [classFilterList]

    # get measures from this stream
    measureStream = returnObj.getElementsByClass('Measure')
    if not measureStream:
        raise stream.StreamException(
            'cannot process a stream without measures')

    # environLocal.printDebug([
    #    'makeTies() processing measureStream, length', measureStream,
    #    len(measureStream)])

    # may need to look in activeSite if no time signatures are found
    # presently searchContext is False to save time
    if meterStream is None:
        meterStream = returnObj.getTimeSignatures(sortByCreationTime=True,
                                                  searchContext=False)

    mCount = 0
    lastTimeSignature = None

    while True:  # TODO: find a way to avoid 'while True'
        # update measureStream on each iteration,
        # as new measure may have been added to the returnObj stream
        measureStream = returnObj.getElementsByClass('Measure').stream()
        if mCount >= len(measureStream):
            break  # reached the end of all measures available or added
        # get the current measure to look for notes that need ties
        m = measureStream[mCount]
        if m.timeSignature is not None:
            lastTimeSignature = m.timeSignature

        # get next measure; we may not need it, but have it ready
        if mCount + 1 < len(measureStream):
            mNext = measureStream[mCount + 1]
            mNextAdd = False  # already present; do not append
        else:  # create a new measure
            mNext = stream.Measure()
            # set offset to last offset plus total length
            mOffset = measureStream.elementOffset(m)
            if lastTimeSignature is not None:
                mNext.offset = (mOffset
                                + lastTimeSignature.barDuration.quarterLength)
            else:
                mNext.offset = mOffset
            if not meterStream:  # in case no meters are defined
                ts = meter.TimeSignature()
                ts.load(f'{defaults.meterNumerator}/{defaults.meterDenominatorBeatType}')
            else:  # get the last encountered meter
                ts = meterStream.getElementAtOrBefore(mNext.offset)
            # only copy and assign if not the same as the last
            if (lastTimeSignature is not None
                    and not lastTimeSignature.ratioEqual(ts)):
                mNext.timeSignature = copy.deepcopy(ts)
            # increment measure number
            mNext.number = m.number + 1
            mNextAdd = True  # new measure, needs to be appended

        if mNext.hasVoices():
            mNextHasVoices = True
        else:
            mNextHasVoices = False

        # environLocal.printDebug([
        #    'makeTies() dealing with measure', m, 'mNextAdd', mNextAdd])
        # for each measure, go through each element and see if its
        # duration fits in the bar that contains it

        # if there are voices, we must look at voice id values to only
        # connect ties to components in the same voice, assuming there
        # are voices in the next measure
        try:
            mEnd = lastTimeSignature.barDuration.quarterLength
        except AttributeError:
            ts = m.getContextByClass('TimeSignature')
            if ts is not None:
                lastTimeSignature = ts
                mEnd = lastTimeSignature.barDuration.quarterLength
            else:
                mEnd = 4.0  # Default
        if m.hasVoices():
            bundle = m.voices
            mHasVoices = True
        else:
            bundle = [m]
            mHasVoices = False
        # bundle components may be voices, or just a measure
        for v in bundle:
            for e in v:
                if e.classSet.isdisjoint(classFilterList):
                    continue
                vId = v.id
                # environLocal.printDebug([
                #    'Stream.makeTies() iterating over elements in measure',
                #    m, e])
                # check to see if duration is within Measure
                eOffset = v.elementOffset(e)
                eEnd = opFrac(eOffset + e.duration.quarterLength)
                # assume end can be at boundary of end of measure
                overshot = eEnd - mEnd

                if overshot <= 0:
                    continue
                if eOffset >= mEnd:
                    continue  # skip elements that extend past measure boundary.
                    # raise stream.StreamException(
                    #     'element (%s) has offset %s within a measure '
                    #     'that ends at offset %s' % (e, eOffset, mEnd))

                qLenBegin = mEnd - eOffset
                e, eRemain = e.splitAtQuarterLength(
                    qLenBegin,
                    retainOrigin=True,
                    displayTiedAccidentals=displayTiedAccidentals
                )

                # manage bridging voices
                if mNextHasVoices:
                    if mHasVoices:  # try to match voice id
                        if not isinstance(vId, int):
                            dst = mNext.voices[vId]
                        else:
                            dst = mNext.getElementById(vId)
                    # src does not have voice, but dst does
                    else:  # place in top-most voice
                        dst = mNext.voices[0]
                else:
                    # mNext has no voices but this one does
                    if mHasVoices:
                        # internalize all components in a voice
                        moveNotesToVoices(mNext)
                        # place in first voice
                        dst = mNext.voices[0]
                    else:  # no voices in either
                        dst = None

                if dst is None:
                    dst = mNext

                # mNext.coreSelfActiveSite(eRemain)
                # manually set activeSite
                # cannot use coreInsert here
                dst.insert(0, eRemain)

                # we are not sure that this element fits
                # completely in the next measure, thus, need to
                # continue processing each measure
                if mNextAdd:
                    # environLocal.printDebug([
                    #    'makeTies() inserting mNext into returnObj',
                    #    mNext])
                    returnObj.insert(mNext.offset, mNext)
        mCount += 1
    for measure in measureStream:
        measure.flattenUnnecessaryVoices(inPlace=True)
    del measureStream  # clean up unused streams

    if not inPlace:
        return returnObj
    else:
        return None


def makeTupletBrackets(s: 'music21.stream.Stream', *, inPlace=False):
    # noinspection PyShadowingNames
    '''
    Given a flat Stream of mixed durations, designates the first and last tuplet of any group
    of tuplets as the start or end of the tuplet, respectively.

    TODO: does not handle nested tuplets

    >>> n = note.Note()
    >>> n.duration.quarterLength = 1/3
    >>> s = stream.Stream()
    >>> s.insert(0, meter.TimeSignature('2/4'))
    >>> s.repeatAppend(n, 6)
    >>> tupletTypes = [x.duration.tuplets[0].type for x in s.notes]
    >>> tupletTypes
    [None, None, None, None, None, None]
    >>> stream.makeNotation.makeTupletBrackets(s, inPlace=True)
    >>> tupletTypes = [x.duration.tuplets[0].type for x in s.notes]
    >>> tupletTypes
    ['start', None, 'stop', 'start', None, 'stop']

    Changed in v1.8: `inPlace` is False by default
    Changed in v7: Legacy behavior of taking in a list of durations removed.
    '''
    durationList = []

    # Stream, as it should be...
    if not inPlace:  # make a copy
        returnObj = s.coreCopyAsDerivation('makeTupletBrackets')
    else:
        returnObj = s

    # only want to look at notes and rests.
    for n in returnObj.notesAndRests:
        if n.duration.isGrace:
            continue
        durationList.append(n.duration)

    tupletMap = []  # a list of [tuplet obj, Duration] pairs
    for dur in durationList:  # all Duration objects
        tupletList = dur.tuplets
        if not tupletList:  # no tuplets
            tupletMap.append([None, dur])
        elif len(tupletList) > 1:
            # for i in range(len(tuplets)):
            #    tupletMap.append([tuplets[i],dur])
            environLocal.warn(
                f'got multi-tuplet duration; cannot yet handle this. {tupletList!r}'
            )
            tupletMap.append([None, dur])
        else:
            tupletMap.append([tupletList[0], dur])

    # have a list of tuplet, Duration pairs
    completionCount: Union[float, int, Fraction] = 0  # qLen currently filled
    completionTarget: Union[float, int, Fraction, None] = None  # qLen necessary to fill tuplet
    for i in range(len(tupletMap)):
        tupletObj, dur = tupletMap[i]

        if i > 0:
            tupletPrevious = tupletMap[i - 1][0]
        else:
            tupletPrevious = None

        if i < len(tupletMap) - 1:
            tupletNext = tupletMap[i + 1][0]
            # if tupletNext != None:
            #     nextNormalType = tupletNext.durationNormal.type
            # else:
            #     nextNormalType = None
        else:
            tupletNext = None
            # nextNormalType = None

        # environLocal.printDebug(['updateTupletType previous, this, next:',
        #                          tupletPrevious, tuplet, tupletNext])

        if tupletObj is not None:
            # thisNormalType = tuplet.durationNormal.type
            completionCount = opFrac(completionCount + dur.quarterLength)
            # if previous tuplet is None, always start
            # always reset completion target
            if tupletPrevious is None or completionTarget is None:
                if tupletNext is None:  # single tuplet w/o tuplets either side
                    tupletObj.type = 'startStop'
                    tupletObj.bracket = False
                    completionCount = 0  # reset
                else:
                    tupletObj.type = 'start'
                    # get total quarter length of this tuplet
                    completionTarget = tupletObj.totalTupletLength()
                    # environLocal.printDebug(['starting tuplet type, value:',
                    #                          tuplet, tuplet.type])
                    # environLocal.printDebug(['completion count, target:',
                    #                          completionCount, completionTarget])

            # if tuplet next is None, always stop
            # if both previous and next are None, just keep a start

            # this, below, is optional:
            # if next normal type is not the same as this one, also stop
            elif tupletNext is None or completionCount >= completionTarget:
                tupletObj.type = 'stop'  # should be impossible once frozen...
                completionTarget = None  # reset
                completionCount = 0  # reset
                # environLocal.printDebug(['stopping tuplet type, value:',
                #                          tuplet, tuplet.type])
                # environLocal.printDebug(['completion count, target:',
                #                          completionCount, completionTarget])

            # if tuplet next and previous not None, increment
            elif tupletPrevious is not None and tupletNext is not None:
                # do not need to change tuplet type; should be None
                pass
                # environLocal.printDebug(['completion count, target:',
                #                          completionCount, completionTarget])

    returnObj.streamStatus.tuplets = True

    if not inPlace:
        return returnObj


def realizeOrnaments(s: 'music21.stream.Stream'):
    '''
    Realize all ornaments on a stream

    Creates a new stream that contains all realized ornaments in addition
    to other elements in the original stream.

    >>> s1 = stream.Stream()
    >>> m1 = stream.Measure()
    >>> m1.number = 1
    >>> m1.append(meter.TimeSignature('4/4'))
    >>> n1 = note.Note('C4', type='whole')
    >>> n1.expressions.append(expressions.Mordent())
    >>> m1.append(n1)
    >>> m2 = stream.Measure()
    >>> m2.number = 2
    >>> n2 = note.Note('D4', type='whole')
    >>> m2.append(n2)
    >>> s1.append(m1)
    >>> s1.append(m2)
    >>> for x in s1.recurse(includeSelf=True):
    ...     x
    <music21.stream.Stream ...>
    <music21.stream.Measure 1 offset=0.0>
    <music21.meter.TimeSignature 4/4>
    <music21.note.Note C>
    <music21.stream.Measure 2 offset=4.0>
    <music21.note.Note D>

    >>> s2 = stream.makeNotation.realizeOrnaments(s1)
    >>> for x in s2.recurse(includeSelf=True):
    ...     x
    <music21.stream.Stream ...>
    <music21.stream.Measure 1 offset=0.0>
    <music21.meter.TimeSignature 4/4>
    <music21.note.Note C>
    <music21.note.Note B>
    <music21.note.Note C>
    <music21.stream.Measure 2 offset=4.0>
    <music21.note.Note D>

    TODO: does not work for Gapful streams because it uses append rather
       than the offset of the original
    '''
    newStream = s.cloneEmpty(derivationMethod='realizeOrnaments')
    newStream.offset = s.offset

    def realizeElementExpressions(innerElement):
        elementHasBeenRealized = False
        for exp in innerElement.expressions:
            if not hasattr(exp, 'realize'):
                continue
            # else:
            before, during, after = exp.realize(innerElement)
            elementHasBeenRealized = True
            for n in before:
                newStream.append(n)
            if during is not None:
                newStream.append(during)
            for n in after:
                newStream.append(n)
        if elementHasBeenRealized is False:
            newStream.append(innerElement)

    # If this streamObj contains more streams (i.e., a Part that contains
    # multiple measures):
    for element in s:
        if element.isStream:
            newStream.append(realizeOrnaments(element))
        else:
            if hasattr(element, 'expressions'):
                realizeElementExpressions(element)
            else:
                newStream.append(element)

    return newStream


def moveNotesToVoices(source: 'music21.stream.Stream', classFilterList=('GeneralNote',)):
    '''
    Move notes into voices.  Happens inplace always.  Returns None
    '''
    from music21.stream import Voice
    dst = Voice()

    # cast to list so source can be edited.
    affectedElements = list(source.getElementsByClass(classFilterList))

    for e in affectedElements:
        dst.insert(source.elementOffset(e), e)
        source.remove(e)
    source.insert(0, dst)


def getTiePitchSet(prior: 'music21.note.NotRest'):
    # noinspection PyShadowingNames
    '''
    helper method for makeAccidentals to get the tie pitch set (or None)
    from the prior

    >>> n1 = note.Note('C4')
    >>> n2 = note.Note('D4')
    >>> n2.tie = tie.Tie('start')
    >>> n3 = note.Note('E4')
    >>> n3.tie = tie.Tie('stop')
    >>> n4 = note.Note('F4')
    >>> n4.tie = tie.Tie('continue')
    >>> c = chord.Chord([n1, n2, n3, n4])
    >>> tps = stream.makeNotation.getTiePitchSet(c)
    >>> isinstance(tps, set)
    True
    >>> sorted(tps)
    ['D4', 'F4']

    Non tie possessing objects return None

    >>> r = bar.Repeat()
    >>> stream.makeNotation.getTiePitchSet(r) is None
    True

    Note or Chord without ties, returns an empty set:

    >>> n = note.Note('F#5')
    >>> stream.makeNotation.getTiePitchSet(n)
    set()

    Rest return None

    >>> r = note.Rest()
    >>> stream.makeNotation.getTiePitchSet(r) is None
    True
    '''
    if not hasattr(prior, 'tie') or not hasattr(prior, 'pitches'):
        return None

    tiePitchSet = set()
    if isinstance(prior, chord.Chord):
        previousNotes = list(prior)
    else:
        previousNotes = [prior]

    for n in previousNotes:
        if n.tie is None or n.tie.type == 'stop' or isinstance(n, note.Unpitched):
            continue
        tiePitchSet.add(n.pitch.nameWithOctave)
    return tiePitchSet

def makeAccidentalsInMeasureStream(
    s: 'music21.stream.Stream',
    *,
    pitchPast: Optional[List[pitch.Pitch]] = None,
    pitchPastMeasure: Optional[List[pitch.Pitch]] = None,
    useKeySignature: Union[bool, key.KeySignature] = True,
    alteredPitches: Optional[List[pitch.Pitch]] = None,
    cautionaryPitchClass: bool = True,
    cautionaryAll: bool = False,
    overrideStatus: bool = False,
    cautionaryNotImmediateRepeat: bool = True,
    tiePitchSet: Optional[Set[str]] = None
):
    '''
    Makes accidentals in place on a stream consisting of only Measures.
    Helper for Stream.makeNotation and Part.makeAccidentals.

    Walks measures in order to update the values for the following keyword
    arguments of :meth:`~music21.stream.base.makeAccidentals` and calls
    that method on each Measure. (For this reason, the values supplied
    for these arguments in the method signature will be used on the first
    measure only, or in the case of `useKeySignature`, not at all if the first
    measure contains a `KeySignature`.)::

        pitchPastMeasure
        useKeySignature
        tiePitchSet

    Operates on the measures in place; make a copy first if this is not desired.
    '''
    if s.getElementsNotOfClass('Measure'):
        raise ValueError(f'{s} must contain only Measures')

    # bool values for useKeySignature are not helpful here
    # because we are definitely searching key signature contexts
    # only key.KeySignature values are interesting
    # but method arg is typed this way for backwards compatibility
    if isinstance(useKeySignature, key.KeySignature):
        ksLast = useKeySignature
    else:
        ksLast = None

    for i, m in enumerate(s):
        # if beyond the first measure, use the pitches from the last
        # measure for context (cautionary accidentals)
        # unless this measure has a key signature object
        if i > 0:
            pitchPastMeasure = None
            if m.keySignature is None:
                pitchPastMeasure = s[i - 1].pitches
            elif ksLast:
                # If there is any key signature object to the left,
                # just get the chromatic pitches from previous measure
                # G-naturals in C major following G-flats in F major need cautionary
                # G-naturals in C major following G-flats in Db major don't
                ksLastDiatonic = [p.name for p in ksLast.getScale().pitches]
                pitchPastMeasure = [p for p in s[i - 1].pitches
                    if p.name not in ksLastDiatonic]
            # Get tiePitchSet from previous measure
            try:
                previousNoteOrChord = s[i - 1][note.NotRest][-1]
                tiePitchSet = getTiePitchSet(previousNoteOrChord)
                if tiePitchSet is not None and m.keySignature is not None:
                    # Get the diatonic pitches in this (new) key
                    # and limit tiePitchSet to just those
                    # Disregard tie continuation on pitches foreign to new key
                    ksNewDiatonic = [p.name for p in m.keySignature.getScale().pitches]
                    tiePitchSet = {tp for tp in tiePitchSet if tp in ksNewDiatonic}
            except (IndexError, StreamException):
                pass

        if m.keySignature is not None:
            ksLast = m.keySignature

        m.makeAccidentals(
            pitchPast=pitchPast,
            pitchPastMeasure=pitchPastMeasure,
            useKeySignature=ksLast,
            alteredPitches=alteredPitches,
            searchKeySignatureByContext=False,
            cautionaryPitchClass=cautionaryPitchClass,
            cautionaryAll=cautionaryAll,
            inPlace=True,
            overrideStatus=overrideStatus,
            cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
            tiePitchSet=tiePitchSet,
        )

def iterateBeamGroups(
    s: 'music21.stream.Stream',
    skipNoBeams=True,
    recurse=True
) -> Generator[List[note.NotRest], None, None]:
    '''
    Generator that yields a List of NotRest objects that fall within a beam group.

    If `skipNoBeams` is True, then NotRest objects that have no beams are skipped.

    Recurse is True by default.

    Unclosed beam groups (like start followed by a Rest before a stop), currently
    will continue to yield until the first stop, but this behavior may change at any time in
    the future as beaming-over-barlines with multiple voices or beaming across
    Parts or PartStaffs is supported.

    >>> from music21.stream.makeNotation import iterateBeamGroups
    >>> sc = converter.parse('tinyNotation: 3/4 c8 d e f g4   a4 b8 a16 g16 f4')
    >>> sc.makeBeams(inPlace=True)
    >>> for beamGroup in iterateBeamGroups(sc):
    ...     print(beamGroup)
    [<music21.note.Note C>, <music21.note.Note D>]
    [<music21.note.Note E>, <music21.note.Note F>]
    [<music21.note.Note B>, <music21.note.Note A>, <music21.note.Note G>]

    >>> for beamGroup in iterateBeamGroups(sc, skipNoBeams=False):
    ...     print(beamGroup)
    [<music21.note.Note C>, <music21.note.Note D>]
    [<music21.note.Note E>, <music21.note.Note F>]
    [<music21.note.Note G>]
    [<music21.note.Note A>]
    [<music21.note.Note B>, <music21.note.Note A>, <music21.note.Note G>]
    [<music21.note.Note F>]

    If recurse is False, assumes a flat Score:

    >>> for beamGroup in iterateBeamGroups(sc, recurse=False):
    ...     print(beamGroup)

    >>> for beamGroup in iterateBeamGroups(sc.flatten(), recurse=False):
    ...     print(beamGroup)
    [<music21.note.Note C>, <music21.note.Note D>]
    [<music21.note.Note E>, <music21.note.Note F>]
    [<music21.note.Note B>, <music21.note.Note A>, <music21.note.Note G>]

    New in v6.7.
    '''
    iterator: 'music21.stream.iterator.StreamIterator' = s.recurse() if recurse else s.iter()
    current_beam_group: List[note.NotRest] = []
    in_beam_group: bool = False
    for el in iterator.getElementsByClass('NotRest'):
        first_el_type: Optional[str] = None
        if el.beams and el.beams.getByNumber(1):
            first_el_type = el.beams.getTypeByNumber(1)

        if first_el_type == 'start':
            in_beam_group = True
        if in_beam_group:
            current_beam_group.append(el)
        if first_el_type == 'stop':
            yield current_beam_group
            current_beam_group = []
            in_beam_group = False
        elif not skipNoBeams and not in_beam_group:
            yield [el]

    if current_beam_group:
        yield current_beam_group


def setStemDirectionForBeamGroups(
    s: 'music21.stream.Stream',
    *,
    setNewStems=True,
    overrideConsistentStemDirections=False,
) -> None:
    '''
    Find all beam groups and set all the `stemDirection` tags for notes/chords
    in a beam group to point either up or down.  If any other stem direction is
    encountered ('double', 'noStem', etc.) that note is skipped.

    If all notes have the same (non-unspecified) direction, then they are left alone unless
    `overrideConsistentStemDirections` is True (default: False).  For instance,
    :meth:`~music21.clef.Clef.getStemDirectionForPitches` might say "down" but
    if everything in the beamGroup is either

    if `setANewStems` is True (as by default), then even notes with stemDirection
    of 'unspecified' get a stemDirection.

    Currently assumes that the clef does not change within a beam group.  This
    assumption may change in the future.

    Operates in place.  Run `copy.deepcopy(s)` beforehand for a non-inPlace version.

    New in v6.7.
    '''
    beamGroup: List[note.NotRest]
    for beamGroup in iterateBeamGroups(s, skipNoBeams=True, recurse=True):
        setStemDirectionOneGroup(
            beamGroup,
            setNewStems=setNewStems,
            overrideConsistentStemDirections=overrideConsistentStemDirections
        )


def setStemDirectionOneGroup(
    group: List[note.NotRest],
    *,
    setNewStems=True,
    overrideConsistentStemDirections=False,
) -> None:
    '''
    Helper function to set stem directions for one beam group (or perhaps a beat, etc.)

    See setStemDirectionForBeamGroups for detailed information.

    New in v6.7.
    '''
    if not group:  # pragma: no cover
        return  # should not happen

    stem_directions = {n.stemDirection for n in group
                       if n.stemDirection in ('up', 'down', 'unspecified')}
    if 'unspecified' in stem_directions:
        has_consistent_stem_directions = False
    elif len(stem_directions) < 2:
        has_consistent_stem_directions = True
    else:
        has_consistent_stem_directions = False

    # noinspection PyTypeChecker
    clef_context: clef.Clef = group[0].getContextByClass(clef.Clef)
    if not clef_context:
        return

    pitchList: List[pitch.Pitch] = []
    for n in group:
        pitchList.extend(n.pitches)
    if not pitchList:
        # Handle empty chord
        return
    groupStemDirection = clef_context.getStemDirectionForPitches(pitchList)

    for n in group:
        noteDirection = n.stemDirection
        if noteDirection == 'unspecified' and not setNewStems:
            continue
        elif (noteDirection in ('up', 'down')
              and not overrideConsistentStemDirections
              and has_consistent_stem_directions):
            continue
        elif noteDirection in ('up', 'down', 'unspecified'):
            n.stemDirection = groupStemDirection



# -----------------------------------------------------------------------------

class Test(unittest.TestCase):
    '''
    Note: most Stream tests are found in stream/tests.py
    '''
    allaBreveBeamTest = "tinyNotation: 2/2 c8 d e f   trip{a b c' a b c'}  f' e' d' G  a b c' d'"

    def testNotesToVoices(self):
        from music21 import stream
        s = stream.Stream()
        n1 = note.Note()
        s.repeatAppend(n1, 4)
        self.assertEqual(len(s), 4)

        moveNotesToVoices(s)
        # now have one component
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0].classes[0], 'Voice')  # default is a Voice
        self.assertEqual(len(s[0]), 4)
        self.assertEqual(str(list(s.voices[0].notesAndRests)),
                         '[<music21.note.Note C>, <music21.note.Note C>, '
                         + '<music21.note.Note C>, <music21.note.Note C>]')

    def testSetStemDirectionOneGroup(self):
        from music21 import converter
        p = converter.parse(self.allaBreveBeamTest)
        p.makeBeams(inPlace=True, setStemDirections=False)
        a, b, c, d = iterateBeamGroups(p)

        def testDirections(group, expected):
            self.assertEqual(len(group), len(expected))
            for j in range(len(group)):
                self.assertEqual(group[j].stemDirection, expected[j])

        testDirections(a, ['unspecified'] * 4)
        setStemDirectionOneGroup(a, setNewStems=False)
        testDirections(a, ['unspecified'] * 4)
        setStemDirectionOneGroup(a)
        testDirections(a, ['up'] * 4)
        for n in a:
            n.stemDirection = 'down'
        setStemDirectionOneGroup(a)
        testDirections(a, ['down'] * 4)
        setStemDirectionOneGroup(a, overrideConsistentStemDirections=True)
        testDirections(a, ['up'] * 4)

        setStemDirectionOneGroup(b)
        testDirections(b, ['down'] * 6)

        # this one is all high but has one very low G
        setStemDirectionOneGroup(c)
        testDirections(c, ['up'] * 4)

        dStems = ['down', 'noStem', 'double', 'up']
        for i, n in enumerate(d):
            n.stemDirection = dStems[i]
        setStemDirectionOneGroup(d)
        testDirections(d, ['down', 'noStem', 'double', 'down'])

    def testSetStemDirectionForBeamGroups(self):
        from music21 import converter
        p = converter.parse(self.allaBreveBeamTest)
        p.makeBeams(inPlace=True, setStemDirections=False)
        d = list(iterateBeamGroups(p))[-1]
        dStems = ['down', 'noStem', 'double', 'up']
        for i, n in enumerate(d):
            n.stemDirection = dStems[i]

        setStemDirectionForBeamGroups(p)
        self.assertEqual([n.stemDirection for n in p.flatten().notes],
                         ['up'] * 4 + ['down'] * 6 + ['up'] * 4
                         + ['down', 'noStem', 'double', 'down']
                         )

    def testSetStemDirectionConsistency(self):
        """
        Stems that would all be up starting from scratch,
        but because of overrideConsistentStemDirections=False,
        we only change the first group with an "unspecified" direction
        """
        from music21 import converter
        p = converter.parse('tinyNotation: 2/4 b8 f8 a8 b8')
        p.makeBeams(inPlace=True)
        self.assertEqual(
            [n.stemDirection for n in p.flatten().notes],
            ['up', 'up', 'up', 'up']
        )

        # make manual changes
        dStems = ['down', 'unspecified', 'down', 'down']
        for n, stemDir in zip(p.flatten().notes, dStems):
            n.stemDirection = stemDir

        setStemDirectionForBeamGroups(p, setNewStems=True, overrideConsistentStemDirections=False)
        self.assertEqual(
            [n.stemDirection for n in p.flatten().notes],
            ['up', 'up', 'down', 'down']
        )

    def testMakeBeamsWithStemDirection(self):
        from music21 import converter
        p = converter.parse(self.allaBreveBeamTest)
        dStems = ['down', 'noStem', 'double', 'up']
        for i, n in enumerate(p.flatten().notes[-4:]):
            n.stemDirection = dStems[i]
        p.makeBeams(inPlace=True)
        self.assertEqual([n.stemDirection for n in p.flatten().notes],
                         ['up'] * 4 + ['down'] * 6 + ['up'] * 4
                         + ['down', 'noStem', 'double', 'down']
                         )

    def testMakeBeamsOnEmptyChord(self):
        from music21 import converter
        p = converter.parse('tinyNotation: 4/4')
        c1 = chord.Chord('d f')
        c1.quarterLength = 0.5
        c2 = chord.Chord('d f')
        c2.quarterLength = 0.5
        p.measure(1).insert(0, c1)
        p.measure(1).insert(0.5, c2)
        p.flatten().notes[0].notes = []
        p.flatten().notes[1].notes = []
        p.makeNotation(inPlace=True)
        self.assertEqual(
            [n.stemDirection for n in p.flatten().notes],
            ['unspecified', 'unspecified'],
        )

    def testMakeBeamsFromTimeSignatureInContext(self):
        from music21 import converter
        from music21 import stream

        p = converter.parse('tinyNotation: 2/4 r2 d8 d8 d8 d8')
        m2 = p[stream.Measure].last()
        self.assertIsNone(m2.timeSignature)
        m2_n0 = m2.notes.first()
        self.assertEqual(len(m2_n0.beams.beamsList), 0)
        m2.makeBeams(inPlace=True)
        self.assertEqual(len(m2_n0.beams.beamsList), 1)

        # Failure if no TimeSignature in context
        m1 = p[stream.Measure].first()
        m1.timeSignature = None
        msg = 'cannot process beams in a Measure without a time signature'
        with self.assertRaisesRegex(stream.StreamException, msg):
            m2.makeBeams(inPlace=True, failOnNoTimeSignature=True)

    def testStreamExceptions(self):
        from music21 import converter
        from music21 import duration
        from music21 import stream
        p = converter.parse(self.allaBreveBeamTest)
        with self.assertRaises(stream.StreamException) as cm:
            p.makeMeasures(meterStream=duration.Duration())
        self.assertEqual(str(cm.exception),
            'meterStream is neither a Stream nor a TimeSignature!')

    def testMakeAccidentalsInMeasureStreamException(self):
        from music21 import converter
        p = converter.parse(self.allaBreveBeamTest)
        with self.assertRaises(ValueError) as cm:
            makeAccidentalsInMeasureStream(p.measure(1))
        self.assertIn('must contain only Measures', str(cm.exception))


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
