# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         webapps.apps.py
# Purpose:      application-specific commands and templates.
#
# Authors:      Lars Johnson
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Webapps is a module designed for using music21 with a webserver.

This file includes application-specific components of the webserver.

It includes a set of applicationInitializers which augment agendas with data and commands
specific to a given application as well as a set of commands specific to the various applications.

'''

import unittest
import doctest

from music21 import converter
import music21

import templates

def setupURLCorpusParseApp(agenda):
    '''
    Augments an agenda with the data and commands related to the URL Corpus Parse App.
    
    
    >>> from music21 import *
    >>> agenda = webapps.Agenda()
    >>> agenda.addData('measureEnd','4')
    >>> agenda.addData('workName',"'bwv7.7'")
    >>> agenda.addData('command',"commands.reduction")
    >>> agenda.addData('output',"musicxmlDownload")
    >>> webapps.apps.setupURLCorpusParseApp(agenda)

    >>> processor = webapps.CommandProcessor(agenda)
    >>> processor.executeCommands()
    >>> (responseData, responseContentType) = processor.getOutput()
    >>> responseContentType
    'application/vnd.recordare.musicxml+xml; charset=utf-8'
    >>> converter.parse(responseData).flat.highestOffset
    16.5
    '''
    agenda.addCommand('function','outputStream',None,'corpus.parse',['workName'])
    
    if agenda.getData('measureStart') != None or agenda.getData('measureEnd') != None:
        # Get only certian measures
        if agenda.getData('measureStart') == None:
            agenda.addData('measureStart',0)
        if agenda.getData('measureEnd') == None:
            agenda.addData('measureEnd','None')
        agenda.addCommand('method','outputStream','outputStream','measures',['measureStart','measureEnd'])

    
    if agenda.getData('command') != None: # Command specified
        agenda.addCommand('function','outputStream',None,'command',['outputStream'])
    
    # Resolve desired output
    outputType = agenda.getData('output')
    if outputType in templates.outputShortcuts.keys():
        outputTemplateName = templates.outputShortcuts[outputType]
        agenda.setOutputTemplate(outputTemplateName, ['outputStream'])
    

def setupZipfileApp(agenda):
    pass


def setupCognitionApp(agenda):
    pass

applicationInitializers = {'corpusParseApp':setupURLCorpusParseApp}

#-------------------------------------------------------------------------------
# Tests 
#-------------------------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == '__main__':
    music21.mainTest(Test)
        