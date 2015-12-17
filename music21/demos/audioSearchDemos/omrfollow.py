# -*- coding: utf-8 -*-
from __future__ import print_function

from music21 import audioSearch
from music21 import converter
from music21 import search
from music21 import stream


from music21 import environment
_MOD = "audioSearch.omrfollow"
environLocal = environment.Environment(_MOD)

_missingImport = []

try:
    import numpy
except ImportError:
    _missingImport.append('numpy')

if len(_missingImport) > 0:
    if environLocal['warnings'] in [1, '1', True]:
        pass
        #environLocal.warn(common.getMissingImportStr(_missingImport), header='music21:')

import time

def recognizeLuca():
    '''
    can music21 using audio search recognize which page I play if I play a passage from dLuca's gloria
    OMRd?
    
    
    Works great!
    
    
    OMR was done with SharpEye Light on Finale.
    '''
    # first page begins on m1, second on m23, etc. -- not needed when we import page objects in music21.
    pageMeasureNumbers = [1,23,50,81,104, 126]  #126 is end of document
    dlucaAll = converter.parse('dluca_scanned.xml')
    #dlucaAll = corpus.parse('luca/gloria')
    dlucaCantus = dlucaAll.parts[0]
    recognizeScore(dlucaCantus, pageMeasureNumbers)

def recognizeKuhlau():
    '''
    A more difficult task: a difficult to read 19th c. non-retypeset score: Kuhlau's op81
    second flute part.  N.B. -- missing page 18 (=p2) and 24.
    
    Only does the first couple of pages
    '''
    # first page begins on m1, second on m23, etc. -- not needed when we import page objects in music21.
    pageMeasureNumbers = [1,73,151,217,268,313,366,437,506,555,614, 662, 702, 737, 764]  #764 is end of document
    kuhlau = converter.parse('kuhlau_op81_fl2.xml')
    recognizeScore(kuhlau, pageMeasureNumbers, iterations=3)

    
def recognizeScore(scorePart, pageMeasureNumbers, iterations = 1):
    pages = []

    for i in range(len(pageMeasureNumbers)-1):
        pages.append(scorePart.measures(pageMeasureNumbers[i], pageMeasureNumbers[i+1]).flat.notes)
    #divide into 24 note groups, overlapping by 16 notes each...

    allStreams = []
    for pgMinus1 in range(len(pages)):
        print(str(pgMinus1 + 1))
        thisPage = pages[pgMinus1]
        totalNotes = len(thisPage)
        for i in range(0, totalNotes, 8):
            startNote = thisPage[i]
            startMeasure = startNote.measureNumber
            print("  " + str(startMeasure))
            newStream = stream.Stream(thisPage[i:i+24])
            newStream.pageNumber = pgMinus1 + 1
            newStream.startMeasure = startMeasure
            allStreams.append(newStream)

    for loopy in range(iterations):
        if loopy > 0:
            print("\n\nstarting again in 3 seconds")
            time.sleep(3) 
        searchScore = audioSearch.transcriber.runTranscribe(show = False, plot = False, seconds = 15.0, saveFile = False)
        l = search.approximateNoteSearch(searchScore, allStreams)
    
        scores = [0 for j in range(len(pages))]
        for i in range(8): # top 8 searches
            topStream = l[i]
            scorePage = topStream.pageNumber - 1
            scores[scorePage] += (topStream.matchProbability / (i+1.5))*10
    
        
        print("\nBest guesses (pg#, starting measure, probability)")
        for i,st in enumerate(l):
            print(st.pageNumber, st.startMeasure, st.matchProbability)
            if i >= 7:
                break
        
        print("\nWeighed top scores (pg#, score):")
        
        for i in range(len(pages)):
            print( (i+1, scores[i]), end="")
            if i == numpy.argmax(scores):
                print(" **** ")
            else:
                print("")


if __name__ == '__main__':
    recognizeLuca()
