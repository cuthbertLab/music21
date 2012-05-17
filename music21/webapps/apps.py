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

This file includes the classes and functions used to parse and process requests to music21 running on a server.

For information about how to set up a server to use music21, look at the files in webapps.server
For details about shortcut commands available for music21 server requests, see webapps.templates
For examples of application-specific commands and templates, see webapps.apps
For details about various output template options available, see webapps.templates

'''
import commands

def setupURLCorpusParseApp(agenda):
    
    if agenda.getData('measureStart') == None:
        agenda.addData('measureStart',0)
    if agenda.getData('measureEnd') == None:
        agenda.addData('measureEnd','None')
        
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

def setupZipfileApp(agenda):
    pass


def setupCognitionApp(agenda):
    pass

applicationInitializers = {'corpusParseApp':setupURLCorpusParseApp}
