# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         rules.py
# Purpose:      music21 class to define rules used in realization
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2010 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest
from music21 import exceptions21
from music21 import prebase

doc_forbidIncompletePossibilities = '''True by default. If True,
    :meth:`~music21.figuredBass.possibility.isIncomplete` is applied to all possibA,
    and all those possibilities for which the method returns False are retained.'''
doc_upperPartsMaxSemitoneSeparation = '''12 by default. A number, in semitones,
    representing the maxSemitoneSeparation argument provided to
    :meth:`~music21.figuredBass.possibility.upperPartsWithinLimit`.
    Method is applied to all possibA, and all those possibilities for which the method returns
    True are retained.'''
doc_forbidVoiceCrossing = '''True by default. If True,
    :meth:`~music21.figuredBass.possibility.voiceCrossing` is applied to all possibA,
    and all those possibilities for which the method returns False are retained.'''
singlePossibilityDoc = [('forbidIncompletePossibilities', doc_forbidIncompletePossibilities),
                        ('upperPartsMaxSemitoneSeparation', doc_upperPartsMaxSemitoneSeparation),
                        ('forbidVoiceCrossing', doc_forbidVoiceCrossing)]
singlePossibilityDoc.sort()


doc_parallelFifths = '''True by default. If True,
    :meth:`~music21.figuredBass.possibility.parallelFifths` is applied to all
    (possibA, possibB) pairs, and all those pairs for which the method returns
    False are retained.'''
doc_parallelOctaves = '''True by default. If True,
    :meth:`~music21.figuredBass.possibility.parallelOctaves` is applied to all
    (possibA, possibB) pairs, and all those pairs for which the method returns
    False are retained.'''
doc_hiddenFifths = '''True by default. If True,
    :meth:`~music21.figuredBass.possibility.hiddenFifth` is applied to all
    (possibA, possibB) pairs, and all those pairs for which the method returns
    False are retained.'''
doc_hiddenOctaves = '''True by default. If True,
    :meth:`~music21.figuredBass.possibility.hiddenOctave` is applied to all
    (possibA, possibB) pairs, and all those pairs for which the method returns
    False are retained.'''
doc_voiceOverlap = '''True by default. If True,
    :meth:`~music21.figuredBass.possibility.voiceOverlap` is applied to all
    (possibA, possibB) pairs, and all those pairs for which the method returns
    False are retained.'''
doc_partMovementLimits = '''[] (empty list) by default. Contains (partNumber, maxSeparation)
    pairs provided as arguments
    to :meth:`~music21.figuredBass.possibility.partMovementsWithinLimits`.
    Method is applied to all (possibA, possibB) pairs, and all those pairs
    for which the method returns True are retained.'''
consecutivePossibilityDoc = [
    ('forbidParallelFifths', doc_parallelFifths),
    ('forbidParallelOctaves', doc_parallelOctaves),
    ('forbidHiddenFifths', doc_hiddenFifths),
    ('forbidHiddenOctaves', doc_hiddenOctaves),
    ('forbidVoiceOverlap', doc_voiceOverlap),
    ('partMovementLimits', doc_partMovementLimits),
]
consecutivePossibilityDoc.sort()


doc_domSeventh = '''True by default. If True, Segments
    whose :attr:`~music21.figuredBass.segment.Segment.segmentChord` spells out a
    dominant seventh chord are resolved properly by
    using :meth:`~music21.figuredBass.segment.Segment.resolveDominantSeventhSegment`.'''
doc_dimSeventh = '''True by default. If True, Segments
    whose :attr:`~music21.figuredBass.segment.Segment.segmentChord` spells out
    a fully-diminished seventh chord are resolved properly by
    using :meth:`~music21.figuredBass.segment.Segment.resolveDiminishedSeventhSegment`.'''
doc_augSixth = '''True by default. If True, Segments
    whose :attr:`~music21.figuredBass.segment.Segment.segmentChord` spells out an
    augmented sixth chord are resolved properly by
    using :meth:`~music21.figuredBass.segment.Segment.resolveAugmentedSixthSegment`.'''
