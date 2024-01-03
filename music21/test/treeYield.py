# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         treeYield.py
# Purpose:      traverse a complex datastructure and yield elements
#               that fit a given criteria
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Asato Cuthbert
# License:      CC-BY (see StackOverflow link below)
# ------------------------------------------------------------------------------
# https://stackoverflow.com/questions/12611337/
#     recursively-dir-a-python-object-to-find-values-of-a-certain-type-or-with-a-cer
from __future__ import annotations

import weakref

import music21

class TreeYielder:  # pragma: no cover
    def __init__(self, yieldValue=None):
        '''
        `yieldValue` should be a lambda function that
        returns True/False or a function/method call that
        will be passed the value of a current attribute
        '''
        self.currentStack = []
        self.memo = None
        self.yieldValue = yieldValue
        self.stackVals = []
        self.nonIterables = [int, str,  # t.LongType,
                             float, type(None), bool]

    def run(self, obj, memo=None):
        '''
        traverse all attributes of an object looking
        for subObjects that meet a certain criteria.
        yield them.

        `memo` is a dictionary to keep track of objects
        that have already been seen

        The original object is added to the memo and
        also checked for yieldValue
        '''
        if memo is None:
            memo = {}
        self.memo = memo
        if id(obj) in self.memo:
            self.memo[id(obj)] += 1
            return
        else:
            self.memo[id(obj)] = 1

        if self.yieldValue(obj) is True:
            yield obj

        # now check for sub values...
        self.currentStack.append(obj)

        tObj = type(obj)
        if tObj in self.nonIterables:
            pass
        elif tObj == dict:
            for keyX in obj:
                dictTuple = ('dict', keyX)
                self.stackVals.append(dictTuple)
                x = obj[keyX]
                for z in self.run(x, memo=memo):
                    yield z
                self.stackVals.pop()

        elif tObj in [list, tuple]:
            for i, x in enumerate(obj):
                listTuple = ('listLike', i)
                self.stackVals.append(listTuple)
                for z in self.run(x, memo=memo):
                    yield z
                self.stackVals.pop()

        else:  # objects or uncaught types...
            # from http://bugs.python.org/file18699/static.py
            try:
                instance_dict = object.__getattribute__(obj, '__dict__')
            except AttributeError:
                # probably uncaught static object
                return

            for x in instance_dict:
                # noinspection PyBroadException
                try:
                    gotValue = object.__getattribute__(obj, x)
                except Exception:  # pylint: disable=broad-exception-caught
                    continue
                objTuple = ('getattr', x)
                self.stackVals.append(objTuple)
                try:
                    for z in self.run(gotValue, memo=memo):
                        yield z
                except RuntimeError:
                    raise ValueError(f'Maximum recursion on:\n{self.currentLevel()}')
                self.stackVals.pop()

        self.currentStack.pop()

    def currentLevel(self):
        currentStr = ''
        for stackType, stackValue in self.stackVals:
            if stackType == 'dict':
                if isinstance(stackValue, str):
                    currentStr += "['" + stackValue + "']"
                else:  # numeric key...
                    currentStr += '[' + str(stackValue) + ']'
            elif stackType == 'listLike':
                currentStr += '[' + str(stackValue) + ']'
            elif stackType == 'getattr':
                currentStr += ".__getattribute__('" + stackValue + "')"
            else:
                raise ValueError(f'Cannot get attribute for stackType {stackType!r}')
        return currentStr


def testCode():  # pragma: no cover
    class Mock:
        def __init__(self, mockThing, embedMock=True):
            self.abby = 30
            self.mocker = mockThing
            self.mockList = [mockThing, mockThing, 40]
            self.embeddedMock = None
            if embedMock is True:
                self.embeddedMock = Mock(mockThing, embedMock=False)

    def mockType(x):
        return x.__class__.__name__ == 'Mock'

    subList = [100, 60, -2]
    myList = [5, 20, [5, 12, 17], 30,
              {'hello': 10, 'goodbye': 22, 'mock': Mock(subList)}, -20, Mock(subList)]
    myList.append(myList)

    ty = TreeYielder(mockType)
    for val in ty.run(myList):
        print(val, ty.currentLevel())


def testMIDIParse():  # pragma: no cover
    from music21 import converter
    from music21 import common
    from music21 import freezeThaw

    # a = 'https://github.com/ELVIS-Project/vis/raw/master/test_corpus/prolationum-sanctus.midi'
    # c = converter.parse(a)
    # c = corpus.parse('bwv66.6', forceSource=True)
    # v = freezeThaw.StreamFreezer(c)
    # v.setupSerializationScaffold()
    # return v.writeStr()  # returns a string

    a = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test03.mid'

    # a = 'https://github.com/ELVIS-Project/vis/raw/master/test_corpus/prolationum-sanctus.midi'
    c = converter.parse(a)
    v = freezeThaw.StreamFreezer(c)
    v.setupSerializationScaffold()

    def mockType(x):
        return isinstance(x, weakref.ReferenceType)

    ty = TreeYielder(mockType)
    for val in ty.run(c):
        print(val, ty.currentLevel())


def find_all_exception_classes_in_m21():  # pragma: no cover
    return find_all_classes_by_criteria(
        lambda mm: issubclass(mm, music21.exceptions21.Music21Exception)
    )

def find_all_non_hashable_m21objects():  # pragma: no cover
    # is a bug if not empty
    def is_unhashable(mm):
        if not issubclass(mm, music21.base.Music21Object):
            return False
        try:
            {mm()}
        except TypeError as te:
            return 'unhashable' in str(te)
        return False
    return find_all_classes_by_criteria(is_unhashable)

def find_all_non_default_instantiation_m21objects():  # pragma: no cover
    # Lack of default instantiation is not necessarily a bug, but
    # let's try not to have them
    def needs_attributes(mm):
        if not issubclass(mm, music21.base.Music21Object):
            return False
        try:
            mm()
        except TypeError:
            return True
        return False
    return find_all_classes_by_criteria(needs_attributes)


def find_all_classes_by_criteria(criteria):  # pragma: no cover
    from collections import deque
    import types

    d = deque([music21])
    seen = set()
    matches = set()
    while d:
        m = d.popleft()
        if m in seen:
            continue
        print(m)
        for mm_name in dir(m):
            mm = getattr(m, mm_name)
            if (isinstance(mm, types.ModuleType)
                    and mm not in seen
                    and 'music21' in getattr(mm, '__file__', '')):
                # noinspection PyTypeChecker
                d.append(mm)
            elif isinstance(mm, type) and mm not in seen and criteria(mm):
                matches.add(mm)
        seen.add(m)
    return matches


if __name__ == '__main__':
    pass
    # testCode()
    testMIDIParse()
