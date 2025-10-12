
import typing as t

from sortedcontainers import SortedKeyList

from music21 import prebase
from music21.sorting import SortTuple

if t.TYPE_CHECKING:
    from music21.base import Music21Object


KeyT = t.TypeVar('KeyT')

class HasKey(t.Protocol[KeyT]):
    '''
    Protocol for named tuples which are sortable
    '''
    position: KeyT
    def __getitem__(self, i: int) -> t.Any: ...
    def __lt__(self, other: t.Any) -> bool: ...


NodeT = t.TypeVar('NodeT', bound=HasKey)


# only about 8% speedup even to 100000 entries -- not worth maintaining the added complexity

# class SortedAppendKeyList(SortedKeyList[NodeT, KeyT], t.Generic[NodeT, KeyT]):
#     def append(self, value: NodeT) -> None:  # type: ignore[attr-defined]
#         '''
#         Append value to the sorted-key list
#         if its key is >= the current maximum; otherwise,
#         raise ValueError.
#
#         Works in O(1) time up to LOAD FACTOR and then O(log(n/LOAD FACTOR))
#         after that -- essentially free.
#         '''
#         # pylint: disable=protected-access
#         _lists = self._lists  # noqa
#         _keys = self._keys  # noqa
#         _maxes = self._maxes  # noqa
#         key = self._key(value)  # noqa
#
#         # First element: initialize structures
#         if not _maxes:
#             _lists.append([value])
#             _keys.append([key])
#             _maxes.append(key)
#             self._len += 1  # noqa
#             return
#
#         last = len(_maxes) - 1
#
#         # Enforce monotonicity
#         if key < _maxes[last]:
#             raise ValueError(
#                 f'Append key {key!r} is less than current maximum {_maxes[last]!r}'
#             )
#
#         # Fast path: append to last sublist
#         _lists[last].append(value)
#         _keys[last].append(key)
#         _maxes[last] = key
#         self._expand(last)  # noqa
#         self._len += 1  # noqa


class ElementNode(t.NamedTuple):
    position: SortTuple
    payload: Music21Object

class OffsetNode(t.NamedTuple):
    position: float
    payload: Music21Object


class CoreTree(SortedKeyList[NodeT, KeyT], t.Generic[NodeT, KeyT], prebase.ProtoM21Object):
    def getNodeBefore(self, key: KeyT) -> NodeT | None:
        '''
        Return the node immediately before the given key.
        '''
        index = self.bisect_left(key)
        if index == 0:
            return None
        return self[index - 1]

    def getNodeAfter(self, key: KeyT) -> NodeT | None:
        '''
        Return the node immediately after the given key.
        '''
        index = self.bisect_right(key)
        if index == len(self):
            return None
        return self[index]

    def getPositionBefore(self, key: KeyT) -> KeyT | None:
        '''
        Return the key immediately before the given key.
        '''
        index = self.bisect_left(key)
        if index == 0:
            return None
        return self[index - 1][0]

    def getPositionAfter(self, key: KeyT) -> KeyT|None:
        index = self.bisect_right(key)
        if index == len(self):
            return None
        return self[index][0]

    def removeNode(self, key: KeyT) -> bool:
        '''
        Remove the node at the given key. Returns True if removed.
        '''
        node = self.getNodeByPosition(key)
        if node is None:
            return False
        self.remove(node)
        return True

    def getNodeByPosition(self, position: KeyT) -> NodeT|None:
        index = self.bisect(position)
        if index == len(self):
            return None
        if self[index][0] != position:
            return None
        return self[index]


