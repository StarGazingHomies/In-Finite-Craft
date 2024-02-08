# Wrapper around Priority_Queue with set so that we don't get repeats

from queue import PriorityQueue, SimpleQueue
from dataclasses import dataclass
from typing import Optional


# target_word = "geometry"


@dataclass()
class GameState:
    priority: int
    item: tuple[str, Optional[tuple[str, str]]]

    def __init__(self, item):
        self.item = item
        # if target_word == "":
        self.priority = len(item)
        # else:
        #     self.priority = min([phraseDistance(target_word, i[0]) for i in item]) * len(item)

    def addRecipe(self, output: str, input1: str, input2: str) -> 'GameState':
        return GameState(self.item + ((output, (input1, input2)),))

    def output(self):
        return self.item[-1][0]

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.priority == other.priority

    def __hash__(self):
        objects = [i[0] for i in self.item]
        objects.sort()
        return hash(tuple(objects))


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
        self.seen.remove(item)
        return item

    def __len__(self):
        return len(self.seen)

    def __contains__(self, item):
        return item in self.seen

    def __str__(self):
        return str(self.queue)
