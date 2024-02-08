# Wrapper around Priority_Queue with set so that we don't get repeats

from queue import PriorityQueue, SimpleQueue
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

    def output(self):
        return self.item[-1][0]

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.priority == other.priority

    def __hash__(self):
        return hash(self.item)


class NoRepeatPriorityQueue:
    queue: PriorityQueue
    seen: set
    recipes_found: set

    def __init__(self):
        self.queue = PriorityQueue()
        self.seen = set()
        self.recipes_found = set()

    def put(self, item):
        if item not in self.seen:
            self.queue.put(item)
            self.seen.add(item)

            if item.output() not in self.recipes_found:
                self.recipes_found.add(item.output())
                print(item.output() + ":")
                for output, inputs in item.item:
                    if inputs is not None:
                        left, right = inputs
                        print(f"{left} + {right} -> {output}")

                if len(item.item) > 4 + 5:
                    print("Current queue size: ", len(self.seen))
                print(flush=True)

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
