# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testDocs.py
# Purpose:      tests from or derived from the Documentation
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import copy, types, random
import doctest, unittest
import os
import shutil

import music21
from music21 import common


class DocTester(object):

    def __init__(self):
        self.srcDirRst = os.path.join(common.getBuildDocFilePath(), 'rst')
        self.dstDirRst = os.path.join(common.getTestDocsFilePath(), 'testRst')

        self.testConfigDir = os.path.join(common.getTestDocsFilePath())

    def _transferDocFiles(self):
        '''Get all RST doc files that are not auto-generated from modules
        '''
        # need find all .rst files that do not start with 'module'
        fileNames = ['quickStart.rst']
        # copy all the necessary doc files to the temp dir       
        for fn in fileNames:
            src = os.path.join(self.srcDirRst, fn)
            dst = os.path.join(self.dstDirRst, fn)
            shutil.copy2(src, dst)
 

    def run(self):
        self._transferDocFiles()

        try:
            import sphinx
        except ImportError:
            raise BuildException("Building documentation requires the Sphinx toolkit. Download it by typing 'easy_install -U Sphinx' at the command line or at http://sphinx.pocoo.org/")

        sphinxList = ['sphinx', '-E', 
                      '-b', 'doctest', # build as text
                      # use a different config file
                      '-c', self.testConfigDir, 
                     self.dstDirRst, self.dstDirRst] 
        # run
        statusCode = sphinx.main(sphinxList)




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testMain(self):
        # collect all files

        pass



if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    #music21.mainTest(Test)

    dt = DocTester()
    dt.run()

