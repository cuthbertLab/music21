# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         nonHarmonicTones.py
# Purpose:      locater routines to label (with colors) non-harmonic tones
#               for use in music21 theory checker routines
#
# Authors:      Beth Hadley
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21

class NonHarmonicException(music21.Music21Exception):
    pass

def labelPassingTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True):
    '''searches through all voices of all parts in a given music21 stream and
    colors red the passing tones.
    
    From wikipedia:
    Passing tone: A passing tone (PT) is a non-harmonic tone prepared 
    by a chord tone a step above or below it and resolved by continuing in the same 
    direction stepwise to the next chord tone (which is either part of the same 
    chord or of the next chord in the harmonic progression). Where there are two 
    non-chord notes before the resolution we have double passing tones.
    
    Selectivity in labeling is provided by the following optional arguments:
    checkForDissonance (default = True) --> checks if the chord formed is dissonant, and only
    labels tone as a passing tone if the chord is dissonant.
    
    checkSimultaneous (default = True) --> iterates through every instance where simultaneous notes
    are labeled (with color) and if their durations are different, labels only the tone that has a shorter duration
    
    checkForAccent (default = True) --> only labels passing tones on unacented beats of the measure
    '''

    for part in music21Stream.parts:
        notes = part.flat.getElementsByClass(music21.note.Note)
        index = 0
        for note in notes[1:len(notes) - 1]:
            index = index + 1
            if _isPassingTone(note, notes[index - 1], notes[index + 1]):
                listOfTruths = []
                if checkForDissonance:
                    listOfTruths.append(not _chordIsConsonant(note, note.offset, part, music21Stream))
                if checkForAccent:
                    listOfTruths.append(_beatIsUnaccented(note))
                if not (False in listOfTruths):
                    note.color = '#FF0000'
                
    if checkSimultaneous:
        music21Stream = _checkForSimultaneousLabels(music21Stream)
    return music21Stream
    
def labelNeighborTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True):
    '''searches through all voices of all parts in a given music21 stream and
    colors green the passing tones.
    
    From wikipedia:
    A neighbor tone (NT) is a nonchord tone that passes stepwise from a chord tone directly 
    above or below it (which frequently causes the NT to create dissonance with the chord) 
    and resolves to the same chord tone.
    
    Selectivity in labeling is provided by the following optional arguments:
    checkForDissonance (default = True) --> checks if the chord formed is dissonant, and only
    labels tone as a passing tone if the chord is dissonant.
    
    checkSimultaneous (default = True) --> iterates through every instance where simultaneous notes
    are labeled (with color) and if their durations are different, labels only the tone that has a shorter duration
    
    checkForAccent (defulat = True) --> only labels passing tones on unacented beats of the measure
    
    From wikipedia:
    A neighbor tone (NT) is a nonchord tone that passes stepwise from a chord tone directly 
    above or below it (which frequently causes the NT to create dissonance with the chord) 
    and resolves to the same chord tone.
    '''
    for part in music21Stream.parts:
        notes = part.flat.getElementsByClass(music21.note.Note)
        index = 0
        for note in notes[1:len(notes) - 1]:
            index = index + 1
            if _isNeighborTone(note, notes[index - 1], notes[index + 1]):
                listOfTruths = []
                if checkForDissonance:
                    listOfTruths.append(not _chordIsConsonant(note, note.offset, part, music21Stream))
                if checkForAccent:
                    listOfTruths.append(_beatIsUnaccented(note))
                if not (False in listOfTruths):
                    note.color = '#00FF00'
                
    if checkSimultaneous:
        music21Stream = _checkForSimultaneousLabels(music21Stream)
    return music21Stream
    
def _checkForSimultaneousLabels(coloredMusic21Stream):
    '''
    If after running a non-harmonic labeling method (such as labelPassingTones or labelNeighborTones)
    you find that there are simultaneous pitches labeled when at least one of those pitches must
    not be labeled, run this method to sort out which has the shorter duration, and this one remains
    labeled while the other one becomes unlabeled
    
    '''
    for note in coloredMusic21Stream.parts[0].flat.getElementsByClass(music21.note.Note):
        if note.color != '#000000':
            for part in coloredMusic21Stream.parts[1:]:
                for simultaneousNote in part.flat.getElementsByOffset(note.offset).flat.getElementsByClass(music21.note.Note):
                    if simultaneousNote.color != '#000000':
                        if simultaneousNote.duration.quarterLength > note.duration.quarterLength:
                            simultaneousNote.color = '#000000'
                        elif simultaneousNote.duration.quarterLength < note.duration.quarterLength:
                            note.color = '#000000'
                        else:
                            pass
                            #if the two durations are equal, then how do we know which is the passing tone
                            #and which is the chordal tone???
    
    return coloredMusic21Stream
    
