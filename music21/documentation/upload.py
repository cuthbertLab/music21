# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         upload.py
# Purpose:      music21 documentation upload utility
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2009-2010, 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
#pylint: disable=line-too-long
'''
if you get a 'ssh_askpass' not found error, create this file in 
/usr/libexec/ssh-askpass and sudo chmod +x it afterwards:

..raw::
    #!/bin/bash
    # Script: ssh-askpass
    # Author: Mark Carver
    # Created: 2011-09-14
    # Copyright (c) 2011 Beyond Eden Development, LLC. All rights reserved.
    
    # A ssh-askpass command for Mac OS X
    # Based from author: Joseph Mocker, Sun Microsystems
    # http://blogs.oracle.com/mock/entry/and_now_chicken_of_the
    # To use this script:
    #   Install this script running INSTALL as root
    #
    # If you plan on manually installing this script, please note that you will have
    # to set the following variable for SSH to recognize where the script is located:
    #   export SSH_ASKPASS="/path/to/ssh-askpass"
    TITLE="${SSH_ASKPASS_TITLE:-SSH}";
    TEXT="$(whoami)'s password:";
    IFS=$(printf "\n");
    CODE=("on GetCurrentApp()");
    CODE=(${CODE[*]} "tell application \"System Events\" to get short name of first process whose frontmost is true");
    CODE=(${CODE[*]} "end GetCurrentApp");
    CODE=(${CODE[*]} "tell application GetCurrentApp()");
    CODE=(${CODE[*]} "activate");
    CODE=(${CODE[*]} "display dialog \"${@:-$TEXT}\" default answer \"\" with title \"${TITLE}\" with icon caution with hidden answer");
    CODE=(${CODE[*]} "text returned of result");
    CODE=(${CODE[*]} "end tell");
    SCRIPT="/usr/bin/osascript"
    for LINE in ${CODE[*]}; do
    SCRIPT="${SCRIPT} -e $(printf "%q" "${LINE}")";
    done;
    eval "${SCRIPT}";


Otherwise just contact MSC...
'''    

import getpass, os


def getDirBuildHtml():
    '''Return the html directory
    '''
    from music21 import common
    cwdir = common.getSourceFilePath()
    parentDir = os.path.dirname(cwdir)
    dirBuild = os.path.join(parentDir, 'music21', 'documentation', 'build')
    dirBuildHtml = os.path.join(dirBuild, 'html')
    return dirBuildHtml

if __name__ == '__main__':
    
    # this needs to be on level higher then the level of the source
    #DST_MIT = 'athena.dialup.mit.edu:/afs/athena.mit.edu/org/m/music21/doc/'
    remoteHost = 'athena.dialup.mit.edu'
    remoteDir = '/afs/athena.mit.edu/org/m/music21/doc/'
    #tar czpf - -C build/html/ . | ssh cuthbert@linux.mit.edu "tar xzpf - -C /afs/athena.mit.edu/org/m/music21/doc/"
    
    user = getpass.getpass('provide user name : ')
    
    
    src = getDirBuildHtml()
    # -r flag makes this recursive
    cmdStr = 'tar czpf - -C %s . | ssh %s@%s "tar xzpf - -C %s"' % (src, user, remoteHost, remoteDir)
    #cmdStr = 'scp -r "%s" %s@%s' % (src + "/*", user, DST_MIT)
    print(cmdStr)
    
    os.system(cmdStr)
    
    
