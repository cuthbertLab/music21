from pathlib import Path
from tempfile import NamedTemporaryFile
import unittest
from xml.etree import ElementTree as ET

import music21 as m21

DATA_FILE = Path(__file__).parent / 'data/Test1.mxl'

class Test(unittest.TestCase):
    def testDeserialization(self):
        """Sample score deserializes properly"""
        score = m21.converter.parse(str(DATA_FILE))
        self.assertEqual(
            [str(p.getInstrument()) for p in score.parts],
            ['P1: Piano: Piano',
             'P1: Piano: Piano',
             'P2: Voice: Voice',
             'P2: Voice: Voice']
        )
        self.assertTrue(all(len(p.getElementsByClass('Measure')) == 8 for p in score.parts))

    def testSerialization(self):
        """Staff-type information maintained after serialization to musicxml"""
        score = m21.converter.parse(str(DATA_FILE))
        with NamedTemporaryFile() as mxl_file:
            score.write(fmt='musicxml', fp=mxl_file.name)

            tree = ET.parse(mxl_file)
            self.assertEqual(
                # Note that the structure of this musicxml file is different from the input one. The
                # input has 2 parts each with 2 staves, whereas this one has 4 parts.
                [part.find('./measure/attributes/staff-details/staff-type')
                 for part in tree.getroot().findall('part')],
                [None, None, 'ossia', None]
            )

    def testOssiaRecognized(self):
        """Part marked with <staff-type>ossia</staff-type> in sample score is recognized"""
        score = m21.converter.parse(str(DATA_FILE))
        self.assertEqual(
            # TODO: staff-type access method
            [p.metadata.custom.get('staff-type') if p.metadata else None for p in score.parts],
            [None, None, 'ossia', None]
        )

if __name__ == '__main__':
    m21.mainTest(Test)
