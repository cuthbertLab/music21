# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         noteworthy/translate.py
# Purpose:      translates Noteworthy Composer's NWCTXT format
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Module to translate Noteworthy Composer's NWCTXT format to music21.
'''
# to do:
# |SongInfo|Title:"<FileTitle>"|Author:"<Author>"|Lyricist:"<Lyricist>"|
#                Copyright1:"<Copyright1>"|Copyright2:"<Copyright2>"|Comments:"<Comments>"
# |StaffProperties|Muted:N|Volume:127|StereoPan:64|Device:0|Channel:2
# |StaffInstrument|Name:"Lead 6 (voice)"|Patch:85|Trans:0|DynVel:10,30,45,60,75,92,108,127
#
# UnderscoreAsSpace? N or Y
# |Lyrics|Placement:Bottom|Align:Standard Rules|Offset:0|UnderscoreAsSpace:N
#
# strip \\r and \\n
# |Lyric1|Text:"Ahoy________\\r\\n"
#
# support lyric 2
# |Lyric2|Text:"2_1 2_2 2_3 2_4\r\n2_5 2_6 2_7 2_8\r\n"
#
# |Ending|Endings:1
# |Ending|Endings:2,D
#
# ...as expression
# |TempoVariance|Style:Fermata|Pause:3|Pos:-4
#
# ...as spanner
# |TempoVariance|Style:Accelerando|Pos:-6
#
#
# ...beams:
# |Note|Dur:8th|Pos:0|Opts:Stem=Down,Beam=First
# |Note|Dur:8th|Pos:0|Opts:Stem=Down,Beam
# |Note|Dur:8th|Pos:0|Opts:Stem=Down,Beam
# |Dynamic|Style:ppp|Pos:-8
# |Rest|Dur:8th
# |Note|Dur:8th|Pos:0|Opts:Stem=Down,Beam
# |Note|Dur:8th|Pos:0|Opts:Stem=Down,Beam
# |Note|Dur:8th|Pos:0|Opts:Stem=Down,Beam
# |Note|Dur:8th|Pos:0|Opts:Stem=Down,Beam=End
#
# performance style
# |PerformanceStyle|Style:Animato|Pos:-7
#
# low priority:
# |MPC|Controller:vol|Style:Linear Sweep|TimeRes:Whole|SweepRes:1|
#                        Pt1:0,127|Pt2:8,30|Pos:8|Wide:Y|Placement:BestFitForward
#
# Pos2? Dur2?
# |Chord|Dur:8th|Pos:-4,n-3,b-2,#-1,x0,v1,2x|Opts:Stem=Down,Crescendo|Dur2:8th,DblDotted|Pos2:3x

import unittest
from music21 import bar
from music21 import chord
from music21 import clef
from music21 import common
from music21 import duration
from music21 import dynamics
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21 import tie
from music21.exceptions21 import Music21Exception

from music21 import environment
_MOD = 'noteworthy.translate'
environLocal = environment.Environment(_MOD)


# initializations

# file = open("Part_OWeisheit.nwctxt")


class NoteworthyTranslator:
    '''
    stores all the data about the current parse context (whether we're in a slur, tuplet, etc.)
    '''

    def __init__(self):
        self.currentPart = None
        self.currentMeasure = None
        self.score = stream.Score()

        self.currentClef = 'TREBLE'
        self.currentKey = key.KeySignature(0)

        self.withinSlur = False
        self.beginningSlurNote = None
        self.withinTie = False

        self.lyricPosition = 0
        self.lyrics = []

        self.activeAccidentals = {}

    def parseFile(self, filePath):
        try:
            data = common.readFileEncodingSafe(filePath)
            dataList = data.split('\n')
            return self.parseList(dataList)
        except (OSError, FileNotFoundError):
            raise NoteworthyTranslateException(f'cannot open {filePath}: ')

    def parseString(self, data):
        dataList = data.splitlines()
        return self.parseList(dataList)

    def parseList(self, dataList):
        r'''
        Parses a list where each element is a line from a nwctxt file.

        Returns a :class:`~music21.stream.Score` object



        >>> data = []
        >>> data.append('!NoteWorthyComposer(2.0)\n')
        >>> data.append('|AddStaff|\n')
        >>> data.append('|Clef|Type:Bass\n')
        >>> data.append('|TimeSig|Signature:4/4\n')
        >>> data.append('|Note|Dur:Whole|Pos:1\n')

        >>>
        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> s = nwt.parseList(data)
        >>> s.show('text')
        {0.0} <music21.stream.Part ...>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.BassClef>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Note E>

        '''
        # Main
        for pi in dataList:
            pi = pi.rstrip()
            if pi.startswith('|') is False:
                continue
            sections = pi.split('|')
            command = sections[1]
            attributes = {}
            for attribute in sections[2:]:
                try:
                    (name, value) = attribute.split(':', 1)
                    attributes[name] = value
                except ValueError:
                    if attribute.strip() == '':
                        pass
                    else:
                        raise NoteworthyTranslateException(
                            f'Cannot unpack value from {attribute} in {pi}')

            if command == 'Note':
                self.translateNote(attributes)
                self.lyricPosition += 1
            elif command == 'Clef':
                self.createClef(attributes)
            elif command == 'Rest':
                self.translateRest(attributes)
            elif command == 'Key':
                self.createKey(attributes)
            elif command == 'TimeSig':
                self.createTimeSignature(attributes)
            elif command == 'Chord':
                self.translateChord(attributes)
                self.lyricPosition += 1
            elif command == 'AddStaff':
                self.createPart()
                self.currentKey = key.KeySignature(0)
                self.activeAccidentals = {}
                self.lyrics = []
                self.lyricPosition = 0
            elif command == 'Lyric1':
                self.lyrics = self.createLyrics(attributes)
            elif command == 'Bar':
                self.createBarlines(attributes)
            elif command == 'Flow':
                self.createOtherRepetitions(attributes)
            elif command == 'DynamicVariance':
                self.createDynamicVariance(attributes)
            elif command == 'Dynamic':
                self.createDynamics(attributes)

        # Add the last Stuff
        if self.currentMeasure:
            self.currentPart.append(self.currentMeasure)

        self.score.insert(0, self.currentPart)

        # print('SHOW')
        # totalscore.show('text')
        # totalscore.show()
        return self.score

    def setDurationForObject(self, generalNote, durationInfo):
        '''
        generalNote could be a Note, Chord, or Rest

        DurationInfo is a string like:

            Whole,Dotted,Slur

        '''
        from music21 import noteworthy
        dictionaries = noteworthy.dictionaries

        parts = durationInfo.split(',')
        lengthNote = parts[0]
        thisNoteIsSlurred = False
        durationObject = duration.Duration(dictionaries['dictionaryNoteLength'][lengthNote])

        for kk in parts:
            if kk == 'Grace':
                # Now it doesn't work, the function for grace notes have to be added here
                environLocal.warn('skipping grace note')
                return
            elif kk == 'Slur':
                if self.withinSlur is False:
                    self.beginningSlurNote = generalNote
                thisNoteIsSlurred = True
            elif kk == 'Dotted':
                durationObject.dots = 1
            elif kk == 'DblDotted':
                durationObject.dots = 2

            elif kk in ('Triplet', 'Triplet=First', 'Triplet=End'):
                tup = duration.Tuplet(3, 2, durationObject.type)
                durationObject.appendTuplet(tup)

        generalNote.duration = durationObject

        # if Slur
        if self.withinSlur is True and thisNoteIsSlurred is False:
            music21SlurObj = spanner.Slur(self.beginningSlurNote, generalNote)
            self.currentMeasure.append(music21SlurObj)
            self.withinSlur = False
        elif thisNoteIsSlurred is True:
            self.withinSlur = True
        else:
            self.withinSlur = False

    def setTieFromPitchInfo(self, noteOrChord, pitchInfo):
        '''
        sets the tie status for a noteOrChord from the pitchInfo
        '''
        thisNoteBeginsATie = False
        thisNoteIsTied = False

        if pitchInfo[-1] == '^':
            if self.withinTie is False:
                thisNoteBeginsATie = True
            thisNoteIsTied = True
            self.withinTie = True

        # if Tied
        if thisNoteBeginsATie:
            noteOrChord.tie = tie.Tie('start')
        if self.withinTie is True and thisNoteIsTied is False:
            noteOrChord.tie = tie.Tie('stop')
            self.withinTie = False

    def getPitchFromPositionInfo(self, posInfo):
        '''
        returns a pitch object given the Pos: info

        removes ties and alteration signs.  Otherwise
        is same as getOnePitchFromPosition()


        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentClef = 'BASS'
        >>> p = nwt.getPitchFromPositionInfo('b3^')  # removes ties
        >>> p
        <music21.pitch.Pitch G-3>
        '''
        pos = posInfo.rstrip('^')  # remove any tie
        # What does this do???
        pos = pos.rstrip('x')
        pos = pos.rstrip('X')
        pos = pos.rstrip('z')
        p = self.getOnePitchFromPosition(pos)
        return p

    def getMultiplePitchesFromPositionInfo(self, posInfo):
        '''
        returns a list of pitch objects given the Pos:... info
        for a chord.


        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentClef = 'BASS'
        >>> pList = nwt.getMultiplePitchesFromPositionInfo('1,b3,5^')
        >>> pList
        [<music21.pitch.Pitch E3>, <music21.pitch.Pitch G-3>, <music21.pitch.Pitch B3>]
        '''
        # from music21 import noteworthy
        # dictionaries = noteworthy.dictionaries
        pos = posInfo.rstrip('^')  # remove any tie
        # What does this do???
        pos = pos.rstrip('x')
        pos = pos.rstrip('X')
        pos = pos.rstrip('z')
        pitchList = []

        for thisPos in pos.split(','):
            p = self.getOnePitchFromPosition(thisPos)
            pitchList.append(p)
        return pitchList

    def getOnePitchFromPosition(self, pos):
        '''
        get one pitch from a position...


        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentClef = 'BASS'
        >>> p = nwt.getOnePitchFromPosition('b3')
        >>> p
        <music21.pitch.Pitch G-3>
        >>> p.ps
        54.0
        '''
        accidental = ''
        if pos[0] in ['n', 'b', '#', 'x', 'v']:
            accidental = pos[0]
            pos = pos[1:]
            if accidental == 'b':
                accidental = '-'
            elif accidental == 'x':
                accidental = '##'
            elif accidental == 'v':
                accidental = '--'
        positionNote = int(pos)
        (noteStep, octave) = self.getStepAndOctaveFromPosition(positionNote)

        p = pitch.Pitch()
        p.step = noteStep
        p.octave = octave
        pName = p.nameWithOctave

        if accidental != '':
            p.accidental = pitch.Accidental(accidental)
            self.activeAccidentals[pName] = accidental
        # previous accidental in same bar that is still active
        elif pName in self.activeAccidentals:
            p.accidental = pitch.Accidental(self.activeAccidentals[pName])
        else:
            stepAccidental = self.currentKey.accidentalByStep(noteStep)
            if stepAccidental is not None:
                p.accidental = stepAccidental
        return p

    def getStepAndOctaveFromPosition(self, positionNote):
        '''
        Given an int representing the position on the staff for the
        current clef,
        returns a string for the step and an int for the octave


        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentClef = 'BASS'
        >>> (step, octave) = nwt.getStepAndOctaveFromPosition(3)
        >>> (step, octave)
        ('G', 3)
        '''
        from music21 import noteworthy
        dictionaries = noteworthy.dictionaries

        octave = 4
        currentClef = self.currentClef
        dictionary = ''

        minPosition = 1
        if currentClef == 'TREBLE8dw':
            octave = 4
            minPosition = 1
            dictionary = 'dictionaryTreble'
        elif currentClef == 'TREBLE8up':
            octave = 6
            minPosition = 1
            dictionary = 'dictionaryTreble'
        elif currentClef == 'BASS':
            octave = 3
            minPosition = -1
            dictionary = 'dictionaryBass'
        elif currentClef == 'BASS8dw':
            octave = 2
            minPosition = -1
            dictionary = 'dictionaryBass'
        elif currentClef == 'BASS8up':
            octave = 4
            minPosition = -1
            dictionary = 'dictionaryBass'
        elif currentClef == 'ALTO':
            octave = 4
            minPosition = 0
            dictionary = 'dictionaryAlto'
        elif currentClef == 'TENOR':
            octave = 3
            minPosition = -5
            dictionary = 'dictionaryTenor'
        else:  # 'TREBLE':
            octave = 5
            minPosition = 1
            dictionary = 'dictionaryTreble'

        while positionNote < minPosition or positionNote > (minPosition + 6):
            if positionNote < minPosition:
                positionNote = positionNote + 7
                octave = octave - 1
            if positionNote > (minPosition + 6):
                positionNote = positionNote - 7
                octave = octave + 1
        noteName = dictionaries[dictionary][positionNote]

        return (noteName, octave)

    def translateNote(self, attributes):
        r'''
        Translation of a music21 note from a NWC note.



        >>> measure = stream.Measure()
        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = measure
        >>> nwt.translateNote({'Dur': 'Half', 'Pos': '#-3'})
        >>> measure[0]
        <music21.note.Note F#>

        Note that the next note in the measure with the same position should
        inherit the last position's accidental:

        >>> nwt.translateNote({'Dur': 'Half', 'Pos': '-3'})
        >>> measure[1]
        <music21.note.Note F#>

        '''
        durationInfo = attributes['Dur']
        pitchInfo = attributes['Pos']

        n = note.Note()   # note!

        # durationInfo
        self.setDurationForObject(n, durationInfo)

        # pitchInfo
        self.setTieFromPitchInfo(n, pitchInfo)
        n.pitch = self.getPitchFromPositionInfo(pitchInfo)

        # if Lyrics
        if self.lyrics and self.lyricPosition < len(self.lyrics):
            n.addLyric(self.lyrics[self.lyricPosition])

        self.currentMeasure.append(n)

    def translateChord(self, attributes):
        r'''
        Translation of a music21 chord from a NWC one.

        >>> measure = stream.Measure()

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = measure
        >>> nwt.translateChord({'Dur': 'Half', 'Pos': '1,3,#5'})
        >>> measure[0]
        <music21.chord.Chord C5 E5 G#5>

        Chords also inherit accidentals:
        >>> nwt.translateChord({'Dur': 'Half', 'Pos': '1,3,5'})
        >>> measure[1]
        <music21.chord.Chord C5 E5 G#5>

        '''
        durationInfo = attributes['Dur']
        pitchInfo = attributes['Pos']

        c = chord.Chord()   # note!

        # durationInfo
        self.setDurationForObject(c, durationInfo)

        # pitchInfo
        self.setTieFromPitchInfo(c, pitchInfo)
        c.pitches = self.getMultiplePitchesFromPositionInfo(pitchInfo)

        # if Lyrics
        if self.lyrics and self.lyricPosition < len(self.lyrics):
            c.addLyric(self.lyrics[self.lyricPosition])

        self.currentMeasure.append(c)

    def translateRest(self, attributes):
        r'''
        Translation of a music21 rest.  Adds the rest to the given measure.



        >>> measureIn = stream.Measure()
        >>> measureIn.append(note.Note('C#4', type='half'))

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = measureIn
        >>> nwt.translateRest({'Dur': '8th,Dotted'})
        >>> nwt.translateRest({'Dur': '4th'})
        >>> measureIn.show('text')
        {0.0} <music21.note.Note C#>
        {2.0} <music21.note.Rest rest>
        {2.75} <music21.note.Rest rest>

        '''
        durationInfo = attributes['Dur']

        r = note.Rest()
        self.setDurationForObject(r, durationInfo)
        self.currentMeasure.append(r)

    def createClef(self, attributes):
        r'''
        Add a new clef to the current measure and return the currentClef.


        Clef lines should look like: \|Clef\|Type:ClefType  or
        \|Clef\|Type:ClefType\|OctaveShift:Octave Down (or Up)



        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.createClef({'Type': 'Treble'})
        >>> nwt.currentMeasure.show('text')
        {0.0} <music21.clef.TrebleClef>
        >>> nwt.currentClef
        'TREBLE'
        >>> nwt.createClef({'Type' : 'Bass', 'OctaveShift' : 'Octave Down'})
        >>> nwt.currentMeasure.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.clef.Bass8vbClef>




        If no clef can be found then it raises a NoteworthyTranslate exception


        >>> nwt.createClef({'Type' : 'OrangeClef'})
        Traceback (most recent call last):
        music21.noteworthy.translate.NoteworthyTranslateException: Did
            not find a proper clef in type, OrangeClef

        '''
        currentClef = None
        if 'OctaveShift' in attributes:
            if attributes['OctaveShift'] == 'Octave Down':
                octaveShift = -1
            elif attributes['OctaveShift'] == 'Octave Up':
                octaveShift = 1
            else:
                raise NoteworthyTranslateException(
                    f'Did not get a proper octave shift from {attributes[3]}')
        else:
            octaveShift = 0

        cl = attributes['Type']
        if cl == 'Treble':
            if octaveShift == 0:
                self.currentMeasure.append(clef.TrebleClef())
                currentClef = 'TREBLE'
            elif octaveShift == -1:
                self.currentMeasure.append(clef.Treble8vbClef())
                currentClef = 'TREBLE8dw'
            elif octaveShift == 1:
                self.currentMeasure.append(clef.Treble8vaClef())
                currentClef = 'TREBLE8up'

        elif cl == 'Bass':
            if octaveShift == 0:
                self.currentMeasure.append(clef.BassClef())
                currentClef = 'BASS'
            elif octaveShift == -1:
                self.currentMeasure.append(clef.Bass8vbClef())
                currentClef = 'BASS8dw'
            elif octaveShift == 1:
                self.currentMeasure.append(clef.Bass8vaClef())
                currentClef = 'BASS8up'

        elif cl == 'Alto':
            if octaveShift != 0:
                raise NoteworthyTranslateException('cannot shift octaves on an alto clef')
            self.currentMeasure.append(clef.AltoClef())
            currentClef = 'ALTO'
        elif cl == 'Tenor':
            if octaveShift != 0:
                raise NoteworthyTranslateException('cannot shift octaves on a tenor clef')
            self.currentMeasure.append(clef.TenorClef())
            currentClef = 'TENOR'
        if currentClef is None:
            raise NoteworthyTranslateException(f'Did not find a proper clef in type, {cl}')
        self.currentClef = currentClef

    def createKey(self, attributes):
        r'''
        Adds a new key signature to the given measure.
        Returns the number of sharps (negative for flats)



        >>> measureIn = stream.Measure()
        >>> measureIn.append(note.Rest(quarterLength=3.0))

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = measureIn
        >>> nwt.createKey({'Signature':'F#,C#,G#,D#'})
        >>> nwt.currentKey.sharps
        4
        >>> measureIn.show('text')
        {0.0} <music21.note.Rest rest>
        {3.0} <music21.key.KeySignature of 4 sharps>
        '''
        ke = attributes['Signature']
        currentSharps = 0
        for a in range(len(ke)):
            if ke[a] == '#':
                currentSharps = currentSharps + 1
            if ke[a] == 'b':
                currentSharps = currentSharps - 1
        currentKey = key.KeySignature(currentSharps)
        self.currentMeasure.append(currentKey)
        self.currentKey = currentKey

    def createTimeSignature(self, attributes):
        r'''
        Adding a time signature in the score.


        >>> measure = stream.Measure()
        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = measure
        >>> nwt.createTimeSignature({'Signature':'4/4'})
        >>> measure[0]
        <music21.meter.TimeSignature 4/4>
        '''
        times = attributes['Signature']
        if times == 'AllaBreve':  # These are strange cases
            times = '2/2'
        elif times == 'Common':
            times = '4/4'

        self.currentMeasure.append(meter.TimeSignature(times))

    def createPart(self):
        '''
        Add a new part to the score.
        '''
        if self.currentPart is None:
            self.currentPart = stream.Part()
            self.currentMeasure = stream.Measure()
        else:
            self.currentPart.append(self.currentMeasure)
            self.score.insert(0, self.currentPart)
            self.currentPart = stream.Part()
            self.currentMeasure = stream.Measure()

    def createBarlines(self, attributes):
        r'''
        Translates bar lines into music21.




        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentPart = stream.Part()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.createBarlines({'Style':'MasterRepeatOpen'})
        >>> nwt.currentMeasure
        <music21.stream.Measure 0 offset=0.0>
        >>> nwt.currentMeasure.leftBarline
        <music21.bar.Repeat direction=start>

        '''
        self.activeAccidentals = {}

        if 'Style' not in attributes:
            # pure barline
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()
            return

        style = attributes['Style']

        if style == 'MasterRepeatOpen':
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()
            self.currentMeasure.leftBarline = bar.Repeat(direction='start')

        elif style == 'MasterRepeatClose':
            self.currentMeasure.rightBarline = bar.Repeat(direction='end')
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()

        elif style == 'LocalRepeatOpen':
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()
            self.currentMeasure.leftBarline = bar.Repeat(direction='start')

        elif style == 'LocalRepeatClose':
            self.currentMeasure.rightBarline = bar.Repeat(direction='end')
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()

        elif style == 'Double':
            self.currentMeasure.rightBarline = bar.Barline('double')
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()

        elif style == 'SectionOpen':
            self.currentMeasure.rightBarline = bar.Barline('heavy-light')
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()
        elif style == 'SectionClose':
            self.currentMeasure.rightBarline = bar.Barline('final')
            self.currentPart.append(self.currentMeasure)
            self.currentMeasure = stream.Measure()
        else:
            raise NoteworthyTranslateException(f'cannot find a style {style} in our list')

    def createOtherRepetitions(self, attributes):
        r'''
        Repetitions like 'Coda', 'Segno' and some others.


        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.createOtherRepetitions({'Style' : 'ToCoda', 'Pos': '8',
        ...                             'Wide':'Y', 'Placement': 'BestFitForward'})
        >>> 'Coda' in nwt.currentMeasure[0].classes
        True
        '''
        # DaCapoAlFine - Coda - Segno - ToCoda
        style = attributes['Style']
        if style == 'DCalFine':
            g = repeat.DaCapoAlFine()
        elif style == 'Coda':
            g = repeat.Coda()
        elif style == 'ToCoda':
            g = repeat.Coda()
        elif style == 'Segno':
            g = repeat.Segno()
        elif style == 'DSalCoda':
            g = repeat.DalSegnoAlCoda()
        elif style == 'Fine':
            g = repeat.Fine()
        else:
            raise NoteworthyTranslateException(f'Cannot get style from {str(attributes)}')
        self.currentMeasure.append(g)

    def createDynamicVariance(self, attributes):
        r'''
        Adding dynamics like "crescendo" to the measure.


        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.createDynamicVariance({'Style' : 'Crescendo', 'Pos': '-6'})
        >>> nwt.currentMeasure.show('text')
        {0.0} <music21.dynamics.Crescendo>
        '''
        style = attributes['Style']
        g = None
        if style == 'Crescendo':
            g = dynamics.Crescendo()
        elif style == 'Decrescendo':
            g = dynamics.Diminuendo()
        else:
            pass
            # raise NoteworthyTranslateException('Cannot get style from %s' % str(attributes))
        if g is not None:
            self.currentMeasure.append(g)

    def createDynamics(self, attributes):
        r'''
        Adding dynamics like "fff", "pp", ... to the measure.


        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.createDynamics({'Style': 'fff', 'Pos': '-8'})
        >>> nwt.currentMeasure[0]
        <music21.dynamics.Dynamic fff>
        '''
        # Dynamic case
        if 'Style' in attributes:
            g = dynamics.Dynamic(attributes['Style'])
            self.currentMeasure.append(g)

    def createLyrics(self, attributes):
        r'''
        Get a list of lyrics from a Lyric line

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> lyricsList = nwt.createLyrics({'Text': '"Hello world"'})
        >>> lyricsList[0]
        'Hello'
        '''
        lyrics = []
        space = 0
        allText = attributes['Text']
        allText = allText.strip('"')
        allText = allText.replace('\r\n', ' ')
        allText = allText.replace('\r', ' ')
        allText = allText.replace('\n', ' ')
        for word in allText.split(' '):
            nou = 1
            for wordPart in word.split('-'):
                if space == 1:
                    nou = 0
                    space = 0
                for w in wordPart.split('\n'):
                    if nou != 1:
                        ll = f' -{w}'
                    else:
                        ll = w
                        nou = 0
                    if w == '':
                        space = 0  # if 'space=1', it will appear a '-' before the next syllable
                        ll = ' - '
                    lyrics.append(ll)
        return lyrics


class NoteworthyTranslateException(Music21Exception):
    pass


class Test(unittest.TestCase):

    def testBasic(self):
        nwcTranslatePath = common.getSourceFilePath() / 'noteworthy'
        simplePath = nwcTranslatePath / 'verySimple.nwctxt'
        myScore = NoteworthyTranslator().parseFile(simplePath)
        self.assertEqual(len(myScore.flat.notes), 1)
        self.assertEqual(str(myScore.flat.notes[0].name), 'E')
        self.assertEqual(str(myScore.flat.getElementsByClass('Clef')[0]),
                         '<music21.clef.BassClef>')

    def testKeySignatureAtBeginning(self):
        '''
        test a problem with accidentals at the end of one staff not
        being cleared at the beginning of the next

        showed up in Morley, "Since my tears and lamenting" where
        Staff 1 ended with a B-natural Picardy, and Staff
        2 began with a B in a flat key, but was showing up as B-natural also
        '''

        info = '''!NoteWorthyComposer(2.0)
|AddStaff|
|Clef|Type:Treble
|Key|Signature:Bb
|TimeSig|Signature:Common
|Tempo|Base:Half|Tempo:60|Pos:7|Visibility:Never
|Note|Dur:Half|Pos:2^|Opts:Stem=Down
|Bar
|Note|Dur:Half|Pos:2|Opts:Stem=Down
|Note|Dur:Half|Pos:n0|Opts:Stem=Down
|Bar
|AddStaff|
|Clef|Type:Treble
|Key|Signature:Bb
|TimeSig|Signature:Common
|Note|Dur:Half|Pos:0^|Opts:Stem=Down
|Bar
|Note|Dur:Half|Pos:0|Opts:Stem=Down
|Note|Dur:Half|Pos:0|Opts:Stem=Down
|Bar
!NoteWorthyComposer-End'''
        nwt = NoteworthyTranslator()
        s = nwt.parseString(info)
        # s.show('text')
        n1 = s.parts[1].getElementsByClass('Measure')[0].notes[0]
        self.assertEqual(n1.pitch.accidental.alter, -1.0)


class TestExternal(unittest.TestCase):  # pragma: no cover

    def testComplete(self):
        nwcTranslatePath = common.getSourceFilePath() / 'noteworthy'
        complete = nwcTranslatePath / 'NWCTEXT_Really_complete_example_file.nwctxt'
        # 'Part_OWeisheit.nwctxt' #

        myScore = NoteworthyTranslator().parseFile(complete)
        myScore.show()


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , TestExternal)
