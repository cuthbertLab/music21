# -*- coding: utf-8 -*-
# index.py
# A simple script to test file uploading
# Each function is accessed via /FUNCTION_NAME
# Prompts for a file, then prints out the file's contents

from mod_python import apache

# Patch for music21 import
import re
import os
os.environ['HOME'] = '/Library/WebServer/Documents/humdrum/tmp'

import tempfile

from music21 import *

# Welcomes to page, provides options to use default file or upload file
def index(req):
    html = """
        <html ><body>
        <h1>Humdrum Census+: Humdrum Census-like results using music21</h1>
        <p><a href='defaultfile'>Test using default corpus file</a><p>
        <p><a href='selectfile'>Select a file from music21's corpus</a><p>
        <p><a href='uploadform'>Upload a file</a><p>
        </body></html>
        """
    return html

# Displays the upload form
def uploadform(req):
    html = """
        <html ><body>
        <h1>File Uploader:</h1>
        <a href='./'>Back</a>
        <p>Note: Only XML files can be uploaded.<p />
        <form action="processupload" method="POST" enctype="multipart/form-data">
        <input type="hidden" name="subUploadForm" value=1/>
        <input type="file" name="fileupload"/><br />
        <input type="submit" value="Upload" onclick="this.value='Processing...';submit()">
        </form>
        </body></html>
        """
    return html

# Displays the upload form
def selectfile(req):
    html = """
        <html ><body>
        <h1>Select File From Corpus:</h1>
        <a href='./'>Back</a><br />
        <form action="processcorpusfile" method="POST">
        <input type="hidden" name="subCorpusSelectForm" value=1/>
        <select name="corpusfile">
        """
    paths = corpus.base.getPaths({'xml'})
    paths.sort()
    
    for path in paths:
        html += "<option value = '" + path[49:] + "'>" + path[49:] + "</option>\n"
        
    html += """
        </select>
        <input type="submit" value="Select" onclick="this.disabled ='true'; this.value='Processing...';submit()">
        </form>
        <p>Please be patient. This process may take up to a minute for very large scores<p />
        </body></html>
        """
    return html

# Called when file is uploaded
def processupload(req):
    
    # Check if form data is present. If not found, display error
    try:
        file = req.form['subUploadForm']
    except:
        html = """
            <html ><body>
            <h1>Error:</h1>
            <p>Form information not found</p>
            <p><a href='form'>try again</a></p>
            </body></html>
            """
        return html

    
    # Get file from POST
    uploadedFile = req.form['fileupload'].file
    filename = req.form['fileupload'].filename
    type = req.form['fileupload'].type

    # Check if filename is empty - display no file chosen error
    if filename == "":
        html = """
            <html ><body>
            <h1>Error:</h1>
            <p>No file chosen</p>
            <p><a href='uploadform'>try again</a></p>
            </body></html>
            """
        return html
    
#    if type != "text/xml":
#        html = """
#            <html ><body>
#            <h1>Error:</h1>
#            <p>File not in XML Format</p>
#            <p><a href='uploadform'>try again</a></p>
#            </body></html>
#            """
#        return html

    matchedFormat = re.sub('^.*\.', '', filename)
    if matchedFormat == "":
        pass ### nice error...
    else:
        music21FormatName = common.findFormat(matchedFormat)[0]
        if music21FormatName is None:
            pass

    html = music21FormatName
    
    parsedFile = converter.parse(uploadedFile.read(),format=music21FormatName)
    info = humdrumInfo(parsedFile)
    html += humdrumInfoTemplate(info,filename)

    return html

# Called when corpus file is selected
def processcorpusfile(req):
    
    # Check if form data is present. If not found, display error
    try:
        file = req.form['subCorpusSelectForm']
    except:
        html = """
            <html ><body>
            <h1>Error:</h1>
            <p>Form information not found</p>
            <p><a href='selectfile'>try again</a></p>
            </body></html>
            """
        return html
    
    # Get corpusfile from POST.
    corpusfilename = req.form['corpusfile']

    # Check if name is empty - display no name error
    if corpusfilename == "":
        html = """
            <html ><body>
            <h1>Error:</h1>
            <p>No corpus file selected</p>
            <p><a href='selectfile'>try again</a></p>
            </body></html>
            """
        return html

    file = corpus.parse(corpusfilename)
    info = humdrumInfo(file)
    html = humdrumInfoTemplate(info,corpusfilename)

    return html

