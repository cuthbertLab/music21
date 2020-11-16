# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         basic.py
# Purpose:      music21 class which allows transcription of music21Object instances to braille.
# Authors:      Jose Cabal-Ugaz
#               Bo-cheng (Sponge) Jhan (Clef routines)
#
# Copyright:    Copyright © 2011, 2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest
from typing import List

# from music21 import articulations
from music21 import clef
from music21 import environment
from music21 import exceptions21
from music21 import interval
from music21 import note
from music21 import tempo  # for typing

from music21.braille import lookup
from music21.common import stringTools

# Add aliases to lookup tables ONLY if it will be used in many different contexts
# if it is used in only one function, make the alias there.
alphabet = lookup.alphabet
ascii_chars = lookup.ascii_chars
symbols = lookup.symbols

environRules = environment.Environment('basic.py')

beamStatus = {}
# ------------------------------------------------------------------------------
# music21Object to braille unicode methods

# noinspection PyStatementEffect
'''
Any :class:`~music21.base.Music21Object` which cannot be transcribed in
:mod:`~music21.braille.basic` returns a braille literary question mark
and outputs a warning to the console, rather than raising an exception.
This is so that a transcription of a :class:`~music21.stream.Stream` in
:class:`~music21.braille.translate` is completed as thoroughly as possible.
'''

def barlineToBraille(music21Barline):
    r'''
    Takes in a :class:`~music21.bar.Barline` and returns its representation
    as a braille string in UTF-8 unicode.

    .. note:: Only dashed, double barlines, and final barlines can be transcribed.

    >>> from music21.braille import basic
    >>> doubleBarline = bar.Barline('double')
    >>> print(basic.barlineToBraille(doubleBarline))
    ⠣⠅⠄
    >>> finalBarline = bar.Barline('final')
    >>> print(basic.barlineToBraille(finalBarline))
    ⠣⠅

    Heavy gives an "unusual barline" symbol

    >>> heavyBarline = bar.Barline('heavy')
    >>> print(basic.barlineToBraille(heavyBarline))
    ⠇
    '''
    try:
        brailleBarline = lookup.barlines[music21Barline.type]
        music21Barline.editorial.brailleEnglish = [
            f'Barline {music21Barline.type} {brailleBarline}']
        return brailleBarline
    except KeyError:  # pragma: no cover
        environRules.warn(f'Barline {music21Barline} cannot be transcribed to braille.')
        music21Barline.editorial.brailleEnglish = [f'Barline {music21Barline.type} None']
        return symbols['basic_exception']


def chordToBraille(music21Chord, descending=True, showOctave=True):
    '''
    Takes in a :class:`~music21.chord.Chord` and returns its representation
    as a braille string in UTF-8 unicode.


    In braille, only one pitch of a chord is brailled, with the rest represented
    as numeric intervals from that one pitch. If descending is True, the highest
    (sounding) pitch is brailled, and intervals are labeled in descending order;
    if descending is False, the lowest (sounding) pitch is brailled, and the
    intervals are labeled in ascending order. Convention dictates that chords
    found in the treble clef are brailled descending, and those found in the bass
    clef are brailled ascending.


    If showOctave is True, the octave of the brailled pitch is shown. Other
    octave marks are shown in context relative to the brailled pitch.

    >>> from music21.braille import basic
    >>> gMajorTriadA = chord.Chord(['G4', 'B4', 'D5', 'G5'], quarterLength=4.0)
    >>> print(basic.chordToBraille(gMajorTriadA, descending=True))
    ⠨⠷⠼⠴⠤
    >>> gMajorTriadB = chord.Chord(['G2', 'B2', 'D3', 'G3'], quarterLength=4.0)
    >>> print(basic.chordToBraille(gMajorTriadB, descending=False))
    ⠘⠷⠬⠔⠤
    >>> gMajorTriadRightHand = chord.Chord(['D4', 'B4', 'G5'], quarterLength=4.0)
    >>> print(basic.chordToBraille(gMajorTriadRightHand, descending=True))
    ⠨⠷⠴⠼
    >>> gMajorTriadLeftHand = chord.Chord(['G2', 'D3', 'B3'], quarterLength=4.0)
    >>> print(basic.chordToBraille(gMajorTriadLeftHand, descending=False))
    ⠘⠷⠔⠬
    >>> cMajorTriadRightHand = chord.Chord(['C4', 'E5'], quarterLength=4.0)
    >>> print(basic.chordToBraille(cMajorTriadRightHand, descending=True))
    ⠨⠯⠐⠬
    >>> cMajorTriadLeftHand = chord.Chord(['C2', 'E3'], quarterLength=4.0)
    >>> print(basic.chordToBraille(cMajorTriadLeftHand, descending=False))
    ⠘⠽⠸⠬
    >>> cMajorSeventhRightHand = chord.Chord(['C6', 'E5', 'B4'], quarterLength=4.0)
    >>> print(basic.chordToBraille(cMajorSeventhRightHand, descending=True))
    ⠰⠽⠴⠌
    >>> cMajorSeventhLeftHand = chord.Chord(['G2', 'E3', 'E4'], quarterLength=4.0)
    >>> print(basic.chordToBraille(cMajorSeventhLeftHand, descending=False))
    ⠘⠷⠴⠐⠴


    >>> chordWithoutAccidentals = chord.Chord(['C4', 'E4', 'F4'], quarterLength=4.0)
    >>> print(basic.chordToBraille(chordWithoutAccidentals, descending=True))
    ⠐⠿⠌⠼

    >>> chordWithAccidentals = chord.Chord(['C4', 'E-4', 'F#4'], quarterLength=4.0)
    >>> chordWithAccidentals.pitches[0].accidental = 'natural'
    >>> print(basic.chordToBraille(chordWithAccidentals, descending=True))
    ⠩⠐⠿⠣⠌⠡⠼
    '''
    music21Chord.editorial.brailleEnglish = []
    allPitches = sorted(music21Chord.pitches)
    direction = 'Descending'
    if descending:
        allPitches.reverse()
    else:
        direction = 'Ascending'

    chordTrans = []
    basePitch = allPitches[0]
    initNote = note.Note(
        basePitch,
        quarterLength=music21Chord.quarterLength
    )
    brailleNote = noteToBraille(
        music21Note=initNote,
        showOctave=showOctave
    )
    if brailleNote == symbols['basic_exception']:  # pragma: no cover
        environRules.warn(f'Chord {music21Chord} cannot be transcribed to braille.')
        music21Chord.editorial.brailleEnglish.append(f'{music21Chord} None')
        return symbols['basic_exception']
    chordTrans.append(brailleNote)
    music21Chord.editorial.brailleEnglish.append(
        '{0} Chord:\n{1}'.format(direction, '\n'.join(initNote.editorial.brailleEnglish))
    )

    for currentPitchIndex in range(1, len(allPitches)):
        currentPitch = allPitches[currentPitchIndex]
        try:
            handlePitchWithAccidental(
                currentPitch,
                chordTrans,
                music21Chord.editorial.brailleEnglish
            )
        except KeyError:
            environRules.warn(
                f'Accidental {currentPitch.accidental} of '
                + f'chord {music21Chord} cannot be transcribed to braille.'
            )
        intervalDistance = interval.notesToInterval(basePitch, currentPitch).generic.undirected
        if intervalDistance > 8:
            intervalDistance = (intervalDistance - 1) % 7 + 1
            if currentPitchIndex == 1:
                brailleOctave = pitchToOctave(currentPitch)
                chordTrans.append(brailleOctave)
                music21Chord.editorial.brailleEnglish.append(
                    f'Octave {currentPitch.octave} {brailleOctave}')
            else:
                previousPitch = allPitches[currentPitchIndex - 1]
                relativeIntervalDist = interval.notesToInterval(previousPitch,
                                                                currentPitch).generic.undirected
                if relativeIntervalDist >= 8:
                    brailleOctave = pitchToOctave(currentPitch)
                    chordTrans.append(brailleOctave)
                    music21Chord.editorial.brailleEnglish.append(
                        f'Octave {currentPitch.octave} {brailleOctave}'
                    )
        elif intervalDistance == 1:
            brailleOctave = pitchToOctave(currentPitch)
            chordTrans.append(brailleOctave)
            music21Chord.editorial.brailleEnglish.append(
                f'Octave {currentPitch.octave} {brailleOctave}')
        if intervalDistance == 1:
            intervalDistance = 8
        chordTrans.append(lookup.intervals[intervalDistance])
        music21Chord.editorial.brailleEnglish.append(
            f'Interval {intervalDistance} {lookup.intervals[intervalDistance]}'
        )
    return ''.join(chordTrans)


