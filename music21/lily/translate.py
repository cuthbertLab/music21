# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         lily/translate.py
# Purpose:      music21 classes for translating to Lilypond
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2007-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

'''
music21 translates to Lilypond format and if Lilypond is installed on the
local computer, can automatically generate .pdf, .png, and .svg versions
of musical files using Lilypond

this replaces (July 2012) the old LilyString() conversion methods.
'''
from __future__ import unicode_literals

import os
import sys
import tempfile
import re
import time
# import threading
import unittest, doctest
import copy
import random

import re
from music21 import common
from music21 import duration
from music21 import environment
from music21 import exceptions21
from music21 import variant
from music21 import note
from music21.lily import lilyObjects as lyo
_MOD = 'lily.translate2012.py'
environLocal = environment.Environment(_MOD)


try: 
    # optional imports for PIL 
    from PIL import Image
    from PIL import ImageOps
    noPIL = False
except ImportError:
    noPIL = True

from music21 import corpus

### speed up tests! move to music21 base...
class _sharedCorpusTestObject(object):
    sharedCache = {}

sharedCacheObject = _sharedCorpusTestObject()

def _getCachedCorpusFile(keyName):
    #return corpus.parse(keyName)
    if keyName not in sharedCacheObject.sharedCache:
        sharedCacheObject.sharedCache[keyName] = corpus.parse(keyName)
    return sharedCacheObject.sharedCache[keyName]


#b.parts[0].measure(4)[2].color = 'blue'#.rightBarline = 'double'

def makeLettersOnlyId(inputString):
    '''
    >>> from music21 import *
    >>> print lily.translate.makeLettersOnlyId('rainbow123@@dfas')
    rainbowxyzmmdfas

    '''
    inputString = str(inputString)
    returnString = ''
    for c in inputString:
        if not c.isalpha():
            c = chr(ord(c) % 26 + 97)
        returnString += c

    return returnString

