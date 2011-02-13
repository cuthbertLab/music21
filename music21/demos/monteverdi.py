from music21 import *

def spliceAnalysis(book = 3, madrigal = 13):
    mad = corpus.parseWork('monteverdi/madrigal_%s_%s.xml' % (book, madrigal))
    analysis = corpus.parseWork('monteverdi/madrigal_%s_%s.rntxt' % (book, madrigal))

    # these are multiple parts in a score stream
    excerpt = mad.measures(1,20)

    # get from first part
    aMeasures = analysis.parts[0].measures(1,20)
    aMeasures.getElementsByClass('Measure')[0].clef = clef.TrebleClef()
    excerpt.insert(0, aMeasures)
    excerpt.show()
    
def showAnalysis(book = 3, madrigal = 13):
    #analysis = converter.parse('d:/docs/research/music21/dmitri_analyses/Mozart Piano Sonatas/k331.rntxt') 
    analysis = corpus.parseWork('monteverdi/madrigal_%s_%s.rntxt' % (book, madrigal))
#    analysis.show('text')
    iqChordsAndPercentage(analysis)
    
def iqChordsAndPercentage(analysisStream):
    totalDuration = analysisStream.duration.quarterLength
    romMerged = analysisStream.flat.stripTies()
    romMerged.show('text')
    for element in romMerged:
        if "RomanNumeral" in element.classes:       
            print element.figure + " (" + str(int(element.duration.quarterLength*10000.0/totalDuration)/100.0) + ")",
        elif hasattr(element, 'tonic'):
            print "\n" + element.tonic + " " + element.mode,

def iqSemiTonesAndPercentage(analysisStream):
    totalDuration = analysisStream.duration.quarterLength
    romMerged = analysisStream.flat.stripTies()
    romMerged.show('text')
    for element in romMerged:
        if "RomanNumeral" in element.classes:       
            distanceToTonicInSemis = int((element.root().ps - pitch.Pitch(element.scale.tonic).ps) % 12)
            print str(distanceToTonicInSemis) + " (" + str(int(element.duration.quarterLength*10000.0/totalDuration)/100.0) + ")",
        elif hasattr(element, 'tonic'):
            print "\n" + element.tonic + " " + element.mode,

def iqRootsAndPercentage(analysisStream):
    totalDuration = analysisStream.duration.quarterLength
    romMerged = analysisStream.flat.stripTies()
    romMerged.show('text')
    for element in romMerged:
        if "RomanNumeral" in element.classes:       
            print str(element.root().name) + " (" + str(int(element.duration.quarterLength*10000.0/totalDuration)/100.0) + ")",
        elif hasattr(element, 'tonic'):
            print "\n" + element.tonic + " " + element.mode,



    
if __name__ == '__main__':
    #spliceAnalysis()
    showAnalysis()