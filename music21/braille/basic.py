# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         basic.py
# Purpose:      music21 class which allows transcription of music21Object instances to braille.
# Authors:      Jose Cabal-Ugaz
#               Bo-cheng (Sponge) Jhan (Clef routines)
#
# Copyright:    Copyright © 2011, 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import unittest

#from music21 import articulations
from music21 import clef
from music21 import environment
from music21 import exceptions21
from music21 import interval
from music21 import note

from music21.braille import lookup

# Add aliases to lookup tables ONLY if it will be used in many different contexts
# if it is used in only one function, make the alias there.
alphabet = lookup.alphabet
ascii_chars = lookup.ascii_chars
symbols = lookup.symbols

environRules = environment.Environment('basic.py')

beamStatus = {}
#-------------------------------------------------------------------------------
# music21Object to braille unicode methods

#noinspection PyStatementEffect
"""
Any :class:`~music21.base.Music21Object` which cannot be transcribed in
:mod:`~music21.braille.basic` returns a braille literary question mark
and outputs a warning to the console, rather than raising an exception.
This is so that a transcription of a :class:`~music21.stream.Stream` in
:class:`~music21.braille.translate` is completed as thoroughly as possible.
"""
def barlineToBraille(music21Barline):
    u"""
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
    """
    try:
        brailleBarline = lookup.barlines[music21Barline.style]
        music21Barline._brailleEnglish = [
                        u"Barline {0} {1}".format(music21Barline.style, brailleBarline)]
        return brailleBarline
    except KeyError:  # pragma: no cover
        environRules.warn("Barline {0} cannot be transcribed to braille.".format(music21Barline))
        music21Barline._brailleEnglish = ["Barline {0} None".format(music21Barline.style)]
        return symbols['basic_exception']

def chordToBraille(music21Chord, descending=True, showOctave=True):
    u"""
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
    """
    music21Chord._brailleEnglish = []
    allPitches = sorted(music21Chord.pitches)
    direction = 'Descending'
    if descending:
        allPitches.reverse()
    else:
        direction = 'Ascending'

    chordTrans = []
    basePitch = allPitches[0]
    initNote = note.Note(basePitch, quarterLength=music21Chord.quarterLength)
    brailleNote = noteToBraille(music21Note=initNote,showOctave=showOctave)
    if brailleNote == symbols['basic_exception']:  # pragma: no cover
        environRules.warn("Chord {0} cannot be transcribed to braille.".format(music21Chord))
        music21Chord._brailleEnglish.append("{0} None".format(music21Chord))
        return symbols['basic_exception']
    chordTrans.append(brailleNote)
    music21Chord._brailleEnglish.append(u"{0} Chord:\n{1}".format(
                                direction, u"\n".join(initNote._brailleEnglish)))

    for currentPitchIndex in range(1, len(allPitches)):
        currentPitch = allPitches[currentPitchIndex]
        intervalDistance = interval.notesToInterval(basePitch, currentPitch).generic.undirected
        if intervalDistance > 8:
            intervalDistance = intervalDistance % 8 + 1
            if currentPitchIndex == 1:
                brailleOctave = pitchToOctave(currentPitch)
                chordTrans.append(brailleOctave)
                music21Chord._brailleEnglish.append(
                    u"Octave {0} {1}".format(currentPitch.octave, brailleOctave))
            else:
                previousPitch = allPitches[currentPitchIndex - 1]
                relativeIntervalDist = interval.notesToInterval(previousPitch, 
                                                            currentPitch).generic.undirected
                if relativeIntervalDist >= 8:
                    brailleOctave = pitchToOctave(currentPitch)
                    chordTrans.append(brailleOctave)
                    music21Chord._brailleEnglish.append(
                        u"Octave {0} {1}".format(currentPitch.octave, brailleOctave))
        chordTrans.append(lookup.intervals[intervalDistance])
        music21Chord._brailleEnglish.append(u"Interval {0} {1}".format(intervalDistance, 
                                                            lookup.intervals[intervalDistance]))
    return u"".join(chordTrans)

