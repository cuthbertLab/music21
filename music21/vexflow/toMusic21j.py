# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         vexflow/toM21p.py
# Purpose:      music21 classes for converting music21 objects to music21j
#
# Authors:      Michael Scott Cuthbert
#               based on an earlier version by Christopher Reyes
#
# Copyright:    Copyright © 2012-14 Michael Scott Cuthbert and the music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Convert a music21 object into JSON and send it to the browser for music21j to use.
'''
import unittest

from music21.exceptions21 import Music21Exception
from music21 import freezeThaw
from music21 import stream

supportedDisplayModes = [
    'html',
    'jsbody',
    'jsbodyScript',
    'json'
]


def fromObject(thisObject, mode='html'):
    '''
    returns a string of data for a given Music21Object such as a Score, Note, etc. that
    can be displayed in a browser using the music21j package.  Called by .show('vexflow').
    
    >>> n = note.Note('C#4')
    >>> #_DOCS_SHOW print(vexflow.toMusic21j.fromObject(n))
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <!-- for MSIE 10 on Windows 8 -->
        <meta http-equiv="X-UA-Compatible" content="requiresActiveX=true"/>
        <title>Music21 Fragment</title>
        <script data-main='http://web.mit.edu/music21/music21j/src/music21' src='http://web.mit.edu/music21/music21j/ext/require/require.js'></script>
        <script>
            require(['music21'], function() {
                var pickleIn = '{"m21Version": {"py/tuple": [1, 9, 2]}, "stream": {"_mutable": true, "_activeSite": null, "xPosition": null, "' + 
    '_priority": 0, "_elements": [], "_cache": {}, "definesExplicitPageBreaks": false, "_unlinkedDuration": null, "' + 
    'id": ..., "_duration": null, "py/object": "music21.stream.Stream", "streamStatus": {"py/object": "music' + 
    '21.stream.streamStatus.StreamStatus", "_enharmonics": null, "_dirty": null, "_concertPitch": null, "_accidenta' + 
    'ls": null, "_ties": null, "_rests": null, "_ornaments": null, "_client": null, "_beams": null, "_measures": nu' + 
    ...
    'd": null}, "definesExplicitSystemBreaks": false, "_idLastDeepCopyOf": ...}}';
                var jpc = new music21.jsonPickle.Converter();
                streamObj = jpc.run(pickleIn);
                streamObj.renderOptions.events.resize = "reflow";
                streamObj.appendNewCanvas();
            });
        </script>
    <BLANKLINE>
    </head>
    <body>
    </body>
    </html>
    '''
    conv = VexflowPickler()
    conv.mode = mode
    return conv.fromObject(thisObject)

class VexflowPickler(object):
    templateHtml = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <!-- for MSIE 10 on Windows 8 -->
        <meta http-equiv="X-UA-Compatible" content="requiresActiveX=true"/>
        <title>{title}</title>
        {loadM21Template}
        {jsBodyScript}
    </head>
    <body>
    </body>
    </html>
    '''
    jsBodyScript = '''<script>\n{jsBody}\n</script>'''
    jsBody = '''require(['music21'], function() {{
                var pickleIn = {pickleOutput};
                var jpc = new music21.jsonPickle.Converter();
                streamObj = jpc.run(pickleIn);
                {callback}
            }});'''
    loadM21Template = '''<script data-main='{m21URI}' src='{requireURI}'></script>'''

    def __init__(self):
        self.defaults = {
            'pickleOutput' : '{"py/object": "hello"}',
            'm21URI' : 'http://web.mit.edu/music21/music21j/src/music21',
            'requireURI' :'http://web.mit.edu/music21/music21j/ext/require/require.js',
            'callback' :'streamObj.renderOptions.events.resize = "reflow";\n\t\t\tstreamObj.appendNewCanvas();'
        }
        self.mode = 'html'
    
        
    def fromObject(self, thisObject, mode=None):
        if mode is None:
            mode = self.mode
        if (thisObject.isStream is False):
            retStream = stream.Stream()
            retStream.append(thisObject)
        else:
            retStream = thisObject
        return self.fromStream(retStream, mode=mode)
    
        
    def splitLongJSON(self, jsonString, chunkSize=110):
        allJSONList = []
        for i in xrange(0, len(jsonString), chunkSize):
            allJSONList.append('\'' + jsonString[i:i+chunkSize] + '\'')
        return ' + \n    '.join(allJSONList)
    
    def getLoadTemplate(self, urls=None):
        '''
        Gets the <script> tag for loading music21 from require.js
        
        >>> vfp = vexflow.toMusic21j.VexflowPickler()
        >>> vfp.getLoadTemplate()
        "<script data-main='http://web.mit.edu/music21/music21j/src/music21' src='http://web.mit.edu/music21/music21j/ext/require/require.js'></script>"

        >>> d = {'m21URI': 'file:///tmp/music21', 'requireURI': 'http://requirejs.com/require.js'}
        >>> vfp.getLoadTemplate(d)
        "<script data-main='file:///tmp/music21' src='http://requirejs.com/require.js'></script>"
        '''
        
        if urls is None:
            urls = self.defaults
        loadM21formatted = self.loadM21Template.format(m21URI = urls['m21URI'], 
                                                       requireURI = urls['requireURI'],)
        return loadM21formatted
    
    def getJSBodyScript(self, dataSplit, defaults = None):
        '''
        Get the <script>...</script> tag to render the JSON
        
        >>> vfp = vexflow.toMusic21j.VexflowPickler()
        >>> print(vfp.getJSBodyScript('{"hi": "hello"}'))
           <script>
                require(['music21'], function() {
                    var pickleIn = {"hi": "hello"};
                    var jpc = new music21.jsonPickle.Converter();
                    streamObj = jpc.run(pickleIn);
                    streamObj.renderOptions.events.resize = "reflow";
                streamObj.appendNewCanvas();
                });
            </script>        
        '''
        if defaults is None:
            defaults = self.defaults
        jsBody = self.getJSBody(dataSplit, defaults)
        jsBodyScript = self.jsBodyScript.format(jsBody = jsBody)
        return jsBodyScript;

    def getJSBody(self, dataSplit, defaults = None):
        '''
        Get the javascript code without the <script> tags to render the JSON
        
        >>> vfp = vexflow.toMusic21j.VexflowPickler()
        >>> print(vfp.getJSBody('{"hi": "hello"}'))
                require(['music21'], function() {
                    var pickleIn = {"hi": "hello"};
                    var jpc = new music21.jsonPickle.Converter();
                    streamObj = jpc.run(pickleIn);
                    streamObj.renderOptions.events.resize = "reflow";
                streamObj.appendNewCanvas();
                });
        '''
        if defaults is None:
            d = self.defaults
        else:
            d = defaults
        jsBody = self.jsBody.format(pickleOutput = dataSplit,
                                    callback = d['callback'])
        return jsBody;
    
    def getHTML(self, dataSplit, title=None, defaults=None):
        '''
        Get the complete HTML page to pass to the browser:
        
        >>> vfp = vexflow.toMusic21j.VexflowPickler()
        >>> print(vfp.getHTML('{"hi": "hello"}', 'myPiece'))
           <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
                <html xmlns="http://www.w3.org/1999/xhtml">
                <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8" />
            <!-- for MSIE 10 on Windows 8 -->
            <meta http-equiv="X-UA-Compatible" content="requiresActiveX=true"/>
            <title>myPiece</title>
            <script data-main='http://web.mit.edu/music21/music21j/src/music21' src='http://web.mit.edu/music21/music21j/ext/require/require.js'></script>
            <script>
            require(['music21'], function() {
                            var pickleIn = {"hi": "hello"};
                            var jpc = new music21.jsonPickle.Converter();
                            streamObj = jpc.run(pickleIn);
                            streamObj.renderOptions.events.resize = "reflow";
                        streamObj.appendNewCanvas();
                        });
            </script>
            </head>
            <body>
            </body>
            </html>
        '''
        if defaults is None:
            d = self.defaults
        else:
            d = defaults
        loadM21Formatted = self.getLoadTemplate(d)
        jsBodyScript = self.getJSBodyScript(dataSplit, d)
        formatted = self.templateHtml.format(title = title, 
                                                 loadM21Template=loadM21Formatted,
                                                 jsBodyScript=jsBodyScript)
        return formatted
    
    def fromStream(self, thisStream, mode=None):
        if mode is None:
            mode = self.mode

        if (thisStream.metadata is not None and thisStream.metadata.title != ""):
            title = thisStream.metadata.title
        else:
            title = "Music21 Fragment"
        sf = freezeThaw.StreamFreezer(thisStream)
        data = sf.writeStr(fmt='jsonpickle')
        dataSplit = self.splitLongJSON(data)
        if mode == 'json':
            return data
        elif mode == 'jsonSplit':
            return dataSplit
        elif mode == 'jsbody':
            return self.getJSBody(dataSplit)
        elif mode == 'jsbodyScript':
            return self.getJSBodyScript(dataSplit)
        elif mode == 'html':
            return self.getHTML(dataSplit, title)
        else:
            raise VexflowToM21JException("Cannot deal with mode: %r" % mode)

class VexflowToM21JException(Music21Exception):
    pass

class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testDummy(self):
        pass
    
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testCuthbertLocal(self):
        '''
        test a local version of this mess...
        '''
        from music21 import corpus, environment
        environLocal = environment.Environment()
        
        s = corpus.parse('luca/gloria').measures(1,19)
        #s = corpus.parse('beethoven/opus18no1', 2).parts[0].measures(4,10)
        
        vfp = VexflowPickler()
        vfp.defaults['m21URI'] = 'file:///Users/Cuthbert/git/music21j/src/music21'
        vfp.defaults['requireURI'] = 'file:///Users/Cuthbert/git/music21j/ext/require/require.js'
        data = vfp.fromObject(s);
        fp = environLocal.getTempFile('.html')
        with open(fp, 'w') as f:
            f.write(data)
        environLocal.launch('vexflow', fp)


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
    
    #s.show('vexflow')
