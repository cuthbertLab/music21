# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:          installer.py
# Purpose:       install and configure
#
# Authors:       Christopher Ariza
#                Michael Scott Cuthbert
#
# Copyright:     (c) 2009-2016 Michael Scott Cuthbert and the music21 Project
# License:       BSD, see license.txt
# ------------------------------------------------------------------------------

import os, sys


def main():
    sys.stdout.write('Starting the music21 Configuration Assistant.\n'
                     + 'Module loading could take a few moments, please wait...')
    sys.stdout.flush()

    if 'music21' in os.listdir(os.getcwd()):
        p1 = os.path.join(os.getcwd(), 'music21')
        if p1 not in sys.path:
            sys.path.append(p1)
        if 'music21' in os.listdir(p1):
            p2 = os.path.join(p1, 'music21')
            if p2 not in sys.path:
                sys.path.append(os.path.join(p2, 'music21'))

    run = False
    try:
        from music21 import configure
        run = True
    except ImportError:
        pass


    # need to be sure that we have the configure.py file found in the right place

    if run:
        ca = configure.ConfigurationAssistant()
        ca.run()

if __name__ == '__main__':
    main()
