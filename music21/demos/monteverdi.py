from music21 import *

def spliceAnalysis(book = 3, madrigal = 13):
    mad = corpus.parseWork('monteverdi/madrigal_' + str(book) + "_" + str(madrigal) + '.xml')
    anal = corpus.parseWork('monteverdi/madrigal_' + str(book) + "_" + str(madrigal) + '.rntxt')
    anal.transpose("P8", inPlace = True)
    mad.insert(0, anal.parts[0])
    mad.show()
    
if __name__ == '__main__':
    spliceAnalysis()