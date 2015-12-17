# -*- coding:utf-8 -*-
#--------------------------------------------------------
# Name:         gatherAccidentals.py
# Purpose:      Demo for music21 documentation
#
# Authors:      Hugh Zabriskie
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#--------------------------------------------------------
'''
Have you ever wondered whether Bach uses more sharps than flats in the Chorales? With just a
few lines of code, music21 allows you to quickly answer this question.

Defined below is two functions that can solve this question. getAccidentalCount() combs through 
a score and returns of dictionary containing a tally of each type of accidental found in the input 
score (a music21.stream.Score object). getAccidentalCountSum() is simply a helpful extension of 
getAccidentalCount() and is meant for counting accidentals in a batch of scores.
 
These tallies are dictionaries. Dictionaries are ideal for this situation since they are simple and 
mutable data structures that can associate each type of accidental with a positive integer corresponding
to the number of occurrences of that accidental. Both getAccidentalCount() and getAccidentalCountSum() 
return a dictionary designed in this way. We use _initializeTally() to generate the initial dictionary and 
_excludeZeros() after searching the score to remove accidentals from the dictionary that were not found at all.
The purpose of this is to simplify the data structure by removing keys for uncommon accidentals (i.e. the triple-
sharp and the quadruple-flat). However, both functions have an excludeZeros option (default: true) that allows you
to keep all accidentals in the dictionary regardless of the number of occurrences.
   
How does getAccidentalCount work? Well, it first creates our tally object, which will be updated by incrementing the
appropriate key that corresponds to the newly found accidental. As a basic validation check, we can check that our
input score is in a fact a music21.stream.Stream object, and if it isn't we throw an exception. Next, we "flatten" the
score and extract a list of notes using music21.stream.Stream.flat and music21.stream.Stream.notes. Finally, the loop
in getAccidentalCount() simply iterates though the notes in the work and updates the tally object each time it comes
across an accidental. Interestingly, we are not simply iterating through notes. The .notes method also gathers chords,
and indeed we do find chords within a voice in some of the Chorales, so we must account for that. The chord is then
de-constructed into each of its pitches, and the pitches are then checked for accidentals with pitch.accidental.

Look at the bottom of the tests to see how these functions are used to count the total accidentals in the Bach Chorales.

Based on this demo, can you figure out how to determine how many accidentals occur on the beat versus off the beat? How
is it similar to the demo below? What are your corner cases?
Here's some inspiration:
"Some art is off the beat, but 'Mostart' is on the beat."

'''

from music21 import exceptions21
from music21 import stream
from music21 import note
from music21 import pitch
from music21 import corpus
import unittest



#-------------------------------------------------------- 

def getAccidentalCount(score, includeNonAccidentals=False, excludeZeros=True):
    '''
    Given a score, return a dictionary with keys as accidentals and values corresponding to
    the number of occurrences of each accidental.
    
    The possible accidentals are listed in pitch.Accidental.listNames(). 
    
    For the sake of brevity, any accidental not found at all will be deleted 
    from the dictionary before being returned. This can be prevented by setting
    excludeZeros to False.
    
    Optionally you can count for notes without accidentals as
    'natural' if includeNonAccidentals = True.
    
    >>> from pprint import pprint
    >>> from music21 import *
    >>> s1 = stream.Stream()
    >>> demos.gatherAccidentals.getAccidentalCount(s1)
    {}
    
    >>> s2 = stream.Stream()
    >>> note1 = note.Note("C4")
    >>> note2 = note.Note("C#4")
    >>> note3 = note.Note("D-4")
    >>> for note in [note1, note2, note3]:
    ...    s2.append(note)
    >>> pprint(demos.gatherAccidentals.getAccidentalCount(s2))
    {'flat': 1, 'sharp': 1}
    >>> pprint(demos.gatherAccidentals.getAccidentalCount(s2, True))
    {'flat': 1, 'natural': 1, 'sharp': 1}
    
    >>> s = corpus.parse('bach/bwv66.6') 
    >>> demos.gatherAccidentals.getAccidentalCount(s)
    {'sharp': 87}
    
    '''
    # check for non-streams
    if not score.isStream:
        raise GatherAccidentalsException("Input score must be a music21.stream.Stream object")
    notes = score.flat.notes
    tally = _initializeTally()
    for obj in notes:
        if obj.isChord:  # react to chords
            plist = obj.pitches
        elif obj.isNote:
            plist = [obj.pitch]
        for p in plist:
            accidental = p.accidental
            if accidental is None:
                if includeNonAccidentals:
                    tally['natural'] +=1
                continue
            tally[accidental.name] += 1
    return _deleteZeros(tally, excludeZeros)
    
#-------------------------------------------------------- 