def pitchToOctave(music21PitchOrInt):
    u'''
    takes a pitch object and returns the brailling for the octave.
    
    Can also be given an int specifying the octave.
    
    Expands the definition given in Degarmo Ch 7 to allow even less commonly used octaves such
    as -1, and > 8 by tripling, etc. the number of octave marks.
    
    >>> print(braille.basic.pitchToOctave(pitch.Pitch("C4")))
    ⠐
    >>> print(braille.basic.pitchToOctave(pitch.Pitch("B-4")))
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
    u"""
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
    >>> basic.clefToBraille(noClef) == ""
    True
    >>> sopranoClef = clef.SopranoClef()
    >>> print("%s, %d, %s" % (sopranoClef.sign, sopranoClef.line, basic.clefToBraille(sopranoClef)))
    C, 1, ⠜⠬⠈⠇
    """
    clefNames = {
        "FrenchViolinClef": u"French Violin",
        "TrebleClef": u"Treble",
        "GSopranoClef": u"G-soprano",
        "SopranoClef": u"Soprano",
        "MezzoSopranoClef": u"Mezzo-soprano",
        "AltoClef": u"Alto",
        "TenorClef": u"Tenor",
        "CBaritoneClef": u"C-baritone",
        "FBaritoneClef": u"F-baritone",
        "BassClef": u"Bass",
        "SubBassClef": u"Sub-bass"
        }
    if isinstance(music21Clef, clef.NoClef):
        music21Clef._brailleEnglish = [u"No Clef {0}".format(str(music21Clef))]
        return u""
    clefs = lookup.clefs
    brailleClef = clefs['prefix']
    try:
        brailleClef += clefs[music21Clef.sign][music21Clef.line]
        try:
            music21Clef._brailleEnglish = ([clefNames[music21Clef.__class__.__name__] + 
                                            u" Clef {0}".format(brailleClef)])
        except KeyError:  # pragma: no cover
            music21Clef._brailleEnglish = [u"Unnamed Clef {0}".format(str(music21Clef))]
        if isinstance(music21Clef, clef.TrebleClef) or isinstance(music21Clef, clef.BassClef):
            brailleClef += clefs['suffix'][keyboardHandSwitched]
            if keyboardHandSwitched:
                music21Clef._brailleEnglish.append(' Keyboard hand switched')
        else:
            brailleClef += clefs['suffix'][False]
        return brailleClef
    except KeyError: # pragma: no cover
        environRules.warn("Clef {0} cannot be transcribed to braille.".format(music21Clef))
        music21Clef._brailleEnglish = ["{0} None".format(str(music21Clef))]
        return symbols['basic_exception']

def dynamicToBraille(music21Dynamic, precedeByWordSign=True):
    u"""
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
    """
    dynamicTrans = []
    music21Dynamic._brailleEnglish = []
    if precedeByWordSign:
        dynamicTrans.append(symbols['word'])
        music21Dynamic._brailleEnglish.append(u"Word: {0}".format(symbols['word']))
    
    try:
        brailleDynamic = wordToBraille(music21Dynamic.value, isTextExpression=True)
    except BrailleBasicException as wordException:  # pragma: no cover
        environRules.warn("Dynamic {0}: {1}".format(music21Dynamic, wordException))
        music21Dynamic._brailleEnglish.append("Dynamic {0} None".format(music21Dynamic.value))
        return symbols['basic_exception']
    
    music21Dynamic._brailleEnglish.append(
            u"Dynamic {0} {1}".format(music21Dynamic.value, brailleDynamic))
    dynamicTrans.append(brailleDynamic)
    return u"".join(dynamicTrans)
    

def instrumentToBraille(music21Instrument):
    u"""
    Takes in a :class:`~music21.instrument.Instrument` and returns its "best name"
    as a braille string in UTF-8 unicode.

    >>> from music21.braille import basic
    >>> print(basic.instrumentToBraille(instrument.Bassoon()))
    ⠠⠃⠁⠎⠎⠕⠕⠝
    >>> print(basic.instrumentToBraille(instrument.BassClarinet()))
    ⠠⠃⠁⠎⠎⠀⠉⠇⠁⠗⠊⠝⠑⠞
    """
    music21Instrument._brailleEnglish = []
    allWords = music21Instrument.bestName().split()
    try:
        trans = [wordToBraille(word) for word in allWords]
    except BrailleBasicException as wordException:  # pragma: no cover
        environRules.warn("Instrument {0}: {1}".format(music21Instrument, wordException))
        music21Instrument._brailleEnglish.append("Instrument {0} None".format(
                                                music21Instrument.bestName()))
        return symbols['basic_exception']

    brailleInst = symbols['space'].join(trans)
    music21Instrument._brailleEnglish.append(
        u"Instrument {0} {1}".format(music21Instrument.bestName(), brailleInst))
    return brailleInst

def keySigToBraille(music21KeySignature, outgoingKeySig=None):
    u"""
    Takes in a :class:`~music21.key.KeySignature` and returns its representation
    in braille as a string in UTF-8 unicode.

    >>> from music21.braille import basic
    >>> print(basic.keySigToBraille(key.KeySignature(4)))
    ⠼⠙⠩


    If given an old key signature, then its cancellation will be applied before
    and in relation to the new key signature.


    >>> print(basic.keySigToBraille(key.KeySignature(0), outgoingKeySig = key.KeySignature(-3)))
    ⠡⠡⠡
    """
    naturals = lookup.naturals
    music21KeySignature._brailleEnglish = []
    incomingSharps = music21KeySignature.sharps
    try:
        ks_braille = lookup.keySignatures[incomingSharps]
    except KeyError:
        environRules.warn("Incoming Key Signature {0} cannot be transcribed to braille.".format(
                                                music21KeySignature))
        music21KeySignature._brailleEnglish.append("Key Signature {0} sharps None".format(
                                                music21KeySignature))
        return symbols['basic_exception']

    if incomingSharps > 0:
        music21KeySignature._brailleEnglish.append(u"Key Signature {0} sharp(s) {1}".format(
                                            incomingSharps, ks_braille))
    else:
        music21KeySignature._brailleEnglish.append(u"Key Signature {0} flat(s) {1}".format(
                                            abs(incomingSharps), ks_braille))
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
            music21KeySignature._brailleEnglish.insert(0, 
                u"Key Signature {0} naturals {1}".format(outgoingSharps, 
                                                         naturals[absOutgoing]))
        elif absOutgoing >= absIncoming:
            trans.append(naturals[abs(outgoingSharps - incomingSharps)])
            music21KeySignature._brailleEnglish.insert(0, 
                u"Key Signature {0} naturals {1}".format(
                    outgoingSharps, naturals[abs(outgoingSharps - incomingSharps)]))
        trans.append(ks_braille)
        return u"".join(trans)
    
    except KeyError:  # pragma: no cover
        environRules.warn(
            "Outgoing Key Signature {0} cannot be transcribed to braille.".format(outgoingKeySig))
        music21KeySignature._brailleEnglish.append("{0} naturals=None".format(outgoingKeySig))
        return ks_braille
    
def metronomeMarkToBraille(music21MetronomeMark):
    u"""
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
    """
    music21MetronomeMark._brailleEnglish = []
    try:
        metroTrans = []
        metroNote = note.Note('C4', quarterLength=music21MetronomeMark.referent.quarterLength)
        brailleNote = noteToBraille(metroNote, showOctave=False)
        metroTrans.append(brailleNote)
        music21MetronomeMark._brailleEnglish.append(u"Metronome Note {0}".format(u" ".join(
                                                    metroNote._brailleEnglish)))
        metroTrans.append(symbols['metronome'])
        music21MetronomeMark._brailleEnglish.append(u"Metronome symbol {0}".format(
                                                    symbols['metronome']))
        brailleNumber = numberToBraille(music21MetronomeMark.number)
        metroTrans.append(brailleNumber)
        music21MetronomeMark._brailleEnglish.append(u"Metronome number {0} {1}".format(
                                                    music21MetronomeMark.number, brailleNumber))
        return u"".join(metroTrans)
    except BrailleBasicException as numberException:  # pragma: no cover
        environRules.warn("Metronome Mark {0}: {1}".format(music21MetronomeMark, numberException))  
        music21MetronomeMark._brailleEnglish.append("{0} None".format(music21MetronomeMark))
        return symbols['basic_exception']


def yieldBrailleArticulations(noteEl):
    u'''
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
    def _brailleArticulationsSortKey(art):
        isStaccato = (art.name not in ('staccato', 'staccatissimo'))
        return (isStaccato, art.name)
    
    if hasattr(noteEl, 'articulations'): # should be True, but safeside.
        for art in sorted(noteEl.articulations, key=_brailleArticulationsSortKey):
            if art.name in lookup.beforeNoteExpr:
                brailleArt = lookup.beforeNoteExpr[art.name]
                if hasattr(noteEl, '_brailleEnglish'):
                    noteEl._brailleEnglish.append(u"Articulation {0} {1}".format(
                                                                art.name, brailleArt))            
                yield brailleArt
        

