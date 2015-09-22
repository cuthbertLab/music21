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
import cgi


def music21ModWSGIUnifiedApplication(environ, start_response):
    '''
    Application function in proper format for a MOD-WSGI Application:
    Used to see what information can be obtained by the server
    
    '''
    status = '200 OK'


    resultStr = ""
    
    
    formFields = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    
    resultStr += "Form Fields:\n"
    for f in formFields: 
        resultStr +=  "   "+str(f)+": "+str(formFields[f]) +"\n"
    
    resultStr += "\nURL Info:\n"
    resultStr += "   PATH_INFO: " + environ['PATH_INFO'] +"\n" # Contents of path after mount point of wsgi app but before question mark
    resultStr += "   QUERY_STRING: " + environ['QUERY_STRING'] +"\n" # Contents of URL after question mark
    
    resultStr += "\nEnviron Info:\n"
    
    
    for k in environ:
        resultStr += "   "+k+": "+ str(environ[k])+"\n"

    response_headers = [('Content-type', 'text/plain'),('Content-Length', str(len(resultStr)))]

    start_response(status, response_headers)

    return [resultStr]
        
application = music21ModWSGIUnifiedApplication
