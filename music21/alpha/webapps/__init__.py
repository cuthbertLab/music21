# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         webapps/__init__.py
# Purpose:      music21 functions for implementing web interfaces
#
# Authors:      Lars Johnson
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2012-14 The music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Webapps is a module designed for using music21 with a webserver.

This file includes the classes and functions used to parse and process requests to music21 running on a server.

For information about how to set up a server to use music21, look at the files in webapps.server
For examples of application-specific commands and templates, see webapps.apps
For details about various output template options available, see webapps.templates

**Overview of Processing a Request**

1. The GET and POST data from the request are combined into an agenda object. 
The POST data can be in the formats ``'application/json', 'multipart/form-data' or 
'application/x-www-form-urlencoded'``. 
For more information, see the documentation for Agenda and makeAgendaFromRequest

2. If an appName is specified, additional data and commands are added to the agenda. 
For more information, see the applicationInitializers in apps.py.

3. A CommandProcessor is created for the agenda

4. The processor parses its dataDict into primitives or music21 objects and saves them 
to a parsedDataDict. For more information, see ``commandProcessor._parseData()``

5. The processor executes its commandList, modifying its internal parsedDataDict. 
For more information, see :meth:`~music21.webapps.CommandProcessor.executeCommands`

6. If outputTemplate is specified, the processor uses a template to generate and output. 
For more information, see :meth:`~music21.webapps.CommandProcessor.getOutput` and the templates in templates.py

7. Otherwise, the data will be returned as JSON, where the variables in the agenda's 
returnDict specify which variables to include in the returned JSON.

8. If an error occurs, an error message will be returned to the user 

**Full JSON Example:**

Below is an example of a complete JSON request::

    {
        "dataDict": {
            "myNum": {
                "fmt": "int", 
                "data": "23"
            }
        }, 
        "returnDict": {
            "myNum": "int", 
            "ho": "int"
        }, 
        "commandList": [
            {
                "function": "corpus.parse", 
                "argList": [
                    "'bwv7.7'"
                ], 
                "resultVar": "sc"
            }, 
            {
                "method": "transpose", 
                "argList": [
                    "'p5'"
                ], 
                "caller": "sc", 
                "resultVar": "sc"
            }, 
            {
                "attribute": "flat", 
                "caller": "sc", 
                "resultVar": "scFlat"
            }, 
            {
                "attribute": "highestOffset", 
                "caller": "scFlat", 
                "resultVar": "ho"
            }
        ]
    }
    
