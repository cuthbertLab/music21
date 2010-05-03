import xml.dom.minidom

######### music21 subdir ###############
import sys, os
scriptDir = sys.path[0]
parentDir = os.path.dirname(scriptDir)
if parentDir not in sys.path:
    sys.path.append(parentDir)
    grandParentDir = os.path.dirname(parentDir)
    if grandParentDir not in sys.path:
        sys.path.append(grandParentDir)
import music21
########################################

class XML_SimpleNote_Factory(object):
    durationFactory = None
    
    def makeDoc(self, note, noteDoc = xml.dom.minidom.Document()):
        noteDoc = xml.dom.minidom.Document()
        noteEl  = noteDoc.createElement("note")

        pitchEl = noteDoc.createElement("pitch")
        noteEl.appendChild(pitchEl)

        stepEl  = noteDoc.createElement("step")
        pitchEl.appendChild(stepEl)

        if (note.step):
            stepNode = noteDoc.createTextNode(note.step)
            stepEl.appendChild(stepNode)

        ## alter
        if (note.accidental):
            alterEl = noteDoc.createElement("alter")
            alterNode = noteDoc.createTextNode(str(note.accidental.alter))
            alterEl.appendChild(alterNode)
            noteEl.appendChild(alterEl)

        octaveEl = noteDoc.createElement("octave")
        pitchEl.appendChild(octaveEl)

        if (note.octave):
            octaveNode = noteDoc.createTextNode(str(note.octave))
            octaveEl.appendChild(octaveNode)

        if (self.durationFactory is None):
            self.durationFactory = XML_Duration_Factory()

        if (note.duration):
            (durationNode, typeNode, dotNodes, timeMods) = self.durationFactory.makeDoc(note.duration, noteDoc)

        if (durationNode):
            noteEl.appendChild(durationNode)

        if (note.tie):
            tieEl = noteDoc.createElement("tie")
            tieEl.setAttribute("type", note.tie.type)
            noteEl.appendChild(tieEl)

        ### voice goes here

        if (typeNode):
            noteEl.appendChild(typeNode)

        for thisDot in dotNodes:
            noteEl.appendChild(thisDot)

        if (note.accidental and note.accidental.displayStatus != False):
            accidentalEl = noteDoc.createElement("accidental")
            accidentalNode = noteDoc.createTextNode(note.accidental.name)
            accidentalEl.appendChild(accidentalNode)
            noteEl.appendChild(accidentalEl)

        if (timeMods):
            noteEl.appendChild(timeMods)

        ### stem goes here
        ### notehead goes here
        ### staff goes here
        ### beam goes here

        notationsEl = noteDoc.createElement("notations")  ## can be empty
        noteEl.appendChild(notationsEl)

        if (note.tie):  ## unlike above, tie*d* specifies notation of tie
            tiedEl = noteDoc.createElement("tied")
            tiedEl.setAttribute("type", note.tie.type)
            notationsEl.appendChild(tiedEl)

            ### tuplets go here
            ### fermatas go here

        ### lyric goes here

        return noteEl

class XML_Duration_Factory(object):

    '''Divisions are a MusicXML concept that music21 does not share
    It basically represents the lowest time unit that all other notes
    are integer multiples of.  Useful for compatibility with MIDI, but
    ultimately restricting since it must be less than 16384, so thus
    cannot accurately reflect a piece which uses 64th notes, triplets,
    quintuplets, septuplets, 11-tuplets, and 13-tuplets in the same piece
    I have chosen a useful base that allows for perfect representation of
    128th notes, triplets within triplets, quintuplets, and septuplets
    within the piece.  Other tuplets (11, etc.) will be close enough for
    most perceptual uses (11:1 will be off by 4 parts per thousand) but
    will cause measures to be incompletely filled, etc.  If this gets to
    be a problem, music21 could be modified to keep track of "rounding errors"
    and make sure that for instance half the notes of an 11:1 are 916 divisions
    long and the other half are 917.  But this has not been done yet.
    '''

    divisionsPerQuarter = 32*3*3*5*7 # 10080

    def makeDoc(self, duration, openDoc = xml.dom.minidom.Document()):
        divisions = str(int(round(duration.quarterLength * self.divisionsPerQuarter)))

        divisionsEl = openDoc.createElement("divisions")
        divisionsNode = openDoc.createTextNode(divisions)
        divisionsEl.appendChild(divisionsNode)

        typeEl = openDoc.createElement("type")
        typeNode = openDoc.createTextNode(duration.type)
        typeEl.appendChild(typeNode)

        dotsHolder = []
        for i in range(int(duration.dots)):
            dotEl  = openDoc.createElement("dot")
            dotsHolder.append(dotEl)

        timeModEl = ""
        tupletEls = []

        if (len(duration.tuplets) > 0):
            (num, den) = duration.aggregateTupletRatio()
            timeModEl = openDoc.createElement("time-modification")
            actNotesEl = openDoc.createElement("actual-notes")
            actNotesNode = openDoc.createTextNode(str(num))
            actNotesEl.appendChild(actNotesNode)

            normNotesEl = openDoc.createElement("normal-notes")
            normNotesNode = openDoc.createTextNode(str(den))
            normNotesEl.appendChild(normNotesNode)

            timeModEl.appendChild(actNotesEl)
            timeModEl.appendChild(normNotesEl)

            for i in range(duration.tuplets):
                thisTuplet = duration.tuplets[i]
                if thisTuplet.type == "start" or thisTuplet.type == "stop":
                    newTupEl = openDoc.createElement("tuplet")
                    newTupEl.setAttribute("type", thisTuplet.type)
                    if len(duration.tuplets > 1):
                        newTupEl.setAttribute("number", i+1)
                        
                    tupletActual = openDoc.createElement("tuplet-actual")
                    tupletANum   = openDoc.createElement("tuplet-number")
                    tupletANumN  = openDoc.createTextElement(thisTuplet.tupletActual[0])
                    tupletANum.appendChild(tupletANumN)
                    
        
        return(divisionsEl, typeEl, dotsHolder, timeModEl, tupletEls)



if (__name__ == "__main__"):
    n1 = music21.note.Note()
    n1.name = "G#"
    n1.octave = 5
    n1.duration.type = "whole"
    n1.duration.dots = 2
    n1.duration.tuplets.append(music21.note.Tuplet())
    n1.duration.tuplets[0].type = "start"
    n1.tie = music21.note.Tie("start")

    fac2 = XML_SimpleNote_Factory()
    md = fac2.makeDoc(n1)
    print md.toprettyxml()
    
