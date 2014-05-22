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

from music21 import freezeThaw
from music21 import stream

def fromObject(thisObject, mode='txt'):
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
    'll}, "sites": {"py/object": "music21.base.Sites", "_lastOffset": null, "_siteIndex": 1, "siteDict": {}' + 
    ', "_lastID": -1, "containedById": ..., "_locationKeys": []}, "py/seq": [], "isFlat": true, "autoSort": ' + 
    'true, "_storedElementOffsetTuples": [{"py/tuple": [{"lyrics": [], "_notehead": "normal", "_volume": {"py/objec' + 
    't": "music21.volume.Volume", "_parent": {"py/id": 6}, "velocityIsRelative": true, "_cachedRealized": null, "_v' + 
    'elocity": null}, "_activeSite": null, "xPosition": null, "_priority": 0, "pitch": {"py/object": "music21.pitch' + 
    '.Pitch", "_octave": 4, "groups": {"py/object": "music21.base.Groups", "py/seq": []}, "_activeSiteId": null, "_' + 
    'overridden_freq440": null, "_step": "C", "sites": {"py/object": "music21.base.Sites", "_lastOffset": null, "_s' + 
    'iteIndex": 1, "siteDict": {"None": {"py/object": "music21.base.Site", "obj": null, "globalSiteIndex": ' + 
    '98, "classString": null, "siteIndex": 0, "isDead": false, "offset": 0.0}}, "_lastID": -1, "containedById": ...' + 
    '..., "_locationKeys": [null]}, "implicitAccidental": false, "_classes": null, "_activeSite": null, "_accid' + 
    'ental": {"py/object": "music21.pitch.Accidental", "_modifier": "#", "_alter": 1.0, "displayLocation": "normal"' + 
    ', "_displayType": "normal", "displaySize": "full", "_name": "sharp", "_displayStatus": null, "displayStyle": "' + 
    'normal"}, "hideObjectOnPrint": false, "_priority": 0, "fundamental": null, "id": ..., "_microtone": {"p' + 
    'y/object": "music21.pitch.Microtone", "_harmonicShift": 1, "_centShift": 0}, "defaultOctave": 4, "_idLastDeepC' + 
    'opyOf": ..., "_fullyQualifiedClasses": null, "_duration": {"py/id": 8}, "xPosition": null}, "expression' + 
    's": [], "id": ..., "_duration": {"py/object": "music21.duration.Duration", "_componentsNeedUpdating": f' + 
    'alse, "_cachedIsLinked": true, "_qtrLength": 1.0, "_components": [{"py/object": "music21.duration.DurationUnit' + 
    '", "_type": "quarter", "_componentsNeedUpdating": false, "_qtrLength": 1.0, "_tuplets": {"py/tuple": []}, "_li' + 
    'nk": true, "_typeNeedsUpdating": false, "_quarterLengthNeedsUpdating": false, "_dots": [0]}], "_typeNeedsUpdat' + 
    'ing": false, "_quarterLengthNeedsUpdating": false, "linkage": "tie"}, "py/object": "music21.note.Note", "_note' + 
    'headParenthesis": false, "sites": {"py/object": "music21.base.Sites", "_lastOffset": null, "_siteIndex": 6, "_' + 
    'definedContexts": {}, "_lastID": -1, "containedById": ..., "_locationKeys": []}, "_editorial": null, "t' + 
    'ie": null, "_noteheadFill": "default", "beams": {"py/object": "music21.beam.Beams", "feathered": false, "beams' + 
    'List": []}, "_classes": ["Note", "NotRest", "GeneralNote", "Music21Object", "object"], "groups": {"py/object":' + 
    ' "music21.base.Groups", "py/seq": []}, "_fullyQualifiedClasses": null, "articulations": [], "_activeSiteId": n' + 
    'ull, "hideObjectOnPrint": false, "_stemDirection": "unspecified", "_idLastDeepCopyOf": ...}, 0.0]}], "_' + 
    'atSoundingPitch": "unknown", "_classes": ["Stream", "Music21Object", "object"], "groups": {"py/object": "music' + 
    '21.base.Groups", "py/seq": []}, "_fullyQualifiedClasses": null, "isSorted": false, "hideObjectOnPrint": false,' + 
    ' "_activeSiteId": null, "flattenedRepresentationOf": null, "_endElements": [], "_derivation": {"py/object": "m' + 
    'usic21.derivation.Derivation", "_clientId": null, "_client": null, "_originId": null, "_origin": null, "_metho' + 
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
    template = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <!-- for MSIE 10 on Windows 8 -->
        <meta http-equiv="X-UA-Compatible" content="requiresActiveX=true"/>
        <title>{title}</title>
        <script data-main='{m21URI}' src='{requireURI}'></script>
        <script>
            require(['music21'], function() {{
                var pickleIn = {pickleOutput};
                var jpc = new music21.jsonPickle.Converter();
                streamObj = jpc.run(pickleIn);
                {callback}
            }});
        </script>
    
    </head>
    <body>
    </body>
    </html>
    '''
    def __init__(self):
        self.defaults = {
            'pickleOutput' : '{"py/object": "hello"}',
            'm21URI' : 'http://web.mit.edu/music21/music21j/src/music21',
            'requireURI' :'http://web.mit.edu/music21/music21j/ext/require/require.js',
            'callback' :'streamObj.renderOptions.events.resize = "reflow";\n\t\t\tstreamObj.appendNewCanvas();'
        }

    
        
    def fromObject(self, thisObject, mode='txt'):
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
    
    def fromStream(self,thisStream, mode='txt'):
        if (thisStream.metadata is not None and thisStream.metadata.title != ""):
            title = thisStream.metadata.title
        else:
            title = "Music21 Fragment"
        sf = freezeThaw.StreamFreezer(thisStream)
        data = sf.writeStr(fmt='jsonpickle')
        dataSplit = self.splitLongJSON(data)
        d = self.defaults
        formatted = self.template.format(title = title, pickleOutput = dataSplit, 
                                    m21URI = d['m21URI'], requireURI = d['requireURI'], callback = d['callback'])
        return formatted

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
