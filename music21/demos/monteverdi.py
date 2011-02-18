#-------------------------------------------------------------------------------
# Name:         demos/monteverdi.py
# Purpose:      Bellairs Workshop on Monteverdi Madrigals, Barbados, Feb 2011
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
The project was to see how well (or not) Monteverdi's 5-voice madrigals in Books
3, 4, and 5 follow the principles of common-practice, tonal harmony.  Organized
by Dmitri T. 

The workshop gave the excuse to add the romanText format, which DT and others
have encoded lots of analyses in.  Some demos of the format are below
'''


from music21 import *

def spliceAnalysis(book = 3, madrigal = 1):
    '''
    splice an analysis of the madrigal under the analysis itself
    '''
    mad = corpus.parseWork('monteverdi/madrigal.%s.%s.xml' % (book, madrigal))
    analysis = corpus.parseWork('monteverdi/madrigal.%s.%s.rntxt' % (book, madrigal))

    # these are multiple parts in a score stream
    #excerpt = mad.measures(1,20)

    # get from first part
    aMeasures = analysis.parts[0].measures(1,20)
    aMeasures.getElementsByClass('Measure')[0].clef = clef.TrebleClef()
    for myN in aMeasures.flat.notes:
        myN.hideObjectOnPrint = True
    x = aMeasures.write()    
    print x
    #excerpt.insert(0, aMeasures)
    #excerpt.show()
    
def showAnalysis(book = 3, madrigal = 13):
    #analysis = converter.parse('d:/docs/research/music21/dmitri_analyses/Mozart Piano Sonatas/k331.rntxt') 
    filename = 'monteverdi/madrigal.%s.%s.rntxt' % (book, madrigal)
    analysis = corpus.parseWork(filename)
    #analysis.show()
    (major, minor) = iqSemitonesAndPercentage(analysis)
    print major
    print minor
    
def analyzeBooks(books = [3], start = 1, end = 20, show = False, strict = False):
    majorFig = ""
    minorFig = ""
    majorSt = ""
    minorSt = ""
    majorRoot = ""
    minorRoot = ""
    for book in books:
        for i in range(start, end+1):
            filename = 'monteverdi/madrigal.%s.%s.rntxt' % (book, i)
            if strict == True:
                analysis = corpus.parseWork(filename)
                print book,i
            else:
                try:
                    analysis = corpus.parseWork(filename)
                    print book,i
                except:
                    print "Cannot parse %s, maybe it does not exist..." % (filename)
                    continue
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
        elif "Key" in element.classes:
            if element.mode == 'major':
                active = 'major'
                major += "\n" + element.tonic + " " + element.mode + " "
            else:
                active = 'minor'
                minor += "\n" + element.tonic + " " + element.mode + " "
    return (major, minor)

def monteverdiParallels(books = [3], start = 1, end = 20, show = True, strict = False):
    '''
    find all instances of parallel fifths or octaves in Monteverdi madrigals.
    '''
    for book in books:
        for i in range(start, end+1):
            filename = 'monteverdi/madrigal.%s.%s.xml' % (book, i)
            if strict == True:
                c = corpus.parseWork(filename)
                print book,i
            else:
                try:
                    c = corpus.parseWork(filename)
                    print book,i
                except:
                    print "Cannot parse %s, maybe it does not exist..." % (filename)
                    continue
            displayMe = False
            for i in range(len(c.parts) - 1):
                iName = c.parts[i].id
                ifn = c.parts[i].flat.notes
                omi = ifn.offsetMap
                for j in range(i+1, len(c.parts)):
                    jName = c.parts[j].id      
    
                    jfn = c.parts[j].flat.notes
                    for k in range(len(omi) - 1):
                        n1pi = omi[k]['element']
                        n2pi = omi[k+1]['element']                    
                        n1pjAll = jfn.getElementsByOffset(offsetStart = omi[k]['endTime'] - .001, offsetEnd = omi[k]['endTime'] - .001, mustBeginInSpan = False)
                        if len(n1pjAll) == 0:
                            continue
                        n1pj = n1pjAll[0]
                        n2pjAll = jfn.getElementsByOffset(offsetStart = omi[k+1]['offset'], offsetEnd = omi[k+1]['offset'], mustBeginInSpan = False) 
                        if len(n2pjAll) == 0:
                            continue
                        n2pj = n2pjAll[0]
                        if n1pj is n2pj:
                            continue # no oblique motion
                        if n1pi.isRest or n2pi.isRest or n1pj.isRest or n2pj.isRest:
                            continue
                        if n1pi.isChord or n2pi.isChord or n1pj.isChord or n2pj.isChord:
                            continue
    
                        vlq = voiceLeading.VoiceLeadingQuartet(n1pi, n2pi, n1pj, n2pj)
                        if vlq.parallelMotion('P8') is False and vlq.parallelMotion('P5') is False:
                            continue
                        displayMe = True
                        n1pi.addLyric('par ' + str(vlq.vIntervals[0].name))
                        n2pi.addLyric(' w/ ' + jName)
            if displayMe and show:
                c.show()
                

if __name__ == '__main__':
    #spliceAnalysis()
    #analyzeBooks(books = [3,4,5])
    analyzeBooks(books = [4], start=10, end=10, show=True, strict=True)
    #monteverdiParallels(books = [3], start=1, end=1, show=True, strict=True)