def pitchToOctave(music21PitchOrInt):
    '''
    takes a pitch object and returns the brailling for the octave.

    Can also be given an int specifying the octave.

    Expands the definition given in Degarmo Ch 7 to allow even less commonly used octaves such
    as -1, and > 8 by tripling, etc. the number of octave marks.

    >>> print(braille.basic.pitchToOctave(pitch.Pitch('C4')))
    ⠐
    >>> print(braille.basic.pitchToOctave(pitch.Pitch('B-4')))
    ⠐
    >>> print(braille.basic.pitchToOctave(4))
    ⠐
    >>> print(braille.basic.pitchToOctave(3))
    ⠸
    >>> print(braille.basic.pitchToOctave(2))
    ⠘
    >>> print(braille.basic.pitchToOctave(1))
    ⠈
    >>> print(braille.basic.pitchToOctave(0))
    ⠈⠈
    >>> print(braille.basic.pitchToOctave(-1))
    ⠈⠈⠈
    >>> print(braille.basic.pitchToOctave(5))
    ⠨
    >>> print(braille.basic.pitchToOctave(6))
    ⠰
    >>> print(braille.basic.pitchToOctave(7))
    ⠠
    >>> print(braille.basic.pitchToOctave(8))
    ⠠⠠
    >>> print(braille.basic.pitchToOctave(9))
    ⠠⠠⠠
    '''
    if hasattr(music21PitchOrInt, 'octave'):
        octave = music21PitchOrInt.octave
    else:
        octave = music21PitchOrInt

    if octave in lookup.octaves:
        return lookup.octaves[octave]
    elif octave < 1:
        return lookup.octaves[1] * (2 - octave)
    elif octave > 7:
        return lookup.octaves[7] * (octave - 6)


def clefToBraille(music21Clef, keyboardHandSwitched=False):
    '''
    Takes in a :class:`~music21.clef.Clef` and returns its representation
    as a braille string in UTF-8 unicode.

    Only :class:`~music21.clef.GClef`, :class:`~music21.clef.CClef`,
    :class:`~music21.clef.FClef`, :class:`~music21.clef.NoClef` and
    their subclasses (such as :class:`~music21.clef.TrebleClef`,
    :class:`~music21.clef.BassClef`) can be transcribed.

    If keyboardHandSwitched is True, the suffix of the brailled clef changes from dots
    1-2-3 to dots 1-3. In scores of keyboard instruments, this change indicates
    that the playing hand differs from which implied by the clef. (E.g. A G clef
    in the left hand part of a piano score needs the change of suffix.) Note
    that changeSuffix works only for G and F clefs.

    >>> from music21.braille import basic
    >>> trebleClef = clef.TrebleClef()
    >>> print(basic.clefToBraille(trebleClef))
    ⠜⠌⠇
    >>> print(basic.clefToBraille(trebleClef, keyboardHandSwitched=True))
    ⠜⠌⠅
    >>> bassClef = clef.BassClef()
    >>> print(basic.clefToBraille(bassClef))
    ⠜⠼⠇
    >>> print(basic.clefToBraille(bassClef, keyboardHandSwitched=True))
    ⠜⠼⠅

    >>> altoClef = clef.AltoClef()
    >>> print(basic.clefToBraille(altoClef))
    ⠜⠬⠇
    >>> tenorClef = clef.TenorClef()
    >>> print(basic.clefToBraille(tenorClef))
    ⠜⠬⠐⠇
    >>> noClef = clef.NoClef()
    >>> basic.clefToBraille(noClef) == ''
    True
    >>> sopranoClef = clef.SopranoClef()
    >>> print('%s, %d, %s' % (sopranoClef.sign, sopranoClef.line, basic.clefToBraille(sopranoClef)))
    C, 1, ⠜⠬⠈⠇
    '''
    clefNames = {
        'FrenchViolinClef': 'French Violin',
        'TrebleClef': 'Treble',
        'GSopranoClef': 'G-soprano',
        'SopranoClef': 'Soprano',
        'MezzoSopranoClef': 'Mezzo-soprano',
        'AltoClef': 'Alto',
        'TenorClef': 'Tenor',
        'CBaritoneClef': 'C-baritone',
        'FBaritoneClef': 'F-baritone',
        'BassClef': 'Bass',
        'SubBassClef': 'Sub-bass'
    }
    if isinstance(music21Clef, clef.NoClef):
        music21Clef.editorial.brailleEnglish = [f'No Clef {str(music21Clef)}']
        return ''
    clefs = lookup.clefs
    brailleClef = clefs['prefix']
    try:
        brailleClef += clefs[music21Clef.sign][music21Clef.line]
        try:
            music21Clef.editorial.brailleEnglish = (
                [clefNames[music21Clef.__class__.__name__] + f' Clef {brailleClef}']
            )
        except KeyError:  # pragma: no cover
            music21Clef.editorial.brailleEnglish = [f'Unnamed Clef {music21Clef}']
        if isinstance(music21Clef, (clef.TrebleClef, clef.BassClef)):
            brailleClef += clefs['suffix'][keyboardHandSwitched]
            if keyboardHandSwitched:
                music21Clef.editorial.brailleEnglish.append(' Keyboard hand switched')
        else:
            brailleClef += clefs['suffix'][False]
        return brailleClef
    except KeyError:  # pragma: no cover
        environRules.warn(f'Clef {music21Clef} cannot be transcribed to braille.')
        music21Clef.editorial.brailleEnglish = [f'{music21Clef} None']
        return symbols['basic_exception']


def dynamicToBraille(music21Dynamic, precedeByWordSign=True):
    '''
    Takes in a :class:`~music21.dynamics.Dynamic` and returns its
    :attr:`~music21.dynamics.Dynamic.value` as a braille string in
    UTF-8 unicode.


    If precedeByWordSign is True, the value is preceded by a word
    sign (⠜).


    >>> from music21.braille import basic
    >>> print(basic.dynamicToBraille(dynamics.Dynamic('f')))
    ⠜⠋
    >>> print(basic.dynamicToBraille(dynamics.Dynamic('pp')))
    ⠜⠏⠏
    '''
    dynamicTrans = []
    music21Dynamic.editorial.brailleEnglish = []
    if precedeByWordSign:
        dynamicTrans.append(symbols['word'])
        music21Dynamic.editorial.brailleEnglish.append(f'Word: {symbols["word"]}')

    try:
        brailleDynamic = wordToBraille(music21Dynamic.value, isTextExpression=True)
    except BrailleBasicException as wordException:  # pragma: no cover
        environRules.warn(f'Dynamic {music21Dynamic}: {wordException}')
        music21Dynamic.editorial.brailleEnglish.append(f'Dynamic {music21Dynamic.value} None')
        return symbols['basic_exception']

    music21Dynamic.editorial.brailleEnglish.append(
        f'Dynamic {music21Dynamic.value} {brailleDynamic}')
    dynamicTrans.append(brailleDynamic)
    return ''.join(dynamicTrans)


