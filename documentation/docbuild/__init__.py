# -*- coding: utf-8 -*-
__all__ = ['documenters', 'iterators', 'writers']

import sys
if sys.version_info[0] < 3:
    raise Exception("Building documentation requires Python 3.")

from . import documenters # @UnresolvedImport
from . import iterators # @UnresolvedImport
from . import writers # @UnresolvedImport

