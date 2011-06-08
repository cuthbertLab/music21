#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         rules.py
# Purpose:      music21 class to define rules used in realization
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project    
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest


doc_forbidIncompletePossibilities = 'True by default. If True, :meth:`~music21.figuredBass.possibility.isIncomplete` is applied, and all possibA which return True are filtered out.'
doc_upperPartsMaxSemitoneSeparation = '''12 by default. :meth:`~music21.figuredBass.possibility.upperPartsWithinLimit` is applied with the argument (number in semitones) and all possibA 
which return False are filtered out. If set to None, rule is not applied.'''
doc_forbidVoiceCrossing = 'True by default. If True, :meth:`~music21.figuredBass.possibility.voiceCrossing` is applied, and all possibA which return True are filtered out.'
singlePossibilityDoc = [('forbidIncompletePossibilities', doc_forbidIncompletePossibilities),
                        ('upperPartsMaxSemitoneSeparation', doc_upperPartsMaxSemitoneSeparation),
                        ('forbidVoiceCrossing', doc_forbidVoiceCrossing)]  
singlePossibilityDoc.sort()


doc_parallelFifths = 'True by default. If True, :meth:`~music21.figuredBass.possibility.parallelFifths` is applied, and all (possibA, possibB) pairs which return False are filtered out.'
doc_parallelOctaves = 'True by default. If True, :meth:`~music21.figuredBass.possibility.parallelOctaves` is applied, and all (possibA, possibB) pairs which return False are filtered out.'
doc_hiddenFifths = 'True by default. If True, :meth:`~music21.figuredBass.possibility.hiddenFifth` is applied, and all (possibA, possibB) pairs which return False are filtered out.'
doc_hiddenOctaves = 'True by default. If True, :meth:`~music21.figuredBass.possibility.hiddenOctave` is applied, and all (possibA, possibB) pairs which return False are filtered out.'
doc_voiceOverlap = 'True by default. If True, :meth:`~music21.figuredBass.possibility.voiceOverlap` is applied, and all (possibA, possibB) pairs which return False are filtered out.'
doc_partMovementLimits = '''[] (empty list) by default. (partNumber, maxSeparation) pairs provided as arguments to :meth:`~music21.figuredBass.possibility.partMovementsWithinLimits`, 
and all (possibA, possibB) pairs which return False are filtered out.'''
consecPossibilityDoc = [('forbidParallelFifths', doc_parallelFifths),
                        ('forbidParallelOctaves', doc_parallelOctaves),
                        ('forbidHiddenFifths', doc_hiddenFifths),
                        ('forbidHiddenOctaves', doc_hiddenOctaves),
                        ('forbidVoiceOverlap', doc_voiceOverlap),
                        ('partMovementLimits', doc_partMovementLimits)]
consecPossibilityDoc.sort()


doc_domSeventh = 'True by default. If True, resolves dominant seventh Segments properly by using :meth:`~music21.figuredBass.segment.Segment.resolveDominantSeventhSegment`.'
doc_dimSeventh = 'True by default. If True, resolves fully-diminished seventh Segments properly by using :meth:`~music21.figuredBass.segment.Segment.resolveDiminishedSeventhSegment`'
doc_augSixth = 'True by default. If True, resolves augmented sixth Segments properly by using :meth:`~music21.figuredBass.segment.Segment.resolveAugmentedSixthSegment`.'
doc_doubledRootInDim7 = '''False by default. If True, diminished seventh resolutions to the tonic will contain a doubled root, as opposed to a doubled third.
Rule is ignored (determined in context) if :attr:`~music21.figuredBass.segment.Segment.segmentChord` is in first inversion.'''
doc_singleToRes = 'False by default. If True, apply single possibility rules to resolution possibilities.'
doc_consecToRes = 'False by default. If True, apply consecutive possibility rules between (specialPossib, resPossib) pairs.'
specialResDoc = [('resolveDominantSeventhProperly', doc_domSeventh),
                 ('resolveDiminishedSeventhProperly', doc_dimSeventh),
                 ('resolveAugmentedSixthProperly', doc_augSixth),
                 ('doubledRootInDim7', doc_doubledRootInDim7),
                 ('applySinglePossibRulesToResolution', doc_singleToRes),
                 ('applyConsecutivePossibRulesToResolution', doc_consecToRes)]
specialResDoc.sort()


class Rules(object):
    #Attributes in rules should just point to their corresponding methods in possibility
    _DOC_ORDER =  [x[0] for x in singlePossibilityDoc] + [y[0] for y in consecPossibilityDoc] + [z[0] for z in specialResDoc]
    _DOC_ATTR = dict(singlePossibilityDoc + consecPossibilityDoc + specialResDoc)

    def __init__(self):
        '''
        A Rules object is provided as an input to a :class:`~music21.figuredBass.segment.Segment`,
        and controls the application of methods designed to filter out undesired possibilities in
        a single Segment or undesired progressions between two consecutive Segments.
        
        
        The rules are categorized in an identical manner to methods in :mod:`~music21.figuredBass.possibility`:
        
        
        1) Single Possibility Rules. These rules apply to any possibility within a single Segment (possibA). 


        2) Consecutive Possibility Rules. These rules apply between any correct single possibility in segmentA 
        (possibA) and any correct single possibility in segmentB (possibB), segmentB coming directly after segmentA.

        
        3) Special Resolution Rules. These rules apply to Segments whose :attr:`~music21.figuredBass.segment.Segment.segmentChord` is an
        augmented sixth, dominant seventh, or diminished seventh chord.
        
        
        
        >>> from music21.figuredBass import rules
        >>> fbRules = rules.Rules()
        >>> fbRules.forbidParallelFifths = False
        >>> fbRules.upperPartsMaxSemitoneSeparation = None
        '''
        #Single Possibility rules
        self.forbidIncompletePossibilities = True
        self.upperPartsMaxSemitoneSeparation = 12
        self.forbidVoiceCrossing = True
        
        #Consecutive Possibility rules
        self.forbidParallelFifths = True
        self.forbidParallelOctaves = True
        self.forbidHiddenFifths = True
        self.forbidHiddenOctaves = True
        self.forbidVoiceOverlap = True
        self.partMovementLimits = []

        #Special resolution rules
        self.resolveDominantSeventhProperly = True
        self.resolveDiminishedSeventhProperly = True
        self.resolveAugmentedSixthProperly = True
        self.doubledRootInDim7 = False
        self.applySinglePossibRulesToResolution = False
        self.applyConsecutivePossibRulesToResolution = False
        
        self._upperPartsRemainSame = False
    
    def __repr__(self):
        return "<music21.figuredBass.rules Rules>" 


class FiguredBassRulesException(music21.Music21Exception):
    pass



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)  

#------------------------------------------------------------------------------
# eof
  