def _chordIsConsonant(note, offsetOfPitchToIdentify, partNoteIsIn, music21Stream):
    pitches = []
    pitches.append(note)
    
    for part in music21Stream.parts:
        
        if part != partNoteIsIn: #only look at the parts 
            #of music21Stream that isn't the part the pitch being analyzed is in
            value = part.flat.getElementAtOrBefore(offsetOfPitchToIdentify, classList=['Pitch', 'Note', 'Chord'])
    
            if hasattr(value, 'classes') and ('Chord' in value.classes):
                value = value.pitches
            
            pitches.append(value)
    c = music21.chord.Chord(pitches)
    return c.isConsonant()
    
   
def _isPassingTone(noteToAnalyze, leftNote, rightNote):
    '''checks if the two intervals are steps and if these steps
    are moving in the same direction. Does NOT check if tone is non harmonic
    
    Accepts pitch or note objects; method is dependent on octave information
    
    >>> _isPassingTone(music21.pitch.Pitch('D3'), music21.pitch.Pitch('C3'), music21.pitch.Pitch('E3'))
    True
    >>> _isPassingTone(music21.pitch.Pitch('C4'), music21.pitch.Pitch('B3'), music21.pitch.Pitch('D4'))
    True
    >>> _isPassingTone(music21.pitch.Pitch('F3'), music21.pitch.Pitch('E-3'), music21.pitch.Pitch('G-3'))
    True
    >>> _isPassingTone(music21.pitch.Pitch('C3'), music21.pitch.Pitch('C3'), music21.pitch.Pitch('C3'))
    False
    >>> _isPassingTone(music21.pitch.Pitch('C3'), music21.pitch.Pitch('A3'), music21.pitch.Pitch('D3'))
    False
    '''
    iLeft = music21.interval.Interval(leftNote, noteToAnalyze)
    iRight = music21.interval.Interval(noteToAnalyze, rightNote)
    return iLeft.isStep and iRight.isStep and (iLeft.direction * iRight.direction == 1)

def _isNeighborTone(noteToAnalyze, leftNote, rightNote):
    '''checks if the two intervals are steps and if these steps
    are moving in the opposite direction. Does NOT check if tone is non harmonic
    
    Accepts pitch or note objects; method is dependent on octave information
    
    >>> _isNeighborTone(music21.pitch.Pitch('F3'), music21.pitch.Pitch('E3'), music21.pitch.Pitch('E3'))
    True
    >>> _isNeighborTone(music21.pitch.Pitch('C5'), music21.pitch.Pitch('B-4'), music21.pitch.Pitch('B-4'))
    True
    >>> _isNeighborTone(music21.pitch.Pitch('F3'), music21.pitch.Pitch('E-3'), music21.pitch.Pitch('E-4'))
    False
    >>> _isNeighborTone(music21.pitch.Pitch('D3'), music21.pitch.Pitch('C3'), music21.pitch.Pitch('E3'))
    False
    >>> _isNeighborTone(music21.pitch.Pitch('C3'), music21.pitch.Pitch('A3'), music21.pitch.Pitch('D3'))
    False'''
    iLeft = music21.interval.Interval(leftNote, noteToAnalyze)
    iRight = music21.interval.Interval(noteToAnalyze, rightNote)
    return iLeft.isStep and iRight.isStep and (iLeft.direction * iRight.direction == -1)

def _beatIsUnaccented(note):
    #print note.beatStrength < 0.5
    try:
        return note.beatStrength < 0.5
    except:
        return False
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
    #s = music21.converter.parse('''\
#C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/\
#XML11_worksheets/S11_6_IB.xml''')

    #s = labelPassingTones(s)
    #labelNeighborTones(s).show()
