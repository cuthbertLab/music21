# -*- coding: utf-8 -*-
'''
An interface for music21 using mod_wsgi

To use, first install mod_wsgi and include it in the HTTPD.conf file.

Add this file to the server, ideally not in the document root, 
on mac this could be /Library/WebServer/wsgi-scripts/zipfileapp.py

Then edit the HTTPD.conf file to redirect any requests to WEBSERVER:/music21interface to call this file:
Note: unlike with mod_python, the end of the URL does not determine which function is called,
WSGIScriptAlias always calls application.

WSGIScriptAlias /music21/zipfileinterface /Library/WebServer/wsgi-scripts/zipfileapp.py

Further down the conf file, give the webserver access to this directory:

<Directory "/Library/WebServer/wsgi-scripts">
    Order allow,deny
    Allow from all
</Directory>

The mod_wsgi handler will call the application function below with the request
content in the environ variable.

To use the application, send a POST request to WEBSERVER:/music21interface
where the contents of the POST is a POST from a form containing a zip file.

'''
from music21 import common
from music21 import converter
from music21 import note
from music21 import interval
from music21 import exceptions21

from music21.ext import six
StringIO = six.StringIO

import zipfile
import cgi
import re
#

def music21ModWSGIZipFileApplication(environ, start_response):
    '''
    Music21 webapp to demonstrate processing of a zip file containing scores.
    Will be moved and integrated into __init__.py upon developing a standardized URL format
    as application that can perform variety of commands on user-uploaded files
    '''
    status = '200 OK'

    pathInfo = environ['PATH_INFO'] # Contents of path after mount point of wsgi app but before question mark

    command = pathInfo

    formFields = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
        
    uploadedFile = formFields['file1'].file
    filename = formFields['file1'].filename
    
    [name, unused_extension]= filename.rsplit('.',1)
    
    outputFileName = name + "-"+command.split('/')[1]+"-results.zip"
    
    # Create ZipFile Object
    zipIn = zipfile.ZipFile(uploadedFile, 'r')
    
    outputBuffer = StringIO.StringIO()
    zipOut = zipfile.ZipFile(outputBuffer, 'w')
    
    # Loop Through Files
    for scoreFileInfo in zipIn.infolist():
        
        filePath = scoreFileInfo.filename
        
        # Skip Directories
        if(filePath.endswith('/')):
            continue
        scoreFile = zipIn.open(filePath)
        
        # Use Music21's converter to parse file
        sc = idAndParseFile(scoreFile,filePath)
        
        # If valid music21 format, add to data set
        if sc is not None:
            resultSc = performFunction(sc,command)
            if resultSc is not None:
                zipOut.writestr(filePath, resultSc.musicxml)

    zipOut.close()
    
    resultStr = outputBuffer.getvalue()

    response_headers = [('Content-type', 'application/zip'),  ('Content-disposition','attachment; filename='+outputFileName),
            ('Content-Length', str(len(resultStr)))]

    start_response(status, response_headers)


    return [resultStr]

application = music21ModWSGIZipFileApplication

def performFunction(sc, command):
    '''
    Function that determines what command to perform on the score and returns the resulting score.
    Currently is a lookup table based on the URL, but will be improved and incorporated into webapps/__init__.py
    as it changes to allow for more standard music21 functions 
    '''
    commandParts = command.split("/")
    if (len(commandParts) < 3):
        raise exceptions21.Music21Exception("Not enough parts on the command")
    
    if commandParts[1] == "transpose":
        return sc.transpose(commandParts[2])
    
    elif commandParts[1] == "allCMajor":
        key = sc.analyze('key')
        (p, unused_mode) = key.pitchAndMode
        intv = interval.Interval(note.Note(p),note.Note('C'))
        
        for ks in sc.flat.getElementsByClass('KeySignature'):
            ks.transpose(intv, inPlace = True)
        sc.transpose(intv, inPlace = True)
        return sc
    
    elif commandParts[1] == "addReduction":
        reductionStream = reduction(sc)
        sc.insert(0,reductionStream)
        return sc
    
    elif commandParts[1] == "reduction":
        reductionStream = reduction(sc)
        return reductionStream
    
    elif commandParts[1] == "scaleDegrees":
        key = sc.analyze('key')
        #rootPitch = key.pitchAndMode[0]
        #rootNote = note.Note(rootPitch)
        
        for n in sc.flat.getElementsByClass('Note'):
            sd = key.getScaleDegreeFromPitch(n)
            if sd is not None:
                n.lyric = sd
        return sc

    else:
        return sc

def reduction(sc):
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    return reductionStream
    
def idAndParseFile(fileToParse,filename):
    '''Takes in a file object and filename, identifies format, and returns parsed file'''
    matchedFormat = re.sub(r'^.*\.', '', filename)
    if matchedFormat == "":
        pass
    else:
        music21FormatName = common.findFormat(matchedFormat)[0]
        if music21FormatName is None:
            parsedFile = None
        else:
            parsedFile = converter.parse(fileToParse.read(),format=music21FormatName)
            
    return parsedFile