'''
import collections
import sys
import unittest

# music21 imports
from music21 import common
from music21 import converter
from music21 import stream #@UnusedImport
from music21 import corpus #@UnusedImport
from music21 import note #@UnusedImport
from music21 import features #@UnusedImport
from music21 import harmony #@UnusedImport
from music21 import clef #@UnusedImport
from music21 import tempo #@UnusedImport
from music21.alpha.theoryAnalysis import theoryAnalyzer #@UnusedImport

from music21.ext import six

if six.PY2:
    import apps
    import commands
    import templates
else:
    from music21.alpha.webapps import templates # @Reimport
    from music21.alpha.webapps import apps      # @Reimport
    from music21.alpha.webapps import commands  # @Reimport

# python library imports
import json
import zipfile #@UnusedImport
import cgi
try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse
import re #@UnusedImport
import traceback

from music21.ext.six import StringIO

if six.PY3:
    import io
    file = io.IOBase # @ReservedAssignment
    unicode = str # @ReservedAssignment
#-------------------------------------------------------------------------------

# Valid format types for data input to the server
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
                        'float',
                        'file']

# Commands of type function (no caller) must be in this list
availableFunctions = ['checkLeadSheetPitches',
                      'colorAllChords',
                      'colorAllNotes',
                      'colorResults',
                      'commands.generateIntervals',
                      'commands.reduction',
                      'commands.runPerceivedDissonanceAnalysis',
                      'commands.writeMIDIFileToServer',
                      'converter.parse',
                      'corpus.parse',
                      'createMensuralCanon',
                      'getResultsString',
                      'generateChords',
                      'reduction',
                      'stream.transpose',
                      'tempo.MetronomeMark',
                      'theoryAnalyzer.identifyHiddenFifths',
                      'theoryAnalyzer.identifyHiddenOctaves',
                      'theoryAnalyzer.identifyParallelFifths',
                      'theoryAnalyzer.identifyParallelOctaves',
                      ] 

# Commands of type method (have a caller) must be in this list
availableMethods = ['__getitem__',
                    'augmentOrDiminish',
                    'chordify',
                    'insert',
                    'measures',
                    'transpose'
                    ]

# Commands of type attribute must be in this list
availableAttribtues = ['highestOffset',
                       'flat',
                       '_theoryScore',
                       'musicxml']

# Commands of type attribute must be in this list
availableOutputTemplates = ['templates.noteflightEmbed',
                            'templates.musicxmlText',
                            'templates.musicxmlFile',
                            'templates.vexflow',
                            'templates.braille']

#-------------------------------------------------------------------------------

def ModWSGIApplication(environ, start_response):
    '''
    Application function in proper format for a mod_wsgi Application:
    Reads the contents of a post request, and passes the data string to
    webapps.processDataString for further processing. 
        
    For an example of how to install this application on a server see music21.webapps.server.wsgiapp.py
    
    The request to the application should have the following structures:

    >>> from music21.ext.six import StringIO
    >>> environ = {}              # environ is usually created by the server. Manually constructing dictionary for demonstrated
    >>> wsgiInput = StringIO()    # wsgi.input is usually a buffer containing the contents of a POST request. Using StringIO to demonstrate
    >>> unused = wsgiInput.write('{"dataDict":{"a":{"data":3}},"returnDict":{"a":"int"}}')
    >>> unused = wsgiInput.seek(0)
    >>> environ['wsgi.input'] = wsgiInput
    >>> environ['QUERY_STRING'] = ""
    >>> environ['DOCUMENT_ROOT'] = "/Library/WebServer/Documents"
    >>> environ['HTTP_HOST'] = "ciconia.mit.edu"
    >>> environ['SCRIPT_NAME'] = "/music21/unifiedinterface"
    >>> environ['CONTENT_TYPE'] = "application/json"
    >>> start_response = lambda status, headers: None         # usually called by mod_wsgi server. Used to initiate response
    >>> alpha.webapps.ModWSGIApplication(environ, start_response)
    [b'{"dataDict": {"a": {...}}, "errorList": [], "status": "success"}']
    '''    

    # Get content of request: is in a file-like object that will need to be .read() to get content
    requestFormat = str(environ.get("CONTENT_TYPE")).split(';')[0]
    requestInput = environ['wsgi.input']

    try:        
        agenda = makeAgendaFromRequest(requestInput,environ,requestFormat)
        processor = CommandProcessor(agenda)
        #(responseData, responseContentType) = (str(processor.parsedDataDict), 'text/plain')
        processor.executeCommands()
        (responseData, responseContentType) = processor.getOutput()
        
    # Handle any unexpected exceptions
    # TODO: Change output based on environment variables...
    except Exception as e:
        errorData = 'music21_server_error: %s\n' % e
        errorData += traceback.format_exc()
        sys.stderr.write(errorData)
        (responseData, responseContentType) = (errorData, 'text/plain')

    start_response('200 OK', [('Content-type', responseContentType),
                              ('Content-Length', str(len(responseData)))])

    return [responseData]

#-------------------------------------------------------------------------------

def makeAgendaFromRequest(requestInput, environ, requestType = None):
    '''
    Combines information from POST data and server info into an agenda object
    that can be used with the CommandProcessor.

    Takes in a file-like requestInput (has ``.read()``) containing POST data,
    a dictionary-like environ from the server containing at a minimum a value for the 
    keys QUERY_STRING,
    and a requestType specifying the content-type of the POST data 
    ('application/json','multipart/form-data', etc.)
        
    Note that variables specified via query string will be returned as a list if
    they are specified more than once (e.g. ``?b=3&b=4`` will yeld ``['3', '4']`` 
    as the value of b
    
    requestInput should be buffer from the server application. Using StringIO for demonstration
    
    >>> from music21.ext.six import StringIO
    >>> requestInput = StringIO()
    >>> unused = requestInput.write('{"dataDict":{"a":{"data":3}}}')
    >>> unused = requestInput.seek(0)
    >>> environ = {"QUERY_STRING":"b=3"}
    >>> agenda = alpha.webapps.makeAgendaFromRequest(requestInput, environ, 'application/json')

    >>> from pprint import pprint as pp
    >>> pp(agenda)
    {'commandList': [],
     'dataDict': {'a': {'data': 3}, 'b': {'data': '3'}},
     'returnDict': {}}

    (the ellipses above comment out the u unicode prefix in PY2)

    >>> environ2 = {"QUERY_STRING":"a=2&b=3&b=4"}
    >>> agenda2 = alpha.webapps.makeAgendaFromRequest(requestInput, environ2, 'multipart/form-data')

    Note that the 3 in a:data becomes '2' -- a string.
    
    >>> pp(agenda2)
    {'commandList': [],
     'dataDict': {'a': {'data': '2'}, 'b': {'data': ['3', '4']}},
     'returnDict': {}}
    '''
    
    agenda = Agenda()
    
    combinedFormFields = {}
    
    # Use requestType to process the POST data into the agenda
    if requestType is None:
        requestType = str(environ.get("CONTENT_TYPE")).split(';')[0]
    
    if requestType == 'application/json':
        combinedFormFields['json'] = requestInput.read()
    
    elif requestType == 'multipart/form-data':
        postFormFields = cgi.FieldStorage(requestInput, environ = environ)  
        for key in postFormFields:
            if hasattr(postFormFields[key],'filename') and postFormFields[key].filename != None: # Its an uploaded file
                value = postFormFields[key].file
            else:
                value = postFormFields.getlist(key)
                if len(value) == 1:
                    value = value[0]
            combinedFormFields[key] = value
            
    elif requestType == 'application/x-www-form-urlencoded':
        postFormFields =urlparse.parse_qs(requestInput.read())
        for (key, value) in postFormFields.items():
            if len(value) == 1:
                value = value[0]
            combinedFormFields[key] = value
       
    # Load json into the agenda first
    if 'json' in combinedFormFields:
        agenda.loadJson(combinedFormFields['json'])
        
    # Add GET fields:
    getFormFields = urlparse.parse_qs(environ['QUERY_STRING']) # Parse GET request in URL to dict
    for (key,value) in getFormFields.items():
        if len(value) == 1:
            value = value[0]
        combinedFormFields[key] = value

    # Add remaining form fields to agenda
    for (key, value) in combinedFormFields.items():
        if key in ['dataDict','commandList','returnDict','json']: # These values can only be specified via JSON, JSON already loaded
            pass
            
        elif key in ['appName','outputTemplate','outputArgList']:
            agenda[key] = value
            
        elif type(value) == file:
            agenda['dataDict'][key] = collections.OrderedDict([("data",value),
                                                               ("fmt","file")])
    
        else: # Put in data dict
            agenda['dataDict'][key] = {"data": value}
             
    
    # Allows the appName to direct final processing
    if 'appName' in agenda:
        setupApplication(agenda)
    
    return agenda


def setupApplication(agenda, appName = None):
    '''
    Given an agenda, determines which application is desired either from the appName parameter
    or if the appName parameter is none, from the value associated with the "appName" key in the agenda.
    
    If the application name is a valid application name, calls the appropriate application initializer
    from music21.webapps.apps.py on the agenda.
    '''
    if appName == None:
        if 'appName' in agenda:
            appName = agenda['appName']
        else:
            raise Exception("appName is None and no appName key in agenda.")
    
    if appName not in apps.applicationInitializers:
        raise Exception ("Unknown appName: " + appName)
    
    # Run initializer on agenda - edits it in place.
    apps.applicationInitializers[appName](agenda)


#-------------------------------------------------------------------------------

class Agenda(dict):
    '''
    Subclass of dictionary that represents data and commands to be processed by a CommandProcessor.
    
    The Agenda contains the following keys:
    
*   **'dataDict'** whose value is a dictionary specifying data to be input to the  processor of the form::
    
            "dataDict" : {"<VARIABLE_1_NAME>": {"data": "<VARIABLE_1_DATA>",
                                                "fmt":  "<VARIABLE_1_FMT>"},
                          "<VARIABLE_2_NAME>": {"data": "<VARIABLE_2_DATA>",
                                                "fmt":  "<VARIABLE_2_FMT>"},
                          etc.
                          }
        
    where the variable formats are elements of availableDataFormats ("str","int","musicxml", etc.)
    
*     **'commandList'**  whose value is a list specifying commands to be executed by the processor of the form::
    
            "commandList" : [{"<CMD_1_TYPE>": "<CMD_2_COMMAND_NAME>",
                              "resultVar":    "<CMD_1_RESULT_VARIABLE>",
                              "caller":       "<CMD_1_CALLER>",
                              "command":      "<CMD_1_COMMAND_NAME>",
                              "argList":      ['<CMD_1_ARG_1>','<CMD_1_ARG_2>'...]},
                              
                              "<CMD_2_TYPE>": "<CMD_2_COMMAND_NAME>",
                              "resultVar":    "<CMD_2_RESULT_VARIABLE>",
                              "caller":       "<CMD_2_CALLER>",
                              "argList":      ['<CMD_2_ARG_1>','<CMD_2_ARG_2>'...]},
                              etc.
                              ]
                              
    Calling :meth:`~music21.webapps.CommandProcessor.executeCommands` iterates through 
    the commandList sequentially, calling the equivalent of 
    ``<CMD_n_RESULT_VARAIBLE> = <CMD_n_CALLER>.<CMD_n_COMMAND_NAME>(<CMD_n_ARG_1>,<CMD_n_ARG_2>...)``
    where the command TYPE is "function", "method", or "attribute"
    
