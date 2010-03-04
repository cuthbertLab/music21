### DEPRECATED -- REMOVE ---
import copy

import music21
import music21.lily
from music21.lily.lilyString import LilyString


class LilyContainer(LilyString):
    contents = ""
    containerStart = "{\n"
    containerEnd   = "\n}\n"
    definedLily = ""
    element = "generic"
    
    def __init__(self, *otherContents):
        self.contentSections = []
        if (otherContents):
            for listEl in otherContents:
                self.contentSections.append(listEl)            
    
    def getLily(self):
        if self.definedLily:
            return self.definedLily
        else:
            retLily = self.containerStart
            for obj in self.contentSections:
                if hasattr(obj, "lily"):
                    retLily += obj.lily
                else:
                    retLily += obj
                    
            retLily += self.containerEnd
            return retLily
        
    def setLily(self, value):
        self.definedLily = value

    def __repr__(self):
        return self.getLily()
    
    lily = property(getLily, setLily)
    value = property(getLily, setLily)

    def firstContents(self, elType, Recursive = True):
        '''
        Find the first instance of elType ("voice", "staff", "stream", "note", etc.) in the lilypond score
        and return it
        
        Unless Recursive is False, will descend into the tree to find the element.
        '''
        for thisCS in self.contentSections:
            if hasattr(thisCS, "element"):
                if thisCS.element == elType:
                    return thisCS
                else:
                    if Recursive is True and len(thisCS.contentSections) > 0:
                        foundFirst = thisCS.firstContents(elType)
                        if foundFirst is not None:
                            return foundFirst
            else:
                ## text node
                if elType == "text":
                    return thisCS
        return None
    
    def contains(self, elType, Recursive = True):
        if self.firstContents(elType, Recursive) is not None:
            return True
        else:
            return False

    def appendElement(self, el):
        self.contentSections.append(el)
    
    def appendTimeSignature(self, tS):
        if hasattr(tS, "lily"):
            self.contentSections.append("\\time " + tS.lily)
        else:
            self.contentSections.append("\\time " + tS)

    def prependTimeSignature(self, tS):
        if self.contentSections:
            if hasattr(tS, "lily"):
                self.contentSections.insert(0, "\\time " + tS.lily)
            else:   
                self.contentSections.insert(0, "\\time " + tS)
        else:
            self.appendTimeSignature(tS)
    
    def appendHeader(self, headerString):
        self.contentSections.append(music21.lily.quickHeader(headerString))
    
class LilyFile(LilyContainer):
    containerStart = ""
    containerEnd = ""
    element = "file"
    
class LilyScore(LilyContainer):
    containerStart = "\\score {\n"
    containerEnd   = "\n}\n"
    element = "score"
    
    def addVoiceSection(self, contents = None):
        lvs1 = LilyVoiceSection(contents)
    
class LilyVoiceSection(LilyContainer):
    containerStart = "   <<\n"
    containerEnd   = "   >>\n"
    element = "voiceSection"
    
class LilyVoice(LilyContainer):
    element = "voice"

class LilyStaff(LilyContainer):
    containerStart = "  \\new Staff {\n"
    element = "staff"

class LilyLayout(LilyContainer):
    containerStart = "\\layout {\n"    
    element = "layout"

class LilyMidi(LilyContainer):
    containerStart = "\\midi {\n"
    element = "midi"
    










def test():
    from music21.stream import Stream
    
    n1 = music21.note.Note()
    n1.name = "E"
    n1.duration.type = "half"
    
    n3 = music21.note.Note()
    n3.name = "D"
    n3.duration.type = "half"
    
    n2 = music21.note.Note()
    n2.name = "C#"
    n2.octave = 5
    n2.duration.type = "half"
    
    n4 = n3.clone()
    n4.octave = 5

    st1 = Stream()
    st2 = Stream()
    st1.append([n1, n3])
    st2.append([n2, n4])

    staff1 = LilyStaff()
    staff1.appendElement(st1)
    staff2 = LilyStaff()
    staff2.appendElement(st2)
    vs1 = LilyVoiceSection(staff2, staff1)
    vs1.prependTimeSignature("2/2")
    isStaff2 = vs1.firstContents("staff")
    assert isStaff2 is staff2, "first staff in Voice Section should be staff2"
    
    s1 = LilyScore(vs1, LilyLayout(), LilyMidi() )
    lf1 = LilyFile(s1)
    isStaff2 = lf1.firstContents("staff")
    assert isStaff2 is staff2, "first staff in File should be staff2"

    print(lf1)
    if lf1:
        lf1.showPNGandPlayMIDI()
    print(lf1.midiFilename)

if (__name__ == "__main__"):
    test()