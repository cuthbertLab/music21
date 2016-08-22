# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         alpha.webapps.apps.py
# Purpose:      application-specific commands and templates.
#
# Authors:      Lars Johnson
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Webapps is a module designed for using music21 with a webserver.

This file includes application-specific components of the webserver.

It includes a set of applicationInitializers which augment agendas with data and commands
specific to a given application as well as a set of commands specific to the various applications.

'''
import unittest

from music21.alpha.webapps import templates

def setupURLCorpusParseApp(agenda):
    '''
    Augments an agenda with the data and commands related to the URL Corpus Parse App.
    
    ResponseData is returned as a bytes object in Python3
    
    >>> agenda = alpha.webapps.Agenda()
    >>> agenda.addData('measureEnd', '4')
    >>> agenda.addData('workName',"'bwv7.7'")
    >>> agenda.addData('command',"commands.reduction")
    >>> agenda.addData('output',"musicxmlDownload")
    >>> alpha.webapps.apps.setupURLCorpusParseApp(agenda)

    >>> processor = alpha.webapps.CommandProcessor(agenda)
    >>> processor.executeCommands()
    >>> (responseData, responseContentType) = processor.getOutput()
    >>> responseContentType
    'application/vnd.recordare.musicxml+xml; charset=utf-8'
    
    Python 3 conversion first... 
    
    >>> if ext.six.PY3:
    ...     responseData = responseData.decode('utf-8')
    
    >>> converter.parse(responseData).flat.highestOffset
    16.5
    '''
    agenda.addCommand('function', 'outputStream', None, 'corpus.parse', ['workName'])
    
    if agenda.getData('measureStart') != None or agenda.getData('measureEnd') != None:
        # Get only certian measures
        if agenda.getData('measureStart') is None:
            agenda.addData('measureStart', 0)
        if agenda.getData('measureEnd') is None:
            agenda.addData('measureEnd', 'None')
        agenda.addCommand('method', 'outputStream', 'outputStream', 'measures', 
                          ['measureStart', 'measureEnd'])

    
    if agenda.getData('command') != None: # Command specified
        agenda.addCommand('function', 'outputStream', None, 'command', ['outputStream'])
    
    # Resolve desired output
    outputType = agenda.getData('output')
    if outputType in templates.outputShortcuts:
        outputTemplateName = templates.outputShortcuts[outputType]
        agenda.setOutputTemplate(outputTemplateName, ['outputStream'])
    

def setupConverterApp(agenda):
    '''
    Augments an agenda with the data and commands related to the Converter App
    demoed at the Digital Humanities conference in Hamburg Germany
    The converter app takes as query values:
    
    source: a source compatible with converter.parse in quotes (e.g. "tinyNotation:C2 D E F...")
    output: an output format (musicxml, vexflow, braille...)
    
    Example::

        http://ciconia.mit.edu/music21/webinterface?appName=converterApp&source=
        "tinynotation:F4 A-  B- B c e f2"&output=vexflow
        
    >>> agenda = alpha.webapps.Agenda()
    >>> agenda.addData('source', 'tinynotation:F4 A- B- B c e f2')
    >>> agenda.addData('output',"musicxml")
    >>> alpha.webapps.apps.setupConverterApp(agenda)

    >>> processor = alpha.webapps.CommandProcessor(agenda)
    >>> processor.executeCommands()
    >>> (responseData, responseContentType) = processor.getOutput()
    >>> responseContentType
    'application/vnd.recordare.musicxml+xml; charset=utf-8'
    
    Python 3 conversion first... 
    
    >>> if ext.six.PY3:
    ...     responseData = responseData.decode('utf-8')

    
    >>> print(responseData)
    <?xml version="1.0" ...?>
    <!DOCTYPE score-partwise
      PUBLIC '-//Recordare//DTD MusicXML 2.0 Partwise//EN'
      'http://www.musicxml.org/dtds/partwise.dtd'>
    <score-partwise>
      <movement-title>Music21 Fragment</movement-title>
      <identification>
        <creator type="composer">Music21</creator>
        <encoding>
          <encoding-date>...</encoding-date>
          <software>Music21</software>
        </encoding>
      </identification>
      <defaults>
        <scaling>
          <millimeters>7</millimeters>
          <tenths>40</tenths>
        </scaling>
      </defaults>
      <part-list>
    ...
    >>> converter.parse(responseData).flat.notes[0].pitch.ps
    53.0
    '''
    if agenda.getData('format') == 'tinyNotation':
        agenda.addCommand('function', 'outputStream', None, 'converter.parseData', 
                          ['source', 'None', 'tinyNotation'])        
    else:
        agenda.addCommand('function', 'outputStream', None, 'converter.parse', ['source'])        
    
    # Resolve desired output
    outputTypeShortcut = agenda.getData('output')
    if outputTypeShortcut in templates.outputShortcuts:
        outputTemplateName = templates.outputShortcuts[outputTypeShortcut]
        #print outputTemplateName 
        agenda.setOutputTemplate(outputTemplateName, ['outputStream'])


def setupZipfileApp(agenda):
    pass


def setupCognitionApp(agenda):
    pass

applicationInitializers = {'corpusParseApp':setupURLCorpusParseApp,
                           'converterApp':setupConverterApp}

#-------------------------------------------------------------------------------
# Tests 
#-------------------------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
        