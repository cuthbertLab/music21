# -*- coding: utf-8 -*-

import sys

if sys.version > '3':
    from .cleaners import *
    from .documenters import *
    from .iterators import *
    from .writers import *    
else:
    from cleaners import *
    from documenters import *
    from iterators import *
    from writers import *