def getAccidentalCountSum(scores, includeNonAccidentals=False, excludeZeros=True):
    '''
    An extension of getAccidentalCount(). Given a list of scores, return an AccidentalSum
    containing a tally of accidentals for all scores in the list.

    >>> from pprint import pprint
    >>> s1 = stream.Stream()
    >>> s1.append(note.Note('C4'))
    >>> s2 = stream.Score()         # all types of streams are valid
    >>> s2.append(note.Note('C#4'))
    >>> demos.gatherAccidentals.getAccidentalCountSum([s1, s2])
    {'sharp': 1}
    >>> pprint(demos.gatherAccidentals.getAccidentalCountSum([s1, s2], True))
    {'natural': 1, 'sharp': 1}
    
    >>> s3 = corpus.parse('bach/bwv7.7')
    >>> s4 = corpus.parse('bach/bwv66.6')
    >>> pprint(demos.gatherAccidentals.getAccidentalCountSum([s3, s4], True))
    {'natural': 324, 'sharp': 195}
    '''
    tally = _initializeTally()
    for score in scores:
        assert score.isStream
        scoreTally = getAccidentalCount(score, includeNonAccidentals, False)
        # dict.update() won't suffice; list() for Python v3
        for k in list(scoreTally.keys()):
            tally[k] += scoreTally[k]
    return _deleteZeros(tally, excludeZeros)
    
            
#-------------------------------------------------------- 
# HELPER METHODS

def _initializeTally():
    '''
    Private method.
    TODO: change to pitch.Accidental.listNames()
    
    >>> accidentalTally = demos.gatherAccidentals._initializeTally()
    >>> from pprint import pprint as pp
    >>> pp(accidentalTally)
    {'double-flat': 0,
     'double-sharp': 0,
     'flat': 0,
     'half-flat': 0,
     'half-sharp': 0,
     'natural': 0,
     'one-and-a-half-flat': 0,
     'one-and-a-half-sharp': 0,
     'quadruple-flat': 0,
     'quadruple-sharp': 0,
     'sharp': 0,
     'triple-flat': 0,
     'triple-sharp': 0}

    '''
    tally = dict.fromkeys(pitch.Accidental.listNames(), 0)
    return tally
    

def _deleteZeros(tally, excludeZeros):
    ''' 
    Private method.
    Searches the tally for keys with values of 0 and removes them.
    The updated tally is then returned.
    Usually this involves deleting the triple-flats and quadruple-sharps.
    
    >>> from pprint import pprint
    >>> dict = {'a': 5, 'b': 3, 'c': 0}
    >>> pprint(demos.gatherAccidentals._deleteZeros(dict, True))
    {'a': 5, 'b': 3}
    '''
    if excludeZeros:
        for k in list(tally.keys()):
            if tally[k] is 0:
                del tally[k]
    return tally

#--------------------------------------------------------   
    
class GatherAccidentalsException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------- 

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testGetAccidentalCountBasic(self):
        s = stream.Stream()
        self.assertEqual(len(s.flat.notes), 0) # the stream should be empty
        self.assertEqual(getAccidentalCount(s), {})

    def testGetAccidentalCountIntermediate(self):
        s = stream.Stream()
        s.append(note.Note("C4"))   # no accidental
        s.append(note.Note("C#4"))  # sharp
        s.append(note.Note("D-4"))  # flat
        self.assertEqual(getAccidentalCount(s), {'flat': 1, 'sharp': 1})
        self.assertEqual(getAccidentalCount(s, True), {'flat': 1, 'sharp': 1, 'natural': 1})
        
        note4 = note.Note("C4")
        self.assertIsNone(note4.pitch.accidental)
        note4.pitch.accidental = pitch.Accidental('natural')  # add a natural accidental
        s.append(note4)
        self.assertEqual(getAccidentalCount(s), {'flat': 1, 'sharp': 1, 'natural': 1})
        
    def testGetAccidentalCountAdvanced(self):
        s = corpus.parse('bach/bwv7.7')
        tally = getAccidentalCount(s)
        self.assertEqual(tally, {'sharp': 108, 'natural': 7})
        tally = getAccidentalCount(s, True)
        self.assertEqual(tally, {'sharp': 108, 'natural': 246})
        totalNotes = len(s.flat.notes)
        self.assertEqual(totalNotes, tally['sharp'] + tally['natural'])
    
    def testGetAccidentalCountSumBasic(self):
        s1 = stream.Stream()
        self.assertEqual(getAccidentalCountSum([s1]), {})
        
    def testGetAccidentalCountSumIntermediate(self):
        s1 = stream.Stream()
        s2 = stream.Stream()
        s2.append(note.Note('D-2'))
        s2.append(note.Note('F#5'))
        self.assertEqual(getAccidentalCountSum([s1, s2]), {'flat': 1, 'sharp': 1})
    
    def testGetAccidentalCountSumAdvanced(self):
        s1 = corpus.parse('bach/bwv7.7')
        s2 = corpus.parse('bach/bwv66.6')
        totalNotes = len(s1.flat.notes) + len(s2.flat.notes)
        tally = getAccidentalCountSum([s1, s2], True)
        self.assertEqual(tally, {'sharp': 195, 'natural': 324})
        self.assertEqual(totalNotes, tally['sharp'] + tally['natural'])
        

class TestSlow(unittest.TestCase):
    
    def runTest(self):
        pass

    def testAccidentalCountBachChorales(self):
        # the total number of accidentals in the Bach Chorales
        chorales = list( corpus.chorales.Iterator() )
        self.assertEqual(getAccidentalCountSum(chorales, True), 
                         {'double-sharp': 4, 'flat': 7886, 'natural': 79869, 'sharp': 14940})
            
    
if __name__ == "__main__":
    from music21 import base
    base.mainTest(Test) # replace 'Test' with 'TestSlow' to test it on all 371 Bach Chorales.
        