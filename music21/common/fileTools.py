#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/fileTools.py
# Purpose:      Utilities for files
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Tools for working with files
'''

import codecs
import contextlib # for with statements
import io
import os
import time

from music21.ext import chardet
from music21.common.pathTools import cleanpath

__all__ = ['readFileEncodingSafe',
           'sortFilesRecent',
           'cd',
           ]

@contextlib.contextmanager
def cd(targetDir):
    '''
    Useful for a temporary cd for use in a `with` statement:
    
         with cd('/Library/'):
              os.system(make)
              
    will switch temporarily, and then switch back when leaving.
    '''
    try:
        cwd = os.getcwdu() # unicode # @UndefinedVariable
    except AttributeError:
        cwd = os.getcwd() # non unicode

    try:
        os.chdir(targetDir)
        yield
    finally:
        os.chdir(cwd)


def sortFilesRecent(fileList):
    '''Given two files, sort by most recent. Return only the file
    paths.

    >>> import os
    >>> a = os.listdir(os.curdir)
    >>> b = common.sortFilesRecent(a)

    :rtype: list(str)
    '''
    sort = []
    for fp in fileList:
        lastmod = time.localtime(os.stat(fp)[8])
        sort.append([lastmod, fp])
    sort.sort()
    sort.reverse()
    # just return
    return [y for dummy, y in sort]

def readFileEncodingSafe(filePath, firstGuess='utf-8'):
    r'''
    Slow, but will read a file of unknown encoding as safely as possible using
    the LGPL chardet package in music21.ext.  
    
    Let's try to load this file as ascii -- it has a copyright symbol at the top
    so it won't load in Python3:
    
    >>> import os 
    >>> c = os.path.join(common.getSourceFilePath(), 'common', '__init__.py')
    >>> f = open(c)
    >>> #_DOCS_SHOW data = f.read()
    Traceback (most recent call last):
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2 in position ...: 
        ordinal not in range(128)

    That won't do! now I know that it is in utf-8, but maybe you don't. Or it could
    be an old humdrum or Noteworthy file with unknown encoding.  This will load it safely.
    
    >>> data = common.readFileEncodingSafe(c)
    >>> data[0:30]
    '#-*- coding: utf-8 -*-\n#------'
    
    Well, that's nothing, since the first guess here is utf-8 and it's right. So let's
    give a worse first guess:
    
    >>> data = common.readFileEncodingSafe(c, firstGuess='SHIFT_JIS') # old Japanese standard
    >>> data[0:30]
    '#-*- coding: utf-8 -*-\n#------'
    
    It worked!
    
    Note that this is slow enough if it gets it wrong that the firstGuess should be set
    to something reasonable like 'ascii' or 'utf-8'.
    
    :rtype: str
    '''
    filePath = cleanpath(filePath)
    try:
        with io.open(filePath, 'r', encoding=firstGuess) as thisFile:
            data = thisFile.read()
            return data
    except OSError: # Python3 FileNotFoundError...
        raise
    except UnicodeDecodeError:
        with io.open(filePath, 'rb') as thisFileBinary:
            dataBinary = thisFileBinary.read()
            encoding = chardet.detect(dataBinary)['encoding']
            return codecs.decode(dataBinary, encoding)


#===============================================================================
# Image functions 
#===============================================================================
### Removed because only used by MuseScore and newest versions have -T option...
# try:
#     imp.find_module('Image')
#     hasPIL = True
# except ImportError:
#     imp.find_module('PIL')
#     except ImportError:
#         hasPIL = False
# 
# def cropImageFromPath(fp, newPath=None):
#     '''
#     Autocrop an image in place (or at new path) from Path, if PIL is installed and return True,
#     otherwise return False.  leave a border of size (
#     
#     Code from
#     https://gist.github.com/mattjmorrison/932345
#     '''
#     if newPath is None:
#         newPath = fp
#     if hasPIL:
#         try: 
#             from PIL import Image, ImageChops 
#             # overhead of reimporting is low compared to imageops
#         except ImportError:
#             import Image, ImageChops
#         imageObj = Image.open(fp)
#         imageBox = imageObj.getbbox()
#         if imageBox:
#             croppedImg = imageObj.crop(imageBox)
#         options = {}
#         if 'transparency' in imageObj.info:
#             options['transparency'] = imageObj.info["transparency"]
# #         border = 255 # white border...
# #         tempBgImage = Image.new(imageObj.mode, imageObj.size, border)
# #         differenceObj = ImageChops.difference(imageObj, tempBgImage)
# #         boundingBox = differenceObj.getbbox()
# #         if boundingBox: # empty images return None...
# #             croppedImg = imageObj.crop(boundingBox)
#         croppedImg.save(newPath, **options)
#         return True
#         
# 
#     else:
#         from music21 import environment
#         if six.PY3:
#             pip = 'pip3'
#         else:
#             pip = 'pip'
#         environLocal = environment.Environment('common.py')        
#         environLocal.warn('PIL/Pillow is not installed -- "sudo ' + pip + ' install Pillow"')
#         return False
#         


#------------------------------------------------------------------------------

if __name__ == "__main__":
    import music21 # @Reimport
    music21.mainTest()
#------------------------------------------------------------------------------
# eof

