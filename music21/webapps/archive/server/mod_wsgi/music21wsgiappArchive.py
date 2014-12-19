# -*- coding: utf-8 -*-
# An interface for music21 using mod_wsgi
#
# To use, first install mod_wsgi and include it in the HTTPD.conf file.
#
# Add this file to the server, ideally not in the document root, 
# on mac this could be /Library/WebServer/wsgi-scripts/music21wsgiapp.py
#
# Then edit the HTTPD.conf file to redirect any requests to WEBSERVER:/music21interface to call this file:
# Note: unlike with mod_python, the end of the URL does not determine which function is called,
# WSGIScriptAlias always calls application.
# 
# WSGIScriptAlias /music21interface /Library/WebServer/wsgi-scripts/music21wsgiapp.py
#
# Further down the conf file, give the webserver access to this directory:
#
# <Directory "/Library/WebServer/wsgi-scripts">
#     Order allow,deny
#     Allow from all
# </Directory>
#
# The mod_wsgi handler will call the application function below with the request
# content in the environ variable.

# To use the post, send a POST request to WEBSERVER:/music21interface
# where the contents of the POST is a JSON string.
# In general:
#  - type is "code" "simplecommand" or "m21theory" to direct the request to the appropriate set of functions
#  - xml is the musicxml of the file
# with type = "code":
#  - code is a string of python code to be executed
# with type = "simplecommand":
#  - cmd is a string, delimited by spaces, determining which function(s) to execute

from music21 import *
import music21.theoryAnalysis.theoryAnalyzer

import json

# Other imports
import copy
import itertools

import sys

# Used for Music Theory Examples
from music21.theoryAnalysis import *

# Used for Theory Analyzer And WWNorton
from music21.theoryAnalysis.theoryAnalyzer import *
from music21.theoryAnalysis.wwnortonMGTA import *

# Used for previous demonstrations:
from music21.figuredBass import checker

# Emailing:
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

import gzip


# Patch for music21 import
#import re
#import os
#os.environ['HOME'] = '/Library/WebServer/Documents/humdrum/tmp'


# Receives the WSGI Request to the application. environ.read() gets the contents of the POST.
def application(environ, start_response):
    status = '200 OK'

    json_str_data = environ['wsgi.input'].read()

    json_str_response = processJSONData(json_str_data)

    response_headers = [('Content-type', 'text/plain'),
            ('Content-Length', str(len(json_str_response)))]

    start_response(status, response_headers)

    return [json_str_response]

class stringOutput:
    def __init__(self):
        self.outputString = ""
        
    def write(self,strToAppend):
        self.outputString = self.outputString + strToAppend
        
    def read(self):
        return self.outputString

## -- the below was previously in a different file on my system, but I moved it to this location for ease of install ##

# Receives JSON information in string format, converts to dictionary, and dispatches to appropriate method:
# Then converts the resulting object back to a string to be returned to the wsgi application.
def processJSONData(json_data_str):
    errorStringHolder = stringOutput()
    stdOutStringHolder = stringOutput()
    prevStdError = sys.stderr
    prevStdOut = sys.stdout
    sys.stderr = errorStringHolder
    sys.stdout = stdOutStringHolder
    
    
    # Turn the JSON string into a dictionary
    json_obj = json.loads(json_data_str)

    # Get type of request  from the json object
    # Note: need str() because json object returns an object of unicode type
    try:
        requestType = str(json_obj['type'])
    except KeyError:
        requestType = "none"
    
    # Dispatch based on type
    if (requestType == "simpleCommand"): # Simple command implements the previous web interface for demos
        result_obj = processSimpleCommandJSON(json_obj)
    elif (requestType == "code"):
        try:
            result_obj = processCodeJSON(json_obj)
            result_obj['status'] = "success"
        except Exception as e:
            result_obj = {}
            result_obj['origObj'] = json_obj
            result_obj['status'] = 'error'
            result_obj['error'] =  stdOutStringHolder.read() + str(type(e)) + str(e)
    elif (requestType == "m21theory"):
        result_obj = processM21TheoryJSON(json_obj)
    elif (requestType == "wwnorton"):
        result_obj = processWWNortonJSON(json_obj)
    else:
        result_obj = {
           "message":"no type found"}

    
    result_obj['stdOut'] = stdOutStringHolder.read()
        
    
    
    sys.stderr = prevStdError
    sys.stdout = prevStdOut
    
    # Convert dictionary back to string and return
    json_response = json.dumps(result_obj)        
    return json_response

