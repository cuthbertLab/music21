# -*- coding: utf-8 -*-
import re
import unittest
from typing import Type
from music21 import metadata



class Test(unittest.TestCase):

    # When `maxDiff` is None, `assertMultiLineEqual()` provides better errors.
    maxDiff = None

    def testMetadataLoadCorpus(self):
        from music21 import converter
        from music21.musicxml import testFiles as mTF

        c = converter.parse(mTF.mozartTrioK581Excerpt)
        md = c.metadata

        self.assertEqual(md['movementNumber'], (metadata.Text('3'),))
        self.assertEqual(md['movementName'],
            (metadata.Text('Menuetto (Excerpt from Second Trio)'),))
        self.assertEqual(md['title'],
            (metadata.Text('Quintet for Clarinet and Strings'),))
        self.assertEqual(md['number'], (metadata.Text('K. 581'),))
        self.assertEqual(md['composer'],
            (metadata.Contributor(role='composer', name='Wolfgang Amadeus Mozart'),))

        c = converter.parse(mTF.binchoisMagnificat)
        md = c.metadata
        self.assertEqual(md['composer'],
            (metadata.Contributor(role='composer', name='Gilles Binchois'),))

    def testMetadataLoadCorpusBackwardCompatible(self):
        from music21 import converter
        from music21.musicxml import testFiles as mTF

        c = converter.parse(mTF.mozartTrioK581Excerpt)
        md = c.metadata

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(
            md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        # get contributors directly from Metadata interface
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')

        c = converter.parse(mTF.binchoisMagnificat)
        md = c.metadata
        self.assertEqual(md.composer, 'Gilles Binchois')

    def testJSONSerializationMetadata(self):
        from music21 import converter
        from music21.musicxml import testFiles as mTF

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

        # test getting metadata from an imported source
        c = converter.parse(mTF.mozartTrioK581Excerpt)
        md = c.metadata

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(
            md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')

    def testRichMetadata01(self):
        from music21 import corpus

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

        opus = corpus.parse('essenFolksong/teste')
        self.assertEqual(len(opus.scores), 8)

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
                field='movementName',
            ),
            (True, 'movementName'),
        )
        self.assertEqual(
            score.metadata.search(
                'qu.d',
                field='movementName',
            ),
            (True, 'movementName'),
        )
        self.assertEqual(
            score.metadata.search(
                re.compile('(.*)canon(.*)'),
            ),
            (True, 'movementName'),
        )

    def testRichMetadata02(self):
        from music21 import corpus

        score = corpus.parse('bwv66.6')
        richMetadata = metadata.RichMetadata()
        richMetadata.merge(score.metadata)
        richMetadata.update(score)
        self.assertEqual(richMetadata.noteCount, 165)
        self.assertEqual(richMetadata.quarterLength, 36.0)

    def checkUniqueNamedItem(
            self,
            uniqueName: str,
            nsKey: str,
            contributorRole: str = None,
            valueType: Type = metadata.Text):

        if ':' not in nsKey:
            # It's just the namespace because name == uniqueName
            # and I didn't want to spend the time to type it twice...
            nsKey += ':' + uniqueName

        if nsKey.startswith('marcrel'):
            # The marcrel namespace is all Contributors (more typing saved)
            valueType = metadata.Contributor

        md = metadata.Metadata()

        self.assertTrue(md.isStandardKey(uniqueName))
        self.assertFalse(md.isStandardKey(uniqueName + '_'))

        self.assertTrue(md.isStandardKey(nsKey))
        self.assertFalse(md.isStandardKey(nsKey + '_'))

        item = getattr(md, uniqueName)
        self.assertIsNone(item)
        itemtuple = md[uniqueName]
        self.assertEqual(itemtuple, tuple())
        itemtuple = md[nsKey]
        self.assertEqual(itemtuple, tuple())

        if valueType is metadata.DateSingle:
            md[nsKey] = ['1978/6/11']
            self.assertEqual(getattr(md, uniqueName), '1978/06/11')
            md[uniqueName] = ('1979/6/11',)
            self.assertEqual(getattr(md, uniqueName), '1979/06/11')
        elif valueType is metadata.Copyright:
            md[nsKey] = ['Copyright © 1978 Joe Smith']
            self.assertEqual(getattr(md, uniqueName), 'Copyright © 1978 Joe Smith')
            md[uniqueName] = ('Copyright © 1979 Joe Smith',)
            self.assertEqual(getattr(md, uniqueName), 'Copyright © 1979 Joe Smith')
        elif valueType is metadata.Contributor:
            md[nsKey] = [f'The {nsKey}']
            self.assertEqual(getattr(md, uniqueName), f'The {nsKey}')
            md[uniqueName] = (f'The {uniqueName}',)
            self.assertEqual(getattr(md, uniqueName), f'The {uniqueName}')
        elif valueType is metadata.Text:
            md[nsKey] = [f'The {nsKey}']
            self.assertEqual(getattr(md, uniqueName), f'The {nsKey}')
            md[uniqueName] = (f'The {uniqueName}',)
            self.assertEqual(getattr(md, uniqueName), f'The {uniqueName}')
        else:
            self.fail('internal test error: invalid valueType')


        if valueType is metadata.DateSingle:
            md.add(nsKey, [metadata.DateBetween(['1978', '1980']),
                metadata.DateSingle('1979/6/11/4:50:32')])
            self.assertEqual(getattr(md, uniqueName),
                '1979/06/11, 1978/--/-- to 1980/--/--, 1979/06/11/04/50/032.00')
        elif valueType is metadata.Copyright:
            md.add(nsKey, metadata.Text('Lyrics copyright © 1979 John Jones'))
            md.add(uniqueName,
                [metadata.Copyright('Other content copyright © 1979 Jenni Johnson',
                    role='other'),
                metadata.Copyright(
                    metadata.Text('Even more content copyright © 1979 Sarah Michaels'),
                    role='even more')])
            self.assertEqual(getattr(md, uniqueName),
                'Copyright © 1979 Joe Smith'
                    + ', Lyrics copyright © 1979 John Jones'
                    + ', Other content copyright © 1979 Jenni Johnson'
                    + ', Even more content copyright © 1979 Sarah Michaels')
        elif valueType is metadata.Contributor:
            md.add(uniqueName, [metadata.Text(f'The 2nd {uniqueName}'),
                metadata.Contributor(
                    role=contributorRole if contributorRole else uniqueName,
                    name=f'The 3rd {uniqueName}')])
            self.assertEqual(getattr(md, uniqueName),
                f'The {uniqueName} and 2 others')
        elif valueType is metadata.Text:
            md.add(nsKey, [metadata.Text(f'The 2nd {uniqueName}'),
                metadata.Text(f'The 3rd {uniqueName}')])
            self.assertEqual(getattr(md, uniqueName),
                f'The {uniqueName}, The 2nd {uniqueName}, The 3rd {uniqueName}')

        mdItemsUnique = md[uniqueName]
        mdItemsNSKey = md[nsKey]
        self.assertEqual(len(mdItemsUnique), len(mdItemsNSKey))

        for itemUnique, itemNSKey in zip(mdItemsUnique, mdItemsNSKey):
            self.assertIsInstance(itemUnique, valueType)
            self.assertIsInstance(itemNSKey, valueType)
            self.assertEqual(itemUnique, itemNSKey)

        if valueType is metadata.Contributor:
            for itemNSKey in mdItemsNSKey:
                # I'm asserting this way to keep mypy happy.
                # self.assertIsInstance isn't sufficient, apparently.
                assert isinstance(itemNSKey, metadata.Contributor)
                self.assertEqual(itemNSKey.role,
                    contributorRole if contributorRole else uniqueName)

    def testUniqueNameAccess(self):
        self.checkUniqueNamedItem('abstract', 'dcterms')
        self.checkUniqueNamedItem('accessRights', 'dcterms')
        self.checkUniqueNamedItem('alternativeTitle', 'dcterms:alternative')
        self.checkUniqueNamedItem('audience', 'dcterms')
        self.checkUniqueNamedItem('dateAvailable', 'dcterms:available',
            valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('bibliographicCitation', 'dcterms')
        self.checkUniqueNamedItem('conformsTo', 'dcterms')
        self.checkUniqueNamedItem('dateCreated', 'dcterms:created', valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('otherDate', 'dcterms:date', valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('dateAccepted', 'dcterms', valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('dateCopyrighted', 'dcterms', valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('dateSubmitted', 'dcterms', valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('description', 'dcterms')
        self.checkUniqueNamedItem('educationLevel', 'dcterms')
        self.checkUniqueNamedItem('extent', 'dcterms')
        self.checkUniqueNamedItem('format', 'dcterms')
        self.checkUniqueNamedItem('hasFormat', 'dcterms')
        self.checkUniqueNamedItem('hasPart', 'dcterms')
        self.checkUniqueNamedItem('hasVersion', 'dcterms')
        self.checkUniqueNamedItem('identifier', 'dcterms')
        self.checkUniqueNamedItem('instructionalMethod', 'dcterms')
        self.checkUniqueNamedItem('isFormatOf', 'dcterms')
        self.checkUniqueNamedItem('isPartOf', 'dcterms')
        self.checkUniqueNamedItem('isReferencedBy', 'dcterms')
        self.checkUniqueNamedItem('isReplacedBy', 'dcterms')
        self.checkUniqueNamedItem('isRequiredBy', 'dcterms')
        self.checkUniqueNamedItem('dateIssued', 'dcterms:issued', valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('isVersionOf', 'dcterms')
        self.checkUniqueNamedItem('language', 'dcterms')
        self.checkUniqueNamedItem('license', 'dcterms')
        self.checkUniqueNamedItem('medium', 'dcterms')
        self.checkUniqueNamedItem('dateModified', 'dcterms:modified',
            valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('provenance', 'dcterms')
        self.checkUniqueNamedItem('publisher', 'dcterms', valueType=metadata.Contributor)
        self.checkUniqueNamedItem('references', 'dcterms')
        self.checkUniqueNamedItem('relation', 'dcterms')
        self.checkUniqueNamedItem('replaces', 'dcterms')
        self.checkUniqueNamedItem('requires', 'dcterms')
        self.checkUniqueNamedItem('copyright', 'dcterms:rights', valueType=metadata.Copyright)
        self.checkUniqueNamedItem('rightsHolder', 'dcterms', valueType=metadata.Contributor)
        self.checkUniqueNamedItem('source', 'dcterms')
        self.checkUniqueNamedItem('subject', 'dcterms')
        self.checkUniqueNamedItem('tableOfContents', 'dcterms')
        self.checkUniqueNamedItem('title', 'dcterms')
        self.checkUniqueNamedItem('type', 'dcterms')
        self.checkUniqueNamedItem('dateValid', 'dcterms:valid', valueType=metadata.DateSingle)
        self.checkUniqueNamedItem('adapter', 'marcrel:ADP')
        self.checkUniqueNamedItem('annotator', 'marcrel:ANN')
        self.checkUniqueNamedItem('arranger', 'marcrel:ARR')
        self.checkUniqueNamedItem('quotationsAuthor', 'marcrel:AQT')
        self.checkUniqueNamedItem('afterwordAuthor', 'marcrel:AFT')
        self.checkUniqueNamedItem('dialogAuthor', 'marcrel:AUD')
        self.checkUniqueNamedItem('introductionAuthor', 'marcrel:AUI')
        self.checkUniqueNamedItem('calligrapher', 'marcrel:CLL')
        self.checkUniqueNamedItem('collaborator', 'marcrel:CLB')
        self.checkUniqueNamedItem('collotyper', 'marcrel:CLT')
        self.checkUniqueNamedItem('commentaryAuthor', 'marcrel:CWT')
        self.checkUniqueNamedItem('compiler', 'marcrel:COM')
        self.checkUniqueNamedItem('composer', 'marcrel:CMP')
        self.checkUniqueNamedItem('conceptor', 'marcrel:CCP')
        self.checkUniqueNamedItem('conductor', 'marcrel:CND')
        self.checkUniqueNamedItem('otherContributor', 'marcrel:CTB')
        self.checkUniqueNamedItem('editor', 'marcrel:EDT')
        self.checkUniqueNamedItem('engraver', 'marcrel:EGR')
        self.checkUniqueNamedItem('etcher', 'marcrel:ETR')
        self.checkUniqueNamedItem('illuminator', 'marcrel:ILU')
        self.checkUniqueNamedItem('illustrator', 'marcrel:ILL')
        self.checkUniqueNamedItem('instrumentalist', 'marcrel:ITR')
        self.checkUniqueNamedItem('librettist', 'marcrel:LBT')
        self.checkUniqueNamedItem('lithographer', 'marcrel:LTG')
        self.checkUniqueNamedItem('lyricist', 'marcrel:LYR')
        self.checkUniqueNamedItem('metalEngraver', 'marcrel:MTE')
        self.checkUniqueNamedItem('musician', 'marcrel:MUS')
        self.checkUniqueNamedItem('platemaker', 'marcrel:PLT')
        self.checkUniqueNamedItem('printmaker', 'marcrel:PRM')
        self.checkUniqueNamedItem('producer', 'marcrel:PRO')
        self.checkUniqueNamedItem('responsibleParty', 'marcrel:RPY')
        self.checkUniqueNamedItem('scribe', 'marcrel:SCR')
        self.checkUniqueNamedItem('singer', 'marcrel:SNG')
        self.checkUniqueNamedItem('transcriber', 'marcrel:TRC')
        self.checkUniqueNamedItem('translator', 'marcrel:TRL')
        self.checkUniqueNamedItem('woodEngraver', 'marcrel:WDE')
        self.checkUniqueNamedItem('woodCutter', 'marcrel:WDC')
        self.checkUniqueNamedItem('accompanyingMaterialWriter', 'marcrel:WAM')
        self.checkUniqueNamedItem('distributor', 'marcrel:DST')
        self.checkUniqueNamedItem('textOriginalLanguage', 'humdrum:TXO')
        self.checkUniqueNamedItem('textLanguage', 'humdrum:TXL')
        self.checkUniqueNamedItem('popularTitle', 'humdrum:OTP')
        self.checkUniqueNamedItem('parentTitle', 'humdrum:OPR')
        self.checkUniqueNamedItem('actNumber', 'humdrum:OAC')
        self.checkUniqueNamedItem('sceneNumber', 'humdrum:OSC')
        self.checkUniqueNamedItem('movementNumber', 'humdrum:OMV')
        self.checkUniqueNamedItem('movementName', 'humdrum:OMD')
        self.checkUniqueNamedItem('opusNumber', 'humdrum:OPS')
        self.checkUniqueNamedItem('number', 'humdrum:ONM')
        self.checkUniqueNamedItem('volumeNumber', 'humdrum:OVM')
        self.checkUniqueNamedItem('dedicatedTo', 'humdrum:ODE')
        self.checkUniqueNamedItem('commissionedBy', 'humdrum:OCO')
        self.checkUniqueNamedItem('countryOfComposition', 'humdrum:OCY')
        self.checkUniqueNamedItem('localeOfComposition', 'humdrum:OPC')
        self.checkUniqueNamedItem('groupTitle', 'humdrum:GTL')
        self.checkUniqueNamedItem('associatedWork', 'humdrum:GAW')
        self.checkUniqueNamedItem('collectionDesignation', 'humdrum:GCO')
        self.checkUniqueNamedItem('attributedComposer', 'humdrum:COA',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('suspectedComposer', 'humdrum:COS',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('composerAlias', 'humdrum:COL',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('composerCorporate', 'humdrum:COC',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('orchestrator', 'humdrum:LOR',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('originalDocumentOwner', 'humdrum:YOO',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('originalEditor', 'humdrum:YOE',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('electronicEditor', 'humdrum:EED',
            valueType=metadata.Contributor)
        self.checkUniqueNamedItem('electronicEncoder', 'humdrum:ENC',
            valueType=metadata.Contributor)

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test, 'noDocTest')
