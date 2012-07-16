# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         environment.py
# Purpose:      Storage for user environment settings and defaults
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
The environment module describes an object for accessing and setting
variables related to the user's music21 environment. Such variables include
the location of external applications such as MusicXML readers (e.g. Finale), 
whether music21 is allowed to download files directly (via the virtual corpus), 
and other settings.

Additional documentation for and examples of using this module are found in :ref:`environment`.
'''


import os, sys
import tempfile
import doctest, unittest
import xml.sax

import music21
from music21 import common
from music21 import xmlnode


_MOD = 'environment.py'


#-------------------------------------------------------------------------------
class EnvironmentException(Exception):
    pass

class UserSettingsException(EnvironmentException):
    pass


#-------------------------------------------------------------------------------
class Settings(xmlnode.XMLNodeList):
    '''
    '''
    def __init__(self):
        '''
        >>> a = Settings()
        '''
        xmlnode.XMLNodeList.__init__(self)
        self._tag = 'settings' # assumed for now
        self.componentList = [] # list of Part objects

    def _getComponents(self):
        return self.componentList

class Preference(xmlnode.XMLNode):
    '''
    An xmlnode.XMLNode subclass representing a single environment preference

    '''
    # TODO: Make private class because there's no docs and no public interface.
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = environment.Preference()
        '''
        xmlnode.XMLNode.__init__(self)
        self._tag = 'preference' # assumed for now
        # attributes
        self._attr['name'] = None
        self._attr['value'] = None

