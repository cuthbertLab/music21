# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         icmc2010.py
# Purpose:      icmc2010.py
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-10 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------


import unittest

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
    from music21 import humdrum, meter, stream
    score = humdrum.parseData(humdata).stream[0]
    if show:
        score.show()
   
    ts = score.flat.getElementsByClass(meter.TimeSignature)[0]
   
# TODO: what is the best way to do this now that 
# this raises a TupletException for being frozen?
#     for thisNote in score.flat.notes:
#         thisNote.duration.tuplets[0].setRatio(12, 8)

    for thisMeasure in score.getElementsByClass(stream.Measure):
        thisMeasure.clef = deepcopy(ts)
        thisMeasure.makeBeams(inPlace=True)

    if show:
        score.show()



def showDots(show=True):
    from music21 import corpus, meter
    score = corpus.parse('bach/bwv281.xml') 
    partBass = score.getElementById('Bass')
    ts = partBass.flat.getElementsByClass(
         meter.TimeSignature)[0]
    
    ts.beatSequence.partition(1)
    for h in range(len(ts.beatSequence)):
        ts.beatSequence[h] = ts.beatSequence[h].subdivide(2)
        for i in range(len(ts.beatSequence[h])):
            ts.beatSequence[h][i] = \
                ts.beatSequence[h][i].subdivide(2)
            for j in range(len(ts.beatSequence[h][i])):
                ts.beatSequence[h][i][j] = \
                    ts.beatSequence[h][i][j].subdivide(2)
    
    for m in partBass.getElementsByClass('Measure'):
        for n in m.notes:
            for i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('*')
    if show:
        partBass.getElementsByClass('Measure')[0:7].show() 




def findRaisedSevenths(show=True):
    from music21 import corpus, meter, stream, clef

    score = corpus.parse('bach/bwv366.xml')  
    ts = score.flat.getElementsByClass(
        meter.TimeSignature)[0]
    #ts.beatSequence.partition(3)

    found = stream.Stream()
    count = 0
    for part in score.iter.getElementsByClass(stream.Part):
        found.insert(count, 
                     part.flat.iter.getElementsByClass(clef.Clef)[0])
        for i, m in enumerate(part.iter.getElementsByClass('Measure')):
            for n in m.iter.notes:
                if n.name == 'C#': 
                    n.addLyric('%s, m. %s' % (part.partName[0], m.number))
                    n.addLyric('beat %s' % ts.getBeat(n.offset))
                    found.insert(count, n)
                    count += 4
    if show:
        found.show('musicxml')



def oldAccent(show=True):
    from music21 import corpus, meter, articulations
    
    score = corpus.parse('bach/bwv366.xml')
    partBass = score.getElementById('Bass')
    
    ts = partBass.flat.getElementsByClass(meter.TimeSignature)[0]
    ts.beatSequence.partition(['3/8', '3/8'])
    ts.accentSequence.partition(['3/8', '3/8'])
    ts.setAccentWeight([1, .5])
    
    for m in partBass.getElementsByClass('Measure'):
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
        partBass.measures(1,8).show('musicxml')


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''icmc2010: Test non-showing functions
        '''
        for func in [bergEx01, showDots, findRaisedSevenths, oldAccent]:
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
    import music21
    #bergEx01()
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

