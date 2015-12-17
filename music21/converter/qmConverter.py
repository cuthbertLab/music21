# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         converter/qmConverter.py
# Purpose:      Example of subclassing Subconverter to parse a new format
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This is an example of how converter.subConverters.SubConverter
can be subclassed in order to parse and write an unsupported format
in this case, the format, .qm, consists of a line of letters separated
by spaces:

    C E G D F
    
and turns each of them into a quarter note in octave 4 in 4/4.

Consult the code to see how it works.  To use, call 
`converter.registerSubconverter(converter.qmConverter.QMConverter)`.

'''

from music21 import converter, note, stream, meter, environment

environLocal = environment.Environment()

class QMConverter(converter.subConverters.SubConverter):

    registerFormats = ('qm', 'quarterMusic')
    registerInputExtensions = ('qm',)
    registerOutputExtensions = ('qm')

    def parseData(self, strData, number=None):
        strDataList = strData.split()
        s = stream.Part()
        m = meter.TimeSignature('4/4')
        s.insert(0, m)

        for beat in strDataList:
            nObj = note.Note(beat)
            nObj.duration.quarterLength = 1
            s.append(nObj)
            
        self.stream = s.makeMeasures()

    def parseFile(self, filePath, number=None):
        with open(filePath, 'r') as f:
            self.parseData(f.read())

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):
        music = ''
        if fp is None:
            fp = environLocal.getTempFile('.qm')

        for n in obj.flat.notes:
            music = music + n.name + ' '
        music += '\n'

        with open(fp, 'w') as f:
            f.write(music)

        return fp
    
    
if __name__ == '__main__':
    from music21 import common
    import os
    
    converter.registerSubconverter(QMConverter)
    
    print('\nFILE')
    print('+++++++++++++++++++++++++')

    parserPath = common.getSourceFilePath() + os.path.sep + 'converter'
    testPath = parserPath + os.path.sep + 'quarterMusicTestIn.qm'
    
    a = converter.parse(testPath)
    
    a.show('text')
    
    
    print('\nIn-Line')
    print('+++++++++++++++++++++++++')
    
    b = converter.parse('quarterMusic: G C G')
    b.show('text')
    print( b.write('qm') )
