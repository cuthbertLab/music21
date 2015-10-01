#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common.py
# Purpose:      Basic Utilties
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Common is a collection of utility functions, objects, constants and dictionaries used 
throughout music21.

functions in common/ can import from music21.defaults, music21.exceptions21, and music21.ext
and that is all (except in tests and doctests).

For historical reasons all the (non-private) functions etc. of the common/
folder are available by importing common. 

split according to function -- September 2015
'''

# should NOT import music21 or anything like that, except in doctests.
import codecs
import copy
import inspect
import os
import sys
import textwrap
import time
import unittest
import weakref

from music21 import defaults
from music21 import exceptions21
from music21.ext import six

# pylint: disable=wildcard-import
from music21.common.classTools import * #including isNum, isListLike 
from music21.common.decorators import * # gives the deprecated decorator
from music21.common.fileTools import * # file tools.
from music21.common.formats import * # most are deprecated!
from music21.common.numberFunc import * #including opFrac
from music21.common.stringTools import * 
from music21.common.weakrefTools import * # including wrapWeakref

if six.PY2:
    try:
        import cPickle as pickleMod # much faster on Python 2
    except ImportError:
        import pickle as pickleMod # @UnusedImport
else:
    import pickle as pickleMod # @Reimport
    # on python 3 -- do NOT import _pickle directly. it will be used if  it exists, and _pickle lacks HIGHEST_PROTOCOL constant.

DEBUG_OFF = 0
DEBUG_USER = 1
DEBUG_DEVEL = 63
DEBUG_ALL = 255




#-------------------------------------------------------------------------------
# provide warning strings to users for use in conditional imports

def getMissingImportStr(modNameList):
    '''
    Given a list of missing module names, returns a nicely-formatted message to the user
    that gives instructions on how to expand music21 with optional packages.


    >>> print(common.getMissingImportStr(['matplotlib']))
    Certain music21 functions might need the optional package matplotlib;
    if you run into errors, install it by following the instructions at
    http://mit.edu/music21/doc/installing/installAdditional.html
    
    >>> print(common.getMissingImportStr(['matplotlib', 'numpy']))
    Certain music21 functions might need these optional packages: matplotlib, numpy;
    if you run into errors, install them by following the instructions at
    http://mit.edu/music21/doc/installing/installAdditional.html    
    '''
    if len(modNameList) == 0:
        return None
    elif len(modNameList) == 1:
        return textwrap.dedent('''\
                  Certain music21 functions might need the optional package %s;
                  if you run into errors, install it by following the instructions at
                  http://mit.edu/music21/doc/installing/installAdditional.html''' % 
                  modNameList[0])
    else:
        return textwrap.dedent('''\
                   Certain music21 functions might need these optional packages: %s;
                   if you run into errors, install them by following the instructions at
                   http://mit.edu/music21/doc/installing/installAdditional.html''' % 
                   ', '.join(modNameList))


def getPlatform():
    '''
    Return the name of the platform, where platforms are divided
    between 'win' (for Windows), 'darwin' (for MacOS X), and 'nix' for (GNU/Linux and other variants).

    :rtype: str
    '''
    # possible os.name values: 'posix', 'nt', 'mac', 'os2', 'ce',
    # 'java', 'riscos'.
    if os.name in ['nt'] or sys.platform.startswith('win'):
        return 'win'
    elif sys.platform in ['darwin']:
        return 'darwin' #
    elif os.name == 'posix': # catch all other nix platforms
        return 'nix'



def sortModules(moduleList):
    '''
    Sort a lost of imported module names such that most recently modified is
    first.  In ties, last accesstime is used then module name
    
    Will return a different order each time depending on the last mod time
    
    :rtype: list(str)
    '''
    sort = []
    modNameToMod = {}    
    for mod in moduleList:
        modNameToMod[mod.__name__] = mod
        fp = mod.__file__ # returns the pyc file
        stat = os.stat(fp)
        lastmod = time.localtime(stat[8])
        asctime = time.asctime(lastmod)
        sort.append((lastmod, asctime, mod.__name__))
    sort.sort()
    sort.reverse()
    # just return module list
    return [modNameToMod[modName] for lastmod, asctime, modName in sort]






