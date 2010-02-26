from music21 import corpus, stream, note

def richardBreedGetWell():
    '''
    Richard Breed is a donor who supports the purchases of early music materials at M.I.T. --
    I used this code as part of a get well card for him, it finds the name BREED in the Beethoven
    quartets.  (well something close, B-rest-E-E-D returned nothing, so I instead did b-r-E-d, where
    the e has to be long...)
    '''
    names = ['opus132', 'opus133', 'opus18no3', 'opus18no4', 'opus18no5', 'opus74']
    names += ['opus59no1', 'opus59no2', 'opus59no3']

    for workName in names:
        beethovenScore = corpus.parseWork('beethoven/' + workName, 1)
        for partNum in range(len(beethovenScore)):
            print workName, str(partNum)
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
                        thisSite = None
                        for j in range(4):
                            for site in notes[i+j]._definedContexts.getSites():
                                if isinstance(site, stream.Measure) and site is not thisSite:
                                    thisSite = site
                                    measureNumber = site.measureNumber
                                    display.append(site)
                        notes[i].lyric = workName + " " + str(thisPart.id) + " " + str(measureNumber)
                        m = stream.Measure()
                        m.append(notes[i])
                        m.append(notes[i+1])
                        m.append(notes[i+2])
                        m.append(notes[i+3])
                        m.insert(0, m.bestClef())
                        display.append(m)

            if len(display) > 0:
                display.show()

#-------------------------------------------------------------------------------
if (__name__ == "__main__"):
    richardBreedGetWell()