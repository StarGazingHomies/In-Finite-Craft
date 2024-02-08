import multiprocessing
import sys
import time

from objects import NoRepeatPriorityQueue, GameState, gameStateFromString
from typing import Optional

import recipe
import tracemalloc


# Adapted from analog_hors on Manechat
# https://discord.com/channels/98609319519453184/1204570015857250344/1204753221294497792
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

    print(GameState(tuple(init_state.items())))
    print(gameStateFromString(str(GameState(tuple(init_state.items())))))

    start_time = time.perf_counter()
    recipes_found = set()

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
                        print(str(len(recipes_found)) + ": " + output)
                        for output, inputs in child:
                            if inputs is not None:
                                left, right = inputs
                                print(f"{left} + {right} -> {output}")

                        # current, peak = tracemalloc.get_traced_memory()
                        # print(f"Current memory usage is {current / 2**20}MB; Peak was {peak / 2**20}MB")
                        # print("Current time elapsed: ", time.perf_counter() - start_time)

                        # if len(child) > 4 + 5:
                        #     print("Current queue size: ", len(queue))
                        #     print("Current time elapsed: ", time.perf_counter() - start_time)
                        #     return

                        print(flush=True)


if __name__ == '__main__':
    # tracemalloc.start()
    bfs()