def noteToBraille(music21Note, showOctave=True, upperFirstInFingering=True):
    u"""
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
    >>> for x in B._brailleEnglish:
    ...     print(x)
    Octave 4 ⠐
    B quarter ⠺
    Note-fermata: Shape normal: ⠣⠇
    
    >>> f.shape = 'square'
    >>> print(basic.noteToBraille(B))
    ⠐⠺⠰⠣⠇
    >>> for x in B._brailleEnglish:
    ...     print(x)
    Octave 4 ⠐
    B quarter ⠺
    Note-fermata: Shape square: ⠰⠣⠇
    """
    
    # Note: both beamStatus, and _brailleEnglish are crutches that I hope to remove
    # when moving all the translation features to a separate class.
    music21Note._brailleEnglish = []
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
        music21Note._brailleEnglish.append(u"Opening bracket slur {0}".format(
                                                        symbols['opening_bracket_slur']))
    elif beamStatus['beginLongDoubleSlur']: 
        noteTrans.append(symbols['opening_double_slur'])
        music21Note._brailleEnglish.append(u"Opening double slur {0}".format(
                                                        symbols['opening_double_slur']))
    if beamStatus['endLongBracketSlur'] and beamStatus['beginLongBracketSlur']: 
        noteTrans.append(symbols['closing_bracket_slur'])
        music21Note._brailleEnglish.append(u"Closing bracket slur {0}".format(
                                                        symbols['closing_bracket_slur']))

    # Tuplets
    # -------
    allTuplets = music21Note.duration.tuplets
    if allTuplets:
        if beamStatus['beamStart']: 
            if allTuplets[0].fullName == 'Triplet':
                noteTrans.append(symbols['triplet']) # dot 2-3
            else:
                noteTrans.append(symbols['tuplet_prefix']) # dots 4,5,6
                noteTrans.append(numberToBraille(allTuplets[0].numberNotesActual, 
                                                 withNumberSign=False, 
                                                 lower=True))
                noteTrans.append(symbols['dot'])
            music21Note._brailleEnglish.append(u"{0} {1}".format(allTuplets[0].fullName, 
                                                                 symbols['triplet']))
        elif beamStatus['beamContinue']: 
            beamStatus['beamContinue'] = False
    
    # signs of expression or execution that precede a note
    # articulations
    # -------------
    for brailleArticulation in yieldBrailleArticulations(music21Note):
        noteTrans.append(brailleArticulation)
    
    # accidental
    # ----------
    handleNoteWithAccidental(music21Note, noteTrans)
                            
    # octave mark
    # -----------
    if showOctave:
        brailleOctave = pitchToOctave(music21Note.pitch)
        noteTrans.append(brailleOctave)
        music21Note._brailleEnglish.append(u"Octave {0} {1}".format(
                        music21Note.octave, brailleOctave))

    # note name
    # ---------
    try:
        notesInStep = lookup.pitchNameToNotes[music21Note.pitch.step]
    except KeyError:  # pragma: no cover
        environRules.warn("Name '{0}' of note {1} cannot be transcribed to braille.".format(
                        music21Note.pitch.step, music21Note)) 
        music21Note._brailleEnglish.append("Name {0} None".format(music21Note.pitch.step))
        return symbols['basic_exception']
    
    # note duration
    # -------------
    if 'GraceDuration' in music21Note.duration.classes:
        # TODO: Short Appogiatura mark...
        nameWithDuration = notesInStep['eighth']
        noteTrans.append(nameWithDuration)
        music21Note._brailleEnglish.append(u"{0} {1} Gracenote--not supported {2}".format(
                        music21Note.step, 'eighth', nameWithDuration))
    else:
        try:
            if beamStatus['beamContinue']: 
                nameWithDuration = notesInStep['eighth']
                music21Note._brailleEnglish.append(u"{0} beam {1}".format(
                        music21Note.step, nameWithDuration))
            else:
                nameWithDuration = notesInStep[music21Note.duration.type]
                music21Note._brailleEnglish.append(u"{0} {1} {2}".format(
                        music21Note.step, music21Note.duration.type, nameWithDuration))
            noteTrans.append(nameWithDuration)
            for unused_counter_dot in range(music21Note.duration.dots):
                noteTrans.append(symbols['dot'])
                music21Note._brailleEnglish.append(u"Dot {0}".format(symbols['dot']))
        except KeyError:  # pragma: no cover
            environRules.warn("Duration {0} of note {1} cannot be transcribed to braille.".format(
                                        music21Note.duration, music21Note))
            music21Note._brailleEnglish.append("Duration {0} None".format(music21Note.duration))
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
        music21Note._brailleEnglish.append(
                u"Opening single slur {0}".format(symbols['opening_single_slur']))
    if not(beamStatus['endLongBracketSlur'] and beamStatus['beginLongBracketSlur']): 
        if beamStatus['endLongDoubleSlur']: 
            noteTrans.append(symbols['closing_double_slur'])
            music21Note._brailleEnglish.append(
                u"Closing bracket slur {0}".format(symbols['closing_double_slur']))
        elif beamStatus['endLongBracketSlur']: 
            noteTrans.append(symbols['closing_bracket_slur'])
            music21Note._brailleEnglish.append(
                u"Closing bracket slur {0}".format(symbols['closing_bracket_slur']))


    # tie
    # ---
    if music21Note.tie is not None and music21Note.tie.type != 'stop':
        noteTrans.append(symbols['tie'])
        music21Note._brailleEnglish.append(u"Tie {0}".format(symbols['tie']))

    return u"".join(noteTrans)

