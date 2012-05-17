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

def setupURLCorpusParseApp(agenda):
    '''
    Augments an agenda with the data and commands related to the URL Corpus Parse App.
    
    
    
    >>> agenda = music21.webapps.Agenda()
    >>> agenda.addData('measureEnd','4')
    >>> agenda.addData('workName',"'bwv7.7'")
    >>> agenda.addData('command',"commands.reduction")
    >>> agenda.addData('output',"musicxmlDownload")
    >>> setupURLCorpusParseApp(agenda)
    >>> processor = music21.webapps.CommandProcessor(agenda)
    >>> processor.executeCommands()
    >>> (responseData, responseContentType) = processor.getOutput()
    >>> responseContentType
    'application/vnd.recordare.musicxml+xml'
    >>> converter.parse(responseData).flat.highestOffset
    16.5
    '''
    
    if agenda.getData('measureStart') == None:
        agenda.addData('measureStart',0)
    if agenda.getData('measureEnd') == None:
        agenda.addData('measureEnd','None')
    if agenda.getData('command') == None:
        agenda.addData('command','')
        
    agenda.addCommand('function','sc',None,'corpus.parse',['workName'])
    agenda.addCommand('function','sc','sc','measures',['measureStart','measureEnd'])
    agenda.addCommand('function','sc',None,'command',['sc'])
    
    if agenda.getData('output') == 'noteflight':
        agenda.setOutputTemplate('templates.noteflightEmbed',['sc','"Output Display"'])
        
    elif agenda.getData('output') == 'musicxmlDisplay':
        agenda.setOutputTemplate('templates.musicxmlText',['sc'])
        
    elif agenda.getData('output') == 'musicxmlDownload':
        agenda.setOutputTemplate('templates.musicxmlFile',['sc'])
        
    elif agenda.getData('output') == 'vexflow':
        agenda.setOutputTemplate('templates.vexflow',['sc'])
    elif agenda.getData('output') == 'braille':
        agenda.setOutputTemplate('templates.braille',['sc'])

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
        