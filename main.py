# import time
from functools import cache
from typing import Optional

import recipe
# import tracemalloc


@cache
def int_to_pair(n: int) -> tuple[int, int]:
    if n < 0:
        return -1, -1
    j = 0
    while n > j:
        n -= j + 1
        j += 1
    i = n
    return i, j


@cache
def limit(n: int) -> int:
    return n * (n + 1) // 2


class GameState:
    items: list[str]
    state: list[int]
    visited: list[set[str]]
    children: set[str]

    def __init__(self, items: list[str], state: list[int], children: set[str]):
        self.state = state
        self.items = items
        self.children = children

    def __str__(self):
        steps = [self.items[-1] + ":"]
        for i in range(len(self.state)):
            left, right = int_to_pair(self.state[i])
            if (left < 0) or (right < 0):
                continue
            steps.append(f"{self.items[left]} + {self.items[right]} -> {self.items[i]}")
        return "\n".join(steps)

    def __len__(self):
        return len(self.state)

    def __eq__(self, other):
        return self.state == other.state

    def __hash__(self):
        return hash(str(self.state))

    def child(self, i: int) -> Optional['GameState']:
        if i <= self.state[-1] or i >= limit(len(self)):
            return None

        u, v = int_to_pair(i)
        craft_result = recipe.combine(self.items[u], self.items[v])
        if (craft_result is None or
                craft_result == "Nothing" or
                craft_result in self.items or
                craft_result in self.children):
            return None
        self.children.add(craft_result)

        new_state = self.state + [i]
        new_items = self.items + [craft_result]
        return GameState(new_items, new_state, self.children.copy())

    def tail_item(self) -> str:
        return self.items[-1]


# best_recipes: dict[str] = dict()
visited = set()
best_recipes_file: str = "best_recipes.txt"


def process_node(state: GameState):
    if state.tail_item() not in visited:
        visited.add(state.tail_item())
        with open(best_recipes_file, "a") as file:
            file.write(str(len(visited)) + ": " + str(state) + "\n\n")
        # best_recipes[state.tail_item()] = str(state)


def dls(state: GameState, depth: int):
    if depth == 0:
        process_node(state)
        return 1
    lower_limit = 0
    if depth == 1 and len(state) >= 5:
        lower_limit = limit(len(state) - 1)

    count = 0
    for i in range(lower_limit, limit(len(state))):
        child = state.child(i)
        if child is not None:
            count += dls(child, depth - 1)

    return count


def iterative_deepening_dfs():
    with open("recipes.txt", "w"):
        pass

    init_state = {
        "Water": None,
        "Fire": None,
        "Wind": None,
        "Earth": None,
    }

    curDepth = 1

    # start_time = time.perf_counter()

    while True:
        dls(
            GameState(
                list(init_state.keys()),
                [-1 for _ in range(len(init_state))],
                set()),
            curDepth)
        # print()
        # print(len(visited))

        # Performance
        # current, peak = tracemalloc.get_traced_memory()
        # print(f"Current memory usage is {current / 2**20}MB; Peak was {peak / 2**20}MB")
        # print(f"Current time elapsed: {time.perf_counter() - start_time:.4f}")
        # print("Completed depth: ", curDepth)
        # print(flush=True)
        curDepth += 1


def main():
    iterative_deepening_dfs()


if __name__ == "__main__":
    # tracemalloc.start()
    main()
