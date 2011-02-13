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
import tarfile
import distutils.sysconfig

# define on or more directories to try to use as a scratch directory for download; the first valid match will be used.
SCRATCH = ['~/_download', '/_scratch']

# set a download path if downloading source
M21_SOURCE = 'http://music21.googlecode.com/files/music21-0.2.5a4.tar.gz'
# if true, a new installer will always be downloaded. otherwise, if an appropriately named path exists on the local machine, downloading will be skipped
FORCE_DOWNLOAD = False
# if true, and an extracted installer is already present, use the extracted file rather than re-extracting
FORCE_EXTRACT = False

# can set the python to be used
PY_BIN = ['python']


# to run on a local svn check out, and assuming that checkout is in ~/music21, 
# first build a source distribution
# python setup.py sdist
# then pass path to source distribution to test routine (update the version)
# python music21/test/testInstallation.py ~/music21/dist/music21-0.3.4a8.tar.gz


#-------------------------------------------------------------------------------
class InstallRunner:
    '''Base class for install runners. All methods in this class are cross platform. Platform specific code should be placed in subclasses.
    '''

    def __init__(self):
    
        self._fpScratch = None
        self._toClean = [] # store list of file paths to clean


    def _findScratch(self):
        '''Find a scratch directory on this machine. This is not the music21 scratch directory, but a download or similar directory to store or copy installation packages that are being tested. Everything added into this directory will be deleted in cleaning. 
        '''
        for fp in SCRATCH:
            fp = os.path.expanduser(fp) # support ~
            if os.path.exists(fp) and os.path.isdir(fp):
                return fp
        raise Exception('cannot find a valid scratch path')

    def download(self):
        '''Optionally download the installation package from on-line. This is not usually run, as a local build (int0 dist) is always going to be more up to date. Instead, pass a file path to an installer package, use as an arg to run.
        '''
        pass

    def copyToScratch(self, fp):
        pass

    def _extractTar(self, fp):
        # remove tar
        fpExtracted = fp.replace('.tar.gz', '')
        
        if not os.path.exists(fpExtracted) or FORCE_EXTRACT:
            tar = tarfile.open(fp)
            tar.extractall(path=self._fpScratch)
            tar.close()

        if not os.path.exists(fpExtracted):
            raise Exception('cannot find expected extaction: %s' % fpExtracted)
        return fpExtracted
        

    def install(self, fp):
        pass

    def test(self):
        pass

    def _getSitePackageDir(self):
        '''Get the music21 site package dir
        '''
        dir = distutils.sysconfig.get_python_lib()
        fp = os.path.join(dir, 'music21')
        if not os.path.exists(fp):
            raise Exception('cannot find music21 in site-packages: %s' % fp)
        return fp

    def _findSitePackagesToClean(self):
        found = []
        fp = distutils.sysconfig.get_python_lib()
        for fn in os.listdir(fp):
            if fn.startswith('music21'):
                found.append(os.path.join(fp, fn))
        return found
        
    def clean(self):
        pass

    def run(self, fpDistribution=None):
        '''Run the installer, test, and clean.

        If `fpDistribution` is not None, the specified distribution will be used. Thus, a built distribution on a local machine can be pass by file path.

        The run does three things: install the source, run all tests, and tehn remove the installation. 
        '''
        if fpDistribution == None:
            fpSource = self.download()
        else:
            fpSource = self.copyToScratch(fpDistribution)
        # for now, just get the first py bin
        self.install(fpSource, PY_BIN[0])
        self.test(PY_BIN[0])
        self.clean()


#-------------------------------------------------------------------------------
class InstallRunnerNix(InstallRunner):
    '''Install runner for mac, linux, and unix machines.
    '''
    def __init__(self):
        InstallRunner.__init__(self)
        self._fpScratch = self._findScratch()

    def download(self):
        print('using download file path: %s' % self._fpScratch)
        junk, fn = os.path.split(M21_SOURCE)
        dst = os.path.join(self._fpScratch, fn)

        if not os.path.exists(dst) or FORCE_DOWNLOAD:
            cmd = 'wget -P %s %s' % (self._fpScratch, M21_SOURCE)
            os.system(cmd)
        # return resulting file name
        self._toClean.append(dst)
        return dst

    def copyToScratch(self, fp):
        '''Copy a file to a scratch directory.

        This is used to store the downloaded or passed distribution file. 
        '''
        junk, fn = os.path.split(fp)
        dst = os.path.join(self._fpScratch, fn)
        cmd = 'cp %s %s' % (fp, dst)
        os.system(cmd)
        self._toClean.append(dst)
        return dst

    def install(self, fp, pyBin):
        '''Decompress, then install into site packages using setup.py install.
        '''
        # first, decompress
        print('extracting: %s' % fp)
        fpExtracted = self._extractTar(fp)
        self._toClean.append(fpExtracted)

        fpSetup = os.path.join(fpExtracted, 'setup.py')
        if not os.path.exists(fpSetup):
            raise Exception('cannot find seutp.py: %s' % fpSetup)

        # create install command
        cmd = 'cd %s; sudo %s setup.py install' % (fpExtracted, pyBin)
        print('running setup.py: %s' % cmd)
        os.system(cmd)

        self._toClean += self._findSitePackagesToClean()


    def test(self, pyBin):
        '''Run the main music21 test script.

        This assumes that the only music21 files foudn in the search pat are those that are contained in site-packages. If there is another music21 installation that is also in a search path on this machine, it is possible that those files, not the ones just installed, are being tested.
        '''
        testScript = os.path.join(self._getSitePackageDir(), 'test', 'test.py')
        cmd = '%s %s' % (pyBin, testScript)
        os.system(cmd)

    def clean(self):
        '''Remove all files created in this installation. 
        '''
        for fp in self._toClean:
            print('cleaning: %s' % fp)
            cmd = 'sudo rm -R %s' % fp
            os.system(cmd)





if __name__ == '__main__':
    
    if len(sys.argv) > 0:
        fpDist = sys.argv[1]
    else:
        fpDist = None

    ir = InstallRunnerNix()
    ir.run(fpDist)



#------------------------------------------------------------------------------
# eof




