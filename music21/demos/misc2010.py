from music21 import converter, corpus, stream, note

def richardBreedGetWell():
    '''
    Richard Breed is a donor who supports the purchases of early music materials at M.I.T. --
    I used this code as part of a get well card for him, it finds the name BREED in the Beethoven
    quartets.  (well something close, B-rest-E-E-D returned nothing, so I instead did b-r-E-d, where
    the e has to be long...)

    finds a few places in opus132 and nothing else
    '''
    for workName in corpus.beethovenStringQuartets:
        if 'opus132' not in workName:
            continue
        beethovenScore = converter.parse(workName)
        for partNum in range(len(beethovenScore)):
            print(workName, str(partNum))
            thisPart = beethovenScore[partNum]
            thisPart.title = workName + str(partNum)
            display = stream.Stream()
            notes = thisPart.flat.notes 
            for i in range(len(notes) - 5):
                if (notes[i].isNote and notes[i].name == 'B') and \
                    notes[i+1].isRest is True and \
                   (notes[i+2].isNote and notes[i+2].name == 'E') and \
                   (notes[i+3].isNote and notes[i+3].name == 'D') and \
                   (notes[i+2].duration.quarterLength > notes[i].duration.quarterLength) and \
                   (notes[i+2].duration.quarterLength > notes[i+1].duration.quarterLength) and \
                   (notes[i+2].duration.quarterLength > notes[i+3].duration.quarterLength):
                        
                        measureNumber = 0
                        lastMeasure = None
                        for j in range(4):
                            thisMeasure = notes[i+j].getContextByClass(stream.Measure)
                            if thisMeasure is not None and thisMeasure is not lastMeasure:
                                lastMeasure = thisMeasure
                                measureNumber = thisMeasure.measureNumber
                                thisMeasure.insert(0, thisMeasure.bestClef())
                                display.append(thisMeasure)
                        notes[i].lyric = workName + " " + str(thisPart.id) + " " + str(measureNumber)

            if len(display) > 0:
                display.show()

def annotateWithGerman():
    '''
    annotates a score with the German notes for each note
    '''
    bwv295 = corpus.parseWork('bach/bwv295')
    for thisNote in bwv295.flat.notes:
        thisNote.addLyric(thisNote.pitch.german)
    bwv295.show()



#-------------------------------------------------------------------------------
if (__name__ == "__main__"):
#    richardBreedGetWell()
    annotateWithGerman()