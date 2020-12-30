# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         volpiano.py
# Purpose:      music21 classes for converting to and from volpiano
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
The Volpiano font is a specialized font for encoding Western Plainchant
easily with immediate visual feedback (see the CANTUS database).

This module parses chants encoded in Volpiano and can generate Volpiano
from any music21 Stream.

This module will move to a medren package hopefully by v.7
'''
import enum
import unittest

from music21 import bar
from music21 import base
from music21 import clef
from music21 import environment
from music21 import exceptions21
from music21 import layout
from music21 import note
from music21 import pitch
from music21 import spanner
from music21 import stream

environLocal = environment.Environment('volpiano.py')


class VolpianoException(exceptions21.Music21Exception):
    pass


# JetBrains does not understand this form of Enum
# noinspection PyArgumentList
ErrorLevel = enum.Enum('ErrorLevel', 'WARN LOG')


class Neume(spanner.Spanner):
    '''
    A spanner that represents a Neume.  No name of the neume, just that it is a Neume.
    '''


class LineBreak(base.Music21Object):
    '''
    Indicates that the line breaks at this point in the manuscript.

    Denoted by one 7.
    '''
    pass


class PageBreak(base.Music21Object):
    '''
    Indicates that the page breaks at this point in the manuscript

    Denoted by two 7s.
    '''
    pass


class ColumnBreak(base.Music21Object):
    '''
    Indicates that the page breaks at this point in the manuscript

    Denoted by three 7s.
    '''
    pass


classByNumBreakTokens = [None, LineBreak, PageBreak, ColumnBreak]
classByNumBreakTokensLayout = [None, layout.SystemLayout, layout.PageLayout, ColumnBreak]

normalPitches = '9abcdefghjklmnopqrs'
liquescentPitches = ')ABCDEFGHJKLMNOPQRS'

eflatTokens = 'wx'
bflatTokens = 'iyz'
flatTokens = eflatTokens + bflatTokens
naturalTokens = flatTokens.upper()
accidentalTokens = flatTokens + naturalTokens


def toPart(volpianoText, *, breaksToLayout=False):
    '''
    Returns a music21 Part from volpiano text.

    >>> veniSancti = volpiano.toPart('1---c--d---f--d---ed--c--d---f'
    ...                              + '---g--h--j---hgf--g--h---')
    >>> veniSancti.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note F>
        {3.0} <music21.note.Note D>
        {4.0} <music21.note.Note E>
        {5.0} <music21.note.Note D>
        {6.0} <music21.volpiano.Neume <music21.note.Note E><music21.note.Note D>>
        {6.0} <music21.note.Note C>
        {7.0} <music21.note.Note D>
        {8.0} <music21.note.Note F>
        {9.0} <music21.note.Note G>
        {10.0} <music21.note.Note A>
        {11.0} <music21.note.Note B>
        {12.0} <music21.note.Note A>
        {13.0} <music21.note.Note G>
        {14.0} <music21.note.Note F>
        {15.0} <music21.volpiano.Neume <music21.note.Note A><music21.note.Note G>>
        {15.0} <music21.note.Note G>
        {16.0} <music21.note.Note A>

    Clefs!

    >>> clefTest = volpiano.toPart('1---c--2---c')
    >>> clefTest.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note C>
        {1.0} <music21.clef.BassClef>
        {1.0} <music21.note.Note E>
    >>> for n in clefTest.recurse().notes:
    ...     n.nameWithOctave
    'C4'
    'E2'

    Flats and Naturals:

    >>> accTest = volpiano.toPart('1---e--we--e--We--e')
    >>> [n.name for n in accTest.recurse().notes]
    ['E', 'E-', 'E-', 'E', 'E']

    Breaks and barlines

    >>> breakTest = volpiano.toPart('1---e-7-e-77-e-777-e-3-e-4')
    >>> breakTest.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note E>
        {1.0} <music21.volpiano.LineBreak object at 0x105250fd0>
        {1.0} <music21.note.Note E>
        {2.0} <music21.volpiano.PageBreak object at 0x105262128>
        {2.0} <music21.note.Note E>
        {3.0} <music21.volpiano.ColumnBreak object at 0x105262240>
        {3.0} <music21.note.Note E>
        {4.0} <music21.bar.Barline type=regular>
    {4.0} <music21.stream.Measure 0 offset=4.0>
        {0.0} <music21.note.Note E>
        {1.0} <music21.bar.Barline type=double>


    As layout objects using breaksToLayout=True

    >>> breakTest = volpiano.toPart('1---e-7-e-77-e-777-e-3-e-4', breaksToLayout=True)
    >>> breakTest.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note E>
        {1.0} <music21.layout.SystemLayout>
        {1.0} <music21.note.Note E>
        {2.0} <music21.layout.PageLayout>
        {2.0} <music21.note.Note E>
        {3.0} <music21.volpiano.ColumnBreak object at 0x105262240>
        {3.0} <music21.note.Note E>
        {4.0} <music21.bar.Barline type=regular>
    {4.0} <music21.stream.Measure 0 offset=4.0>
        {0.0} <music21.note.Note E>
        {1.0} <music21.bar.Barline type=double>


    Liquescence test:

    >>> breakTest = volpiano.toPart('1---e-E-')
    >>> breakTest.recurse().notes[0].editorial.liquescence
    False
    >>> breakTest.recurse().notes[0].notehead
    'normal'
    >>> breakTest.recurse().notes[1].editorial.liquescence
    True
    >>> breakTest.recurse().notes[1].notehead
    'x'

    Changed in v5.7 -- corrected spelling of liquescence.
    '''
    p = stream.Part()
    m = stream.Measure()

    currentMeasure = m
    currentNeumeSpanner = None
    noteThatWouldGoInSpanner = None
    lastClef = clef.TrebleClef()
    continuousNumberOfBreakTokens = 0


    bIsFlat = False
    eIsFlat = False

    for token in volpianoText:
        if token == '7':
            continuousNumberOfBreakTokens += 1
            continue
        elif continuousNumberOfBreakTokens > 0:
            if not breaksToLayout:  # default
                breakClass = classByNumBreakTokens[continuousNumberOfBreakTokens]
                breakToken = breakClass()  # pylint: disable=not-callable
            else:
                breakClass = classByNumBreakTokensLayout[continuousNumberOfBreakTokens]
                if continuousNumberOfBreakTokens < 3:
                    breakToken = breakClass(isNew=True)  # pylint: disable=not-callable
                else:
                    breakToken = breakClass()  # pylint: disable=not-callable

            currentMeasure.append(breakToken)

        continuousNumberOfBreakTokens = 0

        if token == '-':
            noteThatWouldGoInSpanner = None
            if currentNeumeSpanner:
                currentMeasure.append(currentNeumeSpanner)
                currentNeumeSpanner = None
            continue

        if token in '1234':
            noteThatWouldGoInSpanner = None
            currentNeumeSpanner = None

        if token in '12':
            if token == '1':
                c = clef.TrebleClef()
            else:
                c = clef.BassClef()

            lastClef = c
            m.append(c)

        elif token in '34':
            bl = bar.Barline()
            if token == '4':
                bl.type = 'double'
            m.rightBarline = bl
            p.append(m)
            m = stream.Measure()

        elif token in normalPitches or token in liquescentPitches:
            n = note.Note()
            n.stemDirection = 'noStem'

            if token in normalPitches:
                distanceFromLowestLine = normalPitches.index(token) - 5
                n.editorial.liquescence = False
            else:
                distanceFromLowestLine = liquescentPitches.index(token) - 5
                n.notehead = 'x'
                n.editorial.liquescence = True

            clefLowestLine = lastClef.lowestLine
            diatonicNoteNum = clefLowestLine + distanceFromLowestLine

            n.pitch.diatonicNoteNum = diatonicNoteNum
            if n.pitch.step == 'B' and bIsFlat:
                n.pitch.accidental = pitch.Accidental('flat')
            elif n.pitch.step == 'E' and eIsFlat:
                n.pitch.accidental = pitch.Accidental('flat')

            m.append(n)

            if noteThatWouldGoInSpanner is not None:
                currentNeumeSpanner = Neume([noteThatWouldGoInSpanner, n])
                noteThatWouldGoInSpanner = None
            else:
                noteThatWouldGoInSpanner = n

        elif token in accidentalTokens:
            if token.lower() in eflatTokens and token in naturalTokens:
                eIsFlat = False
            elif token.lower() in bflatTokens and token in naturalTokens:
                bIsFlat = False
            elif token.lower() in eflatTokens and token in flatTokens:
                eIsFlat = True
            elif token.lower() in bflatTokens and token in flatTokens:
                bIsFlat = True
            else:  # pragma: no cover
                raise VolpianoException(
                    'Unknown accidental: ' + token + ': Should not happen')


    if continuousNumberOfBreakTokens > 0:
        breakClass = classByNumBreakTokens[continuousNumberOfBreakTokens]
        breakToken = breakClass()  # pylint: disable=not-callable
        currentMeasure.append(breakToken)

    if m:
        p.append(m)

    return p



def fromStream(s, *, layoutToBreaks=False):
    '''
    Convert a Stream to Volpiano.

    These tests show how the same input converts back out:

    >>> volpianoInput = '1--c--d---f--d---ed--c--d---f---g--h--j---hgf--g--h---'
    >>> veniSancti = volpiano.toPart(volpianoInput)
    >>> volpiano.fromStream(veniSancti)
    '1---c-d-f-d-ed-c-d-f-g-h-j-hg-f-g-h-'

    >>> breakTest = volpiano.toPart('1---e-E--')
    >>> volpiano.fromStream(breakTest)
    '1---e-E-'

    >>> accTest = volpiano.toPart('1---e--we--e--We--e')
    >>> volpiano.fromStream(accTest)
    '1---e-we-e-We-e-'
    '''

    volpianoTokens = []

    def error(innerEl, errorLevel=ErrorLevel.LOG):
        msg = f'Could not convert token {innerEl!r} to Volpiano.'
        if errorLevel == ErrorLevel.WARN:
            environLocal.warn(msg + ' this can lead to incorrect data.')
        else:
            environLocal.printDebug(msg)

    def ap(tokens):
        for t in tokens:
            volpianoTokens.append(t)

    def popHyphens():
        while volpianoTokens and volpianoTokens[-1] == '-':
            volpianoTokens.pop()


    distToAccidental = {
        -3: 'y',
        0: 'w',
        4: 'i',
        7: 'x',
        11: 'z',
    }

    def setAccFromPitch(dist, setNatural=False):
        if dist not in distToAccidental:
            error(f'{dist} above lowest line', ErrorLevel.WARN)
            return
        accidentalToken = distToAccidental[dist]
        if setNatural:
            accidentalToken = accidentalToken.upper()
        ap(accidentalToken)

    lastClef = clef.TrebleClef()

    bIsFlat = False
    eIsFlat = False

    for el in s.recurse():
        elClasses = el.classes
        if 'Clef' in elClasses:
            lastClef = el
            if 'TrebleClef' in elClasses:
                ap('1---')
            elif 'BassClef' in elClasses:
                ap('2---')
            else:
                error(el, ErrorLevel.WARN)

        elif 'Barline' in elClasses:
            if el.type in ('double', 'final'):
                ap('---4')
            else:
                ap('---3')

        elif 'Note' in elClasses:
            n = el
            p = n.pitch
            dnn = p.diatonicNoteNum
            distanceFromLowestLine = dnn - lastClef.lowestLine
            indexInPitchString = distanceFromLowestLine + 5
            if indexInPitchString < 0 or indexInPitchString >= len(normalPitches):
                error(n, ErrorLevel.WARN)
                continue

            if n.notehead == 'x' or (n.hasEditorialInformation
                                      and 'liquescence' in n.editorial
                                      and n.editorial.liquescence):
                tokenName = liquescentPitches[indexInPitchString]
            else:
                tokenName = normalPitches[indexInPitchString]

            if p.accidental is not None and p.accidental.alter != 0:
                if p.step not in ('B', 'E'):
                    error(el, ErrorLevel.WARN)
                    ap(tokenName)
                    continue
                elif p.accidental.alter != -1:
                    error(el, ErrorLevel.WARN)
                    ap(tokenName)
                    continue

                if p.step == 'B' and not bIsFlat:
                    setAccFromPitch(distanceFromLowestLine)
                    bIsFlat = True
                elif p.step == 'E' and not eIsFlat:
                    setAccFromPitch(distanceFromLowestLine)
                    eIsFlat = True
            elif p.name == 'B' and bIsFlat:
                setAccFromPitch(distanceFromLowestLine, setNatural=True)
                bIsFlat = False
            elif p.name == 'E' and eIsFlat:
                setAccFromPitch(distanceFromLowestLine, setNatural=True)
                eIsFlat = False
            ap(tokenName)

            neumeSpanner = n.getSpannerSites('Neume')
            if neumeSpanner and n is not neumeSpanner[0].getLast():
                pass
            elif not n.lyric:
                ap('-')
            else:
                lyricObject = n.lyrics[0]
                syl = lyricObject.syllabic
                if syl in ('single', 'end'):
                    ap('---')
                else:
                    ap('--')

        elif 'SystemLayout' in elClasses and layoutToBreaks:
            popHyphens()
            ap('7---')
        elif 'PageLayout' in elClasses and layoutToBreaks:
            popHyphens()
            ap('77---')
        elif 'LineBreak' in elClasses:
            popHyphens()
            ap('7---')
        elif 'PageBreak' in elClasses:
            popHyphens()
            ap('77---')
        elif 'ColumnBreak' in elClasses:
            popHyphens()
            ap('777---')
        else:
            error(el, ErrorLevel.LOG)

    return ''.join(volpianoTokens)



class Test(unittest.TestCase):
    pass

    def testNoteNames(self):
        pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test, 'importPlusRelative')