# WWNorton related commands -- in progress
def processWWNortonJSON(json_obj):
    print('processing WW Norton')
    message = ""
    # Get what command the JSON is requesting
    try:
        command = str(json_obj['command'])
    except KeyError:
        command = "none"

    if command == "loadExercise":
        obj = wwNortonLoadExercise(json_obj)
    elif command == "checkExercise":
        obj = wwNortonCheckExercise(json_obj)
    elif command == "submitExercise":
        obj = wwNortonSubmitExercise(json_obj)
    elif command == "analyzeAndEmail":
        obj = wwnortonAnalyzeAndEmail(json_obj)
    else:
        obj = {"message" : "Error"}

    return obj


# WWNorton related commands -- in progress
def wwNortonLoadExercise(json_obj):
    message = ""
    title = ""
    instructions = ""
    # Get what action the JSON is requesting
    try:
        exerciseID = str(json_obj['exerciseID'])
    except KeyError:
        return {"message" : "error"}

    if exerciseID == "11_1_I_A":
        ex = ex11_1_I()
    elif exerciseID == "11_1_I_B":
        ex = ex11_1_I('B')
    elif exerciseID == "11_1_I_C":
        ex = ex11_1_I('C')
    elif exerciseID == "11_1_I_D":
        ex = ex11_1_I('D')
    elif exerciseID == "11_3_A_1":
        ex = ex11_3_A()
    elif exerciseID == "11_3_A_2":
        ex = ex11_3_A(2)
    elif exerciseID == "11_3_A_3":
        ex = ex11_3_A(3)
    else:
         return {"message" : "error"}

    sc = ex.modifiedExercise
    
    xmltext = sc.musicxml
    obj = {"xml" : ex.modifiedExercise.musicxml,
        "exerciseID": exerciseID,
        "title":ex.title,
        "instructions":ex.instructions,
        "message":message}
    
    return obj

# WWNorton related commands -- in progress
def wwNortonCheckExercise(json_obj):
    message = ""
    xmltext = str(json_obj['xml'])
    
    # ADD XML doctype header if not present -- needed for converter to parse
    if xmltext.find("<?xml") == -1:
        xmltext = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
"http://www.musicxml.org/dtds/partwise.dtd">""" + xmltext

    # Initialize sc and message.
    sc = converter.parse(xmltext)

    try:
        exerciseID = str(json_obj['exerciseID'])
    except KeyError:
        exerciseID = "none"

    if exerciseID == "11_1_I_A":
        ex = ex11_1_I()
    elif exerciseID == "11_1_I_B":
        ex = ex11_1_I('B')
    elif exerciseID == "11_1_I_C":
        ex = ex11_1_I('C')
    elif exerciseID == "11_1_I_D":
        ex = ex11_1_I('D')
    elif exerciseID == "11_3_A_1":
        ex = ex11_3_A()
    elif exerciseID == "11_3_A_2":
        ex = ex11_3_A(2)
    elif exerciseID == "11_3_A_3":
        ex = ex11_3_A(3)
        
        
    
    ex.loadStudentExercise(sc)
    ex.checkExercise()
    sc = ex.studentExercise
    message += ex.textResultString
    
    if exerciseID != "none":
        xmltext = sc.musicxml
        obj = {"xml" : xmltext,
            "message":message}
    else:
        obj = {"message" : "error"}
    
    return obj

# WWNorton related commands -- in progress
def wwNortonSubmitExercise(json_obj):
    message = ""
    xmltext = str(json_obj['xml'])
    
    # ADD XML doctype header if not present -- needed for converter to parse
    if xmltext.find("<?xml") == -1:
        xmltext = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
"http://www.musicxml.org/dtds/partwise.dtd">""" + xmltext

    # Initialize sc and message.
    sc = converter.parse(xmltext)

    try:
        exerciseID = str(json_obj['exerciseID'])
    except KeyError:
        exerciseID = "none"

    if exerciseID == "11_1_I_A":
        ex = ex11_1_I()
    elif exerciseID == "11_1_I_B":
        ex = ex11_1_I('B')
    elif exerciseID == "11_1_I_C":
        ex = ex11_1_I('C')
    elif exerciseID == "11_1_I_D":
        ex = ex11_1_I('D')
    elif exerciseID == "11_3_A_1":
        ex = ex11_3_A()
    elif exerciseID == "11_3_A_2":
        ex = ex11_3_A(2)
    elif exerciseID == "11_3_A_3":
        ex = ex11_3_A(3)
        
        
    
    ex.loadStudentExercise(sc)
    ex.checkExercise()
    sc = ex.studentExercise
    message += ex.textResultString

    studentName = str(json_obj['studentName'])
    studentEmail = str(json_obj['studentEmail'])
    # Get what action the JSON is requesting
    try:
        toEmail = str(json_obj['toEmail'])
    except KeyError:
        toEmail = "none"


    messageBody = ""
    messageBody += "<img src='http://ciconia.mit.edu/music21/pluginresources/header.png' width='470' height='60'/><br />" 
    messageBody += studentName  +" ("+studentEmail+")  has submitted an response to "+ex.shortTitle+" using the musescore plugin. Pre-grading results are listed below. A colored XML file is attached.<br /><br />"
    messageBody += "<b>PRE_GRADING RESULTS:</b><br /><br />"
    messageBody += "<ul>"

    messageBody += ex.textResultString
    messageBody += "<br />The comments above are instances where the student's assignment is not in the style of common practice counterpoint. Final grading is left to the discretion of the teacher."

    subject = "WWNorton Exercise Submission from "+studentName

    sc.metadata.movementName = ex.shortTitle +" - "+studentName

    xmlTextToSend = sc.musicxml

    fileName = ex.shortTitle+"-"+studentName+".xml"

    sendEmail(toEmail,messageBody,subject,xmlTextToSend, fileName)

    obj = {"xml" : xmlTextToSend,
        "message":"Message has been submitted successfully to "+toEmail+"."}
    
    return obj

    if exerciseID != "none":
        xmltext = sc.musicxml
        obj = {"xml" : xmltext,
            "message":message}
    else:
        obj = {"message" : "error"}
    
    return obj

