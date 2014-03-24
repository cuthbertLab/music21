# -*- coding: utf-8 -*-

'''
Demos of research done on automatic reduction of chords in the Trecento
repertory.

Used by Josiah and Myke for the ELVIS project
'''
from music21 import analysis, corpus, interval


def iterateChordsNwise(chords, n=2):
    chordBuffer = []
    for chord in chords:
        if not chordBuffer or chord.pitches != chordBuffer[-1].pitches:
            chordBuffer.append(chord)
        if len(chordBuffer) == n:
            yield(tuple(chordBuffer))
            chordBuffer.pop(0)


def chordToIntervalString(chord):
    if len(chord) == 1:
        intervalString = 'P1'
    else:
        intervalString = interval.Interval(chord[0], chord[1]).name
    return intervalString


def chordsToBassMelodictIntervalString(chordOne, chordTwo):
    bassPitchOne = min(chordOne)
    bassPitchTwo = min(chordTwo)
    bassMelodicInterval = interval.Interval(bassPitchOne, bassPitchTwo)
    bassMelodicIntervalString = bassMelodicInterval.directedName
    return bassMelodicIntervalString


def computeNGrams(part, nGramLength=2):
    stripped = part.stripTies(matchByPitch=True)
    allChords = tuple(stripped.flat.getElementsByClass('Chord'))
    nGrams = []
    for chords in iterateChordsNwise(allChords, n=nGramLength):
        nGram = []
        intervalString = chordToIntervalString(chords[0])
        nGram.append(intervalString)
        for chordOne, chordTwo in iterateChordsNwise(chords, n=2):
            bassMelodicIntervalString = chordsToBassMelodictIntervalString(
                chordOne, chordTwo)
            nGram.append(bassMelodicIntervalString)
            intervalString = chordToIntervalString(chordTwo)
            nGram.append(intervalString)
        nGrams.append(tuple(nGram))
    return nGrams


def hashNGrams(nGrams):
    import collections
    nGramDict = collections.Counter()
    for nGram in nGrams:
        nGramDict[nGram] += 1
    sortedDict = tuple(nGramDict.most_common())
    return sortedDict


if __name__ == '__main__':
    import pprint
    filename = 'PMFC_06_Giovanni-05_Donna_Gia_Fu_Leggiadra.xml'
    score = corpus.parse('trecento/' + filename).measures(1, 30)

    chordReducer = analysis.reduceChords.ChordReducer()
    reduction = chordReducer(score).parts[0]
    nGrams = computeNGrams(reduction)
    pprint.pprint(hashNGrams(nGrams))

    chordified = score.chordify()
    nGrams = computeNGrams(chordified)
    pprint.pprint(hashNGrams(nGrams))
