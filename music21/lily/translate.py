# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         lily/translate.py
# Purpose:      music21 classes for translating to Lilypond
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2007-2012 The music21 Project
# License:      LGPL
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

import re
import music21
from music21 import duration
from music21 import environment
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

# for tests -- speeds things up a lot!
b = corpus.parse('bach/bwv66.6')
#b.parts[0].measure(4)[2].color = 'blue'#.rightBarline = 'double'

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
        self.currentMeasure = None

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
              << \new Staff { c' 4  
                      }
                >>
          }
        \paper { }
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
        
        self.context.contents = contents

    
    def loadObjectFromScore(self, scoreIn = None, makeNotation = True):
        r'''
        
        creates a filled topLevelObject (lily.lilyObjects.LyLilypondTop)
        whose string representation accurately reflects this Score object.
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> #b = corpus.parse('bwv66.6')
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
        contents = [lpVersionScheme, lpColorScheme, lpHeader, lpScoreBlock, lpOutputDef]
        
        if scoreIn.metadata is not None:
            self.setHeaderFromMetadata(scoreIn.metadata, lpHeader = lpHeader)

        self.context.contents = contents
        
        
    #------- return Lily objects or append to the current context -----------#
    def lyScoreBlockFromScore(self, scoreIn):
        
        lpCompositeMusic = lyo.LyCompositeMusic()
        self.newContext(lpCompositeMusic)

        if hasattr(scoreIn, 'parts') and len(scoreIn.parts) > 0:
            lpGroupedMusicList = self.lyGroupedMusicListFromScoreWithParts(scoreIn)
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

    def lyGroupedMusicListFromScoreWithParts(self, scoreIn):
        r'''
        
        >>> from music21 import *
        >>> lpc = lily.translate.LilypondConverter()
        >>> #_DOCS_SHOW b = corpus.parse('bwv66.6')
        >>> lpGroupedMusicList = lpc.lyGroupedMusicListFromScoreWithParts(b)
        >>> print lpGroupedMusicList
        << \new Staff { \partial 32*8 
               \clef "treble" 
               \key fis \minor 
               \time 4/4
               \once \override Stem #'direction = #DOWN 
               cis'' 8  
               \once \override Stem #'direction = #DOWN 
               b' 8  
               \bar "|"  %{ end measure 0 %} 
               \once \override Stem #'direction = #UP 
               a' 4  
               \once \override Stem #'direction = #DOWN 
               b' 4  
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
        \new Staff { \partial 32*8 
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
        >>
        '''
        
        compositeMusicList = []
        
        lpGroupedMusicList = lyo.LyGroupedMusicList()
        lpSimultaneousMusic = lyo.LySimultaneousMusic()
        lpMusicList = lyo.LyMusicList()
        lpSimultaneousMusic.musicList = lpMusicList
        lpGroupedMusicList.simultaneousMusic = lpSimultaneousMusic

        self.newContext(lpMusicList)
        
        for p in scoreIn.parts:
            compositeMusicList.append(self.lyPrefixCompositeMusicFromStream(p))

        self.restoreContext()
        lpMusicList.contents = compositeMusicList
        
        return lpGroupedMusicList

    def lyPrefixCompositeMusicFromStream(self, part):
        '''
        returns an LyPrefixCompositeMusic object from
        a stream (generally a part, but who knows...)
        '''
        
        c = part.classes
        if 'Part' in c:
            newContext = 'Staff'
        elif 'Voice' in c:
            newContext = 'Voice'
        else:
            newContext = 'Voice'
        
        musicList = []

        lpMusicList = lyo.LyMusicList(contents = musicList)
        lpSequentialMusic = lyo.LySequentialMusic(musicList = lpMusicList)
        lpGroupedMusicList = lyo.LyGroupedMusicList(sequentialMusic = lpSequentialMusic)
        lpCompositeMusic = lyo.LyCompositeMusic(groupedMusicList = lpGroupedMusicList)
        lpMusic = lyo.LyMusic(compositeMusic = lpCompositeMusic)
        lpPrefixCompositeMusic = lyo.LyPrefixCompositeMusic(type = 'new',
                                                            simpleString = newContext,
                                                            music = lpMusic)
        
        self.newContext(lpMusicList)    
        self.appendObjectsToContextFromStream(part)
                    
        lyObject = self.closeMeasure()
        if lyObject is not None:
            musicList.append(lyObject)    
        
        self.restoreContext()
        return lpPrefixCompositeMusic


    def appendObjectsToContextFromStream(self, streamObject):
        r'''
        takes a Stream and appends all the elements in it to the current
        context's .contents list, and deals with creating Voices in it.
        
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
            if len(groupedElements) == 1: # one thing at that moment...
                el = groupedElements[0]
                self.appendM21ObjectToContext(el)
            else: # voices or other More than one thing at once...
                # if voices
                voiceList = []
                for el in groupedElements:
                    if 'Voice' in el.classes:
                        voiceList.append(el)
                    else:
                        self.appendM21ObjectToContext(el)
                
                if len(voiceList) > 0:
                    musicList2 = []
                    lp2GroupedMusicList = lyo.LyGroupedMusicList()
                    lp2SimultaneousMusic = lyo.LySimultaneousMusic()
                    lp2MusicList = lyo.LyMusicList()
                    lp2SimultaneousMusic.musicList = lp2MusicList
                    lp2GroupedMusicList.simultaneousMusic = lp2SimultaneousMusic

                    for voice in voiceList:
                        lpPrefixCompositeMusic = self.lyPrefixCompositeMusicFromStream(voice)
                        musicList2.append(lpPrefixCompositeMusic)
                    
                    lp2MusicList.contents = musicList2
                    
                    contextObject = self.context
                    currentMusicList = contextObject.contents
                    currentMusicList.append(lp2GroupedMusicList)
                    lp2GroupedMusicList.setParent(self.context)
    

    def appendM21ObjectToContext(self, thisObject):
        '''
        converts any type of object into a lilyObject of LyMusic (
        LySimpleMusic, LyEmbeddedScm etc.) type
        '''
        ### treat complex duration objects as multiple objects
        c = thisObject.classes

        
        if 'Stream' not in c and thisObject.duration.type == 'complex':
            thisObjectSplit = thisObject.splitAtDurations()
            for subComponent in thisObjectSplit:
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
            try:
                lyObject = self.lyPrefixCompositeMusicFromStream(thisObject)
                currentMusicList.append(lyObject)
                lyObject.setParent(contextObject)
            except AttributeError as ae:
                raise Exception("Cannot parse %s: %s" % (thisObject, str(ae)))
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
        elif "TimeSignature" in c:
            lyObject = self.lyEmbeddedScmFromTimeSignature(thisObject)
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
        elif 'Rest' in c:
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
        if generalNote.lyric is not None: # hack that uses markup...
            postEvents.append(r'_\markup { "' + generalNote.lyric + '" }\n ')

        
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
        keyScheme = lpEmbeddedScm.backslash + 'time ' + str(ts) + lpEmbeddedScm.newlineIndent
        lpEmbeddedScm.content = keyScheme
        return lpEmbeddedScm


    def setContextForTupletStart(self, inObj):
        '''
        if the inObj has tuplets then we set a new context
        for the tuplets and anything up till a tuplet stop.
        
        Note that a broken tuplet (a la Michael Gordon)
        will not work.
        
        If there are no tuplets, this routine does
        nothing.
        
        For now, no nested tuplets.  They're an
        easy extension, but there's too much
        else missing to do it now...
        '''
        if inObj.duration.tuplets is None or len(inObj.duration.tuplets) == 0:
            return None
        elif inObj.duration.tuplets[0].type == 'start':
            numerator = str(int(inObj.duration.tuplets[0].tupletNormal[0]))
            denominator = str(int(inObj.duration.tuplets[0].tupletActual[0]))            
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

        else:
            return None

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

    def closeMeasure(self):
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
        else:
            if m.rightBarline is not None:
                barString = self.barlineDict[m.rightBarline.style]
            else:
                barString = "|"
            lpBarline = lyo.LyEmbeddedScm()
            if m.number is not None:
                barString = lpBarline.backslash + 'bar ' + lpBarline.quoteString(barString) + lpBarline.comment("end measure %d" % m.number)
            else:
                barString = lpBarline.backslash + 'bar ' + lpBarline.quoteString(barString)
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
    
    def runThroughLily(self, format = 'png', backend = 'ps', fileName = None, skipWriting = False):
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
            
        lilyCommand = '"' + self.LILYEXEC + '"' + " -f " + format + " " + \
                    self.backendString + backend + " -o " + fileName + " " + fileName
        
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


    def testConvertNote(self):
        from music21 import note
        n = note.Note("C5")
        n.show('lily.png')
    
    def testConvertChorale(self):
        for n in b.flat:
            n.beams = None
        b.parts[0].show('lily.svg')

    def xtestSlowConvertOpus(self):
        from music21 import corpus
        fifeOpus = corpus.parse('miscFolk/americanfifeopus.abc')
        fifeOpus.show('lily.png')
    
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    music21.mainTest(TestExternal)
    
#------------------------------------------------------------------------------
# eof



