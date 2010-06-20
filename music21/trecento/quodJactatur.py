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
            
#            for thisContext in classesToMove:
#                curCon = myEl.getContextByClass(thisContext)
#                if currentContexts[thisContext.__name__] is not curCon:
#                    returnObj.insert(newOffset, curCon)
#                    currentContexts[thisContext.__name__] = curCon
                    
            returnObj.insert(newOffset, myEl)
        
        return returnObj.sorted



# this module searches for solutions to Johannes Ciconia's Enigmatic canon:
# "Quod Jactatur", a piece that has resisted solutions.
#
# Michael Scott Cuthbert

qj = corpus.parseWork("ciconia/quod_jactatur")

qjSolved = stream.Score()
qjpart2 = copy.deepcopy(qj[0])

for n in qjpart2.flat.notes:
    if n.isRest is False:
        n.pitch.diatonicNoteNum = 54 - n.pitch.diatonicNoteNum

    
qjpart3 = copy.deepcopy(qj[0])

qjpart4 = copy.deepcopy(qj[0])

for n in qjpart4.flat.notes:
    if n.isRest is False:
        n.pitch.diatonicNoteNum += 4


r0 = note.Rest()
r0.duration.quarterLength = 70

qjpart4b = qjpart4.flat
qjpart4b.insertAndShift(0, meter.TimeSignature('2/4'))
qjpart4b.insertAndShift(0, r0)
qjpart4c = qjpart4b.makeMeasures()

#qjexcerpt = qjpart2.getMeasureRange(1,4)
#qjexcerpt.show('text')

#qjpart2.transpose("P-5", inPlace=True)

r1 = note.Rest()
r1.duration.quarterLength = 34

qjpart2.insert(qjpart2.highestTime, r1)
qjpartRev = reverse(qjpart2.flat)
qjpartRev.insert(0, clef.Treble8vbClef())
qjpartRev.insert(0, meter.TimeSignature('2/4'))
qjpartRev2 = qjpartRev.sorted
qjpartRev3 = qjpartRev2.makeMeasures()
qjpartRev3.makeBeams()
qjpartRev3.insert(0, clef.Treble8vbClef())

qjSolved.insert(0, qjpart4c)
qjSolved.insert(0, qjpart3)
qjSolved.insert(0, qjpartRev3)

qjSolved.show('musicxml')
#qjpartRev.show()
