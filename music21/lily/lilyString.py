TRANSPARENCY_START = r'''
 \override Rest #'transparent  = ##t
 \override Dots #'transparent  = ##t
 '''
TRANSPARENCY_STOP = r'''
 \revert Rest #'transparent
 \revert Dots #'transparent
 '''

import os
import sys
import tempfile
import re
import time
import threading

import music21

import unittest, doctest

try: 
    ### required imports for PIL -- otherwise it doesnot like it, for some reason
    from PIL import Image
    from PIL import ImageOps    
    noPIL = False
except ImportError:
    noPIL = True


_MOD = 'lilyString.py' # module name for debugging reference


class LilyString(object):
    LILYEXEC = 'lilypond'
    if sys.platform == "darwin":
        LILYEXEC = '/Applications/Lilypond.app/Contents/Resources/bin/lilypond'
    format   = 'pdf'
    version  = '2.11' # this should be obtained from user and/or user's system
    backend  = 'ps'
    backendString = '--backend='
    midiWrapped = False
    
    if version.count("2.11") > 0:  # new version of backend as of 2.11
        backendString = '-dbackend='
    elif sys.platform == "win32": 
        backendString = '-dbackend='
    elif sys.platform == "linux2":
        backendString = '-dbackend='
        
    if version.startswith("2.12"):
        # note: version 2.12 of lilypond needs a -formats flag, not --backend
        backendString = '--formats='
        

    snippet  = r'''
\paper {
#(define dump-extents #t)

indent = 0\mm
force-assignment = #""
line-width = #(- line-width (* mm  3.000000))
oddFooterMarkup=##f
oddHeaderMarkup=##f
bookTitleMarkup=##f

}

'''

    noHeader = r'''
scoreTitleMarkup=##f
'''
    
    layout = r'''
\layout {

}
'''

    midi = r'''
\midi {

}
'''
    
    fictaDef = \
    """ficta = #(define-music-function (parser location) () #{ \\once \\set suggestAccidentals = ##t #})
    color = #(define-music-function (parser location color) (string?) #{ 
    \\once \\override NoteHead #'color = #(x11-color $color) 
    \\once \\override Stem #'color = #(x11-color $color)
    \\once \\override Rest #'color = #(x11-color $color)
    \\once \\override Beam #'color = #(x11-color $color)
     #})
     
     """

    headerInformation = "\\version \"" + version + "\"" + layout + fictaDef
    savePNG = False ## PNGs are deleted immediately.
    
    def __init__(self, value = ""):
        self.value = u""
        if hasattr(value, "value"):
            self.value = value.value
        else:
            self.value = unicode(value)
    
    def __add__(self, addStr):
        if hasattr(addStr, "value"):
            self.value = self.value + addStr.value
        else:
            self.value = self.value + addStr
        return self
    
    def __mul__(self, value):
        self.value = self.value * value
        return self
        
    def __del__(self):
        if hasattr(self, "tempName") and self.tempName:
            try:
                os.remove(self.tempName)
            except:
                pass
    
    def __str__(self):
        return self.value
    
    def __unicode__(self):
        return self.value
    
    def __repr__(self):
        return self.value
    
    def wrapForMidi(self):
        self.value = "\\score { { " + self.value + "} \\layout { } \\midi { \\context { \\Score tempoWholesPerMinute = #(ly:make-moment 100 2) } }  }"
        self.midiWrapped = True
    
    def _getWrappedValue(self):
        '''
        returns a value that is wrapped with { } if it doesn't contain a score element
        so that it can run through lilypond
        '''
        if self.midiWrapped is True:
            return self.value
        elif r'\score' in self.value:
            return self.value
        elif self.value.lstrip().startswith('{'):
            return self.value
        else:
            return unicode('{' + self.value + '}')
    
    wrappedValue = property(_getWrappedValue)
    
    def writeTemp(self):
        (fd, tempName) = tempfile.mkstemp()
        self.tempName = tempName
        try:
            ntf = open(tempName, "w")
            print>>ntf, self.snippet
            print>>ntf, self.headerInformation
            print>>ntf, self.wrappedValue.encode('utf-8')
            ntf.flush()
            ntf.close()
        except:
            raise
        return tempName
    
    def runThroughLily(self):
        filename = self.tempName
        format   = self.format
        backend  = self.backend
        lilyCommand = self.LILYEXEC + " --" + format + " " + \
                    self.backendString + backend + " -o " + filename + " " + filename
        
        try:
            os.system(lilyCommand)    
        except:
            raise
        
        try:
            os.remove(filename + ".eps")
        except:
            pass
        fileform = filename + '.' + format
        if not os.path.exists(fileform):
            fileend = os.path.basename(fileform)
            if not os.path.exists(fileend):
                raise Exception("I can't find " + fileend)
            else:
                fileform = fileend
        return (fileform)

    def createPDF(self):
        self.writeTemp()
        lilyFile = self.runThroughLily()
        return lilyFile

    def showPDF(self):
        lF = self.createPDF()
        if not os.path.exists(lF):
            raise Exception("Something went wrong with PDF Creation")
        else:
            if os.name == "nt":
                command = "start /wait %s && del /f %s" % (lF, lF)
            elif sys.platform == "darwin":
                command = "open %s" % lF
            else:
                command = ""
            os.system(command)
        
    def showPNG(self):
        '''Take the LilyString, run it through LilyPond, and then show it as a PNG file.
        On Windows, the PNG file will not be deleted, so you  will need to clean out
        TEMP every once in a while
        '''        
        self.format = 'png'
        self.backend = 'eps'
        self.writeTemp()
        lilyFile = self.runThroughLily()
        if noPIL is False:
            try:
                lilyImage = Image.open(lilyFile)
                lilyImage2 = ImageOps.expand(lilyImage, 10, "white")
                if os.name == "nt":
                    format = "PNG"
                elif sys.platform == "darwin":
                    format = "JPEG"
                else:
                    format = None
                
                if lilyImage2.mode == "I;16":
                # @PIL88 @PIL101
                # "I;16" isn't an 'official' mode, but we still want to
                # provide a simple way to show 16-bit images.
                    base = "L"
                else:
                    base = Image.getmodebase(lilyImage2.mode)
                if base != lilyImage2.mode and lilyImage2.mode != "1":
                    file = lilyImage2.convert(base)._dump(format=format)
                else:
                    file = lilyImage2._dump(format=format)    
                self.showImageDirect(file)
            except:
                raise
                self.showImageDirect(lilyFile)
        else:
            self.showImageDirect(lilyFile)
        
        return lilyFile
        
    def showPNGandPlayMIDI(self):
        if self.midiWrapped is False:
            self.wrapForMidi()
        lilyFile = self.showPNG()
        midiFile = re.sub("\.png",".midi",lilyFile)
        self.playMIDIfile(midiFile)

    def checkForMidiAndAdd(self):
        if self.checkForMidi():
            pass
        else:
            self.addMidi()
            
    def addMidi(self):
        '''override this in subclasses, such as LilyScore'''
        a = self.midi
        self.value += self.midi
    
    def checkForMidi(self):
        if self.value.count('\\midi') > 1:
            return True
        else:
            return False
        
    def playMIDIfile(self, file):
        if not os.path.exists(file):
            f2 = re.sub("\.midi",".mid", file)
            if os.path.exists(f2):
                file = f2
            elif os.path.exists("/tmp/" + file):
                file = "/tmp/" + file
            else:
                raise Exception("Cannot play midi file %s: file does not exist", file)
        if os.name == "nt":
            command = "start %s" % (file)
        else:
            command = "open %s" % (file)
        self.midiFilename = file
        os.system(command)
        
    def quickHeader(self, string):
        '''Returns a quick and dirty lilyPond header for the stream
        '''
        headOut = " \\header { \n piece = \"" 
        headOut += string
        headOut += " \" \n}\n";
        return headOut

    def showImageDirect(self, imageFile, title = None, command = None):
        '''borrowed from and modified from the excellent PIL image library, but needed
        some changes to the NT handling'''
        
        if os.name == "nt":
            format = "PNG"
        elif sys.platform == "darwin":
            format = "JPEG"
            if not command:
                command = "open -a /Applications/Preview.app"
        else:
            format = None
            if not command:
                command = "xv"
                if title:
                    command = command + " -name \"%s\"" % title
        
        if os.name == "nt":
            command = "start %s" % (imageFile)
            os.system(command)
            if self.savePNG is False:
                def quickDel():
                    command = "del /f %s" % (imageFile)
                    os.system(command)
                t = threading.Timer(6.0, quickDel)
                t.start()  ## give 6 seconds for viewer to open before deleting  
        elif sys.platform == "darwin":
            # on darwin open returns immediately resulting in the temp
            # file removal while app is opening
            command = "(%s %s; sleep 20; rm -f %s)&" % (command, imageFile, imageFile)
            os.system(command)
        else:
            command = "(%s %s; rm -f %s)&" % (command, imageFile, imageFile)
            os.system(command)

class Test(unittest.TestCase):
    pass

class TestExternal(unittest.TestCase):
    
    def testPNG(self):
        a = LilyString("c'4")
#        a.showPNG()    

    def testPNGandPlayMIDI(self):
        a = LilyString("c'4")
#        a.showPNGandPlayMIDI()
        
    def testAdd(self):
        a = LilyString("c'4 ")
        a += "d'4 "
        b = LilyString("b4 ") + a
        self.assertEqual(b.value, u"b4 c'4 d'4 ")
        b.showPNG()    
        

if __name__ == "__main__":
    music21.mainTest(Test, TestExternal)