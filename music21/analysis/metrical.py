# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         metrical.py
# Purpose:      Tools for metrical analysis
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''Various tools and utilities for doing metrical or rhythmic analysis. 

See the chapter :ref:`overviewMeters` for more information on defining metrical structures in music21.
'''


import music21.stream
import unittest

from music21 import environment
_MOD = "analysis.metrical.py"
environLocal = environment.Environment(_MOD)




def labelBeatDepth(streamIn):
    '''
    Modify a Stream in place by annotating metrical analysis symbols.

    This assumes that the Stream is already partitioned into Measures.

    
    >>> s = stream.Stream()
    >>> ts = meter.TimeSignature('4/4')
    >>> s.insert(0, ts)
    >>> n = note.Note()
    >>> s.repeatAppend(n, 4)
    >>> post = analysis.metrical.labelBeatDepth(s)
    >>> ts.beatSequence
    <MeterSequence {{1/8+1/8}+{1/8+1/8}+{1/8+1/8}+{1/8+1/8}}>
    '''
#     ts = streamIn.flat.getElementsByClass(
#          music21.meter.TimeSignature)[0]
    

    for m in streamIn.getElementsByClass(music21.stream.Measure):

        # this will search contexts
        ts = m.getTimeSignatures(sortByCreationTime=False)[0]

        ts.beatSequence.subdivideNestedHierarchy(depth=3)

        for n in m.notesAndRests:
            if n.tie != None:
                environLocal.printDebug(['note, tie', n, n.tie, n.tie.type])
                if n.tie.type == 'stop':
                    continue
            for unused_i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('*')

    return streamIn

def thomassenMelodicAccent(streamIn):
    '''
    adds a attribute melodicAccent to each note of a :class:`~music21.stream.Stream` object
    according to the method postulated in Joseph M. Thomassen, "Melodic accent: Experiments and 
    a tentative model," ''Journal of the Acoustical Society of America'', Vol. 71, No. 6 (1982) pp. 
    1598-1605; with, Erratum, ''Journal of the Acoustical Society of America'', Vol. 73, 
    No. 1 (1983) p.373, and in David Huron and Matthew Royal, "What is melodic accent? Converging evidence 
    from musical practice." ''Music Perception'', Vol. 13, No. 4 (1996) pp. 489-516. 
    
    Similar to the humdrum melac_ tool.
    
    .. _melac: http://www.music-cog.ohio-state.edu/Humdrum/commands/melac.html

    Takes in a Stream of :class:`~music21.note.Note` objects (use `.flat.notes` to get it, or
    better `.flat.getElementsByClass('Note')` to filter out chords) and adds the attribute to
    each.  Note that Huron and Royal's work suggests that melodic accent has a correlation
    with metrical accent only for solo works/passages; even treble passages do not have a
    strong correlation. (Gregorian chants were found to have a strong ''negative'' correlation
    between melodic accent and syllable onsets)
    
    Following Huron's lead, we assign a `melodicAccent` of 1.0 to the first note in a piece
    and take the accent marker of the first interval alone to the second note and 
    of the last interval alone to be the accent of the last note.
    
    Example from Thomassen, figure 5:
    
    
    >>> s = converter.parse('tinynotation: 7/4 c4 c c d e d d')
    >>> analysis.metrical.thomassenMelodicAccent(s.flat.notes)
    >>> for n in s.flat.notes:
    ...    (n.pitch.nameWithOctave, n.melodicAccent)
    ('C4', 1.0)
    ('C4', 0.0)
    ('C4', 0.0)
    ('D4', 0.33)
    ('E4', 0.5561)
    ('D4', 0.17)
    ('D4', 0.0)

    '''
    # we use .ps instead of Intervals for speed, since
    # we just need perceived contours
    maxNotes = len(streamIn) - 1
    p2Accent = 1.0
    for i,n in enumerate(streamIn):
        if i == 0:
            n.melodicAccent = 1.0
            continue
        elif i == maxNotes:
            n.melodicAccent = p2Accent
            continue
        
        lastPs = streamIn[i-1].ps
        thisPs = n.ps
        nextPs = streamIn[i+1].ps
        
        if lastPs == thisPs and thisPs == nextPs:
            thisAccent = 0.0
            nextAccent = 0.0
        elif lastPs != thisPs and thisPs == nextPs:
            thisAccent = 1.0
            nextAccent = 0.0
        elif lastPs == thisPs and thisPs != nextPs:
            thisAccent = 0.0
            nextAccent = 1.0
        elif lastPs < thisPs and thisPs > nextPs:
            thisAccent = 0.83
            nextAccent = 0.17
        elif lastPs > thisPs and thisPs < nextPs:
            thisAccent = 0.71
            nextAccent = 0.29
        elif lastPs < thisPs and thisPs < nextPs:
            thisAccent = 0.33
            nextAccent = 0.67
        elif lastPs > thisPs and thisPs > nextPs:
            thisAccent = 0.5
            nextAccent = 0.5
        
        n.melodicAccent = thisAccent * p2Accent
        p2Accent = nextAccent
        



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testSingle(self):
        '''Need to test direct meter creation w/o stream
        '''
        from music21 import stream, note, meter
        s = stream.Stream()
        ts = meter.TimeSignature('4/4')

        s.append(ts)
        n = note.Note()
        n.quarterLength = 1
        s.repeatAppend(n, 4)

        n = note.Note()
        n.quarterLength = .5
        s.repeatAppend(n, 8)

        s = s.makeMeasures()
        s = labelBeatDepth(s)

        s.show()            



class Test(unittest.TestCase):
    '''Unit tests
    '''

    def runTest(self):
        pass
    

    def setUp(self):
        pass


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [labelBeatDepth]


if __name__ == "__main__":
    music21.mainTest(Test, TestExternal)


#------------------------------------------------------------------------------
# eof


