




Setting up and Configuring Environment
======================================


Music21 features and optional environment configuration system. This permits the user to configure settings used by all Music21 objects.

Environment configuration is particularly useful in setting default third-party application for handling Music21 output in different media formats (e.g. MusicXML, lilypond, graphics files).




Creating and Configuring an Environment
----------------------------------------

Environment files are not created by default. To create an environment file, import environment form Music21 and create an Environment object. Then, call the  write() method to create an XML environment file.

    >>> from music21 import environment
    >>> a = environment.Environment()
    >>> a.write()

After creating an environment file, this XML preference file can be edited directly by the user. To find where the XML file is written, the getSettingsPath() method can be called. This path will be different depending on your platform and user name. 

    >>> a.getSettingsPath()
    '/Users/ariza/.music21rc'

Settings can be edited in the XML file or through the object interface. The Environment object acts as a Python dictionary. To view the names of user-configurable parameters, call the keys() method.

    >>> a.keys()
    ['lilypondBackend', 'lilypondVersion', 'graphicsPath', 'lilypondPath', 
    'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'midiPath']

To set a preference, a key value pair of the Environment object can be set. For example, to set the Music21 scratch directory, the 'directoryScratch' key can be set to a file path of the users choice. Note that changes are not permanent until the object's write() method is called.

    >>> a['directoryScratch'] = '/_scratch'
    >>> a.write()


Note that Music21 objects may need to be reloaded, and/or the Python session restarted, to get chagnes made to the Environment object.





Location of Environment Files
----------------------------------------

Environment files are stored in platform-specific locations. 

On Linux and MacOS computers, XML settings are stored as the file .music21rc, located in the user's home directory. 

On Windows computers the XML settings file is generally located in the Application Data directory as the file 'music21-settings.xml'. In some cases the XML settings file may be stored in the user directory. 


The path to the environment settings file can always be found with the getSettingsPath() method.

    >>> from music21 import environment
    >>> a = environment.Environment()
    >>> a.getSettingsPath()
    '/Users/ariza/.music21rc'