def handleNoteWithAccidental(music21Note, noteTrans):
    acc = music21Note.pitch.accidental
    if (acc is not None and acc.displayStatus is not False):
        try:
            if acc.displayStyle == 'parentheses':
                ps = symbols['braille-music-parenthesis']
                noteTrans.append(ps)
                music21Note._brailleEnglish.append(u"Parenthesis {0}".format(ps))              
                
            noteTrans.append(lookup.accidentals[acc.name])
            music21Note._brailleEnglish.append(u"Accidental {0} {1}".format(
                                                    acc.name, lookup.accidentals[acc.name]))              
            if acc.displayStyle == 'parentheses':
                ps = symbols['braille-music-parenthesis']
                noteTrans.append(ps)
                music21Note._brailleEnglish.append(u"Parenthesis {0}".format(ps))              

        except KeyError:  # pragma: no cover
            environRules.warn("Accidental {0} of note {1} cannot be transcribed to braille.".format(
                                acc, music21Note))

def handleArticulations(music21Note, noteTrans, upperFirstInFingering=True):
    # finger mark
    # -----------
    try:
        for art in music21Note.articulations:
            if 'Fingering' in art.classes:
                transcribedFingering = transcribeNoteFingering(art.fingerNumber, 
                                                        upperFirstInFingering=upperFirstInFingering)
                noteTrans.append(transcribedFingering)
    except BrailleBasicException:  # pragma: no cover
        environRules.warn("Fingering {0} of note {1} cannot be transcribed to braille.".format(
                                        music21Note.fingering, music21Note))


