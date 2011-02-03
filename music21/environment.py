#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         environment.py
# Purpose:      Storage for user environment settings and defaults
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
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
from music21 import node


_MOD = 'environment.py'


#-------------------------------------------------------------------------------
class EnvironmentException(Exception):
    pass

class UserSettingsException(Exception):
    pass


#-------------------------------------------------------------------------------
class Settings(node.NodeList):
    '''
    '''
    def __init__(self):
        '''
        >>> a = Settings()
        '''
        node.NodeList.__init__(self)
        self._tag = 'settings' # assumed for now
        self.componentList = [] # list of Part objects

    def _getComponents(self):
        return self.componentList


class Preference(node.Node):
    '''
    '''
    def __init__(self):
        '''
        >>> a = Preference()
        '''
        node.Node.__init__(self)
        self._tag = 'preference' # assumed for now
        # attributes
        self._attr['name'] = None
        self._attr['value'] = None



#-------------------------------------------------------------------------------
class SettingsHandler(xml.sax.ContentHandler):
    '''
    >>> a = SettingsHandler()
    '''
    def __init__(self, tagLib=None):
        self.storage = Settings()        

    def startElement(self, name, attrs):
        if name == 'preference':        
            slot = Preference()
            slot.loadAttrs(attrs)
            self.storage.append(slot)

    def getSettings(self):
        return self.storage


