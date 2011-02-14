from music21 import *

def spliceAnalysis(book = 3, madrigal = 13):
    mad = corpus.parseWork('monteverdi/madrigal.%s.%s.xml' % (book, madrigal))
    analysis = corpus.parseWork('monteverdi/madrigal.%s.%s.rntxt' % (book, madrigal))

    # these are multiple parts in a score stream
    excerpt = mad.measures(1,20)

    # get from first part
    aMeasures = analysis.parts[0].measures(1,20)
    aMeasures.getElementsByClass('Measure')[0].clef = clef.TrebleClef()
    excerpt.insert(0, aMeasures)
    excerpt.show()
    
def showAnalysis(book = 3, madrigal = 13):
    #analysis = converter.parse('d:/docs/research/music21/dmitri_analyses/Mozart Piano Sonatas/k331.rntxt') 
    filename = 'monteverdi/madrigal.%s.%s.rntxt' % (book, madrigal)
    analysis = corpus.parseWork(filename)
    #analysis.show()
    (major, minor) = iqSemitonesAndPercentage(analysis)
    print major
    print minor
    
def analyzeBooks(books = [3], start = 1, end = 20, show = False):
    majorFig = ""
    minorFig = ""
    majorSt = ""
    minorSt = ""
    majorRoot = ""
    minorRoot = ""
    for book in books:
        for i in range(start, end+1):
            filename = 'monteverdi/madrigal.%s.%s.rntxt' % (book, i)
#            try:
            analysis = corpus.parseWork(filename)
            print book,i
#            except:
#                print "Cannot parse %s, maybe it does not exist..." % (filename)
#                continue
            if show == True:
                analysis.show()
            (MF, mF) = iqChordsAndPercentage(analysis)
            (MSt, mSt) = iqSemitonesAndPercentage(analysis)
            (MRoot, mRoot) = iqRootsAndPercentage(analysis)
            majorFig += MF
            minorFig += mF
            majorSt += MSt
            minorSt += mSt
            majorRoot += MRoot
            minorRoot += mRoot
    print majorFig
    print minorFig
    print majorSt
    print minorSt
    print majorRoot
    print minorRoot


def iqChordsAndPercentage(analysisStream):
    '''
    returns two strings, one for major, one for minor, containing the key, figure, and (in parentheses) the % of the total duration that this chord represents.
    '''
    totalDuration = analysisStream.duration.quarterLength
    romMerged = analysisStream.flat.stripTies()
    major = ""
    minor = ""
    active = 'minor'
    for element in romMerged:
        if "RomanNumeral" in element.classes:       
            fig = element.figure
            fig = fig.replace('[no5]','')
            fig = fig.replace('[no3]','')
            fig = fig.replace('[no1]','')
            longString = fig + " (" + str(int(element.duration.quarterLength*10000.0/totalDuration)/100.0) + ") "
            if active == 'major':
                major += longString
            else:
                minor += longString
        elif hasattr(element, 'tonic'):
            if element.mode == 'major':
                active = 'major'
                major += "\n" + element.tonic + " " + element.mode + " "
            else:
                active = 'minor'
                minor += "\n" + element.tonic + " " + element.mode + " "
    return (major, minor)

def iqSemitonesAndPercentage(analysisStream):
    totalDuration = analysisStream.duration.quarterLength
    romMerged = analysisStream.flat.stripTies()
    major = ""
    minor = ""
    active = 'minor'
    for element in romMerged:
        if "RomanNumeral" in element.classes:       
            distanceToTonicInSemis = int((element.root().ps - pitch.Pitch(element.scale.tonic).ps) % 12)
            longString = str(distanceToTonicInSemis) + " (" + str(int(element.duration.quarterLength*10000.0/totalDuration)/100.0) + ") "
            if active == 'major':
                major += longString
            else:
                minor += longString
        elif hasattr(element, 'tonic'):
            if element.mode == 'major':
                active = 'major'
                major += "\n" + element.tonic + " " + element.mode + " "
            else:
                active = 'minor'
                minor += "\n" + element.tonic + " " + element.mode + " "
    return (major, minor)

def iqRootsAndPercentage(analysisStream):
    totalDuration = analysisStream.duration.quarterLength
    romMerged = analysisStream.flat.stripTies()
    major = ""
    minor = ""
    active = 'minor'
    for element in romMerged:
        if "RomanNumeral" in element.classes:       
            distanceToTonicInSemis = int((element.root().ps - pitch.Pitch(element.scale.tonic).ps) % 12)
            elementLetter = str(element.root().name) 
            
            ## leave El
            if element.quality == 'minor' or element.quality == 'diminished':
                elementLetter = elementLetter.lower()
            elif element.quality == 'other':
                rootScaleDegree = element.scale.getScaleDegreeFromPitch(element.root())
                if rootScaleDegree: 
                    thirdPitch = element.scale.pitchFromDegree((rootScaleDegree + 2) % 7)
                    int1 = interval.notesToInterval(element.root(), thirdPitch)
                    if int1.intervalClass == 3:
                        elementLetter = elementLetter.lower()
                else:
                    pass
            longString = elementLetter + " (" + str(int(element.duration.quarterLength*10000.0/totalDuration)/100.0) + ") "
            if active == 'major':
                major += longString
            else:
                minor += longString
        elif hasattr(element, 'tonic'):
            if element.mode == 'major':
                active = 'major'
                major += "\n" + element.tonic + " " + element.mode + " "
            else:
                active = 'minor'
                minor += "\n" + element.tonic + " " + element.mode + " "
    return (major, minor)

    
if __name__ == '__main__':
    #spliceAnalysis()
    analyzeBooks(books = [4], start = 14, end = 14, show = True)