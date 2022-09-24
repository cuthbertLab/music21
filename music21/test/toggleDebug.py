# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         test.toggleDebug.py
# Purpose:      Changes debug on if off, off if on...
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Run from command line to toggle debug status.
'''
from __future__ import annotations

import music21.environment


def toggleDebug():
    '''
    Changes debug status from 0 to 1 or 1 to 0.  Reload environment after calling.
    '''
    e = music21.environment.UserSettings()
    if e['debug'] == 1:
        print('debug was ' + str(e['debug']) + '; switching to 0')
        e['debug'] = 0
    else:
        print('debug was ' + str(e['debug']) + '; switching to 1')
        e['debug'] = 1


if __name__ == '__main__':
    toggleDebug()
