import atexit
import json
import time
import urllib.error
from multiprocessing import Lock
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


lastRequest: float = 0
requestCooldown: float = 0.5
requestLock: Lock = Lock()


def resultKey(param1, param2):
    if param1 > param2:
        return param2 + " + " + param1
    return param1 + " + " + param2


# Based on a stackoverflow post, dunno which
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


# Adapted from analog_hors on Discord
@persist_to_file('recipes.json')
def combine(a: str, b: str) -> str:
    global lastRequest, requestCooldown, requestLock
    requestLock.acquire()

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
                requestLock.release()
                return json.load(response)["result"]
        except urllib.error.HTTPError:
            time.sleep(1)
            print("Retrying...", flush=True)

