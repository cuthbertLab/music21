#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          setup.py
# Purpose:       install
#
# Authors:       Christopher Ariza
#                Michael Scott Cuthbert
#
# Copyright:     (c) 2009-2010 The music21 Project
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import sys, os
import music21


def _getPackagesList():
    """list of all packages, delimited by period"""
    pkg = (  'music21', 
             'music21.analysis', 
             'music21.composition', 
             'music21.corpus', 
             'music21.corpus.bach', 
             'music21.corpus.beethoven', 
             'music21.corpus.beethoven.opus18no1', 
             'music21.corpus.beethoven.opus59no1', 
             'music21.corpus.beethoven.opus59no2', 
             'music21.corpus.beethoven.opus59no3', 
             'music21.corpus.haydn', 
             'music21.corpus.haydn.opus74no1', 
             'music21.corpus.haydn.opus74no2', 
             'music21.corpus.luca', 
             'music21.corpus.mozart', 
             'music21.corpus.mozart.k80', 
             'music21.corpus.mozart.k155', 
             'music21.corpus.mozart.k156', 
             'music21.corpus.mozart.k458', 
             'music21.corpus.schumann', 
             'music21.corpus.schumann.opus41no1', 
             'music21.counterpoint', 
             'music21.demos', 
             'music21.doc', 
             'music21.humdrum', 
             'music21.lily', 
             'music21.musicxml', 
             'music21.test', 
             'music21.trecento', 
             'music21.trecento.xlrd', 
             )
    return pkg

def _getPackageData():
    pkgData = ['corpus/bach/*.xml',
             'corpus/bach/*.krn',
             'corpus/beethoven/*.xml',
             'corpus/beethoven/opus18no1/*.xml',
             'corpus/beethoven/opus18no1/*.krn',
             'corpus/beethoven/opus18no1/*.xml',
             'corpus/beethoven/opus59no1/*.xml',
             'corpus/beethoven/opus59no2/*.xml',
             'corpus/beethoven/opus59no3/*.xml',
             'corpus/haydn/opus74no1/*.xml',
             'corpus/haydn/opus74no2/*.xml',
             'corpus/luca/*.xml',
             'corpus/luca/*.mxl',
             'corpus/mozart/k80/*.xml',
             'corpus/mozart/k155/*.xml',
             'corpus/mozart/k156/*.xml',
             'corpus/mozart/k458/*.xml',
             'corpus/schumann/opus41no1/*.xml',
             'doc/*.html',
             'doc/html/*.html',
             'doc/html/_images/*.png',
             'doc/html/_static/*.css',
             'doc/html/_static/*.png',
             'doc/html/_static/*.js',

    ] 
    return pkgData


def _getClassifiers():
    classifiers = [
            # 'Development Status :: 5 - Production/Stable',
            # 'Environment :: Console',
             'Intended Audience :: End Users/Desktop',
             'Intended Audience :: Developers',
            # 'License :: OSI Approved :: GNU General Public License (GPL)',
             'Natural Language :: English', 
             'Operating System :: MacOS',
             'Operating System :: Microsoft :: Windows',
             'Operating System :: POSIX',
             'Operating System :: OS Independent',
             'Programming Language :: Python',
             'Topic :: Multimedia :: Sound/Audio',
             'Topic :: Artistic Software',
             ]
    return classifiers
     


def writeManifestTemplate(fpPackageDir):
    dst = os.path.join(fpPackageDir, 'MANIFEST.in')
    msg = []
    msg.append('prune dist\n')
    msg.append('prune buildDoc\n')
    msg.append('global-include *.txt *.xml *.krn *.mxl *.pdf *.html *.css *.js *.png\n')

    f = open(dst, 'w')
    f.writelines(msg)
    f.close()



def runDisutils(bdistType):
    if bdistType == 'bdist_egg':
        print('using setuptools')
        from setuptools import setup
    else:
        from distutils.core import setup
    # store object for later examination
    pkgData = _getPackageData()
    setup(name = 'music21', 
        version = music21.VERSION_STR,
        description = 'A toolkit for computer-aided musicology.', 
        long_description =  'A toolkit for computer-aided musicology.',
        author = 'Michael Scott Cuthbert, Christopher Ariza, others',
        #author_email = '',
        license = 'LGPL', 
        #url = '',
        classifiers = _getClassifiers(),
        download_url = 'http://music21.googlecode.com/files/music21-%s.tar.gz' % music21.VERSION_STR,
        packages = _getPackagesList(), 
        package_data = {'music21' : pkgData}
    ) # close setup args
    
        

if sys.argv[1] in ['bdist', 'sdist', 'register', 'bdist_mpkg',
                        'bdist_rpm', 'bdist_deb', 'bdist_wininst',
                        'bdist_egg']:
    import music21
    fpMusic21 = music21.__path__[0] # list, get first item
    fpPackageDir = os.path.dirname(fpMusic21)
    print('fpPackageDir = %s' % fpPackageDir)
    writeManifestTemplate(fpPackageDir)
    runDisutils(sys.argv[1])