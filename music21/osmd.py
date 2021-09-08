# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         osmd.py
# Purpose:      display Streams in IPython notebooks using Open Sheet Music Display
#
# Authors:      Sven Hollowell
#               Jacob Tyler Walls
#
# Copyright:    Copyright © 2018-21 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -------------------------------------------------------------------------------
'''
Helper functions for displaying streams in IPython notebooks using Open Sheet Music Display.
If not in a notebook (e.g. commandline), it will open a browser window with the rendered score
See OSMD project page here: https://github.com/opensheetmusicdisplay/opensheetmusicdisplay
'''
import importlib
import json
import os
import random
import time
import unittest
import urllib.request

from music21.common import getSourceFilePath
from music21.musicxml.m21ToXml import GeneralObjectExporter
from music21 import environment

# when using offline=True, sets the disk location where we will cache the OSMD.min.js file:
environLocal = environment.Environment('osmd')

# when updating the script tag osmd will only reload in a notebook if you: Kernel -> restart and
# clear output, then save the notebook and refresh the page.
# Otherwise the script will stay on the page and not reload.
SCRIPT_URL = ('https://github.com/opensheetmusicdisplay'
            + '/opensheetmusicdisplay/releases/download/1.1.0/opensheetmusicdisplay.min.js')


def hasInstalledIPython() -> bool:
    '''
    Determine if we are running inside an IPython notebook.
    If so will render inline - if not we open a new browser window.
    '''
    try:
        loader = importlib.util.find_spec('IPython.core.display')
    except ImportError:
        loader = None
    return loader is not None

def getUniqueDivId() -> str:
    '''
    Generates a unique id for the div in which the score is displayed.
    This is so we can update a previously used div.

    >>> osmd.getUniqueDivId()
    'OSMD-div-...'
    '''
    return ('OSMD-div-'
            + str(random.randint(0, 1000000))
            + '-' + str(time.time()).replace('.', '-'))  # '.' is the class selector

def getXml(obj) -> str:
    '''
    Prepare a score even if `obj` is not a Score, and ensure the part name is not empty.
    Return a string dump of the XML.

    >>> p = converter.parse('tinyNotation: c1 d1')
    >>> p.partName is None
    True
    >>> dump = osmd.getXml(p)
    >>> '<part-name> </part-name>' in dump
    True
    '''
    gex = GeneralObjectExporter()
    # whether or not obj is score, fromGeneralObject returns a score
    score = gex.fromGeneralObject(obj)
    # fix each part name to be not empty: OSMD currently subs ugly, random IDs
    for part in score.parts:
        if not part.partName:
            part.partName = ' '

    bytesOut = gex.parseWellformedObject(score)
    return bytesOut.decode('utf-8')

def musicXMLToScript(xml, divId, *, offline=False):
    '''
    Converts the xml into Javascript which can be injected into a webpage to display the score.
    If divId is set then it will be used as the container, if not a new div will be created.

    >>> excerpt = corpus.parse('demos/two-parts')
    >>> xml = osmd.getXml(excerpt)
    >>> divId = osmd.getUniqueDivId()
    >>> js = osmd.musicXMLToScript(xml, divId, offline=True)
    >>> 'window.openSheetMusicDisplay = new OSMD.OpenSheetMusicDisplay(div_id);' in js
    True
    '''

    # script that will replace div contents with OSMD display
    script = ''
    script_path = os.path.join(getSourceFilePath(), 'js', 'notebookOSMDLoader.js')
    with open(script_path, 'r', encoding='utf-8') as f:
        script = f.read()
    script = script.replace('{{DIV_ID}}', divId)
    script = script.replace('"{{data}}"', json.dumps(xml))

    fpScratch = environLocal.getRootTempDir()
    osmd_file = os.path.join(fpScratch, 'opensheetmusicdisplay.0.9.2.min.js')

    if offline is True:
        if not os.path.isfile(osmd_file):
            # on first use we download the file and store it locally for subsequent use
            # TODO: catch error for no internet connection
            urllib.request.urlretrieve(SCRIPT_URL, osmd_file)

        # since we can't link to files from a notebook (security risk) inject into file.
        script_content = ''
        with open(osmd_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
        script = script.replace('"{{offline_script}}"', json.dumps(script_content), 1)

    else:
        script = script.replace('"{{script_url}}"', json.dumps(SCRIPT_URL), 1)
    return script


class TestExternal(unittest.TestCase):  # pragma: no cover

    @unittest.skipUnless(hasInstalledIPython(), 'skipping since IPython not installed')
    def testOpenSheetMusicDisplayRuns(self):
        from music21 import corpus

        s = corpus.parse('bwv66.6')
        s.show('osmd')

    @unittest.skipUnless(hasInstalledIPython(), 'skipping since IPython not installed')
    def testOpenSheetMusicDisplayColors(self):
        s = music21.converter.parse('tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c')

        for n in s.recurse().getElementsByClass('Note'):
            n.style.color = 'red'
            if str(n.pitch) == 'G4':
                n.style.color = 'blue'
        for n in s.recurse().getElementsByClass('Rest'):
            n.style.color = 'green'

        # Test fixing part name by ensuring we start with None
        self.assertIsNone(s.partName)
        s.show('osmd')
        # Verify no ugly, random part ID written by OSMD.


if __name__ == '__main__':
    import music21
    music21.mainTest(TestExternal)
