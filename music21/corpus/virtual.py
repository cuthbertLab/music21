# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         corpus/virtual.py
# Purpose:      Access to the Virtual corpus collection
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
The virtual.py module is a library of references to remotely stored music data files,
as well as metadata necessary to download and, if available, access an already downloaded file.

This is probably not the best way to handle this -- instead it should be a link to
a directory or listing of files and repositories, each handled as a different Corpus.

TURNED OFF in 2017 -- to be recreated with a bigger test set.

TODO: Demonstrate with JRP.
'''

import unittest

from music21 import common
from music21 import environment
_MOD = 'converter.virtual'
environLocal = environment.Environment(_MOD)


class VirtualWork:
    def __init__(self):
        self.composer = None
        self.title = None

        # provide a partial path in the corpus that represents this file
        # this path must be unique for each work
        self.corpusPath = None

        # a list of URLs in order of best usage
        # these probably should all be the same format
        self.urlList = []

#     def _getDstFp(self, dir):
#         '''Given a directory (usually the users scratch directory) create
#         a file path based on the md5 of the works title. This means that all
#         works must have unique titles in the virtual corpus.
#         '''
#         dir = pathlib.Path(dir)
#         if dir is None:
#             raise ValueError
#         return dir / ('m21-' + common.getMd5(self.title) + '.p')

    def getUrlByExt(self, extList=None):
        '''Given a request for an extension, find a best match for a URL from
        the list of known URLs. If ext is None, return the first URL.
        '''
        if not common.isListLike(extList):
            extList = [extList]
        if extList is None or extList == [None]:
            return [self.urlList[0]]  # return a list of all

        post = []
        for ext in extList:
            for url in self.urlList:
                unused_format, extFound = common.findFormatExtURL(url)
                # environLocal.printDebug([extFound, ext])
                if extFound == ext:
                    post.append(url)
        return post  # no match


# ------------------------------------------------------------------------------
# keep these in alphabetical order

class BachBWV1007Prelude(VirtualWork):
    '''

    >>> a = corpus.virtual.BachBWV1007Prelude()
    >>> a.getUrlByExt('.xml')
    ['http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml']
    '''

    def __init__(self):
        super().__init__()

        self.composer = 'Johann Sebastian Bach'
        self.title = 'Prelude from Cello Suite No. 1 in G Major, BWV 1007'
        self.corpusPath = 'bach/bwv1007/prelude'
        cello = 'http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello'
        self.urlList.append(cello + '&file=bwv1007-01.krn&f=xml')
        self.urlList.append(cello + '&file=bwv1007-01.krn&f=kern')


class BachBWV772(VirtualWork):
    def __init__(self):
        super().__init__()

        self.composer = 'Johann Sebastian Bach'
        self.title = 'Invention No. 1 in C Major, BWV 772'
        self.corpusPath = 'bach/bwv772'
        invention = 'http://kern.ccarh.org/cgi-bin/ksdata?l=osu/classical/bach/inventions'
        self.urlList.append(invention + '&file=inven01.krn&f=xml')


class BachBWV773(VirtualWork):
    def __init__(self):
        super().__init__()

        self.composer = 'Johann Sebastian Bach'
        self.title = 'Invention No. 2 in C Minor, BWV 773'
        self.corpusPath = 'bach/bwv773'
        invention = 'http://kern.ccarh.org/cgi-bin/ksdata?l=osu/classical/bach/inventions'
        self.urlList.append(invention + '&file=inven02.krn&f=xml')
        self.urlList.append(invention + '&file=inven02.krn&f=kern')


class ColtraneGiantSteps(VirtualWork):
    # post operation: needs make accidentals
    def __init__(self):
        super().__init__()

        self.composer = 'John Coltrane'
        self.title = 'Giant Steps'
        self.corpusPath = 'coltrane/giantSteps'
        self.urlList.append('http://impromastering.com/uploads/transcription_file/file/196/'
                            'Giant_Steps__John_Coltrane_C.xml')


class SchubertD576(VirtualWork):
    def __init__(self):
        super().__init__()

        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-1'
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=cc/schubert/piano/'
                            'd0576&file=d0576-06.krn&f=xml')


class SchubertD5762(VirtualWork):
    def __init__(self):
        super().__init__()

        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-2'
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=users/'
                            'craig/classical/schubert/piano/d0576&file=d0576-02.krn&f=xml')


class SchubertD5763(VirtualWork):
    def __init__(self):
        super().__init__()

        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-3'
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/'
                            'schubert/piano/d0576&file=d0576-03.krn&f=xml')


class SchubertD5764(VirtualWork):
    def __init__(self):
        super().__init__()

        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-4'
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/'
                            'schubert/piano/d0576&file=d0576-04.krn&f=xml')


class PachelbelCanonD(VirtualWork):
    def __init__(self):
        super().__init__()

        self.composer = 'Johann Pachelbel'
        self.title = 'Canon in D Major'
        self.corpusPath = 'pachelbel/canon'
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=cc/'
                            'pachelbel&file=canon.krn&f=xml')


# ------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):  # pragma: no cover
    # interpreter loading
    pass


class Test(unittest.TestCase):

    def testBasic(self):
        '''Test copying all objects defined in the virtual corpus module
        '''
        a = BachBWV1007Prelude()
        self.assertNotEqual(a.getUrlByExt(['.xml']), [])
        self.assertNotEqual(a.getUrlByExt(['.krn']), [])
        BachBWV772()
        BachBWV773()
        ColtraneGiantSteps()
        SchubertD576()
        SchubertD5762()
        SchubertD5763()
        SchubertD5764()
        PachelbelCanonD()


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
    # music21.mainTest(Test, TestExternal)


