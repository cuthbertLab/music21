# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import typing as t
import unittest

from music21 import converter
from music21 import corpus
from music21 import metadata
from music21.musicxml import testFiles as mTF


class Test(unittest.TestCase):
    # When `maxDiff` is None, `assertMultiLineEqual()` provides better errors.
    maxDiff = None

    def testMetadataLoadCorpus(self):
        c = converter.parse(mTF.mozartTrioK581Excerpt)
        md = c.metadata

        self.assertEqual(
            md['movementNumber'],
            (metadata.Text('3'),)
        )
        self.assertEqual(
            md['movementName'],
            (metadata.Text('Menuetto (Excerpt from Second Trio)'),)
        )
        self.assertEqual(
            md['title'],
            (metadata.Text('Quintet for Clarinet and Strings'),)
        )
        self.assertEqual(
            md['number'],
            (metadata.Text('K. 581'),)
        )
        self.assertEqual(
            md['composer'],
            (metadata.Contributor(role='composer', name='Wolfgang Amadeus Mozart'),)
        )

        c = converter.parse(mTF.binchoisMagnificat)
        md = c.metadata
        self.assertEqual(
            md['composer'],
            (metadata.Contributor(role='composer', name='Gilles Binchois'),)
        )

    def testMetadataLoadCorpusBackwardCompatible(self):
        c = converter.parse(mTF.mozartTrioK581Excerpt)
        md = c.metadata

        self.assertEqual(
            md.movementNumber,
            '3'
        )
        self.assertEqual(
            md.movementName,
            'Menuetto (Excerpt from Second Trio)'
        )
        self.assertEqual(
            md.title,
            'Quintet for Clarinet and Strings'
        )
        self.assertEqual(
            md.number,
            'K. 581'
        )
        # get contributors directly from Metadata interface
        self.assertEqual(
            md.composer,
            'Wolfgang Amadeus Mozart'
        )

        c = converter.parse(mTF.binchoisMagnificat)
        md = c.metadata
        self.assertEqual(
            md.composer,
            'Gilles Binchois'
        )

    def testJSONSerializationMetadata(self):
        md = metadata.Metadata(
            title='Concerto in F',
            date='2010',
            composer='Frank',
        )
        # environLocal.printDebug([str(md.json)])
        self.assertEqual(md.composer, 'Frank')
        self.assertEqual(md.dateCreated, '2010/--/--')
        self.assertEqual(md.composer, 'Frank')
        self.assertEqual(md.title, 'Concerto in F')

        # test getting metadata from an imported source
        c = converter.parse(mTF.mozartTrioK581Excerpt)
        md = c.metadata

        self.assertEqual(
            md.movementNumber, '3'
        )
        self.assertEqual(
            md.movementName,
            'Menuetto (Excerpt from Second Trio)'
        )
        self.assertEqual(
            md.title,
            'Quintet for Clarinet and Strings'
        )
        self.assertEqual(
            md.number,
            'K. 581'
        )
        self.assertEqual(
            md.composer,
            'Wolfgang Amadeus Mozart'
        )

    def testRichMetadata01(self):
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
        opus = corpus.parse('essenFolksong/teste')
        self.assertEqual(len(opus.scores), 8)

        score = opus.getScoreByNumber(4)
        self.assertEqual(
            score.metadata.localeOfComposition,
            'Asien, Ostasien, China, Sichuan'
        )

        richMetadata = metadata.RichMetadata()
        richMetadata.merge(score.metadata)
        richMetadata.update(score)

        self.assertEqual(
            richMetadata.localeOfComposition,
            'Asien, Ostasien, China, Sichuan'
        )

    def testMetadataSearch(self):
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
        score = corpus.parse('bwv66.6')
        richMetadata = metadata.RichMetadata()
        richMetadata.merge(score.metadata)
        richMetadata.update(score)
        self.assertEqual(richMetadata.noteCount, 165)
        self.assertEqual(richMetadata.quarterLength, 36.0)

    def checkUniqueNamedItem(
            self,
            uniqueName: str,
            namespaceName: str,
            contributorRole: t.Optional[str] = None,
            valueType: type = metadata.Text):

        if ':' not in namespaceName:
            # It's just the namespace because name == uniqueName,
            # and I didn't want to spend the time to type it twice...
            namespaceName += ':' + uniqueName

        if namespaceName.startswith('marcrel'):
            # The marcrel namespace is all Contributors (more typing saved)
            valueType = metadata.Contributor

        md = metadata.Metadata()

        self.assertTrue(md._isStandardUniqueName(uniqueName))
        self.assertFalse(md._isStandardNamespaceName(uniqueName))

        self.assertTrue(md._isStandardNamespaceName(namespaceName))
        self.assertFalse(md._isStandardUniqueName(namespaceName))

        if uniqueName != 'software':
            # software is always auto-filled-in with the music21 version
            # even in an empty metadata object, so we can't check that
            # it's not there (it is).
            item = getattr(md, uniqueName)
            self.assertIsNone(item)
            itemTuple = md[uniqueName]
            self.assertEqual(itemTuple, tuple())
            itemTuple = md[namespaceName]
            self.assertEqual(itemTuple, tuple())

        if valueType is metadata.DatePrimitive:
            md[namespaceName] = ['1987/6/11']
            self.assertEqual(
                getattr(md, uniqueName),
                '1987/06/11'
            )
            md[uniqueName] = ('1989/6/11',)
            self.assertEqual(
                getattr(md, uniqueName),
                '1989/06/11'
            )
        elif valueType is metadata.Copyright:
            md[namespaceName] = [f'Copyright ©1987 {namespaceName}']
            self.assertEqual(
                getattr(md, uniqueName),
                f'Copyright ©1987 {namespaceName}'
            )
            md[uniqueName] = (f'Copyright ©1987 {uniqueName}',)
            self.assertEqual(
                getattr(md, uniqueName),
                f'Copyright ©1987 {uniqueName}'
            )
        elif valueType is metadata.Contributor:
            md[namespaceName] = [f'The {namespaceName}']
            self.assertEqual(
                getattr(md, uniqueName),
                f'The {namespaceName}'
            )
            md[uniqueName] = (f'The {uniqueName}',)
            self.assertEqual(
                getattr(md, uniqueName),
                f'The {uniqueName}'
            )
        elif valueType is metadata.Text:
            md[namespaceName] = [f'The {namespaceName}']
            if namespaceName == 'musicxml:software':
                # getattr('software') returns a tuple (it's a plural attribute)
                self.assertEqual(
                    getattr(md, uniqueName),
                    (f'The {namespaceName}',)
                )
            else:
                self.assertEqual(
                    getattr(md, uniqueName),
                    f'The {namespaceName}'
                )
            md[uniqueName] = (f'The {uniqueName}',)
            if namespaceName == 'musicxml:software':
                # getattr('software') returns a tuple (it's a plural attribute)
                self.assertEqual(
                    getattr(md, uniqueName),
                    (f'The {uniqueName}',)
                )
            else:
                self.assertEqual(
                    getattr(md, uniqueName),
                    f'The {uniqueName}'
                )
        elif valueType is int:
            md[namespaceName] = [17]
            self.assertEqual(
                getattr(md, uniqueName),
                '17'
            )
            md[uniqueName] = (1,)
            self.assertEqual(
                getattr(md, uniqueName),
                '1'
            )
        else:
            self.fail('internal test error: invalid valueType')


        if valueType is metadata.DatePrimitive:
            md.add(namespaceName,
                   [metadata.DateBetween(['1987', '1989']),
                    metadata.DateSingle('1989/6/11/4:50:32')])
            self.assertEqual(
                getattr(md, uniqueName),
                '1989/06/11, 1987/--/-- to 1989/--/--, 1989/06/11/04:50:32'
            )
            self.assertEqual(
                md[uniqueName],
                (
                    metadata.DateSingle('1989/06/11'),
                    metadata.DateBetween(['1987', '1989']),
                    metadata.DateSingle('1989/6/11/4:50:32')
                )
            )
        elif valueType is metadata.Copyright:
            md.add(
                namespaceName,
                metadata.Text('Lyrics copyright ©1987 Kat Bjelland')
            )
            md.add(
                uniqueName,
                (
                    metadata.Copyright(
                        'Other content copyright ©1987 Lori Barbero',
                        role='other'),
                    metadata.Copyright(
                        metadata.Text('Music contributions copyright ©1987 Michelle Leon'),
                        role='music contributions')
                )
            )
            self.assertEqual(
                getattr(md, uniqueName),
                f'Copyright ©1987 {uniqueName}'
                + ', Lyrics copyright ©1987 Kat Bjelland'
                + ', Other content copyright ©1987 Lori Barbero'
                + ', Music contributions copyright ©1987 Michelle Leon'
            )
            self.assertEqual(
                md[uniqueName],
                (
                    metadata.Copyright(f'Copyright ©1987 {uniqueName}'),
                    metadata.Copyright('Lyrics copyright ©1987 Kat Bjelland'),
                    metadata.Copyright(
                        'Other content copyright ©1987 Lori Barbero',
                        role='other'
                    ),
                    metadata.Copyright(
                        metadata.Text('Music contributions copyright ©1987 Michelle Leon'),
                        role='music contributions'
                    )
                )
            )
        elif valueType is metadata.Contributor:
            md.add(
                uniqueName,
                [
                    metadata.Text(f'The 2nd {uniqueName}'),
                    metadata.Contributor(
                        role=contributorRole if contributorRole else uniqueName,
                        name=f'The 3rd {uniqueName}')
                ]
            )
            self.assertEqual(
                getattr(md, uniqueName),
                f'The {uniqueName} and 2 others'
            )
            self.assertEqual(
                md[uniqueName],
                (
                    metadata.Contributor(name=f'The {uniqueName}', role=uniqueName),
                    metadata.Contributor(name=f'The 2nd {uniqueName}', role=uniqueName),
                    metadata.Contributor(
                        role=contributorRole if contributorRole else uniqueName,
                        name=f'The 3rd {uniqueName}')
                )
            )
        elif valueType is metadata.Text:
            md.add(
                namespaceName,
                [
                    metadata.Text(f'The 2nd {uniqueName}'),
                    metadata.Text(f'The 3rd {uniqueName}')
                ]
            )
            if uniqueName == 'software':
                # software is a plural attribute (returns a tuple)
                self.assertEqual(
                    getattr(md, uniqueName),
                    (f'The {uniqueName}', f'The 2nd {uniqueName}', f'The 3rd {uniqueName}')
                )
            else:
                self.assertEqual(
                    getattr(md, uniqueName),
                    f'The {uniqueName}, The 2nd {uniqueName}, The 3rd {uniqueName}'
                )
            self.assertEqual(
                md[uniqueName],
                (
                    metadata.Text(f'The {uniqueName}'),
                    metadata.Text(f'The 2nd {uniqueName}'),
                    metadata.Text(f'The 3rd {uniqueName}')
                )
            )
        elif valueType is int:
            md.add(namespaceName, [2, 3])
            self.assertEqual(getattr(md, uniqueName), '1, 2, 3')
            self.assertEqual(md[uniqueName], (1, 2, 3))

        # We've tested md[uniqueName], check to make sure that md[namespaceName]
        # returns exactly the same thing.
        mdItemsUnique = md[uniqueName]
        mdItemsNamespaceName = md[namespaceName]
        self.assertEqual(len(mdItemsUnique), len(mdItemsNamespaceName))
        for itemUnique, itemNamespaceName in zip(mdItemsUnique, mdItemsNamespaceName):
            self.assertIsInstance(itemUnique, valueType)
            self.assertIsInstance(itemNamespaceName, valueType)
            self.assertEqual(itemUnique, itemNamespaceName)

        if valueType is metadata.Contributor:
            for itemNamespaceName in mdItemsNamespaceName:
                # I'm asserting this way to keep mypy happy with itemNamespaceName.role
                # self.assertIsInstance isn't sufficient, apparently.
                assert isinstance(itemNamespaceName, metadata.Contributor)
                self.assertEqual(itemNamespaceName.role,
                    contributorRole if contributorRole else uniqueName)

    def testUniqueNameAccess(self):
        self.checkUniqueNamedItem('abstract', 'dcterms')
        self.checkUniqueNamedItem('accessRights', 'dcterms')
        self.checkUniqueNamedItem('alternativeTitle', 'dcterms:alternative')
        self.checkUniqueNamedItem('audience', 'dcterms')
        self.checkUniqueNamedItem(
            'dateAvailable',
            'dcterms:available',
            valueType=metadata.DatePrimitive
        )
        self.checkUniqueNamedItem('bibliographicCitation', 'dcterms')
        self.checkUniqueNamedItem('conformsTo', 'dcterms')
        self.checkUniqueNamedItem('dateCreated',
                                  'dcterms:created',
                                  valueType=metadata.DatePrimitive)
        self.checkUniqueNamedItem('otherDate', 'dcterms:date', valueType=metadata.DatePrimitive)
        self.checkUniqueNamedItem('dateAccepted', 'dcterms', valueType=metadata.DatePrimitive)
        self.checkUniqueNamedItem('dateCopyrighted', 'dcterms', valueType=metadata.DatePrimitive)
        self.checkUniqueNamedItem('dateSubmitted', 'dcterms', valueType=metadata.DatePrimitive)
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
        self.checkUniqueNamedItem('dateIssued',
                                  'dcterms:issued',
                                  valueType=metadata.DatePrimitive)
        self.checkUniqueNamedItem('isVersionOf', 'dcterms')
        self.checkUniqueNamedItem('language', 'dcterms')
        self.checkUniqueNamedItem('license', 'dcterms')
        self.checkUniqueNamedItem('medium', 'dcterms')
        self.checkUniqueNamedItem(
            'dateModified',
            'dcterms:modified',
            valueType=metadata.DatePrimitive
        )
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
        self.checkUniqueNamedItem('dateValid',
                                  'dcterms:valid',
                                  valueType=metadata.DatePrimitive)
        self.checkUniqueNamedItem('adapter', 'marcrel:ADP')
        self.checkUniqueNamedItem('analyst', 'marcrel:ANL')
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
        self.checkUniqueNamedItem('proofreader', 'marcrel:PFR')
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
        self.checkUniqueNamedItem('software', 'musicxml')
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
        self.checkUniqueNamedItem(
            'attributedComposer',
            'humdrum:COA',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'suspectedComposer',
            'humdrum:COS',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'composerAlias',
            'humdrum:COL',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'composerCorporate',
            'humdrum:COC',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'orchestrator',
            'humdrum:LOR',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'firstPublisher',
            'humdrum:PPR',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'dateFirstPublished',
            'humdrum:PDT',
            valueType=metadata.DatePrimitive
        )
        self.checkUniqueNamedItem('publicationTitle', 'humdrum:PTL')
        self.checkUniqueNamedItem('placeFirstPublished', 'humdrum:PPP')
        self.checkUniqueNamedItem('publishersCatalogNumber', 'humdrum:PC#')
        self.checkUniqueNamedItem('scholarlyCatalogName', 'humdrum:SCA')
        self.checkUniqueNamedItem('scholarlyCatalogAbbreviation', 'humdrum:SCT')
        self.checkUniqueNamedItem('manuscriptSourceName', 'humdrum:SMS')
        self.checkUniqueNamedItem('manuscriptLocation', 'humdrum:SML')
        self.checkUniqueNamedItem('manuscriptAccessAcknowledgement', 'humdrum:SMA')
        self.checkUniqueNamedItem(
            'originalDocumentOwner',
            'humdrum:YOO',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'originalEditor',
            'humdrum:YOE',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'electronicEditor',
            'humdrum:EED',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'electronicEncoder',
            'humdrum:ENC',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'electronicPublisher',
            'humdrum:YEP',
            valueType=metadata.Contributor
        )
        self.checkUniqueNamedItem(
            'electronicReleaseDate',
            'humdrum:YER',
            valueType=metadata.DatePrimitive
        )
        self.checkUniqueNamedItem(
            'fileFormat',
            'm21FileInfo',
            valueType=metadata.Text
        )
        self.checkUniqueNamedItem(
            'filePath',
            'm21FileInfo',
            valueType=metadata.Text
        )
        self.checkUniqueNamedItem(
            'fileNumber',
            'm21FileInfo',
            valueType=int
        )


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test, 'noDocTest')
