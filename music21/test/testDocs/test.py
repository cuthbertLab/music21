# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testDocs.py
# Purpose:      Tests the documentation.
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
To use this module, cd into the test/testDocs directory. Then, run test.py from the command line. Note that running this file requires moving and re-processing the documentation files. 
'''

import copy, types, random
import doctest, unittest
import os
import shutil

import music21
from music21 import common

from music21 import environment
_MOD = "metadata.py"
environLocal = environment.Environment(_MOD)




class DocTester(object):

    def __init__(self):
        self.srcDirRst = os.path.join(common.getBuildDocFilePath(), 'rst')
        self.dstDirRst = os.path.join(common.getTestDocsFilePath(), 'testRst')
        self.testConfigDir = os.path.join(common.getTestDocsFilePath())

    def _getRSTFileNames(self):
        fileNames = []
        for fn in os.listdir(self.srcDirRst):
            if fn.endswith('rst') and not fn.startswith('module'):
                fileNames.append(fn)
        #print fileNames
        return fileNames

    def _transferDocFiles(self):
        '''Get all RST doc files that are not auto-generated from modules
        '''
        # need find all .rst files that do not start with 'module'
        # copy all the necessary doc files to the temp dir       
        for fn in self._getRSTFileNames():
            src = os.path.join(self.srcDirRst, fn)
            dst = os.path.join(self.dstDirRst, fn)
            shutil.copy2(src, dst)

    def _cleanUp(self):
        '''Remove the copied .rst files so as not to keep duplicates.
        '''
        for fn in self._getRSTFileNames():
            try:
                os.remove(os.path.join(self.dstDirRst, fn))
            except OSError:
                environLocal.pd(['cannot remove temporary file:', fn])

    def run(self):
        self._transferDocFiles()
        try:
            import sphinx
        except ImportError:
            raise BuildException("Building documentation requires the Sphinx toolkit. Download it by typing 'easy_install -U Sphinx' at the command line or at http://sphinx.pocoo.org/")

        sphinxList = ['sphinx', '-E', 
                      '-b', 'doctest', # build as test
                      # use a different config file
                      '-c', self.testConfigDir, 
                     self.dstDirRst, self.dstDirRst] 
        # run
        statusCode = sphinx.main(sphinxList)
        self._cleanUp()



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

