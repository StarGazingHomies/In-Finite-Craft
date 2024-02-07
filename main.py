import sys
import time

from objects import NoRepeatPriorityQueue, GameState
from typing import Optional

import recipe


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

    recipes_found = set()
    queue = NoRepeatPriorityQueue()
    queue.put(GameState(tuple(init_state.items())))

    start_time = time.perf_counter()

    while len(queue) > 0:
        state = queue.get()
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

                    if output not in recipes_found:
                        recipes_found.add(output)
                        print(output)
                        for output, inputs in child:
                            if inputs is not None:
                                left, right = inputs
                                print(f"{left} + {right} -> {output}")

                        print("Current queue size: ", len(queue))
                        print("Current time elapsed: ", time.perf_counter() - start_time)
                        print(flush=True)


if __name__ == '__main__':
    bfs()
