import multiprocessing
import sys
import time

from objects import NoRepeatPriorityQueue, GameState
from typing import Optional

import recipe


def processState(state: GameState, queue: NoRepeatPriorityQueue):
    elements = state.item

    for i in range(len(elements)):
        for j in range(i, len(elements)):

            elem1 = elements[i][0]
            elem2 = elements[j][0]

            output = recipe.combine(elem1, elem2)
            if (output is None) or (output in [k[0] for k in elements]) or (output == "Nothing"):
                continue

            if output not in elements:
                child = elements + ((output, (elem1, elem2)),)
                # print(child)
                queue.put(state.addRecipe(output, elem1, elem2))


def bfs():
    State = dict[[str, Optional[tuple[str, str]]]]

    init_state: State = {
        "Water": None,
        "Fire": None,
        "Wind": None,
        "Earth": None,
        # "Unicorn": None,
        # "Pegasus": None,
        # "Twilight Sparkle": None,
        # "Rainbow Dash": None,
        # "Princess Celestia": None
    }
    for element in sys.argv[1:]:
        init_state[element] = None

    queue = NoRepeatPriorityQueue()
    queue.put(GameState(tuple(init_state.items())))

    with multiprocessing.Pool(4) as pool:
        while True:
            if len(queue) > 0:
                res = pool.apply_async(processState, (queue.get(), queue))
                print(res.get(timeout = 1))


if __name__ == '__main__':
    bfs()
