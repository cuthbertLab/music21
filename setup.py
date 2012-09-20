#!/usr/local/bin/python
#-------------------------------------------------------------------------------
# Name:          setup.py
# Purpose:       install
#
# Authors:       Christopher Ariza
#                Michael Scott Cuthbert
#
# Copyright:     (c) 2009-2012 The music21 Project
# License:       LGPL
#-------------------------------------------------------------------------------

import sys, os
import music21
from music21 import common


DESCRIPTION = 'A Toolkit for Computer-Aided Musical Analysis and Manipulation.'
DESCRIPTION_LONG = 'A Toolkit for Computer-Aided Musical Analysis and Manipulation. Developed at MIT. Michael Scott Cuthbert, Principal Investigator, Christopher Ariza, Lead Programmer. The development of music21 is supported by the generosity of the Seaver Institute.'



def _getPackagesList():
    """List of all packages, delimited by period, with relative path names. Assigned to setup.py's `packages` argument.
    """
    # example data
    #     pkg = (  'music21', 
    #              'music21.analysis', 
    #              'music21.composition', 

    pkg = common.getPackageDir()
    for directory in pkg:
        print('found package: %s' % directory)
    return pkg

def _getPackageData():
    '''Assigned to setup.py's `package_data` argument. This is not used in the sdist distribution, but is used in Windows and EGGs.

    This list will be assigned to dictionary with the package name.
    '''
    # example data
    #     pkgData = ['corpus/bach/*.xml',
    #              'corpus/bach/*.krn',
    #              'corpus/beethoven/*.xml',
    #              'corpus/beethoven/opus18no1/*.xml',
     
    #              'doc/*.html',
    #              'doc/html/*.html',
    #              'doc/html/_images/*.png',
    #              'doc/html/_static/*.css',

    # get all possible combinations
    pkgData = common.getPackageData()
    return pkgData


def _getClassifiers():
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers = [
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Environment :: Web Environment',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Developers',
            'Intended Audience :: Education',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
            'Natural Language :: English', 
            'Operating System :: MacOS',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Multimedia :: Sound/Audio',
            'Topic :: Multimedia :: Sound/Audio :: MIDI',
            'Topic :: Artistic Software',
            'Topic :: Software Development :: Libraries :: Python Modules',
            ]
    return classifiers
     

#-------------------------------------------------------------------------------
def writeManifestTemplate(fpPackageDir):
    '''
    The manifest input file is used by distutils to make the 'sdist' distribution. This is not used in the creation of EGG files. 
    '''
    dst = os.path.join(fpPackageDir, 'MANIFEST.in')
    msg = []
    
    # when changing this list, also need to update common.getPackageData()
    msg.append('global-include *.py *.txt *.xml *.krn *.mxl *.pdf *.html *.css *.js *.png *.tiff *.jpg *.xls *.mid *.abc *.json *.md *.zip *.rntxt *.command *.scl *.nwctxt *.wav \n')
    # order matters: remove dist and buildDoc directories after global include
    # adding .py to this list gets the obsolete dir

    msg.append('prune dist\n')
    msg.append('prune buildDoc\n')
    msg.append('prune obsolete\n')

    try:
        f = open(dst, 'w')
        f.writelines(msg)
        f.close()
    except Exception as e:
        raise Exception('Could not write MANIFEST.in in %s : %s' % (fpPackageDir, str(e)))


def runDisutils(bdistType=None):
    '''The main distutils routine. 

    When called without arguments, this performs a standard distutils installation. 
    '''
    if bdistType == 'bdist_egg':
        print('using setuptools')
        from setuptools import setup #@UnusedImport
    else:
        print('using distutils')
        from distutils.core import setup #@Reimport

    setup(name = 'music21', 
        version = music21.VERSION_STR,
        description = DESCRIPTION, 
        long_description = DESCRIPTION_LONG,
        author = 'Michael Scott Cuthbert, the music21 project, others',
        author_email = 'cuthbert@mit.edu',
        license = 'LGPL', 
        url = 'http://code.google.com/p/music21',
        classifiers = _getClassifiers(),
        download_url = 'http://music21.googlecode.com/files/music21-%s.tar.gz' % music21.VERSION_STR,
        packages = _getPackagesList(), 
        package_data = {'music21': _getPackageData()},
    ) # close setup args
    
        

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) == 1: # no args
        print('welcome to music21\nto run setup.py for installation, enter, as an administrator (or with sudo): python setup.py install\n')
    
    elif sys.argv[1] in ['bdist', 'sdist', 'register', 'bdist_mpkg',
                            'bdist_rpm', 'bdist_deb', 'bdist_wininst',
                            'bdist_egg']:
        fpMusic21 = music21.__path__[0] # list, get first item
        fpPackageDir = os.path.dirname(fpMusic21)
        print('fpPackageDir = %s' % fpPackageDir)
        writeManifestTemplate(fpPackageDir)
        runDisutils(sys.argv[1])
    
    elif sys.argv[1] in ['install']:
        runDisutils('install')
    
    else:
        print('cannot process provided arguments: %s\n' % sys.argv[1:])