# WWNorton email Exercise
def wwnortonAnalyzeAndEmail(json_obj):
    xmltext = str(json_obj['xml'])
    studentName = str(json_obj['studentName'])
    
    # Get what action the JSON is requesting
    try:
        emailAddress = str(json_obj['emailAddress'])
    except KeyError:
        emailAddress = "none"

    # ADD XML doctype header if not present -- needed for converter to parse
    if xmltext.find("<?xml") == -1:
        xmltext = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
"http://www.musicxml.org/dtds/partwise.dtd">""" + xmltext

    # Initialize sc and message.
    sc = converter.parse(xmltext)
    ta = TheoryAnalyzer(sc)
    ta.identifyCommonPracticeErrors(0,1)

    messageBody = ""
    messageBody += "----------- Notes from Lars ----------\n"
    messageBody += "This message was triggered from a button on a musescore plugin stating 'Analyze score and email'. \n"
    messageBody += "The document was originally uncolored in the musescore editor. \n"
    messageBody += "The analysis and body of this message was processed by music21 running on ciconia.mit.edu. \n"
    messageBody += "The email was sent from the script running on ciconia.mit.edu using python's email.mime and email.smtp modules. \n"
    messageBody += "I created a dummy gmail account so I wouldn't have to (possibly) expose my personal gmail accoun's password.\n"
    messageBody += "--------------------------------------\n\n"
    messageBody += studentName + " has submitted an counterpoint exercise using the musescore plugin. Results are listed below. The colored XML file is attached.\n\n"
    messageBody += "THEORY ANALYZER RESULTS:\n\n"      
    messageBody += ta.getResultsString()
    messageBody += "\n\n"

    subject = "Musescore Plugin Exercise Result" 


    xmlTextToSend = sc.musicxml

    sendEmail(emailAddress,messageBody,subject,xmlTextToSend)

    obj = {"xml" : xmlTextToSend,
        "message":"Email Sent"}
    
    return obj


def sendEmail(toAddress,messageBody, subject, xmlTextToSend,filename):
    COMMASPACE = ', '

    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['Subject'] = subject
    # me == the sender's email address
    # family = the list of all recipients' email addresses
    msg['From'] = "music21emailer@gmail.com"
    msg['To'] = toAddress
    msg.preamble = 'XML File from musescore plugin'

    # Add the Message Body
    bodyMIME = MIMEText(messageBody,'html')
    msg.attach(bodyMIME)
    
    # Add the XML Attachment
    xmlMIME = MIMEText(xmlTextToSend,'xml')
    xmlMIME.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(xmlMIME)
    # Send the email via our own SMTP server.
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login('music21emailer','m21emailer')

    s.sendmail("music21emailer@gmail.com", [toAddress], msg.as_string())
    s.quit()


# Music21Theory related commands -- in progress
def processM21TheoryJSON(json_obj):
    # Get what action the JSON is requesting
    try:
        exerciseID = str(json_obj['exerciseID'])
    except Key:
        exerciseID = "none"
        
    if exerciseID == "triad":
        obj= processTriadExercise(json_obj)
    else:
        obj = {
           "message":"no action found"} 
    
    return obj

# Example exercise - checking triad - to be expanded later.
# JSON key studentanswer is a text file containing student answers: root [space] quality [newline].
def processTriadExercise(json_obj):
    # Get what action the JSON is requesting
    
    xmltext= json_obj['xml']
    sc = converter.parse(xmltext)
    
    studentAnswer = json_obj['studentAnswer']
    
    studentAnswerListOfTuples = list()
    
    for line in studentAnswer.split('\n'):
        if line.strip() == "X":
            answerTuple = ('X','')
        else:
            answerTuple = tuple(line.strip().split(' ',1))
        studentAnswerListOfTuples.append(answerTuple)
        
    responseArr = music21Theory.checkTriadExercise(sc, studentAnswerListOfTuples)
    
        
        
    obj = {
           "message":str(responseArr)}
    return obj

# Enables users to execute python code on the xml of the score
# sc is the variable representing the music21 parsed score of the posted xml
# message is a variable that will be returned in the object.
def processCodeJSON(json_obj):
    # get information from the json object
    # note: need str() because json object returns an object of unicode type
    code = str(json_obj['code'])
    if 'xml' in json_obj:
        xmltext = str(json_obj['xml'])
    
        # ADD XML doctype header if not present -- needed for converter to parse
        if xmltext.find("<?xml") == -1:
            xmltext = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
"http://www.musicxml.org/dtds/partwise.dtd">""" + xmltext
    
        # Initialize sc and message.
        sc = converter.parse(xmltext)
    message = ""
    
    # Do some code checking and then execute 
    if(code.find('import') != -1):
        message = "error: import statements not allowed"
    elif(code.find('exec') != -1):
        message = "error: exec statements not allowed"
    elif(code.find('sys') != -1):
        message = "error: accessing sys is not allowed"
    else:
        compiledCode = compile(code,'<string>','exec')
        exec(compiledCode)
    # Create an object to return :    
    obj = {"xml":sc.musicxml,
           "code":code,
           "message":message}
        
    return obj