def handleExpressions(music21Note, noteTrans):
    u'''
    Transcribe the expressions for a Note or Rest (or anything with a .expressions list.
    '''
    # expressions (so far, just fermata)
    # ----------------------------------
    for expr in music21Note.expressions:
        if 'Fermata' in expr.classes:
            try:
                fermataBraille = lookup.fermatas['shape'][expr.shape]
                noteTrans.append(fermataBraille)
                music21Note._brailleEnglish.append(
                    u'Note-fermata: Shape {0}: {1}'.format(expr.shape, fermataBraille))
            except KeyError: # shape is unusual.
                environRules.warn("Fermata {0} of note {1} cannot be transcribed.".format(
                                        expr, music21Note))
                


def restToBraille(music21Rest):
    u"""
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
    """
    music21Rest._brailleEnglish = []
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
            "Rest of duration {0} cannot be transcribed to braille.".format(music21Rest.duration)) 
        music21Rest._brailleEnglish.append("Rest {0} None".format(music21Rest.duration.type))
        return symbols['basic_exception']

    restTrans.append(simpleRest)
    music21Rest._brailleEnglish.append(u"Rest {0} {1}".format(restType, simpleRest))
    for unused_counter_dot in range(restDots):
        restTrans.append(symbols['dot'])
        music21Rest._brailleEnglish.append(u"Dot {0}".format(symbols['dot']))
        
    handleExpressions(music21Rest, restTrans)
        
    return u"".join(restTrans)

