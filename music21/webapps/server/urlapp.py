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

To use the application, send a POST request to WEBSERVER:/music21interface
where the contents of the POST is a JSON string.

See docs for music21.webapps for specifications about the JSON string structure
'''

from music21 import webapps
from music21 import corpus

def music21ModWSGICorpusURLApplication(environ, start_response):
    '''
    Application function in proper format for a MOD-WSGI Application:
    Reads the contents of a post request, and passes the JSON string to
    webapps.processJSONData for further processing. 
    Returns a proper HTML response.
    
    '''
    status = '200 OK'

    pathInfo = environ['PATH_INFO'] # Contents of path after mount point of wsgi app but before question mark
    queryString = environ['QUERY_STRING'] # Contents of URL after question mark    
    documentRoot = environ['DOCUMENT_ROOT'] # Document root of the server
    
    pathParts = pathInfo.split("/")
    
    returnType = "text"
    
    resultStr = str(pathParts)
    
    if len(pathParts) > 1 and pathParts[1] in ['corpusParse','corpusReduce']:
        try:
            sc = corpus.parse(pathParts[2]).measures(int(pathParts[3]),int(pathParts[4]))
            if pathParts[1] == 'corpusReduce':
                sc = reduction(sc)
            resultStr = sc.musicxml
            returnType = "xml"
            filename = str(pathParts[2])+".m"+str(pathParts[3])+"-"+str(pathParts[4])+"-reduced.xml"
        except:
            try:
                sc = corpus.parse(pathParts[2])
                if pathParts[1] == 'corpusReduce':
                    sc = reduction(sc)
                resultStr = sc.musicxml 
                returnType = "xml"
                filename = str(pathParts[2])+"-reduced.xml"
            except Exception as e:
                resultStr = "Error parsing file "+str(e) + ''


    else:
        resultStr = "Try calling a url of the form:"
        resultStr += "\n\n  /music21/urlinterface/corpusParse/<WORKNAME> to download a musicxml file of the specified corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusParse/<WORKNAME>/<MEASURE_START>/<MEASURE_END> to download a musicxml file of the specified measures of a corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusReduce/<WORKNAME> to download an annotated, chordified reduction of the specified corpus file."
        resultStr += "\n\n  /music21/urlinterface/corpusReduce/<WORKNAME>/<MEASURE_START>/<MEASURE_END> to download an annotated, chordified reduction of the specified measures of a corpus file."

    if returnType == "xml":
        response_headers = [('Content-type', 'application/vnd.recordare.musicxml+xml'),('Content-disposition','attachment; filename='+filename),
            ('Content-Length', str(len(resultStr)))]

        start_response(status, response_headers)
    
        return [resultStr]
        
    else:
        response_headers = [('Content-type', 'text/plain'),
                ('Content-Length', str(len(resultStr)))]
    
        start_response(status, response_headers)
    
        return [resultStr]

application = music21ModWSGICorpusURLApplication

def reduction(sc):
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    return reductionStream
