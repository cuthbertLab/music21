from music21 import *
import copy

def reverse(self, inPlace = False, recursive = True, 
                classesToMove = (key.KeySignature, meter.TimeSignature, clef.Clef, metadata.Metadata, instrument.Instrument) ):
        '''
        synonym: retrograde()
        
        reverse the order of stream members both in the .elements list but also by offset, so that the piece
        sounds properly backwards.  Automatically sorts the stream as well.  If inPlace is True (yes by default)
        the elements are reversed in the current stream.  if inPlace is False then a new stream is returned.

        inPlace doesn't work!

        all elements of class classesToMove get moved to
        '''
        highestTime = self.highestTime

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        savedElements = returnObj._elements
        returnObj._elements = []

        currentContexts = common.defHash()
        
        for myEl in savedElements:
            if isinstance(myEl, classesToMove):
                continue

            releaseTime = myEl.getOffsetBySite(self) + myEl.duration.quarterLength
            newOffset = highestTime - releaseTime
            
            for thisContext in classesToMove:
                curCon = myEl.getContextByClass(thisContext)
                if currentContexts[thisContext.__name__] is not curCon:
                    returnObj.insert(newOffset, curCon)
                    currentContexts[thisContext.__name__] = curCon
                    
            returnObj.insert(newOffset, myEl)
        
        return returnObj.sorted



# this module searches for solutions to Johannes Ciconia's Enigmatic canon:
# "Quod Jactatur", a piece that has resisted solutions.
#
# Michael Scott Cuthbert

qj = corpus.parseWork("ciconia/quod_jactatur")

qjpart2 = copy.deepcopy(qj[0])

qj.insert(0, qjpart2)
qjexcerpt = qjpart2.getMeasureRange(1,4)
#qjexcerpt.show('text')
qjpartRev = reverse(qjexcerpt.flat.sorted)
qjpartRev.show('text')
#qjpartRev.show()
