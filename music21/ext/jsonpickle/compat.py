import sys

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3
PY32 = PY3 and sys.version_info[1] == 2
PY2 = not PY3

try:
    bytes = bytes
except NameError:
    bytes = str

try:
    set = set
except NameError:
    from sets import Set as set
    set = set

try:
    unicode = unicode
except NameError:
    unicode = str

try:
    long = long
except NameError:
    long = int

try:
    unichr = unichr
except NameError:
    unichr = chr
