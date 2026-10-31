# ------------------------------------------------------------------------------
# Name:         noteworthy/translate.py
# Purpose:      translates Noteworthy Composer's NWCTXT format
#
# Authors:      Jordi Bartolome
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2011-2026 Michael Scott Asato Cuthbert
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
# As expression
# |TempoVariance|Style:Fermata|Pause:3|Pos:-4
#
# As spanner
# |TempoVariance|Style:Accelerando|Pos:-6
#
#
# Beams:
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
from __future__ import annotations

import re
import unittest

from music21 import bar
from music21 import chord
from music21 import clef
from music21 import common
from music21 import duration
from music21 import dynamics
from music21 import environment
from music21 import expressions
from music21.exceptions21 import Music21Exception
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21 import tempo
from music21 import tie

from music21.common.numberTools import opFrac
from music21.common.types import OffsetQL
from music21.noteworthy.dictionaries import dictionaries

environLocal = environment.Environment('noteworthy.translate')


# initializations

# file = open("Part_OWeisheit.nwctxt")


class NoteworthyTranslator:
    '''
    stores all the data about the current parse context (whether we're in a slur, tuplet, etc.)
    '''

    def __init__(self):
        self.currentPart = None
        self.currentMeasure = None
        self.measureNumber = 0
        self.currentEnding = 1
        self.repeatedMeasures = []
        self.score = stream.Score()

        self.currentClef = 'TREBLE'
        self.currentKey = key.KeySignature(0)

        self.slurStarts: dict[int, note.GeneralNote] = {}
        self.tiedPositions: set[str] = set()
        self.positionMeasure: stream.Measure|None = None
        self.measurePosition: OffsetQL = 0.0

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
                    if command == 'Chord' and (name in ('Dur', 'Pos')):
                        if attributes.get(name) is None:
                            attributes[name] = [value]
                        else:
                            attributes[name].append(value)
                    else:
                        attributes[name] = value
                except ValueError:
                    if attribute.strip() == '':
                        pass
                    else:
                        raise NoteworthyTranslateException(
                            f'Cannot unpack value from {attribute} in {pi}')

            try:
                if command == 'AddStaff':
                    self.createStaff(attributes)
                elif command == 'Bar':
                    self.createBarlines(attributes)
                elif command == 'Chord':
                    self.translateChord(attributes)
                    self.lyricPosition += 1
                elif command == 'Clef':
                    self.createClef(attributes)
                elif command == 'Dynamic':
                    self.createDynamics(attributes)
                elif command == 'DynamicVariance':
                    self.createDynamicVariance(attributes)
                elif command == 'Ending':
                    self.createEnding(attributes)
                elif command == 'Flow':
                    self.createOtherRepetitions(attributes)
                elif command == 'Key':
                    self.createKey(attributes)
                elif command == 'Lyric1':
                    self.lyrics = self.createLyrics(attributes)
                elif command == 'Note':
                    self.translateNote(attributes)
                    self.lyricPosition += 1
                elif command == 'Rest':
                    self.translateRest(attributes)
                elif command == 'RestChord':
                    self.translateRestChord(attributes)
                    self.lyricPosition += 1
                elif command == 'SongInfo':
                    self.createSongInfo(attributes)
                elif command == 'StaffInstrument':
                    self.createStaffInstrument(attributes)
                elif command == 'Tempo':
                    self.createTempo(attributes)
                elif command == 'Text':
                    self.createText(attributes)
                elif command == 'TimeSig':
                    self.createTimeSignature(attributes)
            except Exception as e:
                print(f'Cannot create object from "{attributes}"')
                raise NoteworthyTranslateException from e

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

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> n = note.Note()
        >>> nwt.setDurationForObject(n, 'Half')
        >>> n.duration
        <music21.duration.Duration 2.0>
        '''
        parts = durationInfo.split(',')
        lengthNote = parts[0]
        durationObject = duration.Duration(dictionaries['dictionaryNoteLength'][lengthNote])

        for kk in parts:
            if kk == 'Grace':
                durationObject = durationObject.getGraceDuration()
            elif kk == 'Dotted':
                durationObject.dots = 1
            elif kk == 'DblDotted':
                durationObject.dots = 2

            elif kk in ('Triplet', 'Triplet=First', 'Triplet=End'):
                tup = duration.Tuplet(3, 2, durationObject.type)
                durationObject.appendTuplet(tup)

        generalNote.duration = durationObject

    def setTieFromPitchInfo(self, noteOrChord, pitchInfo):
        '''
        Sets the ties of a note or chord from its Pos info.  A position ending
        in ``^`` is tied to the next note at that position, whatever group or
        voice it comes in.

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> c = chord.Chord('C5 E5')
        >>> nwt.setTieFromPitchInfo(c, '1^,3')
        >>> [n.tie for n in c]
        [<music21.tie.Tie start>, None]
        >>> c = chord.Chord('C5 E5')
        >>> nwt.setTieFromPitchInfo(c, '1,3')
        >>> [n.tie for n in c]
        [<music21.tie.Tie stop>, None]
        '''
        notes = list(noteOrChord) if isinstance(noteOrChord, chord.Chord) else [noteOrChord]
        for n, posInfo in zip(notes, pitchInfo.split(',')):
            tiedOn = posInfo.endswith('^')
            position = re.search(r'-?\d+', posInfo).group()
            tiedFrom = position in self.tiedPositions
            if tiedFrom and tiedOn:
                n.tie = tie.Tie('continue')
            elif tiedOn:
                n.tie = tie.Tie('start')
            elif tiedFrom:
                n.tie = tie.Tie('stop')
            if tiedOn:
                self.tiedPositions.add(position)
            else:
                self.tiedPositions.discard(position)

    def getPitchFromPositionInfo(self, posInfo):
        # noinspection PyShadowingNames
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
        pitchList = []

        for thisPos in posInfo.split(','):
            p = self.getPitchFromPositionInfo(thisPos)
            pitchList.append(p)
        return pitchList

    def getOnePitchFromPosition(self, pos):
        # noinspection PyShadowingNames
        '''
        Get one pitch from a position:

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
        # noinspection PyShadowingNames
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
        currentClef = self.currentClef
        if currentClef == 'TREBLE8dw':
            octave = 4
            minPosition = 1
            dictionary = dictionaries['dictionaryTreble']
        elif currentClef == 'TREBLE8up':
            octave = 6
            minPosition = 1
            dictionary = dictionaries['dictionaryTreble']
        elif currentClef in ('BASS', 'PERCUSSION'):
            octave = 3
            minPosition = -1
            dictionary = dictionaries['dictionaryBass']
        elif currentClef == 'BASS8dw':
            octave = 2
            minPosition = -1
            dictionary = dictionaries['dictionaryBass']
        elif currentClef == 'BASS8up':
            octave = 4
            minPosition = -1
            dictionary = dictionaries['dictionaryBass']
        elif currentClef == 'ALTO':
            octave = 4
            minPosition = 0
            dictionary = dictionaries['dictionaryAlto']
        elif currentClef == 'TENOR':
            octave = 3
            minPosition = -5
            dictionary = dictionaries['dictionaryTenor']
        else:  # 'TREBLE':
            octave = 5
            minPosition = 1
            dictionary = dictionaries['dictionaryTreble']

        while positionNote < minPosition or positionNote > (minPosition + 6):
            if positionNote < minPosition:
                positionNote = positionNote + 7
                octave = octave - 1
            if positionNote > (minPosition + 6):
                positionNote = positionNote - 7
                octave = octave + 1
        noteName = dictionary[positionNote]

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

        p = self.getPitchFromPositionInfo(pitchInfo)

        if self.currentClef == 'PERCUSSION':
            n = note.Unpitched()
            n.displayStep = p.step
            n.displayOctave = p.octave
        else:
            n = note.Note(p)   # note!

        # durationInfo
        self.setDurationForObject(n, durationInfo)

        # pitchInfo
        self.setTieFromPitchInfo(n, pitchInfo)

        self.addCurrentLyric(n)
        self.appendSimultaneous([(n, durationInfo)])

    def translateChord(self, attributes):
        r'''
        Translation of a music21 chord from a NWC one.

        >>> measure = stream.Measure()

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = measure
        >>> nwt.translateChord({'Dur': ['Half'], 'Pos': ['1,3,#5']})
        >>> measure[0]
        <music21.chord.Chord C5 E5 G#5>

        Chords also inherit accidentals:
        >>> nwt.translateChord({'Dur': ['Half'], 'Pos': ['1,3,5']})
        >>> measure[1]
        <music21.chord.Chord C5 E5 G#5>
        '''
        groups = list(zip(attributes['Dur'], attributes['Pos']))
        if 'Dur2' in attributes:
            groups.append((attributes['Dur2'], attributes['Pos2']))
        chords = [(self.createChord(durationInfo, pitchInfo), durationInfo)
                  for durationInfo, pitchInfo in groups]
        self.addCurrentLyric(chords[0][0])
        self.appendSimultaneous(chords)

    def translateRestChord(self, attributes: dict[str, str]) -> None:
        '''
        Translation of a NWC rest chord: a rest and the chord sounding with it.

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.translateRestChord({'Dur': 'Half', 'Dur2': '4th', 'Pos2': '-1,1'})
        >>> nwt.currentMeasure.show('text')
        {0.0} <music21.stream.Voice 0>
            {0.0} <music21.chord.Chord A4 C5>
        {0.0} <music21.stream.Voice 1>
            {0.0} <music21.note.Rest half>

        * New in v11.
        '''
        c = self.createChord(attributes['Dur2'], attributes['Pos2'])
        r = note.Rest()
        self.setDurationForObject(r, attributes['Dur'])
        self.addCurrentLyric(c)
        self.appendSimultaneous([(c, attributes['Dur2']), (r, attributes['Dur'])])

    def createChord(self, durationInfo: str, pitchInfo: str) -> chord.Chord:
        '''
        Returns a chord from the Dur and Pos info of one group of NWC chord notes.

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.createChord('8th', '-1,1^')
        <music21.chord.Chord A4 C5>

        * New in v11.
        '''
        c = chord.Chord()
        self.setDurationForObject(c, durationInfo)
        c.pitches = self.getMultiplePitchesFromPositionInfo(pitchInfo)
        self.setTieFromPitchInfo(c, pitchInfo)
        return c

    def addCurrentLyric(self, generalNote: note.GeneralNote) -> None:
        '''
        Gives a note or chord the current lyric syllable, if there is one.

        * New in v11.
        '''
        if self.lyrics and self.lyricPosition < len(self.lyrics):
            generalNote.addLyric(self.lyrics[self.lyricPosition])

    def appendSimultaneous(self, generalNotes: list[tuple[note.GeneralNote, str]]) -> None:
        '''
        Places notes, chords or rests, each with its Dur info, at the current
        position in the measure, and moves the position on by the shortest of
        them.  When more than one starts together, or a voice is still
        sounding, each goes in a voice that is free at that position.  A slur
        in the Dur info runs to the next note or rest in the same voice.

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.appendSimultaneous([(note.Note('C5', type='half'), 'Half'),
        ...                         (note.Note('A4'), '4th')])
        >>> nwt.appendSimultaneous([(note.Note('B4'), '4th')])
        >>> nwt.currentMeasure.show('text')
        {0.0} <music21.stream.Voice 0>
            {0.0} <music21.note.Note C>
        {0.0} <music21.stream.Voice 1>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>

        * New in v11.
        '''
        measure = self.currentMeasure
        if self.positionMeasure is not measure:
            self.positionMeasure = measure
            self.measurePosition = measure.highestTime
        offset = self.measurePosition

        voices = list(measure.voices)
        if not voices and len(generalNotes) > 1:
            firstVoice = stream.Voice(id=0)
            notes = [(n.offset, n) for n in measure.getElementsByClass(note.GeneralNote)]
            measure.remove([n for unused, n in notes])
            for noteOffset, n in notes:
                firstVoice.insert(noteOffset, n)
            measure.insert(0, firstVoice)
            voices.append(firstVoice)
        # the voices free at the offset, those that end there first
        freeVoices = sorted((v for v in voices if v.highestTime <= offset),
                            key=lambda v: -v.highestTime)
        for gn, durationInfo in generalNotes:
            if not voices:
                measure.insert(offset, gn)
                voiceId = 0
            else:
                if freeVoices:
                    voice = freeVoices.pop(0)
                else:
                    voice = stream.Voice(id=len(voices))
                    measure.insert(0, voice)
                    voices.append(voice)
                voice.insert(offset, gn)
                voiceId = voice.id
            self.setSlur(gn, voiceId, 'Slur' in durationInfo.split(','))
        self.measurePosition = opFrac(offset + min(gn.quarterLength for gn, unused in generalNotes))

    def setSlur(self, generalNote: note.GeneralNote, voiceId: int, slurred: bool) -> None:
        '''
        Starts, continues or ends a slur in one voice: a slur runs from the
        first slurred note in a row to the next note that is not slurred.

        * New in v11.
        '''
        if slurred:
            self.slurStarts.setdefault(voiceId, generalNote)
        elif voiceId in self.slurStarts:
            self.currentMeasure.append(spanner.Slur(self.slurStarts.pop(voiceId), generalNote))

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
        {2.0} <music21.note.Rest dotted-eighth>
        {2.75} <music21.note.Rest quarter>
        '''
        durationInfo = attributes['Dur']

        r = note.Rest()
        self.setDurationForObject(r, durationInfo)
        self.appendSimultaneous([(r, durationInfo)])

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
        >>> nwt.createClef({'Type' : 'Percussion'})
        >>> nwt.currentMeasure.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.clef.Bass8vbClef>
        {0.0} <music21.clef.PercussionClef>

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
        elif cl == 'Percussion':
            c = clef.PercussionClef()
            c.line = 2
            self.currentMeasure.append(c)
            currentClef = 'PERCUSSION'

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
        {0.0} <music21.note.Rest dotted-half>
        {3.0} <music21.key.KeySignature of 4 sharps>
        '''

        currentSharps = 0
        for attribute in attributes['Signature']:
            if attribute == '#':
                currentSharps += 1
            elif attribute == 'b':
                currentSharps -= 1
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

        m = meter.TimeSignature(times)
        self.currentMeasure.append(m)

    def createPart(self):
        '''
        Add a new part to the score.
        '''
        if self.currentPart is not None:
            self.currentPart.append(self.currentMeasure)
            self.score.insert(0, self.currentPart)

        self.currentPart = stream.Part()
        self.currentMeasure = stream.Measure()
        self.measureNumber = 0

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
            self.currentMeasure = stream.Measure(number=self.measureNumber)
            if len(self.repeatedMeasures) > 0:
                self.repeatedMeasures.append(self.currentMeasure)
            self.measureNumber += 1
            return

        if len(self.repeatedMeasures) > 0:
            rbSpanner = spanner.RepeatBracket(self.repeatedMeasures, number=self.currentEnding)
            self.currentPart.append(rbSpanner)

            self.repeatedMeasures = []

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

        self.currentMeasure.number = self.measureNumber
        self.measureNumber += 1

    def createOtherRepetitions(self, attributes):
        r'''
        Repetitions like 'Coda', 'Segno' and some others.

        >>> nwt = noteworthy.translate.NoteworthyTranslator()
        >>> nwt.currentMeasure = stream.Measure()
        >>> nwt.createOtherRepetitions({'Style' : 'ToCoda', 'Pos': '8',
        ...                             'Wide':'Y', 'Placement': 'BestFitForward'})
        >>> isinstance(nwt.currentMeasure[0], repeat.Coda)
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
            # raise NoteworthyTranslateException(f'Cannot get style from {attributes}')
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

    def createStaff(self, attributes):
        self.createPart()
        self.currentKey = key.KeySignature(0)
        self.activeAccidentals = {}
        self.lyrics = []
        self.lyricPosition = 0
        self.currentPart.partName = attributes.get('Name')
        self.currentPart.partAbbreviation = attributes.get('Name')

    def createStaffInstrument(self, attributes):
        patch = int(attributes.get('Patch', 0))

        staffInstru = instrument.instrumentFromMidiProgram(patch)
        readTranspo = int(attributes.get('Trans', 0))
        staffInstru.transposition = interval.Interval(readTranspo)
        self.currentPart.append(staffInstru)

    def createText(self, attributes):
        text = attributes['Text']
        # Rehearsal is associated to the score while TextExpression is staff-associated.
        expr = expressions.TextExpression(text)
        expr.placement = 'above' if int(attributes.get('Pos')) < 0 else 'below'
        expr.style.relativeY = attributes.get('Pos')
        self.currentMeasure.append(expr)

    def createSongInfo(self, attributes):
        title = attributes.get('Title')
        author = attributes.get('Author')
        md = metadata.Metadata()
        md.title = title
        md.author = author
        self.score.append(md)

    def createEnding(self, attributes):
        end = attributes['Endings']
        if self.currentMeasure.leftBarline is None:
            self.currentMeasure.leftBarline = bar.Barline()
        self.repeatedMeasures = [self.currentMeasure]
        endingType = end.split(',')[0]
        self.currentEnding = int(endingType)

    def createTempo(self, attributes):
        tempo_value = attributes['Tempo']
        mm = tempo.MetronomeMark(number=int(tempo_value))
        self.currentMeasure.insert(0, mm)



class NoteworthyTranslateException(Music21Exception):
    pass


class Test(unittest.TestCase):

    def testBasic(self):
        nwcTranslatePath = common.getSourceFilePath() / 'noteworthy'
        simplePath = nwcTranslatePath / 'verySimple.nwctxt'
        myScore = NoteworthyTranslator().parseFile(simplePath)
        self.assertEqual(len(myScore[note.Note]), 1)
        self.assertEqual(str(myScore[note.Note].first().name), 'E')
        self.assertEqual(str(myScore[clef.Clef].first()),
                         '<music21.clef.BassClef>')

    @staticmethod
    def firstMeasureContents(lines: list[str]) -> list[tuple[float, float, str]]:
        '''
        The offset, length and pitches of each note and rest in the first measure.

        AI-assisted (Claude).
        '''
        s = NoteworthyTranslator().parseList(['|AddStaff|', '|Clef|Type:Treble'] + lines)
        m = s.parts.first().getElementsByClass(stream.Measure).first()
        return sorted((float(e.getOffsetInHierarchy(m)), float(e.quarterLength),
                       ' '.join(p.nameWithOctave for p in e.pitches) or 'rest')
                      for e in m.recurse().notesAndRests)

    def testChordWithTwoDurations(self):
        self.assertEqual(self.firstMeasureContents([
            '|Note|Dur:4th|Pos:0',
            '|Chord|Dur:8th|Pos:-4,n-3,b-2,#-1,x0,v1,2x|Opts:Stem=Down,Crescendo'
            + '|Dur2:8th,DblDotted|Pos2:3x',
            '|Note|Dur:4th|Pos:-5',
        ]), [
            (0.0, 1.0, 'B4'),
            (1.0, 0.5, 'E4 F4 G-4 A#4 B##4 C--5 D5'),
            (1.0, 0.875, 'E5'),
            (1.5, 1.0, 'D4'),
        ])

    def testRestChord(self):
        self.assertEqual(self.firstMeasureContents([
            '|Note|Dur:4th|Pos:0',
            '|RestChord|Dur:Half|Opts:Stem=Up|Dur2:4th|Pos2:-1,1',
            '|RestChord|Dur:4th|Dur2:4th|Pos2:-5',
            '|Note|Dur:4th|Pos:0',
        ]), [
            (0.0, 1.0, 'B4'),
            (1.0, 1.0, 'A4 C5'),
            (1.0, 2.0, 'rest'),
            (2.0, 1.0, 'D4'),
            (2.0, 1.0, 'rest'),
            (3.0, 1.0, 'B4'),
        ])

    def testNotesAfterGroupsFollowThePosition(self):
        self.assertEqual(self.firstMeasureContents([
            '|Chord|Dur:8th|Pos:-4|Dur2:8th,DblDotted|Pos2:3',
            '|Note|Dur:4th|Pos:-5',
            '|Note|Dur:4th|Pos:-4',
        ]), [
            (0.0, 0.5, 'E4'),
            (0.0, 0.875, 'E5'),
            (0.5, 1.0, 'D4'),
            (1.5, 1.0, 'E4'),
        ])
        self.assertEqual(self.firstMeasureContents([
            '|RestChord|Dur:Half|Dur2:4th|Pos2:-1,1',
            '|Note|Dur:Half|Pos:0',
            '|Note|Dur:4th|Pos:1',
        ]), [
            (0.0, 1.0, 'A4 C5'),
            (0.0, 2.0, 'rest'),
            (1.0, 2.0, 'B4'),
            (3.0, 1.0, 'C5'),
        ])
        # notes moved into the first voice keep their offsets
        self.assertEqual(self.firstMeasureContents([
            '|Note|Dur:4th,Triplet|Pos:0',
            '|Note|Dur:4th,Triplet|Pos:1',
            '|Note|Dur:4th,Triplet|Pos:2',
            '|Chord|Dur:4th|Pos:-1|Dur2:Half|Pos2:3',
        ]), [
            (0.0, 2 / 3, 'B4'),
            (2 / 3, 2 / 3, 'C5'),
            (4 / 3, 2 / 3, 'D5'),
            (2.0, 1.0, 'A4'),
            (2.0, 2.0, 'E5'),
        ])

    @staticmethod
    def parseTreble(lines: list[str]) -> stream.Score:
        return NoteworthyTranslator().parseList(['|AddStaff|', '|Clef|Type:Treble'] + lines)

    def testTiesFollowTheirPositions(self):
        def ties(lines):
            return sorted((n.pitch.nameWithOctave, float(c.getOffsetInHierarchy(s)),
                           n.tie.type if n.tie else None)
                          for s in [self.parseTreble(lines)]
                          for c in s.recurse().getElementsByClass(chord.Chord)
                          for n in c)

        self.assertEqual(ties([
            '|Chord|Dur:4th|Pos:1^|Dur2:4th|Pos2:3',
            '|Chord|Dur:4th|Pos:1|Dur2:4th|Pos2:3',
        ]), [('C5', 0.0, 'start'), ('C5', 1.0, 'stop'), ('E5', 0.0, None), ('E5', 1.0, None)])
        self.assertEqual(ties([
            '|Chord|Dur:4th|Pos:1^|Dur2:4th|Pos2:3^',
            '|Chord|Dur:4th|Pos:1|Dur2:4th|Pos2:3',
        ]), [('C5', 0.0, 'start'), ('C5', 1.0, 'stop'),
             ('E5', 0.0, 'start'), ('E5', 1.0, 'stop')])

    def testSlursStayInTheirVoice(self):
        def slurs(lines):
            return [[repr(e) for e in sl.getSpannedElements()]
                    for sl in self.parseTreble(lines).recurse().getElementsByClass(spanner.Slur)]

        self.assertEqual(slurs([
            '|RestChord|Dur:Half|Dur2:4th,Slur|Pos2:-1,1',
            '|Note|Dur:4th|Pos:0',
        ]), [['<music21.chord.Chord A4 C5>', '<music21.note.Note B>']])
        self.assertEqual(slurs([
            '|Chord|Dur:4th,Slur|Pos:1|Dur2:4th|Pos2:3',
            '|Chord|Dur:4th|Pos:1|Dur2:4th|Pos2:3',
        ]), [['<music21.chord.Chord C5>', '<music21.chord.Chord C5>']])

    def testRestChordFromBinary(self):
        import struct
        from music21.noteworthy import binaryTranslate
        # a rest chord in a version 1.75 file: object type 18, visibility, ten
        # data bytes (the rest's duration first, the number of notes ninth),
        # then a quarter note at staff position 0
        for restDuration, dumped, restLength in (
                (1, '|RestChord|Dur:Half|Dur2:4th|Pos2:0', 2.0),
                (2, '|RestChord|Dur:4th|Dur2:4th|Pos2:0', 1.0)):
            data = struct.pack('<hB10s', 18, 0, bytes([restDuration, 0, 0, 0, 0, 0, 0, 0, 1, 0]))
            data += struct.pack('<hB6sbB', 8, 0, bytes([2, 0, 0, 0, 0, 0]), 0, 5)
            nwcc = binaryTranslate.NWCConverter()
            nwcc.version = 175
            nwcc.fileContents = data
            restChord = binaryTranslate.NWCObject(parserParent=nwcc)
            restChord.parse()
            self.assertEqual(restChord.dumpMethod(restChord), dumped)
            self.assertEqual(self.firstMeasureContents([dumped]),
                             [(0.0, 1.0, 'B4'), (0.0, restLength, 'rest')])

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
        n1 = s.parts[1].getElementsByClass(stream.Measure).first().notes.first()
        self.assertEqual(n1.pitch.accidental.alter, -1.0)


class TestExternal(unittest.TestCase):
    show = True

    def testComplete(self):
        nwcTranslatePath = common.getSourceFilePath() / 'noteworthy'
        complete = nwcTranslatePath / 'NWCTEXT_Really_complete_example_file.nwctxt'
        # 'Part_OWeisheit.nwctxt' #

        myScore = NoteworthyTranslator().parseFile(complete)
        if self.show:
            myScore.show()


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , TestExternal)
