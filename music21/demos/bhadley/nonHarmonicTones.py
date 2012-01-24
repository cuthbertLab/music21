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

def labelPassingTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True, markWithColor=False, color='#FF0000'):
    '''searches through all voices of all parts in a given music21 stream and
    identifies passing tones, then assigns a True/False value to the 
    note's :class:`~music21.editorial.NoteEditorial` object. The information is 
    stored as a miscellaneous attribute in the note editorial object, called 'isPassingTone'. 
    Access this data from any note object in the stream after running this method by typing

    for note in labeledStream.flat.getElementsByClass(music21.note.Note):
        print note.editorial.misc['isPassingTone']
    
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
    
    markWithColor (default = False) --> optionally label the identified passing tones with a color; default
    color is red. Change labeling color with color modifier/
    
    color (default = '#00FF00') --> color to label notes if markWithColor is True. Colors must be specified
    in a string HEX. For example, 
     color = '#FF0000' (red)
     color = '#00FF00' (green)
     color = '#0000FF' (blue)
     color = '#FFFF00' (yellow)
     color = '#00FFFF' (turquoise)
     color = '#FF00FF' (magenta)
     color = '#C0C0C0' (grey)
     color = '#FFFFFF' (white)
    
    '''

    for part in music21Stream.parts:
        notes = part.flat.getElementsByClass(music21.note.Note)
        index = 0
        for note in notes[1:len(notes) - 1]:
            index = index + 1
            if couldBePassingTone(note, notes[index - 1], notes[index + 1]):
                listOfTruths = []
                if checkForDissonance:
                    listOfTruths.append(not _noteContextIsConsonant(note, music21Stream))
                if checkForAccent:
                    listOfTruths.append(_beatIsUnaccented(note))
                if not (False in listOfTruths):
                    note.editorial.misc['isPassingTone'] = True
                    if markWithColor:
                        note.color = color
                else:
                    note.editorial.misc['isPassingTone'] = False
            else:
                note.editorial.misc['isPassingTone'] = False
                    
        notes[0].editorial.misc['isPassingTone'] = False
        notes[len(notes)-1].editorial.misc['isPassingTone'] = False
        
    if checkSimultaneous:
        music21Stream = _checkForSimultaneousLabels(music21Stream, markWithColor)
    return music21Stream
    
def labelNeighborTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True, markWithColor=False, color='#00FF00'):
    '''searches through all voices of all parts in a given music21 stream and
    identifies neighbor tones, then assigns a True/False value to the 
    note's :class:`~music21.editorial.NoteEditorial` object. The information is 
    stored as a miscellaneous attribute in the note editorial object, called 'isPassingTone'. 
    Access this data from any note object in the stream after running this method by typing

    for note in labeledStream.flat.getElementsByClass(music21.note.Note):
        print note.editorial.misc['isNeighborTone']
    
    From wikipedia:
    A neighbor tone (NT) is a nonchord tone that passes stepwise from a chord tone directly 
    above or below it (which frequently causes the NT to create dissonance with the chord) 
    and resolves to the same chord tone.
    
    Selectivity in labeling is provided by the following optional arguments:
    checkForDissonance (default = True) --> checks if the chord formed is dissonant, and only
    labels tone as a passing tone if the chord is dissonant.
    
    checkSimultaneous (default = True) --> iterates through every instance where simultaneous notes
    are labeled (with color) and if their durations are different, labels only the tone that has a shorter duration
    
    checkForAccent (default = True) --> only labels passing tones on unacented beats of the measure
    
    markWithColor (default = False) --> optionally label the identified neighbor tones with a color; default
    color is green. Change labeling color with color modifier/
    
    color (default = '#00FF00') --> color to label notes if markWithColor is True. Colors must be specified
    in a string HEX. For example, 
     color = '#FF0000' (red)
     color = '#00FF00' (green)
     color = '#0000FF' (blue)
     color = '#FFFF00' (yellow)
     color = '#00FFFF' (turquoise)
     color = '#FF00FF' (magenta)
     color = '#C0C0C0' (grey)
     color = '#FFFFFF' (white)
    
    '''
    for part in music21Stream.parts:
        notes = part.flat.getElementsByClass(music21.note.Note)
        index = 0
        for note in notes[1:len(notes) - 1]:
            index = index + 1
            if couldBeNeighborTone(note, notes[index - 1], notes[index + 1]):
                listOfTruths = []
                if checkForDissonance:
                    listOfTruths.append(not _noteContextIsConsonant(note, music21Stream))
                if checkForAccent:
                    listOfTruths.append(_beatIsUnaccented(note))
                if not (False in listOfTruths):
                    note.editorial.misc['isNeighborTone'] = True
                    if markWithColor:
                        note.color = color
                else:
                    note.editorial.misc['isNeighborTone'] = False
            else:
                note.editorial.misc['isNeighborTone'] = False         
        notes[0].editorial.misc['isNeighborTone'] = False
        notes[len(notes)-1].editorial.misc['isNeighborTone'] = False
    if checkSimultaneous:
        music21Stream = _checkForSimultaneousLabels(music21Stream, markWithColor)
    return music21Stream
    
