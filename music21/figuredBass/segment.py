# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      music21 class representing a figured bass note and notation
#                realization.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import collections
import copy
import itertools
import unittest

from typing import Dict, Optional, Union

from music21 import chord
from music21 import environment
from music21 import exceptions21
from music21 import note
from music21 import pitch
from music21 import scale
from music21.figuredBass import possibility
from music21.figuredBass import realizerScale
from music21.figuredBass import resolution
from music21.figuredBass import rules

_MOD = 'figuredBass.segment'

_defaultRealizerScale: Dict[str, Optional[realizerScale.FiguredBassScale]] = {
    'scale': None,  # singleton
}


class Segment:
    _DOC_ORDER = ['allSinglePossibilities',
                  'singlePossibilityRules',
                  'allCorrectSinglePossibilities',
                  'consecutivePossibilityRules',
                  'specialResolutionRules',
                  'allCorrectConsecutivePossibilities',
                  'resolveDominantSeventhSegment',
                  'resolveDiminishedSeventhSegment',
                  'resolveAugmentedSixthSegment']
    _DOC_ATTR = {
        'bassNote': '''A :class:`~music21.note.Note` whose pitch
             forms the bass of each possibility.''',
        'numParts': '''The number of parts (including the bass) that possibilities
             should contain, which
             comes directly from :attr:`~music21.figuredBass.rules.Rules.numParts`
             in the Rules object.''',
        'pitchNamesInChord': '''A list of allowable pitch names.
             This is derived from bassNote.pitch and notationString
             using :meth:`~music21.figuredBass.realizerScale.FiguredBassScale.getPitchNames`.''',
        'allPitchesAboveBass': '''A list of allowable pitches in the upper parts of a possibility.
             This is derived using
             :meth:`~music21.figuredBass.segment.getPitches`, providing bassNote.pitch,
             :attr:`~music21.figuredBass.rules.Rules.maxPitch`
             from the Rules object, and
             :attr:`~music21.figuredBass.segment.Segment.pitchNamesInChord` as arguments.''',
        'segmentChord': ''':attr:`~music21.figuredBass.segment.Segment.allPitchesAboveBass`
             represented as a :class:`~music21.chord.Chord`.''',
        'fbRules': 'A deepcopy of the :class:`~music21.figuredBass.rules.Rules` object provided.',
    }

    def __init__(self,
                 bassNote: Union[str, note.Note] = 'C3',
                 notationString: Optional[str] = None,
                 fbScale: Optional[realizerScale.FiguredBassScale] = None,
                 fbRules: Optional[rules.Rules] = None,
                 numParts=4,
                 maxPitch: Union[str, pitch.Pitch] = 'B5',
                 listOfPitches=None):
        '''
        A Segment corresponds to a 1:1 realization of a bassNote and notationString
        of a :class:`~music21.figuredBass.realizer.FiguredBassLine`.
        It is created by passing six arguments: a
        :class:`~music21.figuredBass.realizerScale.FiguredBassScale`, a bassNote, a notationString,
        a :class:`~music21.figuredBass.rules.Rules` object, a number of parts and a maximum pitch.
        Realizations of a Segment are represented
        as possibility tuples (see :mod:`~music21.figuredBass.possibility` for more details).

        Methods in Python's `itertools <http://docs.python.org/library/itertools.html>`_
        module are used extensively. Methods
        which generate possibilities or possibility progressions return iterators,
        which are turned into lists in the examples
        for display purposes only.

        if fbScale is None, a realizerScale.FiguredBassScale() is created

        if fbRules is None, a rules.Rules() instance is created.  Each Segment gets
        its own deepcopy of the one given.


        Here, a Segment is created using the default values: a FiguredBassScale in C,
        a bassNote of C3, an empty notationString, and a default
        Rules object.

        >>> from music21.figuredBass import segment
        >>> s1 = segment.Segment()
        >>> s1.bassNote
        <music21.note.Note C>
        >>> s1.numParts
        4
        >>> s1.pitchNamesInChord
        ['C', 'E', 'G']
        >>> [str(p) for p in s1.allPitchesAboveBass]
        ['C3', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5', 'E5', 'G5']
        >>> s1.segmentChord
        <music21.chord.Chord C3 E3 G3 C4 E4 G4 C5 E5 G5>
        '''
        if isinstance(bassNote, str):
            bassNote = note.Note(bassNote)
        if isinstance(maxPitch, str):
            maxPitch = pitch.Pitch(maxPitch)

        if fbScale is None:
            if _defaultRealizerScale['scale'] is None:
                _defaultRealizerScale['scale'] = realizerScale.FiguredBassScale()
            fbScale = _defaultRealizerScale['scale']  # save making it

        if fbRules is None:
            self.fbRules = rules.Rules()
        else:
            self.fbRules = copy.deepcopy(fbRules)

        self._specialResolutionRuleChecking = None
        self._singlePossibilityRuleChecking = None
        self._consecutivePossibilityRuleChecking = None

        self.bassNote = bassNote
        self.numParts = numParts
        self._maxPitch = maxPitch
        if notationString is None and listOfPitches is not None:
            # must be a chord symbol or roman num.
            self.pitchNamesInChord = listOfPitches
        # ------ Added to accommodate harmony.ChordSymbol and roman.RomanNumeral objects ------
        else:
            self.pitchNamesInChord = fbScale.getPitchNames(self.bassNote.pitch, notationString)

        self.allPitchesAboveBass = getPitches(self.pitchNamesInChord,
                                              self.bassNote.pitch,
                                              self._maxPitch)
        self.segmentChord = chord.Chord(self.allPitchesAboveBass,
                                        quarterLength=bassNote.quarterLength)
        self._environRules = environment.Environment(_MOD)

    # ------------------------------------------------------------------------------
    # EXTERNAL METHODS

    def singlePossibilityRules(self, fbRules=None):
        '''
        A framework for storing single possibility rules and methods to be applied
        in :meth:`~music21.figuredBass.segment.Segment.allCorrectSinglePossibilities`.
        Takes in a :class:`~music21.figuredBass.rules.Rules` object, fbRules.
        If None then a new rules object is created.

        Items are added within this method in the following form:


        (willRunOnlyIfTrue, methodToRun, keepSolutionsWhichReturn, optionalArgs)


        These items are compiled internally when
        :meth:`~music21.figuredBass.segment.Segment.allCorrectSinglePossibilities`
        is called on a Segment. Here, the compilation of rules and
        methods bases on a default fbRules is shown.

        >>> from music21.figuredBass import segment
        >>> segmentA = segment.Segment()
        >>> allSingleRules = segmentA.singlePossibilityRules()
        >>> segment.printRules(allSingleRules)
        Will run:  Method:                       Keep solutions which return:  Arguments:
        True       isIncomplete                  False                         ['C', 'E', 'G']
        True       upperPartsWithinLimit         True                          12
        True       voiceCrossing                 False                         None


        Here, a modified fbRules is provided, which allows for incomplete possibilities.


        >>> from music21.figuredBass import rules
        >>> fbRules = rules.Rules()
        >>> fbRules.forbidIncompletePossibilities = False
        >>> allSingleRules = segmentA.singlePossibilityRules(fbRules)
        >>> segment.printRules(allSingleRules)
        Will run:  Method:                       Keep solutions which return:  Arguments:
        False      isIncomplete                  False                         ['C', 'E', 'G']
        True       upperPartsWithinLimit         True                          12
        True       voiceCrossing                 False                         None
        '''
        if fbRules is None:
            fbRules = rules.Rules()

        singlePossibRules = [
            (fbRules.forbidIncompletePossibilities,
                 possibility.isIncomplete,
                 False,
                 [self.pitchNamesInChord]),
            (True,
                 possibility.upperPartsWithinLimit,
                 True,
                 [fbRules.upperPartsMaxSemitoneSeparation]),
            (fbRules.forbidVoiceCrossing,
                 possibility.voiceCrossing,
                 False)
        ]

        return singlePossibRules

    def consecutivePossibilityRules(self, fbRules=None):
        '''
        A framework for storing consecutive possibility rules and methods to be applied
        in :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`.
        Takes in a :class:`~music21.figuredBass.rules.Rules` object, fbRules; if None
        then a new rules.Rules() object is created.


        Items are added within this method in the following form:


        (willRunOnlyIfTrue, methodToRun, keepSolutionsWhichReturn, optionalArgs)


        These items are compiled internally when
        :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`
        is called on a Segment. Here, the compilation of rules and methods
        bases on a default fbRules is shown.

        >>> from music21.figuredBass import segment
        >>> segmentA = segment.Segment()
        >>> allConsecutiveRules = segmentA.consecutivePossibilityRules()

        >>> segment.printRules(allConsecutiveRules)
        Will run:  Method:                       Keep solutions which return:  Arguments:
        True       partsSame                     True                          []
        False      upperPartsSame                True                          None
        True       voiceOverlap                  False                         None
        True       partMovementsWithinLimits     True                          []
        True       parallelFifths                False                         None
        True       parallelOctaves               False                         None
        True       hiddenFifth                   False                         None
        True       hiddenOctave                  False                         None
        False      couldBeItalianA6Resolution    True           [<music21.pitch.Pitch C3>,
                                                                 <music21.pitch.Pitch C3>,
                                                                 <music21.pitch.Pitch E3>,
                                                                 <music21.pitch.Pitch G3>], True


        Now, a modified fbRules is provided, allowing hidden octaves and
        voice overlap, and limiting the soprano line to stepwise motion.


        >>> from music21.figuredBass import rules
        >>> fbRules = rules.Rules()
        >>> fbRules.forbidVoiceOverlap = False
        >>> fbRules.forbidHiddenOctaves = False
        >>> fbRules.partMovementLimits.append((1, 2))
        >>> allConsecutiveRules = segmentA.consecutivePossibilityRules(fbRules)
        >>> segment.printRules(allConsecutiveRules)
        Will run:  Method:                       Keep solutions which return:  Arguments:
        True       partsSame                     True                          []
        False      upperPartsSame                True                          None
        False      voiceOverlap                  False                         None
        True       partMovementsWithinLimits     True                          [(1, 2)]
        True       parallelFifths                False                         None
        True       parallelOctaves               False                         None
        True       hiddenFifth                   False                         None
        False      hiddenOctave                  False                         None
        False      couldBeItalianA6Resolution    True           [<music21.pitch.Pitch C3>,
                                                                 <music21.pitch.Pitch C3>,
                                                                 <music21.pitch.Pitch E3>,
                                                                 <music21.pitch.Pitch G3>], True
        '''
        if fbRules is None:
            fbRules = rules.Rules()

        isItalianAugmentedSixth = self.segmentChord.isItalianAugmentedSixth()

        consecutivePossibRules = [
            (True, possibility.partsSame, True, [fbRules._partsToCheck]),
            (fbRules._upperPartsRemainSame, possibility.upperPartsSame, True),
            (fbRules.forbidVoiceOverlap, possibility.voiceOverlap, False),
            (True, possibility.partMovementsWithinLimits, True, [fbRules.partMovementLimits]),
            (fbRules.forbidParallelFifths, possibility.parallelFifths, False),
            (fbRules.forbidParallelOctaves, possibility.parallelOctaves, False),
            (fbRules.forbidHiddenFifths, possibility.hiddenFifth, False),
            (fbRules.forbidHiddenOctaves, possibility.hiddenOctave, False),
            (fbRules.resolveAugmentedSixthProperly and isItalianAugmentedSixth,
                possibility.couldBeItalianA6Resolution,
                True,
                [_unpackTriad(self.segmentChord), fbRules.restrictDoublingsInItalianA6Resolution])
        ]

        return consecutivePossibRules

    def specialResolutionRules(self, fbRules=None):
        '''
        A framework for storing methods which perform special resolutions
        on Segments. Unlike the methods in
        :meth:`~music21.figuredBass.segment.Segment.singlePossibilityRules` and
        :meth:`~music21.figuredBass.segment.Segment.consecutivePossibilityRules`,
        these methods deal with the Segment itself, and rely on submethods
        to resolve the individual possibilities accordingly depending on what
        the resolution Segment is.

        If fbRules is None, then a new rules.Rules() object is created.

        Items are added within this method in the following form:


        (willRunOnlyIfTrue, methodToRun, optionalArgs)


        These items are compiled internally
        when :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`
        is called on a Segment. Here, the compilation of rules and methods
        based on a default fbRules is shown.

        >>> from music21.figuredBass import segment
        >>> segmentA = segment.Segment()
        >>> allSpecialResRules = segmentA.specialResolutionRules()
        >>> segment.printRules(allSpecialResRules, maxLength=3)
        Will run:  Method:                          Arguments:
        False      resolveDominantSeventhSegment    None
        False      resolveDiminishedSeventhSegment  False
        False      resolveAugmentedSixthSegment     None


        Dominant Seventh Segment:


        >>> from music21 import note
        >>> segmentA = segment.Segment(bassNote=note.Note('B2'), notationString='6,5')
        >>> allSpecialResRules = segmentA.specialResolutionRules()
        >>> segment.printRules(allSpecialResRules, maxLength=3)
        Will run:  Method:                          Arguments:
        True       resolveDominantSeventhSegment    None
        False      resolveDiminishedSeventhSegment  False
        False      resolveAugmentedSixthSegment     None


        Fully-Diminished Seventh Segment:


        >>> segmentA = segment.Segment(bassNote=note.Note('B2'), notationString='-7')
        >>> allSpecialResRules = segmentA.specialResolutionRules()
        >>> segment.printRules(allSpecialResRules, maxLength=3)
        Will run:  Method:                          Arguments:
        False      resolveDominantSeventhSegment    None
        True       resolveDiminishedSeventhSegment  False
        False      resolveAugmentedSixthSegment     None


        Augmented Sixth Segment:


        >>> segmentA = segment.Segment(bassNote=note.Note('A-2'), notationString='#6,b5')
        >>> allSpecialResRules = segmentA.specialResolutionRules()
        >>> segment.printRules(allSpecialResRules, maxLength=3)
        Will run:  Method:                          Arguments:
        False      resolveDominantSeventhSegment    None
        False      resolveDiminishedSeventhSegment  False
        True       resolveAugmentedSixthSegment     None
        '''
        if fbRules is None:
            fbRules = rules.Rules()

        isDominantSeventh = self.segmentChord.isDominantSeventh()
        isDiminishedSeventh = self.segmentChord.isDiminishedSeventh()
        isAugmentedSixth = self.segmentChord.isAugmentedSixth()

        specialResRules = [
            (fbRules.resolveDominantSeventhProperly and isDominantSeventh,
             self.resolveDominantSeventhSegment),
            (fbRules.resolveDiminishedSeventhProperly and isDiminishedSeventh,
                self.resolveDiminishedSeventhSegment,
                [fbRules.doubledRootInDim7]),
            (fbRules.resolveAugmentedSixthProperly and isAugmentedSixth,
                self.resolveAugmentedSixthSegment)
        ]

        return specialResRules

    def resolveDominantSeventhSegment(self, segmentB):
        '''
        Can resolve a Segment whose :attr:`~music21.figuredBass.segment.Segment.segmentChord`
        spells out a dominant seventh chord. If no applicable method in
        :mod:`~music21.figuredBass.resolution` can be used, the Segment is resolved
        as an ordinary Segment.


        >>> from music21.figuredBass import segment
        >>> from music21 import note
        >>> segmentA = segment.Segment(bassNote=note.Note('G2'), notationString='7')
        >>> allDomPossib = segmentA.allCorrectSinglePossibilities()
        >>> allDomPossibList = list(allDomPossib)
        >>> len(allDomPossibList)
        8
        >>> allDomPossibList[2]
        (<music21.pitch.Pitch D4>, <music21.pitch.Pitch B3>,
         <music21.pitch.Pitch F3>, <music21.pitch.Pitch G2>)
        >>> allDomPossibList[5]
        (<music21.pitch.Pitch D5>, <music21.pitch.Pitch B4>,
         <music21.pitch.Pitch F4>, <music21.pitch.Pitch G2>)

        Here, the Soprano pitch of resolution (C6) exceeds default maxPitch of B5, so
        it's filtered out.

        >>> [p.nameWithOctave for p in allDomPossibList[7]]
        ['B5', 'F5', 'D5', 'G2']


        >>> segmentB = segment.Segment(bassNote=note.Note('C3'), notationString='')
        >>> domResPairs = segmentA.resolveDominantSeventhSegment(segmentB)
        >>> domResPairsList = list(domResPairs)
        >>> len(domResPairsList)
        7
        >>> domResPairsList[2]
        ((<music21.pitch.Pitch D4>, <...B3>, <...F3>, <...G2>),
         (<...C4>, <...C4>, <...E3>, <...C3>))
        >>> domResPairsList[5]
        ((<...D5>, <...B4>, <...F4>, <...G2>), (<...C5>, <...C5>, <...E4>, <...C3>))
        '''
        domChord = self.segmentChord
        if not domChord.isDominantSeventh():
            # Put here for stand-alone purposes.
            raise SegmentException('Dominant seventh resolution: Not a dominant seventh Segment.')
        domChordInfo = _unpackSeventhChord(domChord)
        dominantScale = scale.MajorScale().derive(domChord)
        minorScale = dominantScale.getParallelMinor()

        tonic = dominantScale.getTonic()
        subdominant = dominantScale.pitchFromDegree(4)
        majSubmediant = dominantScale.pitchFromDegree(6)
        minSubmediant = minorScale.pitchFromDegree(6)

        resChord = segmentB.segmentChord
        domInversion = (domChord.inversion() == 2)
        resInversion = (resChord.inversion())
        resolveV43toI6 = domInversion and resInversion == 1

        if (domChord.inversion() == 0
                and resChord.root().name == tonic.name
                and (resChord.isMajorTriad() or resChord.isMinorTriad())):
            # V7 to I resolutions are always incomplete, with a missing fifth.
            segmentB.fbRules.forbidIncompletePossibilities = False

        dominantResolutionMethods = [
            (resChord.root().name == tonic.name and resChord.isMajorTriad(),
             resolution.dominantSeventhToMajorTonic,
             [resolveV43toI6, domChordInfo]),
            (resChord.root().name == tonic.name and resChord.isMinorTriad(),
                resolution.dominantSeventhToMinorTonic,
                [resolveV43toI6, domChordInfo]),
            ((resChord.root().name == majSubmediant.name
              and resChord.isMinorTriad()
              and domInversion == 0),
                resolution.dominantSeventhToMinorSubmediant,
                [domChordInfo]),
            ((resChord.root().name == minSubmediant.name
                and resChord.isMajorTriad()
                and domInversion == 0),
                resolution.dominantSeventhToMajorSubmediant,
                [domChordInfo]),
            ((resChord.root().name == subdominant.name
                and resChord.isMajorTriad()
                and domInversion == 0),
                resolution.dominantSeventhToMajorSubdominant,
                [domChordInfo]),
            ((resChord.root().name == subdominant.name
                and resChord.isMinorTriad()
                and domInversion == 0),
                resolution.dominantSeventhToMinorSubdominant,
                [domChordInfo])
        ]

        try:
            return self._resolveSpecialSegment(segmentB, dominantResolutionMethods)
        except SegmentException:
            self._environRules.warn(
                'Dominant seventh resolution: No proper resolution available. '
                + 'Executing ordinary resolution.')
            return self._resolveOrdinarySegment(segmentB)

    def resolveDiminishedSeventhSegment(self, segmentB, doubledRoot=False):
        '''
        Can resolve a Segment whose :attr:`~music21.figuredBass.segment.Segment.segmentChord`
        spells out a diminished seventh chord. If no applicable method in
        :mod:`~music21.figuredBass.resolution` can be used, the Segment is resolved
        as an ordinary Segment.

        >>> from music21.figuredBass import segment
        >>> from music21 import note
        >>> segmentA = segment.Segment(bassNote=note.Note('B2'), notationString='b7')
        >>> allDimPossib = segmentA.allCorrectSinglePossibilities()
        >>> allDimPossibList = list(allDimPossib)
        >>> len(allDimPossibList)
        7
        >>> [p.nameWithOctave for p in allDimPossibList[4]]
        ['D5', 'A-4', 'F4', 'B2']
        >>> [p.nameWithOctave for p in allDimPossibList[6]]
        ['A-5', 'F5', 'D5', 'B2']


        >>> segmentB = segment.Segment(bassNote=note.Note('C3'), notationString='')
        >>> dimResPairs = segmentA.resolveDiminishedSeventhSegment(segmentB)
        >>> dimResPairsList = list(dimResPairs)
        >>> len(dimResPairsList)
        7
        >>> dimResPairsList[4]
        ((<...D5>, <...A-4>, <...F4>, <...B2>), (<...E5>, <...G4>, <...E4>, <...C3>))
        >>> dimResPairsList[6]
        ((<...A-5>, <...F5>, <...D5>, <...B2>), (<...G5>, <...E5>, <...E5>, <...C3>))
        '''
        dimChord = self.segmentChord
        if not dimChord.isDiminishedSeventh():
            # Put here for stand-alone purposes.
            raise SegmentException(
                'Diminished seventh resolution: Not a diminished seventh Segment.')
        dimChordInfo = _unpackSeventhChord(dimChord)
        dimScale = scale.HarmonicMinorScale().deriveByDegree(7, dimChord.root())
        # minorScale = dimScale.getParallelMinor()

        tonic = dimScale.getTonic()
        subdominant = dimScale.pitchFromDegree(4)

        resChord = segmentB.segmentChord
        if dimChord.inversion() == 1:  # Doubled root in context
            if resChord.inversion() == 0:
                doubledRoot = True
            elif resChord.inversion() == 1:
                doubledRoot = False

        diminishedResolutionMethods = [
            (resChord.root().name == tonic.name and resChord.isMajorTriad(),
             resolution.diminishedSeventhToMajorTonic,
             [doubledRoot, dimChordInfo]),
            (resChord.root().name == tonic.name and resChord.isMinorTriad(),
                resolution.diminishedSeventhToMinorTonic,
                [doubledRoot, dimChordInfo]),
            (resChord.root().name == subdominant.name and resChord.isMajorTriad(),
                resolution.diminishedSeventhToMajorSubdominant,
                [dimChordInfo]),
            (resChord.root().name == subdominant.name and resChord.isMinorTriad(),
                resolution.diminishedSeventhToMinorSubdominant,
                [dimChordInfo])
        ]

        try:
            return self._resolveSpecialSegment(segmentB, diminishedResolutionMethods)
        except SegmentException:
            self._environRules.warn(
                'Diminished seventh resolution: No proper resolution available. '
                + 'Executing ordinary resolution.')
            return self._resolveOrdinarySegment(segmentB)

    def resolveAugmentedSixthSegment(self, segmentB):
        '''
        Can resolve a Segment whose :attr:`~music21.figuredBass.segment.Segment.segmentChord`
        spells out a
        French, German, or Swiss augmented sixth chord. Italian augmented sixth Segments
        are solved as an
        ordinary Segment using :meth:`~music21.figuredBass.possibility.couldBeItalianA6Resolution`.
        If no
        applicable method in :mod:`~music21.figuredBass.resolution` can be used, the Segment
        is resolved
        as an ordinary Segment.


        >>> from music21.figuredBass import segment
        >>> from music21 import note
        >>> segmentA = segment.Segment(bassNote=note.Note('A-2'), notationString='#6,b5,3')
        >>> segmentA.pitchNamesInChord  # spell out a Gr+6 chord
        ['A-', 'C', 'E-', 'F#']
        >>> allAugSixthPossib = segmentA.allCorrectSinglePossibilities()
        >>> allAugSixthPossibList = list(allAugSixthPossib)
        >>> len(allAugSixthPossibList)
        7

        >>> allAugSixthPossibList[1]
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch F#3>, <...E-3>, <...A-2>)
        >>> allAugSixthPossibList[4]
        (<music21.pitch.Pitch C5>, <music21.pitch.Pitch F#4>, <...E-4>, <...A-2>)


        >>> segmentB = segment.Segment(bassNote=note.Note('G2'), notationString='')
        >>> allAugResPossibPairs = segmentA.resolveAugmentedSixthSegment(segmentB)
        >>> allAugResPossibPairsList = list(allAugResPossibPairs)
        >>> len(allAugResPossibPairsList)
        7
        >>> allAugResPossibPairsList[1]
        ((<...C4>, <...F#3>, <...E-3>, <...A-2>), (<...B3>, <...G3>, <...D3>, <...G2>))
        >>> allAugResPossibPairsList[4]
        ((<...C5>, <...F#4>, <...E-4>, <...A-2>), (<...B4>, <...G4>, <...D4>, <...G2>))
        '''
        augSixthChord = self.segmentChord
        if not augSixthChord.isAugmentedSixth():
            # Put here for stand-alone purposes.
            raise SegmentException('Augmented sixth resolution: Not an augmented sixth Segment.')
        if augSixthChord.isItalianAugmentedSixth():
            return self._resolveOrdinarySegment(segmentB)
        elif augSixthChord.isFrenchAugmentedSixth():
            augSixthType = 1
        elif augSixthChord.isGermanAugmentedSixth():
            augSixthType = 2
        elif augSixthChord.isSwissAugmentedSixth():
            augSixthType = 3
        else:
            self._environRules.warn(
                'Augmented sixth resolution: '
                + 'Augmented sixth type not supported. Executing ordinary resolution.')
            return self._resolveOrdinarySegment(segmentB)

        tonic = resolution._transpose(augSixthChord.bass(), 'M3')
        majorScale = scale.MajorScale(tonic)
        # minorScale = scale.MinorScale(tonic)
        resChord = segmentB.segmentChord
        augSixthChordInfo = _unpackSeventhChord(augSixthChord)

        augmentedSixthResolutionMethods = [
            ((resChord.inversion() == 2
                and resChord.root().name == tonic.name
                and resChord.isMajorTriad()),
             resolution.augmentedSixthToMajorTonic, [augSixthType, augSixthChordInfo]),
            ((resChord.inversion() == 2
                and resChord.root().name == tonic.name
                and resChord.isMinorTriad()),
                resolution.augmentedSixthToMinorTonic,
                [augSixthType, augSixthChordInfo]),
            ((majorScale.pitchFromDegree(5).name == resChord.bass().name
                and resChord.isMajorTriad()),
                resolution.augmentedSixthToDominant,
                [augSixthType, augSixthChordInfo])
        ]

        try:
            return self._resolveSpecialSegment(segmentB, augmentedSixthResolutionMethods)
        except SegmentException:
            self._environRules.warn(
                'Augmented sixth resolution: No proper resolution available. '
                + 'Executing ordinary resolution.')
            return self._resolveOrdinarySegment(segmentB)

    def allSinglePossibilities(self):
        '''
        Returns an iterator through a set of naive possibilities for
        a Segment, using :attr:`~music21.figuredBass.segment.Segment.numParts`,
        the pitch of :attr:`~music21.figuredBass.segment.Segment.bassNote`, and
        :attr:`~music21.figuredBass.segment.Segment.allPitchesAboveBass`.

        >>> from music21.figuredBass import segment
        >>> segmentA = segment.Segment()
        >>> allPossib = segmentA.allSinglePossibilities()
        >>> allPossib.__class__
        <... 'itertools.product'>


        The number of naive possibilities is always the length of
        :attr:`~music21.figuredBass.segment.Segment.allPitchesAboveBass`
        raised to the (:attr:`~music21.figuredBass.segment.Segment.numParts` - 1)
        power. The power is 1 less than the number of parts because
        the bass pitch is constant.


        >>> allPossibList = list(allPossib)
        >>> len(segmentA.allPitchesAboveBass)
        9
        >>> segmentA.numParts
        4
        >>> len(segmentA.allPitchesAboveBass) ** (segmentA.numParts-1)
        729
        >>> len(allPossibList)
        729

        >>> for i in (81, 275, 426):
        ...    [str(p) for p in allPossibList[i]]
        ['E3', 'C3', 'C3', 'C3']
        ['C4', 'C4', 'G4', 'C3']
        ['G4', 'G3', 'C4', 'C3']
        '''
        iterables = [self.allPitchesAboveBass] * (self.numParts - 1)
        iterables.append([pitch.Pitch(self.bassNote.pitch.nameWithOctave)])
        return itertools.product(*iterables)

    def allCorrectSinglePossibilities(self):
        '''
        Uses :meth:`~music21.figuredBass.segment.Segment.allSinglePossibilities` and
        returns an iterator through a set of correct possibilities for
        a Segment, all possibilities which pass all filters in
        :meth:`~music21.figuredBass.segment.Segment.singlePossibilityRules`.


        >>> from music21.figuredBass import segment
        >>> segmentA = segment.Segment()
        >>> allPossib = segmentA.allSinglePossibilities()
        >>> allCorrectPossib = segmentA.allCorrectSinglePossibilities()


        Most of the 729 naive possibilities were filtered out using the default rules set,
        leaving only 21.


        >>> allPossibList = list(allPossib)
        >>> len(allPossibList)
        729
        >>> allCorrectPossibList = list(allCorrectPossib)
        >>> len(allCorrectPossibList)
        21

        >>> for i in (5, 12, 20):
        ...   [str(p) for p in allCorrectPossibList[i]]
        ['E4', 'G3', 'G3', 'C3']
        ['C5', 'G4', 'E4', 'C3']
        ['G5', 'G5', 'E5', 'C3']
        '''
        self._singlePossibilityRuleChecking = _compileRules(
            self.singlePossibilityRules(self.fbRules))
        allA = self.allSinglePossibilities()
        return [possibA for possibA in allA if self._isCorrectSinglePossibility(possibA)]

    def allCorrectConsecutivePossibilities(self, segmentB):
        '''
        Returns an iterator through correct (possibA, possibB) pairs.


        * If segmentA (self) is a special Segment, meaning that one of the Segment
          resolution methods in :meth:`~music21.figuredBass.segment.Segment.specialResolutionRules`
          needs to be applied, then this method returns every correct possibility of segmentA
          matched up with exactly one resolution possibility.


        * If segmentA is an ordinary, non-special Segment, then this method returns every
          combination of correct possibilities of segmentA and correct possibilities of segmentB
          which passes all filters
          in :meth:`~music21.figuredBass.segment.Segment.consecutivePossibilityRules`.


        Two notes on segmentA being a special Segment:


        1. By default resolution possibilities are not filtered
           using :meth:`~music21.figuredBass.segment.Segment.singlePossibilityRules`
           rules of segmentB. Filter by setting
           :attr:`~music21.figuredBass.rules.Rules.applySinglePossibRulesToResolution` to True.


        2. By default, (possibA, possibB) pairs are not filtered
           using :meth:`~music21.figuredBass.segment.Segment.consecutivePossibilityRules`
           rules of segmentA. Filter by setting
           :attr:`~music21.figuredBass.rules.Rules.applyConsecutivePossibRulesToResolution`
           to True.

        >>> from music21.figuredBass import segment
        >>> from music21 import note
        >>> segmentA = segment.Segment(bassNote=note.Note('C3'), notationString='')
        >>> segmentB = segment.Segment(bassNote=note.Note('D3'), notationString='4,3')


        Here, an ordinary resolution is being executed, because segmentA is an ordinary Segment.


        >>> consecutivePairs1 = segmentA.allCorrectConsecutivePossibilities(segmentB)
        >>> consecutivePairsList1 = list(consecutivePairs1)
        >>> len(consecutivePairsList1)
        31
        >>> consecutivePairsList1[29]
        ((<...G5>, <...G5>, <...E5>, <...C3>), (<...G5>, <...F5>, <...B4>, <...D3>))


        Here, a special resolution is being executed, because segmentA below is a
        special Segment.


        >>> segmentA = segment.Segment(bassNote=note.Note('D3'), notationString='4,3')
        >>> segmentB = segment.Segment(bassNote=note.Note('C3'), notationString='')
        >>> consecutivePairs2 = segmentA.allCorrectConsecutivePossibilities(segmentB)
        >>> consecutivePairsList2 = list(consecutivePairs2)
        >>> len(consecutivePairsList2)
        6
        >>> consecutivePairsList2[5]
        ((<...G5>, <...F5>, <...B4>, <...D3>), (<...G5>, <...E5>, <...C5>, <...C3>))
        '''
        if not (self.numParts == segmentB.numParts):
            raise SegmentException('Two segments with unequal numParts cannot be compared.')
        if not (self._maxPitch == segmentB._maxPitch):
            raise SegmentException('Two segments with unequal maxPitch cannot be compared.')
        self._specialResolutionRuleChecking = _compileRules(
            self.specialResolutionRules(self.fbRules), 3)
        for (resolutionMethod, args) in self._specialResolutionRuleChecking[True]:
            return resolutionMethod(segmentB, *args)
        return self._resolveOrdinarySegment(segmentB)

    # ------------------------------------------------------------------------------
    # INTERNAL METHODS

    def _isCorrectSinglePossibility(self, possibA):
        '''
        Takes in a possibility (possibA) from a segmentA (self) and returns True
        if the possibility is correct given
        :meth:`~music21.figuredBass.segment.Segment.singlePossibilityRules`
        from segmentA.
        '''
        for (method, isCorrect, args) in self._singlePossibilityRuleChecking[True]:
            if not (method(possibA, *args) == isCorrect):
                return False
        return True

    def _isCorrectConsecutivePossibility(self, possibA, possibB):
        '''
        Takes in a (possibA, possibB) pair from a segmentA (self) and segmentB,
        and returns True if the pair is correct given
        :meth:`~music21.figuredBass.segment.Segment.consecutivePossibilityRules`
        from segmentA.
        '''
        for (method, isCorrect, args) in self._consecutivePossibilityRuleChecking[True]:
            if not (method(possibA, possibB, *args) == isCorrect):
                return False
        return True

    def _resolveOrdinarySegment(self, segmentB):
        '''
        An ordinary segment is defined as a segment which needs no special resolution, where the
        segment does not spell out a special chord, for example, a dominant seventh.


        Finds iterators through all possibA and possibB by calling
        :meth:`~music21.figuredBass.segment.Segment.allCorrectSinglePossibilities`
        on self (segmentA) and segmentB, respectively.
        Returns an iterator through (possibA, possibB) pairs for which
        :meth:`~music21.figuredBass.segment.Segment._isCorrectConsecutivePossibility` returns True.

        >>> from music21.figuredBass import segment
        '''
        self._consecutivePossibilityRuleChecking = _compileRules(
            self.consecutivePossibilityRules(self.fbRules))
        correctA = self.allCorrectSinglePossibilities()
        correctB = segmentB.allCorrectSinglePossibilities()
        correctAB = itertools.product(correctA, correctB)
        return filter(lambda possibAB: self._isCorrectConsecutivePossibility(possibA=possibAB[0],
                                                                              possibB=possibAB[1]),
                       correctAB)

    def _resolveSpecialSegment(self, segmentB, specialResolutionMethods):
        resolutionMethodExecutor = _compileRules(specialResolutionMethods, 3)
        for (resolutionMethod, args) in resolutionMethodExecutor[True]:
            iterables = []
            for arg in args:
                iterables.append(itertools.repeat(arg))
            resolutions = map(resolutionMethod, self.allCorrectSinglePossibilities(), *iterables)
            correctAB = zip(self.allCorrectSinglePossibilities(), resolutions)
            correctAB = filter(lambda possibAB: possibility.pitchesWithinLimit(
                possibA=possibAB[1],
                maxPitch=segmentB._maxPitch),
                correctAB)
            if self.fbRules.applyConsecutivePossibRulesToResolution:
                correctAB = filter(lambda possibAB: self._isCorrectConsecutivePossibility(
                    possibA=possibAB[0],
                    possibB=possibAB[1]),
                    correctAB)
            if self.fbRules.applySinglePossibRulesToResolution:
                segmentB._singlePossibilityRuleChecking = _compileRules(
                    segmentB.singlePossibilityRules(segmentB.fbRules))
                correctAB = filter(lambda possibAB: segmentB._isCorrectSinglePossibility(
                    possibA=possibAB[1]),
                    correctAB)
            return correctAB

        raise SegmentException('No standard resolution available.')


