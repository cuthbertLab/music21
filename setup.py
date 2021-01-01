##!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:          setup.py
# Purpose:       install
#
# Authors:       Christopher Ariza
#                Michael Scott Cuthbert
#
# Copyright:     (c) 2009-2021 Michael Scott Cuthbert and the music21 Project
# License:       BSD, see license.txt
# ------------------------------------------------------------------------------

import os
import setuptools

# Do not import music21 directly.
# Instead, read the _version.py file and exec its contents.
path = os.path.join(os.path.dirname(__file__), 'music21', '_version.py')
with open(path, 'r') as f:
    lines = f.read()
    exec(lines)

m21version = __version__ # @UndefinedVariable

DESCRIPTION = 'A Toolkit for Computer-Aided Musical Analysis.'
DESCRIPTION_LONG = """A Toolkit for Computer-Aided Musical Analysis.
                        Developed by cuthbertLab,
                        Michael Scott Cuthbert (Associate Professor, MIT),
                        Principal Investigator.
                        The development of music21 is supported by the
                        generosity of the Seaver Institute and the NEH."""

INSTALL_REQUIRES = [
    "chardet",
    "joblib",
    "more-itertools",
    "webcolors",
]


classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Environment :: Web Environment',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: MacOS',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3 :: Only',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Multimedia :: Sound/Audio :: MIDI',
    'Topic :: Multimedia :: Sound/Audio :: Conversion',
    'Topic :: Artistic Software',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

download_base = 'https://github.com/cuthbertLab/music21/releases/download/'

if __name__ == '__main__':
    setuptools.setup(
        name='music21',
        version=m21version,
        python_requires='>=3.6',
        description=DESCRIPTION,
        long_description=DESCRIPTION_LONG,
        author='Michael Scott Cuthbert, the music21 project, others',
        author_email='cuthbert@mit.edu',
        license='BSD',
        url='https://github.com/cuthbertLab/music21',
        classifiers=classifiers,
        download_url=f'{download_base}v{m21version}/music21-{m21version}.tar.gz',
        packages=setuptools.find_packages(exclude=['ez_setup']),
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
        zip_safe=False,
    )
