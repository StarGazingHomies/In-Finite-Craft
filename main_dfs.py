import multiprocessing
import sys
import time
from queue import SimpleQueue

from objects import NoRepeatPriorityQueue, GameState, gameStateFromString
from typing import Optional

import recipe
import tracemalloc


def dfs():
    init_state = {
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

    curDepth = 1

    start_time = time.perf_counter()

    while True:
        # Search depth n
        curRecipes = [0 for i in range(curDepth)]
        while True:
            pass

        curDepth += 1