def instrumentToBraille(music21Instrument):
    '''
    Takes in a :class:`~music21.instrument.Instrument` and returns its "best name"
    as a braille string in UTF-8 unicode.

    >>> from music21.braille import basic
    >>> print(basic.instrumentToBraille(instrument.Bassoon()))
    ⠠⠃⠁⠎⠎⠕⠕⠝
    >>> print(basic.instrumentToBraille(instrument.BassClarinet()))
    ⠠⠃⠁⠎⠎⠀⠉⠇⠁⠗⠊⠝⠑⠞
    '''
    music21Instrument.editorial.brailleEnglish = []
    allWords = music21Instrument.bestName().split()
    try:
        trans = [wordToBraille(word) for word in allWords]
    except BrailleBasicException as wordException:  # pragma: no cover
        environRules.warn(f'Instrument {music21Instrument}: {wordException}')
        music21Instrument.editorial.brailleEnglish.append(
            f'Instrument {music21Instrument.bestName()} None')
        return symbols['basic_exception']

    brailleInst = symbols['space'].join(trans)
    music21Instrument.editorial.brailleEnglish.append(
        f'Instrument {music21Instrument.bestName()} {brailleInst}')
    return brailleInst


def keySigToBraille(music21KeySignature, outgoingKeySig=None):
    '''
    Takes in a :class:`~music21.key.KeySignature` and returns its representation
    in braille as a string in UTF-8 unicode.

    >>> from music21.braille import basic
    >>> print(basic.keySigToBraille(key.KeySignature(4)))
    ⠼⠙⠩


    If given an old key signature, then its cancellation will be applied before
    and in relation to the new key signature.


    >>> print(basic.keySigToBraille(key.KeySignature(0), outgoingKeySig = key.KeySignature(-3)))
    ⠡⠡⠡
    '''
    naturals = lookup.naturals
    music21KeySignature.editorial.brailleEnglish = []
    incomingSharps = music21KeySignature.sharps
    try:
        ks_braille = lookup.keySignatures[incomingSharps]
    except KeyError:
        environRules.warn(
            f'Incoming Key Signature {music21KeySignature} cannot be transcribed to braille.'
        )
        music21KeySignature.editorial.brailleEnglish.append(
            f'Key Signature {music21KeySignature} sharps None'
        )
        return symbols['basic_exception']

    if incomingSharps > 0:
        music21KeySignature.editorial.brailleEnglish.append(
            f'Key Signature {incomingSharps} sharp(s) {ks_braille}'
        )
    else:
        music21KeySignature.editorial.brailleEnglish.append(
            f'Key Signature {abs(incomingSharps)} flat(s) {ks_braille}'
        )
    if outgoingKeySig is None:
        return ks_braille

    outgoingSharps = outgoingKeySig.sharps
    absOutgoing = abs(outgoingSharps)
    absIncoming = abs(incomingSharps)

    trans = []

    try:
        if (incomingSharps == 0
                or outgoingSharps == 0
                or (outgoingSharps / absOutgoing) != (incomingSharps / absIncoming)):
            trans.append(naturals[absOutgoing])
            music21KeySignature.editorial.brailleEnglish.insert(
                0,
                f'Key Signature {outgoingSharps} naturals {naturals[absOutgoing]}')
        elif absOutgoing >= absIncoming:
            trans.append(naturals[abs(outgoingSharps - incomingSharps)])
            music21KeySignature.editorial.brailleEnglish.insert(
                0,
                'Key Signature {0} naturals {1}'.format(
                    outgoingSharps,
                    naturals[abs(outgoingSharps - incomingSharps)]
                )
            )
        trans.append(ks_braille)
        return ''.join(trans)

    except KeyError:  # pragma: no cover
        environRules.warn(
            f'Outgoing Key Signature {outgoingKeySig} cannot be transcribed to braille.')
        music21KeySignature.editorial.brailleEnglish.append(f'{outgoingKeySig} naturals=None')
        return ks_braille


def metronomeMarkToBraille(music21MetronomeMark):
    '''
    Takes in a :class:`~music21.tempo.MetronomeMark` and returns it as a
    braille string in UTF-8 unicode.
    The format is (note C with duration of metronome's referent)(metronome symbol)(number/bpm).

    >>> from music21.braille import basic
    >>> mm1 = tempo.MetronomeMark(number=80, referent=note.Note(type='half'))
    >>> print(basic.metronomeMarkToBraille(mm1))
    ⠝⠶⠼⠓⠚
    >>> mm2 = tempo.MetronomeMark(number=135, referent=note.Note(quarterLength=0.5))
    >>> print(basic.metronomeMarkToBraille(mm2))
    ⠙⠶⠼⠁⠉⠑
    '''
    music21MetronomeMark.editorial.brailleEnglish = []
    try:
        metroTrans = []
        metroNote = note.Note('C4', quarterLength=music21MetronomeMark.referent.quarterLength)
        brailleNote = noteToBraille(metroNote, showOctave=False)
        metroTrans.append(brailleNote)
        music21MetronomeMark.editorial.brailleEnglish.append(
            'Metronome Note {0}'.format(' '.join(metroNote.editorial.brailleEnglish))
        )
        metroTrans.append(symbols['metronome'])
        music21MetronomeMark.editorial.brailleEnglish.append(
            f'Metronome symbol {symbols["metronome"]}'
        )
        brailleNumber = numberToBraille(music21MetronomeMark.number)
        metroTrans.append(brailleNumber)
        music21MetronomeMark.editorial.brailleEnglish.append(
            f'Metronome number {music21MetronomeMark.number} {brailleNumber}'
        )
        return ''.join(metroTrans)
    except BrailleBasicException as numberException:  # pragma: no cover
        environRules.warn(f'Metronome Mark {music21MetronomeMark}: {numberException}')
        music21MetronomeMark.editorial.brailleEnglish.append(f'{music21MetronomeMark} None')
        return symbols['basic_exception']


def yieldBrailleArticulations(noteEl):
    '''
    Generator that yields braille before note articulations from a given note.
    Might yield nothing.

    "When a staccato or staccatissimo is shown with any of the other
    [before note expressions], it is brailled first."

    Beyond that, we yield in alphabetical order

    For reference:

    >>> brailleArt = braille.lookup.beforeNoteExpr
    >>> print(brailleArt['tenuto'])
    ⠸⠦
    >>> print(brailleArt['staccato'])
    ⠦
    >>> print(brailleArt['accent'])
    ⠨⠦

    >>> n = note.Note()
    >>> n.articulations.append(articulations.Tenuto())
    >>> n.articulations.append(articulations.Staccato())
    >>> n.articulations.append(articulations.Accent())

    This will yield in order: Staccato, Accent, Tenuto.

    >>> for brailleArt in braille.basic.yieldBrailleArticulations(n):
    ...     print(brailleArt)
    ⠦
    ⠨⠦
    ⠸⠦

    '''
    def _brailleArticulationsSortKey(inner_articulation):
        isStaccato = (inner_articulation.name not in ('staccato', 'staccatissimo'))
        return (isStaccato, inner_articulation.name)

    if hasattr(noteEl, 'articulations'):  # should be True, but safe side.
        for art in sorted(noteEl.articulations, key=_brailleArticulationsSortKey):
            if art.name in lookup.beforeNoteExpr:
                brailleArt = lookup.beforeNoteExpr[art.name]
                if 'brailleEnglish' in noteEl.editorial:
                    noteEl.editorial.brailleEnglish.append(f'Articulation {art.name} {brailleArt}')
                yield brailleArt