class LocalCorpusSettings(xmlnode.XMLNodeList):
    '''
    An xmlnode.XMLNode subclass representing a a list of environment preference
    '''
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = environment.Preference()
        '''
        xmlnode.XMLNode.__init__(self)
        self._tag = 'localCorpusSettings' # assumed for now
        self.componentList = [] # list of LocalCorpusPath objects

    def _getComponents(self):
        return self.componentList

class LocalCorpusPath(xmlnode.XMLNode):
    '''
    An xmlnode.XMLNode subclass representing a a list of environment preference

    >>> from music21 import *
    >>> lcs = environment.LocalCorpusSettings()
    >>> lcp = environment.LocalCorpusPath()
    >>> lcp.charData = 'testing'
    >>> lcs.append(lcp)
    >>> print lcs.xmlStr()
    <?xml version="1.0" encoding="utf-8"?>
    <localCorpusSettings>
      <localCorpusPath>testing</localCorpusPath>
    </localCorpusSettings>
    <BLANKLINE>
    '''
    def __init__(self):
        '''
        >>> from music21 import *
        >>> a = environment.Preference()
        '''
        xmlnode.XMLNode.__init__(self)
        self._tag = 'localCorpusPath' # assumed for now
        self.charData = None # char data stores path
        # attributes


#-------------------------------------------------------------------------------
class SettingsHandler(xml.sax.ContentHandler):
    '''
    An xml.sax.ContentHandler subclass holding settings

    >>> from music21 import *
    >>> sh = environment.SettingsHandler()
    '''
    #TODO: Make private class because there's no docs and no public interface.

    def __init__(self, tagLib=None):
        self.localCorpusSettings = LocalCorpusSettings()
        # create directly, not in sax parsing; this is just a shortcut
        self._settings = Settings() 
        self._charData = ''     

    def startElement(self, name, attrs):
        if name == 'preference':        
            slot = Preference()
            slot.loadAttrs(attrs)
            self._settings.append(slot)

    def characters(self, charData):
        self._charData += charData

    def endElement(self, name):
        if name == 'localCorpusPath':     
            lcp = LocalCorpusPath()   
            lcp.charData = self._charData
            self._charData = '' # must clear after reading in 
            self.localCorpusSettings.append(lcp)
            
    def getSettings(self):
        # only called after processing; can add local corpus settings
        self._settings.append(self.localCorpusSettings)
        return self._settings



#-------------------------------------------------------------------------------
class _EnvironmentCore(object):
    '''This private class should never be directly created; use the Environment object to access this object. 

    Multiple Environment instances may exist, but all share access to the same _EnvironmentCore instance that is stored in this module.

    The only case in which a new _EnvironmentCore is created if the forcePlatform argument is passed and is different than the stored forcePlatform argument. This is only used in testing. 

    NOTE: this is a private class. All documentation for public methods should be placed in the Environment class.
    '''
    def __init__(self, forcePlatform=None):
        # only create one
        #sys.stderr.write('creating singelton _EnvironmentCore\n')
        self._ref = {}
        # define all settings that are paths
        # store names of all values that are keys; check for validity
        self._keysToPaths = [] 
        self._keysToPaths.append('lilypondPath')
        self._keysToPaths.append('musicxmlPath')
        self._keysToPaths.append('graphicsPath')
        self._keysToPaths.append('vectorPath')
        self._keysToPaths.append('pdfPath')
        self._keysToPaths.append('midiPath')
        self._keysToPaths.append('localCorpusPath')

        # defines all valid keys in ref
        self._loadDefaults(forcePlatform=forcePlatform) 
        # read will only right over values if set in field
        if forcePlatform is None: # only read if not forcing platform
            self.read() # load a stored file if available

    def getKeysToPaths(self):
        return self._keysToPaths

    def getRefKeys(self):
        return self._ref.keys()

    def _loadDefaults(self, forcePlatform=None):
        '''Load defaults. All keys are derived from these defaults.
        '''
        self._ref['directoryScratch'] = None # path to a directory for temporary files
        self._ref['lilypondPath'] = None # path to lilypond
        self._ref['lilypondVersion'] = None # version of lilypond
        self._ref['lilypondFormat'] = 'pdf' 
        self._ref['lilypondBackend'] = 'ps' 
        # path to a MusicXML reader: default, will find "Finale Reader"
        self._ref['musicxmlPath'] = None 
        self._ref['midiPath'] = None # path to a midi reader
        self._ref['graphicsPath'] = None # path to a graphics viewer
        self._ref['vectorPath'] = None # path to a vector graphics viewer
        self._ref['pdfPath'] = None # path to a pdf viewer
        self._ref['showFormat'] = 'musicxml' 
        self._ref['writeFormat'] = 'musicxml' 
        self._ref['autoDownload'] = 'ask' 
        self._ref['debug'] = 0
        # printing of missing import warnings
        self._ref['warnings'] = 1 # default/non-zero is on

        # store a list of strings
        self._ref['localCorpusSettings'] = [] 

        if forcePlatform is None:
            platform = common.getPlatform()
        else:
            platform = forcePlatform

        if platform == 'win':
            for name, value in [
                ('lilypondPath', 'lilypond'),
                ]:
                self.__setitem__(name, value) # use for key checking
        elif platform == 'nix':
            for name, value in [('lilypondPath', 'lilypond')]:
                self.__setitem__(name, value) # use for key checking
        elif platform ==  'darwin':
            for name, value in [
            ('lilypondPath', '/Applications/Lilypond.app/Contents/Resources/bin/lilypond'),
            ('musicxmlPath', '/Applications/Finale Reader.app'),
            ('graphicsPath', '/Applications/Preview.app'),
            ('vectorPath', '/Applications/Preview.app'),
            ('pdfPath', '/Applications/Preview.app'),
            ('midiPath', '/Applications/QuickTime Player.app'),

                ]:
                self.__setitem__(name, value) # use for key checking

    def restoreDefaults(self):
        self._ref = {}
        self._loadDefaults() # defines all valid keys in ref

    def __getitem__(self, key):
        # could read file here to update from disk
        # could store last update tim and look of file is more recent
        # how, only doing read once is a bit more conservative
        #self.read()

        # note: this will not get 'localCorpusPath' as there may be more tn 
        # one value
        if key not in self._ref.keys():
            raise EnvironmentException('no preference: %s' % key)
        value = self._ref[key]
        valueStr = str(value).lower()

        if key in ['debug']: # debug expects a number
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
            value = None # return None for values not set
        return value

    def __setitem__(self, key, value):

        #saxutils.escape # used for escaping strings going to xml
        # with unicode encoding
        # http://www.xml.com/pub/a/2002/11/13/py-xml.html?page=2
        # saxutils.escape(msg).encode('UTF-8')

        # add local corpus path as a key
        if key not in self._ref.keys() + ['localCorpusPath']:
            raise EnvironmentException('no preference: %s' % key)
        if value == '':
            value = None # always replace '' with None

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
        else: # temporarily not validating other preferences
            valid = True

        if not valid:
            raise EnvironmentException('%s is not an acceptable value for preference: %s' % (value, key))

        # need to escape problematic characters for xml storage
        if common.isStr(value):
            value = xml.sax.saxutils.escape(value).encode('UTF-8')
        # set value
        if key == 'localCorpusPath':
            # only add if unique
            if value not in self._ref['localCorpusSettings']:
                # check for malicious values here
                self._ref['localCorpusSettings'].append(value)
        else:
            self._ref[key] = value

    def __repr__(self):
        return '<Environment>'

    def __str__(self):
        return repr(self._ref)

    def keys(self):
        return self._ref.keys() + ['localCorpusPath']

    #---------------------------------------------------------------------------
    def getSettingsPath(self):
        platform = common.getPlatform()
        if platform == 'win':
            # try to use defined app data directory for preference file
            # this is not available on all windows versions
            if 'APPDATA' in os.environ.keys():
                dir = os.environ['APPDATA']
            elif ('USERPROFILE' in os.environ.keys() and
                os.path.exists(os.path.join(
                os.environ['USERPROFILE'], 'Application Data'))):
                dir = os.path.join(os.environ['USERPROFILE'], 
                                   'Application Data')
            else: # use home directory
                dir = os.path.expanduser('~')       
            return os.path.join(dir, 'music21-settings.xml')
        elif platform in ['nix', 'darwin']:
            # alt : os.path.expanduser('~') 
            # might not exist if running as nobody in a webserver...
            if 'HOME' in os.environ.keys(): 
                dir = os.environ['HOME']
            else:
                dir = '/tmp/'            
            return os.path.join(dir, '.music21rc')

        # darwin specific option
        # os.path.join(os.environ['HOME'], 'Library',)

    #---------------------------------------------------------------------------
    def _fromSettings(self, settings, ref={}):
        '''Load a ref dictionary from the Settings object. Change the passed-in ref dictionary in place.
        '''
        for slot in settings:
            if isinstance(slot, LocalCorpusSettings):
                ref['localCorpusSettings'] = []
                for lcp in slot:
                    # validate paths on load
                    fpCandidate = lcp.charData.strip()
                    ref['localCorpusSettings'].append(fpCandidate)
            else:    
                name = slot.get('name')
                value = slot.get('value')
                if name not in ref.keys():
                    #self.printDebug(['a preference is defined that is longer used: %s' % name])
                    continue
                    # do not set, ignore for now
                    #raise EnvironmentException('no such defined preference: %s' % name)
                else: # load up stored values, overwriting defaults
                    ref[name] = value


    def read(self, fp=None):
        if fp == None:
            fp = self.getSettingsPath()
        if not os.path.exists(fp):
            return None # do nothing if no file exists

        saxparser = xml.sax.make_parser()
        saxparser.setFeature(xml.sax.handler.feature_external_ges, 0)
        saxparser.setFeature(xml.sax.handler.feature_external_pes, 0)
        saxparser.setFeature(xml.sax.handler.feature_namespaces, 0)  
    
        h = SettingsHandler() 
        saxparser.setContentHandler(h)
        f = open(fp) # file i/o might be done outside of loop
        saxparser.parse(f)
        f.close()    

        # load from XML into dictionary
        # updates self._ref in place
        self._fromSettings(h.getSettings(), self._ref)

    def _toSettings(self, ref):
        '''Convert a ref dictionary to a Settings object
        '''
        settings = Settings()
        for key, item in ref.items():
            if key == 'localCorpusSettings':
                lcs = LocalCorpusSettings()
                for fp in item:
                    lcp = LocalCorpusPath()
                    lcp.charData = fp
                    lcs.append(lcp)
                settings.append(lcs)
            else:
                slot = Preference()
                slot.set('name', key)
                slot.set('value', item)
                settings.append(slot)
        return settings


    def write(self, fp=None):
        if fp == None:
            fp = self.getSettingsPath()

        # need to use __getitem__ here b/c need to covnert debug value
        # to an integer
        dir, fn = os.path.split(fp)
        if fp == None or not os.path.exists(dir):
            raise EnvironmentException('bad file path: %s' % fp)

        settings = self._toSettings(self._ref)

        f = open(fp, 'w')
        f.write(settings.xmlStr())
        f.close()

    #---------------------------------------------------------------------------
    # utility methods for commonly needed OS services

    def getDefaultRootTempDir(self):
        # this returns the root temp dir; this does not create a new dir
        dstDir = os.path.join(tempfile.gettempdir(), 'music21')
        # if this path already exists, we have nothing more to do
        if os.path.exists(dstDir): 
            return dstDir
        else:
            # make this directory as a temp directory
            try:
                os.mkdir(dstDir)
            except OSError: # cannot make the directory
                dstDir = tempfile.gettempdir()
            return dstDir

    def getRootTempDir(self):
        if self._ref['directoryScratch'] is None:
            return self.getDefaultRootTempDir()
        # check that the user-specified directory exists
        elif not os.path.exists(self._ref['directoryScratch']):    
            raise EnvironmentException('user-specified scratch directory (%s) does not exist; remove preference file or reset Environment' % self._ref['directoryScratch'])
        else:
            return self._ref['directoryScratch']

    def getTempFile(self, suffix=''):
        '''
        gets a temporary file with a suffix that will work for a bit.
        note that the file is closed after finding, so some older versions
        of python/OSes, etc. will immediately delete the file.
        '''
        # get the root dir, which may be the user-specified dir
        rootDir = self.getRootTempDir()

        if common.getPlatform() != 'win':
            fd, fp = tempfile.mkstemp(dir=rootDir, suffix=suffix)
            if isinstance(fd, int):
                # on MacOS, fd returns an int, like 3, when this is called
                # in some context (specifically, programmatically in a 
                # TestExternal class. the fp is still valid and works
                pass
            else:
                fd.close() 
        else: # win
            if sys.hexversion < 0x02030000:
                raise EnvironmentException("Need at least Version 2.3 on Windows to create temporary files!")
            else:
                tf = tempfile.NamedTemporaryFile(dir=rootDir, suffix=suffix)
                fp = tf.name
                tf.close()
        #self.printDebug([_MOD, 'temporary file:', fp])
        return fp

    def launch(self, fmt, fp, options='', app=None):
        # see common.fileExtensions for format names 
        format, ext = common.findFormat(fmt)
        if format == 'lilypond':
            environmentKey = 'lilypondPath'
        elif format in ['png', 'jpeg']:
            environmentKey = 'graphicsPath'
        elif format in ['svg']:
            environmentKey = 'vectorPath'
        elif format in ['pdf']:
            environmentKey = 'pdfPath'
        elif format == 'musicxml':
            environmentKey = 'musicxmlPath'
        elif format == 'midi':
            environmentKey = 'midiPath'
        elif format == 'vexflow':
            try:
                import webbrowser
                if fp.find('\\') != -1:
                    pass
                else:
                    if fp.startswith('/'):
                        fp = 'file://' + fp
                
                webbrowser.open(fp)
                return
            except:
                print "Cannot open webbrowser, sorry.  go to file://%s" % fp
        else:
            environmentKey = None
            fpApp = None

        if environmentKey is not None:
            fpApp = self._ref[environmentKey]

        # substitute app provided via argument
        if app is not None:
            fpApp = app 

        platform = common.getPlatform()
        if fpApp is None and platform not in ['win', 'darwin']:
            raise EnvironmentException("Cannot find a valid application path for format %s. Specify this in your Environment by calling environment.set(%r, 'pathToApplication')" % (format, environmentKey))
        
        if platform == 'win' and fpApp is None:
            # no need to specify application here: windows starts the program based on the file extension
            cmd = 'start %s' % (fp)
        elif platform == 'win':  # note extra set of quotes!
            cmd = '""%s" %s "%s""' % (fpApp, options, fp)
        elif platform == 'darwin' and fpApp is None:
            cmd = 'open %s %s' % (options, fp)
        elif platform == 'darwin':
            cmd = 'open -a"%s" %s %s' % (fpApp, options, fp)
        elif platform == 'nix':
            cmd = '%s %s %s' % (fpApp, options, fp)
        os.system(cmd)



#-------------------------------------------------------------------------------
# store one instance of _EnvironmentCore within this module
# this is a module-level implementation of the singleton pattern
# reloading the module will force a recreation of the module
_environStorage = {'instance':None, 'forcePlatform':None}
# create singleton instance
_environStorage['instance'] = _EnvironmentCore()


#-------------------------------------------------------------------------------
class Environment(object):
    '''
    The environment.Environment object stores user preferences as a dictionary-like object. 
    Additionally, the Environment object provides convenience methods to music21 modules 
    for getting temporary files, launching files with external applications, and 
    printing debug and warning messages.

    Generally, each module creates a single, module-level instance of Environment, 
    passing the module's name during creation. 

    For more a user-friendly interface for creating and editing settings, see 
    the :class:`~music21.environment.UserSettings` object. 

    >>> env = Environment(forcePlatform='darwin')
    >>> env['musicxmlPath'] = '/Applications/Finale Reader.app'
    >>> env['musicxmlPath']
    '/Applications/Finale Reader.app'

    '''

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['read', 'write', 'getSettingsPath']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'modNameParent': 'A string representation of the module that contains this Environment instance.',
    }

    def __init__(self, modName=None, forcePlatform=None):
        '''
        Create an instance of this object, reading settings from disk. 

        When created from a module, the `modName` parameter stores a string naming the module. This is used to identify the output of printDebug() calls.

        The `forcePlatform` argument can be used for testing.

        >>> from music21 import *
        >>> myEnv = environment.Environment()
        >>> post = myEnv['writeFormat']
        >>> #_DOCS_SHOW post
        >>> print "\'musicxml\'" #_DOCS_HIDE
        'musicxml'
        '''
        self.modNameParent = modName
        # only re-create the instance if forcing a different platform
        # this only happens in testing
        # otherwise, delegate all calls to the module-level instance
        if forcePlatform != _environStorage['forcePlatform']:
            _environStorage['instance'] = _EnvironmentCore(
                forcePlatform=forcePlatform)

    def getKeysToPaths(self):
        ''' Get the keys that refer to file paths. 

        >>> from music21 import *
        >>> a = environment.Environment()
        >>> a.getKeysToPaths()
        ['lilypondPath', 'musicxmlPath', 'graphicsPath', 'vectorPath', 'pdfPath', 'midiPath', 'localCorpusPath']
        '''
        return _environStorage['instance'].getKeysToPaths()

    def getRefKeys(self):
        '''Get the raw keys stored in the internal reference dictionary. These are different than the keys() method in that the 'localCorpusPath' entry is not included.

        >>> from music21 import *
        >>> a = environment.Environment()
        >>> a.getRefKeys()
        ['lilypondBackend', 'pdfPath', 'lilypondVersion', 'graphicsPath', 'warnings', 'showFormat', 'localCorpusSettings', 'vectorPath', 'writeFormat', 'lilypondPath', 'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'autoDownload', 'midiPath']
        '''
        return _environStorage['instance'].getRefKeys()

    def restoreDefaults(self):
        '''Restore only defaults for all parameters. Useful for testing. 

        >>> from music21 import *
        >>> a = environment.Environment()
        >>> a['debug'] = 1
        >>> a.restoreDefaults()
        >>> a['debug']
        0
        '''
        _environStorage['instance'].restoreDefaults()

    def __getitem__(self, key):
        return _environStorage['instance'].__getitem__(key)

    def __setitem__(self, key, value):
        '''Dictionary-like setting. Changes are made only to local dictionary.
        Must call write() to make permanent

        >>> from music21 import *
        >>> a = environment.Environment()
        >>> a['debug'] = 1
        >>> a['graphicsPath'] = '/test&Encode'
        >>> a['graphicsPath']
        '/test&amp;Encode'
        >>> a['autoDownload'] = 'adsf'
        Traceback (most recent call last):
        EnvironmentException: adsf is not an acceptable value for preference: autoDownload
        >>> a['showFormat'] = 'adsf'
        Traceback (most recent call last):
        EnvironmentException: adsf is not an acceptable value for preference: showFormat
        >>> a['showFormat'] = 'musicxml'
        >>> a['localCorpusPath'] = '/path/to/local'

        '''
        _environStorage['instance'].__setitem__(key, value)

    def __repr__(self):
        return _environStorage['instance'].__repr__()

    def __str__(self):
        return _environStorage['instance'].__str__()

    def keys(self):
        '''Return valid keys to get and set values for the Environment instance.

        >>> from music21 import *
        >>> e = environment.Environment()
        >>> e.keys()
        ['lilypondBackend', 'pdfPath', 'lilypondVersion', 'graphicsPath', 'warnings', 'showFormat', 'localCorpusSettings', 'vectorPath', 'writeFormat', 'lilypondPath', 'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'autoDownload', 'midiPath', 'localCorpusPath']

        '''
        return _environStorage['instance'].keys()

    def getSettingsPath(self):
        '''Return the path to the platform specific settings file.
        '''
        return _environStorage['instance'].getSettingsPath()

    def read(self, fp=None):
        '''
        Load an XML preference file if and only if the file is available 
        and has been written in the past. This means that no preference file 
        will ever be written unless manually done so. If no preference file 
        exists, the method returns None.
        '''
        return _environStorage['instance'].read(fp=fp)

    def write(self, fp=None):
        '''
        Write an XML preference file. This must be manually called to store 
        any changes made to the object and access preferences later. 
        If `fp` is None, the default storage location will be used.
        '''
        return _environStorage['instance'].write(fp=fp)

    def getDefaultRootTempDir(self):
        '''Use the Python tempfile.gettempdir() to get the system specified 
        temporary directory, and try to add a new 'music21' directory, and 
        then return this directory.

        This method is only called if the no scratch directory preference has been set. 

        If not able to create a 'music21' directory, the standard default is returned.
        '''
        dstDir = _environStorage['instance'].getDefaultRootTempDir()
        self.printDebug([_MOD, 'using temporary directory:', dstDir])
        return dstDir

    def getRootTempDir(self):
        '''Return a directory for writing temporary files. This does 
        not create a new directory for each use, but either uses 
        the user-set preference or gets the system-provided 
        directory (with a music21 subdirectory, if possible).
        '''
        return _environStorage['instance'].getRootTempDir()

    def getTempFile(self, suffix=''):
        '''Return a file path to a temporary file with the specified suffix (file extension). 
        '''
        fp = _environStorage['instance'].getTempFile(suffix=suffix)
        self.printDebug([_MOD, 'temporary file:', fp])
        return fp

    def launch(self, fmt, fp, options='', app=None):
        '''
        Opens a file with an either default or user-specified applications.
        
        OMIT_FROM_DOCS

        Optionally, can add additional command to erase files, if necessary 
        Erase could be called from os or command-line arguments after opening
        the file and then a short time delay.

        TODO: Switch to module subprocess to prevent hanging.
        '''
        return _environStorage['instance'].launch(fmt, fp, 
                options=options, app=app)

    #---------------------------------------------------------------------------
    # methods local to each instance that is created in each module

    def printDebug(self, msg, statusLevel=common.DEBUG_USER, format=None):
        '''Format one or more data elements into string, and print it 
        to stderr. The first arg can be a list of string; lists are 
        concatenated with common.formatStr(). 
        '''
        #if not common.isNum(statusLevel):
        #    raise EnvironmentException('bad statusLevel argument given: %s' % statusLevel)
#         if self.__getitem__('debug') >= statusLevel:
#             if common.isStr(msg):
#                 msg = [msg] # make into a list
#             if msg[0] != self.modNameParent and self.modNameParent != None:
#                 msg = [self.modNameParent + ':'] + msg
#             # pass list to common.formatStr
#             msg = common.formatStr(*msg, format=format)
#             sys.stderr.write(msg)

        if _environStorage['instance'].__getitem__('debug') >= statusLevel:
            if common.isStr(msg):
                msg = [msg] # make into a list
            if msg[0] != self.modNameParent and self.modNameParent != None:
                msg = [self.modNameParent + ':'] + msg
            # pass list to common.formatStr
            msg = common.formatStr(*msg, format=format)
            sys.stderr.write(msg)


    def pd(self, msg, statusLevel=common.DEBUG_USER, format=None):
        '''Shortcut for printDebug. Useful as is typed frequently.
        '''
        self.printDebug(msg=msg, statusLevel=statusLevel, format=format)

    def warn(self, msg, header=None):
        '''To print a warning to the user, send a list of strings to this
        method. Similar to printDebug but even if debug is off.
        '''
        if common.isStr(msg):
            msg = [msg] # make into a list
        if header == None:
            if msg[0] != self.modNameParent and self.modNameParent != None:
                msg = [self.modNameParent + ': WARNING:'] + msg
        else:
            msg = [header] + msg
        msg = common.formatStr(*msg)
        sys.stderr.write(msg)
    



#-------------------------------------------------------------------------------
class UserSettings(object):
    '''The UserSettings object provides a simple interface for configuring the user preferences in the :class:`~music21.environment.Environment` object.

    First, create an instance of UserSettings:

    >>> from music21 import *
    >>> us = environment.UserSettings()

    Second, view the available settings keys.

    >>> us.keys()
    ['lilypondBackend', 'pdfPath', 'lilypondVersion', 'graphicsPath', 'warnings', 'showFormat', 'localCorpusSettings', 'vectorPath', 'writeFormat', 'lilypondPath', 'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'autoDownload', 'midiPath', 'localCorpusPath']


    Third, after finding the desired setting, supply the new value as a Python dictionary key value pair. Setting this value updates the user's settings file. For example, to set the file path to the Application that will be used to open MusicXML files, use the 'musicxmlPath' key. 


    >>> #_DOCS_SHOW us['musicxmlPath'] = '/Applications/Finale Reader.app'
    >>> #_DOCS_SHOW us['musicxmlPath']
    u'/Applications/Finale Reader.app'


    Note that the 'localCorpusPath' setting operates in a slightly different manner than other settings. Each time the 'localCorpusPath' setting is set, an additional local corpus file path is added to the list of local corpus paths (unless that path is already defined in the list of local corpus paths). To view all local corpus paths, access the 'localCorpusSettings' settings. This setting can also be used to set a complete list of file paths. 

    >>> #_DOCS_SHOW us['localCorpusPath'] = '~/Documents'
    >>> #_DOCS_SHOW us['localCorpusSettings']
    ['~/Documents']

    Alternatively, the environment.py module provides convenience functions for setting these settings: :func:`~music21.environment.keys`, :func:`~music21.environment.get`, and :func:`~music21.environment.set`.
    '''

    def __init__(self):
        # store environment as a private attribute
        self._environment = Environment()


    def restoreDefaults(self):
        '''Restore platform specific defaults. 
        '''
        # location specific, cannot test further
        self._environment.restoreDefaults()
        self._environment.write()

# this is no longer necessaary
#     def _updateAllEnvironments(self):
#         '''Iterate through all modules; find any that have environLocal, and replace with a new environment.
#         '''
#         from music21 import base # must update this one to get show to work
#         reload(sys)
#         for mStr, m in sys.modules.items():
#             if hasattr(m, 'environLocal'):
#                 #self._environment.printDebug(['reinstantiating Environment on %s' % m])
#                 m.environLocal = Environment()

    def __getitem__(self, key):
        '''Dictionary like getting. 
        '''
        # location specific, cannot test further
        return self._environment.__getitem__(key)


    def __setitem__(self, key, value):
        '''Dictionary-like setting. Changes are made and written to the user configuration file.

        >>> from music21 import *
        >>> us = environment.UserSettings()
        >>> us['musicxmlPath'] = 'asdfwerasdffasdfwer'
        Traceback (most recent call last):
        UserSettingsException: attempting to set a path that does not exist: asdfwerasdffasdfwer

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
            value = os.path.expanduser(value)
            if not os.path.exists(value):
                raise UserSettingsException('attempting to set a path that does not exist: %s' % value)
        # when setting a local corpus setting, if not a list, append
        elif key in ['localCorpusSettings']:
            if not common.isListLike(value):
                raise UserSettingsException('localCorpusSettings must be provided as a list.')
        # location specific, cannot test further
        self._environment.__setitem__(key, value)
        self._environment.write()
        #self._updateAllEnvironments()

    def __repr__(self):
        '''Return a string representation. 

        >>> from music21 import *
        >>> us = environment.UserSettings()
        >>> post = repr(us) # location specific, cannot test
        '''
        return self._environment.__repr__()

    def __str__(self):
        '''Return a string representation. 

        >>> from music21 import *
        >>> us = environment.UserSettings()
        >>> post = repr(us) # location specific, cannot test
        '''
        return self._environment.__str__()

    def keys(self):
        '''Return the keys found in the user's :class:`~music21.environment.Environment` object. 
        '''
        return self._environment.getRefKeys() + ['localCorpusPath']

    def getSettingsPath(self):
        '''Return the path to the platform specific settings file.
        '''
        return self._environment.getSettingsPath()

    def create(self):
        '''If a environment configuration file does not exist, create one based on the default settings.
        '''
        if not os.path.exists(self._environment.getSettingsPath()):
            self._environment.write()
        else:
            raise UserSettingsException('an environment configuration file already exists; simply set values to modify.')

    def delete(self):
        '''Permanently remove the user configuration file. 
        '''
        if os.path.exists(self._environment.getSettingsPath()):
            os.remove(self._environment.getSettingsPath())
        else:
            raise UserSettingsException('an environment configuration file does not exist.')


#-------------------------------------------------------------------------------
# convenience routines for accessing UserSettings. 

def keys():
    '''Return all valid UserSettings keys.
    '''
    us = UserSettings()
    return us.keys()


def set(key, value):
    '''Directly set a single UserSettings key, by providing a key and the appropriate value. This will create a user settings file if necessary.

    >>> from music21 import *
    >>> environment.keys()
    ['lilypondBackend', 'pdfPath', 'lilypondVersion', 'graphicsPath', 'warnings', 'showFormat', 'localCorpusSettings', 'vectorPath', 'writeFormat', 'lilypondPath', 'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'autoDownload', 'midiPath', 'localCorpusPath']
    >>> environment.set('wer', 'asdf')
    Traceback (most recent call last):
    EnvironmentException: no preference: wer
    >>> #_DOCS_SHOW environment.set('musicxmlPath', '/Applications/Finale Reader.app')
    '''
    us = UserSettings()
    try:
        us.create() # no problem if this does not exist
    except UserSettingsException:
        pass # this means it already exists
    us[key] = value # this may raise an exception

def get(key):
    '''Return the current setting of a UserSettings key. This will create a user settings file if necessary.

    >>> from music21 import *
    >>> environment.keys()
    ['lilypondBackend', 'pdfPath', 'lilypondVersion', 'graphicsPath', 'warnings', 'showFormat', 'localCorpusSettings', 'vectorPath', 'writeFormat', 'lilypondPath', 'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'autoDownload', 'midiPath', 'localCorpusPath']
    >>> #_DOCS_SHOW environment.get('musicxmlPath')
    '/Applications/Finale Reader.app'
    '''
    us = UserSettings()
    return us[key]
    

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    '''Unit tests
    '''

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
    
        self.assertEqual("""<?xml version="1.0" encoding="utf-8"?>
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
""", storage.xmlStr())


    def testToSettings(self):

        env = Environment(forcePlatform='darwin')
        match = _environStorage['instance']._toSettings(
            _environStorage['instance']._ref).xmlStr()
        self.assertEqual("""<?xml version="1.0" encoding="utf-8"?>
<settings>
  <preference name="lilypondBackend" value="ps"/>
  <preference name="pdfPath" value="/Applications/Preview.app"/>
  <preference name="lilypondVersion"/>
  <preference name="graphicsPath" value="/Applications/Preview.app"/>
  <preference name="warnings" value="1"/>
  <preference name="showFormat" value="musicxml"/>
  <localCorpusSettings/>
  <preference name="vectorPath" value="/Applications/Preview.app"/>
  <preference name="writeFormat" value="musicxml"/>
  <preference name="lilypondPath" value="/Applications/Lilypond.app/Contents/Resources/bin/lilypond"/>
  <preference name="directoryScratch"/>
  <preference name="lilypondFormat" value="pdf"/>
  <preference name="debug" value="0"/>
  <preference name="musicxmlPath" value="/Applications/Finale Reader.app"/>
  <preference name="autoDownload" value="ask"/>
  <preference name="midiPath" value="/Applications/QuickTime Player.app"/>
</settings>
""",  match)

        # try adding some local corpus settings
        env['localCorpusSettings'] = ['a', 'b', 'c']
        match = _environStorage['instance']._toSettings(
            _environStorage['instance']._ref).xmlStr()
        self.assertEqual("""<?xml version="1.0" encoding="utf-8"?>
<settings>
  <preference name="lilypondBackend" value="ps"/>
  <preference name="pdfPath" value="/Applications/Preview.app"/>
  <preference name="lilypondVersion"/>
  <preference name="graphicsPath" value="/Applications/Preview.app"/>
  <preference name="warnings" value="1"/>
  <preference name="showFormat" value="musicxml"/>
  <localCorpusSettings>
    <localCorpusPath>a</localCorpusPath>
    <localCorpusPath>b</localCorpusPath>
    <localCorpusPath>c</localCorpusPath>
  </localCorpusSettings>
  <preference name="vectorPath" value="/Applications/Preview.app"/>
  <preference name="writeFormat" value="musicxml"/>
  <preference name="lilypondPath" value="/Applications/Lilypond.app/Contents/Resources/bin/lilypond"/>
  <preference name="directoryScratch"/>
  <preference name="lilypondFormat" value="pdf"/>
  <preference name="debug" value="0"/>
  <preference name="musicxmlPath" value="/Applications/Finale Reader.app"/>
  <preference name="autoDownload" value="ask"/>
  <preference name="midiPath" value="/Applications/QuickTime Player.app"/>
</settings>
""",  match)


    def testFromSettings(self):

        env = Environment(forcePlatform='darwin')

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
        self.assertEqual("""<?xml version="1.0" encoding="utf-8"?>
<settings>
  <preference name="lilypondBackend" value="ps"/>
  <preference name="pdfPath" value="/Applications/Preview.app"/>
  <preference name="lilypondVersion"/>
  <preference name="graphicsPath" value="/Applications/Preview.app"/>
  <preference name="warnings" value="1"/>
  <preference name="showFormat" value="musicxml"/>
  <localCorpusSettings>
    <localCorpusPath>x</localCorpusPath>
    <localCorpusPath>y</localCorpusPath>
    <localCorpusPath>z</localCorpusPath>
  </localCorpusSettings>
  <preference name="vectorPath" value="/Applications/Preview.app"/>
  <preference name="writeFormat" value="musicxml"/>
  <preference name="lilypondPath" value="/Applications/Lilypond.app/Contents/Resources/bin/lilypond"/>
  <preference name="directoryScratch"/>
  <preference name="lilypondFormat" value="pdf"/>
  <preference name="debug" value="0"/>
  <preference name="musicxmlPath" value="/Applications/Finale Reader.app"/>
  <preference name="autoDownload" value="ask"/>
  <preference name="midiPath" value="w"/>
</settings>
""",  match)


    def testEnvironmentA(self):
        env = Environment(forcePlatform='darwin')

        # setting the local corpus path pref is like adding a path
        env['localCorpusPath'] = 'a'
        self.assertEqual(env['localCorpusSettings'], ['a'])

        env['localCorpusPath'] = 'b'
        self.assertEqual(env['localCorpusSettings'], ['a', 'b'])


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [UserSettings, Environment, Preference]

if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