#-------------------------------------------------------------------------------
class Environment(object):
    '''The Environment object stores user preferences as dictionary-like object. Additionally, the Environment object provides convenience methods to music21 modules for getting temporary files, launching files with external applications, and printing debug and warning messages.

    Generally, each module creates a single, module-level instance of Environment, passing the module's name during creation. 

    For more a user-level interface for creating and editing settings, see the  :class:`~music21.environment.UserSettings` object. 
    '''

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['read', 'write', 'getSettingsPath']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'modNameParent': 'A string representation of the module that contains this Environment instance.',
    'ref': 'The Python dictionary used to store all internal settings.',
    }

    def __init__(self, modName=None):
        '''Create an instance of this object. A modName argument can be provided for use in printDebug() calls. 

        >>> a = Environment()
        >>> post = a['writeFormat']
        '''
        self.ref = {}
        self.loadDefaults() # defines all valid keys in ref
        # read will only right over values if set in field
        self.read() # load a stored file if available
        # store the name of the module that is using this object
        # this is used for printing debug information
        self.modNameParent = modName


    def loadDefaults(self):
        '''Load defaults. All keys are derived from these defaults.
        '''
        self.ref['directoryScratch'] = None # path to a directory for temporary files
        self.ref['lilypondPath'] = None # path to lilypond
        self.ref['lilypondVersion'] = None # version of lilypond
        self.ref['lilypondFormat'] = 'pdf' 
        self.ref['lilypondBackend'] = 'ps' 
        # path to a MusicXML reader: default, will find "Finale Reader"
        self.ref['musicxmlPath'] = None 
        self.ref['midiPath'] = None # path to a midi reader
        self.ref['graphicsPath'] = None # path to a graphics viewer
        self.ref['pdfPath'] = None # path to a pdf viewer
        self.ref['showFormat'] = 'musicxml' 
        self.ref['writeFormat'] = 'musicxml' 
        self.ref['autoDownload'] = 'ask' 
        self.ref['debug'] = 0
        # printing of missing import warnings
        self.ref['warnings'] = 1 # default/non-zero is on

        platform = common.getPlatform()

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
            # with 2011 version forward default finale reader location is now:
            ('musicxmlPath', '/Applications/Finale Reader.app'),
            ('graphicsPath', '/Applications/Preview.app'),
            ('pdfPath', '/Applications/Preview.app'),
            ('midiPath', '/Applications/QuickTime Player.app'),

                ]:
                self.__setitem__(name, value) # use for key checking


    def restoreDefaults(self):
        '''Restore only defaults for all parameters. Useful for testing. 

        >>> from music21 import *
        >>> a = music21.environment.Environment()
        >>> a['debug'] = 1
        >>> a.restoreDefaults()
        >>> a['debug']
        0
        '''
        self.printDebug(['restoring Environment defaults'])
        self.ref = {}
        self.loadDefaults() # defines all valid keys in ref


    def __getitem__(self, key):
        '''Dictionary like getting. 
        '''
        # could read file here to update from disk
        # could store last update tim and look of file is more recent
        # how, only doing read once is a bit more conservative
        #self.read()
        if key not in self.ref.keys():
            raise EnvironmentException('no preference: %s' % key)
        value = self.ref[key]
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
        '''Dictionary-like setting. Changes are made only to local dictionary.
        Must call write() to make permanent

        >>> from music21 import *
        >>> a = music21.environment.Environment()
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
        '''
        #saxutils.escape # used for escaping strings going to xml
        # with unicode encoding
        # http://www.xml.com/pub/a/2002/11/13/py-xml.html?page=2
        # saxutils.escape(msg).encode('UTF-8')

        if key not in self.ref.keys():
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
        else: # temporarily not validating other preferences
            valid = True

        if not valid:
            raise EnvironmentException('%s is not an acceptable value for preference: %s' % (value, key))

        if common.isStr(value):
            value = xml.sax.saxutils.escape(value).encode('UTF-8')
        self.ref[key] = value

    def __repr__(self):
        return '<Environment>'

    def __str__(self):
        return repr(self.ref)

    def keys(self):
        return self.ref.keys()

    #---------------------------------------------------------------------------
    def getSettingsPath(self):
        '''Return the path to the platform specific settings file.
        '''
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
            dir = os.environ['HOME']
            return os.path.join(dir, '.music21rc')

        # darwin specific option
        # os.path.join(os.environ['HOME'], 'Library',)

     

    #---------------------------------------------------------------------------
    def read(self, fp=None):
        '''Load an XML preference file if and only if the file is available and has been written in the past. This means that no preference file will ever be written unless manually done so. If no preference file exists, the method returns None.
        '''
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
        storage = h.getSettings()
        for slot in storage:
            name = slot.get('name')
            value = slot.get('value')
            if name not in self.ref.keys():
                self.printDebug(['a preference is defined that is longer used: %s' % name])
                continue
                # do not set, ignore for now
                #raise EnvironmentException('no such defined preference: %s' % name)
            else: # load up stored values, overwriting defaults
                self.ref[name] = value

    def write(self, fp=None):
        '''Write an XML preference file. This must be manually called to store any changes made to the object and access preferences later. If `fp` is None, the default storage location will be used.
        '''
        if fp == None:
            fp = self.getSettingsPath()

        # need to use __getitem__ here b/c need to covnert debug value
        # to an integer
        self.printDebug([_MOD, 'writing preference file', self.ref])

        dir, fn = os.path.split(fp)
        if fp == None or not os.path.exists(dir):
            raise EnvironmentException('bad file path: %s' % fp)

        storage = Settings()
        for key, item in self.ref.items():
            slot = Preference()
            slot.set('name', key)
            slot.set('value', item)
            storage.append(slot)

        f = open(fp, 'w')
        f.write(storage.xmlStr())
        f.close()

    #---------------------------------------------------------------------------
    # utility methods for commonly needed OS services

    def getDefaultRootTempDir(self):
        '''Use the Python tempfile.gettempdir() to get the system specified temporary directory, and try to add a new 'music21' directory, and then return this directory.

        This method is only called if the no scratch directory preference has been set. 

        If not able to create a 'music21' directory, the standard default is returned.
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
            except OSError: # cannot make the directory
                dstDir = tempfile.gettempdir()
            self.printDebug([_MOD, 'using temporary directory:', dstDir])
            return dstDir

    def getRootTempDir(self):
        '''Return a directory for writing temporary files. This does not create a new directory for each use, but either uses the user-set preference or gets the system-provided directory (with a music21 subdirectory, if possible).
        '''
        if self.ref['directoryScratch'] == None:
            return self.getDefaultRootTempDir()
        # check that the user-specified directory exists
        elif not os.path.exists(self.ref['directoryScratch']):    
            raise EnvironmentException('user-specified scratch directory (%s) does not exist; remove preference file or reset Environment' % self.ref['directoryScratch'])
        else:
            return self.ref['directoryScratch']

    def getTempFile(self, suffix=''):
        '''Return a file path to a temporary file with the specified suffix
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

        self.printDebug([_MOD, 'temporary file:', fp])
        return fp

    def launch(self, fmt, fp, options='', app=None):
        '''
        Opens a file with an either default or user-specified applications.
        
        OMIT_FROM_DOCS

        Optionally, can add additional command to erase files, if necessary 
        Erase could be called from os or command-line arguments after opening
        the file and then a short time delay.

        TODO: Move showImageDirectfrom lilyString.py ; add MIDI
        TODO: Switch to module subprocess to prevent hanging.
        '''
        # see common.fileExtensions for format names 
        format, ext = common.findFormat(fmt)
        if format == 'lilypond':
            fpApp = self.ref['lilypondPath']
        elif format in ['png', 'jpeg']:
            fpApp = self.ref['graphicsPath']   
        elif format in ['pdf']:
            fpApp = self.ref['pdfPath']   
        elif format == 'musicxml':
            fpApp = self.ref['musicxmlPath']   
        elif format == 'midi':
            fpApp = self.ref['midiPath']   
        else:
            fpApp = None

        # substitute provided app
        if app != None:
            fpApp = app 

        platform = common.getPlatform()
        if fpApp is None and platform != 'win':
            raise EnvironmentException("Cannot find an application for format %s, specify this in your environment" % fmt)
        
        if platform == 'win' and fpApp is None:
            # no need to specify application here: windows starts the program based on the file extension
            cmd = 'start %s' % (fp)
        elif platform == 'win':  # note extra set of quotes!
            cmd = '""%s" %s "%s""' % (fpApp, options, fp)
        elif platform == 'darwin':
            cmd = 'open -a"%s" %s %s' % (fpApp, options, fp)
        elif platform == 'nix':
            cmd = '%s %s %s' % (fpApp, options, fp)
        os.system(cmd)


    def printDebug(self, msg, statusLevel=common.DEBUG_USER, format=None):
        '''Format one or more data elements into string, and print it 
        to stderr. The first arg can be a list of string; lists are 
        concatenated with common.formatStr(). 
        '''
        if not common.isNum(statusLevel):
            raise EnvironmentException('bad statusLevel argument given: %s' % statusLevel)
        if self.__getitem__('debug') >= statusLevel:
            if common.isStr(msg):
                msg = [msg] # make into a list
            if msg[0] != self.modNameParent and self.modNameParent != None:
                msg = [self.modNameParent + ':'] + msg
            # pass list to common.formatStr
            msg = common.formatStr(*msg, format=format)
            sys.stderr.write(msg)
    

    def warn(self, msg, header=None):
        '''To print a warning to the user, send a list of strings to this
        method. 
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
    ['lilypondBackend', 'pdfPath', 'lilypondVersion', 'graphicsPath', 'warnings', 'showFormat', 'writeFormat', 'lilypondPath', 'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'autoDownload', 'midiPath']


    Third, after finding the desired setting, supply the new value as a Python dictionary key value pair. Setting this value updates the user's settings file. For example, to set the file path to the Application that will be used to open MusicXML files, use the 'musicxmlPath' key. 


    >>> #_DOCS_SHOW us['musicxmlPath'] = '/Applications/Finale Reader.app'
    >>> #_DOCS_SHOW us['musicxmlPath']
    u'/Applications/Finale Reader.app'
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

    def __getitem__(self, key):
        '''Dictionary like getting. 
        '''
        # location specific, cannot test further
        return self._environment.__getitem__(key)


    def __setitem__(self, key, value):
        '''Dictionary-like setting. Changes are made and written to the user configuration file.
        '''
        # location specific, cannot test further
        self._environment.__setitem__(key, value)
        self._environment.write()


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
        return self._environment.ref.keys()

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


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [UserSettings, Environment, Preference]

if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