def tempoTextToBraille(music21TempoText, maxLineLength=40):
    u"""
    Takes in a :class:`~music21.tempo.TempoText` and returns its representation in braille 
    as a string in UTF-8 unicode. The tempo text is returned uncentered, and is split around
    the comma, each split returned on a separate line. The literary period required at the end
    of every tempo text expression in braille is also included.
    
    
    >>> from music21.braille import basic
    >>> print(basic.tempoTextToBraille(tempo.TempoText("Lento assai, cantante e tranquillo")))
    ⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂
    ⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲
    >>> print(basic.tempoTextToBraille(tempo.TempoText("Andante molto grazioso")))
    ⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠕⠇⠞⠕⠀⠛⠗⠁⠵⠊⠕⠎⠕⠲

    >>> print(basic.tempoTextToBraille(tempo.TempoText("Andante molto grazioso ma cantabile"), 
    ...                                    maxLineLength=20))
    ⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠕⠇⠞⠕⠀⠛⠗⠁⠵⠊⠕⠎⠕⠀⠍⠁⠀
    ⠉⠁⠝⠞⠁⠃⠊⠇⠑⠲
    """
    music21TempoText._brailleEnglish = []
    allPhrases = music21TempoText.text.split(",")
    braillePhrases = []
    for samplePhrase in allPhrases:
        allWords = samplePhrase.split()
        phraseTrans = []
        for sampleWord in allWords:
            try:
                brailleWord = wordToBraille(sampleWord)
            except BrailleBasicException as wordException:  # pragma: no cover
                environRules.warn("Tempo Text {0}: {1}".format(music21TempoText, wordException))
                music21TempoText._brailleEnglish.append("Tempo Text {0} None".format(
                                                                        music21TempoText.text))
                return symbols['basic_exception']
            
            if len(phraseTrans) + len(brailleWord) + 1 > (maxLineLength - 6):
                phraseTrans.append(u"\n")

            phraseTrans.append(brailleWord)
            phraseTrans.append(symbols['space'])
        braillePhrases.append(u"".join(phraseTrans[0:-1]))
    
    joiner = alphabet[","] + u"\n"
    brailleUnicodeText = joiner.join(braillePhrases) + alphabet["."]

    music21TempoText._brailleEnglish.append(
            u"Tempo Text {0} {1}".format(music21TempoText.text, brailleUnicodeText))
    return brailleUnicodeText

def textExpressionToBraille(music21TextExpression, precedeByWordSign=True):    
    u"""
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
    """
    music21TextExpression._brailleEnglish = []
    teWords = music21TextExpression.content
    if teWords in lookup.textExpressions:
        simpleReturn = lookup.textExpressions[teWords]
        music21TextExpression._brailleEnglish.append(
                u"Text Expression {0} {1}".format(teWords, simpleReturn))
        return simpleReturn

    # not in this basic list...
    
    allExpr = teWords.split()
    textExpressionTrans = []
    
    try:
        for expr in allExpr:
            textExpressionTrans.append(wordToBraille(expr, isTextExpression=True))
    except BrailleBasicException as wordException:  # pragma: no cover
        environRules.warn("Text Expression {0}: {1}".format(music21TextExpression, wordException))
        music21TextExpression._brailleEnglish.append("Text Expression {0} None".format(teWords))
        return symbols['basic_exception']

    brailleTextExpr = symbols['space'].join(textExpressionTrans)
    music21TextExpression._brailleEnglish.append(
        u"Text Expression {0} {1}".format(teWords, brailleTextExpr))

    if precedeByWordSign:
        brailleTextExpr = symbols['word'] + brailleTextExpr
        music21TextExpression._brailleEnglish.insert(0, u"Word {0}".format(symbols['word']))

    if len(allExpr) > 1: # put a word symbol at the end if there is more than one word:
        brailleTextExpr = brailleTextExpr + symbols['word']
        music21TextExpression._brailleEnglish.append(u"Word {0}".format(symbols['word']))

    return brailleTextExpr


def timeSigToBraille(m21TimeSignature):
    u"""
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
    """
    m21TimeSignature._brailleEnglish = []
    
    if m21TimeSignature.symbol in ('common', 'cut'):
        brailleSig = symbols[m21TimeSignature.symbol]
        m21TimeSignature._brailleEnglish.append(
                u"Time Signature {0} {1}".format(m21TimeSignature.symbol, brailleSig))
        return brailleSig
    
    try:
        timeSigTrans = [numberToBraille(m21TimeSignature.numerator), 
                        numberToBraille(m21TimeSignature.denominator, 
                                        withNumberSign=False, 
                                        lower=True)]
        brailleSig = u"".join(timeSigTrans)
        m21TimeSignature._brailleEnglish.append(u"Time Signature {0}/{1} {2}".format(
            m21TimeSignature.numerator, m21TimeSignature.denominator, brailleSig)) 
        return brailleSig
    except (BrailleBasicException, KeyError) as unused_error:  # pragma: no cover
        environRules.warn(
            "Time Signature {0} cannot be transcribed to braille.".format(m21TimeSignature))
        m21TimeSignature._brailleEnglish.append("{0} None".format(m21TimeSignature)) 
        return symbols['basic_exception']

#-------------------------------------------------------------------------------
# Helper methods

def showOctaveWithNote(previousNote, currentNote):
    """
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
    """
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

