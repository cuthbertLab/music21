#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         testInstallation.py
# Purpose:      Controller for automated download, install, and testing.
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


# do not import music21; this does not rely on m21 code
import sys, os

# define on or more directories to try to use as a scratch directory for download

SCRATCH = ['~/_download', '/_scratch']

M21_SOURCE = 'http://music21.googlecode.com/files/music21-0.2.5a4.tar.gz'



class InstallRunner:

    def __init__(self):
    
        self._toClean = [] # store list of file paths to clean


    def _findScratch(self):
        for fp in SCRATCH:
            if os.path.exists(fp) and os.path.isdir(fp):
                return fp
        raise Exception('cannot find a valid scratch path')

    def download(self):
        pass

    def install(self):
        pass

    def test(self):
        pass

    def clean(self):
        pass



class InstallRunnerNix(InstallRunner):
    '''Install runner for mac, linux, and unix machines.
    '''
    def __init__(self):
        InstallRunner.__init__(self)

    def download(self):
        fpScratch = self._findScratch()
        print('using donwload file path: %s' % fpScratch)
        cmd = 'wget -P %s %s' % (fpScratch, M21_SOURCE)
        os.system(cmd)
        junk, fn = os.path.split(M21_SOURCE)
        # return resulting file name
        return os.path.join(fpScratch, fn)

    def install(self):
        pass

    def test(self):
        pass







if __name__ == '__main__':
    
    ir = InstallRunnerNix()
    print ir.download()






