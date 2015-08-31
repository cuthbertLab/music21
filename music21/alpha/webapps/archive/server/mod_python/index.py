# -*- coding: utf-8 -*-
# An interface for music21 using mod_python
# Created by Lars Johnson - Music Hack Day - Nov 5-6, 2011
#
# To use, first install mod_python and include it in the HTTPD.conf file.
#
# Create a new directory on the server used only for this file, 
# on mac this could be /Library/WebServer/Documents/music21interface/index.py
#
# Then edit the HTTPD.conf file to redirect any requests to that directory to call this file:
# 
# <Directory /Library/WebServer/Documents/music21interface
#     SetHandler mod_python
#     PythonHandler mod_python.publisher
#     PythonDebug On
#     DirectoryIndex index.py
# </Directory>
#
# The mod_python publisher handler will call the function in this file associated with the contents
# of the URL after the directory. So, visiting localhost://music21interface/process will call
# process(req) where req is information associated with the request (in our case, POST information)

from mod_python import apache

import os
import re
os.environ['HOME'] = '/tmp/'

from music21 import *

from music21.figuredBass import checker

from music21.demos.bhadley import hack

# To call this function, send a POST request to WEBSERVER:/path-to-directory-containing-this-file/process
# with parameters xmltext, appname, cmd
#  - xmltext is the raw musicxml of the file
#  - appname is either 'noteflight' or 'musescore' - accounts for differences between two
#  - cmd is string, delimited by spaces, determining which function(s) to execute
def process(req):
    # Get fields from POST
    xmltext = req.form['xmltext']
    appname = req.form['appname']
    cmd = req.form['cmd']
    
    # Add Doctype if not included in xml data
    if xmltext.find("<?xml") == -1:
    	xmltext = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