def noteToBraille(
    music21Note: note.Note,
    *,
    showOctave=True,
    upperFirstInFingering=True
):
    '''
    Given a :class:`~music21.note.Note`, returns the appropriate braille
    characters as a string in UTF-8 unicode.


    The format for note display in braille is the accidental (if necessary)
    + octave (if necessary) + pitch name with length.


    If the note has an :class:`~music21.pitch.Accidental`, the accidental is always
    displayed unless its :attr:`~music21.pitch.Accidental.displayStatus` is set to
    False. The octave of the note is only displayed if showOctave is set to True.


    >>> from music21.braille import basic
    >>> C4 = note.Note('C4')
    >>> print(basic.noteToBraille(C4))
    ⠐⠹
    >>> C4.quarterLength = 2.0
    >>> print(basic.noteToBraille(C4))
    ⠐⠝
    >>> Ds4 = note.Note('D#4')
    >>> print(basic.noteToBraille(Ds4))
    ⠩⠐⠱
    >>> print(basic.noteToBraille(Ds4, showOctave=False))
    ⠩⠱
    >>> Ds4.pitch.accidental.displayStatus=False
    >>> print(basic.noteToBraille(Ds4))
    ⠐⠱
    >>> A2 = note.Note('A2')
    >>> A2.quarterLength = 3.0
    >>> print(basic.noteToBraille(A2))
    ⠘⠎⠄


    >>> B = note.Note('B4')
    >>> f = expressions.Fermata()
    >>> B.expressions.append(f)
    >>> print(basic.noteToBraille(B))
    ⠐⠺⠣⠇
    >>> for x in B.editorial.brailleEnglish:
    ...     print(x)
    Octave 4 ⠐
    B quarter ⠺
    Note-fermata: Shape normal: ⠣⠇

    >>> f.shape = 'square'
    >>> print(basic.noteToBraille(B))
    ⠐⠺⠰⠣⠇
    >>> for x in B.editorial.brailleEnglish:
    ...     print(x)
    Octave 4 ⠐
    B quarter ⠺
    Note-fermata: Shape square: ⠰⠣⠇


    >>> C4 = note.Note('C4')
    >>> print(basic.noteToBraille(C4))
    ⠐⠹
    >>> C4.duration.appendTuplet(duration.Tuplet(3, 2))  # triplet
    >>> print(basic.noteToBraille(C4))
    ⠐⠹
    >>> C4.beamStart = True
    >>> print(basic.noteToBraille(C4))
    ⠆⠐⠹
    >>> for x in C4.editorial.brailleEnglish:
    ...     print(x)
    Triplet ⠆
    Octave 4 ⠐
    C quarter ⠹

    >>> C4 = note.Note('C4')
    >>> C4.duration.appendTuplet(duration.Tuplet(7, 4))  # septuplet
    >>> C4.beamStart = True
    >>> print(basic.noteToBraille(C4))
    ⠸⠶⠄⠐⠹
    >>> for x in C4.editorial.brailleEnglish:
    ...     print(x)
    Septuplet ⠸⠶⠄
    Octave 4 ⠐
    C quarter ⠹
    '''
    # Note: beamStatus is a helper that I hope to remove
    # when moving all the translation features to a separate class.
    music21Note.editorial.brailleEnglish = []
    falseKeywords = ['beginLongBracketSlur',
                     'endLongBracketSlur',
                     'beginLongDoubleSlur',
                     'endLongDoubleSlur',
                     'shortSlur',
                     'beamStart',
                     'beamContinue']

    for keyword in falseKeywords:
        try:
            beamStatus[keyword] = getattr(music21Note, keyword)
        except AttributeError:
            beamStatus[keyword] = False

    noteTrans = []
    # opening double slur (before second note, after first note)
    # opening bracket slur
    # closing bracket slur (if also beginning of next long slur)
    # --------------------
    if beamStatus['beginLongBracketSlur']:
        noteTrans.append(symbols['opening_bracket_slur'])
        music21Note.editorial.brailleEnglish.append(
            f'Opening bracket slur {symbols["opening_bracket_slur"]}')
    elif beamStatus['beginLongDoubleSlur']:
        noteTrans.append(symbols['opening_double_slur'])
        music21Note.editorial.brailleEnglish.append(
            f'Opening double slur {symbols["opening_double_slur"]}')
    if beamStatus['endLongBracketSlur'] and beamStatus['beginLongBracketSlur']:
        noteTrans.append(symbols['closing_bracket_slur'])
        music21Note.editorial.brailleEnglish.append(
            f'Closing bracket slur {symbols["closing_bracket_slur"]}')

    # Tuplets
    # -------
    allTuplets = music21Note.duration.tuplets
    if allTuplets:
        if beamStatus['beamStart']:
            if allTuplets[0].fullName == 'Triplet' and allTuplets[0].tupletActualShow != 'none':
                noteTrans.append(symbols['triplet'])  # dot 2-3
            else:
                if allTuplets[0].tupletActualShow == 'none':
                    noteTrans.append(symbols['transcriber-added_sign'])
                    music21Note.editorial.brailleEnglish.append(
                        f'transcriber-added {symbols["transcriber-added_sign"]}')
                tupletTrans = symbols['tuplet_prefix']  # dots 4,5,6
                tupletTrans += numberToBraille(allTuplets[0].numberNotesActual,
                                                 withNumberSign=False,
                                                 lower=True)
                tupletTrans += symbols['dot']
                noteTrans.append(tupletTrans)
            music21Note.editorial.brailleEnglish.append(
                f'{allTuplets[0].fullName} {noteTrans[-1]}'
            )
        elif beamStatus['beamContinue']:
            beamStatus['beamContinue'] = False

    # signs of expression or execution that precede a note
    # articulations
    # -------------
    for brailleArticulation in yieldBrailleArticulations(music21Note):
        noteTrans.append(brailleArticulation)

    # accidental
    # ----------
    try:
        handlePitchWithAccidental(
            music21Note.pitch,
            noteTrans,
            music21Note.editorial.brailleEnglish
        )
    except KeyError:
        environRules.warn(
            f'Accidental {music21Note.pitch.accidental} of note {music21Note} '
            + 'cannot be transcribed to braille.'
        )

    # octave mark
    # -----------
    if showOctave:
        brailleOctave = pitchToOctave(music21Note.pitch)
        noteTrans.append(brailleOctave)
        music21Note.editorial.brailleEnglish.append(f'Octave {music21Note.octave} {brailleOctave}')

    # note name
    # ---------
    try:
        notesInStep = lookup.pitchNameToNotes[music21Note.pitch.step]
    except KeyError:  # pragma: no cover
        environRules.warn(
            f"Name {music21Note.pitch.step!r} of note {music21Note} "
            + 'cannot be transcribed to braille.')
        music21Note.editorial.brailleEnglish.append(f'Name {music21Note.pitch.step} None')
        return symbols['basic_exception']

    # note duration
    # -------------
    if 'GraceDuration' in music21Note.duration.classes:
        # TODO: Short Appoggiatura mark...
        nameWithDuration = notesInStep['eighth']
        noteTrans.append(nameWithDuration)
        music21Note.editorial.brailleEnglish.append(
            f'{music21Note.step} {"eighth"} Gracenote--not supported {nameWithDuration}'
        )
    else:
        try:
            if beamStatus['beamContinue']:
                nameWithDuration = notesInStep['eighth']
                music21Note.editorial.brailleEnglish.append(
                    f'{music21Note.step} beam {nameWithDuration}')
            else:
                nameWithDuration = notesInStep[music21Note.duration.type]
                music21Note.editorial.brailleEnglish.append(
                    f'{music21Note.step} {music21Note.duration.type} {nameWithDuration}'
                )
            noteTrans.append(nameWithDuration)
            for unused_counter_dot in range(music21Note.duration.dots):
                noteTrans.append(symbols['dot'])
                music21Note.editorial.brailleEnglish.append(f'Dot {symbols["dot"]}')
        except KeyError:  # pragma: no cover
            environRules.warn(
                f'Duration {music21Note.duration} of note {music21Note} '
                + 'cannot be transcribed to braille.')
            music21Note.editorial.brailleEnglish.append(f'Duration {music21Note.duration} None')
            return symbols['basic_exception']

    handleArticulations(music21Note, noteTrans, upperFirstInFingering)
    handleExpressions(music21Note, noteTrans)

    # single slur
    # closing double slur (after second to last note, before last note)
    # opening double slur
    # closing bracket slur (unless note also has beginning long slur)
    # ----------------------------------
    if beamStatus['shortSlur']:
        noteTrans.append(symbols['opening_single_slur'])
        music21Note.editorial.brailleEnglish.append(
            f'Opening single slur {symbols["opening_single_slur"]}')
    if not(beamStatus['endLongBracketSlur'] and beamStatus['beginLongBracketSlur']):
        if beamStatus['endLongDoubleSlur']:
            noteTrans.append(symbols['closing_double_slur'])
            music21Note.editorial.brailleEnglish.append(
                f'Closing bracket slur {symbols["closing_double_slur"]}')
        elif beamStatus['endLongBracketSlur']:
            noteTrans.append(symbols['closing_bracket_slur'])
            music21Note.editorial.brailleEnglish.append(
                f'Closing bracket slur {symbols["closing_bracket_slur"]}')

    # tie
    # ---
    if music21Note.tie is not None and music21Note.tie.type != 'stop':
        noteTrans.append(symbols['tie'])
        music21Note.editorial.brailleEnglish.append(f'Tie {symbols["tie"]}')

    return ''.join(noteTrans)


