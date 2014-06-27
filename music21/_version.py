'''
This file contains Music21's version number information.

Q: Why is this here and not in music21/__init__.py?

A: Keeping the information here makes it available to Music21's setup.py file
by simply reading this file in and evaluating its contents.

Importantly, that means that Music21's setup.py *doesn't* need to import any
part of Music21's code during the installation process.  Not importing any part
of Music21 makes installation cleaner, and also helps other software - like
package managers in various Linux distributions - work with Music21 without
complaint.

When it's time to update Music21's version, just change the numbers in the
tuple assigned to __version_info__, and the __version__ string will be
updated along with it.

When changing, update the single test case in base.py, and in freezeThaw.JSONFreezer.jsonPrint
and at the end of the two corpus/metadataCache .jsons
Changing invalidates old pickles
'''

__version_info__ = (1, 9, 3)
__version__ = '.'.join(str(x) for x in __version_info__)
