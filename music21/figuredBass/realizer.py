# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         realizer.py
# Purpose:      music21 class to define a figured bass line, consisting of notes
#                and figures in a given key.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module, the heart of fbRealizer, is all about realizing
a bass line of (bassNote, notationString)
pairs. All it takes to create well-formed realizations of a
bass line is a few lines of music21 code,
from start to finish. See :class:`~music21.figuredBass.realizer.FiguredBassLine` for more details.

>>> from music21.figuredBass import realizer
>>> from music21 import note
>>> fbLine = realizer.FiguredBassLine()
>>> fbLine.addElement(note.Note('C3'))
>>> fbLine.addElement(note.Note('D3'), '4,3')
>>> fbLine.addElement(note.Note('C3', quarterLength = 2.0))
>>> allSols = fbLine.realize()
>>> allSols.getNumSolutions()
30
>>> #_DOCS_SHOW allSols.generateRandomRealizations(14).show()

    .. image:: images/figuredBass/fbRealizer_intro.*
        :width: 500


The same can be accomplished by taking the notes and notations
from a :class:`~music21.stream.Stream`.
See :meth:`~music21.figuredBass.realizer.figuredBassFromStream` for more details.


>>> s = converter.parse('tinynotation: C4 D4_4,3 C2', makeNotation=False)
>>> fbLine = realizer.figuredBassFromStream(s)
>>> allSols2 = fbLine.realize()
>>> allSols2.getNumSolutions()
30
'''

import collections
import copy
import random
import unittest


from music21 import chord
from music21 import clef
from music21 import exceptions21
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
from music21.figuredBass import checker
from music21.figuredBass import notation
from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.figuredBass import segment

_MOD = 'figuredBass.realizer'


def figuredBassFromStream(streamPart):
    '''
    Takes a :class:`~music21.stream.Part` (or another :class:`~music21.stream.Stream` subclass)
    and returns a :class:`~music21.figuredBass.realizer.FiguredBassLine` object whose bass notes
    have notations taken from the lyrics in the source stream. This method along with the
    :meth:`~music21.figuredBass.realizer.FiguredBassLine.realize` method provide the easiest
    way of converting from a notated version of a figured bass (such as in a MusicXML file) to
    a realized version of the same line.

    >>> s = converter.parse('tinynotation: 4/4 C4 D8_6 E8_6 F4 G4_7 c1', makeNotation=False)
    >>> fb = figuredBass.realizer.figuredBassFromStream(s)
    >>> fb
    <music21.figuredBass.realizer.FiguredBassLine object at 0x...>

    >>> fbRules = figuredBass.rules.Rules()
    >>> fbRules.partMovementLimits = [(1, 2), (2, 12), (3, 12)]
    >>> fbRealization = fb.realize(fbRules)
    >>> fbRealization.getNumSolutions()
    13
    >>> #_DOCS_SHOW fbRealization.generateRandomRealizations(8).show()

    .. image:: images/figuredBass/fbRealizer_fbStreamPart.*
        :width: 500

    '''
    sf = streamPart.flat
    sfn = sf.notes

    keyList = sf.getElementsByClass(key.Key)
    myKey = None
    if not keyList:
        keyList = sf.getElementsByClass(key.KeySignature)
        if not keyList:
            myKey = key.Key('C')
        else:
            myKey = keyList[0].asKey('major')
    else:
        myKey = keyList[0]

    tsList = sf.getElementsByClass(meter.TimeSignature)
    if not tsList:
        ts = meter.TimeSignature('4/4')
    else:
        ts = tsList[0]

    fb = FiguredBassLine(myKey, ts)
    if streamPart.hasMeasures():
        paddingLeft = streamPart.measure(0).paddingLeft
        if paddingLeft != 0.0:
            fb._paddingLeft = paddingLeft

    for n in sfn:
        if n.lyrics:
            annotationString = ', '.join([x.text for x in n.lyrics])
            fb.addElement(n, annotationString)
        else:
            fb.addElement(n)

    return fb


def addLyricsToBassNote(bassNote, notationString=None):
    '''
    Takes in a bassNote and a corresponding notationString as arguments.
    Adds the parsed notationString as lyrics to the bassNote, which is
    useful when displaying the figured bass in external software.

    >>> from music21.figuredBass import realizer
    >>> from music21 import note
    >>> n1 = note.Note('G3')
    >>> realizer.addLyricsToBassNote(n1, '6,4')
    >>> n1.lyrics[0].text
    '6'
    >>> n1.lyrics[1].text
    '4'
    >>> #_DOCS_SHOW n1.show()

    .. image:: images/figuredBass/fbRealizer_lyrics.*
        :width: 100
    '''
    bassNote.lyrics = []
    n = notation.Notation(notationString)
    if not n.figureStrings:
        return
    maxLength = 0
    for fs in n.figureStrings:
        if len(fs) > maxLength:
            maxLength = len(fs)
    for fs in n.figureStrings:
        spacesInFront = ''
        for i in range(maxLength - len(fs)):
            spacesInFront += ' '
        bassNote.addLyric(spacesInFront + fs, applyRaw=True)


class FiguredBassLine:
    '''
    A FiguredBassLine is an interface for realization of a line of (bassNote, notationString) pairs.
    Currently, only 1:1 realization is supported, meaning that every bassNote is realized and the
    :attr:`~music21.note.GeneralNote.quarterLength` or duration of a realization above a bassNote
    is identical to that of the bassNote.


    `inKey` defaults to C major.

    `inTime` defaults to 4/4.

    >>> from music21.figuredBass import realizer
    >>> from music21 import key
    >>> from music21 import meter
    >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
    >>> fbLine.inKey
    <music21.key.Key of B major>
    >>> fbLine.inTime
    <music21.meter.TimeSignature 3/4>
    '''
    _DOC_ORDER = ['addElement', 'generateBassLine', 'realize']
    _DOC_ATTR = {'inKey': 'A :class:`~music21.key.Key` which implies a scale value, '
                    'scale mode, and key signature for a '
                    ':class:`~music21.figuredBass.realizerScale.FiguredBassScale`.',
                 'inTime': 'A :class:`~music21.meter.TimeSignature` which specifies the '
                    'time signature of realizations outputted to a '
                    ':class:`~music21.stream.Score`.'}

    def __init__(self, inKey=None, inTime=None):
        if inKey is None:
            inKey = key.Key('C')
        if inTime is None:
            inTime = meter.TimeSignature('4/4')

        self.inKey = inKey
        self.inTime = inTime
        self._paddingLeft = 0.0
        self._overlaidParts = stream.Part()
        self._fbScale = realizerScale.FiguredBassScale(inKey.pitchFromDegree(1), inKey.mode)
        self._fbList = []

    def addElement(self, bassObject, notationString=None):
        '''
        Use this method to add (bassNote, notationString) pairs to the bass line. Elements
        are realized in the order they are added.


        >>> from music21.figuredBass import realizer
        >>> from music21 import key
        >>> from music21 import meter
        >>> from music21 import note
        >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
        >>> fbLine.addElement(note.Note('B2'))
        >>> fbLine.addElement(note.Note('C#3'), '6')
        >>> fbLine.addElement(note.Note('D#3'), '6')
        >>> #_DOCS_SHOW fbLine.generateBassLine().show()

        .. image:: images/figuredBass/fbRealizer_bassLine.*
            :width: 200

        OMIT_FROM_DOCS
        >>> fbLine = realizer.FiguredBassLine(key.Key('C'), meter.TimeSignature('4/4'))
        >>> fbLine.addElement(harmony.ChordSymbol('C'))
        >>> fbLine.addElement(harmony.ChordSymbol('G'))

        >>> fbLine = realizer.FiguredBassLine(key.Key('C'), meter.TimeSignature('4/4'))
        >>> fbLine.addElement(roman.RomanNumeral('I'))
        >>> fbLine.addElement(roman.RomanNumeral('V'))
        '''
        bassObject.notationString = notationString
        c = bassObject.classes
        if 'Note' in c:
            self._fbList.append((bassObject, notationString))  # a bass note, and a notationString
            addLyricsToBassNote(bassObject, notationString)
        # ---------- Added to accommodate harmony.ChordSymbol and roman.RomanNumeral objects ---
        elif 'RomanNumeral' in c or 'ChordSymbol' in c:
            self._fbList.append(bassObject)  # a roman Numeral object
        else:
            raise FiguredBassLineException(
                'Not a valid bassObject (only note.Note, '
                + f'harmony.ChordSymbol, and roman.RomanNumeral supported) was {bassObject!r}')

    def generateBassLine(self):
        '''
        Generates the bass line as a :class:`~music21.stream.Score`.

        >>> from music21.figuredBass import realizer
        >>> from music21 import key
        >>> from music21 import meter
        >>> from music21 import note
        >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
        >>> fbLine.addElement(note.Note('B2'))
        >>> fbLine.addElement(note.Note('C#3'), '6')
        >>> fbLine.addElement(note.Note('D#3'), '6')
        >>> #_DOCS_SHOW fbLine.generateBassLine().show()

        .. image:: images/figuredBass/fbRealizer_bassLine.*
            :width: 200


        >>> from music21 import corpus
        >>> sBach = corpus.parse('bach/bwv307')
        >>> sBach['bass'].measure(0).show('text')
        {0.0} ...
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.key.Key of B- major>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note B->
        {0.5} <music21.note.Note C>

        >>> fbLine = realizer.figuredBassFromStream(sBach['bass'])
        >>> fbLine.generateBassLine().measure(1).show('text')
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.key.KeySignature of 2 flats>
        {0.0} <music21.meter.TimeSignature 4/4>
        {3.0} <music21.note.Note B->
        {3.5} <music21.note.Note C>
        '''
        bassLine = stream.Part()
        bassLine.append(clef.BassClef())
        bassLine.append(key.KeySignature(self.inKey.sharps))
        bassLine.append(copy.deepcopy(self.inTime))
        r = None
        if self._paddingLeft != 0.0:
            r = note.Rest(quarterLength=self._paddingLeft)
            bassLine.append(r)

        for (bassNote, unused_notationString) in self._fbList:
            bassLine.append(bassNote)

        bl2 = bassLine.makeNotation(inPlace=False, cautionaryNotImmediateRepeat=False)
        if r is not None:
            m0 = bl2.getElementsByClass('Measure')[0]
            m0.remove(m0.getElementsByClass('Rest')[0])
            m0.padAsAnacrusis()
        return bl2

    def retrieveSegments(self, fbRules=None, numParts=4, maxPitch=None):
        '''
        generates the segmentList from an fbList, including any overlaid Segments

        if fbRules is None, creates a new rules.Rules() object

        if maxPitch is None, uses pitch.Pitch('B5')
        '''
        if fbRules is None:
            fbRules = rules.Rules()
        if maxPitch is None:
            maxPitch = pitch.Pitch('B5')
        segmentList = []
        bassLine = self.generateBassLine()
        if len(self._overlaidParts) >= 1:
            self._overlaidParts.append(bassLine)
            currentMapping = checker.extractHarmonies(self._overlaidParts)
        else:
            currentMapping = checker.createOffsetMapping(bassLine)
        allKeys = sorted(currentMapping.keys())
        bassLine = bassLine.flat.notes
        bassNoteIndex = 0
        previousBassNote = bassLine[bassNoteIndex]
        bassNote = currentMapping[allKeys[0]][-1]
        previousSegment = segment.OverlaidSegment(bassNote, bassNote.notationString,
                                                   self._fbScale,
                                                   fbRules, numParts, maxPitch)
        previousSegment.quarterLength = previousBassNote.quarterLength
        segmentList.append(previousSegment)
        for k in allKeys[1:]:
            (startTime, unused_endTime) = k
            bassNote = currentMapping[k][-1]
            currentSegment = segment.OverlaidSegment(bassNote, bassNote.notationString,
                                                      self._fbScale,
                                                      fbRules, numParts, maxPitch)
            for partNumber in range(1, len(currentMapping[k])):
                upperPitch = currentMapping[k][partNumber - 1]
                currentSegment.fbRules._partPitchLimits.append((partNumber, upperPitch))
            if startTime == previousBassNote.offset + previousBassNote.quarterLength:
                bassNoteIndex += 1
                previousBassNote = bassLine[bassNoteIndex]
                currentSegment.quarterLength = previousBassNote.quarterLength
            else:
                for partNumber in range(len(currentMapping[k]), numParts + 1):
                    previousSegment.fbRules._partsToCheck.append(partNumber)
                # Fictitious, representative only for harmonies preserved
                # with addition of melody or melodies
                currentSegment.quarterLength = 0.0
            segmentList.append(currentSegment)
            previousSegment = currentSegment
        return segmentList

    def overlayPart(self, music21Part):
        self._overlaidParts.append(music21Part)

    def realize(self, fbRules=None, numParts=4, maxPitch=None):
        '''
        Creates a :class:`~music21.figuredBass.segment.Segment`
        for each (bassNote, notationString) pair
        added using :meth:`~music21.figuredBass.realizer.FiguredBassLine.addElement`.
        Each Segment is associated
        with the :class:`~music21.figuredBass.rules.Rules` object provided, meaning that rules are
        universally applied across all Segments. The number of parts in a realization
        (including the bass) can be controlled through numParts, and the maximum pitch can
        likewise be controlled through maxPitch.
        Returns a :class:`~music21.figuredBass.realizer.Realization`.


        If this methods is called without having provided any (bassNote, notationString) pairs,
        a FiguredBassLineException is raised. If only one pair is provided, the Realization will
        contain :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`
        for the one note.

        if `fbRules` is None, creates a new rules.Rules() object

        if `maxPitch` is None, uses pitch.Pitch('B5')



        >>> from music21.figuredBass import realizer
        >>> from music21.figuredBass import rules
        >>> from music21 import key
        >>> from music21 import meter
        >>> from music21 import note
        >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
        >>> fbLine.addElement(note.Note('B2'))
        >>> fbLine.addElement(note.Note('C#3'), '6')
        >>> fbLine.addElement(note.Note('D#3'), '6')
        >>> fbRules = rules.Rules()
        >>> r1 = fbLine.realize(fbRules)
        >>> r1.getNumSolutions()
        208
        >>> fbRules.forbidVoiceOverlap = False
        >>> r2 = fbLine.realize(fbRules)
        >>> r2.getNumSolutions()
        7908

        OMIT_FROM_DOCS
        >>> fbLine3 = realizer.FiguredBassLine(key.Key('C'), meter.TimeSignature('2/4'))
        >>> h1 = harmony.ChordSymbol('C')
        >>> h1.bass().octave = 4
        >>> fbLine3.addElement(h1)
        >>> h2 = harmony.ChordSymbol('G')
        >>> h2.bass().octave = 4
        >>> fbLine3.addElement(h2)
        >>> r3 = fbLine3.realize()
        >>> r3.getNumSolutions()
        13
        >>> fbLine4 = realizer.FiguredBassLine(key.Key('C'), meter.TimeSignature('2/4'))
        >>> fbLine4.addElement(roman.RomanNumeral('I'))
        >>> fbLine4.addElement(roman.RomanNumeral('IV'))
        >>> r4 = fbLine4.realize()
        >>> r4.getNumSolutions()
        13

        '''
        if fbRules is None:
            fbRules = rules.Rules()
        if maxPitch is None:
            maxPitch = pitch.Pitch('B5')

        segmentList = []

        listOfHarmonyObjects = False
        for item in self._fbList:
            try:
                c = item.classes
            except AttributeError:
                continue
            if 'Note' in c:
                break
            # Added to accommodate harmony.ChordSymbol and roman.RomanNumeral objects
            if 'RomanNumeral' in c or 'ChordSymbol' in c:
                listOfHarmonyObjects = True
                break

        if listOfHarmonyObjects:
            for harmonyObject in self._fbList:
                listOfPitchesJustNames = []
                for thisPitch in harmonyObject.pitches:
                    listOfPitchesJustNames.append(thisPitch.name)
                # remove duplicates just in case...
                d = {}
                for x in listOfPitchesJustNames:
                    d[x] = x
                outputList = d.values()

                def g(y):
                    return y if y != 0.0 else 1.0

                passedNote = note.Note(harmonyObject.bass().nameWithOctave,
                                       quarterLength=g(harmonyObject.duration.quarterLength))
                correspondingSegment = segment.Segment(bassNote=passedNote,
                                                       fbScale=self._fbScale,
                                                       fbRules=fbRules,
                                                       numParts=numParts,
                                                       maxPitch=maxPitch,
                                                       listOfPitches=outputList)
                correspondingSegment.quarterLength = g(harmonyObject.duration.quarterLength)
                segmentList.append(correspondingSegment)
        # ---------- Original code - Accommodates a tuple (figured bass)  --------
        else:
            segmentList = self.retrieveSegments(fbRules, numParts, maxPitch)

        if len(segmentList) >= 2:
            for segmentIndex in range(len(segmentList) - 1):
                segmentA = segmentList[segmentIndex]
                segmentB = segmentList[segmentIndex + 1]
                correctAB = segmentA.allCorrectConsecutivePossibilities(segmentB)
                segmentA.movements = collections.defaultdict(list)
                listAB = list(correctAB)
                for (possibA, possibB) in listAB:
                    segmentA.movements[possibA].append(possibB)
            self._trimAllMovements(segmentList)
        elif len(segmentList) == 1:
            segmentA = segmentList[0]
            segmentA.correctA = list(segmentA.allCorrectSinglePossibilities())
        elif not segmentList:
            raise FiguredBassLineException('No (bassNote, notationString) pairs to realize.')

        return Realization(realizedSegmentList=segmentList, inKey=self.inKey,
                           inTime=self.inTime, overlaidParts=self._overlaidParts[0:-1],
                           paddingLeft=self._paddingLeft)

    def _trimAllMovements(self, segmentList):
        '''
        Each :class:`~music21.figuredBass.segment.Segment` which resolves to another
        defines a list of movements, nextMovements. Keys for nextMovements are correct
        single possibilities of the current Segment. For a given key, a value is a list
        of correct single possibilities in the subsequent Segment representing acceptable
        movements between the two. There may be movements in a string of Segments which
        directly or indirectly lead nowhere. This method is designed to be called on
        a list of Segments **after** movements are found, as happens in
        :meth:`~music21.figuredBass.realizer.FiguredBassLine.realize`.
        '''
        if len(segmentList) == 1 or len(segmentList) == 2:
            return True
        elif len(segmentList) >= 3:
            segmentList.reverse()
            # gets this wrong...  # pylint: disable=cell-var-from-loop
            movementsAB = None
            for segmentIndex in range(1, len(segmentList) - 1):
                movementsAB = segmentList[segmentIndex + 1].movements
                movementsBC = segmentList[segmentIndex].movements
                # eliminated = []
                for (possibB, possibCList) in list(movementsBC.items()):
                    if not possibCList:
                        del movementsBC[possibB]
                for (possibA, possibBList) in list(movementsAB.items()):
                    movementsAB[possibA] = list(
                        filter(lambda possibBB: (possibBB in movementsBC), possibBList))

            for (possibA, possibBList) in list(movementsAB.items()):
                if not possibBList:
                    del movementsAB[possibA]

            segmentList.reverse()
            return True


class Realization:
    '''
    Returned by :class:`~music21.figuredBass.realizer.FiguredBassLine` after calling
    :meth:`~music21.figuredBass.realizer.FiguredBassLine.realize`. Allows for the
    generation of realizations as a :class:`~music21.stream.Score`.


    * See the :mod:`~music21.figuredBass.examples` module for examples on the generation
      of realizations.
    * A possibility progression is a valid progression through a string of
      :class:`~music21.figuredBass.segment.Segment` instances.
      See :mod:`~music21.figuredBass.possibility` for more details on possibilities.
    '''
    _DOC_ORDER = ['getNumSolutions', 'generateRandomRealization',
                  'generateRandomRealizations', 'generateAllRealizations',
                  'getAllPossibilityProgressions', 'getRandomPossibilityProgression',
                  'generateRealizationFromPossibilityProgression']
    _DOC_ATTR = {'keyboardStyleOutput': '''True by default. If True, generated realizations
                        are represented in keyboard style, with two staves. If False,
                        realizations are represented in chorale style with n staves,
                        where n is the number of parts. SATB if n = 4.'''}

    def __init__(self, **fbLineOutputs):
        # fbLineOutputs always will have three elements, checks are for sphinx documentation only.
        if 'realizedSegmentList' in fbLineOutputs:
            self._segmentList = fbLineOutputs['realizedSegmentList']
        if 'inKey' in fbLineOutputs:
            self._inKey = fbLineOutputs['inKey']
            self._keySig = key.KeySignature(self._inKey.sharps)
        if 'inTime' in fbLineOutputs:
            self._inTime = fbLineOutputs['inTime']
        if 'overlaidParts' in fbLineOutputs:
            self._overlaidParts = fbLineOutputs['overlaidParts']
        if 'paddingLeft' in fbLineOutputs:
            self._paddingLeft = fbLineOutputs['paddingLeft']
        self.keyboardStyleOutput = True

    def getNumSolutions(self):
        '''
        Returns the number of solutions (unique realizations) to a Realization by calculating
        the total number of paths through a string of :class:`~music21.figuredBass.segment.Segment`
        movements. This is faster and more efficient than compiling each unique realization into a
        list, adding it to a master list, and then taking the length of the master list.

        >>> from music21.figuredBass import examples
        >>> fbLine = examples.exampleB()
        >>> fbRealization = fbLine.realize()
        >>> fbRealization.getNumSolutions()
        422
        >>> fbLine2 = examples.exampleC()
        >>> fbRealization2 = fbLine2.realize()
        >>> fbRealization2.getNumSolutions()
        833
        '''
        if len(self._segmentList) == 1:
            return len(self._segmentList[0].correctA)
        # What if there's only one (bassNote, notationString)?
        self._segmentList.reverse()
        pathList = {}
        for segmentIndex in range(1, len(self._segmentList)):
            segmentA = self._segmentList[segmentIndex]
            newPathList = {}
            if not pathList:
                for possibA in segmentA.movements:
                    newPathList[possibA] = len(segmentA.movements[possibA])
            else:
                for possibA in segmentA.movements:
                    prevValue = 0
                    for possibB in segmentA.movements[possibA]:
                        prevValue += pathList[possibB]
                    newPathList[possibA] = prevValue
            pathList = newPathList

        numSolutions = 0
        for possibA in pathList:
            numSolutions += pathList[possibA]
        self._segmentList.reverse()
        return numSolutions

    def getAllPossibilityProgressions(self):
        '''
        Compiles each unique possibility progression, adding
        it to a master list. Returns the master list.


        .. warning:: This method is unoptimized, and may take a prohibitive amount
            of time for a Realization which has more than 200,000 solutions.
        '''
        progressions = []
        if len(self._segmentList) == 1:
            for possibA in self._segmentList[0].correctA:
                progressions.append([possibA])
            return progressions

        currMovements = self._segmentList[0].movements
        for possibA in currMovements:
            possibBList = currMovements[possibA]
            for possibB in possibBList:
                progressions.append([possibA, possibB])

        for segmentIndex in range(1, len(self._segmentList) - 1):
            currMovements = self._segmentList[segmentIndex].movements
            for unused_progressionIndex in range(len(progressions)):
                progression = progressions.pop(0)
                possibB = progression[-1]
                for possibC in currMovements[possibB]:
                    newProgression = copy.copy(progression)
                    newProgression.append(possibC)
                    progressions.append(newProgression)

        return progressions

    def getRandomPossibilityProgression(self):
        '''
        Returns a random unique possibility progression.
        '''
        progression = []
        if len(self._segmentList) == 1:
            possibA = random.sample(self._segmentList[0].correctA, 1)[0]
            progression.append(possibA)
            return progression

        currMovements = self._segmentList[0].movements
        if self.getNumSolutions() == 0:
            raise FiguredBassLineException('Zero solutions')
        prevPossib = random.sample(currMovements.keys(), 1)[0]
        progression.append(prevPossib)

        for segmentIndex in range(len(self._segmentList) - 1):
            currMovements = self._segmentList[segmentIndex].movements
            nextPossib = random.sample(currMovements[prevPossib], 1)[0]
            progression.append(nextPossib)
            prevPossib = nextPossib

        return progression

    def generateRealizationFromPossibilityProgression(self, possibilityProgression):
        '''
        Generates a realization as a :class:`~music21.stream.Score` given a possibility progression.
        '''
        sol = stream.Score()

        bassLine = stream.Part()
        bassLine.append([copy.deepcopy(self._keySig), copy.deepcopy(self._inTime)])
        r = None
        if self._paddingLeft != 0.0:
            r = note.Rest(quarterLength=self._paddingLeft)
            bassLine.append(copy.deepcopy(r))

        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            sol.insert(0.0, rightHand)
            rightHand.append([copy.deepcopy(self._keySig), copy.deepcopy(self._inTime)])
            if r is not None:
                rightHand.append(copy.deepcopy(r))

            for segmentIndex in range(len(self._segmentList)):
                possibA = possibilityProgression[segmentIndex]
                bassNote = self._segmentList[segmentIndex].bassNote
                bassLine.append(copy.deepcopy(bassNote))
                rhPitches = possibA[0:-1]
                rhChord = chord.Chord(rhPitches)
                rhChord.quarterLength = self._segmentList[segmentIndex].quarterLength
                rightHand.append(rhChord)
            rightHand.insert(0.0, clef.TrebleClef())

            rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
            if r is not None:
                rightHand[0].pop(3)
                rightHand[0].padAsAnacrusis()

        else:  # Chorale-style output
            upperParts = []
            for partNumber in range(len(possibilityProgression[0]) - 1):
                fbPart = stream.Part()
                sol.insert(0.0, fbPart)
                fbPart.append([copy.deepcopy(self._keySig), copy.deepcopy(self._inTime)])
                if r is not None:
                    fbPart.append(copy.deepcopy(r))
                upperParts.append(fbPart)

            for segmentIndex in range(len(self._segmentList)):
                possibA = possibilityProgression[segmentIndex]
                bassNote = self._segmentList[segmentIndex].bassNote
                bassLine.append(copy.deepcopy(bassNote))

                for partNumber in range(len(possibA) - 1):
                    n1 = note.Note(possibA[partNumber])
                    n1.quarterLength = self._segmentList[segmentIndex].quarterLength
                    upperParts[partNumber].append(n1)

            for upperPart in upperParts:
                c = clef.bestClef(upperPart, allowTreble8vb=True, recurse=True)
                upperPart.insert(0.0, c)
                upperPart.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
                if r is not None:
                    upperPart[0].pop(3)
                    upperPart[0].padAsAnacrusis()

        bassLine.insert(0.0, clef.BassClef())
        bassLine.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        if r is not None:
            bassLine[0].pop(3)
            bassLine[0].padAsAnacrusis()
        sol.insert(0.0, bassLine)
        return sol

    def generateAllRealizations(self):
        '''
        Generates all unique realizations as a :class:`~music21.stream.Score`.


        .. warning:: This method is unoptimized, and may take a prohibitive amount
            of time for a Realization which has more than 100 solutions.
        '''
        allSols = stream.Score()
        possibilityProgressions = self.getAllPossibilityProgressions()
        if not possibilityProgressions:
            raise FiguredBassLineException('Zero solutions')
        sol0 = self.generateRealizationFromPossibilityProgression(possibilityProgressions[0])
        for music21Part in sol0:
            allSols.append(music21Part)

        for possibIndex in range(1, len(possibilityProgressions)):
            solX = self.generateRealizationFromPossibilityProgression(
                possibilityProgressions[possibIndex])
            for partIndex in range(len(solX)):
                for music21Measure in solX[partIndex]:
                    allSols[partIndex].append(music21Measure)

        return allSols

    def generateRandomRealization(self):
        '''
        Generates a random unique realization as a :class:`~music21.stream.Score`.
        '''
        possibilityProgression = self.getRandomPossibilityProgression()
        return self.generateRealizationFromPossibilityProgression(possibilityProgression)

    def generateRandomRealizations(self, amountToGenerate=20):
        '''
        Generates *amountToGenerate* unique realizations as a :class:`~music21.stream.Score`.


        .. warning:: This method is unoptimized, and may take a prohibitive amount
            of time if amountToGenerate is more than 100.
        '''
        if amountToGenerate > self.getNumSolutions():
            return self.generateAllRealizations()

        allSols = stream.Score()
        sol0 = self.generateRandomRealization()
        for music21Part in sol0:
            allSols.append(music21Part)

        for unused_counter_solution in range(1, amountToGenerate):
            solX = self.generateRandomRealization()
            for partIndex in range(len(solX)):
                for music21Measure in solX[partIndex]:
                    allSols[partIndex].append(music21Measure)

        return allSols


_DOC_ORDER = [figuredBassFromStream, addLyricsToBassNote,
              FiguredBassLine, Realization]


class FiguredBassLineException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

