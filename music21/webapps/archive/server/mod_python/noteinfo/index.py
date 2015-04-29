# -*- coding: utf-8 -*-
# A simple test to get note information
from mod_python import apache

import os
os.environ['HOME'] = '/tmp/'

from music21 import *

# Displays message identifying index
def index(req):
    return """
        <html ><body>
	<h1><b>Note Information:</b></h1>
	<p>To view note information, change the URL to <a href='noteinfo?n=c3'>/noteinfo/noteinfo?n=c3</a>, for example.</p>
        </body></html>
        """

def noteinfo(req, n = 'c4'):    
    req.content_type = 'text/html'
    n1 = note.Note(n)
    
    htmltext = """
        <html ><body>
        <h1>Note Information</h1>"""
    
    htmltext += "<p><b>Full Name:</b> "+n1.fullName+"</p>"            
    htmltext += "<p><b>Name with Octave:</b> "+n1.nameWithOctave+"</p>"
    
    if(n1.accidental):
        htmltext += "<p><b>Accidental:</b> "+n1.accidental.fullName+"</p>"            
        
    htmltext += """
        </body></html>
        """
    
    return htmltext