#!/usr/bin/env python
#   Copyright 2014 Sergio Oller <sergioller@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
This module implements map and starmap functions (see python standard
library to learn about them).

The implementations provided in this module allow providing additional
arguments to the mapped functions. Additionally they will initialize
the pool and close it automatically by default if possible.

Use these module in CPU intensive map functions.

Usage:
    import parmap
    # You want to do:
    y = [myfunction(x, argument1, argument2) for x in mylist]
    # In parallel:
    y = parmap.map(myfunction, mylist, argument1, argument2)

    # You want to do:
    z = [myfunction(x, y, argument1, argument2) for (x,y) in mylist]
    # In parallel:
    z = parmap.starmap(myfunction, mylist, argument1, argument2)

    # Yoy want to do:
    listx = [1, 2, 3, 4, 5, 6]
    listy = [2, 3, 4, 5, 6, 7]
    param = 3.14
    param2 = 42
    listz = []
    for x in listx:
        for y in listy:
            listz.append(myfunction(x, y, param1, param2))
    # In parallel:
    listz = parmap.starmap(myfunction, zip(listx,listy), param1, param2)

"""
# The original idea for this implementation was given by J.F. Sebastian
# at  http://stackoverflow.com/a/5443941/446149


from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

try:
    from itertools import izip
except ImportError:  # Python 3 built-in zip already returns iterable
    izip = zip

from itertools import repeat

try:
    import multiprocessing
    HAVE_PARALLEL = True
except ImportError:
    HAVE_PARALLEL = False

def _func_star_single(func_item_args):
    """Equivalent to:
       func = func_item_args[0]
       item = func_item_args[1]
       args = func_item_args[2:]
       return func(item,args[0],args[1],...)  
    """
    return func_item_args[0](*[func_item_args[1]] + func_item_args[2])

def _func_star_many(func_items_args):
    """Equivalent to:
       func = func_item_args[0]
       items = func_item_args[1]
       args = func_item_args[2:]
       return func(items[0],items[1],...,args[0],args[1],...)  
    """
    return func_items_args[0](*list(func_items_args[1]) + func_items_args[2])



def map(function, iterable, *args, **kwargs): # @ReservedAssignment
    """
    Equivalent to:
    return [function(x, args[0], args[1],...) for x in iterable]

    Keyword arguments:
       - parallel=True/False: Force parallelization on/off
       - chunksize=int: see multiprocessing.Pool().map
       - pool=multiprocessing.Pool() Pass an existing pool.
       - processes=int: see multiprocessing.Pool() processes argument
    """
    parallel = kwargs.get("parallel", HAVE_PARALLEL)
    chunksize = kwargs.get("chunksize", None)
    pool = kwargs.get("pool", None)
    close_pool = False
    processes = kwargs.get("processes", None)
    # Check if parallel is inconsistent with HAVE_PARALLEL:
    if HAVE_PARALLEL == False and parallel == True:
        print("W: Parallelization is disabled because",
              "multiprocessing is missing")
        parallel = False
    # Initialize pool if parallel:
    if parallel and pool is None:
        try:
            pool = multiprocessing.Pool(processes=processes)
            close_pool = True
        except AssertionError:  # Disable parallel on error:
            print("W: Could not create multiprocessing.Pool.",
                  "Parallel disabled")
            parallel = False
    # Map:
    if parallel:
        output = pool.map(_func_star_single,
                          izip(repeat(function), iterable,
                               repeat(list(args))),
                          chunksize)
        if close_pool:
            pool.close()
            pool.join()
    else:
        output = [function(*([item] + list(args))) for item in iterable]
    return output

def starmap(function, iterables, *args, **kwargs):
    """ Equivalent to:
        return [function(x1,x2,x3,..., args[0], args[1],...) for \
(x1,x2,x3...) in iterable]

    Keyword arguments:
       - parallel=True/False: Force parallelization on/off
       - chunksize=int: see multiprocessing.Pool().map
       - pool=multiprocessing.Pool() Pass an existing pool.
       - processes=int: see multiprocessing.Pool() processes argument
    """
    parallel = kwargs.get("parallel", HAVE_PARALLEL)
    chunksize = kwargs.get("chunksize", None)
    pool = kwargs.get("pool", None)
    close_pool = False
    processes = kwargs.get("processes", None)
    # Check if parallel is inconsistent with HAVE_PARALLEL:
    if HAVE_PARALLEL == False and parallel == True:
        print("W: Parallelization is disabled because",
              "multiprocessing is missing")
        parallel = False
    # Initialize pool if parallel:
    if parallel and pool is None:
        try:
            pool = multiprocessing.Pool(processes=processes)
            close_pool = True
        except AssertionError:  # Disable parallel on error:
            print("W: Could not create multiprocessing.Pool.",
                  "Parallel disabled")
            parallel = False
    # Map:
    if parallel:
        output = pool.map(_func_star_many,
                          izip(repeat(function),
                               iterables, repeat(list(args))),
                          chunksize)
        if close_pool:
            pool.close()
            pool.join()
    else:
        output = [function(*(list(item) + list(args))) for item in iterables]
    return output


if __name__ == "__main__":
    multiprocessing.freeze_support()
    def _func(*aaa):
        """ Prints and returns the inputs. Trivial example."""
        print(aaa)
        return aaa
    print("Example1: Begins")
    ITEMS = [1, 2, 3, 4]
    OUT = map(_func, ITEMS, 5, 6, 7, 8, parallel=False)
    print("Using parallel:")
    OUT_P = map(_func, ITEMS, 5, 6, 7, 8, parallel=True)
    if OUT != OUT_P:
        print("Example1: Failed")
    else:
        print("Example1: Success")
    print("Example2: Begins")
    ITEMS = [(1, 'a'), (2, 'b'), (3, 'c')]
    OUT = starmap(_func, ITEMS, 5, 6, 7, 8, parallel=False)
    print("Using parallel")
    OUT_P = starmap(_func, ITEMS, 5, 6, 7, 8, parallel=True)
    if OUT != OUT_P:
        print("Example2: Failed")
    else:
        print("Example2: Success")

