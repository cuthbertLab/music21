# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         alpha.webapps.commands.py
# Purpose:      music21 functions for implementing web interfaces
#
# Authors:      Lars Johnson
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------  
'''
Webapps is a module designed for using music21 with a webserver.

This file includes templates detailing different output formats available for the CommandProcessor

Each template returns a tuple of the form (data, contentType).

'''
import unittest

#from music21 import corpus
from string import Template


outputShortcuts = {
    "show(musicxml)"    : "templates.musicxmlText",
    "musicxmlDisplay"   : "templates.musicxmlText",
    
    "musicxml"          : "templates.musicxmlFile",
    "write(musicxml)"   : "templates.musicxmlFile",
    "musicxmlDownload"  : "templates.musicxmlFile",
    "musicxmlFile"      : "templates.musicxmlFile",
    
    "show(vexflow)"     : "templates.vexflow",
    "vexflow"           : "templates.vexflow",
    
    "show(braille)"     : "templates.braille",
    "braille"           : "templates.braille",
    
    "show(noteflight)"  : "templates.noteflightEmbed",
    "noteflight"        : "templates.noteflightEmbed",
}

# These are output templates which take a single parameter, an output stream
streamOutputs = ["musicxmlText", "musicxmlFile", "vexflow", "braille", "noteflightEmbed"]
 
def musicxmlText(outputStream):
    '''
    Takes in a stream outputStream and returns its musicxml with 
    content-type 'text/plain' for displaying in a browser
    
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = alpha.webapps.templates.musicxmlText(sc)
    >>> contentType
    'text/plain; charset=utf-8'
    >>> b'score-partwise' in output
    True
    '''
    from music21.musicxml import m21ToXml
    musicxmlBytes = m21ToXml.GeneralObjectExporter().parse(outputStream)
    return (musicxmlBytes, 'text/plain; charset=utf-8')   

def musicxmlFile(outputStream):
    '''
    Takes in a stream outputStream and returns its musicxml with 
    content-type 'application/vnd.recordare.musicxml+xml' for downloading
    
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = alpha.webapps.templates.musicxmlFile(sc)
    >>> contentType
    'application/vnd.recordare.musicxml+xml; charset=utf-8'
    >>> b'score-partwise' in output
    True

    '''
    from music21.musicxml import m21ToXml
    musicxmlBytes = m21ToXml.GeneralObjectExporter().parse(outputStream)
    return (musicxmlBytes, 'application/vnd.recordare.musicxml+xml; charset=utf-8')
    
def vexflow(outputStream):
    '''
    Takes in a stream outputStream, generates an HTML representation of it using vexflow, and
    outputs it with content-type text/html for displying in a browser.
    
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = alpha.webapps.templates.vexflow(sc)
    >>> contentType
    'text/html; charset=utf-8'
    '''
    from music21 import vexflow as vf
    outputHTML = vf.fromObject(outputStream, mode='html')
    return (outputHTML.encode('utf-8'), 'text/html; charset=utf-8')   
 
def braille(outputStream):
    '''
    Takes in a stream outputStream, generates the braille representation of it, and returns
    the unicode output with content-type text/html for display in a browser
  
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = alpha.webapps.templates.braille(sc)
    >>> contentType
    'text/html; charset=utf-8'
    '''
#    from music21 import braille
    from music21.braille import translate as btranslate
    
    brailleOutput = (u"<html><body><pre>" + btranslate.objectToBraille(outputStream) + 
                     u"</pre></body></html>")
    return (brailleOutput.encode('utf-8'), 'text/html; charset=utf-8')   

def noteflightEmbed(outputStream):
    '''
    Takes in a stream outputStream, and a string title. Returns the HTML for a page 
    containing a noteflight
    flash embed of the stream and the title title
    
    TODO: Change javascript and noteflight embed to relate to be server-specific
  
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = alpha.webapps.templates.noteflightEmbed(sc)
    >>> contentType
    'text/html; charset=utf-8'
    '''
    from music21.musicxml import m21ToXml
    musicxmlBytes = m21ToXml.GeneralObjectExporter().parse(outputStream)   
    musicxmlString = musicxmlBytes.decode('utf-8') 
    musicxmlString = musicxmlString.replace('\n','')
    musicxmlString = musicxmlString.replace('\'','\\\'')
    htmlStr = """
<html>
<head>
<title>Music21 URL App Response</title>
<script language="javascript" 
    src="http://web.mit.edu/music21/webapps/client/javascript/music21.js"></script>
<script>
    // Event handling function
    function noteflightEventHandler(e)
    {
        if(e.type == 'scoreDataLoaded') {
            m21.noteflight.sendMusicXMLToNoteflightEmbed('nfscore', '$musicxml')
        }
    }
</script>
<script language="javascript">
m21 = new Music21interface();

function setup() {
    m21.noteflight.createNoteflightEmbed('noteflightembed', 'nfscore', 
        'fc79df30896da6aa03f90ff771015913ca6880be',800,450,1.0);
}
</script>

</head>
<body onload="setup()">

<h1>Music21 Output</h1> 
<div id="noteflightembed">
</div>


</body>
</html>
    """
    htmlData = Template(htmlStr)
    
    htmlData = htmlData.safe_substitute(musicxml=musicxmlString)
    return (htmlData.encode('utf-8'), 'text/html; charset=utf-8')   

#-------------------------------------------------------------------------------
# Tests 
#-------------------------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
