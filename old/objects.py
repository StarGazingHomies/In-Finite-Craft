# Wrapper around Priority_Queue with set so that we don't get repeats
from collections import deque
from queue import PriorityQueue, SimpleQueue
from dataclasses import dataclass
from typing import Optional, TextIO, BinaryIO


# target_word = "geometry"


@dataclass()
class GameState:
    priority: int
    item: tuple[str, Optional[tuple[str, str]]]

    def __init__(self, item):
        self.item = item
        self.priority = len(item)

    def add_recipe(self, output: str, input1: str, input2: str) -> 'GameState':
        return GameState(self.item + ((output, (input1, input2)),))

    def pop_recipe(self) -> 'GameState':
        return GameState(self.item[:-1])

    @property
    def output(self):
        return self.item[-1][0]

    @property
    def objects(self):
        objects = [i[0] for i in self.item]
        objects.sort()
        return tuple(objects)

    def __lt__(self, other: 'GameState'):
        if self.priority != other.priority:
            return self.priority < other.priority
        return str(self.objects) < str(other.objects)

    def __eq__(self, other: 'GameState'):
        return False not in [i == j for i, j in zip(self.objects, other.objects)]

    def __hash__(self):
        return hash(tuple(self.objects))

    def __str__(self):
        return str(self.item)


def gameStateFromString(string: str) -> GameState:
    return GameState(tuple([tuple(i.split(" + ")) for i in string.split(", ")]))


class NoRepeatPriorityQueue:
    queue: PriorityQueue
    seen: set

    def __init__(self):
        self.queue = PriorityQueue()
        self.seen = set()

    def put(self, item):
        if item in self.seen:
            return
        self.queue.put(item)
        self.seen.add(item)

    def get(self):
        item = self.queue.get()
        return item

    def __len__(self):
        return self.queue.qsize()

    def __contains__(self, item):
        return item in self.seen

    def __str__(self):
        return str(self.queue)
