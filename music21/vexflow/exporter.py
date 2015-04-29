# -*- coding: utf-8 -*-
import json

template = r'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns = "http://www.w3.org/1999/xhtml">
<head>
 <title>Music21 Fragment</title>
 <meta http-equiv="content-type" content="text/html; charset=utf-8" />
 <script src='http://code.jquery.com/jquery-latest.js'></script>
 <!-- vexflow -->
 <script src="http://ciconia.mit.edu/m21j/ext/vexflow/vexflow-min.js"></script>

 <!-- music21j -->
 <script src="http://ciconia.mit.edu/m21j/music21jExp.js" type="text/javascript"></script> 
</head>
<body>
<script type="text/javascript">

%s

window.onload = function () {
   %s
};

</script>
<div class="document">
</div>

</body>
</html>'''

loadFunction = r'''
    //var score = Music21.parseJSON(dataAssignment);
    var jsonObj = JSON.parse(dataAssignment);
    s = new Music21.Score();
    s.tempo = 60;
    s.timeSignature = '3/4';
    for (var i = 0; i < jsonObj['__attr__']['_elements'].length; i++) {
        var jsonPart = jsonObj['__attr__']['_elements'][i];
        if (jsonPart['__class__'] != 'music21.stream.Part') {
            continue;
        }
        
        
        var part = new Music21.Part();
        if (i < 2) {
            part.clef = new Music21.Clef('treble');
        } else {
            part.clef = new Music21.Clef('bass');
        }
        //console.log('got part');
        for (var m = 0; m < jsonPart['__attr__']['_elements'].length; m++) {
            //console.log('got measure');
            var jsonMeasure = jsonPart['__attr__']['_elements'][m];
            if (jsonMeasure['__class__'] != 'music21.stream.Measure') {
                continue;
            }


            var measure = new Music21.Measure();
            for (var nI = 0; nI < jsonMeasure['__attr__']['_elements'].length; nI++) {
                var noteObj = jsonMeasure['__attr__']['_elements'][nI];
                if (noteObj['__class__'] != 'music21.note.Note') {
                    continue;
                }
                var n = new Music21.Note();
                //console.log(noteObj);
                var pitchObj = noteObj['__attr__']['pitch'];
                n.pitch.step = pitchObj['__attr__']['_step'];
                n.pitch.octave = pitchObj['__attr__']['_octave'];
                var durationObj = noteObj['__attr__']['_duration'];
                n.duration.quarterLength = durationObj['__attr__']['_qtrLength'];
                measure.append(n);
            }
            part.append(measure)
        }
        s.append(part);
    }    
    s.appendNewCanvas();
'''

def getFormat(score):
    from music21 import freezeThaw
    sf = freezeThaw.JSONFreezer(score)
    frozen = json.dumps(
            sf.getJSONDict(includeVersion=True),
            sort_keys=True,
            );
    return "var dataAssignment = '" + frozen + "'"

def fillTemplate(score):
    dataAssignment = getFormat(score)
    return template % (dataAssignment, loadFunction)

if __name__ == '__main__':
    from music21 import corpus, converter, note, base, volume, duration, stream, environment
    p = converter.parse('tinynotation: 3/4 c4 d4 e4 f4 g4 a4').makeMeasures()
    s = stream.Score()
    s.insert(0, p)
    p2 = converter.parse('tinynotation: 3/4 A4 B4 c d e f').makeMeasures()
    s.insert(0, p2)
    s = corpus.parse('bwv66.6')
    
    n = note.Note()
    #s = stream.Stream()
    
    b = base.Music21Object()
    v = volume.Volume()
    d = duration.Duration()
    dataStr = fillTemplate(s)

    environLocal = environment.Environment()
    ext = '.html'    
    fp = environLocal.getTempFile(ext)

    f = open(fp, 'w')
    f.write(dataStr)
    f.close()
    environLocal.launch(ext, fp)

#### 
# eof
