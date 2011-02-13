from music21 import *

def spliceAnalysis(book = 3, madrigal = 13):
    mad = corpus.parseWork('monteverdi/madrigal_' + str(book) + "_" + str(madrigal) + '.xml')
    anal = corpus.parseWork('monteverdi/madrigal_' + str(book) + "_" + str(madrigal) + '.rntxt')
    excerpt = mad.measures(1,20)
    excerpt.insert(0, anal.measures(1,20))
    excerpt.show()
    
if __name__ == '__main__':
    spliceAnalysis()