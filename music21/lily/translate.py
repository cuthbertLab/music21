# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         lily/translate.py
# Purpose:      music21 classes for translating to Lilypond
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2007-2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
music21 translates to Lilypond format and if Lilypond is installed on the
local computer, can automatically generate .pdf, .png, and .svg versions
of musical files using Lilypond.
'''
import os
import pathlib
import re
import subprocess
import sys
import unittest

from collections import OrderedDict
from importlib.util import find_spec

from music21 import common
from music21 import corpus
from music21 import duration
from music21 import environment
from music21 import exceptions21
from music21 import variant
from music21 import note
from music21.converter.subConverters import SubConverter
from music21.lily import lilyObjects as lyo

_MOD = 'lily.translate'
environLocal = environment.Environment(_MOD)

try:
    if find_spec('PIL.Image') and find_spec('PIL.ImageOps'):
        noPIL = False
    else:  # pragma: no cover
        noPIL = True
except (ModuleNotFoundError, AttributeError):  # pragma: no cover
    # Python 3.6 raises AttributeError here, remove when 3.7 is minimum.
    noPIL = True

del find_spec

# TODO: speed up tests everywhere! move these to music21 base...

class _sharedCorpusTestObject:
    sharedCache = {}


sharedCacheObject = _sharedCorpusTestObject()


def _getCachedCorpusFile(keyName):
    # return corpus.parse(keyName)
    if keyName not in sharedCacheObject.sharedCache:
        sharedCacheObject.sharedCache[keyName] = corpus.parse(keyName)
    return sharedCacheObject.sharedCache[keyName]

# b.parts[0].measure(4)[2].color = 'blue'#.rightBarline = 'double'


def makeLettersOnlyId(inputString):
    # noinspection SpellCheckingInspection
    r'''
        Takes an id and makes it purely letters by substituting
        letters for all other characters.


        >>> print(lily.translate.makeLettersOnlyId('rainbow123@@dfas'))
        rainbowxyzmmdfas
        '''
    inputString = str(inputString)
    returnString = ''
    for c in inputString:
        if not c.isalpha():
            c = chr(ord(c) % 26 + 97)
        returnString += c

    return returnString

# ------------------------------------------------------------------------------


class LilypondConverter:
    fictaDef = (
        r'''
    ficta = #(define-music-function (parser location) () #{ \once \set suggestAccidentals = ##t #})
    '''.lstrip())
    colorDef = (
        r'''
    color = #(define-music-function (parser location color) (string?) #{
        \once \override NoteHead #'color = #(x11-color color)
        \once \override Stem #'color = #(x11-color color)
        \once \override Rest #'color = #(x11-color color)
        \once \override Beam #'color = #(x11-color color)
     #})
    '''.lstrip())
    simplePaperDefinitionScm = r'''
    \paper { #(define dump-extents #t)
    indent = 0\mm
    force-assignment = #""
    oddFooterMarkup=##f
    oddHeaderMarkup=##f
    bookTitleMarkup=##f
    }
    '''.lstrip()
    transparencyStartScheme = r'''
     \override Rest #'transparent  = ##t
     \override Dots #'transparent  = ##t
     '''.lstrip()
    transparencyStopScheme = r'''
     \revert Rest #'transparent
     \revert Dots #'transparent
     '''.lstrip()
    bookHeader = r'''
    \include "lilypond-book-preamble.ly"
    '''.lstrip()

    accidentalConvert = {'double-sharp': 'isis',
                         'double-flat': 'eses',
                         'one-and-a-half-sharp': 'isih',
                         'one-and-a-half-flat': 'eseh',
                         'sharp': 'is',
                         'flat': 'es',
                         'half-sharp': 'ih',
                         'half-flat': 'eh',
                         }

    barlineDict = {'regular': '|',
                   'dotted': ':',
                   'dashed': 'dashed',
                   'heavy': '.',  # ??
                   'double': '||',
                   'final': '|.',
                   'heavy-light': '.|',
                   'heavy-heavy': '.|.',
                   'start-repeat': '|:',
                   'end-repeat': ':|',
                   # no music21 support for |.| lightHeavyLight yet
                   'tick': '\'',
                   # 'short': '',  # no lilypond support??
                   'none': '',
                   }

    def __init__(self):
        self.majorVersion = '1'
        self.minorVersion = '0'
        self.versionString = '1.0'
        self.backend = 'ps'
        self.versionScheme = ''
        self.headerScheme = ''
        self.backendString = '--backend='

        self.topLevelObject = lyo.LyLilypondTop()
        self.setupTools()
        self.context = self.topLevelObject
        self.storedContexts = []
        self.doNotOutput = []
        self.currentMeasure = None
        self.addedVariants = []
        self.variantColors = ['blue', 'red', 'purple', 'green', 'orange', 'yellow', 'grey']
        self.coloredVariants = False
        self.variantMode = False
        self.LILYEXEC = None
        self.tempName = None
        self.inWord = None

    def findLilyExec(self):
        lpEnvironment = environLocal['lilypondPath']
        if lpEnvironment is not None and lpEnvironment.exists():
            LILYEXEC = str(lpEnvironment)  # pragma: no cover
        else:  # pragma: no cover
            platform = common.getPlatform()
            if platform == 'darwin':
                LILYEXEC = '/Applications/Lilypond.app/Contents/Resources/bin/lilypond'
                if not os.path.exists(LILYEXEC):
                    LILYEXEC = 'lilypond'
            elif platform == 'win' and os.path.exists('c:/Program Files (x86)'):
                LILYEXEC = r'c:/Program\ Files\ (x86)/lilypond/usr/bin/lilypond'
                if not os.path.exists(LILYEXEC) and not os.path.exists(LILYEXEC + '.exe'):
                    LILYEXEC = 'lilypond'
            elif platform == 'win':
                LILYEXEC = r'c:/Program\ Files/lilypond/usr/bin/lilypond'
                if not os.path.exists(LILYEXEC) and not os.path.exists(LILYEXEC + '.exe'):
                    LILYEXEC = 'lilypond'
            else:
                LILYEXEC = 'lilypond'

        self.LILYEXEC = LILYEXEC
        return LILYEXEC

    def setupTools(self):
        LILYEXEC = self.findLilyExec()
        command = [LILYEXEC, '--version']
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        except OSError:  # pragma: no cover
            raise LilyTranslateException(
                'Cannot find a copy of Lilypond installed on your system. '
                + 'Please be sure it is installed. And that your '
                + "environment.UserSettings()['lilypondPath'] is set to find it.")
        stdout, unused = proc.communicate()
        stdout = stdout.decode(encoding='utf-8')
        versionString = stdout.split()[2]
        versionPieces = versionString.split('.')

        self.majorVersion = versionPieces[0]
        self.minorVersion = versionPieces[1]

        self.versionString = (self.topLevelObject.backslash
                              + 'version '
                              + self.topLevelObject.quoteString(str(self.majorVersion)
                                                                + '.'
                                                                + str(self.minorVersion)))
        self.versionScheme = lyo.LyEmbeddedScm(self.versionString)
        self.headerScheme = lyo.LyEmbeddedScm(self.bookHeader)

        self.backend = 'ps'

        if int(self.majorVersion) >= 2:
            if int(self.minorVersion) >= 11:
                self.backendString = '-dbackend='
            else:  # pragma: no cover
                self.backendString = '--backend='
        else:  # pragma: no cover
            self.backendString = '--backend='
        # I had a note that said 2.12 and > should use
        #    'self.backendString = '--formats=' ' but doesn't seem true

    def newContext(self, newContext):
        self.storedContexts.append(self.context)
        self.context = newContext

    def restoreContext(self):
        try:
            self.context = self.storedContexts.pop()
        except IndexError:  # pragma: no cover
            self.context = self.topLevelObject

    # ----------- Set a complete Lilypond Tree from a music21 object ----------#

    def textFromMusic21Object(self, m21ObjectIn):
        r'''
        get a proper lilypond text file for writing from a music21 object


        >>> n = note.Note()
        >>> print(lily.translate.LilypondConverter().textFromMusic21Object(n))
        \version "2..."
        \include "lilypond-book-preamble.ly"
        color = #(define-music-function (parser location color) (string?) #{
                \once \override NoteHead #'color = #(x11-color color)
                \once \override Stem #'color = #(x11-color color)
                \once \override Rest #'color = #(x11-color color)
                \once \override Beam #'color = #(x11-color color)
             #})
        \header { }
        \score  {
              << \new Staff  = ... { c' 4
                      }
                >>
          }
        \paper { }
        ...
        '''
        self.loadFromMusic21Object(m21ObjectIn)
        s = str(self.topLevelObject)
        s = re.sub(r'\s*\n\s*\n', '\n', s).strip()
        return s

    def loadFromMusic21Object(self, m21ObjectIn):
        r'''
        Create a Lilypond object hierarchy in self.topLevelObject from an
        arbitrary music21 object.

        TODO: make lilypond automatically run makeNotation.makeTupletBrackets(s)
        TODO: Add tests...
        '''
        from music21 import stream
        c = m21ObjectIn.classes
        if 'Stream' in c:
            if m21ObjectIn.recurse().variants:
                # has variants so we need to make a deepcopy...
                m21ObjectIn = variant.makeAllVariantsReplacements(m21ObjectIn, recurse=True)
                m21ObjectIn.makeVariantBlocks()

        if ('Stream' not in c) or ('Measure' in c) or ('Voice' in c):
            scoreObj = stream.Score()
            partObj = stream.Part()
            # no need for measures or voices...
            partObj.insert(0, m21ObjectIn)
            scoreObj.insert(0, partObj)
            self.loadObjectFromScore(scoreObj, makeNotation=False)
        elif 'Part' in c:
            scoreObj = stream.Score()
            scoreObj.insert(0, m21ObjectIn)
            self.loadObjectFromScore(scoreObj, makeNotation=False)
        elif 'Score' in c:
            self.loadObjectFromScore(m21ObjectIn, makeNotation=False)
        elif 'Opus' in c:
            self.loadObjectFromOpus(m21ObjectIn, makeNotation=False)
        else:  # treat as part...
            scoreObj = stream.Score()
            scoreObj.insert(0, m21ObjectIn)
            self.loadObjectFromScore(scoreObj, makeNotation=False)
            # raise LilyTranslateException('Unknown stream type %s.' % (m21ObjectIn.__class__))

    def loadObjectFromOpus(self, opusIn=None, makeNotation=True):
        r'''
        creates a filled topLevelObject (lily.lilyObjects.LyLilypondTop)
        whose string representation accurately reflects all the Score objects
        in this Opus object.


        >>> #_DOCS_SHOW fifeOpus = corpus.parse('miscFolk/americanfifeopus.abc')
        >>> #_DOCS_SHOW lpc = lily.translate.LilypondConverter()
        >>> #_DOCS_SHOW lpc.loadObjectFromOpus(fifeOpus, makeNotation=False)
        >>> #_DOCS_SHOW lpc.showPDF()
        '''
        contents = []
        lpVersionScheme = self.versionScheme
        lpHeaderScheme = self.headerScheme
        lpColorScheme = lyo.LyEmbeddedScm(self.colorDef)
        contents.append(lpVersionScheme)
        contents.append(lpHeaderScheme)
        contents.append(lpColorScheme)

        for thisScore in opusIn.scores:
            if makeNotation is True:
                thisScore = thisScore.makeNotation(inPlace=False)

            lpHeader = lyo.LyLilypondHeader()
            lpScoreBlock = self.lyScoreBlockFromScore(thisScore)
            if thisScore.metadata is not None:
                self.setHeaderFromMetadata(thisScore.metadata, lpHeader=lpHeader)

            contents.append(lpHeader)
            contents.append(lpScoreBlock)

        lpOutputDefHead = lyo.LyOutputDefHead(defType='paper')
        lpOutputDefBody = lyo.LyOutputDefBody(outputDefHead=lpOutputDefHead)
        lpOutputDef = lyo.LyOutputDef(outputDefBody=lpOutputDefBody)
        contents.append(lpOutputDef)

        lpLayout = lyo.LyLayout()

        contents.append(lpLayout)

        self.context.contents = contents

    def loadObjectFromScore(self, scoreIn=None, makeNotation=True):
        r'''

        creates a filled topLevelObject (lily.lilyObjects.LyLilypondTop)
        whose string representation accurately reflects this Score object.


        >>> lpc = lily.translate.LilypondConverter()
        >>> #_DOCS_SHOW b = corpus.parse('bach/bwv66.6')
        >>> b = lily.translate._getCachedCorpusFile('bach/bwv66.6') #_DOCS_HIDE
        >>> lpc.loadObjectFromScore(b)
        '''
        if makeNotation is True:
            scoreIn = scoreIn.makeNotation(inPlace=False)

        lpVersionScheme = self.versionScheme
        lpHeaderScheme = self.headerScheme
        lpColorScheme = lyo.LyEmbeddedScm(self.colorDef)
        lpHeader = lyo.LyLilypondHeader()

        # here's the heavy work...
        lpScoreBlock = self.lyScoreBlockFromScore(scoreIn)

        lpOutputDefHead = lyo.LyOutputDefHead(defType='paper')
        lpOutputDefBody = lyo.LyOutputDefBody(outputDefHead=lpOutputDefHead)
        lpOutputDef = lyo.LyOutputDef(outputDefBody=lpOutputDefBody)
        lpLayout = lyo.LyLayout()
        contents = [lpVersionScheme, lpHeaderScheme, lpColorScheme,
                    lpHeader, lpScoreBlock, lpOutputDef, lpLayout]

        if scoreIn.metadata is not None:
            self.setHeaderFromMetadata(scoreIn.metadata, lpHeader=lpHeader)

        self.context.contents = contents

    # ------ return Lily objects or append to the current context -----------#
    def lyScoreBlockFromScore(self, scoreIn):

        lpCompositeMusic = lyo.LyCompositeMusic()
        self.newContext(lpCompositeMusic)

        # Also get the variants, and the total number of measures here and make start each
        # staff context with { \stopStaff s1*n} where n is the number of measures.
        if hasattr(scoreIn, 'parts') and scoreIn.iter.parts:  # or has variants
            if scoreIn.recurse().variants:
                lpPartsAndOssiaInit = self.lyPartsAndOssiaInitFromScore(scoreIn)
                lpGroupedMusicList = self.lyGroupedMusicListFromScoreWithParts(
                    scoreIn,
                    scoreInit=lpPartsAndOssiaInit)
            else:
                lpGroupedMusicList = self.lyGroupedMusicListFromScoreWithParts(scoreIn)
            lpCompositeMusic.groupedMusicList = lpGroupedMusicList
        else:
            # treat as a part...
            lpPrefixCompositeMusic = self.lyPrefixCompositeMusicFromStream(scoreIn)
            lpCompositeMusic.prefixCompositeMusic = lpPrefixCompositeMusic

        lpMusic = lyo.LyMusic(compositeMusic=lpCompositeMusic)
        lpScoreBody = lyo.LyScoreBody(music=lpMusic)
        lpScoreBlock = lyo.LyScoreBlock(scoreBody=lpScoreBody)
        self.restoreContext()

        return lpScoreBlock

    def lyPartsAndOssiaInitFromScore(self, scoreIn):
        r'''
        Takes in a score and returns a block that starts each part context and variant context
        with an identifier and {\stopStaff s1*n} (or s, whatever is needed for the duration)
        where n is the number of measures in the score.


        >>> import copy

        Set up score:

        >>> s = stream.Score()
        >>> p1,p2 = stream.Part(), stream.Part()
        >>> p1.insert(0, meter.TimeSignature('4/4'))
        >>> p2.insert(0, meter.TimeSignature('4/4'))
        >>> p1.append(variant.Variant(name='london'))
        >>> p2.append(variant.Variant(name='london'))
        >>> p1.append(variant.Variant(name='rome'))
        >>> p2.append(variant.Variant(name='rome'))
        >>> for i in range(4):
        ...    m = stream.Measure()
        ...    n = note.Note('D4', type='whole')
        ...    m.append(n)
        ...    p1.append(m)
        ...    p2.append(copy.deepcopy(m))
        >>> p1.id = 'pa'
        >>> p2.id = 'pb'
        >>> s.append(p1)
        >>> s.append(p2)

        Run method

        >>> lpc = lily.translate.LilypondConverter()
        >>> print(lpc.lyPartsAndOssiaInitFromScore(s))
        \new Staff  = pa { \stopStaff s1 s1 s1 s1 }
        \new Staff  = londonpa
                    \with {
                          \remove "Time_signature_engraver"
                          alignAboveContext = #"pa"
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                          \override OctavateEight #'transparent = ##t
                          \consists "Default_bar_line_engraver"
                        }
                 { \stopStaff s1 s1 s1 s1 }
        \new Staff  = romepa
                    \with {
                          \remove "Time_signature_engraver"
                          alignAboveContext = #"pa"
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                          \override OctavateEight #'transparent = ##t
                          \consists "Default_bar_line_engraver"
                        }
                 { \stopStaff s1 s1 s1 s1 }
        \new Staff  = pb { \stopStaff s1 s1 s1 s1 }
        \new Staff  = londonpb
                    \with {
                          \remove "Time_signature_engraver"
                          alignAboveContext = #"pb...
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                          \override OctavateEight #'transparent = ##t
                          \consists "Default_bar_line_engraver"
                        }
                 { \stopStaff s1 s1 s1 s1 }
        \new Staff  = romepb
                    \with {
                          \remove "Time_signature_engraver"
                          alignAboveContext = #"pb...
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                          \override OctavateEight #'transparent = ##t
                          \consists "Default_bar_line_engraver"
                        }
                 { \stopStaff s1 s1 s1 s1 }
        '''
        lpMusicList = lyo.LyMusicList()

        musicList = []
        lpMusic = r'{ \stopStaff %s}'

        for p in scoreIn.parts:
            partIdText = makeLettersOnlyId(p.id)
            partId = lyo.LyOptionalId(partIdText)
            spacerDuration = self.getLySpacersFromStream(p)
            lpPrefixCompositeMusicPart = lyo.LyPrefixCompositeMusic(type='new',
                                                                    optionalId=partId,
                                                                    simpleString='Staff',
                                                                    music=lpMusic % spacerDuration)
            musicList.append(lpPrefixCompositeMusicPart)

            variantsAddedForPart = []
            for v in p.variants:
                variantName = v.groups[0]
                if variantName not in variantsAddedForPart:
                    self.addedVariants.append(variantName)
                    variantsAddedForPart.append(variantName)
                    variantId = lyo.LyOptionalId(makeLettersOnlyId(variantName) + partIdText)
                    lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(
                        type='new',
                        optionalId=variantId,
                        simpleString='Staff',
                        music=lpMusic % spacerDuration
                    )

                    contextModList = [r'\remove "Time_signature_engraver"',
                                      fr'alignAboveContext = #"{partIdText}"',
                                      r'fontSize = #-3',
                                      r"\override StaffSymbol #'staff-space = #(magstep -3)",
                                      r"\override StaffSymbol #'thickness = #(magstep -3)",
                                      r"\override TupletBracket #'bracket-visibility = ##f",
                                      r"\override TupletNumber #'stencil = ##f",
                                      r"\override Clef #'transparent = ##t",
                                      r"\override OctavateEight #'transparent = ##t",
                                      r'\consists "Default_bar_line_engraver"',
                                      ]
                    optionalContextMod = lyo.LyContextModification(contextModList)
                    lpPrefixCompositeMusicVariant.optionalContextMod = optionalContextMod
                    musicList.append(lpPrefixCompositeMusicVariant)

        lpMusicList.contents = musicList

        return lpMusicList

    def getLySpacersFromStream(self, streamIn, measuresOnly=True):
        # noinspection PyShadowingNames
        r'''
        Creates a series of Spacer objects for the measures in a Stream Part.


        >>> m1 = stream.Measure(converter.parse('tinynotation: 3/4 a2.'))
        >>> m2 = stream.Measure(converter.parse('tinynotation: 3/4 b2.'))
        >>> m3 = stream.Measure(converter.parse('tinynotation: 4/4 a1'))
        >>> m4 = stream.Measure(converter.parse('tinynotation: 4/4 b1'))
        >>> m5 = stream.Measure(converter.parse('tinynotation: 4/4 c1'))
        >>> m6 = stream.Measure(converter.parse('tinynotation: 5/4 a4 b1'))
        >>> streamIn = stream.Stream([m1, m2, m3, m4, m5, m6])
        >>> lpc = lily.translate.LilypondConverter()
        >>> print(lpc.getLySpacersFromStream(streamIn))
        s2. s2. s1 s1 s1 s1 s4

        TODO: Low-priority... rare, but possible: tuplet time signatures (3/10)...
        '''

        returnString = ''
        # mostRecentDur = ''
        # recentDurCount = 0
        for el in streamIn:
            if 'Measure' not in el.classes:
                continue
            if el.duration.quarterLength == 0.0:
                continue

            # noinspection PyBroadException
            try:
                dur = str(self.lyMultipliedDurationFromDuration(el.duration))
                returnString = returnString + 's' + dur
            # general exception is the only way to catch str exceptions
            except:  # pylint: disable=bare-except
                for c in el.duration.components:
                    dur = str(self.lyMultipliedDurationFromDuration(c))
                    returnString = returnString + 's' + dur
            # if dur == mostRecentDur:
            #    recentDurCount += 1
            # else:
            #    mostRecentDur = dur
            #    recentDurCount = 0

        # if recentDurCount != 0:
        #    returnString = returnString + '*' + str(recentDurCount)

        return returnString

    def lyGroupedMusicListFromScoreWithParts(self, scoreIn, scoreInit=None):
        # noinspection PyShadowingNames
        r'''
        More complex example showing how the score can be set up with ossia parts...

        >>> lpc = lily.translate.LilypondConverter()
        >>> #_DOCS_SHOW b = corpus.parse('bach/bwv66.6')
        >>> b = lily.translate._getCachedCorpusFile('bach/bwv66.6')  #_DOCS_HIDE
        >>> lpPartsAndOssiaInit = lpc.lyPartsAndOssiaInitFromScore(b)
        >>> lpGroupedMusicList = lpc.lyGroupedMusicListFromScoreWithParts(b,
        ...                scoreInit=lpPartsAndOssiaInit)
        >>> print(lpGroupedMusicList)
        <BLANKLINE>
         << \new Staff  = Soprano { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. }
           \new Staff  = Alto { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. }
           \new Staff  = Tenor { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. }
           \new Staff  = Bass { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. }
        <BLANKLINE>
          \context Staff  = Soprano \with {
              \autoBeamOff
          }
          { \startStaff \partial 32*8
                \clef "treble"
                \key fis \minor
                \time 4/4
                \set stemRightBeamCount = #1
                \once \override Stem #'direction = #DOWN
                cis'' 8 [
                \set stemLeftBeamCount = #1
                \once \override Stem #'direction = #DOWN
                b... 8 ]
                \bar "|"  %{ end measure 0 %}
                \once \override Stem #'direction = #UP
                a' 4
                \once \override Stem #'direction = #DOWN
                b... 4
                \once \override Stem #'direction = #DOWN
                cis'' 4  \fermata
                \once \override Stem #'direction = #DOWN
                e'' 4
                \bar "|"  %{ end measure 1 %}
                \once \override Stem #'direction = #DOWN
                cis'' 4
                ...
        }
        <BLANKLINE>
        <BLANKLINE>
        \context Staff  = Alto \with  {
            \autoBeamOff
         }
         { \startStaff \partial 32*8
            \clef "treble"...
            \once \override Stem #'direction = #UP
            e' 4
            \bar "|"  %{ end measure 0 %}
            \once \override Stem #'direction = #UP
            fis' 4
            \once \override Stem #'direction = #UP
            e' 4
        ...
        }
        <BLANKLINE>
        <BLANKLINE>
        >>
        <BLANKLINE>
        '''

        compositeMusicList = []

        lpGroupedMusicList = lyo.LyGroupedMusicList()
        lpSimultaneousMusic = lyo.LySimultaneousMusic()
        lpMusicList = lyo.LyMusicList()
        lpSimultaneousMusic.musicList = lpMusicList
        lpGroupedMusicList.simultaneousMusic = lpSimultaneousMusic

        self.newContext(lpMusicList)

        if scoreInit is None:
            for p in scoreIn.parts:
                compositeMusicList.append(self.lyPrefixCompositeMusicFromStream(p))
        else:
            compositeMusicList.append(scoreInit)
            for p in scoreIn.parts:
                compositeMusicList.append(
                    self.lyPrefixCompositeMusicFromStream(p,
                                                          type='context',
                                                          beforeMatter='startStaff'))

        self.restoreContext()
        lpMusicList.contents = compositeMusicList

        return lpGroupedMusicList

    def lyNewLyricsFromStream(self, streamIn, streamId=None, alignment='alignBelowContext'):
        r'''
        returns a LyNewLyrics object

        This is a little bit of a hack. This should be switched over to using a
        prefixed context thing with \new Lyric = "id" \with { } {}

        >>> s = converter.parse('tinyNotation: 4/4 c4_hel- d4_-lo r4 e4_world')
        >>> s.makeMeasures(inPlace=True)
        >>> s.id = 'helloWorld'

        >>> lpc = lily.translate.LilypondConverter()
        >>> lyNewLyrics = lpc.lyNewLyricsFromStream(s)
        >>> print(lyNewLyrics)
        \addlyrics { \set alignBelowContext = #"helloWorld"
           "hel" --
           "lo"__
           "world"
            }
        '''
        lyricsDict = streamIn.lyrics(skipTies=True)

        if streamId is None:
            streamId = makeLettersOnlyId(streamIn.id)

        streamId = '#' + lyo.LyObject().quoteString(streamId)

        lpGroupedMusicLists = []
        for lyricNum in sorted(lyricsDict):
            lyricList = []
            lpAlignmentProperty = lyo.LyPropertyOperation(mode='set',
                                                          value1=alignment,
                                                          value2=streamId)
            lyricList.append(lpAlignmentProperty)

            self.inWord = False
            for el in lyricsDict[lyricNum]:
                lpLyricElement = self.lyLyricElementFromM21Lyric(el)
                lyricList.append(lpLyricElement)

            self.inWord = False

            lpLyricList = lyo.LyMusicList(lyricList)

            lpSequentialMusic = lyo.LySequentialMusic(musicList=lpLyricList)
            lpGroupedMusicList = lyo.LyGroupedMusicList(sequentialMusic=lpSequentialMusic)
            lpGroupedMusicLists.append(lpGroupedMusicList)

        lpNewLyrics = lyo.LyNewLyrics(groupedMusicLists=lpGroupedMusicLists)

        return lpNewLyrics

    def lyLyricElementFromM21Lyric(self, m21Lyric):
        r'''
        Returns a :class:`~music21.lily.lilyObjects.LyLyricElement` object
        from a :class:`~music21.note.Lyric` object.

        Uses self.inWord to keep track of whether or not we're in the middle of
        a word.

        >>> s = converter.parse('tinyNotation: 4/4 c4_hel- d4_-lo r2 e2 f2_world')
        >>> s.makeMeasures(inPlace=True)
        >>> lyrics = s.lyrics()[1]  # get first verse (yes, 1 = first, not 0!)

        >>> lpc = lily.translate.LilypondConverter()
        >>> lpc.lyLyricElementFromM21Lyric(lyrics[0])
        <music21.lily.lilyObjects.LyLyricElement "hel" -->
        >>> lpc.inWord
        True
        >>> lpc.lyLyricElementFromM21Lyric(lyrics[1])
        <music21.lily.lilyObjects.LyLyricElement "lo"__>
        >>> lpc.lyLyricElementFromM21Lyric(lyrics[2])
        <music21.lily.lilyObjects.LyLyricElement _>
        >>> lpc.lyLyricElementFromM21Lyric(lyrics[3])
        <music21.lily.lilyObjects.LyLyricElement "world">
        >>> lpc.inWord
        False
        '''

        if hasattr(self, 'inWord'):
            inWord = self.inWord
        else:
            inWord = False

        el = m21Lyric
        if el is None and inWord:
            text = ' _ '
        elif el is None and inWord is False:
            text = ' _ '
        elif el.text == '':
            text = ' _ '
        else:
            text = '"' + el.text + '"'
            if el.syllabic == 'end':
                text = text + '__'
                inWord = False
            elif el.syllabic == 'begin' or el.syllabic == 'middle':
                text = text + ' --'
                inWord = True
            # else: pass

        self.inWord = inWord
        lpLyricElement = lyo.LyLyricElement(text)
        return lpLyricElement

    def lySequentialMusicFromStream(self, streamIn, beforeMatter=None):
        r'''
        returns a LySequentialMusic object from a stream

        >>> c = converter.parse('tinynotation: 3/4 C4 D E F2.')
        >>> lpc = lily.translate.LilypondConverter()
        >>> lySequentialMusicOut = lpc.lySequentialMusicFromStream(c)
        >>> lySequentialMusicOut
        <music21.lily.lilyObjects.LySequentialMusic { \clef "b...>
        >>> print(lySequentialMusicOut)
        { \clef "bass"
         \time 3/4
         c 4
         d 4
         e 4
         \bar "|"  %{ end measure 1 %}
         f 2.
         \bar "|."  %{ end measure 2 %}
          }
        <BLANKLINE>
        '''
        musicList = []

        lpMusicList = lyo.LyMusicList(contents=musicList)
        lpSequentialMusic = lyo.LySequentialMusic(musicList=lpMusicList,
                                                  beforeMatter=beforeMatter)
        self.newContext(lpMusicList)
        self.appendObjectsToContextFromStream(streamIn)

        lyObject = self.closeMeasure()
        if lyObject is not None:
            musicList.append(lyObject)

        self.restoreContext()
        return lpSequentialMusic

    # pylint: disable=redefined-builtin
    def lyPrefixCompositeMusicFromStream(
        self,
        streamIn,
        contextType=None,
        type=None,  # @ReservedAssignment
        beforeMatter=None
    ):
        # noinspection PyShadowingNames
        r'''
        returns an LyPrefixCompositeMusic object from
        a stream (generally a part, but who knows...)

        >>> c = converter.parse('tinynotation: 3/4 C4 D E F2.')
        >>> c.staffLines = 4

        >>> lpc = lily.translate.LilypondConverter()
        >>> lyPrefixCompositeMusicOut = lpc.lyPrefixCompositeMusicFromStream(c, contextType='Staff')
        >>> lyPrefixCompositeMusicOut
        <music21.lily.lilyObjects.LyPrefixCompositeMusic \new Staff...>
        >>> print(lyPrefixCompositeMusicOut)
        \new Staff = ... \with {
         \override StaffSymbol #'line-count = #4
        }
        { \clef "bass"
             \time 3/4
             c 4
             d 4
             e 4
             \bar "|"  %{ end measure 1 %}
             f 2.
             \bar "|."  %{ end measure 2 %}
              }
        <BLANKLINE>
        <BLANKLINE>
        '''
        compositeMusicType = type

        optionalId = None
        contextModList = []

        c = streamIn.classes
        if contextType is None:
            if 'Part' in c:
                newContext = 'Staff'
                optionalId = lyo.LyOptionalId(makeLettersOnlyId(streamIn.id))
            elif 'Voice' in c:
                newContext = 'Voice'
            else:
                newContext = 'Voice'
        else:
            newContext = contextType
            optionalId = lyo.LyOptionalId(makeLettersOnlyId(streamIn.id))

        if streamIn.streamStatus.beams is True:
            contextModList.append(r'\autoBeamOff ')

        if hasattr(streamIn, 'staffLines') and streamIn.staffLines != 5:
            contextModList.append(fr"\override StaffSymbol #'line-count = #{streamIn.staffLines}")
            if streamIn.staffLines % 2 == 0:  # even stafflines need a change...
                pass

        lpNewLyrics = self.lyNewLyricsFromStream(streamIn, streamId=makeLettersOnlyId(streamIn.id))

        lpSequentialMusic = self.lySequentialMusicFromStream(streamIn, beforeMatter=beforeMatter)
        lpGroupedMusicList = lyo.LyGroupedMusicList(sequentialMusic=lpSequentialMusic)
        lpCompositeMusic = lyo.LyCompositeMusic(groupedMusicList=lpGroupedMusicList,
                                                newLyrics=lpNewLyrics)
        lpMusic = lyo.LyMusic(compositeMusic=lpCompositeMusic)

        if compositeMusicType is None:
            compositeMusicType = 'new'

        if contextModList:
            contextMod = lyo.LyContextModification(contextModList)
        else:
            contextMod = None

        lpPrefixCompositeMusic = lyo.LyPrefixCompositeMusic(type=compositeMusicType,
                                                            optionalId=optionalId,
                                                            simpleString=newContext,
                                                            optionalContextMod=contextMod,
                                                            music=lpMusic)
        return lpPrefixCompositeMusic

    def appendObjectsToContextFromStream(self, streamObject):
        r'''
        takes a Stream and appends all the elements in it to the current
        context's .contents list, and deals with creating Voices in it. It also deals with
        variants in it.

        (should eventually replace the main Score parts finding tools)


        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.context.contents
        []
        >>> c = converter.parse('tinynotation: 3/4 b4 d- e#')
        >>> lpc.appendObjectsToContextFromStream(c)
        >>> print(lpc.context.contents)
        [<music21.lily.lilyObjects.LyEmbeddedScm...>,
         <music21.lily.lilyObjects.LySimpleMusic...>,
         <music21.lily.lilyObjects.LySimpleMusic...>,
         <music21.lily.lilyObjects.LySimpleMusic...]
        >>> print(lpc.context)
        \clef "treble"
        \time 3/4
        b' 4
        des' 4
        eis' 4
        <BLANKLINE>


        >>> v1 = stream.Voice()
        >>> v1.append(note.Note('C5', quarterLength = 4.0))
        >>> v2 = stream.Voice()
        >>> v2.append(note.Note('C#5', quarterLength = 4.0))
        >>> m = stream.Measure()
        >>> m.insert(0, v1)
        >>> m.insert(0, v2)
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.appendObjectsToContextFromStream(m)
        >>> print(lpc.context)  # internal spaces removed...
          << \new Voice { c'' 1
                    \bar "|."  %{ end measure 1 %}
                  }
           \new Voice { cis'' 1
                  }
            >>
        '''
        from music21.stream.iterator import OffsetIterator
        for groupedElements in OffsetIterator(streamObject):
            # print(groupedElements)

            if len(groupedElements) == 1:  # one thing at that moment...
                el = groupedElements[0]
                el.activeSite = streamObject
                self.appendM21ObjectToContext(el)
            else:  # voices or other More than one thing at once...
                # if voices
                voiceList = []
                variantList = []
                otherList = []
                for el in groupedElements:
                    if 'Voice' in el.classes:
                        voiceList.append(el)
                    elif 'Variant' in el.classes:
                        variantList.append(el)
                    else:
                        el.activeSite = streamObject
                        otherList.append(el)

                if variantList:
                    for v in variantList:
                        v.activeSite = streamObject
                    self.appendContextFromVariant(variantList,
                                                  activeSite=streamObject,
                                                  coloredVariants=self.coloredVariants)

                if voiceList:
                    musicList2 = []
                    lp2GroupedMusicList = lyo.LyGroupedMusicList()
                    lp2SimultaneousMusic = lyo.LySimultaneousMusic()
                    lp2MusicList = lyo.LyMusicList()
                    lp2SimultaneousMusic.musicList = lp2MusicList
                    lp2GroupedMusicList.simultaneousMusic = lp2SimultaneousMusic

                    for voice in voiceList:
                        if voice not in self.doNotOutput:
                            lpPrefixCompositeMusic = self.lyPrefixCompositeMusicFromStream(voice)
                            musicList2.append(lpPrefixCompositeMusic)

                    lp2MusicList.contents = musicList2

                    contextObject = self.context
                    currentMusicList = contextObject.contents
                    currentMusicList.append(lp2GroupedMusicList)
                    lp2GroupedMusicList.setParent(self.context)

                if otherList:
                    for el in otherList:
                        self.appendM21ObjectToContext(el)

    def appendM21ObjectToContext(self, thisObject):
        r'''
        converts any type of object into a lilyObject of LyMusic (
        LySimpleMusic, LyEmbeddedScm etc.) type
        '''
        if thisObject in self.doNotOutput:
            return

        # treat complex duration objects as multiple objects
        c = thisObject.classes

        if 'Stream' not in c and thisObject.duration.type == 'complex':
            thisObjectSplit = thisObject.splitAtDurations()
            for subComponent in thisObjectSplit:
                self.appendM21ObjectToContext(subComponent)
            return

        contextObject = self.context
        if hasattr(contextObject, 'contents'):
            currentMusicList = contextObject.contents
        else:  # pragma: no cover
            raise LilyTranslateException(
                f'Cannot get a currentMusicList from contextObject {contextObject!r}')

        if hasattr(thisObject, 'startTransparency') and thisObject.startTransparency is True:
            # old hack, replace with the better "hidden" attribute
            lyScheme = lyo.LyEmbeddedScm(self.transparencyStartScheme)
            currentMusicList.append(lyScheme)

        lyObject = None
        if 'Measure' in c:
            # lilypond does not put groups around measures...
            # it does however need barline ends
            # also, if variantMode is True, the last note in each "measure" should have \noBeam
            closeMeasureObj = self.closeMeasure()  # could be None
            if closeMeasureObj is not None:
                currentMusicList.append(closeMeasureObj)
                closeMeasureObj.setParent(contextObject)

            padObj = self.getSchemeForPadding(thisObject)
            if padObj is not None:
                currentMusicList.append(padObj)
                padObj.setParent(contextObject)

            # here we go!
            self.appendObjectsToContextFromStream(thisObject)
            self.currentMeasure = thisObject

        elif 'Stream' in c:
            # try:
            lyObject = self.lyPrefixCompositeMusicFromStream(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
            # except AttributeError as ae:
            #    raise Exception('Cannot parse %s: %s' % (thisObject, str(ae)))
        elif 'Note' in c or 'Rest' in c:
            self.appendContextFromNoteOrRest(thisObject)
        elif 'Chord' in c:
            self.appendContextFromChord(thisObject)
        elif 'Clef' in c:
            lyObject = self.lyEmbeddedScmFromClef(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif 'KeySignature' in c:
            lyObject = self.lyEmbeddedScmFromKeySignature(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif 'TimeSignature' in c and self.variantMode is False:
            lyObject = self.lyEmbeddedScmFromTimeSignature(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif 'Variant' in c:
            self.appendContextFromVariant(thisObject, coloredVariants=self.coloredVariants)
        elif 'SystemLayout' in c:
            lyObject = lyo.LyEmbeddedScm(r'\break')
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif 'PageLayout' in c:
            lyObject = lyo.LyEmbeddedScm(r'\pageBreak')
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        else:
            lyObject = None

        if hasattr(thisObject, 'stopTransparency') and thisObject.stopTransparency is True:
            # old hack, replace with the better "hidden" attribute
            lyScheme = lyo.LyEmbeddedScm(self.transparencyStopScheme)
            currentMusicList.append(lyScheme)

    def appendContextFromNoteOrRest(self, noteOrRest):
        r'''
        appends lySimpleMusicFromNoteOrRest to the
        current context.


        >>> n = note.Note('C#4')
        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.appendContextFromNoteOrRest(n)
        >>> print(lpMusicList)
        cis' 4
        <BLANKLINE>


        >>> n2 = note.Note('D#4')
        >>> n2.duration.quarterLength = 1/3
        >>> n2.duration.tuplets[0].type = 'start'
        >>> n3 = note.Note('E4')
        >>> n3.duration.quarterLength = 1/3
        >>> n4 = note.Note('F4')
        >>> n4.duration.quarterLength = 1/3
        >>> n4.duration.tuplets[0].type = 'stop'

        >>> n5 = note.Note('F#4')

        >>> lpc.appendContextFromNoteOrRest(n2)
        >>> lpc.appendContextFromNoteOrRest(n3)
        >>> lpc.appendContextFromNoteOrRest(n4)
        >>> lpc.appendContextFromNoteOrRest(n5)

        >>> print(lpc.context)
        cis' 4
        \times 2/3 { dis' 8
           e' 8
           f' 8
            }
        <BLANKLINE>
        fis' 4
        <BLANKLINE>

        '''
        # to be removed once grace notes are supported
        if noteOrRest.duration.isGrace:
            return

        # commented out until complete
#         if self.variantMode is True:
#             # TODO: attach \noBeam to note if it is the last note
#             if 'NotRest' in noteOrRest.classes:
#                 n = noteOrRest
#                 activeSite = n.activeSite
#                 offset = n.offset
#                 # failed at least once...
#                 if offset + n.duration.quarterLength == activeSite.duration.quarterLength:
#                     pass

        self.setContextForTupletStart(noteOrRest)
        self.appendBeamCode(noteOrRest)
        self.appendStemCode(noteOrRest)

        lpSimpleMusic = self.lySimpleMusicFromNoteOrRest(noteOrRest)
        self.context.contents.append(lpSimpleMusic)
        lpSimpleMusic.setParent(self.context)
        self.setContextForTupletStop(noteOrRest)

    def appendContextFromChord(self, chord):
        r'''
        appends lySimpleMusicFromChord to the
        current context.


        >>> c = chord.Chord(['C4', 'E4', 'G4'])
        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.appendContextFromChord(c)
        >>> print(lpMusicList)
        < c' e' g'  > 4
        <BLANKLINE>


        >>> c2 = chord.Chord(['D4', 'F#4', 'A4'])
        >>> c2.duration.quarterLength = 1/3
        >>> c2.duration.tuplets[0].type = 'start'
        >>> c3 = chord.Chord(['D4', 'F4', 'G4'])
        >>> c3.duration.quarterLength = 1/3
        >>> c4 = chord.Chord(['C4', 'E4', 'G4', 'C5'])
        >>> c4.duration.quarterLength = 1/3
        >>> c4.duration.tuplets[0].type = 'stop'

        >>> c5 = chord.Chord(['C4', 'F4', 'A-4'])

        >>> lpc.appendContextFromChord(c2)
        >>> lpc.appendContextFromChord(c3)
        >>> lpc.appendContextFromChord(c4)
        >>> lpc.appendContextFromChord(c5)

        >>> print(lpc.context)
        < c'  e'  g'  > 4
        \times 2/3 { < d'  fis'  a'  > 8
           < d'  f'  g'  > 8
           < c'  e'  g'  c''  > 8
            }
        <BLANKLINE>
        < c'  f'  aes'  > 4
        <BLANKLINE>

        '''
        self.setContextForTupletStart(chord)
        self.appendBeamCode(chord)
        self.appendStemCode(chord)

        lpSimpleMusic = self.lySimpleMusicFromChord(chord)
        self.context.contents.append(lpSimpleMusic)
        lpSimpleMusic.setParent(self.context)
        self.setContextForTupletStop(chord)

    def lySimpleMusicFromNoteOrRest(self, noteOrRest):
        r'''
        returns a lilyObjects.LySimpleMusic object for the generalNote containing...

            LyEventChord   containing
            LySimpleChordElements containing
            LySimpleElement containing
            LyPitch  AND
            LyMultipliedDuration containing:

                LyMultipliedDuration containing
                LyStenoDuration

        does not check for tuplets.  That's in
        appendContextFromNoteOrRest

        read-only property that returns a string of the lilypond representation of
        a note (or via subclassing, rest or chord)

        >>> conv = lily.translate.LilypondConverter()

        >>> n0 = note.Note('D#5')
        >>> n0.pitch.accidental.displayType = 'always'
        >>> n0.pitch.accidental.displayStyle = 'parentheses'
        >>> n0.style.color = 'blue'
        >>> sm = conv.lySimpleMusicFromNoteOrRest(n0)
        >>> print(sm)
        \color "blue" dis'' ! ? 4

        Now make the note disappear...

        >>> n0.style.hideObjectOnPrint = True
        >>> sm = conv.lySimpleMusicFromNoteOrRest(n0)
        >>> print(sm)
        s 4
        '''
        c = noteOrRest.classes

        simpleElementParts = []
        if noteOrRest.hasStyleInformation:
            if noteOrRest.style.color and noteOrRest.style.hideObjectOnPrint is False:
                colorLily = r'\color "' + noteOrRest.style.color + '" '
                simpleElementParts.append(colorLily)

        if 'Note' in c:
            if not noteOrRest.hasStyleInformation or noteOrRest.style.hideObjectOnPrint is False:
                lpPitch = self.lyPitchFromPitch(noteOrRest.pitch)
                simpleElementParts.append(lpPitch)
                if noteOrRest.pitch.accidental is not None:
                    if noteOrRest.pitch.accidental.displayType == 'always':
                        simpleElementParts.append('! ')
                    if noteOrRest.pitch.accidental.displayStyle == 'parentheses':
                        simpleElementParts.append('? ')
            else:
                simpleElementParts.append('s ')

        elif 'SpacerRest' in c:
            simpleElementParts.append('s ')
        elif 'Rest' in c:
            if noteOrRest.hasStyleInformation and noteOrRest.style.hideObjectOnPrint:
                simpleElementParts.append('s ')
            else:
                simpleElementParts.append('r ')

        lpMultipliedDuration = self.lyMultipliedDurationFromDuration(noteOrRest.duration)
        simpleElementParts.append(lpMultipliedDuration)

        if hasattr(noteOrRest, 'beams') and noteOrRest.beams:
            if noteOrRest.beams.beamsList[0].type == 'start':
                simpleElementParts.append('[ ')
            elif noteOrRest.beams.beamsList[0].type == 'stop':
                simpleElementParts.append('] ')  # no start-stop in music21...

        simpleElement = lyo.LySimpleElement(parts=simpleElementParts)

        postEvents = self.postEventsFromObject(noteOrRest)

        evc = lyo.LyEventChord(simpleElement, postEvents=postEvents)
        mlSM = lyo.LySimpleMusic(eventChord=evc)

        return mlSM

    def appendBeamCode(self, noteOrChord):
        r'''
        Adds an LyEmbeddedScm object to the context's contents if the object's has a .beams
        attribute.

        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.context.contents
        []
        >>> n1 = note.Note(quarterLength=0.25)
        >>> n2 = note.Note(quarterLength=0.25)
        >>> n1.beams.fill(2, 'start')
        >>> n2.beams.fill(2, 'stop')

        >>> lpc.appendBeamCode(n1)
        >>> print(lpc.context.contents)
        [<music21.lily.lilyObjects.LyEmbeddedScm \set stemR...>]
        >>> print(lpc.context)
        \set stemRightBeamCount = #2

        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.context.contents
        []
        >>> lpc.appendBeamCode(n2)
        >>> print(lpc.context.contents)
        [<music21.lily.lilyObjects.LyEmbeddedScm \set stemL...>]
        >>> print(lpc.context)
        \set stemLeftBeamCount = #2

        '''
        leftBeams = 0
        rightBeams = 0
        if hasattr(noteOrChord, 'beams'):
            if noteOrChord.beams is not None:
                for b in noteOrChord.beams:
                    if b.type == 'start':
                        rightBeams += 1
                    elif b.type == 'continue':
                        rightBeams += 1
                        leftBeams += 1
                    elif b.type == 'stop':
                        leftBeams += 1
                    elif b.type == 'partial':
                        if b.direction == 'left':
                            leftBeams += 1
                        else:  # better wrong direction than none
                            rightBeams += 1
                if leftBeams > 0:
                    beamText = rf'''\set stemLeftBeamCount = #{leftBeams}'''
                    lpBeamScheme = lyo.LyEmbeddedScm(beamText)
                    self.context.contents.append(lpBeamScheme)
                    lpBeamScheme.setParent(self.context)

                if rightBeams > 0:
                    beamText = fr'''\set stemRightBeamCount = #{rightBeams}'''
                    lpBeamScheme = lyo.LyEmbeddedScm(beamText)
                    self.context.contents.append(lpBeamScheme)
                    lpBeamScheme.setParent(self.context)

    def appendStemCode(self, noteOrChord):
        r'''
        Adds an LyEmbeddedScm object to the context's contents if the object's stem direction
        is set (currently, only "up" and "down" are supported).


        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.context.contents
        []
        >>> n = note.Note()
        >>> n.stemDirection = 'up'
        >>> lpc.appendStemCode(n)
        >>> print(lpc.context.contents)
        [<music21.lily.lilyObjects.LyEmbeddedScm \once \ove...>]
        >>> print(lpc.context.contents[0])
        \once \override Stem #'direction = #UP
        '''
        if hasattr(noteOrChord, 'stemDirection') and noteOrChord.stemDirection is not None:
            stemDirection = noteOrChord.stemDirection.upper()
            if stemDirection in ['UP', 'DOWN']:
                stemFile = fr'''\once \override Stem #'direction = #{stemDirection} '''
                lpStemScheme = lyo.LyEmbeddedScm(stemFile)
                self.context.contents.append(lpStemScheme)
                lpStemScheme.setParent(self.context)

    def lySimpleMusicFromChord(self, chordObj):
        '''


        >>> conv = lily.translate.LilypondConverter()
        >>> c1 = chord.Chord(['C#2', 'E4', 'D#5'])
        >>> c1.quarterLength = 3.5
        >>> c1.pitches[2].accidental.displayType = 'always'
        >>> print(conv.lySimpleMusicFromChord(c1))
         < cis, e' dis''  !  > 2..

        test hidden chord:

        >>> c1.style.hideObjectOnPrint = True
        >>> print(conv.lySimpleMusicFromChord(c1))
        s 2..
        '''
        self.appendBeamCode(chordObj)
        if not chordObj.hasStyleInformation or chordObj.style.hideObjectOnPrint is not True:

            self.appendStemCode(chordObj)

            chordBodyElements = []
            for p in chordObj.pitches:
                chordBodyElementParts = []
                lpPitch = self.lyPitchFromPitch(p)
                chordBodyElementParts.append(lpPitch)
                if p.accidental is not None:
                    if p.accidental.displayType == 'always':
                        chordBodyElementParts.append('! ')
                    if p.accidental.displayStyle == 'parentheses':
                        chordBodyElementParts.append('? ')
                lpChordElement = lyo.LyChordBodyElement(parts=chordBodyElementParts)
                chordBodyElements.append(lpChordElement)
            lpChordBody = lyo.LyChordBody(chordBodyElements=chordBodyElements)
        else:
            lpChordBody = lyo.LyPitch('s ', '')

        lpMultipliedDuration = self.lyMultipliedDurationFromDuration(chordObj.duration)

        postEvents = self.postEventsFromObject(chordObj)

        lpNoteChordElement = lyo.LyNoteChordElement(chordBody=lpChordBody,
                                                    optionalNoteModeDuration=lpMultipliedDuration,
                                                    postEvents=postEvents)
        evc = lyo.LyEventChord(noteChordElement=lpNoteChordElement)
        mlSM = lyo.LySimpleMusic(eventChord=evc)
        return mlSM
        # TODO: Chord beaming...

    def postEventsFromObject(self, generalNote):
        r'''
        attaches events that apply to notes and chords (and some other things) equally
        '''

        postEvents = []

        # remove this hack once lyrics work
        # if generalNote.lyric is not None:  # hack that uses markup...
        #    postEvents.append(r'_\markup { "' + generalNote.lyric + '" }\n ')
        # consider this hack removed. Yeah!

        if hasattr(generalNote, 'tie') and generalNote.tie is not None:
            if generalNote.tie.type != 'stop':
                postEvents.append('~ ')

        if hasattr(generalNote, 'expressions') and generalNote.expressions:
            for thisExpression in generalNote.expressions:
                if 'Fermata' in thisExpression.classes:
                    postEvents.append(r'\fermata ')
        return postEvents

    def lyPitchFromPitch(self, pitch):
        r'''
        converts a music21.pitch.Pitch object to a lily.lilyObjects.LyPitch
        object.
        '''

        baseName = self.baseNameFromPitch(pitch)
        octaveModChars = self.octaveCharactersFromPitch(pitch)
        lyPitch = lyo.LyPitch(baseName, octaveModChars)
        return lyPitch

    def baseNameFromPitch(self, pitch):
        r'''
        returns a string of the base name (including accidental)
        for a music21 pitch
        '''

        baseName = pitch.step.lower()
        if pitch.accidental is not None:
            if pitch.accidental.name in self.accidentalConvert:
                baseName += self.accidentalConvert[pitch.accidental.name]
        return baseName

    def octaveCharactersFromPitch(self, pitch):
        r'''
        returns a string of single-quotes or commas or '' representing
        the octave of a :class:`~music21.pitch.Pitch` object
        '''
        implicitOctave = pitch.implicitOctave
        if implicitOctave < 3:
            correctedOctave = 3 - implicitOctave
            octaveModChars = ',' * correctedOctave  # C2 = c,  C1 = c,,
        else:
            correctedOctave = implicitOctave - 3
            octaveModChars = '\'' * correctedOctave  # C4 = c', C5 = c''  etc.
        return octaveModChars

    def lyMultipliedDurationFromDuration(self, durationObj):
        r'''
        take a simple Duration (that is one with one DurationTuple
        object and return a LyMultipliedDuration object:


        >>> d = duration.Duration(3)
        >>> lpc = lily.translate.LilypondConverter()
        >>> lyMultipliedDuration = lpc.lyMultipliedDurationFromDuration(d)
        >>> str(lyMultipliedDuration)
        '2. '

        >>> str(lpc.lyMultipliedDurationFromDuration(duration.Duration(8.0)))
        '\\breve '
        >>> str(lpc.lyMultipliedDurationFromDuration(duration.Duration(16.0)))
        '\\longa '

        Does not work with zero duration notes:

        >>> d = duration.Duration(0.0)
        >>> str(lpc.lyMultipliedDurationFromDuration(d))
        Traceback (most recent call last):
        music21.lily.translate.LilyTranslateException: Cannot translate an object of
            zero duration <music21.duration.Duration 0.0>


        Does not work with complex durations:

        >>> d = duration.Duration(5.0)
        >>> str(lpc.lyMultipliedDurationFromDuration(d))
        Traceback (most recent call last):
        music21.lily.translate.LilyTranslateException: DurationException for durationObject
            <music21.duration.Duration 5.0>: Could not determine durationNumber from complex

        Instead split by components:

        >>> components = d.components
        >>> [str(lpc.lyMultipliedDurationFromDuration(c)) for c in components]
        ['1 ', '4 ']
        '''
        try:
            number_type = duration.convertTypeToNumber(durationObj.type)  # module call
        except duration.DurationException as de:
            raise LilyTranslateException(
                f'DurationException for durationObject {durationObj}: {de}')

        if number_type == 0:
            raise LilyTranslateException(
                f'Cannot translate an object of zero duration {durationObj}')

        if number_type < 1:
            if number_type == 0.5:
                number_type = r'\breve'
            elif number_type == 0.25:
                number_type = r'\longa'
            else:  # pragma no cover
                raise LilyTranslateException('Cannot support durations longer than longa')
        else:
            number_type = int(number_type)

        try:
            stenoDuration = lyo.LyStenoDuration(number_type, int(durationObj.dots))
            multipliedDuration = lyo.LyMultipliedDuration(stenoDuration)
        except duration.DurationException as de:
            raise LilyTranslateException(
                f'DurationException: Cannot translate durationObject {durationObj}: {de}')
        return multipliedDuration

    def lyEmbeddedScmFromClef(self, clefObj):
        # noinspection PyShadowingNames
        r'''
        converts a Clef object to a
        lilyObjects.LyEmbeddedScm object


        >>> tc = clef.TrebleClef()
        >>> conv = lily.translate.LilypondConverter()
        >>> lpEmbeddedScm = conv.lyEmbeddedScmFromClef(tc)
        >>> print(lpEmbeddedScm)
        \clef "treble"

        >>> t8c = clef.Treble8vbClef()
        >>> lpEmbeddedScm = conv.lyEmbeddedScmFromClef(t8c)
        >>> print(lpEmbeddedScm)
        \clef "treble_8"

        '''
        dictTranslate = OrderedDict([
            ('Treble8vbClef', 'treble_8'),
            ('TrebleClef', 'treble'),
            ('BassClef', 'bass'),
            ('AltoClef', 'alto'),
            ('TenorClef', 'tenor'),
            ('SopranoClef', 'soprano'),
            ('PercussionClef', 'percussion'),
        ])

        c = clefObj.classes
        lilyName = None
        for m21Class, lilyStr in dictTranslate.items():
            if m21Class in c:
                lilyName = lilyStr
                break
        else:  # pragma: no cover
            environLocal.printDebug(
                f'got a clef that lilypond does not know what to do with: {clefObj}')
            lilyName = ''

        lpEmbeddedScm = lyo.LyEmbeddedScm()
        clefScheme = (lpEmbeddedScm.backslash + 'clef '
                      + lpEmbeddedScm.quoteString(lilyName)
                      + lpEmbeddedScm.newlineIndent)
        lpEmbeddedScm.content = clefScheme
        return lpEmbeddedScm

    def lyEmbeddedScmFromKeySignature(self, keyObj):
        # noinspection PyShadowingNames
        r'''
        converts a Key or KeySignature object
        to a lilyObjects.LyEmbeddedScm object


        >>> d = key.Key('d')
        >>> conv = lily.translate.LilypondConverter()
        >>> lpEmbeddedScm = conv.lyEmbeddedScmFromKeySignature(d)
        >>> print(lpEmbeddedScm)
        \key d \minor

        Major is assumed:

        >>> fSharp = key.KeySignature(6)
        >>> print(conv.lyEmbeddedScmFromKeySignature(fSharp))
        \key fis \major

        '''
        if 'music21.key.Key' not in keyObj.classSet:
            keyObj = keyObj.asKey('major')

        p = keyObj.tonic
        m = keyObj.mode

        pn = self.baseNameFromPitch(p)

        lpEmbeddedScm = lyo.LyEmbeddedScm()
        keyScheme = (lpEmbeddedScm.backslash
                     + 'key ' + pn
                     + ' '
                     + lpEmbeddedScm.backslash + m
                     + ' '
                     + lpEmbeddedScm.newlineIndent)
        lpEmbeddedScm.content = keyScheme
        return lpEmbeddedScm

    def lyEmbeddedScmFromTimeSignature(self, ts):
        # noinspection PyShadowingNames
        r'''
        convert a :class:`~music21.meter.TimeSignature` object
        to a lilyObjects.LyEmbeddedScm object


        >>> ts = meter.TimeSignature('3/4')
        >>> conv = lily.translate.LilypondConverter()
        >>> print(conv.lyEmbeddedScmFromTimeSignature(ts))
        \time 3/4
        '''
        lpEmbeddedScm = lyo.LyEmbeddedScm()
        keyScheme = lpEmbeddedScm.backslash + 'time ' + ts.ratioString + lpEmbeddedScm.newlineIndent
        lpEmbeddedScm.content = keyScheme
        return lpEmbeddedScm

    def setContextForTupletStart(self, inObj):
        r'''
        if the inObj has tuplets then we set a new context
        for the tuplets and anything up till a tuplet stop.

        Note that a broken tuplet (a la Michael Gordon)
        will not work.

        If there are no tuplets, this routine does
        nothing.  If there are tuplets and they have type start then
        it returns an lpMusicList object, which is the new context

        For now, no nested tuplets.  They're an
        easy extension, but there's too much
        else missing to do it now...
        '''
        if not inObj.duration.tuplets:
            return None
        elif inObj.duration.tuplets[0].type == 'start':
            numerator = str(int(inObj.duration.tuplets[0].tupletNormal[0]))
            denominator = str(int(inObj.duration.tuplets[0].tupletActual[0]))
            lpMusicList = self.setContextForTimeFraction(numerator, denominator)
            return lpMusicList
        else:
            return None

    def setContextForTimeFraction(self, numerator, denominator):
        r'''
        Explicitly starts a new context for scaled music (tuplets, etc.)
        for the given numerator and denominator (either an int or a string or unicode)

        Returns an lpMusicList object contained in an lpSequentialMusic object
        in an lpPrefixCompositeMusic object which sets the times object to a particular
        fraction.


        >>> lpc = lily.translate.LilypondConverter()
        >>> lpc.context
        <music21.lily.lilyObjects.LyLilypondTop>
        >>> lyTop = lpc.context
        >>> lyoMusicList = lpc.setContextForTimeFraction(5, 4)
        >>> lyoMusicList
        <music21.lily.lilyObjects.LyMusicList>
        >>> lpc.context
        <music21.lily.lilyObjects.LyMusicList>
        >>> lpc.context is lyoMusicList
        True
        >>> lpc.context.getParent()
        <music21.lily.lilyObjects.LySequentialMusic {  }>
        >>> lpc.context.getParent().getParent()
        <music21.lily.lilyObjects.LyPrefixCompositeMusic \times 5/4...>
        >>> lpc.context.getParent().getParent().fraction
        '5/4'
        >>> lpc.context.getParent().getParent().type
        'times'
        >>> lpc.context.getParent().getParent().getParent()
        <music21.lily.lilyObjects.LyLilypondTop \times 5/4...>
        >>> lpc.context.getParent().getParent().getParent() is lyTop
        True
        '''
        fraction = str(numerator) + '/' + str(denominator)
        lpMusicList = lyo.LyMusicList()
        lpSequentialMusic = lyo.LySequentialMusic(musicList=lpMusicList)
        # technically needed, but we can speed things up
        # lpGroupedMusicList = lyo.LyGroupedMusicList(sequentialMusic=lpSequentialMusic)
        # lpCompositeMusic = lyo.LyCompositeMusic(groupedMusicList=lpGroupedMusicList)
        # lpMusic = lyo.LyMusic(compositeMusic=lpCompositeMusic)
        lpPrefixCompositeMusic = lyo.LyPrefixCompositeMusic(type='times',
                                                            fraction=fraction,
                                                            music=lpSequentialMusic)
        currentContents = self.context.contents
        if currentContents is None:  # pragma: no cover
            raise LilyTranslateException(
                f'Cannot find contents for self.context: {self.context!r} ')

        currentContents.append(lpPrefixCompositeMusic)
        lpPrefixCompositeMusic.setParent(self.context)
        self.newContext(lpMusicList)
        return lpMusicList

    def setContextForTupletStop(self, inObj):
        r'''
        Reverse of setContextForTupletStart
        '''
        if not inObj.duration.tuplets:
            return
        elif inObj.duration.tuplets[0].type == 'stop':
            self.restoreContext()
        else:
            return None

    def appendContextFromVariant(self, variantObjectOrList, activeSite=None, coloredVariants=False):
        r'''
        Create a new context from the variant object or a list of variants and append.
        '''
        musicList = []
        longestReplacedElements = []

        if isinstance(variantObjectOrList, variant.Variant):
            variantObject = variantObjectOrList
            replacedElements = variantObject.replacedElements(activeSite)
            lpPrefixCompositeMusicVariant = self.lyPrefixCompositeMusicFromVariant(
                variantObject, replacedElements, coloredVariants=coloredVariants
            )
            lpSequentialMusicStandard = self.lySequentialMusicFromStream(replacedElements)
            musicList.append(lpPrefixCompositeMusicVariant)
            musicList.append(lpSequentialMusicStandard)

        elif isinstance(variantObjectOrList, list):
            longestReplacementLength = -1
            variantDict = {}
            for variantObject in variantObjectOrList:
                if variantObject.groups:
                    variantName = variantObject.groups[0]
                else:
                    variantName = 'variant'
                if variantName in variantDict:
                    variantDict[variantName].append(variantObject)
                else:
                    variantDict[variantName] = [variantObject]

            for key in variantDict:
                variantList = variantDict[key]
                if len(variantList) == 1:
                    variantObject = variantList[0]
                    replacedElements = variantObject.replacedElements(activeSite)
                    lpPrefixCompositeMusicVariant = self.lyPrefixCompositeMusicFromVariant(
                        variantObject, replacedElements, coloredVariants=coloredVariants)
                    musicList.append(lpPrefixCompositeMusicVariant)
                else:
                    varTuple = self.lyPrefixCompositeMusicFromRelatedVariants(
                        variantList, activeSite=activeSite, coloredVariants=coloredVariants)
                    lpPrefixCompositeMusicVariant, replacedElements = varTuple
                    musicList.append(lpPrefixCompositeMusicVariant)

                if longestReplacementLength < replacedElements.duration.quarterLength:
                    longestReplacementLength = replacedElements.duration.quarterLength
                    longestReplacedElements = replacedElements

            lpSequentialMusicStandard = self.lySequentialMusicFromStream(longestReplacedElements)

            musicList.append(lpSequentialMusicStandard)
            for el in longestReplacedElements:
                self.doNotOutput.append(el)

        lp2MusicList = lyo.LyMusicList()
        lp2MusicList.contents = musicList
        lp2SimultaneousMusic = lyo.LySimultaneousMusic()
        lp2SimultaneousMusic.musicList = lp2MusicList
        lp2GroupedMusicList = lyo.LyGroupedMusicList()
        lp2GroupedMusicList.simultaneousMusic = lp2SimultaneousMusic

        contextObject = self.context
        currentMusicList = contextObject.contents
        currentMusicList.append(lp2GroupedMusicList)
        lp2GroupedMusicList.setParent(self.context)

    def lyPrefixCompositeMusicFromRelatedVariants(self,
                                                  variantList,
                                                  activeSite=None,
                                                  coloredVariants=False):
        # noinspection PyShadowingNames
        r'''


        >>> s1 = converter.parse('tinynotation: 4/4 a4 a a a  a1')
        >>> s2 = converter.parse('tinynotation: 4/4 b4 b b b')
        >>> s3 = converter.parse('tinynotation: 4/4 c4 c c c')
        >>> s4 = converter.parse('tinynotation: 4/4 d4 d d d')
        >>> s5 = converter.parse('tinynotation: 4/4 e4 e e e  f f f f  g g g g  a a a a  b b b b')

        >>> for s in [ s1, s2, s3, s4, s5]:
        ...     s.makeMeasures(inPlace=True)

        >>> activeSite = stream.Part(s5)

        >>> v1 = variant.Variant()
        >>> for el in s1:
        ...     v1.append(el)
        >>> v1.replacementDuration = 4.0

        >>> v2 = variant.Variant()
        >>> sp2 = note.SpacerRest()
        >>> sp2.duration.quarterLength = 4.0
        >>> v2.replacementDuration = 4.0
        >>> v2.append(sp2)
        >>> for el in s2:
        ...     v2.append(el)

        >>> v3 = variant.Variant()
        >>> sp3 = note.SpacerRest()
        >>> sp3.duration.quarterLength = 8.0
        >>> v3.replacementDuration = 4.0
        >>> v3.append(sp3)
        >>> for el in s3:
        ...     v3.append(el)

        >>> v4 = variant.Variant()
        >>> sp4 = note.SpacerRest()
        >>> sp4.duration.quarterLength = 16.0
        >>> v4.replacementDuration = 4.0
        >>> v4.append(sp4)
        >>> for el in s4:
        ...     v4.append(el)

        >>> variantList = [v4, v1, v3, v2]
        >>> for v in variantList :
        ...     v.groups = ['london']
        ...     activeSite.insert(0.0, v)


        >>> lpc = lily.translate.LilypondConverter()

        >>> print(lpc.lyPrefixCompositeMusicFromRelatedVariants(variantList,
        ...                activeSite=activeSite)[0])
        \new Staff  = london... { { \times 1/2 {\startStaff \clef "treble"
              a' 4
              a' 4
              a' 4
              a' 4
              \clef "treble"
              | %{ end measure 1 %}
              a' 1
              | %{ end measure 2 %}
               \stopStaff}
               }
        <BLANKLINE>
          {\startStaff \clef "treble"
            b... 4
            b... 4
            b... 4
            b... 4
            | %{ end measure 1 %}
             \stopStaff}
        <BLANKLINE>
          {\startStaff \clef "treble"
            c' 4
            c' 4
            c' 4
            c' 4
            | %{ end measure 1 %}
             \stopStaff}
        <BLANKLINE>
          s 1
          {\startStaff \clef "treble"
            d' 4
            d' 4
            d' 4
            d' 4
            | %{ end measure 1 %}
             \stopStaff}
        <BLANKLINE>
           }
        <BLANKLINE>

        '''

        # Order List

        def findOffsetOfFirstNonSpacerElement(inputStream):
            for el in inputStream:
                if 'SpacerRest' in el.classes:
                    pass
                else:
                    return inputStream.elementOffset(el)

        variantList.sort(key=lambda vv: findOffsetOfFirstNonSpacerElement(vv._stream))

        # Stuff that can be done on the first element only (clef, new/old, id, color)
        replacedElements = variantList[0].replacedElements(activeSite)
        re0 = replacedElements[0]
        replacedElementsClef = re0.clef or re0.getContextByClass('Clef')

        variantContainerStream = variantList[0].getContextByClass('Part')
        if variantContainerStream is None:
            variantContainerStream = variantList[0].getContextByClass('Stream')

        variantList[0].insert(0.0, replacedElementsClef)
        variantName = variantList[0].groups[0]
        if variantName in self.addedVariants:
            newVariant = False
        else:
            self.addedVariants.append(variantName)
            newVariant = True

        containerId = makeLettersOnlyId(variantContainerStream.id)
        variantId = lyo.LyOptionalId(makeLettersOnlyId(variantName) + containerId)

        if coloredVariants is True:
            color = self.variantColors[self.addedVariants.index(variantName) % 6]
        else:
            color = None

        #######################

        musicList = []
        highestOffsetSoFar = 0.0
        longestVariant = None

        self.variantMode = True

        for v in variantList:
            # For each variant in the list, we make a lilypond representation of the
            # spacer between this variant and the previous if it is non-zero and append it
            # Then we strip off the spacer and make a lilypond representation of the variant
            # with the appropriate tupletting if any and append that.
            # At the end we make a new lilypond context for it and return it.

            firstOffset = findOffsetOfFirstNonSpacerElement(v._stream)

            if firstOffset < highestOffsetSoFar:
                raise LilyTranslateException('Should not have overlapping variants.')

            spacerDuration = firstOffset - highestOffsetSoFar
            highestOffsetSoFar = v.replacementDuration + firstOffset

            # make spacer with spacerDuration and append
            if spacerDuration > 0.0:
                spacer = note.SpacerRest()
                spacer.duration.quarterLength = spacerDuration
                # noinspection PyTypeChecker
                lySpacer = self.lySimpleMusicFromNoteOrRest(spacer)
                musicList.append(lySpacer)

            if coloredVariants is True:
                for n in v._stream.recurse().notesAndRests:
                    n.style.color = color  # make thing (with or without fraction)

            # Strip off spacer
            endOffset = v.containedHighestTime
            vStripped = variant.Variant(v._stream.getElementsByOffset(firstOffset,
                                                                      offsetEnd=endOffset))
            vStripped.replacementDuration = v.replacementDuration

            replacedElementsLength = vStripped.replacementDuration
            variantLength = vStripped.containedHighestTime - firstOffset

            if variantLength != replacedElementsLength:
                numerator, denominator = common.decimalToTuplet(
                    replacedElementsLength / variantLength)
                fraction = str(numerator) + '/' + str(denominator)
                lpOssiaMusicVariantPreFraction = self.lyOssiaMusicFromVariant(vStripped)
                lpVariantTuplet = lyo.LyPrefixCompositeMusic(type='times',
                                                             fraction=fraction,
                                                             music=lpOssiaMusicVariantPreFraction)

                lpOssiaMusicVariant = lyo.LySequentialMusic(musicList=lpVariantTuplet)
            else:
                lpOssiaMusicVariant = self.lyOssiaMusicFromVariant(vStripped)

            musicList.append(lpOssiaMusicVariant)

            longestVariant = v

        # The last variant in the iteration should have the highestOffsetSoFar,
        # so it has the appropriate replacementElements to return can compare with the rest in
        # appendContextFromVariant.

        replacedElements = longestVariant.replacedElements(activeSite, includeSpacers=True)

        lpMusicList = lyo.LyMusicList(musicList)
        lpInternalSequentialMusic = lyo.LySequentialMusic(musicList=lpMusicList)

        compositeMusicType = 'new' if newVariant else 'context'
        lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(
            type=compositeMusicType,
            optionalId=variantId,
            simpleString='Staff',
            music=lpInternalSequentialMusic)

        self.variantMode = False

        return lpPrefixCompositeMusicVariant, replacedElements

    def lyPrefixCompositeMusicFromVariant(self,
                                          variantObject,
                                          replacedElements,
                                          coloredVariants=False):
        # noinspection PyShadowingNames
        r'''

        >>> pStream = converter.parse('tinynotation: 4/4 a4 b c d   e4 f g a')
        >>> pStream.makeMeasures(inPlace=True)
        >>> p = stream.Part(pStream)
        >>> p.id = 'p1'
        >>> vStream = converter.parse('tinynotation: 4/4 a4. b8 c4 d')
        >>> vStream.makeMeasures(inPlace=True)
        >>> v = variant.Variant(vStream)
        >>> v.groups = ['london']
        >>> p.insert(0.0, v)
        >>> lpc = lily.translate.LilypondConverter()
        >>> replacedElements = v.replacedElements()
        >>> lpPrefixCompositeMusicVariant = lpc.lyPrefixCompositeMusicFromVariant(v,
        ...                                                            replacedElements)
        >>> print(lpPrefixCompositeMusicVariant)  # ellipses are for non-byte fix-ups
        \new Staff  = londonpx { {\startStaff \clef "treble"
            a' 4.
            b...
            c' 4
            d' 4
            | %{ end measure 1 %}
             \stopStaff}
           }

        >>> replacedElements.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note D>

        >>> print(lpc.addedVariants)
        ['london']

        '''
        replacedElementsClef = replacedElements[0].getContextByClass('Clef')

        variantContainerStream = variantObject.getContextByClass('Part')
        if variantContainerStream is None:
            variantContainerStream = variantObject.getContextByClass('Stream')

        if replacedElementsClef is not None:
            if replacedElementsClef not in variantObject.elements:
                variantObject.insert(0, replacedElementsClef)

        if variantObject.groups:
            variantName = variantObject.groups[0]
        else:
            variantName = 'variant'
        if variantName in self.addedVariants:
            newVariant = False
        else:
            self.addedVariants.append(variantName)
            newVariant = True

        containerId = makeLettersOnlyId(variantContainerStream.id)
        variantId = lyo.LyOptionalId(makeLettersOnlyId(variantName) + containerId)

        if coloredVariants is True:
            color = self.variantColors[self.addedVariants.index(variantName) % 6]
            for n in variantObject._stream.recurse().notesAndRests:
                n.style.color = color

        musicList = []

        varFilter = variantObject.getElementsByClass('SpacerRest')
        if varFilter:
            spacer = varFilter[0]
            spacerDur = spacer.duration.quarterLength
            if spacer.duration.quarterLength > 0.0:
                lySpacer = self.lySimpleMusicFromNoteOrRest(spacer)
                musicList.append(lySpacer)
            variantObject.remove(spacer)
        else:
            spacerDur = 0.0

        lpOssiaMusicVariant = self.lyOssiaMusicFromVariant(variantObject)

        replacedElementsLength = variantObject.replacementDuration
        variantLength = variantObject.containedHighestTime - spacerDur

        self.variantMode = True
        if variantLength != replacedElementsLength:
            numerator, denominator = common.decimalToTuplet(replacedElementsLength / variantLength)
            fraction = str(numerator) + '/' + str(denominator)
            lpVariantTuplet = lyo.LyPrefixCompositeMusic(type='times',
                                                         fraction=fraction,
                                                         music=lpOssiaMusicVariant)
            lpInternalSequentialMusic = lyo.LySequentialMusic(musicList=lpVariantTuplet)
            musicList.append(lpInternalSequentialMusic)
        else:
            musicList.append(lpOssiaMusicVariant)

        lpMusicList = lyo.LyMusicList(musicList)
        lpOssiaMusicVariantWithSpacer = lyo.LySequentialMusic(musicList=lpMusicList)

        if newVariant is True:
            lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(
                type='new',
                optionalId=variantId,
                simpleString='Staff',
                music=lpOssiaMusicVariantWithSpacer)
        else:
            lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(
                type='context',
                optionalId=variantId,
                simpleString='Staff',
                music=lpOssiaMusicVariantWithSpacer)

        # optionalContextMod = r'''
        # \with {
        #      \remove "Time_signature_engraver"
        #      alignAboveContext = #"%s"
        #      fontSize = #-3
        #      \override StaffSymbol #'staff-space = #(magstep -3)
        #      \override StaffSymbol #'thickness = #(magstep -3)
        #      \override TupletBracket #'bracket-visibility = ##f
        #      \override TupletNumber #'stencil = ##f
        #      \override Clef #'transparent = ##t
        #    }
        # ''' % containerId #\override BarLine #'transparent = ##t
        # # is the best way of fixing the #barlines that I have come up with.
        # lpPrefixCompositeMusicVariant.optionalContextMod = optionalContextMod

        self.variantMode = False

        return lpPrefixCompositeMusicVariant

        # musicList2 = []
        # musicList2.append(lpPrefixCompositeMusicVariant)
        # musicList2.append(lpSequentialMusicStandard )
        #
        # lp2MusicList = lyo.LyMusicList()
        # lp2MusicList.contents = musicList2
        # lp2SimultaneousMusic = lyo.LySimultaneousMusic()
        # lp2SimultaneousMusic.musicList = lp2MusicList
        # lp2GroupedMusicList = lyo.LyGroupedMusicList()
        # lp2GroupedMusicList.simultaneousMusic = lp2SimultaneousMusic
        #
        # contextObject = self.context
        # currentMusicList = contextObject.contents
        # currentMusicList.append(lp2GroupedMusicList)
        # lp2GroupedMusicList.setParent(self.context)

    def lyOssiaMusicFromVariant(self, variantIn):
        r'''
        returns a LyOssiaMusic object from a stream


        >>> c = converter.parse('tinynotation: 3/4 C4 D E F2.')
        >>> v = variant.Variant(c)
        >>> lpc = lily.translate.LilypondConverter()
        >>> lySequentialMusicOut = lpc.lySequentialMusicFromStream(v)
        >>> lySequentialMusicOut
        <music21.lily.lilyObjects.LySequentialMusic { \clef "b...>
        >>> print(lySequentialMusicOut)
        { \clef "bass"
         \time 3/4
         c 4
         d 4
         e 4
         \bar "|"  %{ end measure 1 %}
         f 2.
         \bar "|."  %{ end measure 2 %}
          }
        <BLANKLINE>
        '''
        musicList = []

        lpMusicList = lyo.LyMusicList(contents=musicList)
        lpOssiaMusic = lyo.LyOssiaMusic(musicList=lpMusicList)
        self.newContext(lpMusicList)

        self.variantMode = True
        self.appendObjectsToContextFromStream(variantIn._stream)

        lyObject = self.closeMeasure()
        if lyObject is not None:
            musicList.append(lyObject)

        self.restoreContext()

        self.variantMode = False

        return lpOssiaMusic

    def setHeaderFromMetadata(self, metadataObject=None, lpHeader=None):
        # noinspection PyShadowingNames
        r'''
        Returns a lilypond.lilyObjects.LyLilypondHeader object
        set with data from the metadata object


        >>> md = metadata.Metadata()
        >>> md.title = 'My Title'
        >>> md.alternativeTitle = 'My "sub"-title'

        >>> lpc = lily.translate.LilypondConverter()
        >>> lpHeader = lpc.setHeaderFromMetadata(md)
        >>> print(lpHeader)
        \header { title = "My Title"
        subtitle = "My \"sub\"-title"
        }
        '''

        if lpHeader is None:
            lpHeader = lyo.LyLilypondHeader()

        if lpHeader.lilypondHeaderBody is None:
            lpHeaderBody = lyo.LyLilypondHeaderBody()
            lpHeader.lilypondHeaderBody = lpHeaderBody
        else:
            lpHeaderBody = lpHeader.lilypondHeaderBody

        lpHeaderBodyAssignments = lpHeaderBody.assignments

        if metadataObject is not None:
            if metadataObject.title is not None:
                lyTitleAssignment = lyo.LyAssignment(assignmentId='title',
                                                     identifierInit=lyo.LyIdentifierInit(
                                                         string=metadataObject.title))
                lpHeaderBodyAssignments.append(lyTitleAssignment)
                lyTitleAssignment.setParent(lpHeaderBody)
            if metadataObject.alternativeTitle is not None:
                lySubtitleAssignment = lyo.LyAssignment(assignmentId='subtitle',
                                                        identifierInit=lyo.LyIdentifierInit(
                                                            string=metadataObject.alternativeTitle))
                lpHeaderBodyAssignments.append(lySubtitleAssignment)
                lySubtitleAssignment.setParent(lpHeaderBody)

        lpHeaderBody.assignments = lpHeaderBodyAssignments
        return lpHeader

    def closeMeasure(self, barChecksOnly=False):
        # noinspection PyShadowingNames
        r'''
        return a LyObject or None for the end of the previous Measure

        uses self.currentMeasure


        >>> lpc = lily.translate.LilypondConverter()
        >>> m = stream.Measure()
        >>> m.number = 2
        >>> m.rightBarline = 'double'
        >>> lpc.currentMeasure = m
        >>> lyObj = lpc.closeMeasure()
        >>> lpc.currentMeasure is None
        True
        >>> print(lyObj)
        \bar "||"  %{ end measure 2 %}
        '''
        m = self.currentMeasure
        self.currentMeasure = None
        if m is None:
            return None
        # if m.rightBarline is None:
        #    return None
        # elif m.rightBarline.type == 'regular':
        #    return None

        if self.variantMode is True:
            barChecksOnly = True

        lpBarline = lyo.LyEmbeddedScm()

        if barChecksOnly is True:
            barString = '|'
        elif m.rightBarline is None:
            barString = lpBarline.backslash + 'bar ' + lpBarline.quoteString('|')
        else:
            barString = lpBarline.backslash + 'bar ' + lpBarline.quoteString(
                self.barlineDict[m.rightBarline.type])

        if m.number is not None:
            barString += lpBarline.comment(f'end measure {m.number}')

        lpBarline.content = barString
        return lpBarline

    def getSchemeForPadding(self, measureObject):
        r'''
        lilypond partial durations are very strange and are really of
        type LyMultipliedDuration.  You notate how many
        notes are left in the measure, for a quarter note, write "4"
        for an eighth, write "8", but for 3 eighths, write "8*3" !
        so we will measure in 32nd notes always... won't work for tuplets
        of course.

        returns a scheme object or None if not needed


        >>> m = stream.Measure()
        >>> m.append(meter.TimeSignature('3/4'))
        >>> m.paddingLeft = 2.0
        >>> lpc = lily.translate.LilypondConverter()
        >>> outScheme = lpc.getSchemeForPadding(m)
        >>> print(outScheme)
        \partial 32*8
        '''
        pL = measureObject.paddingLeft
        if pL == 0:
            return None
        measureTimeSignatures = measureObject.getTimeSignatures()
        if not measureTimeSignatures:
            barLength = 4.0
        else:
            ts = measureTimeSignatures[0]
            barLength = ts.barDuration.quarterLength
        remainingQL = barLength - pL
        if remainingQL <= 0:
            raise LilyTranslateException('your first pickup measure is non-existent!')
        remaining32s = int(remainingQL * 8)
        lyObject = lyo.LyEmbeddedScm()
        schemeStr = lyObject.backslash + 'partial 32*' + str(remaining32s) + ' '
        lyObject.content = schemeStr
        return lyObject

    # -------------display and converter routines ---------------------#
    def writeLyFile(self, ext='', fp=None):
        r'''
        writes the contents of the self.topLevelObject to a file.

        The extension should be ly.  If fp is None then a named temporary
        file is created by environment.getTempFile.

        '''
        tloOut = str(self.topLevelObject)
        if fp is None:
            fp = environLocal.getTempFile(ext, returnPathlib=False)

        self.tempName = pathlib.Path(fp)

        with self.tempName.open('w', encoding='utf-8') as f:
            f.write(tloOut)

        return self.tempName

    # noinspection PyShadowingBuiltins
    def runThroughLily(self, format=None,  # @ReservedAssignment
                       backend=None, fileName=None, skipWriting=False):
        r'''
        creates a .ly file from self.topLevelObject via .writeLyFile
        then runs the file through Lilypond.

        Returns the full path of the file produced by lilypond including the format extension.

        If skipWriting is True and a fileName is given then it will run
        that file through lilypond instead

        '''
        LILYEXEC = self.findLilyExec()
        if fileName is None:
            fileName = self.writeLyFile(ext='ly')
        else:
            if skipWriting is False:
                fileName = self.writeLyFile(ext='ly', fp=fileName)

        lilyCommand = '"' + LILYEXEC + '" '
        if format is not None:
            lilyCommand += '-f ' + format + ' '
        if backend is not None:
            lilyCommand += self.backendString + backend + ' '
        lilyCommand += '-o ' + str(fileName) + ' ' + str(fileName)

        os.system(lilyCommand)

        try:
            os.remove(str(fileName) + '.eps')
        except OSError:
            pass
        fileForm = str(fileName) + '.' + format
        if not os.path.exists(fileForm):
            # cannot find full path; try current directory
            fileEnd = os.path.basename(fileForm)
            if not os.path.exists(fileEnd):
                raise LilyTranslateException('cannot find ' + fileEnd
                                             + ' or the full path ' + fileForm
                                             + ' original file was ' + fileName)
            fileForm = fileEnd
        return pathlib.Path(fileForm)

    def createPDF(self, fileName=None):
        r'''
        create a PDF file from self.topLevelObject and return the filepath of the file.

        most users will just call stream.write('lily.pdf') on a stream.
        '''
        self.headerScheme.content = ''  # clear header
        lilyFile = self.runThroughLily(backend='ps', format='pdf', fileName=fileName)
        return lilyFile

    def showPDF(self):
        r'''
        create a SVG file from self.topLevelObject, show it with your pdf reader
        (often Adobe Acrobat/Adobe Reader or Apple Preview)
        and return the filepath of the file.

        most users will just call stream.Stream.show('lily.pdf') on a stream.
        '''
        lF = self.createPDF()
        if not lF.exists():  # pragma: no cover
            raise Exception('Something went wrong with PDF Creation')

        if os.name == 'nt':
            command = f'start /wait {str(lF)} && del /f {str(lF)}'
        elif sys.platform == 'darwin':
            command = f'open {str(lF)}'
        else:
            command = ''
        os.system(command)

    def createPNG(self, fileName=None):
        r'''
        create a PNG file from self.topLevelObject and return the filepath of the file.

        most users will just call stream.write('lily.png') on a stream.

        if PIL is installed then a small white border is created around the score
        '''
        lilyFile = self.runThroughLily(backend='eps', format='png', fileName=fileName)
        if noPIL is False:
            # noinspection PyPackageRequirements
            from PIL import Image, ImageOps
            # noinspection PyBroadException
            try:
                lilyImage = Image.open(str(lilyFile))  # @UndefinedVariable
                lilyImage2 = ImageOps.expand(lilyImage, 10, 'white')
                lilyImage2.save(str(lilyFile))
            except Exception:  # pylint: disable=broad-except
                pass  # no big deal probably...
        return lilyFile

    def showPNG(self):
        r'''
        Take the object, run it through LilyPond, and then show it as a PNG file.
        On Windows, the PNG file will not be deleted, so you  will need to clean out
        TEMP every once in a while.

        Most users will just want to call stream.Stream.show('lily.png') instead.
        '''
        try:
            lilyFile = self.createPNG()
        except LilyTranslateException as e:
            raise LilyTranslateException('Problems creating PNG file: (' + str(e) + ')')
        # self.showImageDirect(lilyFile)
        return SubConverter().launch(lilyFile, fmt='png')

    def createSVG(self, fileName=None):
        r'''
        create an SVG file from self.topLevelObject and return the filepath of the file.

        most users will just call stream.Stream.write('lily.svg') on a stream.
        '''
        self.headerScheme.content = ''  # clear header
        lilyFile = self.runThroughLily(format='svg', backend='svg', fileName=fileName)
        return lilyFile

    def showSVG(self, fileName=None):
        r'''
        create a SVG file from self.topLevelObject, show it with your
        svg reader (often Internet Explorer on PC)
        and return the filepath of the file.

        most users will just call stream.Stream.show('lily.png') on a stream.
        '''
        lilyFile = self.createSVG(fileName)
        return SubConverter().launch(lilyFile, fmt='svg')


class LilyTranslateException(exceptions21.Music21Exception):
    pass


class Test(unittest.TestCase):
    pass

    def testExplicitConvertChorale(self):
        lpc = LilypondConverter()
        b = _getCachedCorpusFile('bach/bwv66.6')
        lpc.loadObjectFromScore(b, makeNotation=False)
        # print(lpc.topLevelObject)

    def testComplexDuration(self):
        from music21 import stream, meter
        s = stream.Stream()
        n1 = note.Note('C')  # test no octave also!
        n1.duration.quarterLength = 2.5  # BUG 2.3333333333 doesn't work right
        self.assertEqual(n1.duration.type, 'complex')
        n2 = note.Note('D4')
        n2.duration.quarterLength = 1.5
        s.append(meter.TimeSignature('4/4'))
        s.append(n1)
        s.append(n2)
        # s.show('text')
        lpc = LilypondConverter()
        lpc.loadObjectFromScore(s)
        # print(lpc.topLevelObject)
        # lpc.showPNG()
        # s.show('lily.png')


class TestExternal(unittest.TestCase):  # pragma: no cover
    def xtestConvertNote(self):
        n = note.Note('C5')
        n.show('lily.png')

    def xtestConvertChorale(self):
        b = _getCachedCorpusFile('bach/bwv66.6')
        for n in b.flat:
            n.beams = None
        b.parts[0].show('lily.svg')

    def xtestSlowConvertOpus(self):
        fifeOpus = corpus.parse('miscFolk/americanfifeopus.abc')
        fifeOpus.show('lily.png')

    def xtestBreve(self):
        from music21 import stream, meter
        n = note.Note('C5')
        n.duration.quarterLength = 8.0
        m = stream.Measure()
        m.append(meter.TimeSignature('8/4'))
        m.append(n)
        p = stream.Part()
        p.append(m)
        s = stream.Score()
        s.append(p)
        s.show('lily.png')

    def testStaffLines(self):
        from music21 import stream
        s = stream.Score()
        p = stream.Part()
        p.append(note.Note('B4', type='whole'))
        p.staffLines = 1
        s.insert(0, p)
        p2 = stream.Part()
        p2.append(note.Note('B4', type='whole'))
        p2.staffLines = 7
        s.insert(0, p2)
        s.show('lily.png')


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # pylint: disable=ungrouped-imports
    import music21
    music21.mainTest(Test)  # , TestExternal)
    # music21.mainTest(TestExternal, 'noDocTest')

