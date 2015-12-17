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

To use the application, send a POST request to WEBSERVER:/music21interface
where the contents of the POST is a JSON string.

See docs for music21.webapps for specifications about the JSON string structure
'''

#sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/')
#sys.path.insert(0, '/Library/Python/2.7/site-packages/')


#import cgi

#from music21 import webapps
from music21 import note



def music21ModWSGIVisualApplication(environ, start_response):
    '''
    Application function in proper format for a MOD-WSGI Application:
    Used to test returning visual images (plots, lily.png) to the user
    
    '''
    status = '200 OK'

    #pathInfo = environ['PATH_INFO'] # Contents of path after mount point of wsgi app but before question mark
    queryString = environ['QUERY_STRING'] # Contents of URL after question mark    
    
    documentRoot = environ['DOCUMENT_ROOT']
    
        
    #outputStr = ""
        
    noteName = queryString

    n = note.Note(noteName)
    
    tempPath = n.write('png')
    print(tempPath)
    
    writePath = documentRoot + "/music21/OutputFiles/"
    
    
    fin = open(tempPath,'r')
    fout = open(writePath+"out.jpg","w")
    fout.write(fin.read())
    fout.close()
        
    #plt.plot([1,2,3,4])
    #plt.ylabel(workName)

    
    #p = graph.PlotHorizontalBarPitchClassOffset(sc,doneAction=None)
    #p.write('/Library/WebServer/Documents/OutputFiles/graph.jpg')
    #templateStr = tempPath
    
    
    templateStr = imageEmbedTemplate(tempPath,'/music21/OutputFiles/out.jpg')
    
    response_headers = [('Content-type', 'text/html'),('Content-Length', str(len(templateStr)))]

    start_response(status, response_headers)

    return [templateStr]
    
    
application = music21ModWSGIVisualApplication

def reduction(sc):
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    return reductionStream

def imageEmbedTemplate(title, imgSrc):
    htmlData = """
<html>
<head>
<title>Music21 URL App Response</title>

</head>
<body onload="setup()">

<h1>"""
    htmlData += title
    htmlData += "</h1>"
    htmlData += "<img src='"+imgSrc+"'/>"
    htmlData += """
</body>
</html>
"""
    return htmlData
