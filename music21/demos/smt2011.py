# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         smt2011.py
# Purpose:      Demonstrations for the SMT 2011 demo
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------

import copy

from music21 import environment, corpus

_MOD = 'demo/smt2011.py'
environLocal = environment.Environment(_MOD)





def ex01():
    # beethoven
    #s1 = corpus.parse('opus18no1/movement3.xml')
    #s1.show()


    # has lots of triplets toward end
    # viola not coming in as alto clef
#     s2 = corpus.parse('haydn/opus17no1/movement3.zip')
#     s2.show()

    s2 = corpus.parse('haydn/opus17no2/movement3.zip')
    # works well; some triplets are missing but playback correctly
    s2Chordified = s2.measures(1, 25).chordify()
    s2Chordified.show()


#-------------------------------------------------------------------------------
def chordsToAnalysis(chordStream, manifest, scale):
    '''
    manifest is a list of tuples in the following form:
    (measureNumber, chordNumberOrNone, scaleDegree, octaveDisplay, durationTypeDisplay)
    '''
    from music21 import note, bar

    chordMeasures = chordStream.getElementsByClass('Measure')
    measureTemplate = copy.deepcopy(chordMeasures)
    for i, m in enumerate(measureTemplate):
        m.removeByClass(['GeneralNote'])
        # assuming we have measure numbers

    for (measureNumber, chordNumberOrNone, scaleDegree, octaveDisplay,         
        durationTypeDisplay, textDisplay) in manifest:
        # assume measures are in order; replace with different method
        m = chordMeasures[measureNumber-1]
        mPost = measureTemplate[measureNumber-1]
        if chordNumberOrNone is None:
            c = m.notes[0]
        else:
            c = m.notes[chordNumberOrNone-1] # assume counting from 1

        pTarget = scale.pitchFromDegree(scaleDegree)
        match = False
        p = None
        for p in c.pitches:
            if p.name == pTarget.name:
                match = True
                break
        if not match:
            print('no scale degree found in specified chord', p, pTarget)
        pTarget.octave = octaveDisplay
        n = note.Note(pTarget)
        if durationTypeDisplay in ['whole']:
            n.noteheadFill = False
        else:
            n.noteheadFill = True
        n.stemDirection = 'noStem'
        n.addLyric(textDisplay)
        mPost.insert(c.getOffsetBySite(m), n)

    # fill with rests
    for m in measureTemplate:
        m.rightBarline = bar.Barline('none')
        # need to hide rests
        if len(m.notes) == 0:
            r = note.Rest(quarterLength=4)
            r.hideObjectOnPrint = True
            m.append(r)

    return measureTemplate

def exShenker():
    from music21 import stream, scale, bar
    # wtc no 1
    src = corpus.parse('bwv846')
    #src.show()

    melodicSrc = src.parts[0]
    measureTemplate = copy.deepcopy(melodicSrc.getElementsByClass('Measure'))
    for i, m in enumerate(measureTemplate):
        m.removeByClass(['GeneralNote'])
        m.number = i + 1

    # this stream has triple bar lines, clefs, etc
    unused_chords = src.flat.makeChords(minimumWindowSize=2)

    analysis = stream.Score()
    chordReduction = copy.deepcopy(measureTemplate)
    for i, m in enumerate(chordReduction.getElementsByClass('Measure')):
        mNotes = src.flat.getElementsByOffset(m.offset, 
            m.offset+m.barDuration.quarterLength, includeEndBoundary=False)        
        mNotes.makeChords(minimumWindowSize=4, inPlace=True)
        c = mNotes.flat.notes[0]
        c.duration.type = 'whole'
        m.append(c)
        m.rightBarline = bar.Barline('regular')
    # add parts

    scaleCMajor = scale.MajorScale('c')

    #measureNumber, chordNumberOrNone, scaleDegree, octaveDisplay,         
    #    durationTypeDisplay, textDisplay
    manifest = [(1, None, 3, 5, 'whole', '3'), 
                (24, None, 2, 5, 'whole', '2'), 
                (35, None, 1, 5, 'whole', '1'), 
                ]
    analysis1 = chordsToAnalysis(chordReduction, manifest, scaleCMajor)


    manifest = [(1, None, 1, 4, 'whole', 'I'), 
                (24, None, 5, 3, 'whole', 'V'), 
                (31, None, 4, 4, 'quarter', '--7'), 
                (35, None, 1, 4, 'whole', 'I'), 
               ]
    analysis2 = chordsToAnalysis(chordReduction, manifest, scaleCMajor)


    analysis.insert(0, analysis1)
    analysis.insert(0, analysis2)
    analysis.insert(0, chordReduction)
    analysis.show()




def demoMakeChords():
    # wtc no 1
    #src = corpus.parse('bwv65.2').measures(0, 5)
    src = corpus.parse('opus18no1/movement3.xml').measures(0, 10)
    src.flattenParts().makeChords(minimumWindowSize=3).show()


    src = corpus.parse('opus18no1/movement3.xml').measures(0, 10)
    src.chordify().show()


if __name__ == '__main__':
    #ex01()
    #exShenker()
    demoMakeChords()