def _checkForSimultaneousLabels(preLabeledMusic21Stream, checkPT=True, checkNT=True, markWithColor=False, color='#000000'):
    '''
    If after running a non-harmonic labeling method (such as labelPassingTones or labelNeighborTones)
    you find that there are simultaneous pitches labeled when at least one of those pitches must
    not be labeled, run this method to sort out which has the shorter duration, and this one remains
    labeled while the other one becomes unlabeled. Optionally label with colors (as in with label passing tones)
    
    This method is run after every label non-harmonic tone method (labelPassingTones and labelNeighborTones)
    
    if markWithColor = True, then the identified non-harmonic tones that are returned to normal status are 
    set back to the default color of black.
    
    Method steps through each part, and checks that part against each of the other parts. This method
    should unlabel all simultaneous sounding like-type non-harmonic tones that have the same duration if a shorter
    duraiton like-type non-harmonic tone is sounding simultaneously. For example, in four voices (SATB)
    if the soprano and alto both have a passing tone labeled but each is a quarter note, and the tenor 
    has a neighbor tone labeled but it is an eighth note, the soprano and alto labels are removed 
    (editorial.misc['isPassingTone'] set to False and their color optionally returned to black. If the bass
    is labeled as a neighbor tone and is simultaneous, there is no consequence because it is not of the same
    'type' of non-harmonic tone.
    
    '''
    partNumberBeingSearched = -1
    while partNumberBeingSearched < len(preLabeledMusic21Stream.parts) - 1:
        partNumberBeingSearched += 1
        for note in preLabeledMusic21Stream.parts[partNumberBeingSearched].flat.getElementsByClass(music21.note.Note):
            try:
                note.editorial.misc['isPassingTone']
            except:
                note.editorial.misc['isPassingTone'] = False
            try:
                note.editorial.misc['isNeighborTone']
            except:
                note.editorial.misc['isNeighborTone'] = False
                  
            if checkPT and note.editorial.misc['isPassingTone'] == True:
                for part in preLabeledMusic21Stream.parts[partNumberBeingSearched:]:
                    for simultaneousNote in part.flat.getElementsByOffset(note.offset).flat.getElementsByClass(music21.note.Note):
                        if simultaneousNote.editorial.misc['isPassingTone'] == True:
                            if simultaneousNote.duration.quarterLength > note.duration.quarterLength:
                                simultaneousNote.editorial.misc['isPassingTone'] = False
                                simultaneousNote.color = color
                            elif simultaneousNote.duration.quarterLength < note.duration.quarterLength:
                                note.color = color
                                note.editorial.misc['isPassingTone'] = False
                            else:
                                pass
            if checkPT and note.editorial.misc['isNeighborTone'] == True:
                for part in preLabeledMusic21Stream.parts[partNumberBeingSearched:]:
                    for simultaneousNote in part.flat.getElementsByOffset(note.offset).flat.getElementsByClass(music21.note.Note):
                        if simultaneousNote.editorial.misc['isNeighborTone'] == True:
                            if simultaneousNote.duration.quarterLength > note.duration.quarterLength:
                                simultaneousNote.editorial.misc['isNeighborTone'] = False
                                simultaneousNote.color = color
                            elif simultaneousNote.duration.quarterLength < note.duration.quarterLength:
                                note.color = color
                                note.editorial.misc['isNeighborTone'] = False
                            else:
                                pass
                                #if the two durations are equal, then how do we know which is the passing tone
                                #and which is the chordal tone???
    
    return preLabeledMusic21Stream
    
