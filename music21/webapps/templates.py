# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         webapps.commands.py
# Purpose:      music21 functions for implementing web interfaces
#
# Authors:      Lars Johnson
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------    
def musicxmlText(sc):
    musicxml = sc.musicxml
    return (musicxml, 'text/plain')

def musicxmlFile(sc):
    musicxml = sc.musicxml
    return (musicxml,'application/vnd.recordare.musicxml+xml')
    #('Content-disposition','attachment; filename='+filename)
def noteflightEmbed(sc, title):
    musicxml = sc.musicxml
    musicxml = musicxml.replace('\n','')
    musicxml = musicxml.replace('\'','\\\'')
    htmlData = """
<html>
<head>
<title>Music21 URL App Response</title>
<script language="javascript" src="http://ciconia.mit.edu/music21/webapps/client/javascript/music21.js"></script>
<script>
    // Event handling function
    function noteflightEventHandler(e)
    {
        if(e.type == 'scoreDataLoaded') {
            m21.noteflight.sendMusicXMLToNoteflightEmbed('nfscore','"""
    htmlData += musicxml
    htmlData +="""')
        }
    }
</script>
<script language="javascript">
m21 = new Music21interface();

function setup() {
    m21.noteflight.createNoteflightEmbed('noteflightembed','nfscore','fc79df30896da6aa03f90ff771015913ca6880be',800,450,1.0);
}
</script>

</head>
<body onload="setup()">

<h1>"""
    htmlData += title
    htmlData +="""
</p> 
<div id="noteflightembed">
</div>


</body>
</html>
"""
    return (htmlData, 'text/html')