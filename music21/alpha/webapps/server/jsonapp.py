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

Further down the conf file, give the webserver access to this directory::

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

application = webapps.modWSGIJSONApplication #### HHHEEEELLLPPP #  # @UndefinedVariable