def handlePitchWithAccidental(music21Pitch, pitchTrans, brailleEnglish):
    acc = music21Pitch.accidental
    if acc is not None and acc.displayStatus is not False:
        if acc.displayStyle == 'parentheses':
            ps = symbols['braille-music-parenthesis']
            pitchTrans.append(ps)
            brailleEnglish.append(f'Parenthesis {ps}')

        pitchTrans.append(lookup.accidentals[acc.name])
        brailleEnglish.append(f'Accidental {acc.name} {lookup.accidentals[acc.name]}')
        if acc.displayStyle == 'parentheses':
            ps = symbols['braille-music-parenthesis']
            pitchTrans.append(ps)
            brailleEnglish.append(f'Parenthesis {ps}')


def handleArticulations(music21Note, noteTrans, upperFirstInFingering=True):
    # finger mark
    # -----------
    try:
        for art in music21Note.articulations:
            if 'Fingering' in art.classes:
                transcribedFingering = transcribeNoteFingering(
                    art.fingerNumber,
                    upperFirstInFingering=upperFirstInFingering)
                noteTrans.append(transcribedFingering)
    except BrailleBasicException:  # pragma: no cover
        environRules.warn(
            f'Fingering {music21Note.editorial.fingering} of note {music21Note} '
            + 'cannot be transcribed to braille.')


def handleExpressions(music21Note, noteTrans):
    '''
    Transcribe the expressions for a Note or Rest (or anything with a .expressions list.
    '''
    # expressions (so far, just fermata)
    # ----------------------------------
    for expr in music21Note.expressions:
        if 'Fermata' in expr.classes:
            try:
                fermataBraille = lookup.fermatas['shape'][expr.shape]
                noteTrans.append(fermataBraille)
                music21Note.editorial.brailleEnglish.append(
                    f'Note-fermata: Shape {expr.shape}: {fermataBraille}')
            except KeyError:  # shape is unusual.
                environRules.warn(f'Fermata {expr} of note {music21Note} cannot be transcribed.')


def restToBraille(music21Rest):
    '''
    Given a :class:`~music21.note.Rest`, returns the appropriate braille
    characters as a string in UTF-8 unicode.


    Currently, only supports single rests with or without dots.
    Complex rests are not supported.

    >>> from music21.braille import basic
    >>> dottedQuarter = note.Rest(quarterLength=1.5)
    >>> print(basic.restToBraille(dottedQuarter))
    ⠧⠄
    >>> whole = note.Rest(quarterLength=4.0)
    >>> print(basic.restToBraille(whole))
    ⠍

    This would give a warning and gives the basic_exception symbol:

    quarterPlusSixteenth = note.Rest(quarterLength=1.25)
    print(basic.restToBraille(quarterPlusSixteenth))
    ⠜⠦
    '''
    music21Rest.editorial.brailleEnglish = []
    restTrans = []
    restType = music21Rest.duration.type
    restDots = music21Rest.duration.dots
    if music21Rest.fullMeasure is True:
        restType = 'whole'
        restDots = 0
    try:
        simpleRest = lookup.rests[restType]
    except KeyError:  # pragma: no cover
        environRules.warn(
            f'Rest of duration {music21Rest.duration} cannot be transcribed to braille.')
        music21Rest.editorial.brailleEnglish.append(f'Rest {music21Rest.duration.type} None')
        return symbols['basic_exception']

    restTrans.append(simpleRest)
    music21Rest.editorial.brailleEnglish.append(f'Rest {restType} {simpleRest}')
    for unused_counter_dot in range(restDots):
        restTrans.append(symbols['dot'])
        music21Rest.editorial.brailleEnglish.append(f'Dot {symbols["dot"]}')

    handleExpressions(music21Rest, restTrans)

    return ''.join(restTrans)


def tempoTextToBraille(
    music21TempoText: tempo.TempoText,
    *,
    maxLineLength=40
):
    # noinspection SpellCheckingInspection
    '''
    Takes in a :class:`~music21.tempo.TempoText` and returns its representation in braille
    as a string in UTF-8 unicode. The tempo text is returned uncentered, and is split around
    the comma, each split returned on a separate line. The literary period required at the end
    of every tempo text expression in braille is also included.

    >>> from music21.braille import basic
    >>> print(basic.tempoTextToBraille(tempo.TempoText('Lento assai, cantante e tranquillo')))
    ⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂
    ⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲
    >>> print(basic.tempoTextToBraille(tempo.TempoText('Andante molto grazioso')))
    ⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠕⠇⠞⠕⠀⠛⠗⠁⠵⠊⠕⠎⠕⠲

    >>> print(basic.tempoTextToBraille(tempo.TempoText('Andante molto grazioso ma cantabile')))
    ⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠕⠇⠞⠕⠀⠛⠗⠁⠵⠊⠕⠎⠕⠀⠍⠁⠀
    ⠉⠁⠝⠞⠁⠃⠊⠇⠑⠲

    >>> print(basic.tempoTextToBraille(tempo.TempoText('Andante molto grazioso ma cantabile'),
    ...                                    maxLineLength=20))
    ⠠⠁⠝⠙⠁⠝⠞⠑⠀
    ⠍⠕⠇⠞⠕⠀
    ⠛⠗⠁⠵⠊⠕⠎⠕⠀⠍⠁⠀
    ⠉⠁⠝⠞⠁⠃⠊⠇⠑⠲
    '''
    music21TempoText.editorial.brailleEnglish = []
    allPhrases = music21TempoText.text.split(',')
    braillePhrases = []
    for samplePhrase in allPhrases:
        allWords = samplePhrase.split()
        phraseTrans: List[str] = []
        for sampleWord in allWords:
            try:
                brailleWord = wordToBraille(sampleWord)
            except BrailleBasicException as wordException:  # pragma: no cover
                environRules.warn(f'Tempo Text {music21TempoText}: {wordException}')
                music21TempoText.editorial.brailleEnglish.append(
                    f'Tempo Text {music21TempoText.text} None'
                )
                return symbols['basic_exception']

            total_width = 0
            for phrase in phraseTrans:
                if phrase == '\n':
                    total_width = 0
                else:
                    total_width += len(phrase)

            if total_width + len(brailleWord) + 1 > (maxLineLength - 6):
                phraseTrans.append('\n')

            phraseTrans.append(brailleWord)
            phraseTrans.append(symbols['space'])
        braillePhrases.append(''.join(phraseTrans[0:-1]))

    joiner = alphabet[','] + '\n'
    brailleUnicodeText = joiner.join(braillePhrases) + alphabet['.']

    music21TempoText.editorial.brailleEnglish.append(
        f'Tempo Text {music21TempoText.text} {brailleUnicodeText}'
    )
    return brailleUnicodeText