# Called when selecting default file
def defaultfile(req):
    file = corpus.parse('bach/bwv7.7')
    info = humdrumInfo(file)
    html = humdrumInfoTemplate(info,'bach/bwv7.7')
    
    return html

# Use this to experiment with getting data from the corpus file.
def experimentation(req):
    html = """
            <html ><body>
            """
    paths = corpus.base.getPaths()
    
    for path in paths:
        html += "<p>" + path[93:] + "</p>"
    
    html += "</body></html>"

    
    return html
        
# Returns info dictionary of humdrum information for the given, parsed score
def humdrumInfo(sc):
    info = dict()
    
    # Metadata
    composerName = str(sc.metadata.composer)
#    if composerName is None:
#        composerName = 'unknown'
                
    info['composer'] = composerName

    # Counting notes, parts
    info['numPitches'] = len(sc.pitches)
    info['numNotes'] = len(sc.flat.notes)
    info['numNotesAndRests'] = len(sc.flat.notesAndRests)

    # Initialize Note Duration Statistics
    maxNoteDuration = sc.flat.notes[1].duration.quarterLength
    maxNoteDurationText = sc.flat.notes[1].duration.fullName
    minNoteDuration = sc.flat.notes[1].duration.quarterLength
    minNoteDurationText = sc.flat.notes[1].duration.fullName

    # Check Duration Information:
    for n in sc.flat.notes:
        nDuration = n.duration.quarterLength

        if nDuration < minNoteDuration :
            minNoteDuration = nDuration
            minNoteDurationText = n.duration.fullName
            
        elif nDuration > maxNoteDuration :
            maxNoteDuration = nDuration
            maxNoteDurationText = n.duration.fullName
    
    
    # Add duration information to dict
    info['maxNoteDuration'] = maxNoteDuration
    info['maxNoteDurationText'] = maxNoteDurationText
    info['minNoteDuration'] = minNoteDuration
    info['minNoteDurationText'] = minNoteDurationText
    
     # Initialize Pitch Statistics
    highestPitchPS = sc.pitches[1].ps
    highestPitchName = sc.pitches[1].fullName
    lowestPitchPS = sc.pitches[1].ps
    lowestPitchName = sc.pitches[1].fullName

    for p in sc.pitches:
        # Check Pitch Information
        pPitch = p.ps    
        if pPitch < lowestPitchPS :
            lowestPitchPS = pPitch
            lowestPitchName = p.fullName
            
        elif pPitch > highestPitchPS :
            highestPitchPS = pPitch
            highestPitchName = p.fullName

    # Add pitch information to dict
    info['lowestPitchPS'] = lowestPitchPS
    info['lowestPitchName'] = lowestPitchName
    info['highestPitchPS'] = highestPitchPS
    info['highestPitchName'] = highestPitchName

    return info

# Returns the HTML for a webpage displaying information of the given humdrum info file
def humdrumInfoTemplate(info, scorename = ''):
    html = """
        <html ><body>
        """
    html += "<h1>Score Statistics:</h1>"
    html += "<p><b>File:</b> "+ scorename + "</p>"    
    html += "<p><b>Composer:</b> "+ info['composer'] + "</p>"    
    html += "<a href='./'>Analyze another score</a>"
    
    html += "<h2>General Statistics:</h2>"
#    html += "<p><b>Number of Parts:</b> " + str(info['numParts']) + "</p>"
    html += "<p><b>Number of Pitches:</b> " + str(info['numPitches']) + "</p>"
    html += "<p><b>Number of Notes:</b> " + str(info['numNotes']) + "</p>"
    html += "<p><b>Number of Rests:</b> " + str(info['numNotesAndRests'] - info['numNotes']) + "</p>"
    html += "<br />"

    html += "<h2>Duration Statistics:</h2>"
    html += "<p><b>Longest Note:</b> " + info['maxNoteDurationText'] + "</p>"
    html += "<p><b>Shortest Note:</b> " + str(info['minNoteDurationText']) + "</p>"
    html += "<br />"

    html += "<h2>Pitch Statistics:</h2>"
    html += "<p><b>Lowest Note:</b> " + info['lowestPitchName'] + " (PS: " + str(info['lowestPitchPS']) + ")" + "</p>"
    html += "<p><b>Highest Note:</b> " + info['highestPitchName'] + " (PS: " + str(info['highestPitchPS']) + ")" + "</p>"
    html += "<br />"

    html += """
        </body></html>
        """
    
    return html
