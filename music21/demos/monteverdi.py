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
    
if __name__ == '__main__':
    spliceAnalysis()