def transcribeHeading(music21KeySignature=None, 
                      music21TimeSignature=None, 
                      music21TempoText=None, 
                      music21MetronomeMark=None, 
                      maxLineLength=40):
    u"""
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
    ...         tempo.TempoText("Allegretto"),
    ...         tempo.MetronomeMark(number = 135, referent = note.Note(type='eighth'))))
    ⠀⠀⠀⠀⠀⠀⠀⠠⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠲⠀⠙⠶⠼⠁⠉⠑⠀⠼⠑⠩⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀
    >>> print(basic.transcribeHeading(key.KeySignature(-2), meter.TimeSignature('common'),
    ... tempo.TempoText("Lento assai, cantante e tranquillo"), None))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠨⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """
    if (music21KeySignature is None 
            and music21TimeSignature is None 
            and music21TempoText is None 
            and music21MetronomeMark is None):
        raise BrailleBasicException("No heading can be made.")
    # Tempo Text
    tempoTextTrans = None
    if music21TempoText is not None:
        tempoTextTrans = tempoTextToBraille(music21TempoText)
        
    if (music21KeySignature is None 
            and music21TimeSignature is None 
            and music21MetronomeMark is None):
        tempoTextLines = tempoTextTrans.splitlines()
        headingTrans = []
        for ttline in tempoTextLines:
            headingTrans.append(ttline)
        if len(tempoTextTrans) <= (maxLineLength - 6):
            headingTrans = u"".join(headingTrans)
            return headingTrans.center(maxLineLength, symbols['space'])
        else:
            for hlineindex in range(len(headingTrans)):
                headingTrans[hlineindex] = headingTrans[hlineindex].center(maxLineLength, 
                                                                           symbols['space'])
            return u"\n".join(headingTrans)
        
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
            raise BrailleBasicException("No heading can be made.")
    
    otherTransStr = u"".join(otherTrans)
    
    if tempoTextTrans is None:
        return otherTransStr.center(maxLineLength, symbols['space'])
    else:
        tempoTextLines = tempoTextTrans.splitlines()
        headingTrans = []
        for ttline in tempoTextLines:
            headingTrans.append(ttline)
        headingTrans.append(otherTransStr)
        if len(tempoTextTrans) + len(otherTransStr) + 1 <= (maxLineLength - 6):
            headingTrans = symbols['space'].join(headingTrans)
            return headingTrans.center(maxLineLength, symbols['space'])
        else:
            for hlineindex in range(len(headingTrans)):
                headingTrans[hlineindex] = headingTrans[hlineindex].center(maxLineLength, 
                                                                           symbols['space'])
            return u"\n".join(headingTrans)

def transcribeNoteFingering(sampleNoteFingering='1', upperFirstInFingering=True):
    u"""
    Takes in a note fingering, an attribute :attr:`~music21.note.Note.fingering`, and
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
    """
    fingerMarks = lookup.fingerMarks
    if isinstance(sampleNoteFingering, int):
        sampleNoteFingering = str(sampleNoteFingering)

    if len(sampleNoteFingering) == 1:
        try:
            return fingerMarks[sampleNoteFingering]
        except KeyError:  # pragma: no cover
            raise BrailleBasicException("Cannot translate note fingering: " + sampleNoteFingering)
        
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
                fingerMarkToAppend = ""
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
            raise BrailleBasicException("Cannot translate note fingering: " + sampleNoteFingering)

    return u"".join(trans)


def transcribeSignatures(music21KeySignature, music21TimeSignature, outgoingKeySig=None):
    u"""
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
    """
    if (music21TimeSignature is None 
            and (music21KeySignature is None 
                 or (music21KeySignature.sharps == 0 and outgoingKeySig is None))):
        return u""
    
    trans = []
    if music21KeySignature is not None:
        trans.append(keySigToBraille(music21KeySignature, outgoingKeySig=outgoingKeySig))
    if music21TimeSignature is not None:
        trans.append(timeSigToBraille(music21TimeSignature))
        
    return u"".join(trans)

#-------------------------------------------------------------------------------
# Translation between braille unicode and ASCII/other symbols.

def brailleUnicodeToBrailleAscii(brailleUnicode):
    r"""
    translates a braille UTF-8 unicode string into braille ASCII,
    which is the format compatible with most braille embossers.


    .. note:: The method works by corresponding braille symbols to ASCII symbols.
        The table which corresponds said values can be found
        `here <http://en.wikipedia.org/wiki/Braille_ASCII#Braille_ASCII_values>`_.
        Because of the way in which the braille symbols translate2, the resulting
        ASCII string will look like gibberish. Also, the eighth-note notes in braille
        music are one-off their corresponding letters in both ASCII and written braille.
        The written D is really a C eighth-note, the written E is really a
        D eighth note, etc.


    >>> from music21.braille import basic
    >>> basic.brailleUnicodeToBrailleAscii(u'\u2800')
    ' '
    >>> Cs8 = note.Note('C#4', quarterLength=0.5)
    >>> Cs8_braille = basic.noteToBraille(Cs8)
    >>> basic.brailleUnicodeToBrailleAscii(Cs8_braille)
    '%"D'
    >>> Eb8 = note.Note('E-4', quarterLength=0.5)
    >>> Eb8_braille = basic.noteToBraille(Eb8)
    >>> basic.brailleUnicodeToBrailleAscii(Eb8_braille)
    '<"F'
    """
    brailleLines = brailleUnicode.splitlines()
    asciiLines = []
    
    for sampleLine in brailleLines:
        allChars = []
        for char in sampleLine:
            allChars.append(ascii_chars[char])
        asciiLines.append(''.join(allChars))
        
    return '\n'.join(asciiLines)

