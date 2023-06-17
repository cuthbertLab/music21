# -*- coding: utf-8 -*-
'''
This file contains Music21's version number information.

As of v2.0.0, Music21 uses something close to the principles of Semantic Versioning, we'll
try very hard so that X.Y.Z have meanings about changes to the system.
Changes in X represent changes that will break old features.
New Y numbers add new features; Z -- bug fixes.  The X number change about once per year.

Differences with strict semantic versioning: I won't make 100% guarantees that we'll never
break anything without a change in the major number, esp. if the change affects a tiny
number of users or possibly none.  A new feature added in the previous Y release can be tweaked
or removed in the next few releases if the feature itself is marked beta.

Even numbered Ys will be beta releases. Zero Ys 2.0, 3.0, etc. are development releases: they
CAN change functionality until 2.1, 3.1, etc. is released.  This is against the semver standard,
but I don't want to have lots of 2.0.0-alpha2, etc., I'd rather call it 2.0.2, and tell users
to wait for 2.1.  Even numbered first decimal releases (e.g. 5.4) are also beta.


Q: Why is this here and not in music21/__init__.py?

A: Keeping the information here makes it available to package managers and others who
have not yet installed all of music21, by simply reading this file in and evaluating its contents.

Importantly, that means that Music21's setup system (currently Hatch)
*doesn't* need to import any part of Music21's code during the installation process.
Not importing any part
of Music21 makes installation cleaner, and also helps other software - like
package managers in various Linux distributions - work with Music21 without
complaint.


Thanks to Andrew Hankinson for suggesting this way of dealing with versions to begin with.


Changing Versions
==================

When it's time to update Music21's version, just change the numbers in the
tuple assigned to __version__ string and the __version_info__ tuple will be
updated along with it.

When changing, update the single test case in base.py.

Changing this number invalidates old pickles -- do it if the old pickles create a problem.
'''
from __future__ import annotations

__version__ = '9.1.0'

def get_version_tuple(vv):
    v = vv.split('.')
    last_v = v[-1]
    v[-1] = ''
    beta = ''
    in_patch = True
    for ch in last_v:
        if in_patch and ch.isdigit():
            v[-1] += ch
        else:
            in_patch = False
            beta += ch
    if beta:
        v.append(beta)
    return tuple(v)


__version_info__ = get_version_tuple(__version__)


del get_version_tuple
