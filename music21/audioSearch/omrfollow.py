from music21 import *
import numpy

def recognizeLuca():
    '''
    can music21 using audio search recognize which page I play if I play a passage from dLuca's gloria
    OMRd?
    
    
    OMR was done with SharpEye Light on Finale.
    '''
    # first page begins on m1, second on m23, etc. -- not needed when we import page objects in music21.
    pageMeasureNumbers = [1,23,50,81,104, 126]  #126 is end of document
    dlucaAll = converter.parse('dluca_scanned.xml')
    #dlucaAll = corpus.parse('luca/gloria')
    dlucaCantus = dlucaAll.parts[0]
    pages = []
    for i in range(len(pageMeasureNumbers)-1):
        pages.append(dlucaCantus.measures(pageMeasureNumbers[i], pageMeasureNumbers[i+1]).flat.notes)
    #divide into 24 note groups, overlapping by 16 notes each...

    allStreams = []
    for pgMinus1 in range(len(pages)):
        print str(pgMinus1 + 1)
        thisPage = pages[pgMinus1]
        totalNotes = len(thisPage)
        for i in range(0, totalNotes, 8):
            startNote = thisPage[i]
            startMeasure = startNote.measureNumber
            print "  " + str(startMeasure)
            newStream = stream.Stream(thisPage[i:i+24])
            newStream.pageNumber = pgMinus1 + 1
            newStream.startMeasure = startMeasure
            allStreams.append(newStream)
    searchScore = audioSearch.transcriber.runTranscribe(show = False, plot = False, seconds = 12.0, saveFile = False)
    l = search.approximateNoteSearch(searchScore, allStreams)

    scores = [0 for x in range(5)]
    for i in range(8): # top 8 searches
        topStream = l[i]
        scorePage = topStream.pageNumber - 1
        scores[scorePage] += (topStream.matchProbability / (i+2.0))*10

    
    print "\nBest guesses (pg#, starting measure, probability)"
    for i,st in enumerate(l):
        print st.pageNumber, st.startMeasure, st.matchProbability
        if i >= 7:
            break
    
    print "\nWeighed top scores (pg#, score):"
    
    for i in range(len(pages)):
        print i+1, scores[i],
        if i == numpy.argmax(scores):
            print " **** "
        else:
            print ""


if __name__ == '__main__':
    recognizeLuca()