#-------------------------------------------------------------------------------
class LilypondConverter(object):


    fictaDef = \
    r'''
    ficta = #(define-music-function (parser location) () #{ \once \set suggestAccidentals = ##t #})
    '''.lstrip()
    colorDef = \
    r'''
    color = #(define-music-function (parser location color) (string?) #{ 
        \once \override NoteHead #'color = #(x11-color $color) 
        \once \override Stem #'color = #(x11-color $color)
        \once \override Rest #'color = #(x11-color $color)
        \once \override Beam #'color = #(x11-color $color)
     #})    
    '''.lstrip()
    simplePaperDefinitionScm  = r'''
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
 
    accidentalConvert = {"double-sharp": u"isis",
                         "double-flat": u"eses",
                         "one-and-a-half-sharp": u"isih",
                         "one-and-a-half-flat": u"eseh",
                         "sharp": u"is",
                         "flat": u"es",
                         "half-sharp": u"ih",
                         "half-flat": u"eh",
                         }
    
    barlineDict = {'regular': '|',
                   'dotted': ':',
                   'dashed': 'dashed',
                   'heavy': '.',  #??
                   'double': '||',
                   'final': '|.',
                   'heavy-light': '.|',
                   'heavy-heavy': '.|.',
                   'start-repeat': '|:',
                   'end-repeat': ':|',
                   # no music21 support for |.| lightHeavyLight yet
                   'tick': '\'',
                   #'short': '', # no lilypond support??
                   'none': '',
                   }
    
    def __init__(self):
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

    def setupTools(self):
        if os.path.exists(environLocal['lilypondPath']):
            LILYEXEC = environLocal['lilypondPath']
        else:
            if sys.platform == "darwin":
                LILYEXEC = '/Applications/Lilypond.app/Contents/Resources/bin/lilypond'
            elif sys.platform == 'win32' and os.path.exists('c:/Program Files (x86)'):
                LILYEXEC = 'c:/Program\ Files\ (x86)/lilypond/usr/bin/lilypond'
            elif sys.platform == 'win32':
                LILYEXEC = 'c:/Program\ Files/lilypond/usr/bin/lilypond'
            else:
                LILYEXEC = 'lilypond'
        self.LILYEXEC = LILYEXEC
        self.majorVersion = 2 # this should be obtained from user and/or user's system
        self.minorVersion = 13
        self.versionString = self.topLevelObject.backslash + "version " + self.topLevelObject.quoteString(str(self.majorVersion) + '.' + str(self.minorVersion))
        self.versionScheme = lyo.LyEmbeddedScm(self.versionString)
        self.backend  = 'ps'
        
        if self.majorVersion >= 2:
            if self.minorVersion >= 11:
                self.backendString = '-dbackend='
            else:
                self.backendString = '--backend='
        else:
            self.backendString = '--backend='
        # I had a note that said 2.12 and > should use 'self.backendString = '--formats=' ' but doesn't seem true
        
    
    def newContext(self, newContext):
        self.storedContexts.append(self.context)
        self.context = newContext
        
    def restoreContext(self):
        try:
            self.context = self.storedContexts.pop()
        except:
            self.context = self.topLevelObject


    #------------ Set a complete Lilypond Tree from a music21 object ----------#     
    def textFromMusic21Object(self, m21ObjectIn):
        r'''
        get a proper lilypond text file for writing from a music21 object

        >>> from music21 import *
        >>> n = note.Note()
        >>> print lily.translate.LilypondConverter().textFromMusic21Object(n)
        \version "2.13" 
        color = #(define-music-function (parser location color) (string?) #{ 
                \once \override NoteHead #'color = #(x11-color $color) 
                \once \override Stem #'color = #(x11-color $color)
                \once \override Rest #'color = #(x11-color $color)
                \once \override Beam #'color = #(x11-color $color)
             #})
        \header { } 
        \score  {
              << \new Staff  = ... { \stopStaff }
               \context Staff  = ... { \startStaff c' 4  
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
        
        TODO: Add tests...
        TODO: Add test for TinyNotationStream...
        '''
        from music21 import stream
        c = m21ObjectIn.classes
        if 'Stream' in c:
            if len(m21ObjectIn.flat.variants) > 0:
                ## has variants so we need to make a deepcopy...
                m21ObjectIn = variant.makeAllVariantsReplacements(m21ObjectIn, recurse = True)
                m21ObjectIn.makeVariantBlocks()
        
        if ('Stream' not in c) or ('Measure' in c) or ('Voice' in c):
            scoreObj = stream.Score()
            partObj = stream.Part()
            # no need for measures or voices...
            partObj.insert(0, m21ObjectIn)
            scoreObj.insert(0, partObj)
            self.loadObjectFromScore(scoreObj, makeNotation = False)
        elif 'Part' in c:
            scoreObj = stream.Score()
            scoreObj.insert(0, m21ObjectIn)
            self.loadObjectFromScore(scoreObj, makeNotation = False)
        elif 'Score' in c:
            self.loadObjectFromScore(m21ObjectIn, makeNotation = False)
        elif 'Opus' in c:
            self.loadObjectFromOpus(m21ObjectIn, makeNotation = False)
        else: # treat as part...
            scoreObj = stream.Score()
            scoreObj.insert(0, m21ObjectIn)
            self.loadObjectFromScore(scoreObj, makeNotation = False)
            #raise LilyTranslateException("Unknown stream type %s." % (m21ObjectIn.__class__))
            
    
    def loadObjectFromOpus(self, opusIn = None, makeNotation = True):
        r'''
        creates a filled topLevelObject (lily.lilyObjects.LyLilypondTop)
        whose string representation accurately reflects all the Score objects
        in this Opus object.

        >>> from music21 import *
        >>> #_DOCS_SHOW fifeOpus = corpus.parse('miscFolk/americanfifeopus.abc')
        >>> #_DOCS_SHOW lpc = lily.translate.LilypondConverter()
        >>> #_DOCS_SHOW lpc.loadObjectFromOpus(fifeOpus, makeNotation = False)
        >>> #_DOCS_SHOW lpc.showPDF()
        '''
        contents = []
        lpVersionScheme = self.versionScheme        
        lpColorScheme = lyo.LyEmbeddedScm(self.colorDef)
        contents.append(lpVersionScheme)
        contents.append(lpColorScheme)

        for thisScore in opusIn.scores:
            if makeNotation is True:
                thisScore = thisScore.makeNotation(inPlace = False)
        
            lpHeader = lyo.LyLilypondHeader()
            lpScoreBlock = self.lyScoreBlockFromScore(thisScore)
            if thisScore.metadata is not None:
                self.setHeaderFromMetadata(thisScore.metadata, lpHeader = lpHeader)

            contents.append(lpHeader)
            contents.append(lpScoreBlock)
        
        lpOutputDefHead = lyo.LyOutputDefHead(defType = 'paper')
        lpOutputDefBody = lyo.LyOutputDefBody(outputDefHead = lpOutputDefHead)
        lpOutputDef = lyo.LyOutputDef(outputDefBody = lpOutputDefBody)
        contents.append(lpOutputDef)

        lpLayout = lyo.LyLayout()

        contents.append(lpLayout)
        
        self.context.contents = contents

    
    def loadObjectFromScore(self, scoreIn = None, makeNotation = True):
        r'''
        
        creates a filled topLevelObject (lily.lilyObjects.LyLilypondTop)
        whose string representation accurately reflects this Score object.
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> #_DOCS_SHOW b = corpus.parse('bach/bwv66.6')
        >>> b = _getCachedCorpusFile('bach/bwv66.6') #_DOCS_HIDE
        >>> lpc.loadObjectFromScore(b)
        >>> #print lpc.topLevelObject
        '''
        if makeNotation is True:
            scoreIn = scoreIn.makeNotation(inPlace = False)
        
        lpVersionScheme = self.versionScheme        
        lpColorScheme = lyo.LyEmbeddedScm(self.colorDef)
        lpHeader = lyo.LyLilypondHeader()
        lpScoreBlock = self.lyScoreBlockFromScore(scoreIn)
        lpOutputDefHead = lyo.LyOutputDefHead(defType = 'paper')
        lpOutputDefBody = lyo.LyOutputDefBody(outputDefHead = lpOutputDefHead)
        lpOutputDef = lyo.LyOutputDef(outputDefBody = lpOutputDefBody)
        lpLayout = lyo.LyLayout()
        contents = [lpVersionScheme, lpColorScheme, lpHeader, lpScoreBlock, lpOutputDef, lpLayout]
        
        if scoreIn.metadata is not None:
            self.setHeaderFromMetadata(scoreIn.metadata, lpHeader = lpHeader)

        

        self.context.contents = contents
        
        


    #------- return Lily objects or append to the current context -----------#
    def lyScoreBlockFromScore(self, scoreIn):
        
        lpCompositeMusic = lyo.LyCompositeMusic()
        self.newContext(lpCompositeMusic)

        # Also get the variants, and the total number of measures here and make start each staff context with { \stopStaff s1*n} where n is the number of measures.
        if hasattr(scoreIn, 'parts') and len(scoreIn.parts) > 0: # or has variants
            lpPartsAndOssiaInit = self.lyPartsAndOssiaInitFromScore(scoreIn)
            lpGroupedMusicList = self.lyGroupedMusicListFromScoreWithParts(scoreIn, scoreInit = lpPartsAndOssiaInit)
            lpCompositeMusic.groupedMusicList = lpGroupedMusicList
        else:
            # treat as a part...
            lpPrefixCompositeMusic = self.lyPrefixCompositeMusicFromStream(scoreIn)
            lpCompositeMusic.prefixCompositeMusic = lpPrefixCompositeMusic
        
        lpMusic = lyo.LyMusic(compositeMusic = lpCompositeMusic)
        lpScoreBody = lyo.LyScoreBody(music = lpMusic)
        lpScoreBlock = lyo.LyScoreBlock(scoreBody = lpScoreBody)
        self.restoreContext()
        
        return lpScoreBlock

    def lyPartsAndOssiaInitFromScore(self, scoreIn):
        '''
        Takes in a score and returns a block that starts each part context and variant context
        with an identifier and {\stopStaff s1*n} where n is the number of measures in the score.
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> s = stream.Score()
        >>> p1,p2 = stream.Part(), stream.Part()
        >>> p1.append(variant.Variant(name = 'london'))
        >>> p2.append(variant.Variant(name = 'london'))
        >>> p1.append(variant.Variant(name = 'rome'))
        >>> p2.append(variant.Variant(name = 'rome'))
        >>> p1.repeatAppend(stream.Measure(), 10)
        >>> p2.repeatAppend(stream.Measure(), 10)
        >>> p1.id = 'pa'
        >>> p2.id = 'pb'
        >>> s.append(p1)
        >>> s.append(p2)
        >>> print lpc.lyPartsAndOssiaInitFromScore(s)
        \\new Staff  = pa { \stopStaff } 
        \\new Staff  = londonpa
                    \with {
                          \\remove "Time_signature_engraver"
                          alignAboveContext = #"pa"
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                        }
                 { \stopStaff } 
        \\new Staff  = romepa 
                    \with {
                          \\remove "Time_signature_engraver"
                          alignAboveContext = #"pa"
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                        }
                 { \stopStaff } 
        \\new Staff  = pb { \stopStaff } 
        \\new Staff  = londonpb 
                    \with {
                          \\remove "Time_signature_engraver"
                          alignAboveContext = #"pb"
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                        }
                 { \stopStaff } 
        \\new Staff  = romepb 
                    \with {
                          \\remove "Time_signature_engraver"
                          alignAboveContext = #"pb"
                          fontSize = #-3
                          \override StaffSymbol #'staff-space = #(magstep -3)
                          \override StaffSymbol #'thickness = #(magstep -3)
                          \override TupletBracket #'bracket-visibility = ##f
                          \override TupletNumber #'stencil = ##f
                          \override Clef #'transparent = ##t
                        }
                 { \stopStaff } 
        <BLANKLINE>
        '''
        lpMusicList = lyo.LyMusicList()

        musicList = []


        optionalContextMod = r'''
            \with {
                  \remove "Time_signature_engraver"
                  alignAboveContext = #"%s"
                  fontSize = #-3
                  \override StaffSymbol #'staff-space = #(magstep -3)
                  \override StaffSymbol #'thickness = #(magstep -3)
                  \override TupletBracket #'bracket-visibility = ##f
                  \override TupletNumber #'stencil = ##f
                  \override Clef #'transparent = ##t
                  \consists "Default_bar_line_engraver"
                }
        '''

        lpMusic = '{ \stopStaff %s}'

        for p in scoreIn.parts:
            partIdText = makeLettersOnlyId(p.id)
            partId = lyo.LyOptionalId(partIdText)
            spacerDuration = self.getLySpacersFromStream(p)
            lpPrefixCompositeMusicPart = lyo.LyPrefixCompositeMusic(type = 'new',
                                                            optionalId = partId,
                                                            simpleString = 'Staff',
                                                            music = lpMusic % spacerDuration)
            #lpPrefixCompositeMusicPart.optionalContextMod = r'''
            #    \with {
            #          \consists "Default_bar_line_engraver"
            #    }
            #'''

            musicList.append(lpPrefixCompositeMusicPart)  
            
            variantsAddedForPart = []
            for v in p.variants:
                variantName = v.groups[0]
                if not variantName in variantsAddedForPart:
                    self.addedVariants.append(variantName)
                    variantsAddedForPart.append(variantName)
                    variantId = lyo.LyOptionalId(makeLettersOnlyId(variantName)+partIdText)
                    lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(type = 'new',
                                                                optionalId = variantId,
                                                                simpleString = 'Staff',
                                                                music = lpMusic % spacerDuration)
                    
                    lpPrefixCompositeMusicVariant.optionalContextMod = optionalContextMod % partIdText
                    musicList.append(lpPrefixCompositeMusicVariant)

        lpMusicList.contents = musicList

        return lpMusicList

    
    def getLySpacersFromStream(self, streamIn, measuresOnly = True):
        '''
        >>> from music21 import *
        >>> m1 = stream.Measure(converter.parse("a2.", "3/4"))
        >>> m2 = stream.Measure(converter.parse("b2.", "3/4"))
        >>> m3 = stream.Measure(converter.parse("a1", "4/4"))
        >>> m4 = stream.Measure(converter.parse("b1", "4/4"))
        >>> m5 = stream.Measure(converter.parse("c1", "4/4"))
        >>> m6 = stream.Measure(converter.parse("a2", "2/4"))
        >>> streamIn = stream.Stream([m1, m2, m3, m4, m5, m6])
        >>> lpc = lily.translate.LilypondConverter()
        >>> print lpc.getLySpacersFromStream(streamIn)
        s2. s2. s1 s1 s1 s2

        '''

        returnString = ''
        mostRecentDur = ''
        recentDurCount = 0
        for el in streamIn:
            if not "Measure" in el.classes:
                continue
            if el.duration.quarterLength == 0.0:
                continue

            try:
                dur = str(self.lyMultipliedDurationFromDuration(el.duration))
            except:
                dur = '2.'
            #if dur == mostRecentDur:
            #    recentDurCount += 1
            #else:
            returnString = returnString + 's'+ dur
            #    mostRecentDur = dur
            #    recentDurCount = 0

        #if recentDurCount != 0:
         #   returnString = returnString + '*' + str(recentDurCount)

        return returnString


    def lyGroupedMusicListFromScoreWithParts(self, scoreIn, scoreInit = None):
        r'''
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> #_DOCS_SHOW b = corpus.parse('bach/bwv66.6')
        >>> b = _getCachedCorpusFile('bach/bwv66.6') #_DOCS_HIDE
        >>> lpPartsAndOssiaInit = lpc.lyPartsAndOssiaInitFromScore(b)
        >>> lpGroupedMusicList = lpc.lyGroupedMusicListFromScoreWithParts(b, scoreInit = lpPartsAndOssiaInit)
        >>> print lpGroupedMusicList
        <BLANKLINE>
        << \new Staff  = Soprano { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. } 
          \new Staff  = Alto { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. } 
          \new Staff  = Tenor { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. } 
          \new Staff  = Bass { \stopStaff s4 s1 s1 s1 s1 s1 s1 s1 s1 s2. } 
        <BLANKLINE>
        \context Staff  = Soprano { \startStaff \partial 32*8 
               \clef "treble" 
               \key fis \minor 
               \time 4/4
               \once \override Stem #'direction = #DOWN 
               cis'' 8  
               \once \override Stem #'direction = #DOWN 
               b' 8  
               | %{ end measure 0 %} 
               \once \override Stem #'direction = #UP 
               a' 4  
               \once \override Stem #'direction = #DOWN 
               b' 4  
               \once \override Stem #'direction = #DOWN 
               cis'' 4  \fermata  
               \once \override Stem #'direction = #DOWN 
               e'' 4  
               | %{ end measure 1 %} 
               \once \override Stem #'direction = #DOWN 
               cis'' 4  
               ...
        } 
        <BLANKLINE>
        \context Staff  = Alto { \startStaff \partial 32*8 
            \clef "treble"...
            \once \override Stem #'direction = #UP 
            e' 4  
            | %{ end measure 0 %} 
            \once \override Stem #'direction = #UP 
            fis' 4  
            \once \override Stem #'direction = #UP 
            e' 4  
        ...
        } 
        <BLANKLINE>
        >>
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
                compositeMusicList.append(self.lyPrefixCompositeMusicFromStream(p, type='context', beforeMatter = 'startStaff'))

        self.restoreContext()
        lpMusicList.contents = compositeMusicList
        
        return lpGroupedMusicList

    
    def lyNewLyricsFromStream(self, streamIn, sId = None):
        '''
        returns a LyNewLyrics object
        This is a little bit of a hack. This should be switched over to using a prefixed context thing with \new Lyric = "id" \with { } {}

        >>> from music21 import *
        >>> 

        '''

        lyricsDict = streamIn.lyrics(skipTies = True)
        
        if sId is None:
            sId = makeLettersOnlyId(streamIn.id)
        streamId = "#"+ lyo.LyObject().quoteString(sId)

        lpGroupedMusicLists = []
        for lyricNum in sorted(lyricsDict):
            lyricList = []
            lpAlignmentProperty = lyo.LyPropertyOperation(mode = 'set', value1 = 'alignBelowContext', value2 = streamId)
            lyricList.append(lpAlignmentProperty)
            inWord = False
            for el in lyricsDict[lyricNum]:
                if el is None and inWord:
                    text = ' _ '
                elif el is None and inWord is False:
                    text = ' _ '
                elif el.text == '':
                    text = ' _ '
                else:
                    if el.syllabic == 'end':
                        text = el.text + '__'
                        inWord = False
                    elif el.syllabic == 'begin' or el.syllabic == 'middle':
                        text = el.text + ' --'
                        inWord = True
                    else:
                        text = el.text
                      
                lpLyricElement = lyo.LyLyricElement(text)
                lyricList.append(lpLyricElement)

            lpLyricList = lyo.LyMusicList(lyricList)
            
            lpSequentialMusic = lyo.LySequentialMusic(musicList = lpLyricList)
            lpGroupedMusicList = lyo.LyGroupedMusicList(sequentialMusic = lpSequentialMusic)
            lpGroupedMusicLists.append(lpGroupedMusicList)
        
        lpNewLyrics = lyo.LyNewLyrics(groupedMusicLists = lpGroupedMusicLists)

        return lpNewLyrics

    def lySequentialMusicFromStream(self, streamIn, beforeMatter = None):
        r'''
        returns a LySequentialMusic object from a stream

        >>> from music21 import *
        >>> c = converter.parse('tinynotation: 3/4 C4 D E F2.')
        >>> lpc = lily.translate.LilypondConverter()
        >>> lySequentialMusicOut = lpc.lySequentialMusicFromStream(c)
        >>> lySequentialMusicOut
        <music21.lily.lilyObjects.LySequentialMusic object at 0x...>
        >>> print lySequentialMusicOut
        { \time 3/4
         c 4  
         d 4  
         e 4  
         f 2.  
        } 
        '''
        musicList = []

        lpMusicList = lyo.LyMusicList(contents = musicList)
        lpSequentialMusic = lyo.LySequentialMusic(musicList = lpMusicList, beforeMatter = beforeMatter)
        self.newContext(lpMusicList)    
        self.appendObjectsToContextFromStream(streamIn)
                    
        lyObject = self.closeMeasure()
        if lyObject is not None:
            musicList.append(lyObject)    
        
        self.restoreContext()
        return lpSequentialMusic

    def lyPrefixCompositeMusicFromStream(self, streamIn, contextType = None, type = None, beforeMatter = None):
        r'''
        returns an LyPrefixCompositeMusic object from
        a stream (generally a part, but who knows...)

        >>> from music21 import *
        >>> c = converter.parse('tinynotation: 3/4 C4 D E F2.')
        >>> lpc = lily.translate.LilypondConverter()
        >>> lyPrefixCompositeMusicOut = lpc.lyPrefixCompositeMusicFromStream(c, contextType='Staff')
        >>> lyPrefixCompositeMusicOut 
        <music21.lily.lilyObjects.LyPrefixCompositeMusic object at 0x...>
        >>> print lyPrefixCompositeMusicOut
        \new Staff = ...{ \time 3/4
           c 4  
           d 4  
           e 4  
           f 2.  
          } 
        '''
        optionalId = None
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
        

        lpNewLyrics = self.lyNewLyricsFromStream(streamIn, sId = makeLettersOnlyId(streamIn.id))

        lpSequentialMusic = self.lySequentialMusicFromStream(streamIn, beforeMatter = beforeMatter)
        lpGroupedMusicList = lyo.LyGroupedMusicList(sequentialMusic = lpSequentialMusic)
        lpCompositeMusic = lyo.LyCompositeMusic(groupedMusicList = lpGroupedMusicList, newLyrics = lpNewLyrics)
        lpMusic = lyo.LyMusic(compositeMusic = lpCompositeMusic)

        if type is None:
            type = 'new'

        if optionalId is None:
            lpPrefixCompositeMusic = lyo.LyPrefixCompositeMusic(type = type,
                                                            simpleString = newContext,
                                                            music = lpMusic) 
        else:
            lpPrefixCompositeMusic = lyo.LyPrefixCompositeMusic(type = type,
                                                            optionalId = optionalId,
                                                            simpleString = newContext,
                                                            music = lpMusic)    
        return lpPrefixCompositeMusic


    def appendObjectsToContextFromStream(self, streamObject):
        r'''
        takes a Stream and appends all the elements in it to the current
        context's .contents list, and deals with creating Voices in it. It also deals with
        variants in it.
        
        (should eventually replace the main Score parts finding tools)
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lyo.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.context.contents
        []
        >>> c = converter.parse('tinynotation: 3/4 c4 d- e#')
        >>> lpc.appendObjectsToContextFromStream(c)
        >>> print lpc.context.contents
        [<music21.lily.lilyObjects.LyEmbeddedScm...>, <music21.lily.lilyObjects.LySimpleMusic...>, <music21.lily.lilyObjects.LySimpleMusic...>, <music21.lily.lilyObjects.LySimpleMusic...]
        >>> print lpc.context
        \time 3/4
        c' 4  
        des' 4  
        eis' 4  
        <BLANKLINE>


        >>> v1 = stream.Voice()
        >>> v1.append(note.Note("C5", quarterLength = 4.0))
        >>> v2 = stream.Voice()
        >>> v2.append(note.Note("C#5", quarterLength = 4.0))
        >>> m = stream.Measure()
        >>> m.insert(0, v1)
        >>> m.insert(0, v2)
        >>> lpMusicList = lyo.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.appendObjectsToContextFromStream(m)
        >>> print lpc.context # internal spaces removed...
          << \new Voice { c'' 1  
                  } 
           \new Voice { cis'' 1  
                  } 
            >>        
        '''        
        for groupedElements in streamObject.groupElementsByOffset():
            #print groupedElements

            if len(groupedElements) == 1: # one thing at that moment...
                el = groupedElements[0]
                el.activeSite = streamObject
                self.appendM21ObjectToContext(el)
            else: # voices or other More than one thing at once...
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
                
                if len(variantList) > 0:
                    for v in variantList:
                        v.activeSite = streamObject
                    self.appendContextFromVariant(variantList, activeSite = streamObject, coloredVariants = self.coloredVariants)

                if len(voiceList) > 0:
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

                if len(otherList) > 0:
                    for el in otherList:
                        self.appendM21ObjectToContext(el)
    

    def appendM21ObjectToContext(self, thisObject):
        '''
        converts any type of object into a lilyObject of LyMusic (
        LySimpleMusic, LyEmbeddedScm etc.) type
        '''
        if thisObject in self.doNotOutput:
            return
        
        ### treat complex duration objects as multiple objects
        c = thisObject.classes

        
        if 'Stream' not in c and thisObject.duration.type == 'complex':
            thisObjectSplit = thisObject.splitAtDurations()
            for subComponent in thisObjectSplit:
                subComponent.activeSite = thisObject.activeSite
                self.appendM21ObjectToContext(subComponent)
            return

        contextObject = self.context
        currentMusicList = contextObject.contents
        if hasattr(thisObject, 'startTransparency') and thisObject.startTransparency is True:
            # old hack, replace with the better "hidden" attribute
            lyScheme = lyo.LyEmbeddedScm(self.transparencyStartScheme)
            currentMusicList.append(lyScheme)
            
        lyObject = None
        if "Measure" in c:
            ## lilypond does not put groups around measures...
            ## it does however need barline ends
            ## also, if variantMode is True, the last note in each "measure" should have \noBeam
            closeMeasureObj = self.closeMeasure() # could be None
            if closeMeasureObj is not None:
                currentMusicList.append(closeMeasureObj)
                closeMeasureObj.setParent(contextObject)

            padObj = self.getSchemeForPadding(thisObject)
            if padObj is not None:
                currentMusicList.append(padObj)
                padObj.setParent(contextObject)

            ## here we go!
            self.appendObjectsToContextFromStream(thisObject)            
            self.currentMeasure = thisObject

        elif "Stream" in c:
            #try:
            lyObject = self.lyPrefixCompositeMusicFromStream(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
            #except AttributeError as ae:
            #    raise Exception("Cannot parse %s: %s" % (thisObject, str(ae)))
        elif "Note" in c or "Rest" in c:
            self.appendContextFromNoteOrRest(thisObject)
        elif "Chord" in c:
            lyObject = self.lySimpleMusicFromChord(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif "Clef" in c:
            lyObject = self.lyEmbeddedScmFromClef(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif "KeySignature" in c:
            lyObject = self.lyEmbeddedScmFromKeySignature(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif "TimeSignature" in c and self.variantMode is False:
            lyObject = self.lyEmbeddedScmFromTimeSignature(thisObject)
            currentMusicList.append(lyObject)
            lyObject.setParent(contextObject)
        elif "Variant" in c:
            self.appendContextFromVariant(thisObject, coloredVariants = self.coloredVariants)
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
        
        >>> from music21 import *
        >>> n = note.Note("C#4")
        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lily.lilyObjects.LyMusicList()
        >>> lpc.context = lpMusicList 
        >>> lpc.appendContextFromNoteOrRest(n)
        >>> print lpMusicList
        cis' 4  
        <BLANKLINE>


        >>> n2 = note.Note("D#4")
        >>> n2.duration.quarterLength = 0.3333333333333
        >>> n2.duration.tuplets[0].type = 'start'
        >>> n3 = note.Note("E4")
        >>> n3.duration.quarterLength = 0.3333333333333
        >>> n4 = note.Note("F4")
        >>> n4.duration.quarterLength = 0.3333333333333
        >>> n4.duration.tuplets[0].type = 'stop'
        
        >>> n5 = note.Note("F#4")
        
        >>> lpc.appendContextFromNoteOrRest(n2)
        >>> lpc.appendContextFromNoteOrRest(n3)
        >>> lpc.appendContextFromNoteOrRest(n4)
        >>> lpc.appendContextFromNoteOrRest(n5)        
        
        >>> print lpc.context
        cis' 4  
        \times 2/3 { dis' 8  
           e' 8  
           f' 8  
            } 
        <BLANKLINE>
        fis' 4  
        <BLANKLINE>

        '''
        if self.variantMode is True:
            #Then should attach \noBeam to note if it is the last note
            if "NotRest" in noteOrRest.classes:
                n = noteOrRest
                activeSite = n.activeSite
                if n.getOffsetBySite(activeSite) + n.duration.quarterLength == activeSite.duration.quarterLength:
                    pass

        self.setContextForTupletStart(noteOrRest)
        #self.appendBeamCode(noteOrRest)
        self.appendStemCode(noteOrRest)        

        lpSimpleMusic = self.lySimpleMusicFromNoteOrRest(noteOrRest)
        self.context.contents.append(lpSimpleMusic)
        lpSimpleMusic.setParent(self.context)
        self.setContextForTupletStop(noteOrRest)

    
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
        
        >>> from music21 import *
        >>> conv = lily.translate.LilypondConverter()

        >>> n0 = note.Note("D#5")
        >>> n0.pitch.accidental.displayType = 'always'
        >>> n0.pitch.accidental.displayStyle = 'parentheses'
        >>> n0.editorial.color = 'blue'
        >>> sm = conv.lySimpleMusicFromNoteOrRest(n0)
        >>> print sm
        \color "blue" dis'' ! ? 4

        '''

        c = noteOrRest.classes

        simpleElementParts = []
        if noteOrRest.editorial is not None:
            if noteOrRest.editorial.color:
                simpleElementParts.append(noteOrRest.editorial.colorLilyStart())
        
        if 'Note' in c:
            lpPitch = self.lyPitchFromPitch(noteOrRest.pitch)
            simpleElementParts.append(lpPitch)
            if noteOrRest.pitch.accidental is not None:
                if noteOrRest.pitch.accidental.displayType == 'always':
                    simpleElementParts.append('! ')
                if noteOrRest.pitch.accidental.displayStyle == 'parentheses':
                    simpleElementParts.append('? ')
        elif "SpacerRest" in c:
            simpleElementParts.append("s ")
        elif 'Rest' in c:
            if noteOrRest.hideObjectOnPrint is True:
                simpleElementParts.append("s ")
            else:
                simpleElementParts.append("r ")


        lpMultipliedDuration = self.lyMultipliedDurationFromDuration(noteOrRest.duration)
        simpleElementParts.append(lpMultipliedDuration)
        simpleElement = lyo.LySimpleElement(parts = simpleElementParts)

        postEvents = self.postEventsFromObject(noteOrRest)
        
        evc = lyo.LyEventChord(simpleElement, postEvents = postEvents)
        mlSM = lyo.LySimpleMusic(eventChord = evc)
        
        return mlSM

    def appendBeamCode(self, noteOrChord):
        r'''
        Adds an LyEmbeddedScm object to the context's contents if the object's has a .beams
        attribute.
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lyo.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.context.contents
        []
        >>> n1 = note.Note(quarterLength = 0.25)
        >>> n2 = note.Note(quarterLength = 0.25)
        >>> n1.beams.fill(2, 'start')
        >>> n2.beams.fill(2, 'stop')

        >>> lpc.appendBeamCode(n1)
        >>> print lpc.context.contents
        [<music21.lily.lilyObjects.LyEmbeddedScm object at 0x...>, <music21.lily.lilyObjects.LyEmbeddedScm object at 0x...>]
        >>> print lpc.context
        \set stemLeftBeamCount = #0
        \set stemRightBeamCount = #2
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
                        else: # better wrong direction than none
                            rightBeams += 1
            beamText = r'''\set stemLeftBeamCount = #%d''' % leftBeams
            lpBeamScheme = lyo.LyEmbeddedScm(beamText)
            self.context.contents.append(lpBeamScheme)
            lpBeamScheme.setParent(self.context)
            beamText = r'''\set stemRightBeamCount = #%d''' % rightBeams
            lpBeamScheme = lyo.LyEmbeddedScm(beamText)
            self.context.contents.append(lpBeamScheme)
            lpBeamScheme.setParent(self.context)

    def appendStemCode(self, noteOrChord):
        r'''
        Adds an LyEmbeddedScm object to the context's contents if the object's stem direction
        is set (currrently, only "up" and "down" are supported).
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> lpMusicList = lyo.LyMusicList()
        >>> lpc.context = lpMusicList
        >>> lpc.context.contents
        []
        >>> n = note.Note()
        >>> n.stemDirection = 'up'
        >>> lpc.appendStemCode(n)
        >>> print lpc.context.contents
        [<music21.lily.lilyObjects.LyEmbeddedScm object at 0x...>]
        >>> print lpc.context.contents[0]
        \once \override Stem #'direction = #UP
        '''
        if hasattr(noteOrChord, 'stemDirection') and noteOrChord.stemDirection is not None:
            stemDirection = noteOrChord.stemDirection.upper()
            if stemDirection in ['UP', 'DOWN']:
                stemFile = r'''\once \override Stem #'direction = #%s ''' % stemDirection
                lpStemScheme = lyo.LyEmbeddedScm(stemFile)
                self.context.contents.append(lpStemScheme)
                lpStemScheme.setParent(self.context)


    def lySimpleMusicFromChord(self, chordObj):
        '''
        
        >>> from music21 import *
        >>> conv = lily.translate.LilypondConverter()
        >>> c1 = chord.Chord(["C#2", "E4", "D#5"])
        >>> c1.quarterLength = 3.5
        >>> c1.pitches[2].accidental.displayType = 'always'
        >>> print conv.lySimpleMusicFromChord(c1)
         < cis, e' dis''  !  > 2.. 
        '''
        #self.appendBeamCode(chordObj)
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
            lpChordElement = lyo.LyChordBodyElement(parts = chordBodyElementParts)
            chordBodyElements.append(lpChordElement)
        lpChordBody = lyo.LyChordBody(chordBodyElements = chordBodyElements)
        lpMultipliedDuration = self.lyMultipliedDurationFromDuration(chordObj.duration)

        postEvents = self.postEventsFromObject(chordObj)

        lpNoteChordElement = lyo.LyNoteChordElement(chordBody = lpChordBody,
                                                    optionalNoteModeDuration = lpMultipliedDuration,
                                                    postEvents = postEvents)
        evc = lyo.LyEventChord(noteChordElement = lpNoteChordElement)
        mlSM = lyo.LySimpleMusic(eventChord = evc)
        return mlSM

        
    def postEventsFromObject(self, generalNote):
        '''
        attaches events that apply to notes and chords (and some other things) equally
        '''
        
        postEvents = []

        # remove this hack once lyrics work 
        #if generalNote.lyric is not None: # hack that uses markup...
        #    postEvents.append(r'_\markup { "' + generalNote.lyric + '" }\n ')
        # consider this hack removed. Yeah!
        
        if (hasattr(generalNote, 'tie') and generalNote.tie is not None):
            if (generalNote.tie.type != "stop"):
                postEvents.append("~ ")


        if (hasattr(generalNote, 'expressions') and generalNote.expressions):
            for thisExpression in generalNote.expressions:
                if 'Fermata' in thisExpression.classes:
                    postEvents.append(r'\fermata ')        
        return postEvents

    def lyPitchFromPitch(self, pitch):
        '''
        converts a music21.pitch.Pitch object to a lily.lilyObjects.LyPitch
        object.
        '''
        
        baseName = self.baseNameFromPitch(pitch)
        octaveModChars = self.octaveCharactersFromPitch(pitch)
        lyPitch = lyo.LyPitch(baseName, octaveModChars)
        return lyPitch

    def baseNameFromPitch(self, pitch):
        '''
        returns a string of the base name (including accidental)
        for a music21 pitch
        '''
        
        baseName = pitch.step.lower()
        if pitch.accidental is not None:
            if pitch.accidental.name in self.accidentalConvert:
                baseName += self.accidentalConvert[pitch.accidental.name]
        return baseName
        
    
    def octaveCharactersFromPitch(self, pitch):
        '''
        returns a string of single-quotes or commas or "" representing
        the octave of a :class:`~music21.pitch.Pitch` object
        '''
        
        spio = pitch.implicitOctave
        if (spio < 3):
            correctedOctave = 3 - spio
            octaveModChars = u',' * correctedOctave #  C2 = c,  C1 = c,,
        else:
            correctedOctave = spio - 3
            octaveModChars  = u'\'' * correctedOctave # C4 = c', C5 = c''  etc.
        return octaveModChars        

    def lyMultipliedDurationFromDuration(self, durationObj):        
        try:
            number_type = duration.convertTypeToNumber(durationObj.type) # module call
        except duration.DurationException as de:
            raise LilyTranslateException("DurationException for durationObject %s: %s" % (durationObj, de))
        
        if number_type < 1:
            if number_type == 0.5:
                number_type = r'\breve'
            elif number_type == 0.25:
                number_type = r'\longa'
            else:
                # no support for maxima...
                number_type = int(number_type * 16)
        
        try:
            stenoDuration = lyo.LyStenoDuration(number_type, int(durationObj.dots))
            multipliedDuration = lyo.LyMultipliedDuration(stenoDuration)
        except duration.DurationException as de:
            raise LilyTranslateException("DurationException: Cannot translate durationObject %s: %s" % (durationObj, de))
        return multipliedDuration
    
    def lyEmbeddedScmFromClef(self, clefObj):
        r'''
        converts a Clef object to a
        lilyObjects.LyEmbeddedScm object
        
        >>> from music21 import *
        >>> tc = clef.TrebleClef()
        >>> conv = lily.translate.LilypondConverter()
        >>> lpEmbeddedScm = conv.lyEmbeddedScmFromClef(tc)
        >>> print lpEmbeddedScm 
        \clef "treble" 
        
        '''
        
        c = clefObj.classes
        if 'Treble8vbClef' in c:
            lilyName = 'treble_8'
        elif 'TrebleClef' in c:
            lilyName = "treble"
        elif 'BassClef' in c:
            lilyName = "bass"
        elif 'AltoClef' in c:
            lilyName = 'alto'
        elif 'TenorClef' in c:
            lilyName = 'tenor'
        elif 'SopranoClef' in c:
            lilyName = 'soprano'
        else:
            environLocal.printDebug('got a clef that lilypond does not know what to do with: %s' % clefObj)
            lilyName = ""        
        
        lpEmbeddedScm = lyo.LyEmbeddedScm()
        clefScheme = lpEmbeddedScm.backslash + 'clef ' + lpEmbeddedScm.quoteString(lilyName) + lpEmbeddedScm.newlineIndent
        lpEmbeddedScm.content = clefScheme
        return lpEmbeddedScm

    def lyEmbeddedScmFromKeySignature(self, keyObj):
        r'''
        converts a Key or KeySignature object
        to a lilyObjects.LyEmbeddedScm object

        >>> from music21 import *
        >>> d = key.KeySignature(-1)
        >>> d.mode = 'minor'
        >>> conv = lily.translate.LilypondConverter()
        >>> lpEmbeddedScm = conv.lyEmbeddedScmFromKeySignature(d)
        >>> print lpEmbeddedScm
        \key d \minor
        
        Major is assumed:
        
        >>> fsharp = key.KeySignature(6)
        >>> print conv.lyEmbeddedScmFromKeySignature(fsharp)
        \key fis \major
        
        '''
        (p, m) = keyObj.pitchAndMode
        if m is None:
            m = "major"
        pn = self.baseNameFromPitch(p)

        lpEmbeddedScm = lyo.LyEmbeddedScm()
        keyScheme = lpEmbeddedScm.backslash + 'key ' + pn + ' ' + lpEmbeddedScm.backslash + m + ' ' + lpEmbeddedScm.newlineIndent
        lpEmbeddedScm.content = keyScheme
        return lpEmbeddedScm

    def lyEmbeddedScmFromTimeSignature(self, ts):
        r'''
        convert a :class:`~music21.meter.TimeSignature` object 
        to a lilyObjects.LyEmbeddedScm object

        >>> from music21 import *
        >>> ts = meter.TimeSignature('3/4')
        >>> conv = lily.translate.LilypondConverter()
        >>> print conv.lyEmbeddedScmFromTimeSignature(ts)
        \time 3/4
        '''
        lpEmbeddedScm = lyo.LyEmbeddedScm()
        keyScheme = lpEmbeddedScm.backslash + 'time ' + ts.ratioString + lpEmbeddedScm.newlineIndent
        lpEmbeddedScm.content = keyScheme
        return lpEmbeddedScm


    def setContextForTupletStart(self, inObj):
        '''
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
        if inObj.duration.tuplets is None or len(inObj.duration.tuplets) == 0:
            return None
        elif inObj.duration.tuplets[0].type == 'start':
            numerator = str(int(inObj.duration.tuplets[0].tupletNormal[0]))
            denominator = str(int(inObj.duration.tuplets[0].tupletActual[0]))            
            lpMusicList = self.setContextForTimeFraction(numerator, denominator)
        else:
            return None

    def setContextForTimeFraction(self, numerator, denominator):
        '''
        Explicitly starts a new context for scaled music (tuplets, etc.)
        for the given numerator and denominator
        
        Returns an lpMusicList object contained in an lpSequentialMusic object
        in an lpPrefixCompositeMusic object which sets the times object to a particular
        fraction.
        '''
        fraction = numerator + '/' + denominator
        lpMusicList = lyo.LyMusicList()
        lpSequentialMusic = lyo.LySequentialMusic(musicList = lpMusicList)
        ## technically needed, but we can speed things up
        #lpGroupedMusicList = lyo.LyGroupedMusicList(sequentialMusic = lpSequentialMusic)
        #lpCompositeMusic = lyo.LyCompositeMusic(groupedMusicList = lpGroupedMusicList)
        #lpMusic = lyo.LyMusic(compositeMusic = lpCompositeMusic)
        lpPrefixCompositeMusic = lyo.LyPrefixCompositeMusic(type='times', 
                                                            fraction = fraction,
                                                            music = lpSequentialMusic)
        self.context.contents.append(lpPrefixCompositeMusic)
        lpPrefixCompositeMusic.setParent(self.context)
        self.newContext(lpMusicList)
        return lpMusicList

    def setContextForTupletStop(self, inObj):
        '''
        Reverse of setContextForTupletStart
        '''
        if len(inObj.duration.tuplets) == 0:
            return
        elif inObj.duration.tuplets[0].type == 'stop':
            self.restoreContext()
        else:
            return None

    def appendContextFromVariant(self, variantObjectOrList, activeSite = None, coloredVariants = False):
        '''
        '''
        musicList = []
        
        if isinstance(variantObjectOrList, variant.Variant):
            variantObject = variantObjectOrList
            replacedElements = variantObject.replacedElements(activeSite)
            lpPrefixCompositeMusicVariant = self.lyPrefixCompositeMusicFromVariant(variantObject, replacedElements, coloredVariants = coloredVariants)
            lpSequentialMusicStandard = self.lySequentialMusicFromStream(replacedElements)
            musicList.append(lpPrefixCompositeMusicVariant)
            musicList.append(lpSequentialMusicStandard)
        
        elif type(variantObjectOrList) is list:
            longestReplacementLength = -1
            variantDict = {}
            for variantObject in variantObjectOrList:
                variantName = variantObject.groups[0]
                if variantName in variantDict:
                    variantDict[variantName].append(variantObject)
                else:
                    variantDict[variantName] = [variantObject]
            

            for key in variantDict:
                variantList = variantDict[key]
                if len(variantList) == 1:
                    variantObject = variantList[0]
                    replacedElements = variantObject.replacedElements(activeSite)
                    lpPrefixCompositeMusicVariant = self.lyPrefixCompositeMusicFromVariant(variantObject, replacedElements, coloredVariants = coloredVariants)
                    musicList.append(lpPrefixCompositeMusicVariant)
                else:
                    lpPrefixCompositeMusicVariant, replacedElements = self.lyPrefixCompositeMusicFromRelatedVariants(variantList, activeSite = activeSite, coloredVariants = coloredVariants)
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

    
    def lyPrefixCompositeMusicFromRelatedVariants(self, variantList, activeSite = None, coloredVariants = False):
        '''

        >>> from music21 import *
        >>> s1 = converter.parse("a4 a a a  a1", "4/4")
        >>> s2 = converter.parse("b4 b b b", "4/4")
        >>> s3 = converter.parse("c4 c c c", "4/4")
        >>> s4 = converter.parse("d4 d d d", "4/4")
        >>> s5 = converter.parse("e4 e e e  f f f f  g g g g  a a a a  b b b b", "4/4")

        >>> for s in [ s1, s2, s3, s4, s5]:
        ...     s.makeMeasures(inPlace = True)

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

        >>> variantList = [v4,v1,v3,v2]
        >>> for v in variantList :
        ...     v.groups = ['london']
        ...     activeSite.insert(0.0, v)


        >>> lpc = lily.translate.LilypondConverter()

        >>> print lpc.lyPrefixCompositeMusicFromRelatedVariants(variantList, activeSite = activeSite)[0]
        \\new Staff  = ... 
                \with {
                      \\remove "Time_signature_engraver"
                      alignAboveContext = #"..."
                      fontSize = #-3
                      \override StaffSymbol #'staff-space = #(magstep -3)
                      \override StaffSymbol #'thickness = #(magstep -3)
                      \override TupletBracket #'bracket-visibility = ##f
                      \override TupletNumber #'stencil = ##f
                      \override Clef #'transparent = ##t
                    } 
                     { { \\times 1/2 {\startStaff \clef "treble" 
            \\time 4/4
            \clef "treble"
            a' 4  
            a' 4  
            a' 4  
            a' 4  
            | %{ end measure 1 %}
            a' 1
            \\bar "|."  %{ end measure 2 %}
             \stopStaff}
             }
        <BLANKLINE>
          {\startStaff \clef "treble" 
            \\time 4/4
            b' 4  
            b' 4  
            b' 4  
            b' 4  
            \\bar "|."  %{ end measure 1 %} 
             \stopStaff}
        <BLANKLINE>
          {\startStaff \clef "treble" 
            \\time 4/4
            c' 4  
            c' 4  
            c' 4  
            c' 4  
            \\bar "|."  %{ end measure 1 %} 
             \stopStaff}
        <BLANKLINE>
          s 1  
          {\startStaff \clef "treble" 
            \\time 4/4
            d' 4  
            d' 4  
            d' 4  
            d' 4  
            \\bar "|."  %{ end measure 1 %} 
             \stopStaff}
        <BLANKLINE>
           } 
        <BLANKLINE>

        '''
        
        # Order List
        
        def findOffsetOfFirstNonSpacerElement(inputStream):
            for el in inputStream:
                if "SpacerRest" in el.classes:
                    pass
                else:
                    return el.getOffsetBySite(inputStream)

        variantList.sort(key = lambda v: findOffsetOfFirstNonSpacerElement(v._stream))

        
        # Stuff that can be done on the first element only (clef, new/old, id, color)
        replacedElements = variantList[0].replacedElements(activeSite)
        replacedElementsClef = replacedElements[0].getContextByClass('Clef')

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
        variantId = lyo.LyOptionalId(makeLettersOnlyId(variantName)+containerId)

        if coloredVariants is True:
            color = self.variantColors[self.addedVariants.index(variantName) % 6]

        

        #######################

        musicList = []
        highestOffsetSoFar = 0.0
        
        self.variantMode = True

        for v in variantList:
            # For each variant in the list, we make a lilypond representation of the
            # spacer between this variant and the previous if it is non-zero and append it
            # Then we strip off the spacer and make a lilypond representation of the variant
            # with the appropriate tupletting if any and append that.
            # At the end we make a new lilypond context for it and return it.

            firstOffset = findOffsetOfFirstNonSpacerElement(v._stream)

            if firstOffset < highestOffsetSoFar:
                raise LilyTranslateException("Should not have overlapping variants.")
            else:
                spacerDuration = firstOffset - highestOffsetSoFar
                highestOffsetSoFar = v.replacementDuration + firstOffset

            # make spacer with spacerDuration and append
            if spacerDuration > 0.0:
                spacer = note.SpacerRest()
                spacer.duration.quarterLength = spacerDuration
                lySpacer = self.lySimpleMusicFromNoteOrRest(spacer)
                musicList.append(lySpacer)

            if coloredVariants is True:
                for n in v._stream.flat.notesAndRests:
                    n.editorial.color = color# make thing (with or without fraction)

            # Strip off spacer
            endOffset = v.containedHighestTime
            vStripped = variant.Variant(v._stream.getElementsByOffset(firstOffset,
                                        offsetEnd = endOffset))
            vStripped.replacementDuration = v.replacementDuration


            replacedElementsLength = vStripped.replacementDuration
            variantLength = vStripped.containedHighestTime - firstOffset


            if variantLength != replacedElementsLength:
                numerator, denominator = common.decimalToTuplet(replacedElementsLength/variantLength)
                fraction = str(numerator) + '/' + str(denominator)
                lpOssiaMusicVariantPreFraction = self.lyOssiaMusicFromVariant(vStripped)
                lpVariantTuplet = lyo.LyPrefixCompositeMusic(type='times', 
                                                            fraction = fraction,
                                                            music = lpOssiaMusicVariantPreFraction)

                lpOssiaMusicVariant = lyo.LySequentialMusic(musicList = lpVariantTuplet)
            else:
                lpOssiaMusicVariant = self.lyOssiaMusicFromVariant(vStripped)

            musicList.append(lpOssiaMusicVariant)

            longestVariant = v

        # The last variant in the iteration should have the highestOffsetSoFar,
        # so it has the appropriate replacementElements to return can compare with the rest in
        # appendContextFromVariant.

        replacedElements = longestVariant.replacedElements(activeSite, includeSpacers = True)



        lpMusicList = lyo.LyMusicList(musicList)
        lpInternalSequentialMusic = lyo.LySequentialMusic(musicList = lpMusicList )

        if newVariant is True:
            lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(type = 'new',
                                                            optionalId = variantId,
                                                            simpleString = "Staff",
                                                            music = lpInternalSequentialMusic)
        else: #newVariant is False
            lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(type = 'context',
                                                            optionalId = variantId,
                                                            simpleString = "Staff",
                                                            music = lpInternalSequentialMusic)
                

        #optionalContextMod = r'''
        #\with {
        #      \remove "Time_signature_engraver"
        #      alignAboveContext = #"%s"
        #      fontSize = ##-3
        #      \override StaffSymbol #'staff-space = #(magstep -3)
        #      \override StaffSymbol #'thickness = #(magstep -3)
        #      \override TupletBracket #'bracket-visibility = ##f
        #      \override TupletNumber #'stencil = ##f
        #      \override Clef #'transparent = ##t
        #    } 
        #    ''' % containerId #\override BarLine #'transparent = ##t is the best way of fixing #the barlines that I have come up with.
#
        #lpPrefixCompositeMusicVariant.optionalContextMod = optionalContextMod

        self.variantMode = False

        return lpPrefixCompositeMusicVariant, replacedElements


    def lyPrefixCompositeMusicFromVariant(self, variantObject, replacedElements, coloredVariants = False):
        '''
        
        >>> from music21 import *
        >>> pstream = converter.parse("a4 b c d   e4 f g a", "4/4")
        >>> pstream.makeMeasures(inPlace = True)
        >>> p = stream.Part(pstream)
        >>> p.id = 'p1'
        >>> vstream = converter.parse("a4. b8 c4 d", "4/4")
        >>> vstream.makeMeasures(inPlace = True)
        >>> v = variant.Variant(vstream)
        >>> v.groups = ['london']
        >>> p.insert(0.0, v)
        >>> lpc = lily.translate.LilypondConverter()
        >>> replacedElements = v.replacedElements()
        >>> lpPrefixCompositeMusicVariant = lpc.lyPrefixCompositeMusicFromVariant(v, replacedElements)
        >>> print lpPrefixCompositeMusicVariant
        \\new Staff  = londonpx 
        \with {
              \\remove "Time_signature_engraver"
              alignAboveContext = #"px"
              fontSize = #-3
              \override StaffSymbol #'staff-space = #(magstep -3)
              \override StaffSymbol #'thickness = #(magstep -3)
              \override TupletBracket #'bracket-visibility = ##f
              \override TupletNumber #'stencil = ##f
              \override Clef #'transparent = ##t
            } 
            { {\startStaff \clef "treble" 
          \clef "treble" 
          \\time 4/4
          a' 4.  
          b' 8  
          c' 4  
          d' 4  
          \\bar "|."  %{ end measure 1 %} 
           \stopStaff} 
        <BLANKLINE>
           }
        <BLANKLINE>

        >>> replacedElements.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note D>

        >>> print lpc.addedVariants
        [u'london']
        
        '''
        replacedElementsClef = replacedElements[0].getContextByClass('Clef')

        variantContainerStream = variantObject.getContextByClass('Part')
        if variantContainerStream is None:
            variantContainerStream = variantObject.getContextByClass('Stream')

        if not replacedElementsClef in variantObject.elements:
            variantObject.insert(0, replacedElementsClef)

        variantName = variantObject.groups[0]
        if variantName in self.addedVariants:
            newVariant = False
        else:
            self.addedVariants.append(variantName)
            newVariant = True

        containerId = makeLettersOnlyId(variantContainerStream.id)
        variantId = lyo.LyOptionalId(makeLettersOnlyId(variantName)+containerId)

        if coloredVariants is True:
            color = self.variantColors[self.addedVariants.index(variantName) % 6]
            for n in variantObject._stream.flat.notesAndRests:
                n.editorial.color = color

        

        musicList = []

        if len(variantObject.getElementsByClass("SpacerRest")) > 0:
            spacer = variantObject.getElementsByClass("SpacerRest")[0]
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
            numerator, denominator = common.decimalToTuplet(replacedElementsLength/variantLength)
            fraction = str(numerator) + '/' + str(denominator)
            lpVariantTuplet = lyo.LyPrefixCompositeMusic(type='times', 
                                                        fraction = fraction,
                                                        music = lpOssiaMusicVariant)
            lpInternalSequentialMusic = lyo.LySequentialMusic(musicList = lpVariantTuplet)
            musicList.append(lpInternalSequentialMusic)  
        else:
            musicList.append(lpOssiaMusicVariant)
        

        lpMusicList = lyo.LyMusicList(musicList)
        lpOssiaMusicVariantWithSpacer = lyo.LySequentialMusic(musicList = lpMusicList )
        
        if newVariant is True:
            lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(type = 'new',
                                                        optionalId = variantId,
                                                        simpleString = "Staff",
                                                        music = lpOssiaMusicVariantWithSpacer)
        else:
            lpPrefixCompositeMusicVariant = lyo.LyPrefixCompositeMusic(type = 'context',
                                                          optionalId = variantId,
                                                          simpleString = "Staff",
                                                          music = lpOssiaMusicVariantWithSpacer)

#        optionalContextMod = r'''
#\with {
#      \remove "Time_signature_engraver"
#      alignAboveContext = #"%s"
#      fontSize = #-3
#      \override StaffSymbol #'staff-space = #(magstep -3)
#      \override StaffSymbol #'thickness = #(magstep -3)
#      \override TupletBracket #'bracket-visibility = ##f
#      \override TupletNumber #'stencil = ##f
#      \override Clef #'transparent = ##t
#    } 
#    ''' % containerId #\override BarLine #'transparent = ##t is the best way of fixing the #barlines that I have come up with.
#
#        lpPrefixCompositeMusicVariant.optionalContextMod = optionalContextMod

        self.variantMode = False

        return lpPrefixCompositeMusicVariant

        #musicList2 = []
        #musicList2.append(lpPrefixCompositeMusicVariant)
        #musicList2.append(lpSequentialMusicStandard )
        #
        #lp2MusicList = lyo.LyMusicList()
        #lp2MusicList.contents = musicList2
        #lp2SimultaneousMusic = lyo.LySimultaneousMusic()
        #lp2SimultaneousMusic.musicList = lp2MusicList
        #lp2GroupedMusicList = lyo.LyGroupedMusicList()
        #lp2GroupedMusicList.simultaneousMusic = lp2SimultaneousMusic
        #
        #contextObject = self.context
        #currentMusicList = contextObject.contents
        #currentMusicList.append(lp2GroupedMusicList)
        #lp2GroupedMusicList.setParent(self.context)

        
    def lyOssiaMusicFromVariant(self, variantIn):
        r'''
        returns a LyOssiaMusic object from a stream

        >>> from music21 import *
        >>> c = converter.parse('tinynotation: 3/4 C4 D E F2.')
        >>> v = variant.Variant(c)
        >>> lpc = lily.translate.LilypondConverter()
        >>> lySequentialMusicOut = lpc.lySequentialMusicFromStream(v)
        >>> lySequentialMusicOut
        <music21.lily.lilyObjects.LySequentialMusic object at 0x...>
        >>> print lySequentialMusicOut
        { \time 3/4
         c 4  
         d 4  
         e 4  
         f 2.  
        } 
        '''
        musicList = []

        lpMusicList = lyo.LyMusicList(contents = musicList)
        lpOssiaMusic = lyo.LyOssiaMusic(musicList = lpMusicList)
        self.newContext(lpMusicList)    
        
        self.variantMode = True
        self.appendObjectsToContextFromStream(variantIn._stream)
                    
        lyObject = self.closeMeasure()
        if lyObject is not None:
            musicList.append(lyObject)    
        
        self.restoreContext()

        self.variantMode = False
        
        return lpOssiaMusic

    def setHeaderFromMetadata(self, metadataObject = None, lpHeader = None):
        r'''
        Returns a lilypond.lilyObjects.LyLilypondHeader object
        set with data from the metadata object

        >>> from music21 import *
        >>> md = metadata.Metadata()
        >>> md.title = 'My Title'
        >>> md.alternativeTitle = 'My "sub"-title'
        
        >>> lpc = lily.translate.LilypondConverter()
        >>> lpHeader = lpc.setHeaderFromMetadata(md)
        >>> print lpHeader
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
                lyTitleAssignment = lyo.LyAssignment(assignmentId = "title", 
                                                 identifierInit = lyo.LyIdentifierInit(string = metadataObject.title))
                lpHeaderBodyAssignments.append(lyTitleAssignment)
                lyTitleAssignment.setParent(lpHeaderBody)
            if metadataObject.alternativeTitle is not None:
                lySubtitleAssignment = lyo.LyAssignment(assignmentId = "subtitle",
                                                    identifierInit = lyo.LyIdentifierInit(string = metadataObject.alternativeTitle))
                lpHeaderBodyAssignments.append(lySubtitleAssignment)
                lyTitleAssignment.setParent(lpHeaderBody)
        
        lpHeaderBody.assignments = lpHeaderBodyAssignments
        return lpHeader

    def closeMeasure(self, barChecksOnly = False):
        r'''
        return a LyObject or None for the end of the previous Measure
        
        uses self.currentMeasure
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> m = stream.Measure()
        >>> m.number = 2
        >>> m.rightBarline = 'double'
        >>> lpc.currentMeasure = m
        >>> lyObj = lpc.closeMeasure()
        >>> lpc.currentMeasure is None
        True
        >>> print lyObj
        \bar "||"  %{ end measure 2 %} 
        '''
        m = self.currentMeasure
        self.currentMeasure = None
        if m is None:
            return None
        #if m.rightBarline is None:
        #    return None
        #elif m.rightBarline.style == 'regular':
        #    return None
        
        if self.variantMode is True:
            barChecksOnly = True

        lpBarline = lyo.LyEmbeddedScm()

        if barChecksOnly is True:
            barString = "|"
        elif m.rightBarline is None:
            barString = lpBarline.backslash + 'bar ' + lpBarline.quoteString("|")
        else:
            barString = lpBarline.backslash + 'bar ' + lpBarline.quoteString(self.barlineDict[m.rightBarline.style])
        
        if m.number is not None:
            barString += lpBarline.comment("end measure %d" % m.number)

        
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

        >>> from music21 import *
        >>> m = stream.Measure()
        >>> m.append(meter.TimeSignature('3/4'))
        >>> m.paddingLeft = 2.0
        >>> lpc = lily.translate.LilypondConverter()
        >>> outScheme = lpc.getSchemeForPadding(m)
        >>> print outScheme
        \partial 32*8
        '''
        pL = measureObject.paddingLeft
        if pL == 0:
            return None
        tses = measureObject.getTimeSignatures()
        if len(tses) == 0:
            barLength = 4.0
        else:
            ts = tses[0]
            barLength = ts.barDuration.quarterLength 
        remainingQL = barLength - pL
        if remainingQL <= 0:
            raise LilypondTranslateException('your first pickup measure is non-existent!')
        remaining32s = int(remainingQL * 8)
        lyObject = lyo.LyEmbeddedScm()
        schemeStr = lyObject.backslash + 'partial 32*' + str(remaining32s) + ' ' 
        lyObject.content = schemeStr
        return lyObject

    #--------------display and converter routines ---------------------#        
    def writeLyFile(self, ext = '', fp = None):
        '''
        writes the contents of the self.topLevelObject to a file.
        
        The extension should be ly.  If fp is None then a named temporary
        file is created by environment.getTempFile.
        
        '''
        
        if fp is None:
            fp = environLocal.getTempFile(ext)
        
        self.tempName = fp

        with open(self.tempName, 'w') as f:
            f.write(str(self.topLevelObject).encode('utf-8'))

        return self.tempName
    
    def runThroughLily(self, format = None, backend = None, fileName = None, skipWriting = False):
        '''
        creates a .ly file from self.topLevelObject via .writeLyFile
        then runs the file through Lilypond.
        
        Returns the full path of the file produced by lilypond including the format extension.
        
        If skipWriting is True and a fileName is given then it will run that file through lilypond instead
        
        '''
        
        if fileName is None:
            fileName = self.writeLyFile(ext = 'ly')
        else:
            if skipWriting is False:
                fileName = self.writeLyFile(ext = 'ly', fp = fileName)
            
        
        lilyCommand = '"' + self.LILYEXEC + '" ' 
        if format is not None:
            lilyCommand += "-f " + format + " "
        if backend is not None:
            lilyCommand += self.backendString + backend + " "
        lilyCommand += "-o " + fileName + " " + fileName
        
        try:
            os.system(lilyCommand)    
        except:
            raise
        
        try:
            os.remove(filename + ".eps")
        except:
            pass
        fileform = fileName + '.' + format
        if not os.path.exists(fileform):
            fileend = os.path.basename(fileform)
            if not os.path.exists(fileend):
                raise LilyTranslateException("cannot find " + fileend + " original file was " + fileName)
            else:
                fileform = fileend
        return fileform

    def createPDF(self, fileName=None):
        '''
        create a PDF file from self.topLevelObject and return the filepath of the file.        

        most users will just call stream.write('lily.pdf') on a stream.
        '''
        lilyFile = self.runThroughLily(backend='ps', format = 'pdf', fileName = fileName)
        return lilyFile

    def showPDF(self):
        '''
        create a SVG file from self.topLevelObject, show it with your pdf reader (often Adobe Acrobat/Adobe Reader or Apple Preview)
        and return the filepath of the file.        

        most users will just call stream.Stream.show('lily.pdf') on a stream.
        '''
        lF = self.createPDF()
        if not os.path.exists(lF):
            raise Exception('Something went wrong with PDF Creation')
        else:
            if os.name == 'nt':
                command = 'start /wait %s && del /f %s' % (lF, lF)
            elif sys.platform == 'darwin':
                command = 'open %s' % lF
            else:
                command = ''
            os.system(command)
    
    def createPNG(self, fileName=None):
        '''
        create a PNG file from self.topLevelObject and return the filepath of the file.        

        most users will just call stream.write('lily.png') on a stream.

        if PIL is installed then a small white border is created around the score
        '''
        lilyFile = self.runThroughLily(backend='eps', format = 'png', fileName = fileName)
        if noPIL is False:
            try:
                lilyImage = Image.open(lilyFile)
                lilyImage2 = ImageOps.expand(lilyImage, 10, 'white')
                lilyImage2.save(lilyFile)
            except:
                pass # no big deal probably...
        return lilyFile
        

#                if os.name == 'nt':
#                    format = 'png'
#                # why are we changing format for darwin? -- did not work before
#                elif sys.platform == 'darwin':
#                    format = 'jpeg'
#                else: # default for all other platforms
#                    format = 'png'
#                
#                if lilyImage2.mode == "I;16":
#                # @PIL88 @PIL101
#                # "I;16" isn't an 'official' mode, but we still want to
#                # provide a simple way to show 16-bit images.
#                    base = "L"
#                else:
#                    base = Image.getmodebase(lilyImage2.mode)
#                if base != lilyImage2.mode and lilyImage2.mode != "1":
#                    file = lilyImage2.convert(base)._dump(format=format)
#                else:
#                    file = lilyImage2._dump(format=format)
#                return file
#            except:
#                raise
                
    def showPNG(self):
        '''
        Take the object, run it through LilyPond, and then show it as a PNG file.
        On Windows, the PNG file will not be deleted, so you  will need to clean out
        TEMP every once in a while.
        
        Most users will just want to call stream.Stream.show('lily.png') instead.
        '''
        try:
            lilyFile = self.createPNG()
        except LilyTranslateException as e:
            raise LilyTranslateException("Problems creating PNG file: (" + str(e) + ")")
        environLocal.launch('png', lilyFile)
        #self.showImageDirect(lilyFile)
        
        return lilyFile
        
    def createSVG(self, fileName = None):
        '''
        create an SVG file from self.topLevelObject and return the filepath of the file.        

        most users will just call stream.Stream.write('lily.svg') on a stream.
        '''
        lilyFile = self.runThroughLily(format = 'svg', backend = 'svg', fileName = fileName)
        return lilyFile

    def showSVG(self, fileName = None):
        '''
        create a SVG file from self.topLevelObject, show it with your svg reader (often Internet Explorer on PC)
        and return the filepath of the file.        

        most users will just call stream.Stream.show('lily.png') on a stream.
        '''
        lilyFile = self.createSVG(fileName)
        environLocal.launch('svg', lilyFile)
        return lilyFile
        

class LilyTranslateException(Exception):
    pass


class Test(unittest.TestCase):
    pass
    def testExplicitConvertChorale(self):
        lpc = LilypondConverter()
        b = _getCachedCorpusFile('bach/bwv66.6')
        lpc.loadObjectFromScore(b, makeNotation = False)
        #print lpc.topLevelObject

    def testComplexDuration(self):
        from music21 import stream, note, meter
        s = stream.Stream()
        n1 = note.Note('C') # test no octave also!
        n1.duration.quarterLength = 2.5 # BUG 2.3333333333 doesn't work right
        self.assertEqual(n1.duration.type, 'complex')
        n2 = note.Note('D4')
        n2.duration.quarterLength = 1.5
        s.append(meter.TimeSignature('4/4'))
        s.append(n1)
        s.append(n2)
        #s.show('text')
        lpc = LilypondConverter()
        lpc.loadObjectFromScore(s)
        #print lpc.topLevelObject
        #lpc.showPNG()
        #s.show('lily.png')


class TestExternal(unittest.TestCase):


    def xtestConvertNote(self):
        from music21 import note
        n = note.Note("C5")
        n.show('lily.png')
    
    def xtestConvertChorale(self):
        b = _getCachedCorpusFile('bach/bwv66.6')
        for n in b.flat:
            n.beams = None
        b.parts[0].show('lily.svg')

    def xtestSlowConvertOpus(self):
        from music21 import corpus
        fifeOpus = corpus.parse('miscFolk/americanfifeopus.abc')
        fifeOpus.show('lily.png')

    def xtestBreve(self):
        from music21 import note, stream, meter
        n = note.Note("C5")
        n.duration.quarterLength = 8.0
        m = stream.Measure()
        m.append(meter.TimeSignature('8/4'))
        m.append(n)
        p = stream.Part()
        p.append(m)
        s = stream.Score()
        s.append(p)
        s.show('lily.png')
    
    def testJosquin(self):
        from music21 import converter
        j = converter.parse('http://jrp.ccarh.org/cgi-bin/josquin?a=parallel&f=Jos2308-Ave_maris_stella', format='humdrum')
        j.show('lilypond')

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
    #music21.mainTest(TestExternal, 'noDocTest')
    
#------------------------------------------------------------------------------
# eof



