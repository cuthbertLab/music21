# -*- coding: utf-8 -*-
'''
Runs MultiprocessTest with all warnings including traceback...
'''
#
# https://stackoverflow.com/questions/22373927/get-traceback-of-warnings
import traceback
import warnings
import sys


def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
    log = file if hasattr(file, 'write') else sys.stderr
    if 'music21' in filename:
        # do not give stack trace for matplotlib PendingDeprecation, etc.
        traceback.print_stack(file=log)
    log.write(warnings.formatwarning(message, category, filename, lineno, line))


if __name__ == '__main__':
    warnings.showwarning = warn_with_traceback
    warnings.simplefilter("always")
    from music21.test import multiprocessTest
    multiprocessTest.mainPoolRunner()
