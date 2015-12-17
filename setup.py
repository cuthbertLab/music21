##!/usr/bin/env python   
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:          setup.py
# Purpose:       install
#
# Authors:       Christopher Ariza
#                Michael Scott Cuthbert
#
# Copyright:     (c) 2009-2015 The music21 Project
# License:       LGPL or BSD
#-------------------------------------------------------------------------------

import os
from setuptools import setup, find_packages

# Do not import music21 directly.
# Instead, read the _version.py file and exec its contents. 
path = os.path.join(os.path.dirname(__file__), 'music21', '_version.py')
with open(path, 'r') as f:
    lines = f.read()
    exec(lines)

m21version = __version__ # @UndefinedVariable

DESCRIPTION = 'A Toolkit for Computer-Aided Musical Analysis.'
DESCRIPTION_LONG = """A Toolkit for Computer-Aided Musical Analysis. 
                        Developed at MIT by cuthbertLab.
                        Michael Scott Cuthbert, Principal Investigator.
                        The development of music21 is supported by the
                        generosity of the Seaver Institute and the NEH."""

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Environment :: Web Environment',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
    'Natural Language :: English',
    'Operating System :: MacOS',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Multimedia :: Sound/Audio :: MIDI',
    'Topic :: Multimedia :: Sound/Audio :: Conversion',
    'Topic :: Artistic Software',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

if __name__ == '__main__':
    setup(
        name='music21',
        version=m21version,
        description=DESCRIPTION,
        long_description=DESCRIPTION_LONG,
        author='Michael Scott Cuthbert, the music21 project, others',
        author_email='cuthbert@mit.edu',
        license='BSD',
        url='https://github.com/cuthbertLab/music21',
        classifiers=classifiers,
        download_url='https://github.com/cuthbertLab/music21/releases/download/v%s/music21-%s.tar.gz' % (m21version, m21version),
        packages=find_packages(exclude=['ez_setup']),
        include_package_data=True,
    )

#------------------------------------------------------------------------------
# eof
