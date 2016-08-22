# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         fromCapellaXML.py
# Purpose:      Module for importing capellaXML (.capx) files.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
A beta version of a complete .capx to music21 converter.

Currently only handles one <voice> per <staff> and does not deal with
Slurs, Dynamics, Ornamentation, etc.

Does not handle pickup notes, which are defined simply with an early barline
(same as incomplete bars at the end).
'''
import xml.etree.ElementTree
import unittest
import zipfile

from music21.ext.six import StringIO, string_types

from music21 import bar
from music21 import chord
from music21 import clef
from music21 import common
from music21 import duration
#from music21 import dynamics
from music21 import exceptions21
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
from music21 import tie

#from music21 import environment
#_MOD = 'capella/fromCapellaXML.py'
#environLocal = environment.Environment(_MOD)

#capellaDynamics = {'r': 'ppp',
#                   'q': 'pp',
#                   'p': 'p',
#                   'i': 'mp',
#                   'j': 'mf',
#                   'f': 'f',
#                   'g': 'ff',
#                   'h': 'fff',
#                   's': 'sf',
#                   'z': 'sfz',
#                   '{': 'fz',
#                   '|': 'fp',
#                   }
#
#isSegno1 = lambda char: char == 'y'
#isSegno2 = lambda char: char == '$'
#isSegno  = lambda char: isSegno1(char) or isSegno2(char)
#isCodaLarge = lambda char: char == 'n'
#isCodaSmall = lambda char: char == 'o'
#isCoda = lambda char: isCodaLarge(char) or isCodaSmall(char) 
#isPedalStart = lambda char: char == 'a'
#isPedalStop = lambda char: char == 'b'
#isFermataAbove = lambda char: char == 'u'
#isFermataBelow = lambda char: char == 'k'
#isFermata = lambda char: isFermataAbove(char) or isFermataBelow(char)
#
#isUpbow = lambda char: char == 'Z'
#isDownbow = lambda char: char == 'Y'
#
#isTrill = lambda char: char == 't'
#isInvertedMordent = lambda char: char == 'l'
#isMordent = lambda char: char == 'x'
#isTurn = lambda char: char == 'w'
#isOrnament = lambda char: (isTrill(char) or isInvertedMordent(char) or 
#        isMordent(char) or isTurn(char))


class CapellaImportException(exceptions21.Music21Exception):
    pass

class CapellaImporter(object):
    '''
    Object for importing .capx, CapellaXML files into music21 (from which they can be
    converted to musicxml, MIDI, lilypond, etc.

    Note that Capella stores files closer to their printed versions -- that is to say,
    Systems enclose all the parts for that system and have new clefs etc.
    '''
    def __init__(self):
        self.xmlText = None
        self.zipFilename = None
        self.mainDom = None

    def scoreFromFile(self, filename, systemScore=False):
        '''
        main program: opens a file given by filename and returns a complete
        music21 Score from it.
        
        If systemScore is True then it skips the step of making Parts from Systems
        and Measures within Parts.
        '''
                #ci.readCapellaXMLFile(r'd:/desktop/achsorgd.capx')
        self.readCapellaXMLFile(filename)
        self.parseXMLText()
        scoreObj = self.systemScoreFromScore(self.mainDom)
        if systemScore is True:
            return scoreObj
        else:
            partScore = self.partScoreFromSystemScore(scoreObj)
            return partScore

    def readCapellaXMLFile(self, filename):
        '''
        Reads in a .capx file at `filename`, stores it as self.zipFilename, unzips it, 
        extracts the score.xml embedded file, sets self.xmlText to the contents.
        
        Returns self.xmlText
        '''
        self.zipFilename = filename
        zipFileHandle = zipfile.ZipFile(filename, 'r')
        xmlText = zipFileHandle.read('score.xml')
        self.xmlText = xmlText
        return xmlText

    def parseXMLText(self, xmlText=None):
        '''
        Takes the string (or unicode string) in xmlText and parses it with `xml.dom.minidom`.
        Sets `self.mainDom` to the dom object and returns the dom object.
        '''
        if xmlText is None:
            xmlText = self.xmlText
        if not isinstance(xmlText, string_types):
            xmlText = xmlText.decode('utf-8')
        it = xml.etree.ElementTree.iterparse(StringIO(xmlText))
        for unused, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        self.mainDom = it.root
        return self.mainDom

    def domElementFromText(self, xmlText=None):
        '''
        Utility method, especially for the documentation examples/tests, which uses
        `xml.etree.ElementTree` to parse the string and returns its root object.
        
        Not used by the main parser
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> funnyTag = ci.domElementFromText(
        ...    '<funny yes="definitely"><greg/>hi<greg><ha>ha</ha>' + 
        ...    '<greg type="embedded"/></greg></funny>')
        >>> funnyTag
        <Element 'funny' at 0x...>
        
        iter searches recursively
        
        >>> len(list(funnyTag.iter('greg')))
        3
        
        findall does not:
        
        >>> len(funnyTag.findall('greg'))
        2
        '''
        return xml.etree.ElementTree.fromstring(xmlText)
        

    def partScoreFromSystemScore(self, systemScore):
        '''
        Take a :class:`~music21.stream.Score` object which is organized
        by Systems and return a new `Score` object which is organized by
        Parts.
        '''
        # this line is redundant currently, since all we have in systemScore
        # are Systems, but later there will be other things.
        systemStream = systemScore.getElementsByClass('System') 
        partDictById = {}
        for thisSystem in systemStream:
            # this line is redundant currently, since all we have in
            # thisSystem are Parts, but later there will be other things.
            systemOffset = systemScore.elementOffset(thisSystem)
            partStream = thisSystem.getElementsByClass('Part')
            for j, thisPart in enumerate(partStream):
                if thisPart.id not in partDictById:
                    newPart = stream.Part()
                    newPart.id = thisPart.id
                    partDictById[thisPart.id] = {'part': newPart, 'number': j}
                else:
                    newPart = partDictById[thisPart.id]['part']
                for el in thisPart: # no need for recurse...
                    newPart._insertCore(common.opFrac(el.offset + systemOffset), el)
                newPart.elementsChanged()
        newScore = stream.Score()
        ## ORDERED DICT
        parts = [None for i in range(len(partDictById))]
        for partId in partDictById:
            partDict = partDictById[partId]
            parts[partDict['number']] = partDict['part']
        for p in parts:
            # remove redundant Clef and KeySignatures
            if p is None:
                print('part entries do not match partDict!')
                continue
            clefs = p.getElementsByClass('Clef')
            keySignatures = p.getElementsByClass('KeySignature')
            lastClef = None
            lastKeySignature = None
            for c in clefs:
                if c == lastClef:
                    p.remove(c)
                else:
                    lastClef = c
            for ks in keySignatures:
                if ks == lastKeySignature:
                    p.remove(ks)
                else:
                    lastKeySignature = ks
            p.makeMeasures(inPlace=True)
#            for m in p.getElementsByClass('Measure'):
#                barLines = m.getElementsByClass('Barline')
#                for bl in barLines:
#                    blOffset = bl.offset
#                    if blOffset == 0.0:
#                        m.remove(bl)
#                        m.leftBarline = bl
#                    elif blOffset == m.highestTime:
#                        m.remove(bl)
#                        m.rightBarline = bl # will not yet work for double repeats!
                        
            newScore._insertCore(0, p)
        newScore.elementsChanged()
        return newScore

    def systemScoreFromScore(self, scoreElement, scoreObj=None):
        '''
        returns an :class:`~music21.stream.Score` object from a <score> tag.
        
        The Score object is not a standard music21 Score object which contains
        parts, then measures, then voices, but instead contains systems which 
        optionally contain voices, which contain parts.  No measures have yet
        been created.
        '''
        if scoreObj is None:
            scoreObj = stream.Score()

        systemsList = scoreElement.findall('systems')
        if len(systemsList) == 0:
            raise CapellaImportException(
                "Cannot find a <systems> tag in the <score> object")
        elif len(systemsList) > 1:
            raise CapellaImportException(
                "Found more than one <systems> tag in the <score> object, what does this mean?")
        systemsElement = systemsList[0]
        
        systemList = systemsElement.findall('system')
        if len(systemList) == 0:
            raise CapellaImportException(
                'Cannot find any <system> tags in the <systems> tag in the <score> object')
        
        for systemNumber, thisSystem in enumerate(systemList):
            systemObj = self.systemFromSystem(thisSystem)
            systemObj.systemNumber = systemNumber + 1 # 1 indexed, like musicians think
            scoreObj._appendCore(systemObj)

        scoreObj.elementsChanged()
        return scoreObj

    def systemFromSystem(self, systemElement, systemObj=None):
        r'''
        returns a :class:`~music21.stream.System` object from a <system> tag.
        The System object will contain :class:`~music21.stream.Part` objects
        which will have the notes, etc. contained in it.  

        TODO: Handle multiple <voices>
        '''
        if systemObj is None:
            systemObj = stream.System()
            
        stavesList = systemElement.findall('staves')
        if len(stavesList) == 0:
            raise CapellaImportException("No <staves> tag found in this <system> element")
        elif len(stavesList) > 1:
            raise CapellaImportException(
                "More than one <staves> tag found in this <system> element")
        stavesElement = stavesList[0]
        staffList = stavesElement.findall('staff')
        if len(stavesList) == 0:
            raise CapellaImportException(
                "No <staff> tag found in the <staves> element for this <system> element")
        for thisStaffElement in staffList:
            # do something with defaultTime
            partId = "UnknownPart"
            if 'layout' in thisStaffElement.attrib:
                partId = thisStaffElement.attrib['layout']
            partObj = stream.Part()
            partObj.id = partId
            
            voicesList = thisStaffElement.findall('voices')
            if len(voicesList) == 0:
                raise CapellaImportException(
                    "No <voices> tag found in the <staff> tag for the <staves> element " + 
                    "for this <system> element")
            voicesElement = voicesList[0]
            voiceList = voicesElement.findall('voice')
            if len(voiceList) == 0:
                raise CapellaImportException(
                    "No <voice> tag found in the <voices> tag for the <staff> tag for the " + 
                    "<staves> element for this <system> element")
            if len(voiceList) == 1: # single voice staff... perfect!
                thisVoiceElement = voiceList[0]
                noteObjectsList = thisVoiceElement.findall('noteObjects')
                if len(noteObjectsList) == 0:
                    raise CapellaImportException(
                            "No <noteObjects> tag found in the <voice> tag found in the " + 
                            "<voices> tag for the <staff> tag for the <staves> element for " + 
                            "this <system> element")
                elif len(noteObjectsList) > 1:
                    raise CapellaImportException(
                            "More than one <noteObjects> tag found in the <voice> tag found " + 
                            "in the <voices> tag for the <staff> tag for the <staves> element " + 
                            "for this <system> element")
                thisNoteObject = noteObjectsList[0]
                self.streamFromNoteObjects(thisNoteObject, partObj)
            systemObj.insert(0, partObj)
        return systemObj
    
    def streamFromNoteObjects(self, noteObjectsElement, streamObj=None):
        r'''
        
        Converts a <noteObjects> tag into a :class:`~music21.stream.Stream` object 
        which is returned.
        A Stream can be given as an optional argument, in which case the objects of this
        Stream are appended to this object.
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> noteObjectsString = r"""
        ...           <noteObjects>
        ...                <clefSign clef="G2-"/>
        ...                <keySign fifths="-1"/>
        ...                <chord>
        ...                    <duration base="1/2"/>
        ...                    <lyric>
        ...                        <verse i="0">das,</verse>
        ...                        <verse i="1">scherz,</verse>
        ...                    </lyric>
        ...                    <heads>
        ...                        <head pitch="G4"/>
        ...                    </heads>
        ...                </chord>
        ...                <chord>
        ...                    <duration base="1/2"/>
        ...                    <lyric>
        ...                        <verse i="0">so</verse>
        ...                        <verse i="1">der</verse>
        ...                    </lyric>
        ...                    <heads>
        ...                        <head pitch="A4"/>
        ...                    </heads>
        ...                </chord>
        ...                <barline type="end"/>
        ...            </noteObjects>
        ...            """
        >>> noteObjectsElement = ci.domElementFromText(noteObjectsString)
        >>> s = ci.streamFromNoteObjects(noteObjectsElement)
        >>> s.show('text')
        {0.0} <music21.clef.Treble8vbClef>
        {0.0} <music21.key.KeySignature of 1 flat>
        {0.0} <music21.note.Note G>
        {2.0} <music21.note.Note A>
        {4.0} <music21.bar.Barline style=final>
        
        >>> s.highestTime
        4.0
        '''
        if streamObj is None:
            s = stream.Stream()
        else:
            s = streamObj
            
        mapping = {'clefSign': self.clefFromClefSign,
                   'keySign': self.keySignatureFromKeySign,
                   'timeSign': self.timeSignatureFromTimeSign,
                   'rest': self.restFromRest,
                   'chord': self.chordOrNoteFromChord,
                   'barline': self.barlineListFromBarline,
                   }

        for d in noteObjectsElement:
            el = None
            t = d.tag
            if t not in mapping:
                print("Unknown tag type: %s" % t)
            else:
                el = mapping[t](d)
                if isinstance(el, list): #barlineList returns a list
                    for elSub in el:
                        s._appendCore(elSub)
                elif el is None:
                    pass
                else:
                    s._appendCore(el)
                    
        s.elementsChanged()
        return s

    def restFromRest(self, restElement):
        '''
        Returns a :class:`~music21.rest.Rest` object from a <rest> tag. 
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> restElement = ci.domElementFromText('<rest><duration base="1/2"/></rest>')
        >>> r = ci.restFromRest(restElement)
        >>> r
        <music21.note.Rest rest>
        >>> r.duration.type
        'half'
        '''
        r = note.Rest()
        durationList = restElement.findall('duration')
        r.duration = self.durationFromDuration(durationList[0])
        return r
    
    def chordOrNoteFromChord(self, chordElement):
        '''
        returns a :class:`~music21.note.Note` or :class:`~music21.chord.Chord` 
        from a chordElement -- a `Note`
        is returned if the <chord> has one <head> element, a `Chord` is 
        returned if there are multiple <head> elements.

        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> chordElement = ci.domElementFromText(
        ...     '<chord><duration base="1/1"/><heads><head pitch="G4"/></heads></chord>')
        >>> n = ci.chordOrNoteFromChord(chordElement)
        >>> n
        <music21.note.Note G>
        >>> n.duration
        <music21.duration.Duration 4.0>

        This one is an actual chord
        
        >>> chordElement = ci.domElementFromText(
        ...        '<chord><duration base="1/8"/>' + 
        ...        '<heads><head pitch="G4"/><head pitch="A5"/></heads></chord>')
        >>> c = ci.chordOrNoteFromChord(chordElement)
        >>> c
        <music21.chord.Chord G3 A4>
        >>> c.duration
        <music21.duration.Duration 0.5>
        
        
        TODO: test Lyrics
        '''
        durationList = chordElement.findall('duration')
        headsList = chordElement.findall('heads')
        
        if len(durationList) != 1 or len(headsList) != 1:
            raise CapellaImportException("Malformed chord!")

        notesList = self.notesFromHeads(headsList[0])
        
        noteOrChord = None
        if len(notesList) == 0:
            raise CapellaImportException("Malformed chord!")
        elif len(notesList) == 1:
            noteOrChord = notesList[0] # a Note object
        else:
            noteOrChord = chord.Chord(notesList)
        
        noteOrChord.duration = self.durationFromDuration(durationList[0])

        lyricsList = chordElement.findall('lyric')
        if len(lyricsList) > 0:
            lyricsList = self.lyricListFromLyric(lyricsList[0])
            noteOrChord.lyrics = lyricsList
            
        return noteOrChord
            
    def notesFromHeads(self, headsElement):
        '''
        returns a list of :class:`~music21.note.Note` elements for each <head> in <heads> 

        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> headsElement = ci.domElementFromText(
        ...    '<heads><head pitch="B7"><alter step="-1"/></head><head pitch="C2"/></heads>')
        >>> ci.notesFromHeads(headsElement)
        [<music21.note.Note B->, <music21.note.Note C>]
        '''
        notes = []
        headDomList = headsElement.findall('head')
        for headElement in headDomList:
            notes.append(self.noteFromHead(headElement))            
        return notes

    def noteFromHead(self, headElement):
        ''' 
        return a :class:`~music21.note.Note` object from a <head> element.  This will become
        part of Chord._notes if there are multiple, but in any case, it needs to be a Note
        not a Pitch for now, because it could have Tie information

        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> headElement = ci.domElementFromText(
        ...      '<head pitch="B7"><alter step="-1"/><tie end="true"/></head>')
        >>> n = ci.noteFromHead(headElement)
        >>> n
        <music21.note.Note B->
        >>> n.octave # capella octaves are one higher than written
        6
        >>> n.tie
        <music21.tie.Tie stop>
        '''
        if 'pitch' not in headElement.attrib:
            raise CapellaImportException("Cannot deal with <head> element without pitch!")
    
        noteNameWithOctave = headElement.attrib['pitch']
        n = note.Note()
        n.nameWithOctave = noteNameWithOctave
        n.octave = n.octave - 1 # capella octaves are 1 off...

        alters = headElement.findall('alter')
        if len(alters) > 1:
            raise CapellaImportException("Cannot deal with multiple <alter> elements!")
        elif len(alters) == 1:
            acc = self.accidentalFromAlter(alters[0])
            n.pitch.accidental = acc

        ties = headElement.findall('tie')
        if len(ties) > 1:
            raise CapellaImportException("Cannot deal with multiple <tie> elements!")
        elif len(ties) == 1:
            thisTie = self.tieFromTie(ties[0])
            n.tie = thisTie

        return n

    def accidentalFromAlter(self, alterElement):
        '''
        return a :class:`~music21.pitch.Accidental` object from an <alter> tag.
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> alter = ci.domElementFromText('<alter step="-1"/>')
        >>> ci.accidentalFromAlter(alter)
        <accidental flat>

        The only known display type is "suppress"

        >>> alter = ci.domElementFromText('<alter step="2" display="suppress"/>')
        >>> acc = ci.accidentalFromAlter(alter)
        >>> acc
        <accidental double-sharp>
        >>> acc.displayType
        'never'
        '''
        if 'step' in alterElement.attrib:
            alteration = int(alterElement.attrib['step'])
        else:
            print("No alteration...")
            alteration = 0
        acc = pitch.Accidental(alteration)

        if 'display' in alterElement.attrib and alterElement.attrib['display'] == 'suppress':
            acc.displayType = 'never'
        return acc
        
    def tieFromTie(self, tieElement):
        '''
        returns a :class:`~music21.tie.Tie` element from a <tie> tag
        
        if begin == 'true' then Tie.type = start
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> tieEl = ci.domElementFromText('<tie begin="true"/>')
        >>> ci.tieFromTie(tieEl)
        <music21.tie.Tie start>

        if end == 'true' then Tie.type = stop

        >>> tieEl = ci.domElementFromText('<tie end="true"/>')
        >>> ci.tieFromTie(tieEl)
        <music21.tie.Tie stop>
        
        if begin == 'true' and end == 'true' then Tie.type = continue (is this right???)

        >>> tieEl = ci.domElementFromText('<tie begin="true" end="true"/>')
        >>> ci.tieFromTie(tieEl)
        <music21.tie.Tie continue>
        '''
        begin = False
        end = False
        if 'begin' in tieElement.attrib and tieElement.attrib['begin'] == 'true':
            begin = True
        if 'end' in tieElement.attrib and tieElement.attrib['end'] == 'true':
            end = True
        
        tieType = None
        if begin is True and end is True:
            tieType = 'continue'
        elif begin is True:
            tieType = 'start'
        elif end is True:
            tieType = 'stop'
        else:
            return None
            
        tieObj = tie.Tie(tieType)
        return tieObj

    def lyricListFromLyric(self, lyricElement):
        '''
        returns a list of :class:`~music21.note.Lyric` objects from a <lyric> tag
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> lyricEl = ci.domElementFromText(
        ...      '<lyric><verse i="0" hyphen="true">di</verse>' + 
        ...      '<verse i="1">man,</verse><verse i="2">frau,</verse></lyric>')
        >>> ci.lyricListFromLyric(lyricEl)
        [<music21.note.Lyric number=1 syllabic=begin text="di">, 
         <music21.note.Lyric number=2 syllabic=single text="man,">, 
         <music21.note.Lyric number=3 syllabic=single text="frau,">]
        '''
        lyricList = []
        verses = lyricElement.findall('verse')
        for d in verses:
            thisLyric = self.lyricFromVerse(d)
            if thisLyric is not None:
                lyricList.append(thisLyric)
        return lyricList

    def lyricFromVerse(self, verse):
        '''
        returns a :class:`~music21.note.Lyric` object from a <verse> tag

        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> verse = ci.domElementFromText('<verse i="0" hyphen="true">di&quot;</verse>')
        >>> ci.lyricFromVerse(verse)
        <music21.note.Lyric number=1 syllabic=begin text="di"">

        Does not yet support 'align' attribute

        if the text is empty, returns None
        '''
        verseNumber = 1
        syllabic = 'single'
        if 'i' in verse.attrib:
            verseNumber = int(verse.attrib['i']) + 1
        if 'hyphen' in verse.attrib and verse.attrib['hyphen'] == 'true':
            syllabic = 'begin'
        text = verse.text
        if text is None or text == "":
            return None
        else:
            lyric = note.Lyric(text=text, number=verseNumber, syllabic=syllabic, applyRaw=True)        
            return lyric
        
        # i = number - 1
        # align
        # hyphen = true
    
    
    clefMapping = {'treble': clef.TrebleClef,
                   'bass': clef.BassClef,
                   'alto': clef.AltoClef,
                   'tenor': clef.TenorClef,
                   'G2-': clef.Treble8vbClef,
                   }
    
    def clefFromClefSign(self, clefSign):
        '''
        returns a :class:`~music21.clef.Clef` object or subclass from a <clefSign> tag. 
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> clefSign = ci.domElementFromText('<clefSign clef="treble"/>')
        >>> ci.clefFromClefSign(clefSign)
        <music21.clef.TrebleClef>

        >>> clefSign = ci.domElementFromText('<clefSign clef="G2-"/>')
        >>> ci.clefFromClefSign(clefSign)
        <music21.clef.Treble8vbClef>

        >>> clefSign = ci.domElementFromText('<clefSign clef="F1+"/>')
        >>> clefObject = ci.clefFromClefSign(clefSign)
        >>> clefObject
        <music21.clef.FClef>
        >>> clefObject.sign
        'F'
        >>> clefObject.line
        1
        >>> clefObject.octaveChange
        1
        '''
        if 'clef' in clefSign.attrib:
            clefValue = clefSign.attrib['clef']
            if clefValue in self.clefMapping:
                return self.clefMapping[clefValue]()
            elif clefValue[0] == 'p':
                return clef.PercussionClef()
            elif len(clefValue) > 1:
                clefSignAndLine = clefValue[0:2]
                clefOctaveChange = 0
                if len(clefValue) > 2:
                    if clefValue[2] == '+':
                        clefOctaveChange = 1
                    elif clefValue[2] == '-':
                        clefOctaveChange = -1
                clefObj = clef.clefFromString(clefSignAndLine, clefOctaveChange)
                return clefObj
                    
        return None
    
    def keySignatureFromKeySign(self, keySign):
        '''
        Returns a :class:`~music21.key.KeySignature` object from a keySign tag. 
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> keySign = ci.domElementFromText('<keySign fifths="-1"/>')
        >>> ci.keySignatureFromKeySign(keySign)
        <music21.key.KeySignature of 1 flat>
        '''
        if 'fifths' in keySign.attrib:
            keyFifths = int(keySign.attrib['fifths'])
            return key.KeySignature(keyFifths)
    
    def timeSignatureFromTimeSign(self, timeSign):
        '''
        Returns a :class:`~music21.meter.TimeSignature` object from a timeSign tag. 
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> timeSign = ci.domElementFromText('<timeSign time="4/4"/>')
        >>> ci.timeSignatureFromTimeSign(timeSign)
        <music21.meter.TimeSignature 4/4>

        >>> timeSign = ci.domElementFromText('<timeSign time="infinite"/>')
        >>> ci.timeSignatureFromTimeSign(timeSign) is None
        True
        '''
        if 'time' in timeSign.attrib:
            timeString = timeSign.attrib['time']
            if timeString != 'infinite':
                return meter.TimeSignature(timeString)
            else:
                return None
        else:
            return None
    
    
    def durationFromDuration(self, durationElement):
        '''
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> durationTag = ci.domElementFromText('<duration base="1/32" dots="1"/>')
        >>> d = ci.durationFromDuration(durationTag)
        >>> d
        <music21.duration.Duration 0.1875>
        >>> d.type
        '32nd'
        >>> d.dots
        1

        >>> durationTag2 = ci.domElementFromText(
        ...      '<duration base="1/4"><tuplet count="3"/></duration>')
        >>> d2 = ci.durationFromDuration(durationTag2)
        >>> d2
        <music21.duration.Duration 2/3>
        >>> d2.type
        'quarter'
        >>> d2.tuplets
        (<music21.duration.Tuplet 3/2/eighth>,)


        Does not handle noDuration='true', display, churchStyle on rest durations
        '''
        dur = duration.Duration()

        if 'base' in durationElement.attrib:
            baseValue = durationElement.attrib['base']
            slashIndex = baseValue.find("/")
            if slashIndex != -1:
                firstNumber = int(baseValue[0:slashIndex])
                secondNumber = int(baseValue[slashIndex+1:])
                quarterLength = (4.0 * firstNumber)/secondNumber
                dur.quarterLength = quarterLength

        if 'dots' in durationElement.attrib:
            dotNumber = int(durationElement.attrib['dots'])
            dur.dots = dotNumber
        
        tuplets = durationElement.findall('tuplet')
        for d in tuplets:
            tuplet = self.tupletFromTuplet(d)
            dur.appendTuplet(tuplet)

        return dur
    
    def tupletFromTuplet(self, tupletElement):
        '''
        Returns a :class:`~music21.duration.Tuplet` object from a <tuplet> tag. 

        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> tupletTag = ci.domElementFromText('<tuplet count="3"/>')
        >>> ci.tupletFromTuplet(tupletTag)    
        <music21.duration.Tuplet 3/2/eighth>
        
        does not handle 'tripartite' = True
        '''
        numerator = 1
        denominator = 1
        if 'count' in tupletElement.attrib:
            numerator = int(tupletElement.attrib['count'])
            denominator = 1
            while numerator > denominator * 2:
                denominator *= 2
        if 'prolong' in tupletElement.attrib and tupletElement.attrib['count'] == 'true':
            denominator *= 2
        
        if 'tripartite' in tupletElement.attrib:
            print(
                "WE DON'T HANDLE TRIPARTITE YET! Email the file and a pdf so I can figure it out")
        
        tup = duration.Tuplet(numerator, denominator)
        return tup

    barlineMap = {'single': 'normal',
                  'double': 'double',
                  'end': 'final',
                  'repEnd': 'end',
                  'repBegin': 'start',
                  'repEndBegin': 'end-start',
                  }

    def barlineListFromBarline(self, barlineElement):
        '''
        Indication that the barline at this point should be something other than normal.
        
        Capella does not indicate measure breaks or barline breaks normally, so the only barlines
        that are indicated are unusual ones.
        
        Returns a LIST of :class:`~music21.bar.Barline` or :class:`~music21.bar.Repeat` objects
        because the `repEndBegin` type requires two `bar.Repeat` objects to encode in `music21`. 
        
        
        >>> ci = capella.fromCapellaXML.CapellaImporter()
        >>> barlineTag = ci.domElementFromText('<barline type="end"/>')
        >>> ci.barlineListFromBarline(barlineTag)    
        [<music21.bar.Barline style=final>]

        >>> repeatTag = ci.domElementFromText('<barline type="repEndBegin"/>')
        >>> ci.barlineListFromBarline(repeatTag)    
        [<music21.bar.Repeat direction=end>, <music21.bar.Repeat direction=start>]

        '''
        barlineList = []
        hasRepeatEnd = False
        if 'type' in barlineElement.attrib:
            barlineType = barlineElement.attrib['type']
            if barlineType.startswith('rep'): # begins with rep
                if barlineType in self.barlineMap:
                    repeatType = self.barlineMap[barlineType]
                    if repeatType.find('end') > -1:
                        barlineList.append(bar.Repeat('end'))
                        hasRepeatEnd = True
                    if repeatType.find('start') > -1:
                        startRep = bar.Repeat('start')
                        if hasRepeatEnd is True:
                            startRep.priority = 1
                        barlineList.append(startRep)
            else:            
                if barlineType in self.barlineMap:
                    barlineList.append(bar.Barline(self.barlineMap[barlineType]))
            
        return barlineList
    def slurFromDrawObjSlur(self, drawObj):
        '''
        not implemented
        '''
        pass
    

class Test(unittest.TestCase):
    pass

class TestExternal(unittest.TestCase):
    pass

    def testComplete(self):
        ci = CapellaImporter()
        #ci.readCapellaXMLFile(r'd:/desktop/achsorgd.capx')
        import os
        capellaDirPath = common.getSourceFilePath() + os.path.sep + 'capella'
        oswaldPath = capellaDirPath + os.path.sep + r'Nu_rue_mit_sorgen.capx'
        partScore = ci.scoreFromFile(oswaldPath)
        partScore.show()
        
    def xtestImportSorgen(self):
        ci = CapellaImporter()
        import os
        capellaDirPath = common.getSourceFilePath() + os.path.sep + 'capella'
        oswaldPath = capellaDirPath + os.path.sep + r'Nu_rue_mit_sorgen.capx'

        ci.readCapellaXMLFile(oswaldPath)
        ci.parseXMLText()
        #firstSystemObject = ci.mainDom.documentElement.getElementsByTagName('system')[0]
        #m21SystemObj = ci.systemFromSystem(firstSystemObject)
        #m21SystemObj.show('text')
        #scoreElement = ci.mainDom.documentElement.getElementsByTagName('score')[0]
        scoreObj = ci.systemScoreFromScore(ci.mainDom.documentElement)
        partScore = ci.partScoreFromSystemScore(scoreObj)
        partScore.show()
        #ci.walkNodes()
        #print ci.xmlText


if __name__ == '__main__':
    import music21
    music21.mainTest(Test, TestExternal)
