# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         converter/qmConverter.py
# Purpose:      Example of subclassing Subconverter to parse a new format
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This is an example of how converter.subConverters.SubConverter
can be subclassed in order to parse and write an unsupported format
in this case, the format, .qm, consists of a line of letters separated
by spaces:

    C E G D F

and turns each of them into a quarter note in octave 4 in 4/4.

Consult the code to see how it works.  To use, call
`converter.registerSubconverter(converter.qmConverter.QMConverter)`
then `myStream = converter.parse('quarterMusic: C E G D F')`

'''
from music21 import converter, note, stream, meter, environment

environLocal = environment.Environment()


class QMConverter(converter.subConverters.SubConverter):

    registerFormats = ('qm', 'quarterMusic')
    registerInputExtensions = ('qm',)
    registerOutputExtensions = ('qm',)

    def parseData(self, strData, number=None):
        '''
        Parse the data.  The number attribute is not used.

        >>> from music21.converter.qmConverter import QMConverter
        >>> qmc = QMConverter()
        >>> qmc.parseData('C D E G C')
        >>> s = qmc.stream
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note G>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.bar.Barline type=final>
        '''
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
        '''
        parse a file from disk.  If QMConverter is registered, then any
        file ending in .qm will automatically be parsed.

        >>> import os
        >>> parserPath = common.getSourceFilePath() / 'converter'
        >>> testPath = parserPath / 'quarterMusicTestIn.qm'

        >>> from music21.converter.qmConverter import QMConverter
        >>> qmc = QMConverter()
        >>> qmc.parseFile(testPath)
        >>> s = qmc.stream
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note G>
            {3.0} <music21.note.Note F>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note C>
            {3.0} <music21.bar.Barline type=final>
        '''
        with open(filePath, 'r') as f:
            self.parseData(f.read())

    def write(self, obj, fmt, fp=None, subformats=None, **keywords):  # pragma: no cover
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
    import music21
    music21.mainTest()
#     from music21 import common
#
#     converter.registerSubconverter(QMConverter)
#
#     print('\nFILE')
#     print('+++++++++++++++++++++++++')
#
#     parserPath = common.getSourceFilePath() / 'converter'
#     testPath = parserPath / 'quarterMusicTestIn.qm'
#
#     a = converter.parse(testPath)
#
#     a.show('text')
#
#
#     print('\nIn-Line')
#     print('+++++++++++++++++++++++++')
#
#     b = converter.parse('quarterMusic: G C G')
#     b.show('text')
#     print( b.write('qm') )