class OverlaidSegment(Segment):
    '''
    Class to allow Segments to be overlaid with non-chord notes.
    '''

    def allSinglePossibilities(self):
        iterables = [self.allPitchesAboveBass] * (self.numParts - 1)  # Parts 1 -> n-1
        iterables.append([pitch.Pitch(self.bassNote.pitch.nameWithOctave)])  # Part n
        for (partNumber, partPitch) in self.fbRules._partPitchLimits:
            iterables[partNumber - 1] = [pitch.Pitch(partPitch.nameWithOctave)]
        return itertools.product(*iterables)


# HELPER METHODS
# --------------
def getPitches(pitchNames=('C', 'E', 'G'),
               bassPitch: Union[str, pitch.Pitch] = 'C3',
               maxPitch: Union[str, pitch.Pitch] = 'C8'):
    '''
    Given a list of pitchNames, a bassPitch, and a maxPitch, returns a sorted list of
    pitches between the two limits (inclusive) which correspond to items in pitchNames.

    >>> from music21.figuredBass import segment
    >>> from music21 import pitch

    >>> pitches = segment.getPitches()
    >>> print(', '.join([p.nameWithOctave for p in pitches]))
    C3, E3, G3, C4, E4, G4, C5, E5, G5, C6, E6, G6, C7, E7, G7, C8

    >>> pitches = segment.getPitches(['G', 'B', 'D', 'F'], bassPitch=pitch.Pitch('B2'))
    >>> print(', '.join([p.nameWithOctave for p in pitches]))
    B2, D3, F3, G3, B3, D4, F4, G4, B4, D5, F5, G5, B5, D6, F6, G6, B6, D7, F7, G7, B7

    >>> pitches = segment.getPitches(['F##', 'A#', 'C#'], bassPitch=pitch.Pitch('A#3'))
    >>> print(', '.join([p.nameWithOctave for p in pitches]))
    A#3, C#4, F##4, A#4, C#5, F##5, A#5, C#6, F##6, A#6, C#7, F##7, A#7
    '''
    if isinstance(bassPitch, str):
        bassPitch = pitch.Pitch(bassPitch)
    if isinstance(maxPitch, str):
        maxPitch = pitch.Pitch(maxPitch)

    iter1 = itertools.product(pitchNames, range(maxPitch.octave + 1))
    iter2 = map(lambda x: pitch.Pitch(x[0] + str(x[1])), iter1)
    iter3 = itertools.filterfalse(lambda samplePitch: bassPitch > samplePitch, iter2)
    iter4 = itertools.filterfalse(lambda samplePitch: samplePitch > maxPitch, iter3)
    allPitches = list(iter4)
    allPitches.sort()
    return allPitches


def _unpackSeventhChord(seventhChord):
    bass = seventhChord.bass()
    root = seventhChord.root()
    third = seventhChord.getChordStep(3)
    fifth = seventhChord.getChordStep(5)
    seventh = seventhChord.getChordStep(7)
    seventhChordInfo = [bass, root, third, fifth, seventh]
    return seventhChordInfo


def _unpackTriad(threePartChord):
    bass = threePartChord.bass()
    root = threePartChord.root()
    third = threePartChord.getChordStep(3)
    fifth = threePartChord.getChordStep(5)
    threePartChordInfo = [bass, root, third, fifth]
    return threePartChordInfo


def _compileRules(rulesList, maxLength=4):
    ruleChecking = collections.defaultdict(list)
    for ruleIndex in range(len(rulesList)):
        args = []
        if len(rulesList[ruleIndex]) == maxLength:
            args = rulesList[ruleIndex][-1]
        if maxLength == 4:
            (shouldRunMethod, method, isCorrect) = rulesList[ruleIndex][0:3]
            ruleChecking[shouldRunMethod].append((method, isCorrect, args))
        elif maxLength == 3:
            (shouldRunMethod, method) = rulesList[ruleIndex][0:2]
            ruleChecking[shouldRunMethod].append((method, args))

    return ruleChecking


