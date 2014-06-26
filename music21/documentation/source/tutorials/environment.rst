.. _environment:


Configuring Environment Settings
================================


Music21 features an environment configuration system which lets users configure
and customize settings.  These settings will be saved so that the next time the
user starts Python, the settings will still work.

Environment configuration is particularly useful for setting default
third-party applications (necessary for handling Music21 output in different
media formats such as MusicXML, Lilypond, and graphics files) and for setting a
default scratch directory (for writing output without providing explitic file
paths).

Environment configuration can be handled with two objects. The
:class:`~music21.environment.Environment` object provides lower-level access
and control, as well as a numerous utiity methods for music21 modules. The
:class:`~music21.environment.UserSettings` object is a convenience class for
users to quickly set and check settings, and is reccommended for general usage.
For complete information on the Environment and UserSettings objects, see
:mod:`~music21.environment`.


Creating and Configuring the UserSettings Object
------------------------------------------------

Environment configuration files are not created by default. To create an
environment configuration file, import environment form Music21 and create an
:class:`~music21.environment.UserSettings` object. Then, call the
:meth:`~music21.environment.UserSettings.create` method to create an XML
environment file.

::

    >>> from music21 import *
    >>> us = environment.UserSettings()
    >>> us.create()   # doctest: +SKIP

After creating an environment file, the resulting XML preference file can be
edited directly by the user. To find where the XML file is written, the
:meth:`~music21.environment.UserSettings.getSettingsPath` method can be called.
This path will be different depending on your platform and/or user name. 

::

    >>> us.getSettingsPath() # doctest: +SKIP
    '/Users/ariza/.music21rc'

Settings can be edited directly in the XML file or through the UserSettings
object interface. The UserSettings object acts as a Python dictionary. To view
the names of user-configurable parameters, call the keys() method.

::

    >>> for key in sorted(us.keys()):
    ...     key
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

To set and write a preference, a key and value pair must be provided using
Python dictionary-like syntax. For example, to set the Music21 scratch
directory, the 'directoryScratch' key can be set to a file path of the user's
choice. Changes are made immediately to the environment configuration file. To
see the current setting, the value can be accesed by key.

::

    >>> us['directoryScratch'] = '/_scratch'  # doctest: +SKIP
    >>> us['directoryScratch']  # doctest: +SKIP
    '/_scratch'

Note that Music21 objects may need to be reloaded, and/or the Python session
restarted, to have changes made to the UserSettings object take effect.


Location of Environment Configuration Files
-------------------------------------------

Environment configuration files are stored in platform-specific locations. 

On Linux and MacOS computers, the configuration file is stored as the file
.music21rc, located in the user's home directory. 

On Windows computers the configuration file is generally located in the
Application Data directory as the file 'music21-settings.xml'. In some cases
the XML settings file may be stored in the user directory. 

The path to the environment settings file can always be found with the
:meth:`~music21.environment.UserSettings.getSettingsPath` method.

::

    >>> from music21 import *
    >>> us = environment.UserSettings()
    >>> us.getSettingsPath()   # doctest: +SKIP
    '/Users/ariza/.music21rc'

To permanently delete the environment configuration file, call the
:meth:`~music21.environment.UserSettings.delete` method.

::

    >>> us = environment.UserSettings()
    >>> us.delete()    # doctest: +SKIP


Important Tools that May Use Environment Settings
-------------------------------------------------

The following important functions and methods will make use of environment
configuration file and are important to properly configure.

`show()` Methods and 'directoryScratch', 'showFormat' and 'writeFormat'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The show method, inherited from :meth:`~music21.base.Music21Object.show`, will,
depending on user settings, write a temporary file in a user specified format
in a user-specified scratch directory. 

Setting the `showFormat` key will set the default output format of all calls to
`show()` methods. The behavior can be deviated from by providing an argument to
`show()`.

Setting the `writeFormat` key will set the default output format of all calls
to `write()` methods. The behavior can be deviated from by providing an
argument to `write()`.

Setting the `directoryScratch` key will determine where the file is written. If
this setting is not made, the file will be written in a system-specified
scratch directory. While useful, such temporary files and directories may be
buried deeply in your file system.

`parseURL()` and `parse()` Functions and 'autoDownload'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`~music21.converter.parseURL` function, as well as the
:func:`~music21.corpus.parse` function, offer the ability to download a files
directly directly from the internet.

Users may configure the 'autoDownload' key to determine whether downloading is
attempted automatically without prompting the user ('allow'), whether the user
is asked first before attempting a download ('ask'), or whether downloading is
prohibited ('deny').
