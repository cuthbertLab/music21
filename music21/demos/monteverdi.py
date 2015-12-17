# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         demos/monteverdi.py
# Purpose:      Bellairs Workshop on Monteverdi Madrigals, Barbados, Feb 2011
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------

'''
The project was to see how well (or not) Monteverdi's 5-voice madrigals in Books
3, 4, and 5 follow the principles of common-practice, tonal harmony.  Organized
by Dmitri T. 

The workshop gave the excuse to add the romanText format, which DT and others
have encoded lots of analyses in.  Some demos of the format are below
'''

from music21 import corpus, clef, interval, pitch, voiceLeading, roman

def spliceAnalysis(book = 3, madrigal = 1):
    '''
    splice an analysis of the madrigal under the analysis itself
    '''
    #mad = corpus.parse('monteverdi/madrigal.%s.%s.xml' % (book, madrigal))
    analysis = corpus.parse('monteverdi/madrigal.%s.%s.rntxt' % (book, madrigal))

    # these are multiple parts in a score stream
    #excerpt = mad.measures(1,20)

    # get from first part
    aMeasures = analysis.parts[0].measures(1,20)
    aMeasures.getElementsByClass('Measure')[0].clef = clef.TrebleClef()
    for myN in aMeasures.flat.notesAndRests:
        myN.hideObjectOnPrint = True
    x = aMeasures.write()    
    print (x)
    #excerpt.insert(0, aMeasures)
    #excerpt.show()
    
def showAnalysis(book = 3, madrigal = 13):
    #analysis = converter.parse('d:/docs/research/music21/dmitri_analyses/Mozart Piano Sonatas/k331.rntxt') 
    filename = 'monteverdi/madrigal.%s.%s.rntxt' % (book, madrigal)
    analysis = corpus.parse(filename)
    #analysis.show()
    (major, minor) = iqSemitonesAndPercentage(analysis)
    print (major)
    print (minor)
    
def analyzeBooks(books = (3,), start = 1, end = 20, show = False, strict = False):
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
                analysis = corpus.parse(filename)
                print(book,i)
            else:
                try:
                    analysis = corpus.parse(filename)
                    print(book,i)
                except Exception:
                    print("Cannot parse %s, maybe it does not exist..." % (filename))
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
    print(majorFig)
    print(minorFig)
    print(majorSt)
    print(minorSt)
    print(majorRoot)
    print(minorRoot)


def iqChordsAndPercentage(analysisStream):
    '''
    returns two strings, one for major, one for minor, containing the key, 
    figure, and (in parentheses) the % of the total duration that this chord represents.
    
    Named for Ian Quinn
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
            #distanceToTonicInSemis = int((element.root().ps - pitch.Pitch(element.scale.tonic).ps) % 12)
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

def monteverdiParallels(books = (3,), start = 1, end = 20, show = True, strict = False):
    '''
    find all instances of parallel fifths or octaves in Monteverdi madrigals.
    '''
    for book in books:
        for i in range(start, end+1):
            filename = 'monteverdi/madrigal.%s.%s.xml' % (book, i)
            if strict == True:
                c = corpus.parse(filename)
                print (book,i)
            else:
                try:
                    c = corpus.parse(filename)
                    print (book,i)
                except:
                    print ("Cannot parse %s, maybe it does not exist..." % (filename))
                    continue
            displayMe = False
            for i in range(len(c.parts) - 1):
                #iName = c.parts[i].id
                ifn = c.parts[i].flat.notesAndRests
                omi = ifn.offsetMap
                for j in range(i+1, len(c.parts)):
                    jName = c.parts[j].id      
    
                    jfn = c.parts[j].flat.notesAndRests
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
                
def findPhraseBoundaries(book = 4, madrigal = 12):
    filename = 'monteverdi/madrigal.%s.%s' % (book, madrigal)
    sc = corpus.parse(filename + '.xml')
    analysis = corpus.parse(filename + '.rntxt')
    analysisFlat  = analysis.flat.stripTies().getElementsByClass(roman.RomanNumeral)

    phraseScoresByOffset = {}

    for p in sc.parts:
        partNotes = p.flat.stripTies(matchByPitch = True).notesAndRests
        #thisPartPhraseScores = [] # keeps track of the likelihood that a phrase boundary is after note i
        for i in range(2, len(partNotes) - 2): # start on the third note and stop searching on the third to last note...
            thisScore = 0
            twoNotesBack = partNotes[i-2]
            previousNote = partNotes[i-1]
            thisNote = partNotes[i]
            nextNote = partNotes[i+1]
            nextAfterThatNote = partNotes[i+2]
            
            phraseOffset = nextNote.offset
            if phraseOffset in phraseScoresByOffset:
                existingScore = phraseScoresByOffset[phraseOffset]
            else:
                phraseScoresByOffset[phraseOffset] = 0
                existingScore = 0
            
            if thisNote.isRest == True:
                continue

            if nextNote.isRest == True:
                thisScore = thisScore + 10
            else:
                intervalToNextNote = interval.notesToInterval(thisNote, nextNote)
                if intervalToNextNote.chromatic.undirected >= 6: # a tritone or bigger
                    thisScore = thisScore + 10
            if (thisNote.quarterLength > previousNote.quarterLength) and \
                (thisNote.quarterLength > nextNote.quarterLength):
                thisScore = thisScore + 10
            if (thisNote.quarterLength > previousNote.quarterLength) and \
                (thisNote.quarterLength > twoNotesBack.quarterLength) and \
                (nextNote.quarterLength > nextAfterThatNote.quarterLength):
                thisScore = thisScore + 10

            previousNoteAnalysis = analysisFlat.getElementAtOrBefore(previousNote.offset)
            thisNoteAnalysis = analysisFlat.getElementAtOrBefore(thisNote.offset)
            
            if previousNoteAnalysis.romanNumeral == 'V' and thisNoteAnalysis.romanNumeral.upper() == 'I':
                thisScore = thisScore + 11
            elif previousNoteAnalysis.romanNumeral.upper() == 'II' and thisNoteAnalysis.romanNumeral.upper() == 'I':
                thisScore = thisScore + 6
                
            if thisNote.lyric is not None and thisNote.lyric.endswith('.'):
                thisScore = thisScore + 15 # would be higher but our lyrics data is bad.
                
            phraseScoresByOffset[phraseOffset] = existingScore + thisScore

    flattenedBass = sc.parts[-1].flat.notesAndRests
    for thisOffset in sorted(phraseScoresByOffset.keys()):
        psbo = phraseScoresByOffset[thisOffset]
        if psbo > 0: 
            print (thisOffset, psbo)
            relevantNote = flattenedBass.getElementAtOrBefore(thisOffset - 0.1)
            if hasattr(relevantNote, 'score'):
                print ("adjusting score from %d to %d for note in measure %d" % (relevantNote.score, relevantNote.score + psbo, relevantNote.measureNumber))
                relevantNote.score += psbo
            else:
                relevantNote.score = psbo
    for n in flattenedBass:
        if hasattr(n, 'score'):
            n.lyric = str(n.score)
    
    sc.show()


if __name__ == '__main__':
    #spliceAnalysis()
    #analyzeBooks(books = [3,4,5])
    #analyzeBooks(books = [4], start=10, end=10, show=True, strict=True)
    findPhraseBoundaries(book = 4, madrigal = 12)
    #monteverdiParallels(books = [3], start=1, end=1, show=True, strict=True)