def textExpressionToBraille(music21TextExpression, precedeByWordSign=True):
    '''
    Takes in a :class:`~music21.expressions.TextExpression` and returns its
    representation in UTF-8 unicode.

    From the lookup table:

    >>> print(braille.basic.textExpressionToBraille(expressions.TextExpression('cresc.')))
    ⠜⠉⠗⠄

    Single word expression has word symbol (⠜) only at beginning:

    >>> print(braille.basic.textExpressionToBraille(expressions.TextExpression('dolce')))
    ⠜⠙⠕⠇⠉⠑

    Multiple word expression has word symbol at beginning and end.

    >>> print(braille.basic.textExpressionToBraille(expressions.TextExpression('dim. e rall.')))
    ⠜⠙⠊⠍⠄⠀⠑⠀⠗⠁⠇⠇⠄⠜
    '''
    music21TextExpression.editorial.brailleEnglish = []
    teWords = music21TextExpression.content
    if teWords in lookup.textExpressions:
        simpleReturn = lookup.textExpressions[teWords]
        music21TextExpression.editorial.brailleEnglish.append(
            f'Text Expression {teWords} {simpleReturn}')
        return simpleReturn

    # not in this basic list...

    allExpr = teWords.split()
    textExpressionTrans = []

    try:
        for expr in allExpr:
            textExpressionTrans.append(wordToBraille(expr, isTextExpression=True))
    except BrailleBasicException as wordException:  # pragma: no cover
        environRules.warn(f'Text Expression {music21TextExpression}: {wordException}')
        music21TextExpression.editorial.brailleEnglish.append(f'Text Expression {teWords} None')
        return symbols['basic_exception']

    brailleTextExpr = symbols['space'].join(textExpressionTrans)
    music21TextExpression.editorial.brailleEnglish.append(
        f'Text Expression {teWords} {brailleTextExpr}')

    if precedeByWordSign:
        brailleTextExpr = symbols['word'] + brailleTextExpr
        music21TextExpression.editorial.brailleEnglish.insert(0, f'Word {symbols["word"]}')

    if len(allExpr) > 1:  # put a word symbol at the end if there is more than one word:
        brailleTextExpr = brailleTextExpr + symbols['word']
        music21TextExpression.editorial.brailleEnglish.append(f'Word {symbols["word"]}')

    return brailleTextExpr


def timeSigToBraille(m21TimeSignature):
    '''
    Takes in a :class:`~music21.meter.TimeSignature` and returns its
    representation in braille as a string in UTF-8 unicode.

    >>> from music21.braille import basic
    >>> print(basic.timeSigToBraille(meter.TimeSignature('4/4')))
    ⠼⠙⠲
    >>> print(basic.timeSigToBraille(meter.TimeSignature('3/4')))
    ⠼⠉⠲
    >>> print(basic.timeSigToBraille(meter.TimeSignature('12/8')))
    ⠼⠁⠃⠦
    >>> print(basic.timeSigToBraille(meter.TimeSignature('c')))
    ⠨⠉
    '''
    m21TimeSignature.editorial.brailleEnglish = []

    if m21TimeSignature.symbol in ('common', 'cut'):
        brailleSig = symbols[m21TimeSignature.symbol]
        m21TimeSignature.editorial.brailleEnglish.append(
            f'Time Signature {m21TimeSignature.symbol} {brailleSig}')
        return brailleSig

    try:
        timeSigTrans = [numberToBraille(m21TimeSignature.numerator),
                        numberToBraille(m21TimeSignature.denominator,
                                        withNumberSign=False,
                                        lower=True)]
        brailleSig = ''.join(timeSigTrans)
        m21TimeSignature.editorial.brailleEnglish.append(
            f'Time Signature {m21TimeSignature.numerator}/{m21TimeSignature.denominator} '
            + f'{brailleSig}'
        )
        return brailleSig
    except (BrailleBasicException, KeyError) as unused_error:  # pragma: no cover
        environRules.warn(
            f'Time Signature {m21TimeSignature} cannot be transcribed to braille.')
        m21TimeSignature.editorial.brailleEnglish.append(f'{m21TimeSignature} None')
        return symbols['basic_exception']

# ------------------------------------------------------------------------------
# Helper methods


def showOctaveWithNote(previousNote, currentNote):
    '''
    Determines whether a currentNote carries an octave designation in relation to a previous Note.


    Rules:

    * If currentNote is found within a second or third
      of previousNote, currentNote does not
      carry an octave designation.

    * If currentNote is found a sixth or
      more away from previousNote, currentNote does carry
      an octave designation.

    * If currentNote is found within a fourth or fifth
      of previousNote, currentNote carries
      an octave designation if and only if currentNote and
      previousNote are not found in the
      same octave.


    Of course, these rules cease to apply in quite a few cases, which are not directly reflected
    in the results of this method:


    1) If a braille measure goes to a new line, the first note in the measure carries an
       octave designation regardless of what the previous note was.


    2) If a braille measure contains a new key or time signature, the first note carries
       an octave designation regardless of what the previous note was.


    3) If a new key or time signature occurs in the middle of a measure, or if a double bar
       line is encountered, both of which would necessitate a music hyphen, the next note after
       those cases needs an octave marking.


    If any special case happens, previousNote can be set to None and the method will return
    True.


    >>> from music21.braille import basic
    >>> basic.showOctaveWithNote(note.Note('C4'), note.Note('E4'))
    False
    >>> basic.showOctaveWithNote(note.Note('C4'), note.Note('F4'))
    False
    >>> basic.showOctaveWithNote(note.Note('C4'), note.Note('F3'))
    True
    >>> basic.showOctaveWithNote(note.Note('C4'), note.Note('A4'))
    True

    If previousNote is None, it is always True

    >>> basic.showOctaveWithNote(None, note.Note('A4'))
    True
    '''
    if previousNote is None:
        return True
    i = interval.notesToInterval(previousNote, currentNote)
    isSixthOrGreater = i.generic.undirected >= 6
    isFourthOrFifth = i.generic.undirected == 4 or i.generic.undirected == 5
    sameOctaveAsPrevious = previousNote.octave == currentNote.octave
    doShowOctave = False
    if isSixthOrGreater or (isFourthOrFifth and not sameOctaveAsPrevious):
        doShowOctave = True

    return doShowOctave


def transcribeHeading(
    music21KeySignature=None,
    music21TimeSignature=None,
    music21TempoText=None,
    music21MetronomeMark=None,
    maxLineLength=40
):
    # noinspection SpellCheckingInspection
    '''
    Takes in a :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature`,
    :class:`~music21.tempo.TempoText`, and
    :class:`~music21.tempo.MetronomeMark` and returns its representation in braille as a
    string in UTF-8 unicode. The contents
    are always centered on a line, whose width is 40 by default.

    In most cases, the format is (tempo text)(space)(metronome mark)(space)(key/time signature),
    centered, although all of
    these need not be included. If all the contents do not fit on one line with at
    least 3 blank characters on each side, then
    the tempo text goes on the first line (and additional lines if necessary),
    and the metronome mark + key and time signature
    goes on the last line.

    If the resulting heading is of length zero, a BrailleBasicException is raised.

    >>> from music21.braille import basic
    >>> print(basic.transcribeHeading(key.KeySignature(5), meter.TimeSignature('3/8'),
    ...         tempo.TempoText('Allegretto'),
    ...         tempo.MetronomeMark(number=135, referent=note.Note(type='eighth'))))
    ⠀⠀⠀⠀⠀⠀⠀⠠⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠲⠀⠙⠶⠼⠁⠉⠑⠀⠼⠑⠩⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀
    >>> print(basic.transcribeHeading(
    ...          key.KeySignature(-2),
    ...          meter.TimeSignature('common'),
    ...          tempo.TempoText('Lento assai, cantante e tranquillo'),
    ...          None))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠨⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    >>> print(basic.transcribeHeading(
    ...          key.KeySignature(-2),
    ...          meter.TimeSignature('common'),
    ...          tempo.TempoText('Lento assai, cantante e tranquillo'),
    ...          None,
    ...          maxLineLength=10))
    ⠀⠠⠇⠑⠝⠞⠕⠀⠀⠀
    ⠀⠀⠁⠎⠎⠁⠊⠂⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠉⠁⠝⠞⠁⠝⠞⠑⠀⠀
    ⠀⠀⠀⠀⠑⠀⠀⠀⠀⠀
    ⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲
    ⠀⠀⠀⠣⠣⠨⠉⠀⠀⠀

    '''
    if (music21KeySignature is None
            and music21TimeSignature is None
            and music21TempoText is None
            and music21MetronomeMark is None):
        raise BrailleBasicException('No heading can be made.')
    # Tempo Text
    tempoTextTrans = None
    if music21TempoText is not None:
        tempoTextTrans = tempoTextToBraille(music21TempoText, maxLineLength=maxLineLength)

    if (music21KeySignature is None
            and music21TimeSignature is None
            and music21MetronomeMark is None):
        tempoTextLines = tempoTextTrans.splitlines()
        headingTrans = []
        for tempoText_line in tempoTextLines:
            headingTrans.append(tempoText_line)
        if len(tempoTextTrans) <= (maxLineLength - 6):
            headingTrans = ''.join(headingTrans)
            return headingTrans.center(maxLineLength, symbols['space'])
        else:
            for heading_line_index in range(len(headingTrans)):
                headingTrans[heading_line_index] = headingTrans[heading_line_index].center(
                    maxLineLength,
                    symbols['space']
                )
            return '\n'.join(headingTrans)

    otherTrans = []
    # Metronome Mark
    if music21MetronomeMark is not None:
        metronomeMarkTrans = metronomeMarkToBraille(music21MetronomeMark)
        otherTrans.append(metronomeMarkTrans)
    # Key Signature and Time Signature
    try:
        keyAndTimeSig = transcribeSignatures(music21KeySignature, music21TimeSignature)
        if music21MetronomeMark is not None:
            otherTrans.append(symbols['space'])
        otherTrans.append(keyAndTimeSig)
    except BrailleBasicException:
        if music21MetronomeMark is None and music21TempoText is None:
            raise BrailleBasicException('No heading can be made.')

    otherTransStr = ''.join(otherTrans)

    if tempoTextTrans is None:
        return otherTransStr.center(maxLineLength, symbols['space'])
    else:
        tempoTextLines = tempoTextTrans.splitlines()
        headingTrans = []
        for tempo_text_line in tempoTextLines:
            headingTrans.append(tempo_text_line)
        headingTrans.append(otherTransStr)
        while len(headingTrans) > 1 and not headingTrans[0]:
            # remove leading blank lines
            headingTrans = headingTrans[1:]
        while len(headingTrans) > 1 and not headingTrans[-1]:
            # remove trailing blank lines
            headingTrans = headingTrans[:-1]

        if len(tempoTextTrans) + len(otherTransStr) + 1 <= (maxLineLength - 6):
            headingTrans_str = symbols['space'].join(headingTrans)
            return headingTrans_str.center(maxLineLength, symbols['space'])
        else:
            for heading_line_index in range(len(headingTrans)):
                headingTrans[heading_line_index] = headingTrans[heading_line_index].center(
                    maxLineLength,
                    symbols['space']
                )
            return '\n'.join(headingTrans)