def _noteContextIsConsonant(note, music21Stream):
    '''
    determines if the given note is consonant when compared vertically to all
    other pitches sounding simultaneously. Consonance is determined by making
    a chord of the simultaneous pitches, then calling chord's isConsonant() on that chord.
    
    TODO:
    This is a very tricky method – will it work with measures?
    ???What does this mean...'work with measures', no, you can't pass
    a measure in instead of a note object. Would you want to test to see if an entire
    measure is consonant? If so...that would be an entirely seperate method I think
    
    DONE:
    Is there a way to do it so as not to require the user to give the offset or partNoteIsIn?  
    (there should be, but it’ll require knowing a bit 
    more about how streams and .sites work (.sites are lists of places where an 
    object could appear).  
    Fix: yes. I was not thinking when I required the user to pass in those two parameters
    I wrote the code to extract the necessary information solely given the note object and 
    the music21 stream. the code relies on the method getOffsetBySite()
    
    DONE:
    What will happen if there’s a rest in another part at 
    the same moment as the note? will the previous note get added to the chord 
    even though it’s no longer sounding?  
    Fix: getElementAtorBefore now grabs the rest object, but doesn't add
    it to the pitches list. 
    '''
    pitches = []
    #hypothetically (and in actuality if used correctly), note.offset should be equal to offsetOfPitchToIdentify
    offsetOfPitchToIdentify =  note.getOffsetBySite(music21Stream.flat)

    for part in music21Stream.parts:
        value = part.flat.getElementAtOrBefore(offsetOfPitchToIdentify, classList=['Pitch', 'Note', 'Chord', music21.note.Rest])
        if hasattr(value, 'classes') and ('Chord' in value.classes):
            value = value.pitches
        if not (hasattr(value, 'classes') and ('Rest' in value.classes)):
            pitches.append(value)

    c = music21.chord.Chord(pitches)
    return c.isConsonant()

