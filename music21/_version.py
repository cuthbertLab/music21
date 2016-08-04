# -*- coding: utf-8 -*-
'''
This file contains Music21's version number information.

As of v.2.0.0, Music21 uses something close to the principles of Semantic Versioning, we'll
try very hard so that X.Y.Z have meanings about changes to the system.  
Changes in X represent changes that will break old features.
New Y numbers add new features; Z -- bug fixes.  This means that the X number
will change more often than before.  

Differences with strict semantic versioning: I won't make 100% guarantees that we'll never
break anything without a change in the major number, esp. if the change affects a tiny
number of users or possibly none.  A new feature added in the previous Y release can be tweaked
or removed in the next few releases if the feature itself is marked beta.

Even numbered Ys will be beta releases. Zero Ys 2.0, 3.0, etc. are development releases: they
CAN change functionality until 2.1, 3.1, etc. is released.  This is against the semver standard,
but I don't want to have lots of 2.0.0-alpha2, etc., I'd rather call it 2.0.2, and tell users
to wait for 2.1.


Q: Why is this here and not in music21/__init__.py?

A: Keeping the information here makes it available to Music21's setup.py file
by simply reading this file in and evaluating its contents.

Importantly, that means that Music21's setup.py *doesn't* need to import any
part of Music21's code during the installation process.  Not importing any part
of Music21 makes installation cleaner, and also helps other software - like
package managers in various Linux distributions - work with Music21 without
complaint.

Changing Versions
==================

When it's time to update Music21's version, just change the numbers in the
tuple assigned to __version_info__, and the __version__ string will be
updated along with it.

When changing, update the single test case in base.py, and in freezeThaw.JSONFreezer.jsonPrint
(on a major version change). If you dare edit a 28MB file, chang it 
at the end of the two corpus/metadataCache .jsons, but only a problem there sometimes.

Changing this number invalidates old pickles -- do it if the old pickles create a problem.
'''

__version_info__ = (3, 1, 0)
__version__ = '.'.join(str(x) for x in __version_info__)