def transcribeNoteFingering(sampleNoteFingering='1', upperFirstInFingering=True):
    '''
    Takes in a note fingering, an attribute :attr:`~music21.note.Note.editorial.fingering`, and
    returns its correct transcription to braille. Fingering is not officially supported
    by music21, but it is described in Chapter 9 of the "Introduction to Braille Music
    Transcription" manual.

    >>> from music21.braille import basic
    >>> print(basic.transcribeNoteFingering('4'))
    ⠂

    A change of fingering:

    >>> print(basic.transcribeNoteFingering('2-1'))
    ⠃⠉⠁

    A choice of fingering, both on either the top or bottom of the staff:

    >>> print(basic.transcribeNoteFingering('5|4', upperFirstInFingering=True))
    ⠅⠂
    >>> print(basic.transcribeNoteFingering('5|4', upperFirstInFingering=False))
    ⠂⠅

    A choice of fingering, one on top and one below the staff:

    >>> print(basic.transcribeNoteFingering('2,1', upperFirstInFingering=True))
    ⠃⠁
    >>> print(basic.transcribeNoteFingering('2,1', upperFirstInFingering=False))
    ⠁⠃

    A choice of fingering, first set missing fingermark:

    >>> print(basic.transcribeNoteFingering('2,x'))
    ⠃⠄

    A choice of fingering, second set missing fingermark:

    >>> print(basic.transcribeNoteFingering('x,2'))
    ⠠⠃

    Missing fingermarks change with upperFirstInFingering

    >>> print(basic.transcribeNoteFingering('x,4', upperFirstInFingering=True))
    ⠠⠂
    >>> print(basic.transcribeNoteFingering('x,4', upperFirstInFingering=False))
    ⠂⠄
    >>> print(basic.transcribeNoteFingering('4,x', upperFirstInFingering=True))
    ⠂⠄
    >>> print(basic.transcribeNoteFingering('4,x', upperFirstInFingering=False))
    ⠠⠂


    A change of fingering and a choice of fingering combined (thanks to Bo-cheng Jhan
    for the patch):

    >>> print(basic.transcribeNoteFingering('1-2|3-4'))
    ⠁⠉⠃⠇⠉⠂

    Incorrect fingerings raise a BrailleBasicException:

    >>> basic.transcribeNoteFingering('6')
    Traceback (most recent call last):
    music21.braille.basic.BrailleBasicException: Cannot translate note fingering: 6
    '''
    fingerMarks = lookup.fingerMarks
    if isinstance(sampleNoteFingering, int):
        sampleNoteFingering = str(sampleNoteFingering)

    if len(sampleNoteFingering) == 1:
        try:
            return fingerMarks[sampleNoteFingering]
        except KeyError:  # pragma: no cover
            raise BrailleBasicException(f'Cannot translate note fingering: {sampleNoteFingering}')

    trans = []
    choice = sampleNoteFingering.split(',')
    if len(choice) == 2:
        allowAbsence = True
    elif len(choice) == 1:
        choice = sampleNoteFingering.split('|')
        allowAbsence = False
    else:
        raise KeyError
    if not upperFirstInFingering:
        choice.reverse()

    for i in range(len(choice)):
        change = choice[i].split('-')
        try:
            if len(change) == 2:
                trans.append(fingerMarks[change[0]])
                trans.append(symbols['finger_change'])
                trans.append(fingerMarks[change[1]])
            elif len(change) == 1:
                changeMark = change[0]
                fingerMarkToAppend = ''
                try:
                    fingerMarkToAppend = fingerMarks[changeMark]
                except KeyError as e:
                    if not allowAbsence:
                        raise e
                    # a missing symbol, such as "x" was used.  Get the appropriate
                    # missing fingermark symbol.
                    if i == 0:
                        fingerMarkToAppend = symbols['first_set_missing_fingermark']
                    else:
                        fingerMarkToAppend = symbols['second_set_missing_fingermark']
                trans.append(fingerMarkToAppend)
        except KeyError:  # pragma: no cover
            raise BrailleBasicException(f'Cannot translate note fingering: {sampleNoteFingering}')

    return ''.join(trans)


def transcribeSignatures(music21KeySignature, music21TimeSignature, outgoingKeySig=None):
    '''
    Takes in a :class:`~music21.key.KeySignature` and
    :class:`~music21.meter.TimeSignature` and returns its representation
    in braille as a string in UTF-8 unicode. If given an old key signature,
    then its cancellation will be applied before
    and in relation to the new key signature.

    Raises a BrailleBasicException if the resulting key and time signature is
    empty, which happens if the time signature
    is None and (a) the key signature is None or (b) the key signature has
    zero sharps and there is no previous key signature.

    >>> from music21.braille import basic
    >>> print(basic.transcribeSignatures(key.KeySignature(5), meter.TimeSignature('3/8'), None))
    ⠼⠑⠩⠼⠉⠦
    >>> print(basic.transcribeSignatures(key.KeySignature(0), None, key.KeySignature(-3)))
    ⠡⠡⠡
    '''
    if (music21TimeSignature is None
            and (music21KeySignature is None
                 or (music21KeySignature.sharps == 0 and outgoingKeySig is None))):
        return ''

    trans = []
    if music21KeySignature is not None:
        trans.append(keySigToBraille(music21KeySignature, outgoingKeySig=outgoingKeySig))
    if music21TimeSignature is not None:
        trans.append(timeSigToBraille(music21TimeSignature))

    return ''.join(trans)

# ------------------------------------------------------------------------------
# Translation between braille unicode and ASCII/other symbols.