def couldBePassingTone(noteToAnalyze, leftNote, rightNote):
    '''
    checks to see if noteToAnalyze([0]) could be a passing tone between leftNote([1])
    and rightNote([2])
    
    checks if the two intervals are steps and if these steps
    are moving in the same direction. Does NOT check if tone is non harmonic
    
    Accepts pitch or note objects; method is dependent on octave information
    >>> from music21 import *
    >>> couldBePassingTone(pitch.Pitch('D3'), pitch.Pitch('C3'), pitch.Pitch('E3'))
    True
    >>> couldBePassingTone(pitch.Pitch('C4'), pitch.Pitch('B3'), pitch.Pitch('D4'))
    True
    >>> couldBePassingTone(pitch.Pitch('F3'), pitch.Pitch('E-3'), pitch.Pitch('G-3'))
    True
    >>> couldBePassingTone(pitch.Pitch('C3'), pitch.Pitch('C3'), pitch.Pitch('C3'))
    False
    >>> couldBePassingTone(pitch.Pitch('C3'), pitch.Pitch('A3'), pitch.Pitch('D3'))
    False
    
    Accepts pitch or note objects
    >>> couldBePassingTone(note.Note('d'), note.Note('c'), note.Note('e'))
    True
    
    Directionality must be maintained:
    >>> couldBePassingTone(pitch.Pitch('C4'), pitch.Pitch('B##3'), pitch.Pitch('D--4'))
    False
   
    If no octave is given then ._defaultOctave is used.  This is generally octave 4:
    >>> couldBePassingTone(pitch.Pitch('D'), pitch.Pitch('C'), pitch.Pitch('E'))
    True
    >>> couldBePassingTone(pitch.Pitch('D'), pitch.Pitch('C4'), pitch.Pitch('E'))
    True
    >>> couldBePassingTone(pitch.Pitch('D'), pitch.Pitch('C5'), pitch.Pitch('E'))
    False
    
    SPELLING MATTERS!
    This method depends on how the notes are 'spelled', or how they actually 
    looks on the staff. The following four tests are all enharmonically equivalent, 
    based on the progression B - C - C# but the spelling of each makes the 
    first three return False but the last is actually True because when 
    it's written on the staff, B - C - Db it actually looks like a passing tone.
    
    >>> couldBePassingTone(note.Note('C4'), note.Note('B3'), note.Note('B##3'))
    False
    >>> couldBePassingTone(note.Note('C4'), note.Note('B3'), note.Note('C#4'))
    False
    >>> couldBePassingTone(note.Note('C4'), note.Note('A##3'), note.Note('E---4'))
    False
    >>> couldBePassingTone(note.Note('C4'), note.Note('B3'), note.Note('D-4'))
    True
    
    '''

    leftToRight = music21.interval.Interval(leftNote, rightNote)
    iLeft = music21.interval.Interval(leftNote, noteToAnalyze)
    iRight = music21.interval.Interval(noteToAnalyze, rightNote)
    return leftToRight.generic.isSkip and iLeft.isStep and iRight.isStep and (iLeft.direction * iRight.direction == 1)



def couldBeNeighborTone(noteToAnalyze, leftNote, rightNote):
    '''checks if the two intervals are steps and if these steps
    are moving in the opposite direction. Does NOT check if tone is non harmonic
    
    Accepts pitch or note objects; method is dependent on octave information
    
    >>> from music21 import *
    >>> couldBeNeighborTone(pitch.Pitch('F3'), pitch.Pitch('E3'), pitch.Pitch('E3'))
    True
    >>> couldBeNeighborTone(pitch.Pitch('C5'), pitch.Pitch('B-4'), pitch.Pitch('B-4'))
    True
    >>> couldBeNeighborTone(pitch.Pitch('F3'), pitch.Pitch('E-3'), pitch.Pitch('E-4'))
    False
    >>> couldBeNeighborTone(pitch.Pitch('D3'), pitch.Pitch('C3'), pitch.Pitch('E3'))
    False
    >>> couldBeNeighborTone(pitch.Pitch('C3'), pitch.Pitch('A3'), pitch.Pitch('D3'))
    False'''
    
    
    iLeft = music21.interval.Interval(leftNote, noteToAnalyze)
    iRight = music21.interval.Interval(noteToAnalyze, rightNote)
    return leftNote.nameWithOctave == rightNote.nameWithOctave and iLeft.isStep and iRight.isStep and (iLeft.direction * iRight.direction == -1)

def _beatIsUnaccented(note):
    #print note.beatStrength < 0.5
    try:
        return note.beatStrength < 0.5
    except:
        return False
    
if __name__ == "__main__":

    #music21.mainTest()
    
    import doctest
    doctest.testmod()

    
    #s = music21.converter.parse('''\
#C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/\
#XML11_worksheets/S11_6_IB.xml''')
    #from music21 import corpus
    #paths = corpus.getComposer('bach')
    #for path in paths[0:1]:
    #    s = corpus.parse(path)
    
    #s = labelPassingTones(s, markWithColor=True)
    #s = labelNeighborTones(s, markWithColor=True)
    #for note in s.flat.getElementsByClass(music21.note.Note):
    #    print note
    #    print 'PT', note.editorial.misc['isPassingTone']
    #    print 'NT', note.editorial.misc['isNeighborTone']
        
    #s = labelPassingTones(s, markWithColor=True)
    #labelNeighborTones(s, markWithColor=True).show()
