# Wrapper around Priority_Queue with set so that we don't get repeats

from queue import PriorityQueue
from dataclasses import dataclass
from typing import Optional


@dataclass()
class GameState:
    priority: int
    item: tuple[str, Optional[tuple[str, str]]]

    def __init__(self, item):
        self.item = item
        self.priority = len(item)

    def addRecipe(self, output: str, input1: str, input2: str) -> 'GameState':
        return GameState(self.item + ((output, (input1, input2)),))

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.priority == other.priority

    def __hash__(self):
        return hash(self.item)


class NoRepeatPriorityQueue:
    queue: PriorityQueue
    seen: set

    def __init__(self):
        self.queue = PriorityQueue()
        self.seen = set()

    def put(self, item):
        if item not in self.seen:
            self.queue.put(item)
            self.seen.add(item)

    def get(self):
        item = self.queue.get()
        self.seen.remove(item)
        return item

    def empty(self):
        return self.queue.empty()

    def __len__(self):
        return self.queue.__sizeof__()

    def __contains__(self, item):
        return item in self.seen

    def __str__(self):
        return str(self.queue)