"http://www.musicxml.org/dtds/partwise.dtd">""" + xmltext
    
    # Strip improperly formatted 
    xmltext = re.sub("<notehead color=\"#[0-9A-Fa-f]*\"/>",'',xmltext)
    
    sc = converter.parse(xmltext)

    # Command syntax is "function:args function2:args2"
    cmdarr = cmd.split(' ')
    
    message = 'no function found'
            
    for cmdline in cmdarr:
        cmdlineparts = cmdline.split(':')
        functionID = cmdlineparts[0]
        if(len(cmdlineparts)>1):
            functionArgs = cmdlineparts[1]
        
        if functionID == 'transpose':
            (sc,message) = transpose(sc, functionArgs)
    
        elif functionID == 'reduction':
            (sc,message) = reduction(sc)
    
        elif functionID  == 'color':
            (sc,message) = changeColorOfAllNotes(sc, functionArgs)
    
        elif functionID == 'canon':
            (sc,message) = createMensuralCanon(sc)
    
        elif functionID == 'showcorpus':
            (sc,message) = displayCorpusFile(functionArgs)
    
        elif functionID == 'idparallelfifths':
            message = identifyParallelFifths(sc) # modifies score in place
    
        elif functionID == 'idparalleloctaves':
            message = identifyParallelOctaves(sc) # modifies score in place
    
        elif functionID == 'idhiddenfifths':
            message =identifyHiddenFifths(sc) # modifies score in place
    
        elif functionID == 'idhiddenoctaves':
            message =identifyHiddenOctaves(sc) # modifies score in place
    
        elif functionID == 'idvoicecrossings':
            message =identifyVoiceCrossing(sc) # modifies score in place

        elif functionID == 'checkleadsheetpitches':
            (sc,message) =checkLeadSheetPitches(sc,functionArgs)
            
    # Necessary for Beth's script to run
    sc.show('text')
    # return sc._reprText() # Debug - see music21 output
                
    output = sc.musicxml
    
    if(appname == 'noteflight'):
        output += "\n---"
        output += str(message)

    return output

# Beth's code for chord symbols: returns answer if returnType = 'answerkey'
def checkLeadSheetPitches(sc, returnType=''):
    nicePiece = sc
    incorrectPiece = sc
    
    #incorrectPiece = messageconverter.parse('C:\Users\sample.xml')
    
    sopranoLine = nicePiece.getElementsByClass(stream.Part)[0]
    chordLine = nicePiece.getElementsByClass(stream.Part)[1]
    #chordLine.show('text')
    #bassLine = nicePiece.part(2)
    s = harmony.getDuration(sopranoLine)
    onlyChordSymbols = s.flat.getElementsByClass(harmony.ChordSymbol)
    newStream = stream.PartStaff()
    newStream.append(clef.BassClef())
    answerKey = stream.Score()
    answerKey.append(sopranoLine)
    for chordSymbol in onlyChordSymbols:
        newStream.append(hack.realizePitches(chordSymbol))
    
    answerKey.insert(0,newStream)
    
    correctedAssignment, numCorrect = hack.correctChordSymbols(answerKey, incorrectPiece)
    correctedAssignment.show('text')
    answerKey.show('text')
    
    if returnType == 'answerkey':
        returnScore = answerKey
        message = 'answer key displayed'
    else: 
        returnScore = correctedAssignment
        message = 'you got '+str(numCorrect)+' percent correct'

    
    return (returnScore,message)

# Jose's Methods for Theory Checking - result is an array of measure numbers where the errors occured
def identifyParallelFifths(sc):
    result = checker.checkConsecutivePossibilities(sc,checker.parallelFifths)
    return processCheckerResult(result,'parallel fifths')

def identifyParallelOctaves(sc):
    result = checker.checkConsecutivePossibilities(sc,checker.parallelOctaves)
    return processCheckerResult(result,'parallel octaves')

def identifyHiddenFifths(sc):
    result = checker.checkConsecutivePossibilities(sc,checker.hiddenFifth)
    return processCheckerResult(result,'hidden fifths')

def identifyHiddenOctaves(sc):
    result = checker.checkConsecutivePossibilities(sc,checker.hiddenOctave)
    return processCheckerResult(result,'hidden octaves')

def identifyVoiceCrossing(sc):
    result = checker.checkSinglePossibilities(sc,checker.identifyVoiceCrossing)
    return processCheckerResult(result,'voice crossing')

# Converts the resuling array of measure numbers to string
def processCheckerResult(result,type):
    if len(result)==0 :
        return 'no '+type+' found'
    msg = ''
    for measure in result:
        msg += str(measure) + ','
    return type+' found on measures '+msg[:-1]

# Iterate through all notes and change their color to the given hex value string color. ex "#FF0000" for red
def changeColorOfAllNotes(sc, color):
    for n in sc.flat.notes:
        n.color = color 
    return (sc,'color changed to '+color)

# Implements music21 example of reducing and annotating score
def reduction(sc):
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    sc.insert(0,reductionStream)
    return (sc,'score reduced')

# Transposes the score by the given transposeInterval string (ex. "p5")
def transpose(sc, transposeInterval):
    return (sc.transpose(transposeInterval),'transposed by '+transposeInterval)

# Returns XML of corpus file
def displayCorpusFile(file):
    msg = file+'  displayed'
    
    # Enable us to load our demo files for the presentation
    if file.find('demo') != -1:
        file = '/Library/Python/2.7/site-packages/music21/corpus/'+file
        sc = converter.parse(file)
        return (sc,msg)
        
    sc = corpus.parse(file)
    return (sc,msg)

# Implements music21 example of creating a mensural canon
def createMensuralCanon(sc):
    melody = sc.parts[0].flat.notesAndRests
    
    canonStream = stream.Score()
    for scalar, t in [(1, 'p1'), (2, 'p-5'), (.5, 'p-11'), (1.5, -24)]:
        part = melody.augmentOrDiminish(scalar, inPlace=False)
        part.transpose(t, inPlace=True)
        canonStream.insert(0, part)
    
    return (canonStream,'mensural canon generated')