"""The jsonpickle.tags module provides the custom tags
used for pickling and unpickling Python objects.

These tags are keys into the flattened dictionaries
created by the Pickler class.  The Unpickler uses
these custom key names to identify dictionaries
that need to be specially handled.
"""
from jsonpickle.compat import set

ID = 'py/id'
OBJECT = 'py/object'
TYPE = 'py/type'
REPR = 'py/repr'
REF = 'py/ref'
TUPLE = 'py/tuple'
SET = 'py/set'
SEQ = 'py/seq'
STATE = 'py/state'
JSON_KEY = 'json://'

# All reserved tag names
RESERVED = set([OBJECT, TYPE, REPR, REF, TUPLE, SET, SEQ, STATE])
