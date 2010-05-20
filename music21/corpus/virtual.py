# -*- coding: UTF-8 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         corpus/base.py
# Purpose:      Access to the corpus collection
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'The virtual.py module is a library of references to remotely stored music data files, as well as meta-data necessary to download and, if available, access an already downloaded file.'

import doctest
import unittest

import music21
from music21 import common
from music21 import environment
_MOD = 'converter.py'
environLocal = environment.Environment(_MOD)




class VirtualWork(object):
    def __init__(self):
        self.composer = None
        self.title = None
        # provide a partial path in the corpus that represents this file
        self.corpusPath = None
        # a list of URLs in order of best usage
        # these probably should all be the same format
        self.urlList = []

#     def _getDstFp(self, dir):
#         '''Given a directory (usually the users scratch directory) create
#         a file path based on the md5 of the works title. This means that all works must have unique titles in the virtual corpus. 
#         '''
#         if dir == None:
#             raise ValueError
#         return os.path.join(dir, 'm21-' + common.getMd5(self.title) + '.p')

    def getUrlByExt(self, extList=None):
        '''Given a request for an extension, find a best match for a URL from 
        the list of known URLs. If ext is None, return the first URL.
        '''
        if not common.isListLike(extList):
            extList = [extList]
        if extList == None or extList == [None]:
            return [self.urlList[0]] # return a list of all 

        post = []
        for ext in extList:
            for url in self.urlList:
                format, extFound = common.findFormatExtURL(url)
                #environLocal.printDebug([extFound, ext])
                if extFound == ext:
                    post.append(url)
        return post # no match




#-------------------------------------------------------------------------------
# keep these in alphabetical order

class BachBWV1007Prelude(VirtualWork):
    def __init__(self):
        '''
        >>> a = BachBWV1007Prelude()
        >>> a.getUrlByExt('.xml')
        ['http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=xml']

        '''
        VirtualWork.__init__(self)

        self.composer = 'Johann Sebastian Bach'
        self.title = 'Prelude from Cello Suite No. 1 in G Major, BWV 1007'
        self.corpusPath = 'bach/bwv1007/prelude'        
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=xml')        
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=kern')


class BachBWV772(VirtualWork):
    def __init__(self):
        VirtualWork.__init__(self)

        self.composer = 'Johann Sebastian Bach'
        self.title = 'Invention No. 1 in C Major, BWV 772'
        self.corpusPath = 'bach/bwv772'        
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=osu/classical/bach/inventions&file=inven01.krn&f=xml')  


class BachBWV773(VirtualWork):
    def __init__(self):
        VirtualWork.__init__(self)

        self.composer = 'Johann Sebastian Bach'
        self.title = 'Invention No. 2 in C Minor, BWV 773'
        self.corpusPath = 'bach/bwv773'        
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=osu/classical/bach/inventions&file=inven02.krn&f=xml')  
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=osu/classical/bach/inventions&file=inven02.krn&f=kern')  


class ColtraneGiantSteps(VirtualWork):
    # this does not work yet as we cannot handle mxl files
    def __init__(self):
        VirtualWork.__init__(self)

        self.composer = 'John Coltrane'
        self.title = 'Giant Steps'
        self.corpusPath = 'coltrane/giantSteps'        
        self.urlList.append('http://static.wikifonia.org/1164/musicxml.mxl')        



class SchubertD576(VirtualWork):
    def __init__(self):
        VirtualWork.__init__(self)

        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-1'        
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/schubert/piano/d0576&file=d0576-06.krn&f=xml')        


class SchubertD5762(VirtualWork):
    def __init__(self):
        VirtualWork.__init__(self)
        
        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-6'
        self.urlList.append('http://web.mit.edu/sadoian/Public/corpus/schubert576-6.xml')


class SchubertD5763(VirtualWork):
    def __init__(self):
        VirtualWork.__init__(self)
        
        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-6a'
        self.urlList.append('http://web.mit.edu/sadoian/Public/corpus/schubert576-6a.xml')


class SchubertD5764(VirtualWork):
    def __init__(self):
        VirtualWork.__init__(self)
        
        self.composer = 'Franz Schubert'
        self.title = '13 Variations on a Theme by Anselm Hüttenbrenner'
        self.corpusPath = 'schubert/d576-6b'
        self.urlList.append('http://web.mit.edu/sadoian/Public/corpus/schubert576-6b.xml')


class PachelbelCanonD(VirtualWork):
    def __init__(self):
        VirtualWork.__init__(self)

        self.composer = 'Johann Pachelbel'
        self.title = 'Canon in D Major'
        self.corpusPath = 'pachelbel/canon'        
        self.urlList.append('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/pachelbel&file=canon.krn&f=xml')        









#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    # interpreter loading

    def runTest(self):
        pass

    def testParseURL(self):
        urlA = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/schubert/piano/d0576&file=d0576-06.krn&f=xml'
        urlB = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/schubert/piano/d0576&file=d0576-06.krn&f=kern'
        urlC = 'http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=xml'

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        '''Test copyinng all objects defined in this module
        '''
        a = BachBWV1007Prelude()
        self.assertNotEquals(a.getUrlByExt(['.xml']), [])
        self.assertNotEquals(a.getUrlByExt(['.krn']), [])

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == "__main__":
    music21.mainTest(Test)
    #music21.mainTest(Test, TestExternal)


