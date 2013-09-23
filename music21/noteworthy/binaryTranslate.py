# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         noteworthy/binaryTranslate.py
# Purpose:      parses .nwc binary files, compressed and uncompressed
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2013 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Attempts at reading pure .nwc files in music21

First will solve uncompressed .nwc then compressed .nwc

Thanks to Juria90 and the nwc2xml project for solving so many of the documentation problems.
No part of this code is taken from that project, but this project would have been impossible
without his work.

Translates .nwc into .nwctxt and then uses Jordi Guillen's .nwctxt translator to go from
there to music21.
'''
import struct

class NWCConverter(object):
    def __init__(self, *args, **keywords):
        if 'fp' in keywords:
            self.fp = keywords['fp']
        else:
            self.fp = None
        self.fileContents = None
        self.parsePosition = 0
        self.version = 200
        self.numberOfStaves = 0
        self.staves = []
    
    def parseFile(self, fp = None):
        if fp is None:
            fp = self.fp
        with open(fp, 'rb') as f:
            self.fileContents = f.read()
        self.parse()
        return self.toStream()
    
    def parseString(self, stringIn = None):
        self.fileContents = stringIn
        self.parse()
        return self.toStream()
                

    def readLEShort(self, updateParsePosition = True):
        '''
        read a little-endian short value to an integer
        '''
        fc = self.fileContents
        pp = self.parsePosition
        value = struct.unpack('<h', fc[pp:pp+2])[0]
        
        if updateParsePosition is True:
            self.parsePosition = pp+2
        return value

    def byteToInt(self, updateParsePosition = True):
        fc = self.fileContents
        pp = self.parsePosition
        value = ord(fc[pp:pp+1])
        #print value
        if updateParsePosition is True:
            self.parsePosition = pp+1
        return value
        
    def byteToSignedInt(self, updateParsePosition = True):
        val = self.byteToInt(updateParsePosition)
        if val > 127:
            val = val - 256
        return val
        
    def readBytes(self, bytesToRead = 1, updateParsePosition = True):
        fc = self.fileContents
        pp = self.parsePosition
        value = fc[pp:pp+bytesToRead]
        if updateParsePosition is True:
            self.parsePosition = pp+bytesToRead
        return value

    def readToNUL(self, updateParsePosition = True):
        fc = self.fileContents
        nulPosition = fc.find('\x00', self.parsePosition)
        ret = None
        if nulPosition == -1:
            ret = fc[self.parsePosition:]
        else:
            ret = fc[self.parsePosition:nulPosition]
        if updateParsePosition is True:
            self.parsePosition = nulPosition + 1
        return ret

    def isValidNWCFile(self, updateParsePosition = True):
        storedPP = self.parsePosition
        self.parsePosition = 0
        header1 = self.readToNUL()
        if header1 != '[NoteWorthy ArtWare]':
            return False
        junk = self.readToNUL()
        junk = self.readToNUL()
        header2 = self.readToNUL()
        if header2 != '[NoteWorthy Composer]':
            return False
        if updateParsePosition is False and storedPP != 0:
            self.parsePosition = storedPP
        return True


    # thanks to Juria90 for figuring these out! and so much more!
    versionFromHex = {0x0114: 120,
                      0x011E: 130,
                      0x0132: 150,
                      0x0137: 155,
                      0x0146: 170,
                      0x014B: 175,
                      0x0200: 200,
                      0x0201: 201,
                      }

    def fileVersion(self, updateParsePosition = True):
        storedPP = self.parsePosition
        self.parsePosition = 45
        fileVersionRaw = self.readLEShort(updateParsePosition)
        if updateParsePosition is False:
            self.parsePosition = storedPP
        if fileVersionRaw in self.versionFromHex:
            self.version = self.versionFromHex[fileVersionRaw]
        else:
            print "No Version Found! Most likely a newer version.  Using 2.01"
            self.version = 201 # most likely a newer version
        
        return self.version

    def skipBytes(self, numBytes = 1):
        self.parsePosition += numBytes
        
    def advanceToNotNUL(self, nul = '\x00'):
        pp = self.parsePosition
        fc = self.fileContents
        while fc[pp] == nul:
            pp += 1
        self.parsePosition = pp

    def parse(self):
        if self.fileContents[0:6] == '[NWZ]\x00':
            import zlib
            fcNew = zlib.decompress(self.fileContents[6:])
            self.fileContents = fcNew

        self.parsePosition = 0
        self.parseHeader()
        self.staves = []
        for i in range(self.numberOfStaves):
            thisStaff = NWCStaff(parent = self)
            thisStaff.parse()
            self.staves.append(thisStaff)


    def parseHeader(self):
        self.isValidNWCFile()
        #print self.parsePosition
        self.fileVersion()
        #print self.version
        #print self.parsePosition
        self.skipBytes(4) # skipping registered vs. unregistered
        #print self.parsePosition
        self.user = self.readToNUL()
        #print self.user
        unused_unknown = self.readToNUL()
        #print unused_unknown
        self.skipBytes(10)
        self.title = self.readToNUL()
        #print self.title
        self.author = self.readToNUL()
        #print self.author
        if self.version >= 200:
            self.lyricist = self.readToNUL()
            #print self.lyricist
        else:
            self.lyricist = None
        self.copyright1 = self.readToNUL()
        self.copyright2 = self.readToNUL()
        self.comment = self.readToNUL()
        #print self.comment
        self.extendLastSystem = self.readToNUL()
        self.increaseNoteSpacing = self.readToNUL()
        unused = self.readToNUL()
        self.measureNumbers = self.readToNUL()
        unused = self.readToNUL()
        self.measureStart = self.readLEShort()
        if self.version >= 130:
            self.margins = self.readToNUL()
            # split by space
        else:
            self.margins = "0.0 0.0 0.0 0.0"
        self.mirrorMargins = self.readToNUL()
        unused = self.readToNUL()
        if self.version >= 130:
            self.groupVisibility = self.readToNUL()
            self.allowLayering = self.readToNUL()
        else:
            self.groupVisibility = True
            self.allowLayering = True
        if self.version >= 200:
            self.notationTypeface = self.readToNUL()
        else:
            self.notationTypeface = "Maestro"
        self.staffHeight = self.readLEShort()
        if self.version > 170:
            fontCount = 12
        elif self.version > 130:
            fontCount = 10  # some 170 have 12 font info.  See Juria90's code for workaround.
        else:
            fontCount = 0
        self.advanceToNotNUL() # shouldnt be needed, but some parse errors
        self.skipBytes(2)
        self.fonts = []
        for i in range(fontCount):
            fontDict = {}
            fontDict['name'] = self.readToNUL()
            fontDict['style'] = self.byteToInt()
            fontDict['size'] = self.byteToInt()
            unused = self.byteToInt()
            fontDict['charset'] = self.byteToInt()
            if fontDict['name'] == '':
                fontDict['name'] = 'Times New Roman'
            if fontDict['style'] == 0:
                fontDict['style'] = 0 # regular; 1 = bold; 2 = italic; 3 = bold italic???
            if fontDict['size'] == 0:
                fontDict['size'] = 12
            self.fonts.append(fontDict)
            # ansi charset is default; but we don't use
        #print self.fonts
        self.titlePageInfo = self.byteToInt()
        self.staffLables = self.byteToInt() # index of [None, First Systems, Top Systems, All Systems]
        self.pageNumberStart = self.readLEShort()
        if self.version >= 200:
            self.skipBytes(1)
        self.numberOfStaves = self.byteToInt()
        #print "StaffCount", self.numberOfStaves
        self.skipBytes(1)
            
    def dumpToNWCText(self):
        dumpObjects = []
        for s in self.staves:
            staffDumpObjects = s.dump()
            for sdo in staffDumpObjects:
                dumpObjects.append(sdo)

        return dumpObjects

    def toStream(self):
        from music21.noteworthy import translate
        nwt = translate.NoteworthyTranslator()
        s = nwt.parseList(self.dumpToNWCText())
        return s
            
class NWCStaff(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.lyrics = []
        self.objects = []
    
    def parse(self):
        self.parseHeader()
        self.parseLyrics()
        self.parseObjects()
        
    def dump(self):
        dumpObjects = []
        dumpObjects.append("|AddStaff|")    
        for o in self.objects:
            dm = o.dumpMethod
            d = dm(o)
            if d != "":
                dumpObjects.append(d)
        return dumpObjects
    
    def parseHeader(self):
        p = self.parent
        #p = NWCConverter()
        self.name = p.readToNUL()
        #print "staff name:", self.name
        if p.version >= 200:
            self.label = p.readToNUL()
            #print "label:", self.label
            self.instrumentName = p.readToNUL()
            #print "instrument name:", self.instrumentName
        else:
            self.label = None
            self.instrumentName = None
        self.group = p.readToNUL()
        #print "group: ", self.group
        
        
        # assuming version 200 or greater for now...
#        self.endingBar = p.byteToInt()
#        self.muted = p.byteToInt()
#        junk = p.byteToInt()
#        self.channel = p.byteToInt()
#        junk = p.byteToInt()
#        self.playbackDevice = p.byteToInt()
#        junk = p.byteToInt()
#        self.patchBank = p.byteToInt()
#        junk = p.byteToInt()
#        self.patchName = p.byteToInt()
#        junk = p.byteToInt()
#        self.defaultVelocity = p.byteToInt()
#        self.style = p.readLEShort()
#        self.verticalSizeUpper = p.readLEShort()
#        self.verticalSizeLower = p.readLEShort()
        p.skipBytes(27)
        self.lines = p.byteToInt()
        #print "lines:", self.lines
        #print "position:", p.parsePosition
        self.layerWithNextStaff = p.readLEShort()
        self.transposition = p.readLEShort()
        self.partVolume = p.readLEShort()
        self.stereoPan = p.readLEShort()
        self.color = p.byteToInt()
        self.alignSyllable = p.readLEShort()
        self.numberOfLyrics = p.readLEShort()
        
        if self.numberOfLyrics > 0:
            self.lyricAlignment = p.readLEShort()
            self.staffOffset = p.readLEShort()
        else:
            self.lyricAlignment = 0
            self.staffOffset = 0
        #print "Number of lyrics:", self.numberOfLyrics
    
    def parseLyrics(self):
        p = self.parent
        lyrics = []
        for i in range(self.numberOfLyrics):
            syllables = []
            lyricBlockSize = p.readLEShort()
            #print "lyric block size: ", lyricBlockSize
            if lyricBlockSize > 0:
                unused_lyricSize = p.readLEShort()
                parsePositionStart = p.parsePosition
 
                #print "lyric Size: ", lyricSize
                junk = p.readLEShort()
                continueIt = True
                while continueIt is True:
                    syllable = p.readToNUL()
                    #print "syllable: ", syllable
                    if syllable == "":
                        continueIt = False
                    else:
                        syllables.append(syllable)
                p.parsePosition = parsePositionStart + lyricBlockSize
                lyrics.append(syllables)
            #print syllables
        #print lyrics
        if self.numberOfLyrics > 0:
            junk = p.readLEShort()
        junk_2 = p.readLEShort()
        #print p.parsePosition
        self.lyrics = lyrics
        return lyrics
    
    def parseObjects(self):
        p = self.parent
        objects = []
        self.numberOfObjects = p.readLEShort()
        if p.version > 150:
            self.numberOfObjects -= 2
        
        #print "Number of objects: ", self.numberOfObjects
        for i in range(self.numberOfObjects):
            thisObject = NWCObject(staffParent = self, parserParent = p)
            thisObject.parse()
            objects.append(thisObject)
        self.objects = objects
        #print objects
        return objects

class NWCObject(object):
    def __init__(self, staffParent = None, parserParent = None):
        self.staffParent = staffParent
        self.parserParent = parserParent
        
        def genericDumpMethod(self):
            return ""
    
        self.dumpMethod = genericDumpMethod
        
    def parse(self):
        '''
        determine what type of object I am, and set things accordingly
        '''
        p = self.parserParent
        objectType = p.readLEShort()
        if objectType > len(self.objMethods):
            print "CAN'T HANDLE objectType %d" % objectType
            return
        if p.version >= 170:
            self.visible = p.byteToInt()
        else:
            self.visible = 0
        
        objectMethod = self.objMethods[objectType]
        objectMethod(self)
        
        
    def clef(self):
        p = self.parserParent
        #print "Clef at : ", p.parsePosition
        self.type = 'Clef'
        self.clefType = p.readLEShort()
        self.octaveShift = p.readLEShort()
        
        clefNames = ['Treble', 'Bass', 'Alto', 'Tenor']
        if self.clefType < len(clefNames):
            self.clefName = clefNames[self.clefType]
        octaveShiftNames = [None, 'Octave Up', 'Octave Down']
        if self.octaveShift < len(octaveShiftNames):
            self.octaveShiftName = octaveShiftNames[self.octaveShift]
        
        #print "now at: ", p.parsePosition
        def dump(self):
            build = "|Clef|"
            if self.clefName:
                build += "Type:" + self.clefName + "|"
            if self.octaveShiftName:
                build += "OctaveShift:" + self.octaveShiftName + "|"
            return build
        
        self.dumpMethod = dump
    
    def keySig(self):
        p = self.parserParent
        self.type = 'KeySig'
        self.flats = p.byteToInt()
        p.skipBytes(1) #?
        self.sharps = p.byteToInt()
        p.skipBytes(7)

        ## too complex...
        #for letter in ['A','B','C','D','E','F','G']:
        #    bitshift = ord(letter) - ord('A')
        #    letterMask = 1 << bitshift
        
        flatMask = {0x00: '',
                    0x02: 'Bb', 
                    0x12: "Bb,Eb", 
                    0x13: "Bb,Eb,Ab",
                    0x1B: "Bb,Eb,Ab,Db", 
                    0x5B: "Bb,Eb,Ab,Db,Gb", 
                    0x5F: "Bb,Eb,Ab,Db,Gb,Cb",
                    0x7F: "Bb,Eb,Ab,Db,Gb,Cb,Fb"}
        sharpMask = {0x00: '',
                     0x20: 'F#', 
                     0x24: 'F#,C#', 
                     0x64: 'F#,C#,G#', 
                     0x6C: 'F#,C#,G#,D#', 
                     0x6D: 'F#,C#,G#,D#,A#', 
                     0x7D: 'F#,C#,G#,D#,A#,E#', 
                     0x7F: 'F#,C#,G#,D#,A#,E#,B#'}

        if self.flats > 0 and self.flats in flatMask:    
            self.keyString = flatMask[self.flats]
        elif self.sharps > 0 and self.sharps in sharpMask:
            self.keyString = sharpMask[self.sharps]
        else:
            self.keyString = "" # no unusual keysigs
        
        def dump(self):
            build = "|Key|Signature:" + self.keyString
            return build
        
        self.dumpMethod = dump
        
        
    def barline(self):
        p = self.parserParent
        self.type = 'Barline'
        self.style = p.byteToInt()
        self.localRepeatCount = p.byteToInt()
        
        def dump(self):
            build = "|Bar|"
            return build
    
        self.dumpMethod = dump
    
    def ending(self):
        p = self.parserParent
        self.type = 'Ending'
        self.style = p.byteToInt()
        p.skipBytes(1)
    
    def instrument(self):
        p = self.parserParent
        self.type = 'Instrument'
        p.skipBytes(8)
        self.name = p.readToNUL()
        p.skipBytes(1)
        p.skipBytes(8) # velocity
        
    
    def timeSig(self):
        p = self.parserParent
        self.type = 'TimeSignature'
        self.numerator = p.readLEShort()
        self.bits = p.readLEShort()
        self.denominator = 1 << self.bits
        self.style = p.readLEShort()
    
        def dump(self):
            build = '|TimeSig|Signature:%d/%d' % (self.numerator, self.denominator)
            return build
        
        self.dumpMethod = dump
            
    def tempo(self):
        p = self.parserParent
        self.type = 'Tempo'
        self.pos = p.byteToInt() 
        self.placement = p.byteToInt()
        self.value = p.readLEShort()
        self.base = p.byteToInt()
        if p.version < 170:
            junk = p.readLEShort()
        self.text = p.readToNUL()
    
    def dynamic(self):
        p = self.parserParent
        self.type = 'Dynamic'
        if p.version < 170:
            print "ughh. not yet"
        else:
            self.pos = p.byteToInt()
            self.placement = p.byteToInt()
            self.style = p.byteToInt()
            self.velocity = p.readLEShort()
            self.volume = p.readLEShort()
    
    def setDurationForObject(self):
        '''
        get duration string for note or rest
        '''
        if self.type == 'Note':
            self.dotAttribute = self.attribute1[0]
        else:
            self.dotAttribute = self.data2[3]

        if (ord(self.dotAttribute) & 0x01) > 0:
            self.dots = 2
        elif (ord(self.dotAttribute) & 0x04) > 0:
            self.dots = 1
        else:
            self.dots = 0

        durationValues = ['Whole','Half','4th','8th','16th','32nd','64th']
        durStr = durationValues[self.duration]
        if self.dots == 1:
            durStr += ',Dotted'
        elif self.dots == 2:
            durStr += ',DblDotted'
                
        
        return durStr
    
    def note(self):
        p = self.parserParent
        self.type = 'Note'
        #print "Note at parse position: ", p.parsePosition
        if p.version < 170:
            print "ughh. not yet"
        else:
            self.duration = p.byteToInt()
            self.data2 = p.readBytes(3) #??
            self.attribute1 = p.readBytes(2)
            #print hex(ord(self.attribute1[0]))
            self.pos = p.byteToSignedInt()
            self.pos = -1 * self.pos
            self.attribute2 = p.byteToInt()
            if (p.version <= 170):
                self.data3 = p.readBytes(2)
            else:
                self.data3 = None
            if (p.version >= 200):
                if ((self.attribute2 & 0x40) != 0):
                    #print "have stemLength info!"
                    self.stemLength = p.byteToInt()
                else:
                    #print "attribute 2:", hex(self.attribute2)
                    self.stemLength = 7
            else:
                self.stemLength = 7
            #if (p.version >= 200 and ((self.attribute2 & 0x40) != 0)):
            #self.stemLength = p.byteToInt()
            #else:
            #    self.stemLength = 7
        ## uh oh!!!
        #p.skipBytes(2)
        #print "Now at: ", p.parsePosition
        #print "Duration: ", self.duration
        #print "Data2: ", 
        #for i in self.data2:
        #    print hex(ord(i)),
        #print "..."

        self.durationStr = self.setDurationForObject()


        alterationTexts = ["#", "b", 'n', '##', 'bb', '']
        alterationIndex = self.attribute2 & 0x07
        if alterationIndex < len(alterationTexts):
            self.alterationStr = alterationTexts[alterationIndex]
        else:
            self.alterationStr = ""

        self.tieInfo = ""
        if (ord(self.attribute1[0]) & 0x10) > 0:
            self.tieInfo = "^"
        

        def dump(self):
            build = "|Note|Dur:" + self.durationStr + "|"
            build += "Pos:" + self.alterationStr + str(self.pos) + self.tieInfo + "|"
            return build
        
        self.dumpMethod = dump
            
    def rest(self):
        p = self.parserParent
        self.type = 'Rest'
        if p.version <= 150:
            print "igg..."
        else:
            self.duration = p.byteToInt()
            self.data2 = p.readBytes(5)
            self.offset = p.readLEShort()        
        
        self.durationStr = self.setDurationForObject()
            
        def dump(self):
            build = "|Rest|Dur:" + self.durationStr + "|"
            return build
    
        self.dumpMethod = dump
    
    def noteChordMember(self):
        p = self.parserParent
        self.type = 'NoteChordMember'
        if p.version <= 170:
            self.data1 = p.readBytes(12)
        else:
            self.data1 = p.readBytes(8)
        if (p.version >= 200):
            if ((self.data1[7] & 0x40) != 0):
                print "have stemLength info!"
                self.stemLength = p.byteToInt()
            else:
                    #print "attribute 2:", hex(self.attribute2)
                self.stemLength = 7
        else:
            self.stemLength = 7

    def pedal(self):
        p = self.parserParent
        self.type = 'Pedal'
        if (p.version < 170):
            print "uggh"
        else:
            self.pos = p.byteToInt()
            self.placement = p.byteToInt()
            self.style = p.byteToInt()
            
    
    def flowDir(self):
        p = self.parserParent
        self.type = 'FlowDir'
        if (p.version >= 170):
            self.pos = p.byteToInt()
            self.placement = p.byteToInt()
        else:
            self.pos = -8 # so needs to be signed int?
            self.placement = 0x01
        
        self.style = p.readLEShort()
    
    
    def mpc(self):
        '''
        what is this?
        '''
        p = self.parserParent
        self.type = 'MPC'
        self.pos = p.byteToInt()
        self.placement = p.byteToInt()
        if p.version > 155:
            self.data1 = p.readBytes(31)
        else:
            self.data1 = p.readBytes(32)
    
    def tempoVariation(self):
        p = self.parserParent
        self.type = 'TempoVariation'
        if (p.version >= 170):
            self.pos = p.byteToInt()
            self.placement = p.byteToInt()
            self.style = p.byteToInt()
            self.delay = p.byteToInt()
        else:
            self.style = p.byteToInt()
            self.style = self.style & 0x0F
            self.pos = p.byteToInt()
            self.placement = p.byteToInt()
            self.delay = p.byteToInt()
    
    
    def dynamicVariation(self):
        p = self.parserParent
        self.type = 'DynamicVariation'
        self.pos = p.byteToInt()
        if (p.version >= 170):
            self.placement = p.byteToInt()
        else:
            self.placement = 0
        self.style = p.byteToInt()

    def performance(self):
        p = self.parserParent
        self.type = 'Performance'
        self.pos = p.byteToInt()
        if (p.version >= 170):
            self.placement = p.byteToInt()
        else:
            self.placement = 0
        self.style = p.byteToInt()

    def text(self):
        p = self.parserParent
        self.type = 'Text'
        self.pos = p.byteToInt()
        self.data = p.byteToInt()
        self.font = p.byteToInt()
        self.text = p.readToNUL()
        #print "Text: ", self.text
    
    def restChordMember(self):
        p = self.parserParent
        self.type = 'RestChordMember'
        self.count = p.readLEShort()

    objMethods = [clef, keySig, barline, ending, instrument, timeSig, tempo,
                  dynamic, note, rest, noteChordMember, pedal, flowDir, mpc,
                  tempoVariation, dynamicVariation, performance, text, restChordMember]

if __name__ == '__main__':
    pass
    #fp = '/Users/cuthbert/Desktop/395.nwc'
    #fp = 'http://www.cpdl.org/brianrussell/358.nwc'
    #from music21 import converter
    #s = converter.parse(fp)
    #s.show()
    
    # nwc = NWCConverter()
    #s = nwc.parseFile(fp)
    #s.show()
    #print nwc.dumpToNWCText()
    #print nwc.isValidNWCFile()
    #print nwc.fileVersion()
        