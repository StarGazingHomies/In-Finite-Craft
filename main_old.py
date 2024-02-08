import atexit
import json
import sys
import time
import tracemalloc
import urllib.error
from collections import deque
from typing import Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


lastRequest = 0
requestCooldown = 0.5


def resultKey(param1, param2):
    if param1 > param2:
        return param2 + " + " + param1
    return param1 + " + " + param2


def persist_to_file(file_name):
    try:
        resultsCache = json.load(open(file_name, 'r'))
    except (IOError, ValueError):
        resultsCache = {}

    atexit.register(lambda: json.dump(resultsCache, open(file_name, 'w')))

    def decorator(func):
        def new_func(param1, param2):
            if resultKey(param1, param2) not in resultsCache:
                resultsCache[resultKey(param1, param2)] = func(param1, param2)
            return resultsCache[resultKey(param1, param2)]

        return new_func

    return decorator


@persist_to_file('recipes.json')
def combine(a: str, b: str) -> str:
    global lastRequest, requestCooldown
    print(a, "+", b)
    a = quote_plus(a)
    b = quote_plus(b)
    # Don't request too quickly
    if (time.perf_counter() - lastRequest) < requestCooldown:
        # print(f"Sleeping for {requestCooldown - (time.perf_counter() - lastRequest)} seconds", flush=True)
        time.sleep(requestCooldown - (time.perf_counter() - lastRequest))
    lastRequest = time.perf_counter()

    request = Request(
        f"https://neal.fun/api/infinite-craft/pair?first={a}&second={b}",
        headers={
            "Referer": "https://neal.fun/infinite-craft/",
            "User-Agent": "curl/7.54.1",
        },
    )
    while True:
        try:
            with urlopen(request) as response:
                # raise Exception(f"HTTP {response.getcode()}: {response.reason}")
                return json.load(response)["result"]
        except urllib.error.HTTPError:
            time.sleep(1)
            print("Retrying...", flush=True)


def bfs():
    State = dict[str, Optional[tuple[str, str]]]

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
    queue: deque[State] = deque((init_state,))
    start_time = time.perf_counter()

    while len(queue) > 0:
        state = queue.popleft()
        elements = list(state)
        for i in range(len(elements)):
            for j in range(i, len(elements)):
                output = combine(elements[i], elements[j])
                if (output is None) or (output in state) or (output == "Nothing"):
                    continue

                if output not in elements:
                    child = dict(state.items())
                    child[output] = elements[i], elements[j]
                    queue.append(child)
                    if output not in recipes_found:
                        recipes_found.add(output)
                        print(str(len(recipes_found)) + ": " + output)
                        for output, inputs in child.items():
                            if inputs is not None:
                                left, right = inputs
                                print(f"{left} + {right} -> {output}")
                        print(flush=True)

                        # current, peak = tracemalloc.get_traced_memory()
                        # print(f"Current memory usage is {current / 2**20}MB; Peak was {peak / 2**20}MB")
                        print("Current time elapsed: ", time.perf_counter() - start_time)


if __name__ == '__main__':
    # tracemalloc.start()
    bfs()