# Back-compatibility for our first examples - JSON object contains a "cmd" key which represents
# simple commands (reduction, transpose:p5...)
def processSimpleCommandJSON(json_obj):
    # get information from the json object
    # note: need str() because json object returns an object of unicode type
    xmltext = str(json_obj['xml'])
    cmd = str(json_obj['cmd'])    

    # ADD XML doctype header if not present -- needed for converter to parse
    if xmltext.find("<?xml") == -1:
        xmltext = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN"
"http://www.musicxml.org/dtds/partwise.dtd">""" + xmltext

    sc = converter.parse(xmltext)

    # Create an object that will maintain information as we apply various functions to it:    
    obj = {"sc":sc,
           "message":""}
    
    # Command syntax is "function:args function2:args2" Split at spaces then iterate through
    cmdarr = cmd.split(' ')

	# Redirect to appropriate function - all modify the object in place.
    for cmdline in cmdarr:
        cmdlineparts = cmdline.split(':')
        functionID = cmdlineparts[0]
            
        if(len(cmdlineparts)>1):
            functionArgs = cmdlineparts[1]
        
        if functionID == 'transpose':
            transpose(obj, functionArgs)
    
        elif functionID == 'reduction':
            reduction(obj)
            
        elif functionID  == 'color':
            changeColorOfAllNotes(obj, functionArgs)
    
        elif functionID == 'canon':
            createMensuralCanon(obj)
    
        elif functionID == 'showcorpus':
            displayCorpusFile(obj, functionArgs)
    
        elif functionID == 'idparallelfifths':
            identifyParallelFifths(obj) # modifies score in place
    
        elif functionID == 'idparalleloctaves':
            identifyParallelOctaves(obj) # modifies score in place
    
        elif functionID == 'idhiddenfifths':
            identifyHiddenFifths(obj) # modifies score in place
    
        elif functionID == 'idhiddenoctaves':
            identifyHiddenOctaves(obj) # modifies score in place
    
        elif functionID == 'idvoicecrossings':
            identifyVoiceCrossing(obj) # modifies score in place

        elif functionID == 'checkleadsheetpitches':
            checkLeadSheetPitches(obj)
    
    # Change the sc key which is in music21 format to an xml attribute in musicxml
    # Then, delete the sc key
    obj['xml'] = obj['sc'].musicxml
    
    obj.pop('sc') # Don't return the actual score object
    
    return obj

# Implements music21 example of reducing and annotating score
def reduction(obj):
    sc = obj['sc']
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    sc.insert(0,reductionStream)
    
    obj['sc'] = sc
    obj['message'] = obj['message'] + "Score Reduced "

## Beth's code for chord symbols: returns answer if returnType = 'answerkey'
# this is way too outdated to even try to fix it now...
#def checkLeadSheetPitches(obj):
#    sc = obj['sc'];
#    nicePiece = sc
#    incorrectPiece = sc
#    
#    #incorrectPiece = messageconverter.parse('C:\Users\sample.xml')
#    
#    sopranoLine = nicePiece.getElementsByClass(stream.Part)[0]
#    chordLine = nicePiece.getElementsByClass(stream.Part)[1]
#    #chordLine.show('text')
#    #bassLine = nicePiece.part(2)
#    s = harmony.getDuration(sopranoLine)
#    onlyChordSymbols = s.flat.getElementsByClass(harmony.ChordSymbol)
#    newStream = stream.PartStaff()
#    newStream.append(clef.BassClef())
#    answerKey = stream.Score()
#    answerKey.append(sopranoLine)
#    for chordSymbol in onlyChordSymbols:
#        newStream.append(hack.realizePitches(chordSymbol))
#    
#    answerKey.insert(0,newStream)
#    
#    correctedAssignment, numCorrect = hack.correctChordSymbols(answerKey, incorrectPiece)
#    correctedAssignment.show('text')
#    answerKey.show('text')
#    
#    if returnType == 'answerkey':
#        returnScore = answerKey
#        message = 'Answer key displayed '
#    else: 
#        returnScore = correctedAssignment
#        message = 'You got '+str(numCorrect)+' percent correct '
#
#    obj['sc'] = returnScore;
#    obj['message'] = obj['message'] + message
#    
#    return obj

# Jose's Methods for Theory Checking - result is an array of measure numbers where the errors occurred
# Jose's methods modify sc in place, coloring the notes red.
def identifyParallelFifths(obj):
    result = checker.checkConsecutivePossibilities(obj['sc'],checker.parallelFifths)
    obj['message'] = processCheckerResult(result,'parallel fifths')

def identifyParallelOctaves(obj):
    result = checker.checkConsecutivePossibilities(obj['sc'],checker.parallelOctaves)
    obj['message'] = processCheckerResult(result,'parallel octaves')

def identifyHiddenFifths(obj):
    result = checker.checkConsecutivePossibilities(obj['sc'],checker.hiddenFifth)
    obj['message'] = processCheckerResult(result,'hidden fifths')

def identifyHiddenOctaves(obj):
    result = checker.checkConsecutivePossibilities(obj['sc'],checker.hiddenOctave)
    obj['message'] = processCheckerResult(result,'hidden octaves')

def identifyVoiceCrossing(obj):
    result = checker.checkSinglePossibilities(obj['sc'],checker.voiceCrossing)
    obj['message'] = processCheckerResult(result,'voice crossing')

# Converts the resulting array of measure numbers to string
def processCheckerResult(result,type):
    if len(result)==0 :
        return 'no '+type+' found'
    msg = ''
    for measure in result:
        msg += str(measure) + ','
    return type+' found on measures '+msg[:-1]+" "

# Iterate through all notes and change their color to the given hex value string color. ex "#FF0000" for red
def changeColorOfAllNotes(obj, color):
    sc = obj['sc']
    for n in sc.flat.notes:
        n.color = color 
    obj['message'] = obj['message'] + "All note colors changed to "


# Transposes the score by the given transposeInterval string (ex. "p5")
def transpose(obj, transposeInterval):
    obj['sc'] = obj['sc'].transpose(transposeInterval)
    obj['message'] = obj['message'] + 'transposed by '+transposeInterval+" "

# Returns XML of corpus file
def displayCorpusFile(obj, file):
    msg = file+'  displayed'
    
    # Enable us to load our demo files for the presentation
    if file.find('demo') != -1:
        file = '/Library/Python/2.7/site-packages/music21/corpus/'+file
        obj['sc'] = corpus.parse(file)
        obj['message'] = msg
        return
        
    obj['sc'] = corpus.parse(file)
    obj['message'] = msg

# Implements music21 example of creating a mensural canon
def createMensuralCanon(obj):
    sc = obj['sc']
    melody = sc.parts[0].flat.notesAndRests
    
    canonStream = stream.Score()
    for scalar, t in [(1, 'p1'), (2, 'p-5'), (.5, 'p-11'), (1.5, -24)]:
        part = melody.augmentOrDiminish(scalar, inPlace=False)
        part.transpose(t, inPlace=True)
        canonStream.insert(0, part)
    
    obj['sc'] = canonStream
    obj['message'] = obj['message'] + "Canon Generated "
