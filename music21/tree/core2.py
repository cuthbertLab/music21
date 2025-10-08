
import typing as t

from sortedcontainers import SortedList

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



class ElementNode(t.NamedTuple):
    position: SortTuple
    payload: Music21Object

class OffsetNode(t.NamedTuple):
    position: float
    payload: Music21Object


class CoreTree(SortedList[NodeT], t.Generic[NodeT], prebase.ProtoM21Object):
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


