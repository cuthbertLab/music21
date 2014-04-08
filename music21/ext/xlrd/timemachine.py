# -*- coding: cp1252 -*-

##
# <p>Copyright © 2006 Stephen John Machin, Lingfo Pty Ltd</p>
# <p>This module is part of the xlrd package, which is released under a BSD-style licence.</p>
##

# timemachine.py -- adaptation for earlier Pythons e.g. 2.1
# usage: from timemachine import *

import sys

python_version = sys.version_info[:2] # e.g. version 2.4 -> (2, 4)

CAN_PICKLE_ARRAY = True
CAN_SUBCLASS_BUILTIN = True 

if sys.version.startswith("IronPython"):
    array_array = None
else:
    from array import array as array_array


def int_floor_div(x, y):
    return divmod(x, y)[0]

def intbool(x):
    if x:
        return 1
    return 0

