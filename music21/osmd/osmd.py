# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         osmd/osmd.py
# Purpose:      display Streams in IPython notebooks using Open Sheet Music Display
#
# Authors:      Sven Hollowell
#
# Copyright:    Copyright © 2018 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
# -------------------------------------------------------------------------------
'''
Registers the .show('osmd') converter for use in IPython notebook
If not in a notebook (e.g. commandline), it will open a browser window with the rendered score
See OSMD project page here: https://github.com/opensheetmusicdisplay/opensheetmusicdisplay
'''
import unittest
import time
import random
import json
import os
import importlib
import tempfile
import urllib.request
import webbrowser

from music21.converter.subConverters import SubConverter
from music21.instrument import Piano
from music21.common import getSourceFilePath, runningUnderIPython
from music21 import exceptions21
from music21.musicxml import m21ToXml
from music21 import environment

environLocal = environment.Environment('osmd.osmd')


class OpenSheetMusicDisplayException(exceptions21.Music21Exception):
    pass


try:
    loader = importlib.util.find_spec('IPython.core.display')
except ImportError:
    loader = None
hasInstalledIPython = loader is not None
del importlib


def getExtendedModules():
    # pylint: disable=import-outside-toplevel
    if hasInstalledIPython:
        from IPython.core.display import display, HTML, Javascript
    else:
        def display():
            raise OpenSheetMusicDisplayException(
                'OpenSheetMusicDisplay requires IPython to be installed')

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
    # when updating the script tag osmd will only reload in a notebook if you: Kernel -> restart and
    # clear output, then save the notebook and refresh the page.
    # Otherwise the script will stay on the page and not reload.
    script_url = ("https://github.com/opensheetmusicdisplay"
                  + "/opensheetmusicdisplay/releases/download/0.9.2/opensheetmusicdisplay.min.js")

    def __init__(self):
        super().__init__()
        self.display, self.HTML, self.Javascript = getExtendedModules()

    def show(self, obj, fmt, *,
             fixPartName=True, offline=False, divId=None,
             **keywords):
        '''
        Displays the score object in a notebook using the OpenSheetMusicDisplay.js library.

        >>> import music21
        >>> s = music21.converter.parse("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c")
        >>> fig_id1 = s.show('osmd')

        To update a previously displayed score use the returned divId from before:

        >>> fig_id2 = s.show('osmd', divId=fig_id1)
        >>> assert fig_id1 == fig_id2
        '''
        in_ipython = runningUnderIPython()
        score = obj
        if fixPartName:
            self.addDefaultPartName(score)

        if divId is None:
            # create unique reference to output div in case we wish to update it
            divId = self.getUniqueDivId()

        # convert score to xml string
        gex = m21ToXml.GeneralObjectExporter(score)
        bytesOut = gex.parse()
        xml = bytesOut.decode('utf-8')



        script = self.musicXMLToScript(xml, divId, offline=offline)
        if in_ipython:
            self.display(self.HTML(f'<div id="{divId}">loading OpenSheetMusicDisplay</div>'))
            self.display(self.Javascript(script))
        else:

            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp_path = tmp.name + '.html'

            with open(tmp_path, 'w') as f:
                f.write(f'''
                <div id="{divId}"></div>
                <script>{script}</script>
                ''')
            filename = 'file:///' + tmp_path
            webbrowser.open_new_tab(filename)
        return divId

    def parseData(self):
        # pragma: no cover
        raise NotImplementedError('osmd is display-only')

    @staticmethod
    def getUniqueDivId():
        '''
        Generates a unique id for the div in which the score is displayed.
        This is so we can update a previously used div.
        '''
        return ("OSMD-div-"
                + str(random.randint(0, 1000000))
                + "-" + str(time.time()).replace('.', '-'))  # '.' is the class selector

    def musicXMLToScript(self, xml, divId, offline=False):
        '''
        Converts the xml into Javascript which can be injected into a webpage to display the score.
        If divId is provided then it will be used as the container, if not a new
        '''
        # script that will replace div contents with OSMD display

        script_path = os.path.join(getSourceFilePath(), 'osmd', 'notebookOSMDLoader.js')
        script = open(script_path, 'r').read() \
            .replace('{{DIV_ID}}', divId) \
            .replace('"{{data}}"', json.dumps(xml))

        fpScratch = environLocal.getRootTempDir()
        osmd_file = os.path.join(fpScratch, 'opensheetmusicdisplay.0.9.2.min.js')
        # osmd_file = os.path.join(UserSettings().getRootTempDir(), 'opensheetmusicdisplay.0.9.2.min.js')

        if offline is True:
            if not os.path.isfile(osmd_file):
                # on first use we download the file and store it locally for subsequent use
                # TODO: catch error for no internet connection
                urllib.request.urlretrieve(self.script_url, osmd_file)

            # since we can't link to files from a notebook (security risk) inject into file.
            script_content = open(osmd_file).read()
            script = script.replace('"{{offline_script}}"', json.dumps(script_content), 1)

        else:
            script = script.replace('"{{script_url}}"', json.dumps(self.script_url), 1)
        return script

    @staticmethod
    def addDefaultPartName(score):
        '''
        Due to a bug in OpenSheetMusicDisplay if a <part-name> is not provided it will default
        to an auto-generated random string. This method is used to fix that by default.


        >>> import music21
        >>> # display two scores to demonstrate difference.
        >>> s = music21.converter.parse("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c")
        >>> _ = s.show('osmd',fixPartName=False)
        >>> music21.osmd.ConverterOpenSheetMusicDisplay.addDefaultPartName(s)
        >>> _ = s.show('osmd',fixPartName=False)
        '''
        # If no partName is present in the first instrument, OSMD will display the ugly 'partId'
        allInstruments = score.getInstruments(returnDefault=False, recurse=True)

        if not allInstruments:
            defaultInstrument = Piano()
            defaultInstrument.instrumentName = ' '
            score.insert(0.0, defaultInstrument)
        elif not allInstruments.first().instrumentName:
            # instrumentName must not be '' or None
            allInstruments.first().instrumentName = ' '


class TestExternal(unittest.TestCase):

    @unittest.skipUnless(hasInstalledIPython, "skipping since IPython not installed")
    def testOpenSheetMusicDisplayRuns(self):
        from music21 import corpus

        s = corpus.parse('bwv66.6')
        ConverterOpenSheetMusicDisplay().show(s, None)

    @unittest.skipUnless(hasInstalledIPython, "skipping since IPython not installed")
    def testOpenSheetMusicDisplayColors(self):
        s = music21.converter.parse("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c")

        for n in s.recurse().getElementsByClass('Note'):
            n.style.color = 'red'
            if str(n.pitch) == 'G4':
                n.style.color = 'blue'
        for n in s.recurse().getElementsByClass('Rest'):
            n.style.color = 'green'

        s.show('osmd')

class Test(unittest.TestCase):

    def testAddsDefaultPartId(self):
        from music21 import converter
        s = converter.parse("tinyNotation: 3/4 E4 r f#")

        ConverterOpenSheetMusicDisplay.addDefaultPartName(s)
        firstInstrumentObject = s.getInstruments(returnDefault=True, recurse=True).first()
        self.assertNotNone(firstInstrumentObject.instrumentName)
        self.assertNotEqual(firstInstrumentObject.instrumentName, '')


if __name__ == "__main__":
    import music21

    music21.mainTest(TestExternal)