def dirPartitioned(obj, skipLeading=('__',)):
    '''
    Given an object, return three lists of names: methods, attributes, and properties.

    Note that if a name/attribute is dynamically created by a property it
    cannot be found until that attribute is created.

    TODO: this cannot properly partition properties from methods
    '''
    names = dir(obj)
    methods = []
    attributes = []
    properties = []
    for name in names:
        skip = False
        for lead in skipLeading:
            if name.startswith(lead):
                skip = True
                break
        if skip:
            continue
        # get attr returns methods, attributes, and properties
        # when getting an attribute from a property, however, this may call
        # the getter of a name that is only defined in a setter
        part = getattr(obj, name)
        if isinstance(part, property):
            properties.append(name)
#         if inspect.isdatadescriptor(part):
#             properties.append(name)
        elif inspect.ismethod(part):
            methods.append(name)
#         elif isinstance(part, types.MethodType):
#             methods.append(name)
        else:
            attributes.append(name)
    return methods, attributes, properties


#-------------------------------------------------------------------------------
# tools for setup.py
def getSourceFilePath():
    '''
    Get the music21 directory that contains source files. This is not the same as the
    outermost package development directory.
    
    :rtype: str
    '''
    import music21 # @Reimport # pylint: disable=redefined-outer-name 
    fpMusic21 = music21.__path__[0] # list, get first item 
    # use corpus as a test case
    if 'stream' not in os.listdir(fpMusic21):
        raise Exception('cannot find expected music21 directory: %s' % fpMusic21)
    return fpMusic21



def getMetadataCacheFilePath():
    r'''Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getMetadataCacheFilePath()
    >>> fp.endswith('corpus/_metadataCache') or fp.endswith(r'corpus\_metadataCache')
    True
    
    :rtype: str
    '''
    return os.path.join(getSourceFilePath(), 'corpus', '_metadataCache')


def getCorpusFilePath():
    r'''Get the stored music21 directory that contains the corpus metadata cache.

    >>> fp = common.getCorpusFilePath()
    >>> fp.endswith('music21/corpus') or fp.endswith(r'music21\corpus')
    True
    '''
    from music21 import corpus
    coreCorpus = corpus.CoreCorpus()
    if coreCorpus.manualCoreCorpusPath is None:
        return os.path.join(getSourceFilePath(), 'corpus')
    return coreCorpus.manualCoreCorpusPath


def getCorpusContentDirs():
    '''Get all dirs that are found in the corpus that contain content; that is, exclude dirst that have code or other resoures.

    >>> fp = common.getCorpusContentDirs()
    >>> fp # this test will be fragile, depending on composition of dirs
    ['airdsAirs', 'bach', 'beethoven', 'ciconia', 'corelli', 'cpebach',
    'demos', 'essenFolksong', 'handel', 'haydn', 'josquin', 'leadSheet',
    'luca', 'miscFolk', 'monteverdi', 'mozart', 'oneills1850', 'palestrina',
    'ryansMammoth', 'schoenberg', 'schumann', 'schumann_clara',
    'theoryExercises', 'trecento', 'verdi', 'weber']
    
    Make sure that all corpus data has a directoryInformation tag in
    CoreCorpus.
    
    >>> cc = corpus.corpora.CoreCorpus()
    >>> failed = []
    >>> di = [d.directoryName for d in cc.directoryInformation]
    >>> for f in fp:
    ...     if f not in di:
    ...         failed.append(f)
    >>> failed
    []
    
    '''
    directoryName = getCorpusFilePath()
    result = []
    # dirs to exclude; all files will be retained
    excludedNames = (
        'license.txt',
        '_metadataCache',
        '__pycache__',
        )
    for filename in os.listdir(directoryName):
        if filename.endswith(('.py', '.pyc')):
            continue
        elif filename.startswith('.'):
            continue
        elif filename in excludedNames:
            continue
        result.append(filename)
    return sorted(result)


