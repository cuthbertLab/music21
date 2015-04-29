# -*- coding: utf-8 -*-
'''
An interface for music21 using mod_wsgi

To use, first install mod_wsgi and include it in the HTTPD.conf file.

Add this file to the server, ideally not in the document root, 
on mac this could be /Library/WebServer/wsgi-scripts/music21wsgiapp.py

Then edit the HTTPD.conf file to redirect any requests to WEBSERVER:/music21interface to call this file:
Note: unlike with mod_python, the end of the URL does not determine which function is called,
WSGIScriptAlias always calls application.

WSGIScriptAlias /music21interface /Library/WebServer/wsgi-scripts/music21wsgiapp.py

Further down the conf file, give the webserver access to this directory:

<Directory "/Library/WebServer/wsgi-scripts">
    Order allow,deny
    Allow from all
</Directory>

The mod_wsgi handler will call the application function below with the request
content in the environ variable.

'''

#from music21 import webapps
from music21 import corpus
#from music21 import common

from os import path

def music21ModWSGICorpusURLApplication(environ, start_response):
    '''
    Application function in proper format for a MOD-WSGI Application:
    A server-mounted app that uses portions of the URL to parse and return musicxml of manipulated sections of corpus files. 
    Results can be returned either as a noteflight embed in the browser or downloaded as an xml file.
    
    '''
    status = '200 OK'

    pathInfo = environ['PATH_INFO'] # Contents of path after mount point of wsgi app but before question mark
    queryString = environ['QUERY_STRING'] # Contents of URL after question mark    
    returnType = queryString
    
    pathParts = pathInfo.split("/")
    
    error = False
    
    resultStr = ""
    
    if len(pathParts) > 1 and pathParts[1] in ['corpusParse','corpusReduce']:
        workList = corpus.getWorkList(pathParts[2])
        if len(workList) >1:
            resultStr = "Multiple choices for query "+pathParts[2]+". Please try one of the following\n"
            for p in workList:
                resultStr += path.splitext(path.basename(p))[0] + "\n"
            response_headers = [('Content-type', 'text/plain'),
            ('Content-Length', str(len(resultStr)))]
    
            start_response(status, response_headers)
        
            return [resultStr]
        elif len(workList) == 0:
            resultStr = "No results for query "+pathParts[2]+"."
            response_headers = [('Content-type', 'text/plain'),
            ('Content-Length', str(len(resultStr)))]
    
            start_response(status, response_headers)
        
            return [resultStr]
        workName = workList[0]
        try:
            sc = corpus.parse(workName).measures(int(pathParts[3]),int(pathParts[4]))
            if pathParts[1] == 'corpusReduce':
                sc = reduction(sc)
            resultStr = sc.musicxml
            title = pathParts[2]+": Measures "+str(pathParts[3])+"-"+str(pathParts[4])
            filename = str(pathParts[2])+".m"+str(pathParts[3])+"-"+str(pathParts[4])+"-reduced.xml"
        except:
            try:
                sc = corpus.parse(pathParts[2]).measures(int(pathParts[3]),int(pathParts[3]))
                if pathParts[1] == 'corpusReduce':
                    sc = reduction(sc)
                resultStr = sc.musicxml
                title = pathParts[2]+": Measure "+str(pathParts[3])
                filename = str(pathParts[2])+".m"+str(pathParts[3])+"-reduced.xml"
            except:
                try:
                    sc = corpus.parse(pathParts[2])
                    if pathParts[1] == 'corpusReduce':
                        sc = reduction(sc)
                    resultStr = sc.musicxml 
                    title = pathParts[2]
                    filename = str(pathParts[2])+"-reduced.xml"
                except Exception as e:
                    resultStr = "Error parsing file "+str(e) + '\n\n'
                    error = True
    else:
        error = True

    if error:
        resultStr += "Try calling a url of the form:"
        resultStr += "\n  /music21/urlinterface/corpusParse/<WORKNAME> to download a musicxml file of the specified corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusParse/<WORKNAME>/<MEASURE_NUM> to download a musicxml file of the specified measure of a corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusParse/<WORKNAME>/<MEASURE_START>/<MEASURE_END> to download a musicxml file of the specified measures of a corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusReduce/<WORKNAME> to download an annotated, chordified reduction of the specified corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusReduce/<WORKNAME>/<MEASURE_NUM> to download an annotated, chordified reduction of the specified measure of a corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusReduce/<WORKNAME>/<MEASURE_START>/<MEASURE_END> to download an annotated, chordified reduction of the specified measures of a corpus file."
        resultStr += "\n\n\nSpecifying Return Format:"
        resultStr += "\n  The return format will default to a Noteflight embed that will load the resulting score."
        resultStr += "\n\n  Add ?xmltext to the end of the url to display the xmltext of the score as plain text"
        resultStr += "\n\n  Add ?xml to the end of the url to download the result as a .xml file"
        error = True
        
        response_headers = [('Content-type', 'text/plain'),
                ('Content-Length', str(len(resultStr)))]
    
        start_response(status, response_headers)
    
        return [resultStr]
    
    else:
        if returnType == "xml":
            response_headers = [('Content-type', 'application/vnd.recordare.musicxml+xml'),
                                ('Content-disposition','attachment; filename='+filename),
                                ('Content-Length', str(len(resultStr))),
                               ]
            start_response(status, response_headers)
            return [resultStr]
        
        elif returnType == "xmltext":
            
            response_headers = [('Content-type', 'text/plain'),
                                ('Content-Length', str(len(resultStr)))]
    
            start_response(status, response_headers)
        
            return [resultStr]
        
        else:
            templateStr = noteflightEmbedTemplate(resultStr,title)
            response_headers = [('Content-type', 'text/html'),
                                ('Content-Length', str(len(templateStr)))]
            start_response(status, response_headers)
        
            return [templateStr]
            
application = music21ModWSGICorpusURLApplication

def noteflightEmbedTemplate(musicxml, title):
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
    return htmlData

def reduction(sc):
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    return reductionStream
