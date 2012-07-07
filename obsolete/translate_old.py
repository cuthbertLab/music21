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

this replaces (April 2012) the old LilyString() conversion methods.
'''

import os
import sys
import tempfile
import re
import time
# import threading
import unittest, doctest
import copy


import music21
from music21 import duration
from music21 import environment
_MOD = 'lily.translate.py'
environLocal = environment.Environment(_MOD)


try: 
    # optional imports for PIL 
    from PIL import Image
    from PIL import ImageOps
    noPIL = False
except ImportError:
    noPIL = True


#-------------------------------------------------------------------------------


class LilypondConverter(object):
    paperDefinition  = r'''
\paper {
#(define dump-extents #t)

indent = 0\mm
force-assignment = #""
oddFooterMarkup=##f
oddHeaderMarkup=##f
bookTitleMarkup=##f

}
'''
    noHeader = r'''
scoreTitleMarkup=##f
'''
    
    layout = r'''
\layout {

}
'''

    
    fictaDef = \
    """
    ficta = #(define-music-function (parser location) () #{ \\once \\set suggestAccidentals = ##t #})
    color = #(define-music-function (parser location color) (string?) #{ 
        \\once \\override NoteHead #'color = #(x11-color $color) 
        \\once \\override Stem #'color = #(x11-color $color)
        \\once \\override Rest #'color = #(x11-color $color)
        \\once \\override Beam #'color = #(x11-color $color)
     #})    
    """

    savePNG = False ## PNGs are deleted immediately.

    TRANSPARENCY_START = r'''
     \override Rest #'transparent  = ##t
     \override Dots #'transparent  = ##t
     '''
    TRANSPARENCY_STOP = r'''
     \revert Rest #'transparent
     \revert Dots #'transparent
     '''

    accidentalConvert = {"double-sharp": u"isis",
                         "double-flat": u"eses",
                         "one-and-a-half-sharp": u"isih",
                         "one-and-a-half-flat": u"eseh",
                         "sharp": u"is",
                         "flat": u"es",
                         "half-sharp": u"ih",
                         "half-flat": u"eh",
                         }

    
    def __init__(self, loadObj = None):
        self.setupTools()
        self.resetParameters()
        if loadObj is not None:
            self.loadObject(loadObj)

    def resetParameters(self):
        self.lyricList = []
        self.partsList = [u""]
        self.allString = u""
        self.header = None
        self._currentPartNumber = 0


    def loadObject(self, convertObj):
        r'''
        loads an object for conversion.  Can be called directly from LilypondConverter() creation
        or called separately.
        
        Returns nothing unless an error is found.
        
        >>> from music21 import *
        >>> n = note.Note('C#4')
        >>> conv = lily.translate.LilypondConverter()
        >>> conv.loadObject(n)
        >>> print conv.allString
        { cis'4 }
        
        
        But this does the same thing:
        >>> n = note.Note('C#4')
        >>> conv = lily.translate.LilypondConverter(n)
        >>> print conv.allString
        { cis'4 }
        
        '''
        self.resetParameters()
        if 'Stream' not in convertObj.classes:
            stringout = u'{ ' + self.fromObject(convertObj) + u' }'
        else:
            stringout = self.fromObject(convertObj)
        if self.header is not None:
            stringout += '''\n \\header { \n piece = \\markup \\bold "%s" \n } ''' % self.header
        self.allString = stringout

    
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
        self.format   = 'pdf'
        self.majorVersion = 2 # this should be obtained from user and/or user's system
        self.minorVersion = 12
        self.version = str(self.majorVersion) + '.' + str(self.minorVersion)
        self.backend  = 'ps'
        
        if self.majorVersion >= 2:
            if self.minorVersion >= 11:
                self.backendString = '-dbackend='
            else:
                self.backendString = '--backend='
        else:
            self.backendString = '--backend='
        # I had a note that said 2.12 and > should use 'self.backendString = '--formats=' ' but doesn't seem true
        
        self.headerInformation = "\\version \"" + self.version + "\"" + self.layout + self.fictaDef
    
    
#    def _getPartString(self):
#        return self.partsList[self._currentPartNumber]
#    
#    def _setPartString(self, value):
#        if isinstance(value, unicode) is False:
#            value = unicode(value)
#        self.partsList[self._currentPartNumber] = value
#    
#    partString = property(_getPartString, _setPartString, doc='''
#        Returns or sets the current part lilypond entry as a unicode String
#        
#        >>> from music21 import *
#        >>> conv = lily.translate.LilypondConverter()
#        >>> conv.partString = 'hello'
#        >>> conv.partString
#        u'hello'
#        ''')

    def fromObject(self, thisObject):
        '''
        converts any type of object into a unicode lilypond string
        
        '''
        
        lilyout = u''
        if hasattr(thisObject, "startTransparency") and thisObject.startTransparency is True:
            lilyout += self.TRANSPARENCY_START

        if hasattr(thisObject.duration, "tuplets") and thisObject.duration.tuplets:
            if thisObject.duration.tuplets[0].type == "start":
                numerator = unicode(int(thisObject.duration.tuplets[0].tupletNormal[0]))
                denominator = unicode(int(thisObject.duration.tuplets[0].tupletActual[0]))
                lilyout += u"\\times " + numerator + u"/" + denominator + u" {"
                ### TODO-- should get the actual ratio not assume that the
                ### type of top and bottom are the same

        c = thisObject.classes
        if "GeneralNote" in c:
            lilyout += self.fromGeneralNote(thisObject)
        elif "Clef" in c:
            lilyout += self.fromClef(thisObject)
        elif "Part" in c:
            lilyout += self.fromPart(thisObject)
        elif "Score" in c:
            lilyout += self.fromScore(thisObject)
        elif "Stream" in c:
            lilyout += self.fromStream(thisObject)
        elif "KeySignature" in c:
            lilyout += self.fromKeySignature(thisObject)
        elif "TimeSignature" in c:
            lilyout += self.fromTimeSignature(thisObject)
        
        elif hasattr(thisObject, "lily"):
            environLocal.printDebug('found an object with lily in it -- fix in new system... %s' % thisObject)
            lilyout += unicode(thisObject.lily) + u" "
        elif "PageLayout" in c or "SystemLayout" in c or "Barline" in c \
            or "StaffGroup" in c or "TextBox" in c or "Metadata" in c \
            or "Instrument" in c:
            pass # known unsupported
        else:
            environLocal.printDebug('found an object with no way to convert to lily... %s' % thisObject)
        
        if hasattr(thisObject.duration, "tuplets") and thisObject.duration.tuplets:
            if thisObject.duration.tuplets[0].type == "stop":
                lilyout = lilyout.rstrip()
                lilyout += u"} "

        if hasattr(thisObject, "stopTransparency") and thisObject.stopTransparency is True:
            lilyout += self.TRANSPARENCY_STOP

        return lilyout
        
    
    #----------------conversions----------------------------- 
    def fromStream(self, streamObj, omitContainer = False):
        r'''
        Returns the Stream translated into Lilypond format.
        
        For Specialized Stream Subclasses (Part, Score, etc.), there are specialized conversions.

        
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.append(clef.BassClef())
        >>> s1.append(meter.TimeSignature("3/4"))
        >>> k1 = key.KeySignature(5)
        >>> k1.mode = 'minor'
        >>> s1.append(k1)
        >>> s1.append(note.Note("B-3"))   # quarter note
        >>> s1.append(note.HalfNote("C#2"))
        >>> conv = lily.translate.LilypondConverter()
        >>> print conv.fromStream(s1)
        <BLANKLINE>
        { \clef "bass"  \time 3/4  \key gis \minor bes4 cis,2  }
        
        '''
        if omitContainer is False:
            lilyout = u"\n  { "
        else:
            lilyout = u""
        allObjs = []
        #print "stream: %s" % streamObj
        if streamObj.isMeasure is True and streamObj.paddingLeft != 0.0:
            ### lilypond partial durations are very strange.  You notate how many
            ### notes are left in the measure, for a quarter note, write "4"
            ### for an eighth, write "8", but for 3 eighths, write "8*3" !
            ### so we will measure in 32nd notes always... won't work for tuplets
            ### of course. 
            ts = streamObj.getContextByClass('TimeSignature')
            if ts is None:
                barLength = 4.0
            else:
                barLength = ts.barDuration.quarterLength 
            remainingQL = barLength - streamObj.paddingLeft
            if remainingQL <= 0:
                raise LilypondTranslateException('your first pickup measure is non-existent!')
            remaining32s = int(remainingQL * 32)
            lilyout += u'\\partial 32*' + unicode(remaining32s) + u' ' 
        
        
        groupedOffsets = streamObj.groupElementsByOffset()
        for thisOffsetPosition in groupedOffsets:
            if len(thisOffsetPosition) > 1:
                
                ### multiple things at this offset check if they are streams....
                streamsFound = []
                for thisSubElement in thisOffsetPosition:
                    if 'Measure' in thisSubElement.classes:
                        streamsFound.append(self.fromStream(thisSubElement, omitContainer=True))
                    elif 'Part' in thisSubElement.classes:
                        streamsFound.append(self.fromPart(thisSubElement))
                    elif 'Stream' in thisSubElement.classes:
                        streamsFound.append(self.fromStream(thisSubElement))
                    else:
                        lilyout += self.fromObject(thisSubElement) + u' '
                if len(streamsFound) == 1:
                    lilyout += streamsFound[0]
                elif len(streamsFound) > 1:
                    lilyout += u" << "
                    lilyout += u' '.join(streamsFound)
                    lilyout += u" >>\n"
            else:
                lilyout += self.fromObject(thisOffsetPosition[0]) + u' '
        if omitContainer is False:
            lilyout += u' }'
        return lilyout



    def fromPart(self, partObj):
        '''
        converts a single part into a unicode lilypond representation
        '''
        return u"\n \\new Staff " + self.fromStream(partObj)

    def fromScore(self, scoreObj):
        '''
        returns the lily unicode string for a score.
        
        By default runs makeNotation on the object.        
        '''
        if scoreObj.metadata is not None:
            if scoreObj.metadata.title is not None:
                self.header = scoreObj.metadata.title
        score2 = copy.deepcopy(scoreObj)
        for p in score2.parts:
            p.makeNotation(inPlace = True)
        lilyout = u" \\score { " + self.fromStream(score2) + " }"
        return lilyout


    #----------------elements in or out of Streams------------------------------------#
    def fromGeneralNote(self, noteObj):
        r'''
        read-only property that returns a string of the lilypond representation of
        a note (or via subclassing, rest or chord)
        
        >>> from music21 import *
        >>> conv = lily.translate.LilypondConverter()

        >>> n0 = note.Note("D4")
        >>> n0.editorial.color = 'blue'
        >>> print conv.fromGeneralNote(n0)
        \color "blue" d'4

        >>> n1 = note.Note("C#5")
        >>> n1.tie = tie.Tie('start')
        >>> n1.articulations = [articulations.Accent()]  ## DOES NOTHING RIGHT NOW
        >>> n1.quarterLength = 1.25
        >>> print conv.fromGeneralNote(n1)
        cis''4~ cis''16~
        

        >>> r1 = note.Rest()
        >>> r1.duration.type = "half"
        >>> print conv.fromGeneralNote(r1)
        r2
        
        >>> r2 = note.Rest()
        >>> r2.quarterLength = 1.25
        >>> print conv.fromGeneralNote(r2)
        r4 r16
        
        >>> c1 = chord.Chord(["C#2", "E4", "D#5"])
        >>> c1.quarterLength = 2.5   # BUG: 2.333333333 doesnt work yet
        >>> print conv.fromGeneralNote(c1)
        <cis, e' dis''>2~ <cis, e' dis''>8
        '''
        c = noteObj.classes
        lilyInternalTieCharacter = u'~'     
        baseName = u''
        if noteObj.editorial is not None:
            baseName += noteObj.editorial.lilyStart()

        if 'Rest' in c:
            lilyInternalTieCharacter = u' ' # when separating components, dont tie them
            baseName += u'r'
        elif 'Chord' in c:
            baseName += self.chordPreDurationLily(noteObj)
        else:
            baseName += self.notePreDurationLily(noteObj)

        allNames = u""
        if hasattr(noteObj.duration, "components") and len(
            noteObj.duration.components) > 0:
            for i in range(0, len(noteObj.duration.components)):
                thisDuration = noteObj.duration.components[i]            
                allNames += baseName
                allNames += self.fromDuration(thisDuration)
                allNames += noteObj.editorial.lilyAttached()
                if (i != len(noteObj.duration.components) - 1):
                    allNames += lilyInternalTieCharacter
                    allNames += " "
                if (i == 0): # first component
                    if noteObj.lyric is not None: # hack that uses markup...
                        allNames += u"_\markup { \"" + noteObj.lyric + "\" } "
        else:
            allNames += baseName
            allNames += self.fromDuration(thisDuration)
            allNames += noteObj.editorial.lilyAttached()
            if noteObj.lyric is not None: # hack that uses markup...
                allNames += u"_\markup { \"" + noteObj.lyric + "\" }\n "
            
        if (noteObj.tie is not None):
            if (noteObj.tie.type != "stop"):
                allNames += u"~"
        if (noteObj.expressions):
            for thisExpression in noteObj.expressions:
                if 'Fermata' in thisExpression.classes:
                    allNames += u" " + "\\fermata "

        if noteObj.editorial is not None:
            allNames += noteObj.editorial.lilyEnd()

        return allNames

    def fromDuration(self, durationObj):
        '''
        appends the duration lily info from fromDurationUnit into a list...
        '''
        msg = []
        if hasattr(durationObj, 'components'):
            for dur in durationObj.components:
                msg.append(self.fromDurationUnit(dur))
            return u''.join(msg)
        else:
            return self.fromDurationUnit(durationObj)

    
    def fromDurationUnit(self, durationObj):
        '''
        Simple lily duration: does not include tuplets
        These are taken care of in the lily processing in stream.Stream
        since lilypond requires tuplets to be in groups
        '''
        if durationObj._typeNeedsUpdating:
            durationObj.updateType()
        number_type = duration.convertTypeToNumber(durationObj.type) # module call
        dots = "." * int(durationObj.dots)
        if number_type < 1:
           number_type = int(number_type * 16)
        return str(number_type) + dots


    def fromAccidental(self, accidentalObject):
        '''
        converts an accidental into a unicode lilypond string.  Does not
        take into account display status, which is dealt with by
        accidentalLilyDisplayType(), since that comes later in the encoding
        
        >>> from music21 import *
        >>> conv = lily.translate.LilypondConverter()
        >>> conv.fromAccidental(pitch.Accidental('half-sharp'))
        u'ih'
        '''
        
        base = u""
        value = accidentalObject.name
        if value in self.accidentalConvert:
            base = self.accidentalConvert[value]

        if accidentalObject.displayType == "always":
            base += u"!"
        if accidentalObject.displayStyle == "parentheses":
            base += u"?"
        return base

    #---------------------------------------------------------------------------
    def notePreDurationLily(self, noteObj):
        '''
        Method to return all the lilypond information that appears before the 
        duration number for a Note object (not GeneralNote)
        
        Is the same for simple and complex duration notes...
        (for Rests, just use u'r')

        >>> from music21 import *
        >>> conv = lily.translate.LilypondConverter()
        >>> n = note.Note('B-2')
        >>> conv.notePreDurationLily(n)
        u'bes,'
                
        ### TODO: Test Ficta
        '''
        baseName = ""
        fictaObj = None
        if noteObj.editorial.ficta is not None:
            fictaObj = noteObj.editorial.ficta 
        if noteObj.pitch is not None:
            baseName += self.pitchPreDurationLily(noteObj.pitch, fictaObj)
        return baseName
    
    def chordPreDurationLily(self, chordObj):
        '''
        Method to return all the lilypond information that appears before the 
        duration number for a chord.
        Is the same for simple and complex duration chords.

        >>> from music21 import *
        >>> conv = lily.translate.LilypondConverter()
        >>> c = chord.Chord(['C3','E#4','A-5'])
        >>> print conv.chordPreDurationLily(c)
        <c eis' aes''>
                
        ### TODO: Test Ficta, editorials
        '''
        baseName = "<"
        baseName += chordObj.editorial.lilyStart()
        fictaObj = None
        if chordObj.editorial.ficta is not None:
            fictaObj = chordObj.editorial.ficta 
        chordNames = []
        for p in chordObj.pitches:
            chordNames.append(self.pitchPreDurationLily(p, fictaObj))
        baseName += u' '.join(chordNames)
        baseName += u'>'
        return baseName

    def pitchPreDurationLily(self, pitchObj, fictaObj = None):
        '''
        helper routine for notePreDurationLily and chordPreDurationLily
        that gets the duration-free representation of a pitch.

        >>> from music21 import *
        >>> conv = lily.translate.LilypondConverter()
        >>> p = pitch.Pitch('A#1')
        >>> conv.pitchPreDurationLily(p)
        u'ais,,'

        '''
        baseName = self.fromPitchNoOctave(pitchObj)

        if fictaObj is not None:
            baseName += self.fromAccidental(fictaObj)
        spio = pitchObj.implicitOctave
        if (spio < 3):
            correctedOctave = 3 - spio
            octaveModChars = u',' * correctedOctave #  C2 = c,  C1 = c,,
        else:
            correctedOctave = spio - 3
            octaveModChars  = u'\'' * correctedOctave # C4 = c', C5 = c''  etc.
        baseName += octaveModChars
        if fictaObj is not None:
            baseName += u"!"  # always display ficta
        elif pitchObj is not None and pitchObj.accidental is not None:
            baseName += self.accidentalLilyDisplayType(pitchObj.accidental)
        return baseName


    def fromPitchNoOctave(self, pitchObj):
        r'''
        Converts a pitchObject to a string representation in lily
        without the octave or accidental display status
        
        >>> from music21 import *
        >>> p = pitch.Pitch("B-6")
        >>> conv = lily.translate.LilypondConverter()
        >>> conv.fromPitchNoOctave(p)
        u'bes'
        '''

        baseName = unicode(pitchObj.step.lower())
        if (pitchObj.accidental):
            baseName += self.fromAccidental(pitchObj.accidental)
        return baseName

    def accidentalLilyDisplayType(self, acc):
        r'''
        Returns a string representing the display attributes for a :class:`~music21.pitch.Accidental` object
        
        >>> from music21 import *
        >>> acc = pitch.Accidental('sharp')
        >>> acc.displayType = "even-tied"
        >>> acc.displayStyle = "parentheses"
        
        >>> conv = lily.translate.LilypondConverter()
        >>> conv.accidentalLilyDisplayType(acc)
        u'!?'
        
        >>> acc2 = pitch.Accidental('flat')
        >>> conv.accidentalLilyDisplayType(acc2)
        u''
        >>> acc2.displayStatus = True
        >>> conv.accidentalLilyDisplayType(acc2)
        u'!'
        '''
        
        lilyRet = u""
        if acc.displayStatus == True \
           or acc.displayType == "always" \
           or acc.displayType == "even-tied":
            lilyRet += u"!"
        
        if acc.displayStyle == "parentheses" \
           or acc.displayStyle == "both":
            lilyRet += u"?"
            ## no brackets for now

        return lilyRet



    def fromClef(self, clefObj):
        r'''
        converts a Key or KeySignature object to lilypond string.

        >>> from music21 import *
        >>> tc = clef.TrebleClef()
        >>> conv = lily.translate.LilypondConverter()
        >>> print conv.fromClef(tc)
        \clef "treble"
        
        Only limited clefs are supported for now...
        
        '''
        
        c = clefObj.classes
        if 'Treble8vbClef' in c:
            lilyName = 'treble_8'
        elif 'TrebleClef' in c:
            lilyName = "treble"
        elif 'BassClef' in c:
            lilyName = "bass"
        else:
            environLocal.printDebug('got a clef that lilypond does not know what to do with: %s' % clefObj)
            lilyName = ""        
        return unicode("\\clef \"" + lilyName + "\" ")



    def fromKeySignature(self, keyObj):
        r'''
        converts a Key or KeySignature object to lilypond string.

        >>> from music21 import *
        >>> d = key.KeySignature(-1)
        >>> d.mode = 'minor'
        >>> conv = lily.translate.LilypondConverter()
        >>> print conv.fromKeySignature(d)
        \key d \minor
        
        Major is assumed:
        
        >>> fsharp = key.KeySignature(6)
        >>> print conv.fromKeySignature(fsharp)
        \key fis \major
        
        '''
        (p, m) = keyObj.pitchAndMode
        if m is None:
            m = "major"
        pn = self.fromPitchNoOctave(p)
        return unicode(r'\key ' + pn + ' \\' + m + ' ')

    def fromTimeSignature(self, ts):
        r'''
        convert a :class:`~music21.meter.TimeSignature` object to a unicode string for lilypond
        
        >>> from music21 import *
        >>> ts = meter.TimeSignature('3/4')
        >>> conv = lily.translate.LilypondConverter()
        >>> print conv.fromTimeSignature(ts)
        \time 3/4
        '''
        return unicode("\\time " + str(ts) + " ")
    #----------------

    def _getTemplatedString(self):
        data = []
        data.append(self.paperDefinition)
        data.append(self.headerInformation)
        data.append(self.allString)
        return u"\n".join(data)

    templatedString = property(_getTemplatedString, doc=r'''
        Takes the information from the loaded object and returns it as 
        unicode string with proper header information.
        
        >>> from music21 import *
        >>> n = note.Note('C#4')
        >>> n.duration.type = 'half'
        
        >>> conv = lily.translate.LilypondConverter()
        >>> conv.loadObject(n)
        >>> print conv.allString
        { cis'2 }
        
        >>> print conv.templatedString
        <BLANKLINE>
        \paper {
        #(define dump-extents #t)
        <BLANKLINE>
        indent = 0\mm
        force-assignment = #""
        oddFooterMarkup=##f
        oddHeaderMarkup=##f
        bookTitleMarkup=##f
        <BLANKLINE>
        }
        <BLANKLINE>
        \version "2.12"
        \layout {
        <BLANKLINE>
        }
        ficta = #(define-music-function (parser location) () #{ \once \set suggestAccidentals = ##t #})
        color = #(define-music-function (parser location color) (string?) #{ 
            \once \override NoteHead #'color = #(x11-color $color) 
            \once \override Stem #'color = #(x11-color $color)
            \once \override Rest #'color = #(x11-color $color)
            \once \override Beam #'color = #(x11-color $color)
             #})    
        <BLANKLINE>
        { cis'2 }
        
    ''')


    def writeTemp(self, ext='', fp=None):
        if fp == None:
            fp = environLocal.getTempFile(ext)
        
        self.tempName = fp

        f = open(self.tempName, 'w')
        f.write(self.templatedString.encode('utf-8'))
        f.close()
        return self.tempName
    


    def runThroughLily(self):
        filename = self.tempName
        format   = self.format
        backend  = self.backend
        lilyCommand = '"' + self.LILYEXEC + '"' + " -f " + format + " " + \
                    self.backendString + backend + " -o " + filename + " " + filename
        
        try:
            os.system(lilyCommand)    
        except:
            raise
        
        try:
            os.remove(filename + ".eps")
        except:
            pass
        fileform = filename + '.' + format
        if not os.path.exists(fileform):
            fileend = os.path.basename(fileform)
            if not os.path.exists(fileend):
                raise LilyTranslateException("cannot find " + fileend + " original file was " + self.tempName)
            else:
                fileform = fileend
        return fileform

    def createPDF(self, filename=None):
        self.writeTemp(fp=filename) # do not need extension here
        lilyFile = self.runThroughLily()
        return lilyFile

    def showPDF(self):
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
    
    def createPNG(self, filename=None):
        self.format = 'png'
        self.backend = 'eps'
        self.writeTemp(fp=filename) # do not need extension here
        lilyFile = self.runThroughLily()
        if noPIL is False:
            try:
                lilyImage = Image.open(lilyFile)
                lilyImage2 = ImageOps.expand(lilyImage, 10, 'white')
                if os.name == 'nt':
                    format = 'png'
                # why are we changing format for darwin? -- did not work before
                elif sys.platform == 'darwin':
                    format = 'jpeg'
                else: # default for all other platforms
                    format = 'png'
                
                if lilyImage2.mode == "I;16":
                # @PIL88 @PIL101
                # "I;16" isn't an 'official' mode, but we still want to
                # provide a simple way to show 16-bit images.
                    base = "L"
                else:
                    base = Image.getmodebase(lilyImage2.mode)
                if base != lilyImage2.mode and lilyImage2.mode != "1":
                    file = lilyImage2.convert(base)._dump(format=format)
                else:
                    file = lilyImage2._dump(format=format)
                return file
            except:
                raise
                
        return lilyFile
        
    def showPNG(self):
        '''Take the object, run it through LilyPond, and then show it as a PNG file.
        On Windows, the PNG file will not be deleted, so you  will need to clean out
        TEMP every once in a while
        '''
        try:
            lilyFile = self.createPNG()
        except LilyTranslateException as e:
            raise LilyTranslateException("Problems creating PNG file: (" + str(e) + ")")
        environLocal.launch(self.format, lilyFile)
        #self.showImageDirect(lilyFile)
        
        return lilyFile
        
    def createSVG(self, filename=None):
        self.format = 'svg'
        self.backend = 'svg'
        self.writeTemp(fp=filename)
        lilyFile = self.runThroughLily()
        return lilyFile

    def showSVG(self, filename=None):
        lilyFile = self.createSVG(filename)
        environLocal.launch(self.format, lilyFile)
        return lilyFile
        
        

class LilypondImporter(object):
    accidentalConvert = {"isis": "double-sharp",
                         "eses": "double-flat",
                         "isih": "one-and-a-half-sharp",
                         "is": "sharp",
                         "es": "flat",
                         "ih": "half-sharp",
                         "eh": "half-flat",
                         "one-and-a-half-flat": "eseh",
                         }
    
    '''
    stub of a class for future work in importing from Lilypond.
    
    MUSIC21 DOES NOT SUPPORT IMPORTING FROM LILYPOND CURRENTLY.
    
    Lilypond files are extremely complex and can contain Scheme language
    code, thus complete parsing without running a Scheme interpreter is
    impossible.  This class just has a few conversion routines
    '''
    def toAccidental(self, value, accidentalObject = None):
        '''
        Converts a string to an accidental (or adds it to the current
        accidentalObject).  If accidentalObject passed in is None
        returns the new accidental
        
        >>> from music21 import *
        >>> importer = lily.translate.LilypondImporter()
        >>> acc = importer.toAccidental('eses')
        >>> acc
        <accidental double-flat>
        >>> acc2 = importer.toAccidental('eh!?')
        >>> acc2
        <accidental half-flat>
        >>> acc2.displayType
        'always'
        >>> acc2.displayStyle
        'parentheses'

        '''
        
        if accidentalObject is None:
            returnAccidental = True
            from music21 import pitch
            accidentalObject = pitch.Accidental()
        else:
            returnAccidental = False

        if value.endswith('?'):
            value = value[0:len(value)-1]
            accidentalObject.displayStyle = "parentheses"
        if value.endswith('!'):
            value = value[0:len(value)-1]
            accidentalObject.displayType = "always"

        if value in self.accidentalConvert:
            accidentalObject.name = self.accidentalConvert[value]
        else:
            raise LilyTranslateException('Cannot convert this value to an accidental %s.' % value)

        if returnAccidental is True:
            return accidentalObject


class LilyTranslateException(Exception):
    pass


class Test(unittest.TestCase):

    def testStreamLilySimple(self):
        from music21 import meter, note, stream
        
        b = stream.Stream()
        b.insert(0, note.QuarterNote('C5'))
        b.insert(1, note.QuarterNote('D5'))
        b.insert(2, note.QuarterNote('E5'))
        b.insert(3, note.QuarterNote('F5'))
        b.insert(4, note.QuarterNote('G5'))
        b.insert(5, note.QuarterNote('A5'))
        
        bestC = b.bestClef(allowTreble8vb = True)
        ts = meter.TimeSignature("3/4")

        b.insert(0, bestC)
        b.insert(0, ts)

        conv = LilypondConverter()
        outStr = conv.fromObject(b)

        self.assertEqual(outStr, 
                         u'\n  { \\clef "treble"  \\time 3/4  c\'\'4 d\'\'4 e\'\'4 f\'\'4 g\'\'4 a\'\'4  }')
        #conv2 = LilypondConverter(b)
        #conv2.showSVG()

    def testStreamLilySemiComplex(self):
        from copy import deepcopy
        from music21 import meter, note, stream, pitch, duration

        a = stream.Stream()
        ts = meter.TimeSignature("3/8")
        
        b = stream.Stream()
        q = note.EighthNote()

        dur1 = duration.Duration()
        dur1.type = "eighth"
        
        tup1 = duration.Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur1]

        q.octave = 2
        q.duration.appendTuplet(tup1)
        
        
        for i in range(0,5):
            b.append(deepcopy(q))
            b.elements[i].accidental = pitch.Accidental(i - 2)
        
        b.elements[0].duration.tuplets[0].type = "start"
        b.elements[-1].duration.tuplets[0].type = "stop"
        b2temp = b.elements[2]
        c = b2temp.editorial
        c.comment.text = "a real C"
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.insert(bestC)
        a.insert(ts)
        a.insert(b)

        conv = LilypondConverter()
        outStr = conv.fromObject(a)
        testStr = u'\n  { \\clef "bass"  \\time 3/8  \n  { \\times 3/5 {ceses,8 ces,8 c,8_"a real C" cis,8 cisis,8}   } }'
#        for i in range(len(outStr)):
#            self.assertEqual(outStr[i], testStr[i])
#        print outStr
#        print testStr

        self.assertEqual(outStr, testStr)


    def testScoreLily(self):
        from copy import deepcopy
        from music21 import clef, meter, note, stream
        ts = meter.TimeSignature("2/4")
 
        p1 = stream.Part()
        p1.id = "P1"
        p1.append(clef.TrebleClef())
        p1.append(ts)
        p1.append(note.Note("C4"))
        p1.append(note.Note("D4"))
        
        p2 = stream.Part()
        p2.id = "P2"
        p2.append(clef.BassClef())
        p2.append(deepcopy(ts))
        p2.append(note.Note("E2"))
        p2.append(note.Note("F2"))
        
        score1 = stream.Score()
        score1.insert(0, p1)
        score1.insert(0, p2)
#        score1.show('text')
#        score2 = score1.makeNotation()
#        score2.show('text')

        conv = LilypondConverter()
        outStr = conv.fromObject(score1)
#        print outStr

#        conv2 = LilypondConverter(score1)
#        conv2.showSVG()

        self.assertEqual(outStr, 
                         r''' \score { 
  {  << 
 \new Staff 
  { 
  { \clef "treble"  \time 2/4  c'4 d'4   }  } 
 \new Staff 
  { 
  { \clef "bass"  \time 2/4  e,4 f,4   }  } >>
 } }''')

class TestExternal(unittest.TestCase):
    
    def testPDFonCorpus(self):
        from music21 import corpus
        b = corpus.parse('bach/bwv1.6')
        conv = LilypondConverter(b)
        #print conv.allString
        conv.showPDF()
        #b.show()

    def testSVGonCorpus(self):
        from music21 import corpus
        b = corpus.parse('bach/bwv1.6').measures(1,7)
        conv = LilypondConverter(b)
        conv.showSVG()
        #b.show()

    
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    #music21.mainTest(Test)
    music21.mainTest(Test, TestExternal)
    
#------------------------------------------------------------------------------
# eof