*    **'returnDict'** whose value is a list specifying the variables to be returned from the server::
    
            "returnDict" : {"<VARIABLE_1_NAME>": "<VARIABLE_1_FORMAT",
                            "<VARIABLE_2_NAME>": "<VARIABLE_2_FORMAT", etc.}
        
    returnDict is used to limit JSON output to only the relevant variables. If returnDict is not specified,
    the entire set of variables in the processor's environment will be returned in string format.
    
*    **'outputTemplate'**  which specifies the return template to be used
    
*    **'outputArgList'**   which specifies what arguments to pass the return template
    
    '''
    def __init__(self):
        '''
        Agenda initialization function:
        
        Initializes core key values 'dataDict', 'commandList', 'returnDict'

        >>> from pprint import pprint as pp
        >>> agenda = alpha.webapps.Agenda()
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {}, 'returnDict': {}}
        '''
        self['dataDict'] = dict()
        self['commandList'] = list()
        self['returnDict'] = dict()
        dict.__init__(self)
        
    def __setitem__(self, key, value):
        '''
        Raises an error if one attempts to set 'dataDict', 'returnDict', or 'commandList'
        to values that are not of the corresponding dict/list type.

        >>> from pprint import pprint as pp
        >>> agenda = alpha.webapps.Agenda()
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {}, 'returnDict': {}}
        >>> agenda['dataDict'] = {"a":{"data":2}}
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {'a': {'data': 2}}, 'returnDict': {}}
        '''
        if key in ['dataDict','returnDict'] and type(value) is not dict:
            raise Exception('value for key: '+ str(key) + ' must be dict')
            return
        
        elif key in ['commandList'] and type(value) is not list:
            raise Exception('value for key: '+ str(key) + ' must be list')
            return
        
        dict.__setitem__(self,key,value)
    
    def addData(self, variableName, data, fmt = None):
        '''
        Given a variable name, data, and optionally format, constructs the proper dataDictElement structure,
        and adds it to the dataDict of the agenda.
        
        >>> from pprint import pprint as pp
        >>> agenda = alpha.webapps.Agenda()
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {}, 'returnDict': {}}
        >>> agenda.addData('a', 2)
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {'a': {'data': 2}}, 'returnDict': {}}
        >>> agenda.addData(variableName='b', data=[1,2,3], fmt='list')
        >>> pp(agenda)
        {'commandList': [],
         'dataDict': {'a': {'data': 2}, 'b': {'data': [1, 2, 3], 'fmt': 'list'}},
         'returnDict': {}}
        '''
        dataDictElement = {}
        dataDictElement['data'] = data
        if fmt != None:
            dataDictElement['fmt'] = fmt
        self['dataDict'][variableName] = dataDictElement
        
    def getData(self, variableName):
        '''
        Given a variable name, returns the data stored in the agenda for that variable name. If no data is stored,
        returns the value None.        

        >>> from pprint import pprint as pp        
        >>> agenda = alpha.webapps.Agenda()
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {}, 'returnDict': {}}
        >>> agenda.getData('a') == None
        True
        >>> agenda.addData('a', 2)
        >>> agenda.getData('a')
        2
        '''
        if variableName in self['dataDict']:
            return self['dataDict'][variableName]['data']
        else:
            return None
        
    def addCommand(self, commandType, resultVar, caller, command, argList = None):
        '''
        Adds the specified command to the commandList of the agenda. `commandType` is either "function", "attribute" or method. 
        resultVar, caller, and command are strings that will result in the form shown below. Set an argument as 
        none to 
        argList should be a list of data encoded in an appropriate 
        format (see :meth:`~music21.webapps.CommandProcessor.parseInputToPrimitive` for more information)
        
            ``<resultVar> = <caller>.<command>(<argList>)``
        
        >>> from pprint import pprint as pp
        
        >>> agenda = alpha.webapps.Agenda()
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {}, 'returnDict': {}}
        >>> agenda.addCommand('method','sc','sc','transpose',['p5'])
        >>> pp(agenda)
        {'commandList': [{'argList': ['p5'],
                          'caller': 'sc',
                          'method': 'transpose',
                          'resultVar': 'sc'}],
         'dataDict': {},
         'returnDict': {}}
        >>> agenda.addCommand('attribute','scFlat','sc','flat')
        >>> pp(agenda)
        {'commandList': [{'argList': ['p5'],
                          'caller': 'sc',
                          'method': 'transpose',
                          'resultVar': 'sc'},
                         {'attribute': 'flat', 'caller': 'sc', 'resultVar': 'scFlat'}],
         'dataDict': {},
         'returnDict': {}}
        '''        
        commandListElement = {}
        commandListElement[commandType] = command
        if resultVar != None:
            commandListElement['resultVar'] = resultVar
        if caller != None:
            commandListElement['caller'] = caller
        if argList != None:
            commandListElement['argList'] = argList
            
        self['commandList'].append(commandListElement)
        
    def setOutputTemplate(self, outputTemplate, outputArgList):
        '''
        Specifies the output template that will be used for the agenda.
        
        >>> from pprint import pprint as pp ## pprint stablizes dictionary order
        
        >>> agenda = alpha.webapps.Agenda()
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {}, 'returnDict': {}}
        
        >>> agenda.setOutputTemplate('templates.noteflightEmbed',['sc'])
        >>> pp(agenda)
        {'commandList': [],
         'dataDict': {},
         'outputArgList': ['sc'],
         'outputTemplate': 'templates.noteflightEmbed',
         'returnDict': {}}
        '''
        self['outputTemplate'] = outputTemplate
        self['outputArgList'] = outputArgList
    
    def loadJson(self, jsonRequestStr):
        '''
        Runs json.loads on jsonRequestStr and loads the resulting structure into the agenda object.
        
        >>> from pprint import pprint as pp ## pprint stablizes dictionary order
        
        >>> agenda = alpha.webapps.Agenda()
        >>> pp(agenda)
        {'commandList': [], 'dataDict': {}, 'returnDict': {}}
        >>> agenda.loadJson(alpha.webapps.sampleJsonStringSimple)
        >>> pp(agenda)
        {'commandList': [],
         'dataDict': {'myNum': {'data': '23', 'fmt': 'int'}},
         'returnDict': {'myNum': 'int'}}
        '''
        tempDict = json.loads(jsonRequestStr)
        for (key, value) in tempDict.items():
#            if isinstance(key, unicode):
#                key = str(key)
#            if isinstance(value, unicode):
#                value = str(value)
            self[key] = value

        
#-------------------------------------------------------------------------------

class CommandProcessor(object):
    '''
    Processes server request for music21.
    
    Takes an Agenda (dict) as input, containing the keys::
    
        'dataDict'
        'commandList'
        'returnDict'
        'outputTemplate'
        'outputArgList'

    OMIT_FROM_DOCS
    
    TODO: MORE DOCS!
    '''
    def __init__(self,agenda):
        '''
        OMIT_FROM_DOCS
        Given an agenda 
        '''
        self.agenda = agenda
        self.rawDataDict = {}
        self.parsedDataDict = {}
        self.commandList = []
        self.errorList = []
        self.returnDict = {}
        self.outputTemplate = ""
        self.outputArgList = []
        
        if "dataDict" in agenda:
            self.rawDataDict = agenda['dataDict']
            self._parseData()
        
        if "commandList" in agenda:
            self.commandList = agenda['commandList']
        
        if "returnDict" in agenda:
            self.returnDict = agenda['returnDict']

        if "outputTemplate" in agenda:
            self.outputTemplate = agenda['outputTemplate']

        if "outputArgList" in agenda:
            self.outputArgList = agenda['outputArgList']
      
    def recordError(self, errorString, exceptionObj = None):
        '''
        Adds an error to the internal errorList array and prints the whole error to stderr
        so both the user and the administrator know. Error string represents a brief, human-readable
        message decribing the error.
        
        Errors are appended to the errorList as a tuple (errorString, errorTraceback) where errorTraceback
        is the traceback of the exception if exceptionObj is specified, otherwise errorTraceback is the empty string
        '''
        errorTraceback = u''    
        if exceptionObj is not None:
            errorTraceback += traceback.format_exc()
            
        errorString = errorString.encode('ascii','ignore')
        
        sys.stderr.write(errorString)
        sys.stderr.write(errorTraceback)
        self.errorList.append((('music21_server_error: '+errorString).encode('ascii','ignore'),errorTraceback.encode('ascii','ignore')))


    def _parseData(self):
        '''
        Parses data specified as strings in self.dataDict into objects in self.parsedDataDict
        '''
        for (name,dataDictElement) in self.rawDataDict.items():
            if 'data' not in dataDictElement:
                self.recordError("no data specified for data element "+unicode(dataDictElement))
                continue

            dataStr = dataDictElement['data']

            if 'fmt' in dataDictElement:
                fmt = dataDictElement['fmt']
                
                if name in self.parsedDataDict:
                    self.recordError("duplicate definition for data named "+str(name)+" "+str(dataDictElement))
                    continue
                if fmt not in availableDataFormats:
                    self.recordError("invalid data format for data element "+str(dataDictElement))
                    continue
                
                if fmt == 'string' or fmt == 'str':
                    if dataStr.count("'") == 2: # Single Quoted String
                        data = dataStr.replace("'","") # remove excess quotes
                    elif dataStr.count("\"") == 2: # Double Quoted String
                        data = dataStr.replace("\"","") # remove excess quotes
                    else:
                        self.recordError("invalid string (not in quotes...) for data element "+str(dataDictElement))
                        continue
                elif fmt == 'int':
                    try:
                        data = int(dataStr)
                    except:
                        self.recordError("invalid integer for data element "+str(dataDictElement))
                        continue
                elif fmt in ['bool','boolean']:
                    if dataStr in ['true','True']:
                        data = True
                    elif dataStr in ['false','False']:
                        data = False
                    else:
                        self.recordError("invalid boolean for data element "+str(dataDictElement))
                        continue
                elif fmt == 'list':
                    # in this case dataStr should actually be an list object.
                    if not common.isIterable(dataStr):
                        self.recordError("list format must actually be a list structure " + 
                                         str(dataDictElement))
                        continue
                    data = []
                    for elementStr in dataStr:
                        if common.isStr(elementStr):
                            dataElement = self.parseInputToPrimitive(elementStr)
                        else:
                            dataElement = elementStr
                        data.append(dataElement)
                elif fmt == 'file':
                    data = dataStr
                else:
                    if fmt in ['xml','musicxml']:                
                        if dataStr.find("<!DOCTYPE") == -1:
                            dataStr = """<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 1.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">""" + dataStr
                        if dataStr.find("<?xml") == -1:
                            dataStr = """<?xml version="1.0" encoding="UTF-8"?>""" + dataStr
                    try:
                        data = converter.parseData(dataStr)
                    except converter.ConverterException as e:
                        #self.recordError("Error parsing data variable "+name+": "+str(e)+"\n\n"+dataStr)
                        self.recordError("Error parsing data variable "+name+": "+unicode(e)+"\n\n"+dataStr,e)
                        continue
            else: # No format specified
                dataStr = str(dataStr)
                data = self.parseInputToPrimitive(dataStr)
                
                
            self.parsedDataDict[name] = data
                
            
    def executeCommands(self):
        '''
        Parses JSON Commands specified in the self.commandList
        
        In the JSON, commands are described by:
        
        **'commandList'**  whose value is a list specifying commands to be executed by the processor of the form::
        
                "commandList" : [{"<CMD_1_TYPE>": "<CMD_2_COMMAND_NAME>",
                                  "resultVar":    "<CMD_1_RESULT_VARIABLE>",
                                  "caller":       "<CMD_1_CALLER>",
                                  "command":      "<CMD_1_COMMAND_NAME>",
                                  "argList":      ['<CMD_1_ARG_1>','<CMD_1_ARG_2>'...]},
                                  
                                  "<CMD_2_TYPE>": "<CMD_2_COMMAND_NAME>",
                                  "resultVar":    "<CMD_2_RESULT_VARIABLE>",
                                  "caller":       "<CMD_2_CALLER>",
                                  "argList":      ['<CMD_2_ARG_1>','<CMD_2_ARG_2>'...]},
                                  etc.
                                  ]
                                  
        Calling .executeCommands() iterates through the commandList sequentially, calling the equivalent of::
                
                <CMD_n_RESULT_VARAIBLE> = <CMD_n_CALLER>.<CMD_n_COMMAND_NAME>(<CMD_n_ARG_1>,<CMD_n_ARG_2>...)
            
        where the command TYPE is "function" (no caller), "method" (has a caller), or "attribute"
            
        See :meth:`~music21.webapps.CommandProcessor.executeFunctionCommand`, :meth:`~music21.webapps.CommandProcessor.executeMethodCommand`, 
        and :meth:`~music21.webapps.CommandProcessor.executeAttributeCommand` for more information about the format
        required for those commands.
            
        EXAMPLE::
        
            {"commandList:"[
                {"function":"corpus.parse",
                 "argList":["'bwv7.7'"],
                 "resultVar":"sc"},
                 
                {"method":"transpose",
                 "caller":"sc",
                 "argList":["'p5'"],
                 "resultVar":"sc"},
                 
                
                {"attribute":"flat",
                 "caller":"sc",
                 "resultVar":"scFlat"},
                 
                {"attribute":"higestOffset",
                 "caller":"scFlat",
                 "resultVar":"ho"}
                 ]
            }

        '''
        
        for commandElement in self.commandList:
            typeKeysInCommandList = [k for k in commandElement if k in ['function', 'attribute', 'method']]
            if len(typeKeysInCommandList) != 1:
                self.recordError("Must have exactly one key denoting type ('function', 'attribute', or 'method'):  "+str(commandElement))
                continue
            commandType = typeKeysInCommandList[0]
            
            if commandType == 'function':
                self.executeFunctionCommand(commandElement)
            elif commandType == 'attribute':
                self.executeAttributeCommand(commandElement)
            elif  commandType == 'method':
                self.executeMethodCommand(commandElement)
            else:
                self.recordError("No type specified for:  "+str(commandElement))
                continue
        return
        
    def executeFunctionCommand(self, commandElement):
        '''
        Executes the function command specified by commandElement.
        
        Function command elements should be dictionaries of the form::
        
            {'function': "<FUNCTION_NAME>",
             'argList': ["<ARG_1>","<ARG_2>", etc.],
             'resultVar' : "<RESULT_VARIABLE>"}
         
        Executing it yields the equivalent of: ``<RESULT_VARIABLE> = <FUNCTION_NAME>(ARG_1, ARG_2, ...)``
        
        The keys argList and resultVar are optional. A commandElement without argList will just call ``<FUNCTION_NAME>()``
        with no arguments and a commandElement without resutlVar will not assign the result of the function to any variable.
        
        
        '''
        # Get function name
        if 'function' not in commandElement:
            self.recordError("No function specified for function command: "+str(commandElement))
            return
            
        functionName = commandElement['function']
        
        # Allows users to create aliases for functions via the dataDict.
        # i.e. processingCommand = commands.reduction
        # then calling a command element with processingCommand(sc) will yield
        # the same result as commands.reduction(sc)
        if functionName in self.parsedDataDict:
            functionName = self.parsedDataDict[functionName]
        
        # Make sure function is valid for processing on webserver
        if functionName not in availableFunctions:
            self.recordError("Function "+str(functionName)+" not available on webserver:"+str(commandElement))
            return
        
        # Process arguments
        if 'argList' not in commandElement:
            argList = []
        else:
            argList = commandElement['argList']
            for (i,arg) in enumerate(argList):
                parsedArg = self.parseInputToPrimitive(arg)
                argList[i] = parsedArg
        
        # Call the function
        try:
            result = eval(functionName)(*argList)  # safe because of check for functionName in availableFunctions
        except Exception as e:
            self.recordError("Error: "+str(e)+" executing function "+str(functionName)+" :"+str(commandElement))
            return
        
        # Save it if resutlVar specified
        if 'resultVar' in commandElement:
            resultVarName = commandElement['resultVar']
            self.parsedDataDict[resultVarName] = result
                   
            
    def executeAttributeCommand(self, commandElement):
        '''
        Executes the attribute command specified by commandElement

        Function command elements should be dictionaries of the form::
        
            {'attribute': "<ATTRIBUTE_NAME>",
             'caller': "<CALLER_VARIABLE>",
             'resultVar' : "<RESULT_VARIABLE>"}
         
        Executing it yields the equivalent of: ``<RESULT_VARIABLE> = <CALLER_VARIABLE>.<ATTRIBUTE_NAME>.``
        
        All three keys 'attributeName', 'caller', and 'resultVar' are required.

        ''' 
        # Make sure the appropriate keys are set:
        if 'attribute' not in commandElement:
            self.recordError("No attribute specified for attribute command: "+str(commandElement))
            return
        
        if 'caller' not in commandElement:
            self.recordError("calle must be specified with attribute :"+str(commandElement))
            return
        
        if 'resultVar' not in commandElement:
            self.recordError("resultVar must be specified with attribute :"+str(commandElement))
            return
        
        # Get attribute name
        attributeName = commandElement['attribute']
        
        # Make sure attribute is valid for processing on webserver
        if attributeName not in availableAttribtues:
            self.recordError("Attribute "+str(attributeName)+" not available on webserver :"+str(commandElement))
            return
        
        # Get the caller and result variable names
        callerName = commandElement['caller']
        resultVarName = commandElement['resultVar']

        # Make sure the caller is defined        
        if callerName not in self.parsedDataDict:
            self.recordError(callerName+" not defined "+str(commandElement))
            return
        
        # Check that the caller has the desired attribute
        caller = self.parsedDataDict[callerName]
        if not hasattr(caller, attributeName):
            self.recordError("caller "+str(callerName)+": "+str(caller) +" has no attribute "+str(attributeName)+": "+str(commandElement))
            return
    
        self.parsedDataDict[resultVarName] = getattr(caller, attributeName)
            
    def executeMethodCommand(self, commandElement):
        '''
        Example::
        
            {'method': "<METHOD_NAME>",
             'caller': "<CALLER_VARIABLE>",
             'argList': ["<ARG_1>","<ARG_2>", etc.],
             'resultVar' : "<RESULT_VARIABLE>"}
         
        Executing it yields the equivalent of ``<RESULT_VARIABLE> = <CALLER_VARIABLE>.<METHOD_NAME>(ARG_1, ARG_2, ...)``
        
        The keys argList and resultVar are optional. A commandElement without argList will just call ``<CALLER_VARIABLE>.<METHOD_NAME>()``
        with no arguments and a commandElement without resutlVar will not assign the result of the function to any variable.
        
        ''' 
        # Make sure the appropriate keys are set:
        if 'method' not in commandElement:
            self.recordError("No methodName specified for method command: "+str(commandElement))
            return
        if 'caller' not in commandElement:
            self.recordError("No caller specified for method command: "+str(commandElement))
            return
        
        # Get method name and caller name
        methodName = commandElement['method']        
        callerName = commandElement['caller']
        
        # Make sure the method is valid for processing on webserver
        if methodName not in availableMethods:
            self.recordError("Method "+str(methodName)+" not available on webserver :"+str(commandElement))
            return
    
        # Process arguments
        if 'argList' not in commandElement:
            argList = []
        else:
            argList = commandElement['argList']
            for (i,arg) in enumerate(argList):
                parsedArg = self.parseInputToPrimitive(arg)
                argList[i] = parsedArg

        # Make sure the caller is defined        
        if callerName not in self.parsedDataDict:
            self.recordError(callerName+" not defined "+str(commandElement))
            return
        
        # Check that the caller has the desired method
        caller = self.parsedDataDict[callerName]
        if not hasattr(caller, methodName):
            self.recordError("caller "+str(callerName)+": "+str(caller) +" has no method "+str(methodName)+": "+str(commandElement))
            return
        
        if not callable(getattr(caller, methodName)):
            self.recordError(str(callerName)+"."+str(methodName) +" is not callable: "+str(commandElement))
            return

        # Call the method        
        try:
            result = getattr(caller, methodName)(*argList)
        except Exception:
            exc_type, unused_exc_obj, unused_exc_tb = sys.exc_info()
            self.recordError("Error: "+str(exc_type)+" executing method "+str(methodName)+" :"+str(commandElement))
            return
        
        # Save it if resutlVar specified
        if 'resultVar' in commandElement:
            resultVarName = commandElement['resultVar']
            self.parsedDataDict[resultVarName] = result
                      
    def getResultObject(self):
        '''
        Returns a new object ready for json parsing with the string values of the objects
        specified in self.returnDict in the formats specified in self.returnDict::
        
            "returnDict":{
                "myNum" : "int",
                "ho"    : "int"
            }
        '''
        return_obj = {}
        return_obj['status'] = "success"
        return_obj['dataDict'] = {}
        return_obj['errorList'] = []
        
        if len(self.errorList) > 0:
            return_obj['status'] = "error"
            return_obj['errorList'] = self.errorList
            return return_obj
        
        if len(self.returnDict) == 0:
            iterItems = [(k, 'str') for k in sorted(list(self.parsedDataDict.items()))]
        else:
            iterItems = sorted(list(self.returnDict.items()))
        
        for (dataName,fmt) in iterItems:
            if dataName not in self.parsedDataDict:
                self.recordError("Data element "+dataName+" not defined at time of return")
                continue
            if fmt not in availableDataFormats:
                self.recordError("Format "+fmt+" not available")
                continue
            
            data = self.parsedDataDict[dataName]
            
            if fmt == 'string' or fmt == 'str':
                dataStr = str(data)
            elif fmt == 'musicxml':
                dataStr = data.musicxml
            elif fmt == 'reprtext':
                dataStr = data._reprText()
            else:
                dataStr = unicode(data)
                
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
    
    def parseInputToPrimitive(self, inpVal):
        '''
        Determines what format a given input is in and returns a value in that format..
        First checks if it is the name of a variable defined in the parsedDataDict or the
        name of an allowable function. In either of these cases, it will return the actual value
        of the data or the actual function.
        
        Next, it will check if the string is an int, float, boolean, or none, returning the appropriate value.
        If it is a quoted string then it will remove the quotes on the ends and return it as a string.
        If it has square braces indicating a list, the inner elements will be parsed using this same function recursively.
        (Note that recursive lists like [1, 2, [3, 4]] are not yet supported
        
        If the input corresponds to none of these types, it is returned as a string.
        
        
        >>> agenda = alpha.webapps.Agenda()
        >>> agenda.addData("a",2)
        >>> agenda.addData("b",[1,2,3],"list")

        >>> processor = alpha.webapps.CommandProcessor(agenda)
        >>> processor.parseInputToPrimitive("a")
        2
        >>> processor.parseInputToPrimitive("b")
        [1, 2, 3]
        >>> processor.parseInputToPrimitive("1.0")
        1.0
        >>> processor.parseInputToPrimitive("2")
        2
        >>> processor.parseInputToPrimitive("True")
        True
        >>> processor.parseInputToPrimitive("False")
        False
        >>> processor.parseInputToPrimitive("None") == None
        True
        >>> processor.parseInputToPrimitive("'hi'")
        'hi'
        >>> processor.parseInputToPrimitive("'Madam I\'m Adam'")
        "Madam I'm Adam"
        >>> processor.parseInputToPrimitive("[1,2,3]")
        [1, 2, 3]
        >>> processor.parseInputToPrimitive("[1,'hi',3.0,True, a, justAStr]")
        [1, 'hi', 3.0, True, 2, 'justAStr']
        '''
        returnVal = None
        
        if common.isNum(inpVal):
            return inpVal
        
        if common.isIterable(inpVal):
            return [self.parseInputToPrimitive(element) for element in inpVal]
        
        if not common.isStr(inpVal):
            self.recordError("Unknown type for parseInputToPrimitive "+str(inpVal))
        
        strVal = inpVal
        
        strVal = strVal.strip() # removes whitespace on ends
        
        if strVal in self.parsedDataDict: # Used to specify data via variable name
            returnVal = self.parsedDataDict[strVal]
        elif strVal in availableFunctions: # Used to specify function via variable name
            returnVal = strVal
        else:
            try:
                returnVal = int(strVal)
            except:
                try:
                    returnVal = float(strVal)
                except:
                    if strVal == "True":
                        returnVal = True
                        
                    elif strVal == "None":
                        returnVal = None
                        
                    elif strVal == "False":
                        returnVal = False
                        
                    elif strVal[0] == '"' and strVal[-1] == '"': # Double Quoted String
                        returnVal = strVal[1:-1] # remove quotes
                        
                    elif strVal[0] == "'" and strVal[-1] == "'": # Single Quoted String
                        returnVal = strVal[1:-1] # remove quotes
                        
                    elif strVal[0] == "[" and strVal[-1] == "]": # List
                        listElements = strVal[1:-1].split(",") # remove [] and split by commas
                        returnVal = [self.parseInputToPrimitive(element) for element in listElements]
                    else: 
                        returnVal = cgi.escape(str(strVal))
        return returnVal
    
    def getOutput(self):
        '''
        Generates the output of the processor. Uses the attributes outputTemplate and outputArgList from the agenda
        to determine which format the output should be in. If an outputTemplate is unspecified or known,
        will return json by default.
        
        Return is of the style (output, outputType) where outputType is a content-type ready for returning 
        to the server:
        "text/plain", "application/json", "text/html", etc.
        '''
        if len(self.errorList) > 0:
            output = "<br />".join([":".join(e) for e in self.errorList])
            outputType = 'text/html'
        
        if self.outputTemplate == "":
            resDict = self.getResultObject()
            resOrderedDict = collections.OrderedDict(sorted(list(resDict.items())))
            output =  json.dumps(resOrderedDict)
            output = unicode(output).encode('utf-8')
            outputType = 'text/html; charset=utf-8'
            # TODO: unify these two -- duplicate code
        elif self.outputTemplate not in availableOutputTemplates:
            self.recordError("Unknown output template "+str(self.outputTemplate))
            resDict = self.getResultObject()
            resOrderedDict = collections.OrderedDict(sorted(list(resDict.items())))
            output =  json.dumps(resOrderedDict,indent=4)
            output = unicode(output).encode('utf-8')
            outputType = 'text/html; charset=utf-8'
            
        else:
            argList = self.outputArgList
            for (i,arg) in enumerate(argList):
                parsedArg = self.parseInputToPrimitive(arg)
                argList[i] = parsedArg  
            # safe because check for self.outputTemplate in availableOutputTemplates
            ### But let's still TODO: get rid of eval
            (output, outputType) = eval(self.outputTemplate)(*argList)
        return (output, outputType)
    
#-------------------------------------------------------------------------------
# Tests 
#-------------------------------------------------------------------------------


sampleFormDataSimple = '------WebKitFormBoundarytO99C5T6SZEHKAIb\r\nContent-Disposition: form-data; name="a"\r\n\r\n7\r\n------WebKitFormBoundarytO99C5T6SZEHKAIb\r\nContent-Disposition: form-data; name="b"\r\n\r\n8\r\n------WebKitFormBoundarytO99C5T6SZEHKAIb\r\nContent-Disposition: form-data; name="json"\r\n\r\n{"dataDict":{"c":{"data":7}},\r\n        "returnDict":{"a":"int"}\r\n        }\r\n------WebKitFormBoundarytO99C5T6SZEHKAIb--\r\n'

sampleJsonStringSimple = r'''
    {
    "dataDict": {
        "myNum":
            {"fmt" : "int",
             "data" : "23"}
             },
    "returnDict":{
        "myNum" : "int"}
    }'''

        
sampleJsonString = r'''
        {
    "dataDict": {
        "myNum":
            {"fmt" : "int",
             "data" : "23"}
    },
    "commandList":[
        {"function":"corpus.parse",
         "argList":["'bwv7.7'"],
         "resultVar":"sc"},
         
        {"method":"transpose",
         "caller":"sc",
         "argList":["'p5'"],
         "resultVar":"sc"},
         
    
        {"attribute":"flat",
         "caller":"sc",
         "resultVar":"scFlat"},
         
        {"attribute":"highestOffset",
         "caller":"scFlat",
         "resultVar":"ho"}
    ],
    "returnDict":{
        "myNum" : "int",
        "ho"    : "int"
        }
    }'''

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testAgenda(self):
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
         "resultVar":"sc"},
         
        {"method":"transpose",
         "caller":"sc",
         "argList":["'p5'"],
         "resultVar":"sc"},
         
    
        {"attribute":"flat",
         "caller":"sc",
         "resultVar":"scFlat"},
         
        {"attribute":"highestOffset",
         "caller":"scFlat",
         "resultVar":"ho"}
    ],
    "returnDict":{
        "myNum" : "int",
        "ho"    : "int"
        }
    }
    '''
        ad = Agenda()
        ad.loadJson(jsonString)
        self.assertEqual(ad['dataDict']['myNum']['data'], "23")

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof        
