# -*- coding: utf-8 -*-
import re
import unittest


class Test(unittest.TestCase):

    # When `maxDiff` is None, `assertMultiLineEqual()` provides better errors.
    maxDiff = None

    def testMetadataLoadCorpus(self):
        from music21 import converter
        from music21.musicxml import testFiles as mTF

        c = converter.parse(mTF.mozartTrioK581Excerpt)  # @UndefinedVariable
        md = c.metadata

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(
            md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        # get contributors directly from Metadata interface
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')

        c = converter.parse(mTF.binchoisMagnificat)  # @UndefinedVariable
        md = c.metadata
        self.assertEqual(md.composer, 'Gilles Binchois')

    def testJSONSerializationMetadata(self):
        from music21 import converter
        from music21.musicxml import testFiles as mTF
        from music21 import metadata

        md = metadata.Metadata(
            title='Concerto in F',
            date='2010',
            composer='Frank',
        )
        # environLocal.printDebug([str(md.json)])
        self.assertEqual(md.composer, 'Frank')
        self.assertEqual(md.date, '2010/--/--')
        self.assertEqual(md.composer, 'Frank')
        self.assertEqual(md.title, 'Concerto in F')

        # test getting meta data from an imported source
        c = converter.parse(mTF.mozartTrioK581Excerpt)  # @UndefinedVariable
        md = c.metadata

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(
            md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')

    def testRichMetadata01(self):
        from music21 import corpus
        from music21 import metadata

        score = corpus.parse('jactatur')
        self.assertEqual(score.metadata.composer, 'Johannes Ciconia')

        richMetadata = metadata.RichMetadata()
        richMetadata.merge(score.metadata)

        self.assertEqual(richMetadata.composer, 'Johannes Ciconia')
        # update richMetadata with stream
        richMetadata.update(score)

        self.assertEqual(
            richMetadata.keySignatureFirst,
            -1,
        )

        self.assertEqual(str(richMetadata.timeSignatureFirst), '2/4')

        score = corpus.parse('bwv66.6')
        richMetadata = metadata.RichMetadata()
        richMetadata.merge(score.metadata)

        richMetadata.update(score)
        self.assertEqual(
            richMetadata.keySignatureFirst,
            3,
        )
        self.assertEqual(str(richMetadata.timeSignatureFirst), '4/4')

    def testWorkIds(self):
        from music21 import corpus
        from music21 import metadata

        opus = corpus.parse('essenFolksong/teste')
        self.assertEqual(len(opus), 8)

        score = opus.getScoreByNumber(4)
        self.assertEqual(score.metadata.localeOfComposition,
                         'Asien, Ostasien, China, Sichuan')

        richMetadata = metadata.RichMetadata()
        richMetadata.merge(score.metadata)
        richMetadata.update(score)

        self.assertEqual(richMetadata.localeOfComposition,
                         'Asien, Ostasien, China, Sichuan')

    def testMetadataSearch(self):
        from music21 import corpus
        score = corpus.parse('ciconia')
        self.assertEqual(
            score.metadata.search(
                'quod',
                field='title',
            ),
            (True, 'title'),
        )
        self.assertEqual(
            score.metadata.search(
                'qu.d',
                field='title',
            ),
            (True, 'title'),
        )
        self.assertEqual(
            score.metadata.search(
                re.compile('(.*)canon(.*)'),
            ),
            (True, 'movementName'),
        )

    def testRichMetadata02(self):
        from music21 import corpus
        from music21 import metadata

        score = corpus.parse('bwv66.6')
        richMetadata = metadata.RichMetadata()
        richMetadata.merge(score.metadata)
        richMetadata.update(score)
        self.assertEqual(richMetadata.noteCount, 165)
        self.assertEqual(richMetadata.quarterLength, 36.0)

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test, 'noDocTest')