def getPackageDir(fpMusic21=None, relative=True, remapSep='.',
     packageOnly=True):
    '''Manually get all directories in the music21 package, 
    including the top level directory. This is used in setup.py.

    If `relative` is True, relative paths will be returned.

    If `remapSep` is set to anything other than None, the path separator will be replaced.

    If `packageOnly` is true, only directories with __init__.py files are colllected.
    '''
    if fpMusic21 == None:
        import music21 # @Reimport # pylint: disable=redefined-outer-name
        fpMusic21 = music21.__path__[0] # list, get first item

    # a test if this is the correct directory
    if 'corpus' not in os.listdir(fpMusic21):
        raise Exception('cannot find corpus within %s' % fpMusic21)
    #fpCorpus = os.path.join(fpMusic21, 'corpus')
    fpParent = os.path.dirname(fpMusic21)
    match = []
    for dirpath, unused_dirnames, filenames in os.walk(fpMusic21):
        # remove hidden directories
        if ('%s.' % os.sep) in dirpath:
            continue
        elif '.svn' in dirpath:
            continue
        if packageOnly:
            if '__init__.py' not in filenames: # must be to be a package
                continue
        # make relative
        if relative:
            fp = dirpath.replace(fpParent, '')
            if fp.startswith(os.sep):
                fp = fp[fp.find(os.sep)+len(os.sep):]
        else:
            fp = dirpath
        # replace os.sep
        if remapSep != None:
            fp = fp.replace(os.sep, remapSep)
        match.append(fp)
    return match


def getPackageData():
    '''
    Return a list of package data in 
    the format specified by setup.py. This creates a very inclusive list of all data types.
    '''
    # include these extensions for all directories, even if they are not normally there.
    # also need to update writeManifestTemplate() in setup.py when adding
    # new file extensions
    ext = ['txt', 'xml', 'krn', 'mxl', 'pdf', 'html',
           'css', 'js', 'png', 'tiff', 'jpg', 'xls', 'mid', 'abc', 'json', 'md',
           'zip', 'rntxt', 'command', 'scl', 'nwc', 'nwctxt', 'wav']

    # need all dirs, not just packages, and relative to music21
    fpList = getPackageDir(fpMusic21=None, relative=True, remapSep=None,
                            packageOnly=False)
    stub = 'music21%s' % os.sep
    match = []
    for fp in fpList:
        # these are relative to music21 package, so remove music21
        if fp == 'music21':
            continue
        elif fp.startswith(stub):
            fp = fp[fp.find(stub)+len(stub):]
        for e in ext:
            target = fp + os.sep + '*.%s' % e
            match.append(target)

    return match

#-----------------------------
def pitchList(pitchL):
    '''
    utility method that replicates the previous behavior of 
    lists of pitches
    '''
    return '[' + ', '.join([x.nameWithOctave for x in pitchL]) + ']'




def runningUnderIPython():
    '''
    return bool if we are running under iPython Notebook (not iPython)

    (no tests, since will be different)

    This post:
    http://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook
    says not to do this, but really, I can't think of another way to have different output as default.
    
    :rtype: bool
    '''
    if sys.stderr.__class__.__name__ == 'OutStream':
        return True
    else:
        return False


def relativepath(path, start='.'):
    '''
    A cross-platform wrapper for `os.path.relpath()`, which returns `path` if
    under Windows, otherwise returns the relative path of `path`.

    This avoids problems under Windows when the current working directory is
    on a different drive letter from `path`.
    
    :type path: str
    :type start: str
    :rtype: str
    '''
    import platform
    if platform == 'Windows':
        return path
    return os.path.relpath(path, start)


#-----------------------------
# match collections, defaultdict()

class defaultlist(list):
    '''
    Call a function for every time something is missing:
    
    >>> a = common.defaultlist(lambda:True)
    >>> a[5]
    True    
    '''
    def __init__(self, fx):
        list.__init__(self)
        self._fx = fx
    def _fill(self, index):
        while len(self) <= index:
            self.append(self._fx())
    def __setitem__(self, index, value):
        self._fill(index)
        list.__setitem__(self, index, value)
    def __getitem__(self, index):
        self._fill(index)
        return list.__getitem__(self, index)


_singletonCounter = {}
_singletonCounter['value'] = 0

class SingletonCounter(object):
    '''
    A simple counter that can produce unique numbers regardless of how many instances exist.
    
    Instantiate and then call it.
    '''
    def __init__(self):
        pass

    def __call__(self):
        post = _singletonCounter['value']
        _singletonCounter['value'] += 1
        return post

#-------------------------------------------------------------------------------
class SlottedObject(object):
    r'''
    Provides template for classes implementing slots allowing it to be pickled
    properly.
    
    Only use SlottedObjects for objects that we expect to make so many of
    that memory storage and speed become an issue. Thus, unless you are Xenakis, 
    Glissdata is probably not the best example:
    
    >>> import pickle
    >>> class Glissdata(common.SlottedObject):
    ...     __slots__ = ('time', 'frequency')
    >>> s = Glissdata()
    >>> s.time = 0.125
    >>> s.frequency = 440.0
    >>> #_DOCS_SHOW out = pickle.dumps(s)
    >>> #_DOCS_SHOW t = pickle.loads(out)
    >>> t = s #_DOCS_HIDE -- cannot define classes for pickling in doctests
    >>> t.time, t.frequency
    (0.125, 440.0)

    OMIT_FROM_DOCS
    
    >>> class BadSubclass(Glissdata):
    ...     pass
    
    >>> bsc = BadSubclass()
    >>> bsc.amplitude = 2
    >>> #_DOCS_SHOW out = pickle.dumps(bsc)
    >>> #_DOCS_SHOW t = pickle.loads(out)
    >>> t = bsc #_DOCS_HIDE -- cannot define classes for pickling in doctests
    >>> t.amplitude
    2
    '''
    
    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __getstate__(self):
        if getattr(self, '__dict__', None) is not None:
            state = getattr(self, '__dict__').copy()
        else:
            state = {}
        slots = set()
        for cls in self.__class__.mro():
            slots.update(getattr(cls, '__slots__', ()))
        for slot in slots:
            sValue = getattr(self, slot, None)
            if isinstance(sValue, weakref.ref):
                sValue = sValue()
                print("Warning: uncaught weakref found in %r - %s, will not be rewrapped" % (self, slot))
            state[slot] = sValue
        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)


#-------------------------------------------------------------------------------
class Iterator(object):
    '''A simple Iterator object used to handle iteration of Streams and other
    list-like objects.
    
    >>> i = common.Iterator([2,3,4])
    >>> for x in i:
    ...     print(x)
    2
    3
    4
    >>> for y in i:
    ...     print(y)
    2
    3
    4
    '''
    def __init__(self, data):
        self.data = data
        self.index = 0

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.data):
            raise StopIteration
        post = self.data[self.index]
        self.index += 1
        return post

    def next(self):
        return self.__next__()


#-------------------------------------------------------------------------------
class Timer(object):
    """
    An object for timing. Call it to get the current time since starting.
    
    >>> t = common.Timer()
    >>> now = t()
    >>> nownow = t()
    >>> nownow > now
    True
    
    Call `stop` to stop it. Calling `start` again will reset the number
    
    >>> t.stop()
    >>> stopTime = t()
    >>> stopNow = t()
    >>> stopTime == stopNow
    True
    
    All this had better take less than one second!
    
    >>> stopTime < 1
    True
    """

    def __init__(self):
        # start on init
        self._tStart = time.time()
        self._tDif = 0
        self._tStop = None

    def start(self):
        '''Explicit start method; will clear previous values. Start always happens on initialization.'''
        self._tStart = time.time()
        self._tStop = None # show that a new run has started so __call__ works
        self._tDif = 0

    def stop(self):
        self._tStop = time.time()
        self._tDif = self._tStop - self._tStart

    def clear(self):
        self._tStop = None
        self._tDif = 0
        self._tStart = None

    def __call__(self):
        '''Reports current time or, if stopped, stopped time.
        '''
        # if stopped, gets _tDif; if not stopped, gets current time
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return t

    def __str__(self):
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return str(round(t,3))




# NB -- temp files (tempFile) etc. are in environment.py

#-------------------------------------------------------------------------------
def defaultDeepcopy(obj, memo, callInit=True):
    '''
    Unfortunately, it is not possible to do something like:
    
        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                copy.deepcopy(self, memo, ignore__deepcopy__=True)
    
    so that's what this is for:
    
        def __deepcopy__(self, memo):
            if self._noDeepcopy:
                return self.__class__()
            else:
                common.defaultDeepcopy(obj, memo)
                
    looks through both __slots__ and __dict__ and does a deepcopy
    of anything in each of them and returns the new object.
    
    If callInit is False, then only __new__() is called.  This is
    much faster if you're just going to overload every instance variable.    
    '''
    if callInit is False:
        new = obj.__class__.__new__(obj.__class__)
    else:
        new = obj.__class__()

    dictState = getattr(obj, '__dict__', None)
    if dictState is not None:
        for k in dictState:
            setattr(new, k, copy.deepcopy(dictState[k], memo))
    slots = set()
    for cls in obj.__class__.mro(): # it is okay that it's in reverse order, since it's just names
        slots.update(getattr(cls, '__slots__', ()))
    for slot in slots:
        slotValue = getattr(obj, slot, None) 
            # might be none if slot was deleted; it will be recreated here
        setattr(new, slot, copy.deepcopy(slotValue))

    return new