def brailleUnicodeToBrailleAscii(brailleUnicode):
    r'''
    translates a braille UTF-8 unicode string into braille ASCII,
    which is the format compatible with most braille embossers.


    .. note:: The method works by corresponding braille symbols to ASCII symbols.
        The table which corresponds said values can be found
        `here <http://en.wikipedia.org/wiki/Braille_ASCII#Braille_ASCII_values>`_.
        Because of the way in which the braille symbols translate2, the resulting
        ASCII string will look to a non-reader as gibberish. Also, the eighth-note notes
        in braille
        music are one-off their corresponding letters in both ASCII and written braille.
        The written D is really a C eighth-note, the written E is really a
        D eighth note, etc.


    >>> from music21.braille import basic
    >>> basic.brailleUnicodeToBrailleAscii('\u2800')
    ' '
    >>> Cs8 = note.Note('C#4', quarterLength=0.5)
    >>> Cs8_braille = basic.noteToBraille(Cs8)
    >>> basic.brailleUnicodeToBrailleAscii(Cs8_braille)
    '%"D'
    >>> Eb8 = note.Note('E-4', quarterLength=0.5)
    >>> Eb8_braille = basic.noteToBraille(Eb8)
    >>> basic.brailleUnicodeToBrailleAscii(Eb8_braille)
    '<"F'
    '''
    brailleLines = brailleUnicode.splitlines()
    asciiLines = []

    for sampleLine in brailleLines:
        allChars = []
        for char in sampleLine:
            allChars.append(ascii_chars[char])
        asciiLines.append(''.join(allChars))

    return '\n'.join(asciiLines)


def brailleAsciiToBrailleUnicode(brailleAscii):
    '''
    translates a braille ASCII string to braille UTF-8 unicode, which
    can then be displayed on-screen in braille on compatible systems.


    .. note:: The method works by corresponding ASCII symbols to braille
        symbols in a very direct fashion. It is not a translator from plain
        text to braille, because ASCII symbols may not correspond to their
        equivalents in braille. For example, a literal period is a 4 in
        braille ASCII. Also, all letters are translated into their lowercase
        equivalents, and any capital letters are indicated by preceding them
        with a comma.


    >>> from music21.braille import basic
    >>> t1 = basic.brailleAsciiToBrailleUnicode(',ANDANTE ,MAESTOSO4')
    >>> t2 = basic.tempoTextToBraille(tempo.TempoText('Andante Maestoso'))
    >>> t1 == t2
    True
    '''
    braille_chars = {}
    for key in ascii_chars:
        braille_chars[ascii_chars[key]] = key

    asciiLines = brailleAscii.splitlines()
    brailleLines = []

    for sampleLine in asciiLines:
        allChars = []
        for char in sampleLine:
            allChars.append(braille_chars[char.upper()])
        brailleLines.append(''.join(allChars))

    return '\n'.join(brailleLines)


def brailleUnicodeToSymbols(brailleUnicode, filledSymbol='o', emptySymbol='\u00B7'):
    '''
    translates a braille unicode string into symbols (unicode) -- for debugging.

    >>> print(braille.basic.brailleUnicodeToSymbols('⠜'))
    ·o
    ·o
    o·
    '''
    symbolTrans = {'00': f'{emptySymbol}{emptySymbol}',
                   '01': f'{emptySymbol}{filledSymbol}',
                   '10': f'{filledSymbol}{emptySymbol}',
                   '11': f'{filledSymbol}{filledSymbol}'}

    brailleLines = brailleUnicode.splitlines()
    binaryLines = []

    for sampleLine in brailleLines:
        binaryLine1 = []
        binaryLine2 = []
        binaryLine3 = []
        for char in sampleLine:
            (dots14, dots25, dots36) = lookup.binary_dots[char]
            binaryLine1.append(symbolTrans[dots14])
            binaryLine2.append(symbolTrans[dots25])
            binaryLine3.append(symbolTrans[dots36])
        binaryLines.append('  '.join(binaryLine1))
        binaryLines.append('  '.join(binaryLine2))
        binaryLines.append('  '.join(binaryLine3))
        binaryLines.append('')

    return '\n'.join(binaryLines[0:-1])


def yieldDots(brailleCharacter):
    '''
    Generator that yields symbol['dot'] characters for each row of a
    braille character that where the left dot is filled.  These
    are used in many places in Braille Music Code.

    >>> B = braille.lookup.brailleDotDict
    >>> gen = braille.basic.yieldDots(B[1])
    >>> gen
    <generator object yieldDots at 0x10aee5f68>
    >>> for dot in gen:
    ...     print(dot)
    ⠄
    >>> gen = braille.basic.yieldDots(B[1235])
    >>> for dot in gen:
    ...     print(dot)
    ⠄
    ⠄
    ⠄
    '''
    for dots in lookup.binary_dots[brailleCharacter]:
        if dots in ('10', '11'):
            yield symbols['dot']

# ------------------------------------------------------------------------------
# Transcription of words and numbers.


def wordToBraille(sampleWord, isTextExpression=False):
    # noinspection SpellCheckingInspection
    '''
    Transcribes a word to UTF-8 braille.

    >>> from music21.braille import basic
    >>> print(basic.wordToBraille('Andante'))
    ⠠⠁⠝⠙⠁⠝⠞⠑

    Try the German for violin.

    >>> print(basic.wordToBraille('Geige'))
    ⠠⠛⠑⠊⠛⠑

    Tests number symbol at beginning, punctuation in number
    and switch back to letters.

    >>> print(basic.wordToBraille('25.4cm'))
    ⠼⠃⠑⠲⠙⠰⠉⠍
    '''
    wordTrans = []

    def add_letter(inner_letter):
        if inner_letter in alphabet:
            wordTrans.append(alphabet[inner_letter])
        else:
            l2 = stringTools.stripAccents(inner_letter)
            if l2 == inner_letter:
                raise KeyError('Cannot translate ' + inner_letter)
            wordTrans.append(alphabet['^'])
            wordTrans.append(alphabet[l2])

    if isTextExpression:
        for letter in sampleWord:
            if letter.isupper():
                add_letter(letter.lower())
            elif letter == '.':
                wordTrans.append(symbols['dot'])
            else:
                try:
                    add_letter(letter)
                except KeyError:
                    raise BrailleBasicException(
                        f"Character '{letter}' in Text Expression '{sampleWord}' "
                        + 'cannot be transcribed to braille.')
        return ''.join(wordTrans)

    lastCharWasNumber = False

    for letter in sampleWord:
        try:
            if letter.isdigit() and not lastCharWasNumber:
                wordTrans.append(symbols['number'])
                lastCharWasNumber = True
            elif letter.isalpha() and lastCharWasNumber:
                wordTrans.append(symbols['letter_sign'])
                lastCharWasNumber = False

            if letter.isupper():
                wordTrans.append(symbols['uppercase'])
                add_letter(letter.lower())
            elif letter.isdigit():
                wordTrans.append(lookup.numbersUpper[int(letter)])
            else:
                add_letter(letter)

        except KeyError:  # pragma: no cover
            raise BrailleBasicException(
                f"Character '{letter}' in word '{sampleWord}' cannot be transcribed to braille."
            )

    return ''.join(wordTrans)


def numberToBraille(sampleNumber, withNumberSign=True, lower=False):
    '''
    Transcribes a number to UTF-8 braille. By default, the result number
    occupies the upper two thirds of braille cells with a leading number sign.
    If withNumberSign is set to False, the leading number sign will be removed.
    If lower is set to True, the position will be changed from the upper (1245
    dots) to the lower (2356 dots).

    >>> from music21.braille import basic
    >>> print(basic.numberToBraille(12))
    ⠼⠁⠃
    >>> print(basic.numberToBraille(7))
    ⠼⠛
    >>> print(basic.numberToBraille(37))
    ⠼⠉⠛
    '''
    numberTrans = []
    if withNumberSign:
        numberTrans.append(symbols['number'])
    if lower:
        numbers = lookup.numbersLower
    else:
        numbers = lookup.numbersUpper
    for digit in str(sampleNumber):
        try:
            numberTrans.append(numbers[int(digit)])
        except ValueError:  # pragma: no cover
            raise BrailleBasicException(
                f"Digit '{digit}' in number '{sampleNumber}' cannot be transcribed to braille."
            )
    return ''.join(numberTrans)

# ------------------------------------------------------------------------------


class BrailleBasicException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , verbose=True)

