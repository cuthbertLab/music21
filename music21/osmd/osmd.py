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
import importlib
from music21 import exceptions21


class OpenSheetMusicDisplayException(exceptions21.Music21Exception):
    pass


loader = importlib.util.find_spec('IPython.core.display')
if loader is None:
    hasInstalledIPython = False
    def display(*args, **kwargs):
        raise OpenSheetMusicDisplayException('OpenSheetMusicDisplay requires IPython to be installed')
    HTML = Javascript = display
else:
    from IPython.core.display import display, HTML, Javascript
    hasInstalledIPython = True
del importlib


from music21.converter.subConverters import SubConverter
from music21.instrument import Piano
from urllib.request import pathname2url
import time, random, json, os


class ConverterOpenSheetMusicDisplay(SubConverter):
    '''
    Converter for displaying sheet music inline
    in an IPython notebook.
    Uses: https://opensheetmusicdisplay.org/ for rendering
    '''
    registerFormats = ('osmd',)
    registerShowFormats = ('osmd',) 

    def show(self, obj, fmt,
             fixPartName=True, offline=True, divId=None,
             **keywords):
        score = obj
        if fixPartName:
            score = self.addDefaultPartName(score)

        if divId is None:
            # create unique reference to output div in case we wish to update it
            divId = self.getUniqueDivId()
            # div contents should be replaced by rendering
            display(HTML('<div id="' + divId + '">loading OpenSheetMusicDisplay</div>'))


        xml = open(score.write('musicxml')).read()
        script = self.musicXMLToScript(xml, divId, offline=offline)

        display(Javascript(script))
        return divId

    @staticmethod
    def getUniqueDivId():
        return "OSMD-div-"+ \
                str(random.randint(0,1000000))+ \
                "-"+str(time.time()).replace('.','-') # '.' is the class selector

    @staticmethod
    def musicXMLToScript(xml, divId, offline=True):
        
        # print('xml length:', len(xml))
        script_dir = os.path.join(os.path.dirname(__file__), 'opensheetmusicdisplay.0.3.1.min.js')

        # script that will replace div contents with OSMD display
        script = """
        console.log("loadOSMD()");
        function loadOSMD() { 
            return new Promise(function(resolve, reject){

                if (window.opensheetmusicdisplay) {
                    console.log("already loaded")
                    return resolve(window.opensheetmusicdisplay)
                }
                console.log("loading osmd for the first time")
                // OSMD script has a 'define' call which conflicts with requirejs
                var _define = window.define // save the define object 
                window.define = undefined // now the loaded script will ignore requirejs
                var s = document.createElement( 'script' );
                // alternative to local file is using a CDN
                // s.setAttribute( 'src', "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@0.3.1/build/opensheetmusicdisplay.min.js" );
                //s.setAttribute( 'src', "{{script_dir}}" );
                function oncompleted(){
                    window.define = _define
                    console.log("loaded OSMD for the first time",opensheetmusicdisplay)
                    resolve(opensheetmusicdisplay);
                };
                {{script_command}}
                
            }) 
        }
        loadOSMD().then((OSMD)=>{
            console.log("loaded OSMD",OSMD)
            var div_id = "{{DIV_ID}}";
                console.log(div_id)
            document.querySelector('#'+div_id).innerHTML = "";
            window.openSheetMusicDisplay = new OSMD.OpenSheetMusicDisplay(div_id);
            openSheetMusicDisplay
                .load({{data}})
                .then(
                  function() {
                    console.log("rendering data")
                    openSheetMusicDisplay.render();
                  }
                );
        })
        """ \
        .replace('{{DIV_ID}}', divId) \
        .replace('{{data}}',json.dumps(xml)) \
        .replace('{{script_dir}}',pathname2url(script_dir))

        if offline is True:
            script_content = open(script_dir).read()
            script = script.replace('{{script_command}}',"""
                s.type = 'text/javascript';
                s.text="""+json.dumps(script_content)+""";
                document.body.appendChild( s ); // browser will try to load the new script tag
                oncompleted();
                """)
        else:
            script = script.replace('{{script_command}}',"""
                s.setAttribute( 'src', 'https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@0.3.1/build/opensheetmusicdisplay.min.js' );
                s.onload=oncompleted;
                document.body.appendChild( s ); // browser will try to load the new script tag
                """)

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
        environLocal = environment.Environment()

        s = corpus.parse('bwv66.6')
        # s.show('osmd')
        ConverterOpenSheetMusicDisplay().show(s, None)

    def testAddsDefaultPartId(self):
        from music21 import converter
        s = converter.parse("tinyNotation: 3/4 E4 r f#")

        s = ConverterOpenSheetMusicDisplay.addDefaultPartName(s)
        firstInstrumentObject = s.getInstruments(returnDefault=True, recurse=True)[0]
        # print("firstInstrumentObject",firstInstrumentObject)
        # print("firstInstrumentObject.instrumentName",firstInstrumentObject.instrumentName)
        self.assertNotEqual(firstInstrumentObject.instrumentName, None)
        self.assertNotEqual(firstInstrumentObject.instrumentName,'')


if __name__ == "__main__":
    import music21
    music21.mainTest(TestExternal)
