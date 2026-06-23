# ------------------------------------------------------------------------------
# Name:         upload.py
# Purpose:      music21 documentation upload utility
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2025 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
# pylint: disable=line-too-long
'''
Script to upload music21 documentation to music21.org's music21-docs

Currently, it requires a private key in a very specific location, so not
generally useful beyond to MSAC.
'''
from __future__ import annotations

import os
import shlex
import subprocess

def getDirBuildHtml():
    '''
    Return the html directory
    '''
    from music21 import common
    parentDir = common.getRootFilePath()
    dirBuild = os.path.join(parentDir, 'documentation', 'build')
    dirBuildHtml = os.path.join(dirBuild, 'html')
    return dirBuildHtml


def main():
    '''
    Main upload function -- call by running the "upload.py" file in the parent directory.
    '''
    # AI coding assistance (ChatGPT-4o) was used in translating the finicky old
    # tar version to zip.
    zipPath = '/tmp/music21docs.zip'
    key = '/Users/cuthbert/Web/trecentoweb_key-us-west-2.pem'
    remote = 'bitnami@music21.org'
    remoteZip = '/tmp/music21docs.zip'
    remoteDir = '/home/bitnami/htdocs/music21docs/'
    src = getDirBuildHtml()

    # Zip it
    print('Compressing sources.')
    subprocess.run(['zip', '-qr', '-X', zipPath, '.'], cwd=src, check=True)

    # Copy it
    print('Copying to remote server.')
    subprocess.run(['scp', '-i', key, zipPath, f'{remote}:{remoteZip}'], check=True)

    # Unzip remotely
    print('Unzipping on remote server.')
    subprocess.run([
        'ssh', '-i', key, remote,
        f'unzip -oq {shlex.quote(remoteZip)} -d {shlex.quote(remoteDir)} && rm -f {shlex.quote(remoteZip)}'
    ], check=True)

    # Remove local
    os.remove(zipPath)

    print('Music21 documentation uploaded to music21.org')
