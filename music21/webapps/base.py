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

import music21
from music21 import common
from music21 import converter
from music21 import stream
from music21 import corpus

import json


availableDataFormats = ['xml',
                        'musicxml',
                        'abc',
                        'str',
                        'string',
                        'int',
                        'reprtext']

availableFunctions = ['stream.transpose',
                      'corpus.parse',
                      'transpose',
                      'augmentOrDiminish',]

availableAttribtues = ['highestOffset',
                       'flat']

def modWSGIapplication(environ, start_response):
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
    "returnList":[
        {"name":"myNum",
         "fmt" : "int" },
        {"name":"ho",
         "fmt" : "int" }
    ]
    }
    
    '''
    request_obj = RequestObject(json.loads(json_request_str))
    request_obj.executeCommands()
    result_obj = request_obj.getResultObject();
    json_result_str = json.dumps(result_obj)
    return json_result_str


class RequestObject():
    '''
    Object used to coordinate JSON requests to music21.
    
    Takes a json string as input, parses data specified in dataDict,
    executes the commands in commandList, and returns data specified
    in the returnList.
    '''
    def __init__(self,json_object):
        self.json_object = json_object
        self.dataDict = {}
        self.parsedDataDict = {}
        self.commandList = []
        self.errorList = []
        self.returnList = []
        if "dataDict" in self.json_object.keys():
            self.dataDict = json_object['dataDict']
            self._parseData()
        if "commandList" in self.json_object.keys():
            self.commandList = self.json_object['commandList']
        if "returnList" in self.json_object.keys():
            self.returnList = self.json_object['returnList']
                        
    def _parseData(self):
        '''
        Parses data specified as strings in self.dataDict into objects in self.parsedDataDict
        '''
        for (name,dataDictElement) in self.dataDict.iteritems():
            if 'fmt' not in dataDictElement.keys():
                self.errorList.append("no format specified for data element "+str(dataDictElement))
                continue
            if 'data' not in dataDictElement.keys():
                self.errorList.append("no data specified for data element "+str(dataDictElement))
                continue
            
            fmt = dataDictElement['fmt']
            dataStr = dataDictElement['data']
            
            if name in self.parsedDataDict.keys():
                self.errorList.append("duplicate definition for data named "+str(name)+" "+str(dataDictElement))
                continue
            if fmt not in availableDataFormats:
                self.errorList.append("invalid data format for data element "+str(dataDictElement))
                continue
            
            if fmt == 'string' or fmt == 'str':
                data = str(dataStr)
            elif fmt == 'int':
                data = int(dataStr)
            else:
                if fmt in ['xml','musicxml']:                
                    if dataStr.find("<!DOCTYPE") == -1:
                        dataStr = """<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">""" + dataStr
                    if dataStr.find("<?xml") == -1:
                        dataStr = """<?xml version="1.0" encoding="UTF-8"?>""" + dataStr
                
                data = converter.parseData(dataStr)
                
            self.parsedDataDict[name] = data
                
            
    def executeCommands(self):
        '''
        Parses JSON Commands specified in the self.commandList
        
        In the JSON, commands are described by:
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
                self.errorList.append("cannot specify both function and attribute for:  "+str(commandElement))
                continue
            
            if 'function' in commandElement.keys():
                functionName = commandElement['function']
                
                if functionName not in availableFunctions:
                    self.errorList.append("unknown function "+str(functionName)+" :"+str(commandElement))
                    continue
                
                if 'argList' not in commandElement.keys():
                    argList = []
                else:
                    argList = commandElement['argList']
                    for (i,arg) in enumerate(argList):
                        if arg in self.parsedDataDict.keys():
                            argList[i] = self.parsedDataDict[arg]
                        else:
                            argList[i] = eval(arg)
                
                if 'caller' in commandElement.keys(): # Caller Specified
                    callerName = commandElement['caller']
                    if callerName not in self.parsedDataDict.keys():
                        self.errorList.append(callerName+" not defined "+str(commandElement))
                        continue
                    result = eval("self.parsedDataDict[callerName]."+functionName+"(*argList)")
                    
                else: # No caller specified
                    result = eval(functionName)(*argList)
                
                if 'resultVariable' in commandElement.keys():
                    resultVarName = commandElement['resultVariable']
                    self.parsedDataDict[resultVarName] = result
                    
            elif 'attribute' in commandElement.keys():
                attribtueName = commandElement['attribute']
                
                if attribtueName not in availableAttribtues:
                    self.errorList.append("unknown attribute "+str(attribtueName)+" :"+str(commandElement))
                    continue
                
                if 'args'  in commandElement.keys():
                    self.errorList.append("No args should be specified with attribute :"+str(commandElement))
                    continue
                
                if 'caller' in commandElement.keys(): # Caller Specified
                    callerName = commandElement['caller']
                    if callerName not in self.parsedDataDict.keys():
                        self.errorList.append(callerName+" not defined "+str(commandElement))
                        continue
                    result = eval("self.parsedDataDict[callerName]."+attribtueName)
                    
                else: # No caller specified
                    self.errorList.append("Caller must be specified with attribute :"+str(commandElement))
                    continue

                if 'resultVariable' in commandElement.keys():
                    resultVarName = commandElement['resultVariable']
                    self.parsedDataDict[resultVarName] = result
                    
            else:
                self.errorList.append("must specify function or attribute for:  "+str(commandElement))
                continue
            
    def getResultObject(self):
        '''
        Returns a new object ready for json parsing with the string values of the objects
        specified in self.returnList in the formats specified in self.returnList.
        
        "returnList":[
            {"name":"myNum",
             "fmt" : "int" },
            {"name":"ho",
             "fmt" : "int" }
        ]
        '''
        return_obj = {};
        return_obj['status'] = "success"
        return_obj['dataDict'] = {}
        return_obj['errorList'] = []
        
        if len(self.errorList) > 0:
            return_obj['status'] = "error"
            return_obj['errorList'] = self.errorList
            return return_obj
        
        for returnElement in self.returnList:
            if 'name' not in returnElement.keys():
                self.errorList.append("must specify data name for:  "+str(returnElement))
                continue
            if 'fmt' not in returnElement.keys():
                self.errorList.append("no format specified for return element "+str(returnElement))
                continue
            dataName = returnElement['name']
            fmt = returnElement['fmt']
            if dataName not in self.parsedDataDict.keys():
                self.errorList.append("Data element "+dataName+" not defined at time of return");
                continue
            if fmt not in availableDataFormats:
                self.errorList.append("Format "+fmt+" not available");
                continue
            
            data = self.parsedDataDict[dataName]
            
            if fmt == 'string' or fmt == 'str':
                dataStr = str(data)
            elif fmt == 'xml':
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