doc_doubledRootInDim7 = '''False by default. If True, Diminished seventh resolutions to the
    tonic will contain a doubled *root*, as opposed to a doubled *third*.
    Rule is ignored (determined in context)
    if :attr:`~music21.figuredBass.segment.Segment.segmentChord` is in first inversion.'''
doc_singleToRes = '''False by default. If True, single possibility rules are applied to
    resolution possibilities.'''
doc_consecutiveToRes = '''False by default. If True, consecutive possibility rules are applied
    between (specialPossib, resPossib) pairs.'''
doc_doublings = '''True by default. If True, then doublings in the It+6 chord are limited to the
     tonic, or fifth. Setting this to False allows doubling of the root or third, most likely
    through parallel unisons if :attr:`~music21.figuredBass.rules.Rules.forbidParallelOctaves`
    is set to True.'''
specialResDoc = [('resolveDominantSeventhProperly', doc_domSeventh),
                 ('resolveDiminishedSeventhProperly', doc_dimSeventh),
                 ('resolveAugmentedSixthProperly', doc_augSixth),
                 ('doubledRootInDim7', doc_doubledRootInDim7),
                 ('applySinglePossibRulesToResolution', doc_singleToRes),
                 ('applyConsecutivePossibRulesToResolution', doc_consecutiveToRes),
                 ('restrictDoublingsInItalianA6Resolution', doc_doublings)]
specialResDoc.sort()


class Rules(prebase.ProtoM21Object):
    '''
    A Rules object is provided as an input to a :class:`~music21.figuredBass.segment.Segment`,
    and controls the application of methods designed to filter out undesired possibilities in
    a single Segment or undesired progressions between two consecutive Segments.


    The rules are categorized in an identical manner to methods
    in :mod:`~music21.figuredBass.possibility`:


    1) Single Possibility Rules. These rules apply to any possibility within a
    single Segment (possibA), and
    are applied in finding correct possibilities for a Segment
    in :meth:`~music21.figuredBass.segment.Segment.allCorrectSinglePossibilities`.


    2) Consecutive Possibility Rules. These rules apply between any correct
    single possibility in segmentA
    (possibA) and any correct single possibility in segmentB (possibB),
    segmentB coming directly after segmentA.
    They are applied in finding correct (possibA, possibB) pairs between
    two Segments
    in :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`.


    3) Special Resolution Rules. These rules apply to Segments
    whose :attr:`~music21.figuredBass.segment.Segment.segmentChord` is an
    augmented sixth, dominant seventh, or diminished seventh chord, and are
    applied as necessary in
    :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`.


    >>> from music21.figuredBass import rules
    >>> fbRules = rules.Rules()
    >>> fbRules
    <music21.figuredBass.rules.Rules>
    >>> fbRules.forbidParallelFifths = False
    >>> fbRules.upperPartsMaxSemitoneSeparation = None
    '''
    # Attributes in rules should just point to their corresponding methods in possibility
    _DOC_ORDER = ([_x[0] for _x in singlePossibilityDoc]
                  + [_y[0] for _y in consecutivePossibilityDoc]
                  + [_z[0] for _z in specialResDoc])
    _DOC_ATTR = dict(singlePossibilityDoc + consecutivePossibilityDoc + specialResDoc)

    def __init__(self):
        # Single Possibility rules
        self.forbidIncompletePossibilities = True
        self.upperPartsMaxSemitoneSeparation = 12
        self.forbidVoiceCrossing = True

        # Consecutive Possibility rules
        self.forbidParallelFifths = True
        self.forbidParallelOctaves = True
        self.forbidHiddenFifths = True
        self.forbidHiddenOctaves = True
        self.forbidVoiceOverlap = True
        self.partMovementLimits = []

        # Special resolution rules
        self.resolveDominantSeventhProperly = True
        self.resolveDiminishedSeventhProperly = True
        self.resolveAugmentedSixthProperly = True
        self.doubledRootInDim7 = False
        self.applySinglePossibRulesToResolution = False
        self.applyConsecutivePossibRulesToResolution = False
        self.restrictDoublingsInItalianA6Resolution = True

        self._upperPartsRemainSame = False
        self._partPitchLimits = []
        self._partsToCheck = []

    def _reprInternal(self):
        return ''


class FiguredBassRulesException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

