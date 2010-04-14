.. _environment:



Setting up and Configuring Environment
======================================

Music21 features an environment configuration system. This permits the user to configure and customize settings used by many Music21 objects.

Environment configuration is particularly useful in setting default third-party applications for handling Music21 output in different media formats (e.g. MusicXML, lilypond, graphics files).

For complete information on the Environment object, see :mod:`~music21.environment`.


Creating and Configuring an Environment
----------------------------------------

Environment files are not created by default. To create an environment file, import environment form Music21 and create an :class:`~music21.environment.Environment` object. Then, call the  :meth:`~music21.environment.Environment.write` method to create an XML environment file.

    >>> from music21 import environment
    >>> a = environment.Environment()
    >>> a.write()

After creating an environment file, this XML preference file can be edited directly by the user. To find where the XML file is written, the :meth:`~music21.environment.Environment.getSettingsPath` method can be called. This path will be different depending on your platform and user name. 

    >>> a.getSettingsPath()
    '/Users/ariza/.music21rc'

Settings can be edited in the XML file or through the object interface. The Environment object acts as a Python dictionary. To view the names of user-configurable parameters, call the keys() method.

    >>> a.keys()
    ['lilypondBackend', 'lilypondVersion', 'graphicsPath', 'lilypondPath', 
    'directoryScratch', 'lilypondFormat', 'debug', 'musicxmlPath', 'midiPath']

To set a preference, a key value pair of the Environment object can be set. For example, to set the Music21 scratch directory, the 'directoryScratch' key can be set to a file path of the users choice. Note that changes are not permanent until the object's :meth:`~music21.environment.Environment.write` method is called.

    >>> a['directoryScratch'] = '/_scratch'
    >>> a.write()


Note that Music21 objects may need to be reloaded, and/or the Python session restarted, to get changes made to the Environment object.




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




Important Tools that May Use Environment Settings
----------------------------------------------------

The following important functions and methods will make use of environment values and are often good to set.


`show()` Methods and 'directoryScratch', 'showFormat' and 'writeFormat'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The show method, inherited from :meth:`~music21.base.Music21Object.show`, will, depending on user settings, write a temporary file in a user specified format in a user-specified scratch directory. 

Setting the `showFormat` will set the default output format of all calls to `show()` methods. The behavior can be deviated from by providing an argument to `show()`.

Setting the `writeFormat` will set the default output format of all calls to `write()` methods. The behavior can be deviated from by providing an argument to `write()`.

Setting the `directoryScratch` will determine where the file is written. If this setting is not made, the file will be written in a system-specified scratch directory. While useful, such temporary files and directories mat be buried deeply in your file system.


`parseURL()` and `parseWork()` Functions and 'autoDownload'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`~music21.converter.parseURL` function, as well as the :func:`~music21.corpus.base.parseWork` function, offer the ability to download a files directly directly from the internet.

Users masy configure the 'autoDownload' environment setting to determine whether downloading is attempted automatically, without user prompt ('allow'), the user is asked first before attempting a download ('ask'), or downloading is prohibited ('deny')


