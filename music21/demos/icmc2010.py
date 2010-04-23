#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         icmc2010.py
# Purpose:      icmc2010.py
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import unittest, doctest

import music21
from music21 import *

from copy import deepcopy


#-------------------------------------------------------------------------------
# not being used

def bergEx01(show=True):
    
    # berg, violin concerto, measure 64-65, p12
    # triplets should be sextuplets

    humdata = '''
**kern
*M2/4
=1
24r
24g#
24f#
24e
24c#
24f
24r
24dn
24e-
24gn
24e-
24dn
=2
24e-
24f#
24gn
24b-
24an
24gn
24gn
24f#
24an
24cn
24a-
24en
=3
*-
'''

    score = humdrum.parseData(humdata).stream[0]
    if show:
        score.show()
   
    ts = score.getElementsByClass(meter.TimeSignature)[0]
   
# TODO: what is the best way to do this now that 
# this raises a TupletException for being frozen?
#     for thisNote in score.flat.notes:
#         thisNote.duration.tuplets[0].setRatio(12, 8)

    for thisMeasure in score.getElementsByClass(stream.Measure):
        thisMeasure.clef = deepcopy(ts)
        thisMeasure.makeBeams()

    if show:
        score.show()



def showDots(show=True):
    
    score = corpus.parseWork('bach/bwv281.xml') 
    partBass = score.getElementById('Bass')
    ts = partBass.flat.getElementsByClass(
         meter.TimeSignature)[0]
    
    ts.beat.partition(1)
    for h in range(len(ts.beat)):
        ts.beat[h] = ts.beat[h].subdivide(2)
        for i in range(len(ts.beat[h])):
            ts.beat[h][i] = \
                ts.beat[h][i].subdivide(2)
            for j in range(len(ts.beat[h][i])):
                ts.beat[h][i][j] = \
                    ts.beat[h][i][j].subdivide(2)
    
    for m in partBass.measures:
        for n in m.notes:
            for i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('*')
    if show:
        partBass.measures[0:7].show() 




def findRaisedSevenths(show=True):
    import music21
    from music21 import corpus, meter, stream

    score = corpus.parseWork('bach/bwv366.xml')  
    ts = score.flat.getElementsByClass(
        meter.TimeSignature)[0]
    ts.beat.partition(3)

    found = stream.Stream()
    count = 0
    for part in score:
        found.insert(count, 
            part.flat.getElementsByClass(
            music21.clef.Clef)[0])
        for i in range(len(part.measures)):
            m = part.measures[i]
            for n in m.notes:
                if n.name == 'C#': 
                    n.addLyric('%s, m. %s' % (          
        part.getInstrument().partName[0], 
        m.measureNumber))
                    n.addLyric('beat %s' %
        ts.getBeat(n.offset))
                    found.insert(count, n)
                    count += 4
    if show:
        found.show('musicxml')



def oldAccent(show=True):
    from music21 import corpus, meter, articulations
    
    score = corpus.parseWork('bach/bwv366.xml')
    partBass = score.getElementById('Bass')
    
    ts = partBass.flat.getElementsByClass(meter.TimeSignature)[0]
    ts.beat.partition(['3/8', '3/8'])
    ts.accent.partition(['3/8', '3/8'])
    ts.setAccentWeight([1, .5])
    
    for m in partBass.measures:
        lastBeat = None
        for n in m.notes:
            beat, progress = ts.getBeatProgress(n.offset)
            if beat != lastBeat and progress == 0:
                if n.tie != None and n.tie.type == 'stop':
                    continue
                if ts.getAccentWeight(n.offset) == 1:
                    mark = articulations.StrongAccent()
                elif ts.getAccentWeight(n.offset) == .5:
                    mark = articulations.Accent()
                n.articulations.append(mark)
                lastBeat = beat
            m = m.sorted
    
    if show:
        partBass.measures[0:8].show('musicxml')



class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''Test non-showing functions
        '''
        for func in [bergEx01, showDots, findRaisedSevenths]:
            func(show=False)

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''Test showing functions
        '''
        #  
        for func in [bergEx01, showDots, findRaisedSevenths]:
            func(show=True)


if __name__ == "__main__":

    bergEx01()
    #music21.mainTest(Test)

