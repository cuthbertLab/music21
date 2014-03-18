##!/usr/local/bin/python
#-------------------------------------------------------------------------------
# Name:          setup.py
# Purpose:       install
#
# Authors:       Christopher Ariza
#                Michael Scott Cuthbert
#
# Copyright:     (c) 2009-2013 The music21 Project
# License:       LGPL
#-------------------------------------------------------------------------------

import os
from setuptools import setup, find_packages

# Do not import music21 directly.
# Instead, read the _version.py file and exec its contents. 
path = os.path.join(os.path.dirname(__file__), 'music21', '_version.py')
with open(path, 'r') as f:
    lines = f.read()
    exec(lines)

DESCRIPTION = 'A Toolkit for Computer-Aided Musical Analysis and Manipulation.'
DESCRIPTION_LONG = """A Toolkit for Computer-Aided Musical Analysis
                        and Manipulation. Developed at MIT.
                        Michael Scott Cuthbert, Principal Investigator,
                        Christopher Ariza, Lead Programmer.
                        The development of music21 is supported by the
                        generosity of the Seaver Institute."""

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

if __name__ == '__main__':
    setup(
        name='music21',
        version=__version__,
        description=DESCRIPTION,
        long_description=DESCRIPTION_LONG,
        author='Michael Scott Cuthbert, the music21 project, others',
        author_email='cuthbert@mit.edu',
        license='LGPL',
        url='http://code.google.com/p/music21',
        classifiers=classifiers,
        download_url='http://music21.googlecode.com/files/music21-%s.tar.gz' % __version__,
        packages=find_packages(exclude=['ez_setup']),
        include_package_data=True,
    )


#------------------------------------------------------------------------------
# eof
