# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         braille/runAllBrailleTests.py
# Purpose:      Test runner for Bo-Cheng Jhan and others who would prefer
#               to debug braille output with a minimum of screen reader output
# Author:       Michael Scott Cuthbert
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
A Python 3 only module that runs all the braille Tests and no other tests.

Does not run the doctests, unfortunately.  TODO: use mainTest somehow...

This module produces a minimum of output which is most helpful
to people who are programming music21 on a screen reader.

For Bo-Cheng Jhan with my thanks.
'''
import re
import subprocess
import sys

from music21 import braille

current_executable = sys.executable

def runTest():
    savedStderr = sys.stderr
    totalTests = 0
    hadError = False
    for modName in braille.__all__:
        completion = subprocess.run(
            [current_executable, '-m', f'music21.braille.{modName}'],
            check=False,
            capture_output=True,
        )
        for errOutput in completion.stderr, completion.stdout:
            if errOutput is None:
                continue
            for thisLine in errOutput.decode('utf-8').splitlines():
                if not thisLine:
                    continue
                if re.search(r'found in sys.modules after import', thisLine):
                    continue
                if re.search(r'warn\(RuntimeWarning\(msg\)\)', thisLine):
                    continue
                if re.match(r'^\.*$', thisLine):
                    # all dots or blank line
                    continue
                if re.match(r'^-+$', thisLine):
                    # separator
                    continue
                if thisLine == 'OK':
                    continue
                numTests = re.match(r'^Ran (\d+) tests? in ', thisLine)
                if numTests:
                    totalTests += int(numTests.group(1))
                    continue
                hadError = True
                print(thisLine)
    print('Total tests: ', totalTests)
    if hadError:
        print('ERRORS FOUND')
    else:
        print('All good!')

    sys.stderr = savedStderr


if __name__ == '__main__':
    runTest()
