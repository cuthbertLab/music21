# -*- coding: utf-8 -*-

'''
Demos of research done on automatic reduction of chords in the Trecento repertory.

Used by Josiah and Myke for the ELVIS project
'''
from music21 import analysis, corpus, interval

def countNGrams(part, nGramLength = 2):
    stripped = part.stripTies(matchByPitch=True)
    stripped.show()
    chords = stripped.flat.getElementsByClass('Chord')
    #chords.show()
    allNGrams = []
    for i in range(len(chords) - nGramLength + 1):
        #print chords[i]
        # nGramLength = 2
        lastBass = None
        visType = []
        for j in range(i, nGramLength+i):
            c = chords[j]
            bassPitch = min(c)
            if lastBass is not None:
                bassMelodicIntervalStr = interval.Interval(lastBass, bassPitch).directedName
                #print bassMelodicIntervalStr
                visType.append(bassMelodicIntervalStr)
            lastBass = bassPitch

            intervalString = None
            if len(c) == 1:
                intervalString = 'P1'
            else:
                intervalString = interval.Interval(c[0], c[1]).name
                #print intervalString
            visType.append(intervalString)
        print visType            

if __name__ == '__main__':
    f = 'PMFC_06_Giovanni-05_Donna_Gia_Fu_Leggiadra.xml'
    score = corpus.parse('trecento/' + f).measures(1, 20)
    #chordReducer = analysis.reduceChords.ChordReducer()
    #reduction = chordReducer(score).parts[-1]
    #countNGrams(reduction)
    chordified = score.chordify()
    countNGrams(chordified)





