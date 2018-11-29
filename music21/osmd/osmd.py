# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         osmd/osmd.py
# Purpose:      display Streams in IPython notebooks using Open Sheet Music Display
#
# Authors:      Sven Hollowell
#
# Copyright:    Copyright © 2018 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Registers the .show('osmd') converter for use in IPython browser
See OSMD project page here: https://github.com/opensheetmusicdisplay/opensheetmusicdisplay
'''
import unittest
from music21.converter.subConverters import SubConverter
from music21.instrument import Piano
import time, random, json, os

from music21 import exceptions21


class OpenSheetMusicDisplayException(exceptions21.Music21Exception):
    pass


import importlib
try:
    loader = importlib.util.find_spec('IPython.core.display')
except ImportError:
    loader = None
hasInstalledIPython = loader is not None
del importlib


def getExtendedModules():
    if hasInstalledIPython:
        from IPython.core.display import display, HTML, Javascript
    else:
        def display():
            raise OpenSheetMusicDisplayException('OpenSheetMusicDisplay requires IPython to be installed')
        HTML = Javascript = display
    return display, HTML, Javascript



class ConverterOpenSheetMusicDisplay(SubConverter):
    '''
    Converter for displaying sheet music inline
    in an IPython notebook.
    Uses: https://opensheetmusicdisplay.org/ for rendering
    '''
    registerFormats = ('osmd',)
    registerShowFormats = ('osmd',)
    # when updating the script tag osmd will only reload in a notebook if you: Kernel -> restart and clear output, then
    # save the notebook and refresh the page. Otherwise the script will stay on the page and not reload.
    script_url = """https://github.com/opensheetmusicdisplay/opensheetmusicdisplay/releases/download/0.6.3/
    opensheetmusicdisplay.min.js"""
    osmd_file = os.path.join(os.path.dirname(__file__), 'opensheetmusicdisplay.0.6.3.min.js')

    def __init__(self):
        self.display, self.HTML, self.Javascript = getExtendedModules()

    def show(self, obj, fmt,
             fixPartName=True, offline=False, divId=None,
             **keywords):
        score = obj
        if fixPartName:
            score = self.addDefaultPartName(score)

        if divId is None:
            # create unique reference to output div in case we wish to update it
            divId = self.getUniqueDivId()
            # div contents should be replaced by rendering
            self.display(self.HTML('<div id="' + divId + '">loading OpenSheetMusicDisplay</div>'))

        xml = open(score.write('musicxml')).read()
        script = self.musicXMLToScript(xml, divId, offline=offline)

        self.display(self.Javascript(script))
        return divId

    @staticmethod
    def getUniqueDivId():
        return "OSMD-div-" + \
                str(random.randint(0,1000000)) + \
                "-" + str(time.time()).replace('.','-')  # '.' is the class selector




    def musicXMLToScript(self, xml, divId, offline=False):

        # script that will replace div contents with OSMD display
        script = open('./music21/osmd/notebookOSMDLoader.js', 'r').read() \
            .replace('{{DIV_ID}}', divId) \
            .replace('"{{data}}"',json.dumps(xml))

        if offline is True:
            if not os.path.isfile(self.osmd_file):
                # on first use we download the file and store it locally for subsequent use
                import urllib.request
                # TODO: catch error for no internet connection
                urllib.request.urlretrieve(self.script_url, self.osmd_file)

            # since we can't link to files from a notebook (security risk) we dump the file contents to inject.
            script_content = open(self.osmd_file).read()
            script = script.replace('"{{offline_script}}"',json.dumps(script_content),1 )

        else:
            script = script.replace('"{{script_url}}"',json.dumps(self.script_url), 1)
        return script

    @staticmethod
    def addDefaultPartName(score):
        # If no partName is present in the first instrument, OSMD will display the ugly 'partId'
        allInstruments = list(score.getInstruments(returnDefault=False, recurse=True))
        
        if len(allInstruments)==0:
            # print("adding default inst")
            defaultInstrument = Piano()
            defaultInstrument.instrumentName = 'Default'
            score.insert(None, defaultInstrument)
            score.coreElementsChanged()
        elif not allInstruments[0].instrumentName:
            # print("adding instrumentName")
            # instrumentName must not be '' or None
            allInstruments[0].instrumentName = 'Default'
            score.coreElementsChanged()

        return score

class TestExternal(unittest.TestCase):

    @unittest.skipUnless(hasInstalledIPython, "skipping since IPython not installed")
    def testOpenSheetMusicDisplayRuns(self):
        from music21 import corpus, environment

        s = corpus.parse('bwv66.6')
        # s.show('osmd')
        ConverterOpenSheetMusicDisplay().show(s, None)

    def testAddsDefaultPartId(self):
        from music21 import converter
        s = converter.parse("tinyNotation: 3/4 E4 r f#")

        s = ConverterOpenSheetMusicDisplay.addDefaultPartName(s)
        firstInstrumentObject = s.getInstruments(returnDefault=True, recurse=True)[0]
        self.assertNotEqual(firstInstrumentObject.instrumentName, None)
        self.assertNotEqual(firstInstrumentObject.instrumentName,'')


if __name__ == "__main__":
    import music21
    music21.mainTest(TestExternal)
