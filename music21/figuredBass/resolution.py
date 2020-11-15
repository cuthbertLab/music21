# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         resolution.py
# Purpose:      Defines standard resolutions for possibility instances
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
.. note:: The terminology, V43, viio, iv, etc. are explained
     more fully in *The Music Theory Handbook*
     by Marjorie Merryman.


This module contains methods which can properly resolve
`dominant seventh <http://en.wikipedia.org/wiki/Dominant_seventh_chord>`_,
`diminished seventh <http://en.wikipedia.org/wiki/Diminished_seventh_chord>`_, and
`augmented sixth <http://en.wikipedia.org/wiki/Augmented_sixth_chord>`_
chords expressed as possibilities (See :mod:`~music21.figuredBass.possibility`).
Although these methods can stand alone, they are speed-enhanced for instances
of :class:`~music21.figuredBass.segment.Segment`, where there are many
possibilities formed around the same chord. If provided with additional
arguments, the methods only :meth:`~music21.pitch.Pitch.transpose` each
:class:`~music21.pitch.Pitch` in a possibility by the appropriate interval.
'''
import unittest
from typing import List, Optional

from music21 import exceptions21
from music21 import chord
from music21 import note
from music21 import stream


def augmentedSixthToDominant(augSixthPossib, augSixthType=None, augSixthChordInfo=None):
    '''
    Resolves French (augSixthType = 1), German (augSixthType = 2), and Swiss (augSixthType = 3)
    augmented sixth chords to the root position dominant triad.


    Proper Italian augmented sixth resolutions not supported within this method.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> Bb2 = pitch.Pitch('B-2')
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> Es4 = pitch.Pitch('E#4')
    >>> F4 = pitch.Pitch('F4')
    >>> G4 = pitch.Pitch('G4')
    >>> Gs4 = pitch.Pitch('G#4')
    >>> iv6 = (G4, D4, D4, Bb2)
    >>> itAug6 = (Gs4, D4, D4, Bb2)
    >>> frAug6 = (Gs4, E4, D4, Bb2)
    >>> grAug6 = (Gs4, F4, D4, Bb2)
    >>> swAug6 = (Gs4, Es4, D4, Bb2)

    >>> frRes = resolution.augmentedSixthToDominant(frAug6)
    >>> frRes
    (<music21.pitch.Pitch A4>, <music21.pitch.Pitch E4>,
     <music21.pitch.Pitch C#4>, <music21.pitch.Pitch A2>)
    >>> [str(p) for p in frRes]
    ['A4', 'E4', 'C#4', 'A2']

    >>> grRes = resolution.augmentedSixthToDominant(grAug6)
    >>> [str(p) for p in grRes]
    ['A4', 'E4', 'C#4', 'A2']

    >>> swRes = resolution.augmentedSixthToDominant(swAug6)
    >>> [str(p) for p in swRes]
    ['A4', 'E4', 'C#4', 'A2']
    >>> #_DOCS_SHOW resolution.showResolutions(frAug6, frRes, grAug6, grRes, swAug6, swRes)

        .. image:: images/figuredBass/fbResolution_a6toV.*
            :width: 700


    Above: French, German, and Swiss resolutions, respectively.
    '''
    if augSixthChordInfo is None:
        augSixthChord = chord.Chord(augSixthPossib)
        if not augSixthChord.isAugmentedSixth():
            raise ResolutionException('Possibility is not an augmented sixth chord.')
        augSixthChordInfo = _unpackSeventhChord(chord.Chord(augSixthPossib))

        if augSixthType is None:
            if augSixthChord.isItalianAugmentedSixth():
                raise ResolutionException(
                    'Italian augmented sixth resolution not supported in this method.')

            if augSixthChord.isFrenchAugmentedSixth():
                augSixthType = 1
            elif augSixthChord.isGermanAugmentedSixth():
                augSixthType = 2
            elif augSixthChord.isSwissAugmentedSixth():
                augSixthType = 3

    if augSixthType in (1, 3):
        [bass, other, root, unused_third, fifth] = augSixthChordInfo  # other == sixth
    elif augSixthType == 2:
        [bass, root, unused_third, fifth, other] = augSixthChordInfo  # other == seventh

    howToResolve = [(lambda p: p.name == bass.name, '-m2'),
                    (lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == fifth.name, '-m2'),
                    (lambda p: p.name == other.name and augSixthType == 3, 'd1'),
                    (lambda p: p.name == other.name and augSixthType == 2, '-m2')]

    return _resolvePitches(augSixthPossib, howToResolve)


def augmentedSixthToMajorTonic(augSixthPossib, augSixthType=None, augSixthChordInfo=None):
    '''
    Resolves French (augSixthType = 1), German (augSixthType = 2), and Swiss (augSixthType = 3)
    augmented sixth chords to the major tonic 6,4.


    Proper Italian augmented sixth resolutions not supported within this method.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> Bb2 = pitch.Pitch('B-2')
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> Es4 = pitch.Pitch('E#4')
    >>> F4 = pitch.Pitch('F4')
    >>> G4 = pitch.Pitch('G4')
    >>> Gs4 = pitch.Pitch('G#4')
    >>> iv6 = (G4, D4, D4, Bb2)
    >>> itAug6 = (Gs4, D4, D4, Bb2)
    >>> frAug6 = (Gs4, E4, D4, Bb2)
    >>> grAug6 = (Gs4, F4, D4, Bb2)
    >>> swAug6 = (Gs4, Es4, D4, Bb2)
    >>> frRes = resolution.augmentedSixthToMajorTonic(frAug6)
    >>> [str(p) for p in frRes]
    ['A4', 'F#4', 'D4', 'A2']
    >>> grRes = resolution.augmentedSixthToMajorTonic(grAug6)
    >>> [str(p) for p in grRes]
    ['A4', 'F#4', 'D4', 'A2']
    >>> swRes = resolution.augmentedSixthToMajorTonic(swAug6)
    >>> [str(p) for p in swRes]
    ['A4', 'F#4', 'D4', 'A2']
    >>> #_DOCS_SHOW resolution.showResolutions(frAug6, frRes, grAug6, grRes, swAug6, swRes)

        .. image:: images/figuredBass/fbResolution_a6toI.*
            :width: 700


    Above: French, German, and Swiss resolutions, respectively.
    '''
    if augSixthChordInfo is None:
        augSixthChord = chord.Chord(augSixthPossib)
        if not augSixthChord.isAugmentedSixth():
            raise ResolutionException('Possibility is not an augmented sixth chord.')
        augSixthChordInfo = _unpackSeventhChord(chord.Chord(augSixthPossib))

        if augSixthType is None:
            if augSixthChord.isItalianAugmentedSixth():
                raise ResolutionException(
                    'Italian augmented sixth resolution not supported in this method.')

            if augSixthChord.isFrenchAugmentedSixth():
                augSixthType = 1
            elif augSixthChord.isGermanAugmentedSixth():
                augSixthType = 2
            elif augSixthChord.isSwissAugmentedSixth():
                augSixthType = 3

    if augSixthType in (1, 3):
        [bass, other, root, unused_third, fifth] = augSixthChordInfo  # other == sixth
    elif augSixthType == 2:
        [bass, root, unused_third, fifth, other] = augSixthChordInfo  # other == seventh

    howToResolve = [(lambda p: p.name == bass.name, '-m2'),
                    (lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == fifth.name, 'P1'),
                    (lambda p: p.name == other.name and augSixthType == 1, 'M2'),
                    (lambda p: p.name == other.name and augSixthType == 2, 'A1'),
                    (lambda p: p.name == other.name and augSixthType == 3, 'm2')]

    return _resolvePitches(augSixthPossib, howToResolve)


def augmentedSixthToMinorTonic(augSixthPossib, augSixthType=None, augSixthChordInfo=None):
    '''
    Resolves French (augSixthType = 1), German (augSixthType = 2), and Swiss (augSixthType = 3)
    augmented sixth chords to the minor tonic 6,4.


    Proper Italian augmented sixth resolutions not supported within this method.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> Bb2 = pitch.Pitch('B-2')
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> Es4 = pitch.Pitch('E#4')
    >>> F4 = pitch.Pitch('F4')
    >>> G4 = pitch.Pitch('G4')
    >>> Gs4 = pitch.Pitch('G#4')
    >>> iv6 = (G4, D4, D4, Bb2)
    >>> itAug6 = (Gs4, D4, D4, Bb2)
    >>> frAug6 = (Gs4, E4, D4, Bb2)
    >>> grAug6 = (Gs4, F4, D4, Bb2)
    >>> swAug6 = (Gs4, Es4, D4, Bb2)
    >>> frRes = resolution.augmentedSixthToMinorTonic(frAug6)
    >>> [str(p) for p in frRes]
    ['A4', 'F4', 'D4', 'A2']
    >>> grRes = resolution.augmentedSixthToMinorTonic(grAug6)
    >>> [str(p) for p in grRes]
    ['A4', 'F4', 'D4', 'A2']
    >>> swRes = resolution.augmentedSixthToMinorTonic(swAug6)
    >>> [str(p) for p in swRes]
    ['A4', 'F4', 'D4', 'A2']
    >>> #_DOCS_SHOW resolution.showResolutions(frAug6, frRes, grAug6, grRes, swAug6, swRes)

        .. image:: images/figuredBass/fbResolution_a6toIm.*
            :width: 700


    Above: French, German, and Swiss resolutions, respectively.
    '''
    if augSixthChordInfo is None:
        augSixthChord = chord.Chord(augSixthPossib)
        if not augSixthChord.isAugmentedSixth():
            raise ResolutionException('Possibility is not an augmented sixth chord.')
        augSixthChordInfo = _unpackSeventhChord(chord.Chord(augSixthPossib))

        if augSixthType is None:
            if augSixthChord.isItalianAugmentedSixth():
                raise ResolutionException(
                    'Italian augmented sixth resolution not supported in this method.')

            if augSixthChord.isFrenchAugmentedSixth():
                augSixthType = 1
            elif augSixthChord.isGermanAugmentedSixth():
                augSixthType = 2
            elif augSixthChord.isSwissAugmentedSixth():
                augSixthType = 3

    if augSixthType in (1, 3):
        [bass, other, root, unused_third, fifth] = augSixthChordInfo  # other == sixth
    elif augSixthType == 2:
        [bass, root, unused_third, fifth, other] = augSixthChordInfo  # other == seventh

    howToResolve = [(lambda p: p.name == bass.name, '-m2'),
                    (lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == fifth.name, 'P1'),
                    (lambda p: p.name == other.name and augSixthType == 1, 'm2'),
                    (lambda p: p.name == other.name and augSixthType == 3, 'd2')]

    return _resolvePitches(augSixthPossib, howToResolve)


def dominantSeventhToMajorTonic(domPossib, resolveV43toI6=False, domChordInfo=None):
    '''
    Resolves a dominant seventh chord in root position or any of its
    inversions to the major tonic, in root position or first inversion.


    The second inversion (4,3) dominant seventh chord can resolve to
    the tonic in either inversion. This is controlled by
    resolveV43toI6, and is set to True
    by :meth:`~music21.figuredBass.segment.Segment.resolveDominantSeventhSegment`
    only when the :attr:`~music21.figuredBass.segment.Segment.segmentChord`
    of a :class:`~music21.figuredBass.segment.Segment`
    spells out a dominant seventh chord in second inversion.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> G2 = pitch.Pitch('G2')
    >>> C3 = pitch.Pitch('C3')
    >>> E3 = pitch.Pitch('E3')
    >>> G3 = pitch.Pitch('G3')
    >>> Bb3 = pitch.Pitch('B-3')
    >>> B3 = pitch.Pitch('B3')
    >>> C4 = pitch.Pitch('C4')
    >>> F4 = pitch.Pitch('F4')
    >>> Bb4 = pitch.Pitch('B-4')
    >>> D5 = pitch.Pitch('D5')
    >>> E5 = pitch.Pitch('E5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMajorTonic(domPossibA1)
    >>> resPossibA1
    (<music21.pitch.Pitch C5>, <music21.pitch.Pitch E4>,
     <music21.pitch.Pitch C4>, <music21.pitch.Pitch C3>)
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA1, resPossibA1)

    .. image:: images/figuredBass/fbResolution_V7toI_1.*
            :width: 150

    >>> domPossibA2 = (Bb3, G3, E3, C3)
    >>> resPossibA2 = resolution.dominantSeventhToMajorTonic(domPossibA2)
    >>> [str(p) for p in resPossibA2]
    ['A3', 'F3', 'F3', 'F3']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA2, resPossibA2)

    .. image:: images/figuredBass/fbResolution_V7toI_2.*
            :width: 150

    >>> domPossibA3 = (E5, Bb4, C4, G3)
    >>> resPossibA3a = resolution.dominantSeventhToMajorTonic(domPossibA3, False)
    >>> [str(p) for p in resPossibA3a]
    ['F5', 'A4', 'C4', 'F3']
    >>> resPossibA3b = resolution.dominantSeventhToMajorTonic(domPossibA3, True)
    >>> [str(p) for p in resPossibA3b]
    ['F5', 'C5', 'C4', 'A3']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA3, resPossibA3a, domPossibA3, resPossibA3b)

    .. image:: images/figuredBass/fbResolution_V7toI_3.*
            :width: 200
    '''
    if domChordInfo is None:
        domChord = chord.Chord(domPossib)
        if not domChord.isDominantSeventh():
            raise ResolutionException('Possibility is not a dominant seventh chord.')
        domChordInfo = _unpackSeventhChord(chord.Chord(domPossib))
    [bass, root, third, fifth, seventh] = domChordInfo

    howToResolve = [(lambda p: p.name == root.name and p == bass, 'P4'),
                    (lambda p: p.name == third.name, 'm2'),
                    (lambda p: p.name == fifth.name and resolveV43toI6, 'M2'),
                    (lambda p: p.name == fifth.name, '-M2'),
                    (lambda p: p.name == seventh.name and resolveV43toI6, 'M2'),
                    (lambda p: p.name == seventh.name, '-m2')]

    return _resolvePitches(domPossib, howToResolve)


def dominantSeventhToMinorTonic(domPossib, resolveV43toi6=False, domChordInfo=None):
    '''
    Resolves a dominant seventh chord in root position or any of its
    inversions to the minor tonic, in root position or first inversion,
    accordingly.


    The second inversion (4,3) dominant seventh chord can resolve to
    the tonic in either inversion. This is controlled by
    resolveV43toi6, and is set to True by
    :meth:`~music21.figuredBass.segment.Segment.resolveDominantSeventhSegment`
    only when the :attr:`~music21.figuredBass.segment.Segment.segmentChord`
    of a :class:`~music21.figuredBass.segment.Segment`
    spells out a dominant seventh chord in second inversion.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> G2 = pitch.Pitch('G2')
    >>> C3 = pitch.Pitch('C3')
    >>> E3 = pitch.Pitch('E3')
    >>> G3 = pitch.Pitch('G3')
    >>> Bb3 = pitch.Pitch('B-3')
    >>> B3 = pitch.Pitch('B3')
    >>> C4 = pitch.Pitch('C4')
    >>> F4 = pitch.Pitch('F4')
    >>> Bb4 = pitch.Pitch('B-4')
    >>> D5 = pitch.Pitch('D5')
    >>> E5 = pitch.Pitch('E5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMinorTonic(domPossibA1)
    >>> [str(p) for p in resPossibA1]
    ['C5', 'E-4', 'C4', 'C3']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA1, resPossibA1)

    .. image:: images/figuredBass/fbResolution_V7toIm_1.*
            :width: 150

    >>> domPossibA2 = (Bb3, G3, E3, C3)
    >>> resPossibA2 = resolution.dominantSeventhToMinorTonic(domPossibA2)
    >>> ', '.join([str(p) for p in resPossibA2])
    'A-3, F3, F3, F3'
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA2, resPossibA2)

    .. image:: images/figuredBass/fbResolution_V7toIm_2.*
            :width: 150

    >>> domPossibA3 = (E5, Bb4, C4, G3)
    >>> resPossibA3a = resolution.dominantSeventhToMinorTonic(domPossibA3, False)
    >>> [str(p) for p in resPossibA3a]
    ['F5', 'A-4', 'C4', 'F3']
    >>> resPossibA3b = resolution.dominantSeventhToMinorTonic(domPossibA3, True)
    >>> [str(p) for p in resPossibA3b]
    ['F5', 'C5', 'C4', 'A-3']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA3, resPossibA3a, domPossibA3, resPossibA3b)

    .. image:: images/figuredBass/fbResolution_V7toIm_3.*
            :width: 200
    '''
    if domChordInfo is None:
        domChord = chord.Chord(domPossib)
        if not domChord.isDominantSeventh():
            raise ResolutionException('Possibility is not a dominant seventh chord.')
        domChordInfo = _unpackSeventhChord(chord.Chord(domPossib))
    [bass, root, third, fifth, seventh] = domChordInfo

    howToResolve = [(lambda p: p.name == root.name and p == bass, 'P4'),
                    (lambda p: p.name == third.name, 'm2'),
                    (lambda p: p.name == fifth.name and resolveV43toi6, 'm2'),
                    (lambda p: p.name == fifth.name, '-M2'),
                    (lambda p: p.name == seventh.name and resolveV43toi6, 'M2'),
                    (lambda p: p.name == seventh.name, '-M2')]

    return _resolvePitches(domPossib, howToResolve)


def dominantSeventhToMajorSubmediant(domPossib, domChordInfo=None):
    '''
    Resolves a dominant seventh chord in root position to the
    major submediant (VI) in root position.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> G2 = pitch.Pitch('G2')
    >>> B3 = pitch.Pitch('B3')
    >>> F4 = pitch.Pitch('F4')
    >>> D5 = pitch.Pitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMajorSubmediant(domPossibA1)
    >>> [p.nameWithOctave for p in resPossibA1]
    ['C5', 'E-4', 'C4', 'A-2']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA1, resPossibA1)

    .. image:: images/figuredBass/fbResolution_V7toVI.*
            :width: 150
    '''
    if domChordInfo is None:
        domChord = chord.Chord(domPossib)
        if not domChord.isDominantSeventh():
            raise ResolutionException('Possibility is not a dominant seventh chord.')
        domChordInfo = _unpackSeventhChord(chord.Chord(domPossib))
        if not domChord.inversion() == 0:
            raise ResolutionException('Possibility must be in root position.')
    [unused_bass, root, third, fifth, seventh] = domChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == third.name, 'm2'),
                    (lambda p: p.name == fifth.name, '-M2'),
                    (lambda p: p.name == seventh.name, '-M2')]

    return _resolvePitches(domPossib, howToResolve)


def dominantSeventhToMinorSubmediant(domPossib, domChordInfo=None):
    '''
    Resolves a dominant seventh chord in root position to the
    minor submediant (vi) in root position.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> G2 = pitch.Pitch('G2')
    >>> B3 = pitch.Pitch('B3')
    >>> F4 = pitch.Pitch('F4')
    >>> D5 = pitch.Pitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMinorSubmediant(domPossibA1)
    >>> [p.nameWithOctave for p in resPossibA1]
    ['C5', 'E4', 'C4', 'A2']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA1, resPossibA1)

    .. image:: images/figuredBass/fbResolution_V7toVIm.*
            :width: 150
    '''
    if domChordInfo is None:
        domChord = chord.Chord(domPossib)
        if not domChord.isDominantSeventh():
            raise ResolutionException('Possibility is not a dominant seventh chord.')
        domChordInfo = _unpackSeventhChord(chord.Chord(domPossib))
        if not domChord.inversion() == 0:
            raise ResolutionException('Possibility must be in root position.')
    [unused_bass, root, third, fifth, seventh] = domChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'M2'),
                    (lambda p: p.name == third.name, 'm2'),
                    (lambda p: p.name == fifth.name, '-M2'),
                    (lambda p: p.name == seventh.name, '-m2')]

    return _resolvePitches(domPossib, howToResolve)


def dominantSeventhToMajorSubdominant(domPossib, domChordInfo=None):
    '''
    Resolves a dominant seventh chord in root position
    to the major subdominant (IV) in first inversion.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> G2 = pitch.Pitch('G2')
    >>> B3 = pitch.Pitch('B3')
    >>> F4 = pitch.Pitch('F4')
    >>> D5 = pitch.Pitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMajorSubdominant(domPossibA1)
    >>> [p.nameWithOctave for p in resPossibA1]
    ['C5', 'F4', 'C4', 'A2']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA1, resPossibA1)

    .. image:: images/figuredBass/fbResolution_V7toIV.*
            :width: 150
    '''
    if domChordInfo is None:
        domChord = chord.Chord(domPossib)
        if not domChord.isDominantSeventh():
            raise ResolutionException('Possibility is not a dominant seventh chord.')
        domChordInfo = _unpackSeventhChord(chord.Chord(domPossib))
        if not domChord.inversion() == 0:
            raise ResolutionException('Possibility must be in root position.')
    [unused_bass, root, third, fifth, unused_seventh] = domChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'M2'),
                    (lambda p: p.name == third.name, 'm2'),
                    (lambda p: p.name == fifth.name, '-M2')]

    return _resolvePitches(domPossib, howToResolve)


def dominantSeventhToMinorSubdominant(domPossib, domChordInfo=None):
    '''
    Resolves a dominant seventh chord in root position
    to the minor subdominant (iv) in first inversion.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> G2 = pitch.Pitch('G2')
    >>> B3 = pitch.Pitch('B3')
    >>> F4 = pitch.Pitch('F4')
    >>> D5 = pitch.Pitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMinorSubdominant(domPossibA1)
    >>> [p.nameWithOctave for p in resPossibA1]
    ['C5', 'F4', 'C4', 'A-2']
    >>> #_DOCS_SHOW resolution.showResolutions(domPossibA1, resPossibA1)

    .. image:: images/figuredBass/fbResolution_V7toIVm.*
            :width: 150
    '''
    if domChordInfo is None:
        domChord = chord.Chord(domPossib)
        if not domChord.isDominantSeventh():
            raise ResolutionException('Possibility is not a dominant seventh chord.')
        domChordInfo = _unpackSeventhChord(chord.Chord(domPossib))
        if not domChord.inversion() == 0:
            raise ResolutionException('Possibility must be in root position.')
    [unused_bass, root, third, fifth, unused_seventh] = domChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == third.name, 'm2'),
                    (lambda p: p.name == fifth.name, '-M2')]

    return _resolvePitches(domPossib, howToResolve)


def diminishedSeventhToMajorTonic(dimPossib, doubledRoot=False, dimChordInfo=None):
    '''
    Resolves a fully diminished seventh chord to the major tonic,
    in root position or either inversion.


    The resolution of the diminished seventh chord can have a
    doubled third (standard resolution) or a doubled root
    (alternate resolution), because the third of the diminished
    chord can either rise or fall. The desired resolution is
    attained using doubledRoot, and is set by
    :meth:`~music21.figuredBass.segment.Segment.resolveDiminishedSeventhSegment`.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = pitch.Pitch('C#3')
    >>> G3 = pitch.Pitch('G3')
    >>> E4 = pitch.Pitch('E4')
    >>> Bb4 = pitch.Pitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibAa = resolution.diminishedSeventhToMajorTonic(dimPossibA, False)
    >>> [str(p) for p in resPossibAa]
    ['A4', 'F#4', 'F#3', 'D3']
    >>> resPossibAb = resolution.diminishedSeventhToMajorTonic(dimPossibA, True)
    >>> [p.nameWithOctave for p in resPossibAb]
    ['A4', 'D4', 'F#3', 'D3']
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibAa, dimPossibA, resPossibAb)

    .. image:: images/figuredBass/fbResolution_vii7toI.*
            :width: 200
    '''
    if dimChordInfo is None:
        dimChord = chord.Chord(dimPossib)
        if not dimChord.isDiminishedSeventh():
            raise ResolutionException('Possibility is not a fully diminished seventh chord.')
        dimChordInfo = _unpackSeventhChord(chord.Chord(dimPossib))
    [unused_bass, root, third, fifth, seventh] = dimChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == third.name and doubledRoot, '-M2'),
                    (lambda p: p.name == third.name, 'M2'),
                    (lambda p: p.name == fifth.name, '-m2'),
                    (lambda p: p.name == seventh.name, '-m2')]

    return _resolvePitches(dimPossib, howToResolve)


def diminishedSeventhToMinorTonic(dimPossib, doubledRoot=False, dimChordInfo=None):
    '''
    Resolves a fully diminished seventh chord to the minor tonic,
    in root position or either inversion.


    The resolution of the diminished seventh chord can have a
    doubled third (standard resolution) or a doubled root
    (alternate resolution), because the third of the diminished
    chord can either rise or fall. The desired resolution is
    attained using doubledRoot, and is set by
    :meth:`~music21.figuredBass.segment.Segment.resolveDiminishedSeventhSegment`.

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = pitch.Pitch('C#3')
    >>> G3 = pitch.Pitch('G3')
    >>> E4 = pitch.Pitch('E4')
    >>> Bb4 = pitch.Pitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibAa = resolution.diminishedSeventhToMinorTonic(dimPossibA, False)
    >>> [p.nameWithOctave for p in resPossibAa]
    ['A4', 'F4', 'F3', 'D3']
    >>> resPossibAb = resolution.diminishedSeventhToMinorTonic(dimPossibA, True)
    >>> [p.nameWithOctave for p in resPossibAb]
    ['A4', 'D4', 'F3', 'D3']
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibAa, dimPossibA, resPossibAb)

    .. image:: images/figuredBass/fbResolution_vii7toIm.*
            :width: 200
    '''
    if dimChordInfo is None:
        dimChord = chord.Chord(dimPossib)
        if not dimChord.isDiminishedSeventh():
            raise ResolutionException('Possibility is not a fully diminished seventh chord.')
        dimChordInfo = _unpackSeventhChord(chord.Chord(dimPossib))
    [unused_bass, root, third, fifth, seventh] = dimChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == third.name and doubledRoot, '-M2'),
                    (lambda p: p.name == third.name, 'm2'),
                    (lambda p: p.name == fifth.name, '-M2'),
                    (lambda p: p.name == seventh.name, '-m2')]

    return _resolvePitches(dimPossib, howToResolve)


def diminishedSeventhToMajorSubdominant(dimPossib, dimChordInfo=None):
    '''
    Resolves a fully diminished seventh chord to the
    major subdominant (IV).

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = pitch.Pitch('C#3')
    >>> G3 = pitch.Pitch('G3')
    >>> E4 = pitch.Pitch('E4')
    >>> Bb4 = pitch.Pitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibA = resolution.diminishedSeventhToMajorSubdominant(dimPossibA)
    >>> [str(p) for p in resPossibA]
    ['B4', 'D4', 'G3', 'D3']
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibA)

    .. image:: images/figuredBass/fbResolution_vii7toIV.*
            :width: 150
    '''
    if dimChordInfo is None:
        dimChord = chord.Chord(dimPossib)
        if not dimChord.isDiminishedSeventh():
            raise ResolutionException('Possibility is not a fully diminished seventh chord.')
        dimChordInfo = _unpackSeventhChord(chord.Chord(dimPossib))
    [unused_bass, root, third, unused_fifth, seventh] = dimChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == third.name, '-M2'),
                    (lambda p: p.name == seventh.name, 'A1')]

    return _resolvePitches(dimPossib, howToResolve)


def diminishedSeventhToMinorSubdominant(dimPossib, dimChordInfo=None):
    '''
    Resolves a fully diminished seventh chord to the
    minor subdominant (iv).

    >>> from music21 import pitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = pitch.Pitch('C#3')
    >>> G3 = pitch.Pitch('G3')
    >>> E4 = pitch.Pitch('E4')
    >>> Bb4 = pitch.Pitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibA = resolution.diminishedSeventhToMinorSubdominant(dimPossibA)
    >>> [str(p) for p in resPossibA]
    ['B-4', 'D4', 'G3', 'D3']
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibA)

    .. image:: images/figuredBass/fbResolution_vii7toIVm.*
            :width: 150
    '''
    if dimChordInfo is None:
        dimChord = chord.Chord(dimPossib)
        if not dimChord.isDiminishedSeventh():
            raise ResolutionException('Possibility is not a fully diminished seventh chord.')
        dimChordInfo = _unpackSeventhChord(chord.Chord(dimPossib))
    [unused_bass, root, third, unused_fifth, unused_seventh] = dimChordInfo

    howToResolve = [(lambda p: p.name == root.name, 'm2'),
                    (lambda p: p.name == third.name, '-M2')]

    return _resolvePitches(dimPossib, howToResolve)


def showResolutions(*allPossib):
    '''
    Takes in possibilities as arguments and adds them in order
    to a :class:`~music21.stream.Score` which is then displayed
    in external software.
    '''
    upperParts = stream.Part()
    bassLine = stream.Part()
    for possibA in allPossib:
        chordA = chord.Chord(possibA[0:-1])
        chordA.quarterLength = 2.0
        bassA = note.Note(possibA[-1])
        bassA.quarterLength = 2.0
        upperParts.append(chordA)
        bassLine.append(bassA)
    score = stream.Score()
    score.insert(0, upperParts)
    score.insert(0, bassLine)
    score.show()

# ---------------------------------------------
# INTERNAL METHODS


def _transpose(samplePitch, intervalString):
    return samplePitch.transpose(intervalString)


def _resolvePitches(possibToResolve, howToResolve):
    '''
    Takes in a possibility to resolve and a list of (lambda function, intervalString)
    pairs and transposes each pitch by the intervalString corresponding to the lambda
    function that returns True when applied to the pitch.
    '''
    howToResolve.append((lambda p: True, 'P1'))
    resPitches = []
    for samplePitch in possibToResolve:
        for (expression, intervalString) in howToResolve:
            if expression(samplePitch):
                resPitches.append(_transpose(samplePitch, intervalString))
                break

    return tuple(resPitches)


def _unpackSeventhChord(
    seventhChord: 'music21.chord.Chord'
) -> List[Optional['music21.pitch.Pitch']]:
    '''
    Takes in a Chord and returns a list of Pitches (or Nones) corresponding
    to the bass, root, fifth, seventh.
    '''
    bass = seventhChord.bass()
    root = seventhChord.root()
    third = seventhChord.getChordStep(3)
    fifth = seventhChord.getChordStep(5)
    seventh = seventhChord.getChordStep(7)
    seventhChordInfo = [bass, root, third, fifth, seventh]
    return seventhChordInfo


_DOC_ORDER = [augmentedSixthToDominant,
              augmentedSixthToMajorTonic, augmentedSixthToMinorTonic,
              dominantSeventhToMajorTonic, dominantSeventhToMinorTonic,
              dominantSeventhToMajorSubmediant, dominantSeventhToMinorSubmediant,
              dominantSeventhToMajorSubdominant, dominantSeventhToMinorSubdominant,
              diminishedSeventhToMajorTonic, diminishedSeventhToMinorTonic,
              diminishedSeventhToMajorSubdominant, diminishedSeventhToMinorSubdominant]

# ------------------------------------------------------------------------------


class ResolutionException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

