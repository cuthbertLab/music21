# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         webapps.base.py
# Purpose:      music21 functions for implementing web interfaces
#
# Authors:      Lars Johnson
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Functions for implementing server-based web interfaces. 

This module reads JSON strings as POSTs and implements
the interaction mapping the request contents to music21 functions
and returning appropriate results.

WORK IN PROGRESS
'''
#from __future__ import unicode_literals

import music21
from music21 import common
from music21 import converter
from music21 import stream
from music21 import corpus
from music21 import note
from music21 import features
from music21 import harmony
from music21 import clef
from music21 import tempo
from music21.demos.bhadley import hack
from music21.demos.theoryAnalysis import theoryAnalyzer

import json
import zipfile
import cgi
import re
import unittest
import doctest

import commands

import sys
import traceback

from StringIO import StringIO

availableDataFormats = ['xml',
                        'musicxml',
                        'abc',
                        'str',
                        'string',
                        'bool',
                        'boolean'
                        'int',
                        'reprtext',
                        'list',
                        'int',
                        'float']

availableFunctions = ['stream.transpose',
                      'corpus.parse',
                      'converter.parse',
                      'transpose',
                      'augmentOrDiminish',
                      'reduction',
                      'createMensuralCanon',
                      'checkLeadSheetPitches',
                      'getResultsString',
                      'colorResults',
                      'theoryAnalyzer.identifyParallelFifths',
                      'theoryAnalyzer.identifyParallelOctaves',
                      'theoryAnalyzer.identifyHiddenFifths',
                      'theoryAnalyzer.identifyHiddenOctaves',
                      'colorAllNotes',
                      'colorAllChords',
                      '__getitem__',
                      'writeMIDIFileToServer',
                      'tempo.MetronomeMark',
                      'insert',
                      'commands.runPerceivedDissonanceAnalysis',
                      'measures',
                      'generateChords',
                      'commands.generateIntervals']

availableAttribtues = ['highestOffset',
                       'flat',
                       '_theoryScore']

def music21ModWSGIJSONApplication(environ, start_response):
    '''
    Application function in proper format for a MOD-WSGI Application:
    Reads the contents of a post request, and passes the JSON string to
    webapps.processJSONData for further processing. 
    Returns a proper HTML response.
    
    An interface for music21 using mod_wsgi
    
    To use, first install mod_wsgi and include it in the HTTPD.conf file.
    
    Add this file to the server, ideally not in the document root, 
    on mac this could be /Library/WebServer/wsgi-scripts/music21wsgiapp.py
    
    Then edit the HTTPD.conf file to redirect any requests to WEBSERVER:/music21interface to call this file:
    
    WSGIScriptAlias /music21interface /Library/WebServer/wsgi-scripts/music21wsgiapp.py
    
    Further down the conf file, give the webserver access to this directory::
    
        <Directory "/Library/WebServer/wsgi-scripts">
            Order allow,deny
            Allow from all
        </Directory>
    
    The mod_wsgi handler will call the application function below with the request
    content in the environ variable.
    
    To use the post, send a POST request to WEBSERVER:/music21interface
    where the contents of the POST is a JSON string.
    
    See processJSONSTring below for specifications about the structure of this string.
    '''
    status = '200 OK'

    json_str = environ['wsgi.input'].read()

    json_str_response = processJSONString(json_str)

    response_headers = [('Content-type', 'text/plain'),
        ('Content-Length', str(len(json_str_response)))]

    start_response(status, response_headers)

    return [json_str_response]

def processJSONString(json_request_str):
    '''
    Takes in a raw JSON string, parses the structure into an object **WHAT KIND OF OBJECT**,
    executes the corresponding music21 functions, and returns a string of raw JSON detailing the result
    '''
    
    '''
    {
    "dataDict": {
        "myNum":
            {"fmt" : "int",
             "data" : "23"}
    },
    "commandList":[
        {"function":"corpus.parse",
         "argList":["'bwv7.7'"],
         "resultVariable":"sc"},
         
        {"function":"transpose",
         "caller":"sc",
         "argList":["'p5'"],
         "resultVariable":"sc"},
         
    
        {"attribute":"flat",
         "caller":"sc",
         "resultVariable":"scFlat"},
         
        {"attribute":"highestOffset",
         "caller":"scFlat",
         "resultVariable":"ho"}
    ],
    "returnDict":{
        "myNum" : "int",
        "ho"    : "int"
        }
    }
    
    '''
    agendaDict = AgendaDict()
    
    json_request_str = unicode(json_request_str, 'utf-8')

    agendaDict.loadJson(json_request_str)
    request_obj = RequestObject(agendaDict)
    request_obj.executeCommands()
    result_obj = request_obj.getResultObject();
    json_result_str = json.dumps(result_obj)
    return json_result_str

class AgendaDict(dict):
    '''
    subclass of dictionary that represents data and commands to be run
    through the request object and formats to be returned.
    
    '''
    def loadJson(self, jsonRequestStr):
        '''
        Runs json.loads on jsonRequestStr
        
        
        '''
        tempDict = json.loads(jsonRequestStr)
        for thing in tempDict:
            self[thing] = tempDict[thing]
        
        


class RequestObject(object):
    '''
    Object used to coordinate JSON requests to music21.
    
    Takes a json string as input, parses data specified in dataDict,
    executes the commands in commandList, and returns data specified
    in the returnDict.
    '''
    def __init__(self,json_object):
        self.json_object = json_object
        self.dataDict = {}
        self.parsedDataDict = {}
        self.commandList = []
        self.errorList = []
        self.returnDict = {}
        if "dataDict" in self.json_object.keys():
            self.dataDict = json_object['dataDict']
            self._parseData()
        if "commandList" in self.json_object.keys():
            self.commandList = self.json_object['commandList']
        if "returnDict" in self.json_object.keys():
            self.returnDict = self.json_object['returnDict']
      
    def addError(self, errorString, exceptionObj = None):
        '''
        adds an error to the errorList array and prints the whole error to strerr
        so both the user and the administrator know
        '''      
        print (isinstance(errorString, unicode))
        self.errorList.append(errorString)
        sys.stderr.write(errorString)
        if exceptionObj is not None:
            sys.stderr.write(unicode(exceptionObj))
        traceback.print_exc(file=sys.stderr)

    def _parseData(self):
        '''
        Parses data specified as strings in self.dataDict into objects in self.parsedDataDict
        '''
        for (name,dataDictElement) in self.dataDict.iteritems():
            if 'data' not in dataDictElement.keys():
                self.addError("no data specified for data element "+unicode(dataDictElement))
                continue

            dataStr = dataDictElement['data']

            if 'fmt' in dataDictElement.keys():
                fmt = dataDictElement['fmt']
                
                if name in self.parsedDataDict.keys():
                    self.addError("duplicate definition for data named "+str(name)+" "+str(dataDictElement))
                    continue
                if fmt not in availableDataFormats:
                    self.addError("invalid data format for data element "+str(dataDictElement))
                    continue
                
                if fmt == 'string' or fmt == 'str':
                    if dataStr.count("'") == 2: # Single Quoted String
                        data = dataStr.replace("'","") # remove excess quotes
                    elif dataStr.count("\"") == 2: # Double Quoted String
                        data = dataStr.replace("\"","") # remove excess quotes
                    else:
                        self.addError("invalid string (not in quotes...) for data element "+str(dataDictElement))
                        continue
                elif fmt == 'int':
                    try:
                        data = int(dataStr)
                    except:
                        self.addError("invalid integer for data element "+str(dataDictElement))
                        continue
                elif fmt in ['bool','boolean']:
                    if dataStr in ['true','True']:
                        data = True
                    elif dataStr in ['false','False']:
                        data = False
                    else:
                        self.addError("invalid boolean for data element "+str(dataDictElement))
                        continue
                elif fmt == 'list':
                    # in this case dataStr should actually be an list object.
                    if not common.isListLike(dataStr):
                        self.addError("list format must actually be a list structure "+str(dataDictElement))
                        continue
                    data = []
                    for elementStr in dataStr:
                        if common.isStr(elementStr):
                            (matchFound, dataElement) = self.parseStringToPrimitive(elementStr)
                            if not matchFound:
                                self.addError("format could not be detected for data element  "+str(elementStr))
                                continue
                        else:
                            dataElement = elementStr
                        data.append(dataElement)
                else:
                    if fmt in ['xml','musicxml']:                
                        if dataStr.find("<!DOCTYPE") == -1:
                            dataStr = """<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">""" + dataStr
                        if dataStr.find("<?xml") == -1:
                            dataStr = """<?xml version="1.0" encoding="UTF-8"?>""" + dataStr
                    try:
                        data = converter.parseData(dataStr)
                    except converter.ConverterException as e:
                        #self.addError("Error parsing data variable "+name+": "+str(e)+"\n\n"+dataStr)
                        self.addError("Error parsing data variable "+name+": "+unicode(e)+"\n\n"+dataStr,e)
                        continue
            else: # No format specified
                (matchFound, data) = self.parseStringToPrimitive(dataStr)
                if not matchFound:
                    self.addError("format could not be detected for data element  "+str(dataDictElement))
                    continue
                
            self.parsedDataDict[name] = data
                
            
    def executeCommands(self):
        '''
        Parses JSON Commands specified in the self.commandList
        
        In the JSON, commands are described by::

            {"commandList:"[
                {"function":"corpus.parse",
                 "argList":["'bwv7.7'"],
                 "resultVariable":"sc"},
                 
                {"function":"transpose",
                 "caller":"sc",
                 "argList":["'p5'"],
                 "resultVariable":"sc"},
                 
                
                {"attribute":"flat",
                 "caller":"sc",
                 "resultVariable":"scFlat"},
                 
                {"attribute":"higestOffset",
                 "caller":"scFlat",
                 "resultVariable":"ho"}
                 ]
            }

        '''
        
        for commandElement in self.commandList:
            if 'function' in commandElement.keys() and 'attribute'  in commandElement.keys():
                self.addError("cannot specify both function and attribute for:  "+str(commandElement))
                continue
            
            if 'function' in commandElement.keys():
                functionName = commandElement['function']
                
                if functionName not in availableFunctions:
                    self.addError("unknown function "+str(functionName)+" :"+str(commandElement))
                    continue
                
                if 'argList' not in commandElement.keys():
                    argList = []
                else:
                    argList = commandElement['argList']
                    for (i,arg) in enumerate(argList):
                        (matchFound, parsedArg) = self.parseStringToPrimitive(arg)
                        if not matchFound:
                            self.addError("invalid argument "+str(arg)+" :"+str(commandElement))
                            continue
                        argList[i] = parsedArg

                if 'caller' in commandElement.keys(): # Caller Specified
                    callerName = commandElement['caller']
                    if callerName not in self.parsedDataDict.keys():
                        self.addError(callerName+" not defined "+str(commandElement))
                        continue
                    try:
                        result = eval("self.parsedDataDict[callerName]."+functionName+"(*argList)")
                    except Exception as e:
                        self.addError("Error: "+str(e)+" executing function "+str(functionName)+" :"+str(commandElement))
                        continue
                    
                    
                else: # No caller specified
                    result = eval(functionName)(*argList)
                
                if 'resultVariable' in commandElement.keys():
                    resultVarName = commandElement['resultVariable']
                    self.parsedDataDict[resultVarName] = result
                    
            elif 'attribute' in commandElement.keys():
                attribtueName = commandElement['attribute']
                
                if attribtueName not in availableAttribtues:
                    self.addError("unknown attribute "+str(attribtueName)+" :"+str(commandElement))
                    continue
                
                if 'args'  in commandElement.keys():
                    self.addError("No args should be specified with attribute :"+str(commandElement))
                    continue
                
                if 'caller' in commandElement.keys(): # Caller Specified
                    callerName = commandElement['caller']
                    if callerName not in self.parsedDataDict.keys():
                        self.addError(callerName+" not defined "+str(commandElement))
                        continue
                    result = eval("self.parsedDataDict[callerName]."+attribtueName)
                    
                else: # No caller specified
                    self.addError("Caller must be specified with attribute :"+str(commandElement))
                    continue

                if 'resultVariable' in commandElement.keys():
                    resultVarName = commandElement['resultVariable']
                    self.parsedDataDict[resultVarName] = result
                    
            else:
                self.addError("must specify function or attribute for:  "+str(commandElement))
                continue
            
    def getResultObject(self):
        '''
        Returns a new object ready for json parsing with the string values of the objects
        specified in self.returnDict in the formats specified in self.returnDict::
        
            "returnDict":{
                "myNum" : "int",
                "ho"    : "int"
            }
        '''
        return_obj = {};
        return_obj['status'] = "success"
        return_obj['dataDict'] = {}
        return_obj['errorList'] = []
        
        if len(self.errorList) > 0:
            return_obj['status'] = "error"
            return_obj['errorList'] = self.errorList
            return return_obj
        
        for (dataName,fmt) in self.returnDict.iteritems():
            if dataName not in self.parsedDataDict.keys():
                self.addError("Data element "+dataName+" not defined at time of return");
                continue
            if fmt not in availableDataFormats:
                self.addError("Format "+fmt+" not available");
                continue
            
            data = self.parsedDataDict[dataName]
            
            if fmt == 'string' or fmt == 'str':
                dataStr = str(data)
            elif fmt == 'musicxml':
                dataStr = data.musicxml
            elif fmt == 'reprtext':
                dataStr = data._reprText()
            else:
                dataStr = str(data)
                
            return_obj['dataDict'][dataName] = {"fmt":fmt, "data":dataStr}
            
        
        if len(self.errorList) > 0:
            return_obj['status'] = "error"
            return_obj['errorList'] = self.errorList
            return return_obj
        
        return return_obj
    
    def getErrorStr(self):
        '''
        Converts self.errorList into a string
        '''
        errorStr = ""
        for e in self.errorList:
            errorStr += e + "\n"
        return errorStr
    
    def parseStringToPrimitive(self, strVal):
        returnVal = None
        foundMatch = False
        
        if strVal in self.parsedDataDict.keys():
            returnVal = self.parsedDataDict[strVal]
            foundMatch = True
        else:
            try:
                returnVal = int(strVal)
                foundMatch = True
            except:
                try:
                    returnVal = float(strVal)
                    foundMatch = True
                except:
                    if strVal == "True":
                        returnVal = True
                        foundMatch = True
                    elif strVal == "None":
                        returnVal = None
                        foundMatch = True
                    elif strVal == "False":
                        foundMatch = True
                        returnVal = False
                    elif strVal.count("'") == 2: # Single Quoted String
                        returnVal = strVal.replace("'","") # remove excess quotes
                        foundMatch = True
                    elif strVal.count("\"") == 2: # Double Quoted String
                        returnVal = strVal.replace("\"","") # remove excess quotes
                        foundMatch = True
        if foundMatch:
            return (True, returnVal)
        else:
            return (False, None)
        
        
# -------------------
# URL Application
# -------------------
def music21ModWSGIURLApplication(environ, start_response):
    '''
    Application function in proper format for a MOD-WSGI Application:
    Reads the contents of a post request, and passes the JSON string to
    webapps.processJSONData for further processing. 
    Returns a proper HTML response.
    
    An interface for music21 using mod_wsgi
    
    To use, first install mod_wsgi and include it in the HTTPD.conf file.
    
    Add this file to the server, ideally not in the document root, 
    on mac this could be /Library/WebServer/wsgi-scripts/music21wsgiapp.py
    
    Then edit the HTTPD.conf file to redirect any requests to WEBSERVER:/music21interface to call this file:
    
    WSGIScriptAlias /music21interface /Library/WebServer/wsgi-scripts/music21wsgiapp.py
    
    Further down the conf file, give the webserver access to this directory:
    
    <Directory "/Library/WebServer/wsgi-scripts">
        Order allow,deny
        Allow from all
    </Directory>
    
    The mod_wsgi handler will call the application function below with the request
    content in the environ variable.
    
    To use the post, send a POST request to WEBSERVER:/music21interface
    where the contents of the POST is a JSON string.
    
    See processJSONSTring below for specifications about the structure of this string.
    '''
    status = '200 OK'

    pathInfo = environ['PATH_INFO'] # Contents of path after mount point of wsgi app but before question mark
    queryString = environ['QUERY_STRING'] # Contents of URL after question mark    
    documentRoot = environ['DOCUMENT_ROOT'] # Document root of the server
    
    resultStr = ""
        
    for (k,v) in environ.iteritems():
        resultStr += "\n"+str(k)+": "+str(v)+"\n"

    response_headers = [('Content-type', 'text/plain'),
            ('Content-Length', str(len(resultStr)))]

    start_response(status, response_headers)

    return [resultStr]

def music21ModWSGIFileApplication(environ, start_response):
    '''
    Application function in proper format for a MOD-WSGI Application:
    Reads the contents of a post request, and passes the JSON string to
    webapps.processJSONData for further processing. 
    Returns a proper HTML response.
    
    An interface for music21 using mod_wsgi
    
    To use, first install mod_wsgi and include it in the HTTPD.conf file.
    
    Add this file to the server, ideally not in the document root, 
    on mac this could be /Library/WebServer/wsgi-scripts/music21wsgiapp.py
    
    Then edit the HTTPD.conf file to redirect any requests to WEBSERVER:/music21interface to call this file:
    
    WSGIScriptAlias /music21interface /Library/WebServer/wsgi-scripts/music21wsgiapp.py
    
    Further down the conf file, give the webserver access to this directory:
    
    <Directory "/Library/WebServer/wsgi-scripts">
        Order allow,deny
        Allow from all
    </Directory>
    
    The mod_wsgi handler will call the application function below with the request
    content in the environ variable.
    
    To use the post, send a POST request to WEBSERVER:/music21interface
    where the contents of the POST is a JSON string.
    
    See processJSONSTring below for specifications about the structure of this string.
    '''
    status = '200 OK'

    formFields = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)


    resultStr = ""
    
    fileData = formFields['file1'].file.read()
    
    uploadedFile = formFields['file1'].file
    filename = formFields['file1'].filename
    type = formFields['file1'].type
    
    resultStr += str(filename)+ "\n"
    
    resultStr += uploadedFile.read()


    response_headers = [('Content-type', 'text/plain'), 
            ('Content-Length', str(len(resultStr)))]

    start_response(status, response_headers)

    return [resultStr]

## Shortcuts - temporary procedures used for re-implementation of hackday demo. Will be moved 
## to new home or removed when commandList can accommodate more complex structures (arrays, for loops...)

def reduction(sc):
    '''
    Procedure that returns the annotated reduction of the given score. 
    '''
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    return reductionStream

def createMensuralCanon(sc):
    '''
    Implements music21 example of creating a mensural canon

    '''
    melody = sc.parts[0].flat.notesAndRests
    
    canonStream = stream.Score()
    for scalar, t in [(1, 'p1'), (2, 'p-5'), (.5, 'p-11'), (1.5, -24)]:
        part = melody.augmentOrDiminish(scalar, inPlace=False)
        part.transpose(t, inPlace=True)
        canonStream.insert(0, part)
    
    return canonStream

def checkLeadSheetPitches(sc, returnType=''):
    '''
    Beth's code for chord symbols: returns answer if returnType = 'answerkey'
    '''
    nicePiece = sc
    incorrectPiece = sc
    
    #incorrectPiece = messageconverter.parse('C:\Users\sample.xml')
    
    sopranoLine = nicePiece.getElementsByClass(stream.Part)[0]
    chordLine = nicePiece.getElementsByClass(stream.Part)[1]
    #chordLine.show('text')
    #bassLine = nicePiece.part(2)
    onlyChordSymbols = sopranoLine.flat.getElementsByClass(harmony.ChordSymbol)
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

    
    return returnScore

def colorAllNotes(sc, color):
    '''
    Iterate through all notes and change their color to the given color - 
    used for testing color rendering in noteflight
    '''
    for n in sc.flat.getElementsByClass('Note'):
        n.color = color 
    return sc

def colorAllChords(sc, color):
    '''
    Iterate through all chords and change their color to the given color - 
    used for testing color rendering in noteflight
    '''
    for c in sc.flat.getElementsByClass('Chord'):
        c.color = color 
    return sc

def writeMIDIFileToServer(sc):
    '''
    Iterate through all notes and change their color to the given color - 
    used for testing color rendering in noteflight
    '''
    #documentRoot = environ['DOCUMENT_ROOT']
    documentRoot = '/Library/WebServer/Documents'
    urlPath = "/music21/OutputFiles/cognitionEx.mid"
    writePath = documentRoot + urlPath
    
    sc.write('mid',writePath)
    
    return urlPath
    

## Tests 

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testAgendaDict(self):
        jsonString = r'''
        {
    "dataDict": {
        "myNum":
            {"fmt" : "int",
             "data" : "23"}
    },
    "commandList":[
        {"function":"corpus.parse",
         "argList":["'bwv7.7'"],
         "resultVariable":"sc"},
         
        {"function":"transpose",
         "caller":"sc",
         "argList":["'p5'"],
         "resultVariable":"sc"},
         
    
        {"attribute":"flat",
         "caller":"sc",
         "resultVariable":"scFlat"},
         
        {"attribute":"highestOffset",
         "caller":"scFlat",
         "resultVariable":"ho"}
    ],
    "returnDict":{
        "myNum" : "int",
        "ho"    : "int"
        }
    }
    '''
        ad = AgendaDict()
        ad.loadJson(jsonString)
        self.assertEqual(ad['dataDict']['myNum']['data'], "23")

#def fixXML(xmlStr):
#    startOffset = 0
#    while startOffset < len(xmlStr):
#        xmlStr.find('color = ')
#        

if __name__ == '__main__':
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof