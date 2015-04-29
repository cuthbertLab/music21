# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         environment.py
# Purpose:      Storage for user environment settings and defaults
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
The environment module describes an object for accessing and setting
variables related to the user's music21 environment. Such variables include
the location of external applications such as MusicXML readers (e.g. Finale),
whether music21 is allowed to download files directly (via the virtual corpus),
and other settings.

Additional documentation for and examples of using this module are found in
:ref:`environment`.

# TODO: Update to user's guide
'''
from __future__ import print_function

import os
import sys
import tempfile
import unittest
import xml.sax
from xml.sax import saxutils

from music21 import exceptions21
from music21 import common
from music21 import xmlnode
from music21.ext import six


_MOD = 'environment.py'


#------------------------------------------------------------------------------


class EnvironmentException(exceptions21.Music21Exception):
    pass


class UserSettingsException(EnvironmentException):
    pass


#------------------------------------------------------------------------------


class Settings(xmlnode.XMLNodeList):
    '''
    A settings object:

    ::

        >>> from music21 import environment
        >>> a = environment.Settings()

    '''

    ### INITIALIZER ###

    def __init__(self):
        xmlnode.XMLNodeList.__init__(self)
        self._tag = 'settings'  # assumed for now
        self.componentList = []  # list of Part objects

    ### PRIVATE METHODS ###

    def _getComponents(self):
        return self.componentList


class Preference(xmlnode.XMLNode):
    '''
    An xmlnode.XMLNode subclass representing a single environment preference:

    ::

        >>> from music21 import environment
        >>> a = environment.Preference()

    '''

    ### INITIALIZER ###

    # TODO: Make private class because there's no docs and no public interface.
    def __init__(self):
        xmlnode.XMLNode.__init__(self)
        self._tag = 'preference'  # assumed for now
        # attributes
        self._attr['name'] = None
        self._attr['value'] = None

#     def loadAttrs(self, attrs):
#         # thought that this would solve a bytes problem for Python3, but nope...
#         try:
#             x = attrs.getValue('value')
#             print(repr(x), type(x))
#         except KeyError:
#             pass
#         return xmlnode.XMLNode.loadAttrs(self, attrs)


class LocalCorpusSettings(xmlnode.XMLNodeList):
    '''

    ::

        >>> from music21 import environment
        >>> a = environment.LocalCorpusSettings()

    '''

    ### INITIALIZER ###

    def __init__(self, name=None):
        xmlnode.XMLNodeList.__init__(self)
        self._attr['name'] = name
        self._tag = 'localCorpusSettings'  # assumed for now

    ### PRIVATE METHODS ###

    def _getComponents(self):
        return self.componentList


class LocalCorporaSettings(xmlnode.XMLNodeList):
    '''
    An xmlnode.XMLNode subclass representing information about various
    secondary local corpora:

    ::

        >>> from music21 import environment
        >>> localCorpora = environment.LocalCorporaSettings()
        >>> corpusA = environment.LocalCorpusSettings(name='A')
        >>> corpusA.append(environment.LocalCorpusPath(path='foo'))
        >>> corpusA.append(environment.LocalCorpusPath(path='bar'))
        >>> corpusB = environment.LocalCorpusSettings(name='B')
        >>> corpusB.append(environment.LocalCorpusPath(path='baz'))
        >>> localCorpora.append(corpusA)
        >>> localCorpora.append(corpusB)
        >>> print(localCorpora.xmlStr())
        <?xml version="1.0" ...?>
        <localCorporaSettings>
          <localCorpusSettings name="A">
            <localCorpusPath>foo</localCorpusPath>
            <localCorpusPath>bar</localCorpusPath>
          </localCorpusSettings>
          <localCorpusSettings name="B">
            <localCorpusPath>baz</localCorpusPath>
          </localCorpusSettings>
        </localCorporaSettings>
        <BLANKLINE>

    '''

    ### INITIALIZER ###

    def __init__(self):
        xmlnode.XMLNodeList.__init__(self)
        self._tag = 'localCorporaSettings'

    ### PRIVATE METHODS ###

    def _getComponents(self):
        return self.componentList


class LocalCorpusPath(xmlnode.XMLNode):
    '''
    An xmlnode.XMLNode subclass representing a list of environment
    preference:

    ::

        >>> from music21 import environment
        >>> lcs = environment.LocalCorpusSettings()
        >>> lcp = environment.LocalCorpusPath()
        >>> lcp.charData = 'testing'
        >>> lcs.append(lcp)
        >>> print(lcs.xmlStr())
        <?xml version="1.0" ...?>
        <localCorpusSettings>
        <localCorpusPath>testing</localCorpusPath>
        </localCorpusSettings>
        <BLANKLINE>
    '''

    ### INITIALIZER ###

    def __init__(self, path=None):
        xmlnode.XMLNode.__init__(self)
        self._tag = 'localCorpusPath'  # assumed for now
        self.charData = path  # char data stores path
        # attributes


#------------------------------------------------------------------------------


class SettingsHandler(xml.sax.ContentHandler):
    '''
    An xml.sax.ContentHandler subclass holding settings:

    ::

        >>> from music21 import environment
        >>> sh = environment.SettingsHandler()

    '''
    #TODO: Make private class because there's no docs and no public interface.

    ### INITIALIZER ###

    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self._characters = ''
        self._objectStack = []
        self._settings = None

    ### PUBLIC METHODS ###

    def characters(self, characters):
        self._characters += characters

    def endElement(self, name):
        currentObject = self._objectStack.pop()
        if isinstance(currentObject, Preference):
            self._objectStack[-1].append(currentObject)
        elif isinstance(currentObject, LocalCorpusPath):
            currentObject.charData = self._characters.strip()
            self._objectStack[-1].append(currentObject)
        elif isinstance(currentObject, LocalCorporaSettings):
            currentObject.componentList.sort(
                key=lambda x: (x.__class__.__name__, x._attr.get('name')))
            self._objectStack[-1].append(currentObject)
        elif isinstance(currentObject, LocalCorpusSettings):
            currentObject.componentList.sort(
                key=lambda x: (x.__class__.__name__, x._attr.get('name')))
            self._objectStack[-1].append(currentObject)
        elif isinstance(currentObject, Settings):
            currentObject.componentList.sort(
                key=lambda x: (x.__class__.__name__, x._attr.get('name')))
            self._settings = currentObject

    def getSettings(self):
        return self._settings

    def startElement(self, name, attrs):
        self._characters = ''
        if name == 'preference':
            slot = Preference()
            slot.loadAttrs(attrs)
        elif name == 'localCorporaSettings':
            slot = LocalCorporaSettings()
        elif name == 'localCorpusSettings':
            slot = LocalCorpusSettings(name=attrs.get('name', None))
        elif name == 'localCorpusPath':
            slot = LocalCorpusPath()
        elif name == 'settings':
            slot = Settings()
        self._objectStack.append(slot)


#------------------------------------------------------------------------------


class _EnvironmentCore(object):
    '''
    This private class should never be directly created; use the Environment
    object to access this object.

    Multiple Environment instances may exist, but all share access to the same
    _EnvironmentCore instance that is stored in this module.

    The only case in which a new _EnvironmentCore is created is if the
    forcePlatform argument is passed and is different than the stored
    forcePlatform argument. This is only used in testing--it allows authors to
    test what the settings on a different platform (win, Mac, etc.) would be.

    NOTE: this is a private class. All documentation for public methods should
    be placed in the Environment class.
    '''

    ### INITIALIZER ###

    def __init__(self, forcePlatform=None):
        # only create one
        #sys.stderr.write('creating singleton _EnvironmentCore\n')
        self._ref = {}
        # define all settings that are paths
        # store names of all values that are keys; check for validity
        self._keysToPaths = []
        self._keysToPaths.append('braillePath')
        self._keysToPaths.append('graphicsPath')
        self._keysToPaths.append('lilypondPath')
        self._keysToPaths.append('localCorpusPath')
        self._keysToPaths.append('manualCoreCorpusPath')
        self._keysToPaths.append('midiPath')
        self._keysToPaths.append('musescoreDirectPNGPath')
        self._keysToPaths.append('musicxmlPath')
        self._keysToPaths.append('pdfPath')
        self._keysToPaths.append('vectorPath')

        # defines all valid keys in ref
        self._loadDefaults(forcePlatform=forcePlatform)
        # read will only right over values if set in field
        if forcePlatform is None:  # only read if not forcing platform
            self.read()  # load a stored file if available

    ### SPECIAL METHODS ###

    def __getitem__(self, key):
        # could read file here to update from disk
        # could store last update tim and look of file is more recent
        # how, only doing read once is a bit more conservative
        #self.read()

        # note: this will not get 'localCorpusPath' as there may be more than
        # one value
        if key not in self._ref:
            raise EnvironmentException('no preference: %s' % key)
        value = self._ref[key]
        if six.PY3 and isinstance(value, bytes):
            value = value.decode(errors='replace')
        
        valueStr = str(value).lower()

        if key in ['debug']:  # debug expects a number
            if valueStr == 'true':
                value = common.DEBUG_USER
            elif valueStr == 'false':
                value = common.DEBUG_OFF
            elif 'off' in valueStr:
                value = common.DEBUG_OFF
            elif 'user' in valueStr:
                value = common.DEBUG_USER
            elif 'devel' in valueStr:
                value = common.DEBUG_DEVEL
            elif 'all' in valueStr:
                value = common.DEBUG_ALL
            else:
                value = int(value)
        if value == '':
            value = None  # return None for values not set
        return value

    def __repr__(self):
        return '<Environment>'

    def __setitem__(self, key, value):
        #saxutils.escape # used for escaping strings going to xml
        # with unicode encoding
        # http://www.xml.com/pub/a/2002/11/13/py-xml.html?page=2
        # saxutils.escape(msg).encode('UTF-8')

        # add local corpus path as a key
        if six.PY3 and isinstance(value, bytes):
            value = value.decode(errors='replace')
            
        if key not in self._ref:
            if key != 'localCorpusPath':
                raise EnvironmentException('no preference: %s' % key)
        if value == '':
            value = None  # always replace '' with None

        valid = False
        if key == 'showFormat':
            value = value.lower()
            if value in common.VALID_SHOW_FORMATS:
                valid = True
        elif key == 'writeFormat':
            value = value.lower()
            if value in common.VALID_WRITE_FORMATS:
                valid = True
        elif key == 'autoDownload':
            value = value.lower()
            if value in common.VALID_AUTO_DOWNLOAD:
                valid = True
        elif key == 'localCorpusSettings':
            # needs to be a list of strings for now
            if common.isListLike(value):
                valid = True
        else:  # temporarily not validating other preferences
            valid = True

        if not valid:
            raise EnvironmentException(
                '{} is not an acceptable value for preference: {}'.format(
                    value, key))

        # need to escape problematic characters for xml storage
        if common.isStr(value):
            value = saxutils.escape(value).encode('UTF-8')
        # set value
        if key == 'localCorpusPath':
            # only add if unique
            value = xmlnode.fixBytes(value)
            if value not in self._ref['localCorpusSettings']:
                # check for malicious values here
                self._ref['localCorpusSettings'].append(value)
        else:
            self._ref[key] = value

    def __str__(self):
        return repr(self._ref)

    ### PRIVATE METHODS ###

    def _fromSettings(self, settings, ref=None):
        '''
        Load a ref dictionary from the Settings object. Change the passed-in
        ref dictionary in place.
        '''
        if ref is None:
            ref = {}
        for slot in settings:
            if isinstance(slot, LocalCorpusSettings):
                ref['localCorpusSettings'] = []
                for lcp in slot:
                    # validate paths on load
                    fpCandidate = lcp.charData.strip()
                    ref['localCorpusSettings'].append(fpCandidate)
            elif isinstance(slot, LocalCorporaSettings):
                ref['localCorporaSettings'] = {}
                for localCorpusSettings in slot:
                    name = localCorpusSettings._attr['name']
                    ref['localCorporaSettings'][name] = []
                    for localCorpusPath in localCorpusSettings:
                        fpCandidate = localCorpusPath.charData.strip()
                        ref['localCorporaSettings'][name].append(fpCandidate)
            else:
                name = slot.get('name')
                value = slot.get('value')
                if name not in ref:
                    continue
                    # do not set, ignore for now
                else:  # load up stored values, overwriting defaults
                    ref[name] = value

    def _loadDefaults(self, forcePlatform=None):
        '''
        Load defaults.

        All keys are derived from these defaults.
        '''
        # path to a directory for temporary files
        self._ref['directoryScratch'] = None

        # path to lilypond
        self._ref['lilypondPath'] = None

        # version of lilypond
        self._ref['lilypondVersion'] = None
        self._ref['lilypondFormat'] = 'pdf'
        self._ref['lilypondBackend'] = 'ps'

        # path to a MusicXML reader: default, will find "Finale Notepad"
        self._ref['musicxmlPath'] = None

        # path to a midi reader
        self._ref['midiPath'] = None

        # path to a graphics viewer
        self._ref['graphicsPath'] = None

        # path to a vector graphics viewer
        self._ref['vectorPath'] = None

        # path to a pdf viewer
        self._ref['pdfPath'] = None

        # path to a braille viewer
        self._ref['braillePath'] = None

        # path to MuseScore (if not the musicxmlPath...)
        # for direct creation of PNG from MusicXML
        self._ref['musescoreDirectPNGPath'] = None
        self._ref['showFormat'] = 'musicxml'
        self._ref['writeFormat'] = 'musicxml'
        self._ref['ipythonShowFormat'] = 'ipython.lilypond.png'

        self._ref['autoDownload'] = 'ask'
        self._ref['debug'] = 0

        # printing of missing import warnings
        # default/non-zero is on
        self._ref['warnings'] = 1

        # store a list of strings
        self._ref['localCorpusSettings'] = []
        self._ref['localCorporaSettings'] = {}

        self._ref['manualCoreCorpusPath'] = None

        if forcePlatform is None:
            platform = common.getPlatform()
        else:
            platform = forcePlatform

        if platform == 'win':
            for name, value in [
                ('lilypondPath', 'lilypond'),
                ]:
                self.__setitem__(name, value)  # use for key checking
        elif platform == 'nix':
            for name, value in [('lilypondPath', 'lilypond')]:
                self.__setitem__(name, value)  # use for key checking
        elif platform == 'darwin':
            for name, value in [
                ('lilypondPath', '/Applications/Lilypond.app/Contents/Resources/bin/lilypond'),
                ('musicxmlPath', '/Applications/Finale Notepad 2012.app'),
                ('graphicsPath', '/Applications/Preview.app'),
                ('vectorPath', '/Applications/Preview.app'),
                ('pdfPath', '/Applications/Preview.app'),
                ('midiPath', '/Applications/QuickTime Player.app'),
                ('musescoreDirectPNGPath', '/Applications/MuseScore 2.app/Contents/MacOS/mscore'),
                ]:
                self.__setitem__(name, value)  # use for key checking

    def _toSettings(self, ref):
        '''
        Convert a ref dictionary to a Settings object.
        '''
        settings = Settings()
        for key, value in sorted(ref.items()):
            if key == 'localCorpusSettings':
                localCorpusSettings = LocalCorpusSettings()
                for filePath in sorted(value):
                    filePath = xmlnode.fixBytes(filePath)
                    localCorpusPath = LocalCorpusPath(path=filePath)
                    localCorpusSettings.append(localCorpusPath)
                settings.append(localCorpusSettings)
            elif key == 'localCorporaSettings':
                localCorporaSettings = LocalCorporaSettings()
                for name, paths in sorted(value.items()):
                    localCorpusSettings = LocalCorpusSettings(name=name)
                    for path in sorted(paths):
                        path = xmlnode.fixBytes(path)
                        localCorpusPath = LocalCorpusPath(path=path)
                        localCorpusSettings.append(localCorpusPath)
                    localCorporaSettings.append(localCorpusSettings)
                settings.append(localCorporaSettings)
            else:
                slot = Preference()
                slot.set('name', key)
                value = xmlnode.fixBytes(value)
                slot.set('value', value)
                settings.append(slot)
        return settings

    ### PUBLIC METHODS ###

    def getDefaultRootTempDir(self):
        '''
        returns whatever tempfile.gettempdir() returns plus 'music21'.
        
        Creates the subdirectory if it doesn't exist:
        
        >>> import tempfile
        >>> t = tempfile.gettempdir()
        >>> #_DOCS_SHOW t
        '/var/folders/x5/rymq2tx16lqbpytwb1n_cc4c0000gn/T'

        >>> import os
        >>> e = environment.Environment()
        >>> e.getDefaultRootTempDir() == os.path.join(t, 'music21')
        True
        '''
        # this returns the root temp dir; this does not create a new dir
        dstDir = os.path.join(tempfile.gettempdir(), 'music21')
        # if this path already exists, we have nothing more to do
        if os.path.exists(dstDir):
            return dstDir
        else:
            # make this directory as a temp directory
            try:
                os.mkdir(dstDir)
            except OSError:  # cannot make the directory
                dstDir = tempfile.gettempdir()
            return dstDir

    def getKeysToPaths(self):
        '''
        Find all keys that refer to paths
        
        >>> e = environment.Environment()
        >>> for i in e.getKeysToPaths():
        ...     #_DOCS_SHOW print(i)
        ...     pass #_DOCS_HIDE

        braillePath
        graphicsPath
        lilypondPath
        ...
        '''
        return self._keysToPaths

    def getRefKeys(self):
        '''
        Find all keys (in any order)...
        
        >>> e = environment.Environment()
        >>> for i in e.getRefKeys():
        ...     #_DOCS_SHOW print(i)
        ...     pass #_DOCS_HIDE

        lilypondBackend
        pdfPath
        lilypondVersion
        graphicsPath
        ...
        '''
        # list() is for python3 compatibility
        return list(self._ref.keys())

    def getRootTempDir(self):
        '''
        gets either the directory in key 'directoryScratch' or self.getDefaultRootTempDir
        
        Returns an exception if directoryScratch is defined but does not exist.
        '''
        if self._ref['directoryScratch'] is None:
            return self.getDefaultRootTempDir()
        # check that the user-specified directory exists
        elif not os.path.exists(self._ref['directoryScratch']):
            raise EnvironmentException(
                'user-specified scratch directory ({}) does not exist; '
                'remove preference file or reset Environment'.format(
                    self._ref['directoryScratch']))
        else:
            return self._ref['directoryScratch']

    def getSettingsPath(self):
        platform = common.getPlatform()
        if platform == 'win':
            # try to use defined app data directory for preference file
            # this is not available on all windows versions
            if 'APPDATA' in os.environ:
                directory = os.environ['APPDATA']
            elif ('USERPROFILE' in os.environ and
                os.path.exists(os.path.join(
                    os.environ['USERPROFILE'], 'Application Data'))):
                directory = os.path.join(
                    os.environ['USERPROFILE'],
                    'Application Data',
                    )
            else:  # use home directory
                directory = os.path.expanduser('~')
            return os.path.join(directory, 'music21-settings.xml')
        elif platform in ['nix', 'darwin']:
            # alt : os.path.expanduser('~')
            # might not exist if running as nobody in a webserver...
            if 'HOME' in os.environ:
                directory = os.environ['HOME']
            else:
                directory = '/tmp/'
            return os.path.join(directory, '.music21rc')
        # darwin specific option
        # os.path.join(os.environ['HOME'], 'Library',)

    def getTempFile(self, suffix=''):
        '''
        gets a temporary file with a suffix that will work for a bit.
        note that the file is closed after finding, so some older versions
        of python/OSes, etc. will immediately delete the file.
        '''
        # get the root dir, which may be the user-specified dir
        rootDir = self.getRootTempDir()

        if common.getPlatform() != 'win':
            fileDescriptor, filePath = tempfile.mkstemp(
                dir=rootDir, suffix=suffix)
            if isinstance(fileDescriptor, int):
                # on MacOS, fd returns an int, like 3, when this is called
                # in some context (specifically, programmatically in a
                # TestExternal class. the filePath is still valid and works
                pass
            else:
                fileDescriptor.close()
        else:  # win
            if sys.hexversion < 0x02030000:
                raise EnvironmentException(
                    'Need at least Version 2.3 on Windows to create temporary '
                    'files!')
            else:
                tf = tempfile.NamedTemporaryFile(dir=rootDir, suffix=suffix)
                filePath = tf.name
                tf.close()
        #self.printDebug([_MOD, 'temporary file:', filePath])
        return filePath

    def keys(self):
        return list(self._ref.keys()) + ['localCorpusPath']

    def formatToKey(self, m21Format):
        '''
        Finds the appropriate key to the file/app that can launch the given format:
        
        >>> e = environment.Environment()
        >>> e.formatToKey('lilypond')
        'lilypondPath'
        >>> e.formatToKey('png')
        'graphicsPath'
        >>> e.formatToKey('jpeg')
        'graphicsPath'
        >>> e.formatToKey('svg')
        'vectorPath'
        >>> e.formatToKey('pdf')
        'pdfPath'
        >>> e.formatToKey('musicxml')
        'musicxmlPath'
        >>> e.formatToKey('midi')
        'midiPath'
        >>> e.formatToKey('braille')
        'braillePath'

        returns None if there is no key for this format (whether the format exists or not...)

        >>> e.formatToKey('ipython') is None  # actual format
        True
        >>> e.formatToKey('adobePhotoshop') is None # not a music21 format
        True
        '''
        environmentKey = None
        if m21Format == 'lilypond':
            environmentKey = 'lilypondPath'
        elif m21Format in ('png', 'jpeg'):
            environmentKey = 'graphicsPath'
        elif m21Format == 'svg':
            environmentKey = 'vectorPath'
        elif m21Format == 'pdf':
            environmentKey = 'pdfPath'
        elif m21Format == 'musicxml':
            environmentKey = 'musicxmlPath'
        elif m21Format == 'midi':
            environmentKey = 'midiPath'
        elif m21Format == 'braille':
            environmentKey = 'braillePath'
        return environmentKey

    def formatToApp(self, m21Format):
        environmentKey = self.formatToKey(m21Format)
        if environmentKey is not None:
            if environmentKey not in self._ref:
                raise EnvironmentException(environmentKey + " is not set in UserSettings. ")
            return self._ref[environmentKey]
        return None

    def launch(self, fmt, filePath, options='', app=None):
        '''
        DEPRECATED May 24 -- call Launch on SubConverter
        '''
        # see common.fileExtensions for format names
        m21Format, unused_ext = common.findFormat(fmt)
        environmentKey = self.formatToKey(m21Format)
        if environmentKey is None:
            environmentKey = self.formatToKey(fmt)
        if m21Format == 'vexflow':
            try:
                import webbrowser
                if filePath.find('\\') != -1:
                    pass
                else:
                    if filePath.startswith('/'):
                        filePath = 'file://' + filePath

                webbrowser.open(filePath)
                return
            except ImportError:
                print('Cannot open webbrowser, sorry. Go to file://{}'.format(
                    filePath))
        if app is not None:
            # substitute app provided via argument
            fpApp = app
        elif environmentKey is not None:
            fpApp = self._ref[environmentKey]
        else:
            fpApp = None

        platform = common.getPlatform()
        if fpApp is None:
            if platform == 'win':
                # no need to specify application here:
                # windows starts the program based on the file extension
                cmd = 'start %s' % (filePath)
            elif platform == 'darwin':
                cmd = 'open %s %s' % (options, filePath)
            else:
                if m21Format == 'braille':
                    with open(filePath, 'r') as f:
                        for line in f:
                            print(line, end="")
                        print("")
                    return                    
                else:
                    raise EnvironmentException(
                        "Cannot find a valid application path for format {}. "
                        "Specify this in your Environment by calling "
                        "environment.set({!r}, 'pathToApplication')".format(
                            m21Format, environmentKey))
        elif platform == 'win':  # note extra set of quotes!
            cmd = '""%s" %s "%s""' % (fpApp, options, filePath)
        elif platform == 'darwin':
            cmd = 'open -a"%s" %s "%s"' % (fpApp, options, filePath)
        elif platform == 'nix':
            cmd = '%s %s "%s"' % (fpApp, options, filePath)
        os.system(cmd)

    def read(self, filePath=None):
        if filePath is None:
            filePath = self.getSettingsPath()
        if not os.path.exists(filePath):
            return None  # do nothing if no file exists
        saxparser = xml.sax.make_parser()
        saxparser.setFeature(xml.sax.handler.feature_external_ges, 0)
        saxparser.setFeature(xml.sax.handler.feature_external_pes, 0)
        saxparser.setFeature(xml.sax.handler.feature_namespaces, 0)
        h = SettingsHandler()
        saxparser.setContentHandler(h)
#         if six.PY2:
#             openStyle = 'r'
#         else:
#             openStyle = 'rt'
#         
        openStyle = 'r'
        with open(filePath, openStyle) as f:
            saxparser.parse(f)
        # load from XML into dictionary
        # updates self._ref in place
        self._fromSettings(h.getSettings(), self._ref)

    def restoreDefaults(self):
        self._ref = {}
        self._loadDefaults()  # defines all valid keys in ref

    def write(self, filePath=None):
        if filePath is None:
            filePath = self.getSettingsPath()
        # need to use __getitem__ here b/c need to covnert debug value
        # to an integer
        directory = os.path.split(filePath)[0]
        if filePath is None or not os.path.exists(directory):
            raise EnvironmentException('bad file path: %s' % filePath)
        settings = self._toSettings(self._ref)
        with open(filePath, 'w') as f:
            f.write(settings.xmlStr())


#------------------------------------------------------------------------------


# store one instance of _EnvironmentCore within this module
# this is a module-level implementation of the singleton pattern
# reloading the module will force a recreation of the module
_environStorage = {'instance': None, 'forcePlatform': None}

# create singleton instance
_environStorage['instance'] = _EnvironmentCore()


#------------------------------------------------------------------------------
class Environment(object):
    '''
    The environment.Environment object stores user preferences as a
    dictionary-like object.  Additionally, the Environment object provides
    convenience methods to music21 modules for getting temporary files,
    launching files with external applications, and printing debug and warning
    messages.

    Generally, each module creates a single, module-level instance of
    Environment, passing the module's name during creation. (This is an
    efficient operation since the Environment module caches most information
    from module to module)

    For more a user-friendly interface for creating and editing settings, see
    the :class:`~music21.environment.UserSettings` object.

    ::

        >>> from music21 import environment
        >>> env = environment.Environment(forcePlatform='darwin')
        >>> env['musicxmlPath'] = '/Applications/Finale Reader.app'
        >>> env['musicxmlPath']
        '/Applications/Finale Reader.app'

    '''

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['read', 'write', 'getSettingsPath']

    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
        'modNameParent': '''
            A string representation of the module that contains this
            Environment instance.
            ''',
        }

    ### INITIALIZER ###

    def __init__(self, modName=None, forcePlatform=None):
        '''
        Create an instance of this object, reading settings from disk.

        When created from a module, the `modName` parameter stores a string
        naming the module. This is used to identify the output of printDebug()
        calls.

        The `forcePlatform` argument can be used for testing what the
        environment settings would look like on another OS platform (e.g., win,
        nix, darwin).

        ::

            >>> from music21 import environment
            >>> myEnv = environment.Environment()
            >>> post = myEnv['writeFormat']
            >>> #_DOCS_SHOW post
            >>> print("\'musicxml\'") #_DOCS_HIDE
            'musicxml'

        '''
        self.modNameParent = modName
        # only re-create the instance if forcing a different platform
        # this only happens in testing
        # otherwise, delegate all calls to the module-level instance
        if forcePlatform != _environStorage['forcePlatform']:
            _environStorage['instance'] = _EnvironmentCore(
                forcePlatform=forcePlatform)

    ### SPECIAL METHODS ###

    def __getitem__(self, key):
        return _environStorage['instance'].__getitem__(key)

    def __repr__(self):
        return _environStorage['instance'].__repr__()

    def __setitem__(self, key, value):
        '''
        Dictionary-like setting. Changes are made only to local dictionary.

        Must call write() to make permanent:

        ::

            >>> from music21 import environment
            >>> a = environment.Environment()
            >>> a['debug'] = 1
            >>> a['graphicsPath'] = '/test&Encode'
            >>> a['graphicsPath']
            '/test&amp;Encode'

        ::

            >>> a['autoDownload'] = 'adsf'
            Traceback (most recent call last):
            EnvironmentException: adsf is not an acceptable value for preference: autoDownload

        ::

            >>> a['showFormat'] = 'adsf'
            Traceback (most recent call last):
            EnvironmentException: adsf is not an acceptable value for preference: showFormat

        ::

            >>> a['showFormat'] = 'musicxml'
            >>> a['localCorpusPath'] = '/path/to/local'

        '''
        _environStorage['instance'].__setitem__(key, value)

    def __str__(self):
        return _environStorage['instance'].__str__()

    ### PUBLIC METHODS ###

    def getDefaultRootTempDir(self):
        '''
        Use the Python tempfile.gettempdir() to get the system specified
        temporary directory, and try to add a new 'music21' directory, and then
        return this directory.

        This method is only called if the no scratch directory preference has
        been set.

        If not able to create a 'music21' directory, the standard default is
        returned.
        '''
        dstDir = _environStorage['instance'].getDefaultRootTempDir()
        self.printDebug([_MOD, 'using temporary directory:', dstDir])
        return dstDir

    def getKeysToPaths(self):
        ''' Get the keys that refer to file paths.

        ::

            >>> from music21 import environment
            >>> a = environment.Environment()
            >>> for x in sorted(a.getKeysToPaths()):
            ...     x
            ...
            'braillePath'
            'graphicsPath'
            'lilypondPath'
            'localCorpusPath'
            'manualCoreCorpusPath'
            'midiPath'
            'musescoreDirectPNGPath'
            'musicxmlPath'
            'pdfPath'
            'vectorPath'

        '''
        return _environStorage['instance'].getKeysToPaths()

    def getRefKeys(self):
        '''
        Get the raw keys stored in the internal reference dictionary.

        These are different than the keys() method in that the
        'localCorpusPath' entry is not included.

        ::

            >>> from music21 import environment
            >>> a = environment.Environment()
            >>> for x in sorted(a.getRefKeys()):
            ...     x
            ...
            'autoDownload'
            'braillePath'
            'debug'
            'directoryScratch'
            'graphicsPath'
            'ipythonShowFormat'
            'lilypondBackend'
            'lilypondFormat'
            'lilypondPath'
            'lilypondVersion'
            'localCorporaSettings'
            'localCorpusSettings'
            'manualCoreCorpusPath'
            'midiPath'
            'musescoreDirectPNGPath'
            'musicxmlPath'
            'pdfPath'
            'showFormat'
            'vectorPath'
            'warnings'
            'writeFormat'

        '''
        return _environStorage['instance'].getRefKeys()

    def getRootTempDir(self):
        '''
        Return a directory for writing temporary files. This does not create a
        new directory for each use, but either uses the user-set preference or
        gets the system-provided directory (with a music21 subdirectory, if
        possible).
        '''
        return _environStorage['instance'].getRootTempDir()

    def getSettingsPath(self):
        '''
        Return the path to the platform specific settings file.
        '''
        return _environStorage['instance'].getSettingsPath()

    def getTempFile(self, suffix=''):
        '''
        Return a file path to a temporary file with the specified suffix (file
        extension).
        '''
        filePath = _environStorage['instance'].getTempFile(suffix=suffix)
        self.printDebug([_MOD, 'temporary file:', filePath])
        return filePath

    def keys(self):
        '''
        Return valid keys to get and set values for the Environment instance.

        >>> from music21 import environment
        >>> e = environment.Environment()
        >>> for x in sorted(list(e.keys())):
        ...     x
        ...
        'autoDownload'
        'braillePath'
        'debug'
        'directoryScratch'
        'graphicsPath'
        'ipythonShowFormat'
        'lilypondBackend'
        'lilypondFormat'
        'lilypondPath'
        'lilypondVersion'
        'localCorporaSettings'
        'localCorpusPath'
        'localCorpusSettings'
        'manualCoreCorpusPath'
        'midiPath'
        'musescoreDirectPNGPath'
        'musicxmlPath'
        'pdfPath'
        'showFormat'
        'vectorPath'
        'warnings'
        'writeFormat'

        '''
        return _environStorage['instance'].keys()

    def formatToApp(self, m21Format):
        return _environStorage['instance'].formatToApp(m21Format)

    def formatToKey(self, m21Format):
        return _environStorage['instance'].formatToKey(m21Format)

    def launch(self, fmt, filePath, options='', app=None):
        '''
        Opens a file with an either default or user-specified applications.

        OMIT_FROM_DOCS

        Optionally, can add additional command to erase files, if necessary
        Erase could be called from os or command-line arguments after opening
        the file and then a short time delay.

        TODO: Switch to module subprocess to prevent hanging.
        '''
        return _environStorage['instance'].launch(fmt, filePath,
                options=options, app=app)

    def printDebug(self, msg, statusLevel=common.DEBUG_USER, debugFormat=None):
        '''
        Format one or more data elements into string, and print it to stderr.
        The first arg can be a list of strings or a string; lists are
        concatenated with common.formatStr().
        '''
        if _environStorage['instance'].__getitem__('debug') >= statusLevel:
            if common.isStr(msg):
                msg = [msg]  # make into a list
            if msg[0] != self.modNameParent and self.modNameParent is not None:
                msg = [self.modNameParent + ':'] + msg
            # pass list to common.formatStr
            msg = common.formatStr(*msg, format=debugFormat)
            sys.stderr.write(msg)

    def read(self, filePath=None):
        '''
        Load an XML preference file if and only if the file is available
        and has been written in the past. This means that no preference file
        will ever be written unless manually done so. If no preference file
        exists, the method returns None.
        '''
        return _environStorage['instance'].read(filePath=filePath)

    def restoreDefaults(self):
        '''
        Restore only defaults for all parameters. Useful for testing.

        ::

            >>> from music21 import environment
            >>> a = environment.Environment()
            >>> a['debug'] = 1
            >>> a.restoreDefaults()
            >>> a['debug']
            0

        And we can ``read()`` the environment settings back from our
        configuration file to restore our normal working environment.

        ::

            >>> a = environment.Environment().read()

        '''
        _environStorage['instance'].restoreDefaults()

    def warn(self, msg, header=None):
        '''
        To print a warning to the user, send a list of strings to this method.
        Similar to printDebug but even if debug is off.
        '''
        if common.isStr(msg):
            msg = [msg]  # make into a list
        elif isinstance(msg, dict):
            msg = [repr(msg)]
        elif common.isNum(msg):
            msg = [str(msg)]
        if header is None:
            if msg[0] != self.modNameParent and self.modNameParent is not None:
                msg = [self.modNameParent + ': WARNING:'] + msg
        else:
            msg = [header] + msg
        msg = common.formatStr(*msg)
        sys.stderr.write(msg)

    def write(self, filePath=None):
        '''
        Write an XML preference file. This must be manually called to store
        any changes made to the object and access preferences later.
        If `filePath` is None, the default storage location will be used.
        '''
        return _environStorage['instance'].write(filePath=filePath)


#------------------------------------------------------------------------------


class UserSettings(object):
    '''
    The UserSettings object provides a simple interface for configuring the
    user preferences in the :class:`~music21.environment.Environment` object.

    First, create an instance of UserSettings:

    ::

        >>> from music21 import environment
        >>> us = environment.UserSettings()

    Second, view the available settings keys.

    ::

        >>> for key in sorted(us.keys()):
        ...     key
        ...
        'autoDownload'
        'braillePath'
        'debug'
        'directoryScratch'
        'graphicsPath'
        'ipythonShowFormat'
        'lilypondBackend'
        'lilypondFormat'
        'lilypondPath'
        'lilypondVersion'
        'localCorporaSettings'
        'localCorpusPath'
        'localCorpusSettings'
        'manualCoreCorpusPath'
        'midiPath'
        'musescoreDirectPNGPath'
        'musicxmlPath'
        'pdfPath'
        'showFormat'
        'vectorPath'
        'warnings'
        'writeFormat'

    Third, after finding the desired setting, supply the new value as a Python
    dictionary key value pair. Setting this value updates the user's settings
    file. For example, to set the file path to the Application that will be
    used to open MusicXML files, use the 'musicxmlPath' key.

    ::

        >>> #_DOCS_SHOW us['musicxmlPath'] = '/Applications/Finale Reader.app'
        >>> #_DOCS_SHOW us['musicxmlPath']
        u'/Applications/Finale Reader.app'

    Note that the 'localCorpusPath' setting operates in a slightly different
    manner than other settings. Each time the 'localCorpusPath' setting is set,
    an additional local corpus file path is added to the list of local corpus
    paths (unless that path is already defined in the list of local corpus
    paths). To view all local corpus paths, access the 'localCorpusSettings'
    settings. This setting can also be used to set a complete list of file
    paths.

    ::

        >>> #_DOCS_SHOW us['localCorpusPath'] = '~/Documents'
        >>> #_DOCS_SHOW us['localCorpusSettings']
        ['~/Documents']

    Alternatively, the environment.py module provides convenience functions for
    setting these settings: :func:`~music21.environment.keys`,
    :func:`~music21.environment.get`, and :func:`~music21.environment.set`.
    '''

    ### INITIALIZER ###

    def __init__(self):
        # store environment as a private attribute
        self._environment = Environment()

    ### SPECIAL METHODS ###

    def __getitem__(self, key):
        # location specific, cannot test further
        return self._environment.__getitem__(key)

    def __repr__(self):
        '''
        Return a string representation.

        ::

            >>> from music21 import environment
            >>> us = environment.UserSettings()
            >>> post = repr(us) # location specific, cannot test

        '''
        return self._environment.__repr__()

    def __str__(self):
        '''
        Return a string representation.

        ::

            >>> from music21 import environment
            >>> us = environment.UserSettings()
            >>> post = repr(us) # location specific, cannot test

        '''
        return self._environment.__str__()

    def __setitem__(self, key, value):
        '''
        Dictionary-like setting. Changes are made and written to the user
        configuration file.

        ::

            >>> from music21 import environment
            >>> us = environment.UserSettings()
            >>> us['musicxmlPath'] = 'asdfwerasdffasdfwer'
            Traceback (most recent call last):
            UserSettingsException: attempting to set a path that does not exist: asdfwerasdffasdfwer

        ::

            >>> us['localCorpusPath'] = '/path/to/local'
            Traceback (most recent call last):
            UserSettingsException: attempting to set a path that does not exist: /path/to/local

        '''
        # NOTE: testing setting of any UserSettings key will result
        # in a change in your local preferences files

        # before setting value, see if this is a path and test existence
        # this will accept localCorpusPath
        if key in self._environment.getKeysToPaths():
            # try to expand user if found; otherwise return unaltered
            if value is not None:
                value = os.path.expanduser(value)
                if not os.path.exists(value):
                    raise UserSettingsException(
                        'attempting to set a path that does not exist: {}'.format(
                            value))
        # when setting a local corpus setting, if not a list, append
        elif key == 'localCorpusSettings':
            if not common.isListLike(value):
                raise UserSettingsException(
                    'localCorpusSettings must be provided as a list.')
        # location specific, cannot test further
        self._environment.__setitem__(key, value)
        self._environment.write()
        #self._updateAllEnvironments()

    ### PUBLIC METHODS ###

    def create(self):
        '''
        If a environment configuration file does not exist, create one based on
        the default settings.
        '''
        if not os.path.exists(self._environment.getSettingsPath()):
            self._environment.write()
        else:
            raise UserSettingsException(
                'An environment configuration file already exists; '
                'simply set values to modify.')

    def delete(self):
        '''
        Permanently remove the user configuration file.
        '''
        if os.path.exists(self._environment.getSettingsPath()):
            os.remove(self._environment.getSettingsPath())
        else:
            raise UserSettingsException(
                'An environment configuration file does not exist.')

    def getSettingsPath(self):
        '''
        Return the path to the platform specific settings file.
        '''
        return self._environment.getSettingsPath()

    def keys(self):
        '''
        Return the keys found in the user's
        :class:`~music21.environment.Environment` object.
        '''
        return self._environment.getRefKeys() + ['localCorpusPath']

    def restoreDefaults(self):
        '''
        Restore platform specific defaults.
        '''
        # location specific, cannot test further
        self._environment.restoreDefaults()
        self._environment.write()


#------------------------------------------------------------------------------
# convenience routines for accessing UserSettings.


def keys():
    '''
    Return all valid UserSettings keys.
    '''
    us = UserSettings()
    return us.keys()


def set(key, value):  # okay to override set here: @ReservedAssignment
    '''
    Directly set a single UserSettings key, by providing a key and the
    appropriate value. This will create a user settings file if necessary.

    ::

        >>> from music21 import environment
        >>> for x in sorted(environment.keys()):
        ...     x
        ...
        'autoDownload'
        'braillePath'
        'debug'
        'directoryScratch'
        'graphicsPath'
        'ipythonShowFormat'
        'lilypondBackend'
        'lilypondFormat'
        'lilypondPath'
        'lilypondVersion'
        'localCorporaSettings'
        'localCorpusPath'
        'localCorpusSettings'
        'manualCoreCorpusPath'
        'midiPath'
        'musescoreDirectPNGPath'
        'musicxmlPath'
        'pdfPath'
        'showFormat'
        'vectorPath'
        'warnings'
        'writeFormat'

    ::

        >>> environment.set('wer', 'asdf')
        Traceback (most recent call last):
        EnvironmentException: no preference: wer

    ::

        >>> #_DOCS_SHOW environment.set('musicxmlPath', '/Applications/Finale Reader.app')

    '''
    us = UserSettings()
    try:
        us.create()  # no problem if this does not exist
    except UserSettingsException:
        pass  # this means it already exists
    us[key] = value  # this may raise an exception


def get(key):
    '''
    Return the current setting of a UserSettings key.

    This will create a user settings file if necessary:

    ::

        >>> from music21 import environment
        >>> for x in sorted(environment.keys()):
        ...     x
        ...
        'autoDownload'
        'braillePath'
        'debug'
        'directoryScratch'
        'graphicsPath'
        'ipythonShowFormat'
        'lilypondBackend'
        'lilypondFormat'
        'lilypondPath'
        'lilypondVersion'
        'localCorporaSettings'
        'localCorpusPath'
        'localCorpusSettings'
        'manualCoreCorpusPath'
        'midiPath'
        'musescoreDirectPNGPath'
        'musicxmlPath'
        'pdfPath'
        'showFormat'
        'vectorPath'
        'warnings'
        'writeFormat'

    ::

        >>> #_DOCS_SHOW environment.get('musicxmlPath')
        '/Applications/Finale Reader.app'

    '''
    us = UserSettings()
    return us[key]


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def runTest(self):
        pass

    def testTest(self):
        self.assertEqual(1, 1)

    def testSettings(self):

        storage = Settings()
        for i in range(10):
            slot = Preference()
            slot.set('name', 'name%s' % i)
            slot.set('value', i)
            storage.append(slot)
        xstr = storage.xmlStr()
        if 'encoding' in xstr:
            enc = 'encoding="utf-8"'
        else:
            enc = ''
        self.assertEqual("""<?xml version="1.0" """ + enc + """?>
<settings>
  <preference name="name0" value="0"/>
  <preference name="name1" value="1"/>
  <preference name="name2" value="2"/>
  <preference name="name3" value="3"/>
  <preference name="name4" value="4"/>
  <preference name="name5" value="5"/>
  <preference name="name6" value="6"/>
  <preference name="name7" value="7"/>
  <preference name="name8" value="8"/>
  <preference name="name9" value="9"/>
</settings>
""", xstr)

    def testToSettings(self):

        env = Environment(forcePlatform='darwin')
        match = _environStorage['instance']._toSettings(
            _environStorage['instance']._ref).xmlStr()
        self.maxDiff = None
        if 'encoding' in match:
            enc = 'encoding="utf-8"'
        else:
            enc = ''
        canonic = """<?xml version="1.0" """ + enc + """?>
<settings>
  <preference name="autoDownload" value="ask"/>
  <preference name="braillePath"/>
  <preference name="debug" value="0"/>
  <preference name="directoryScratch"/>
  <preference name="graphicsPath" value="/Applications/Preview.app"/>
  <preference name="ipythonShowFormat" value="ipython.lilypond.png"/>
  <preference name="lilypondBackend" value="ps"/>
  <preference name="lilypondFormat" value="pdf"/>
  <preference name="lilypondPath" value="/Applications/Lilypond.app/Contents/Resources/bin/lilypond"/>
  <preference name="lilypondVersion"/>
  <localCorporaSettings/>
  <localCorpusSettings/>
  <preference name="manualCoreCorpusPath"/>
  <preference name="midiPath" value="/Applications/QuickTime Player.app"/>
  <preference name="musescoreDirectPNGPath" value="/Applications/MuseScore 2.app/Contents/MacOS/mscore"/>
  <preference name="musicxmlPath" value="/Applications/Finale Notepad 2012.app"/>
  <preference name="pdfPath" value="/Applications/Preview.app"/>
  <preference name="showFormat" value="musicxml"/>
  <preference name="vectorPath" value="/Applications/Preview.app"/>
  <preference name="warnings" value="1"/>
  <preference name="writeFormat" value="musicxml"/>
</settings>
"""
        self.assertEqual(canonic.split('\n'), match.split('\n'))

        # try adding some local corpus settings
        env['localCorpusSettings'] = ['a', 'b', 'c']
        env['localCorporaSettings']['foo'] = ['bar', 'baz', 'quux']
        match = _environStorage['instance']._toSettings(
            _environStorage['instance']._ref).xmlStr()
        if 'encoding' in match:
            enc = 'encoding="utf-8"'
        else:
            enc = ''
        canonic = """<?xml version="1.0" """ + enc + """?>
<settings>
  <preference name="autoDownload" value="ask"/>
  <preference name="braillePath"/>
  <preference name="debug" value="0"/>
  <preference name="directoryScratch"/>
  <preference name="graphicsPath" value="/Applications/Preview.app"/>
  <preference name="ipythonShowFormat" value="ipython.lilypond.png"/>
  <preference name="lilypondBackend" value="ps"/>
  <preference name="lilypondFormat" value="pdf"/>
  <preference name="lilypondPath" value="/Applications/Lilypond.app/Contents/Resources/bin/lilypond"/>
  <preference name="lilypondVersion"/>
  <localCorporaSettings>
    <localCorpusSettings name="foo">
      <localCorpusPath>bar</localCorpusPath>
      <localCorpusPath>baz</localCorpusPath>
      <localCorpusPath>quux</localCorpusPath>
    </localCorpusSettings>
  </localCorporaSettings>
  <localCorpusSettings>
    <localCorpusPath>a</localCorpusPath>
    <localCorpusPath>b</localCorpusPath>
    <localCorpusPath>c</localCorpusPath>
  </localCorpusSettings>
  <preference name="manualCoreCorpusPath"/>
  <preference name="midiPath" value="/Applications/QuickTime Player.app"/>
  <preference name="musescoreDirectPNGPath" value="/Applications/MuseScore 2.app/Contents/MacOS/mscore"/>
  <preference name="musicxmlPath" value="/Applications/Finale Notepad 2012.app"/>
  <preference name="pdfPath" value="/Applications/Preview.app"/>
  <preference name="showFormat" value="musicxml"/>
  <preference name="vectorPath" value="/Applications/Preview.app"/>
  <preference name="warnings" value="1"/>
  <preference name="writeFormat" value="musicxml"/>
</settings>
"""
        self.assertEqual(canonic.split('\n'), match.split('\n'))

    def testFromSettings(self):

        unused_env = Environment(forcePlatform='darwin')

        # use a fake ref dict to get settings
        ref = {}
        ref['localCorpusSettings'] = ['x', 'y', 'z']
        ref['midiPath'] = 'w'
        settings = _environStorage['instance']._toSettings(ref)

        # this will load values into the env._ref dictionary
        _environStorage['instance']._fromSettings(settings,
            _environStorage['instance']._ref)
        # get xml strings
        match = _environStorage['instance']._toSettings(
            _environStorage['instance']._ref).xmlStr()
        if 'encoding' in match:
            enc = 'encoding="utf-8"'
        else:
            enc = ''
        canonic = """<?xml version="1.0" """ + enc + """?>
<settings>
  <preference name="autoDownload" value="ask"/>
  <preference name="braillePath"/>
  <preference name="debug" value="0"/>
  <preference name="directoryScratch"/>
  <preference name="graphicsPath" value="/Applications/Preview.app"/>
  <preference name="ipythonShowFormat" value="ipython.lilypond.png"/>
  <preference name="lilypondBackend" value="ps"/>
  <preference name="lilypondFormat" value="pdf"/>
  <preference name="lilypondPath" value="/Applications/Lilypond.app/Contents/Resources/bin/lilypond"/>
  <preference name="lilypondVersion"/>
  <localCorporaSettings/>
  <localCorpusSettings>
    <localCorpusPath>x</localCorpusPath>
    <localCorpusPath>y</localCorpusPath>
    <localCorpusPath>z</localCorpusPath>
  </localCorpusSettings>
  <preference name="manualCoreCorpusPath"/>
  <preference name="midiPath" value="w"/>
  <preference name="musescoreDirectPNGPath" value="/Applications/MuseScore 2.app/Contents/MacOS/mscore"/>
  <preference name="musicxmlPath" value="/Applications/Finale Notepad 2012.app"/>
  <preference name="pdfPath" value="/Applications/Preview.app"/>
  <preference name="showFormat" value="musicxml"/>
  <preference name="vectorPath" value="/Applications/Preview.app"/>
  <preference name="warnings" value="1"/>
  <preference name="writeFormat" value="musicxml"/>
</settings>
"""
        self.assertEqual(canonic.split(), match.split())

    def testEnvironmentA(self):
        env = Environment(forcePlatform='darwin')

        # setting the local corpus path pref is like adding a path
        env['localCorpusPath'] = 'a'
        self.assertEqual(env['localCorpusSettings'], ['a'])

        env['localCorpusPath'] = 'b'
        self.assertEqual(env['localCorpusSettings'], ['a', 'b'])


#------------------------------------------------------------------------------


_DOC_ORDER = [UserSettings, Environment, Preference]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