def brailleAsciiToBrailleUnicode(brailleAscii):
    """
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
    >>> t1 = basic.brailleAsciiToBrailleUnicode(",ANDANTE ,MAESTOSO4")
    >>> t2 = basic.tempoTextToBraille(tempo.TempoText("Andante Maestoso"))
    >>> t1 == t2
    True
    """
    braille_chars = {}
    for key in ascii_chars:
        braille_chars[ascii_chars[key]] = key
        
    asciiLines = brailleAscii.splitlines()
    brailleLines = []
    
    for sampleLine in asciiLines:
        allChars = []
        for char in sampleLine:
            allChars.append(braille_chars[char.upper()])
        brailleLines.append(u''.join(allChars))
    
    return u'\n'.join(brailleLines)

def brailleUnicodeToSymbols(brailleUnicode, filledSymbol=u'o', emptySymbol=u'\u00B7'):
    u"""
    translates a braille unicode string into symbols (unicode) -- for debugging.
    
    >>> print(braille.basic.brailleUnicodeToSymbols(u'⠜'))
    ·o
    ·o
    o·    
    """
    symbolTrans = {'00': u'{symbol1}{symbol2}'.format(symbol1=emptySymbol, symbol2=emptySymbol),
                   '01': u'{symbol1}{symbol2}'.format(symbol1=emptySymbol, symbol2=filledSymbol),
                   '10': u'{symbol1}{symbol2}'.format(symbol1=filledSymbol, symbol2=emptySymbol),
                   '11': u'{symbol1}{symbol2}'.format(symbol1=filledSymbol, symbol2=filledSymbol)}
    
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
        binaryLines.append(u'  '.join(binaryLine1))
        binaryLines.append(u'  '.join(binaryLine2))
        binaryLines.append(u'  '.join(binaryLine3))
        binaryLines.append(u'')
        
    return u'\n'.join(binaryLines[0:-1])

def yieldDots(brailleCharacter):
    u'''
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
        if dots == '10' or dots == '11':
            yield symbols['dot']
            
#-------------------------------------------------------------------------------
# Transcription of words and numbers.

def wordToBraille(sampleWord, isTextExpression=False):
    u"""
    Transcribes a word to UTF-8 braille.

    >>> from music21.braille import basic
    >>> print(basic.wordToBraille('Andante'))
    ⠠⠁⠝⠙⠁⠝⠞⠑
    >>> print(basic.wordToBraille('Fagott'))
    ⠠⠋⠁⠛⠕⠞⠞
    """
    wordTrans = []
    
    if isTextExpression:
        for letter in sampleWord:
            if letter.isupper():
                wordTrans.append(alphabet[letter.lower()])
            elif letter == '.':
                wordTrans.append(symbols['dot'])
            else:
                try:
                    wordTrans.append(alphabet[letter])
                except KeyError:
                    raise BrailleBasicException(
                        "Character '{0}' in Text Expression '{1}' ".format(letter, sampleWord) +
                        "cannot be transcribed to braille.")
        return u"".join(wordTrans)
    
    for letter in sampleWord:
        try:
            if letter.isupper():
                wordTrans.append(symbols['uppercase'] + alphabet[letter.lower()])
            else:
                wordTrans.append(alphabet[letter])
        except KeyError:  # pragma: no cover
            raise BrailleBasicException(
                "Character '{0}' in word '{1}' cannot be transcribed to braille.".format(
                                                                    letter, sampleWord))
            
    return u"".join(wordTrans)

def numberToBraille(sampleNumber, withNumberSign=True, lower=False):
    u"""
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
    """
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
                "Digit '{0}' in number '{1}' cannot be transcribed to braille.".format(
                                                                    digit, sampleNumber))
    return u"".join(numberTrans)

#-------------------------------------------------------------------------------

class BrailleBasicException(exceptions21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #, verbose=True)

#------------------------------------------------------------------------------
# eof