def pickleCopy(obj):
    '''
    use pickle to serialize/deserialize a copy of an object -- much faster than deepcopy,
    but only works for things that are completely pickleable.
    '''
    return pickleMod.loads(pickleMod.dumps(obj, protocol=-1))


#-------------------------------------------------------------------------------
class TestMock(object):
    '''
    A test object with attributes, methods, and properties
    '''
    def __init__(self):
        self.attr1 = 1
        self.attr2 = 2
        self.attr3 = 3

        from music21 import environment
        _MOD = 'music21.common.TestMock'
        self._environLocal = environment.Environment(_MOD)


    def method1(self):
        return 3

    def method2(self):
        return 4

    def _get1(self):
        return self.attr3

    def _set1(self, value):
        self.attr3 = value

    def __deepcopy__(self, memo=None):
        # None is the empty memp default
        #self._environLocal.printDebug(['__deepcopy__ called, got memo',
        #                              self, memo])
        new = self.__class__()
        for name in self.__dict__:
            if name.startswith('_'): # avoid environemnt
                continue
            part = getattr(self, name)
            newValue = copy.deepcopy(part, memo)
            setattr(new, name, newValue)
        return new

    def __copy__(self):
        self.environLocal.printDebug(['copy called'])
        return copy.copy(self)

    property1 = property(_get1, _set1)
    property2 = property(_get1, _set1)




class Test(unittest.TestCase):
    '''
    Tests not requiring file output.
    '''

    def runTest(self):
        pass

    def setUp(self):
        pass


    def testGettingAttributes(self):
        a = TestMock()
        # dir() returns all names, including properties, attributes, methods
        aDir = dir(a)
        self.assertEqual(('_get1' in aDir), True)
        self.assertEqual(('attr1' in aDir), True)
        self.assertEqual(('method1' in aDir), True)
        self.assertEqual(('property1' in aDir), True)
        # __dict__ stores only attributes
        aDictKeys = a.__dict__.keys()
        self.assertEqual(('attr1' in aDictKeys), True)
        # properties are not found htere
        self.assertNotEqual(('property1' in aDictKeys), True)
        # after setting an attribute not defined in __init__ with a property
        # the new data value is store in __dict__
        a.property1 = 3
        aDictKeys = a.__dict__.keys()
        self.assertEqual(('attr3' in aDictKeys), True)

        # we cannot use insepct.isdatadescriptor to find properties
        self.assertEqual(inspect.isdatadescriptor(a.property1), False)


        unused_methods, attributes, unused_properties = dirPartitioned(a)
        self.assertEqual(('attr1' in attributes), True)



    def testDeepcopy(self):
        '''A simple test of deepcopying.
        '''
        a = TestMock()
        b = TestMock()
        a.attr1 = b
        a.attr2 = b
        # test first by using copy.deepcopy
        c = copy.deepcopy(a)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a.attr1, c.attr1)
        self.assertNotEqual(a.attr2, c.attr2)
        # but, the concept of the same object w/ two references is still there
        self.assertEqual(a.attr1, a.attr2)
        self.assertEqual(c.attr1, c.attr2)

        # test second by using the .deepcopy() method
        c = copy.deepcopy(a)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a.attr1, c.attr1)
        self.assertNotEqual(a.attr2, c.attr2)
        self.assertEqual(a.attr1, a.attr2)
        self.assertEqual(c.attr1, c.attr2)

#-------------------------------------------------------------------------------
# define presented order in documentation
# _DOC_ORDER = [fromRoman, toRoman]


if __name__ == "__main__":
    import music21 # @Reimport
    music21.mainTest(Test)
#------------------------------------------------------------------------------
# eof