def printRules(rulesList, maxLength=4):
    '''
    Method which can print to the console rules inputted into
    :meth:`~music21.figuredBass.segment.Segment.singlePossibilityRules`,
    :meth:`~music21.figuredBass.segment.Segment.consecutivePossibilityRules`, and
    :meth:`~music21.figuredBass.segment.Segment.specialResolutionRules`.
    For the first two methods, maxLength is 4. For the third method, maxLength is 3.

    OMIT_FROM_DOCS
    maxLength is the maximum length of a rule, a rule which includes arguments,
    because arguments are optional.
    '''
    MAX_SIZE = 30
    for rule in rulesList:
        if len(rule[1].__name__) >= MAX_SIZE:
            MAX_SIZE = len(rule[1].__name__) + 2

    def padMethod(m):
        methodName = m.__name__[0:MAX_SIZE]
        if len(methodName) < MAX_SIZE:
            methodName += ' ' * (MAX_SIZE - len(methodName))
        return methodName

    methodStr = 'Method:' + ' ' * (MAX_SIZE - 7)
    if maxLength == 4:
        print(f'Will run:  {methodStr}Keep solutions which return:  Arguments:')
    elif maxLength == 3:
        print(f'Will run:  {methodStr}Arguments:')

    for ruleIndex in range(len(rulesList)):
        ruleToPrint = None
        args = []
        if len(rulesList[ruleIndex]) == maxLength:
            args = rulesList[ruleIndex][-1]
        if not args:
            argsString = 'None'
        else:
            argsString = ''
            for itemIndex in range(len(args)):
                argsString += str(args[itemIndex])
                if not itemIndex == len(args) - 1:
                    argsString += ', '
        if maxLength == 4:
            (shouldRunMethod, method, isCorrect) = rulesList[ruleIndex][0:3]
            method = padMethod(method)
            ruleToPrint = f'{str(shouldRunMethod):11}{method}{str(isCorrect):30}{argsString}'
        elif maxLength == 3:
            (shouldRunMethod, method) = rulesList[ruleIndex][0:2]
            method = padMethod(method)
            ruleToPrint = f'{str(shouldRunMethod):11}{method}{argsString}'
        print(ruleToPrint)


class SegmentException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

