import atexit
import json
import os
import sys
import time
import urllib.error
from multiprocessing import Lock
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

# Basically constants
lastRequest: float = 0
requestCooldown: float = 0.5  # 0.5s is safe for this API
# requestLock: Lock = Lock()    # Multiprocessing - not implemented yet
changes: int = 0
autosaveInterval: int = 100
localOnly: bool = True
sleepTime: float = 1.0
retryExponent: float = 2.0


def resultKey(param1, param2):
    if param1 > param2:
        return param2 + " + " + param1
    return param1 + " + " + param2


def save(dictionary, file_name):
    try:
        json.dump(dictionary, open(file_name, 'w'))
    except FileNotFoundError:
        print(f"Could not write to {file_name}! Trying to create a folder...", flush=True)
        try:
            os.mkdir("cache")
            json.dump(dictionary, open(file_name, 'w'))
        except Exception as e:
            print(f"Could not create folder or write to file: {e}", flush=True)
            print(dictionary)
    except Exception as e:
        print(f"Unrecognized Error: {e}", flush=True)
        print(dictionary)


# Based on a stackoverflow post, forgot to write down which one
def persistToFile(fileName, keyFunc):
    try:
        resultsCache = json.load(open(fileName, 'r'))
    except (IOError, ValueError):
        resultsCache = {}

    atexit.register(lambda: save(resultsCache, fileName))

    def decorator(func):
        def newFunc(*args):
            global changes, autosaveInterval, localOnly

            if keyFunc(*args) not in resultsCache:
                # For viewing existing data only
                if localOnly:
                    sys.exit()
                resultsCache[keyFunc(*args)] = func(*args)

                changes += 1
                if changes % autosaveInterval == 0:
                    print("Autosaving...")
                    save(resultsCache, fileName)

            return resultsCache[keyFunc(*args)]

        return newFunc

    return decorator


# Adapted from analog_hors on Discord
@persistToFile('cache/recipes.json', resultKey)
def combine(a: str, b: str) -> str:
    global lastRequest, requestCooldown, requestLock, changes, sleepTime, retryExponent

    # with requestLock:
    print(f"Requesting {a} + {b}", flush=True)
    a = quote_plus(a)
    b = quote_plus(b)

    # Don't request too quickly. Have been 429'd way too many times
    t = time.perf_counter()
    if (t - lastRequest) < requestCooldown:
        # print("Sleeping...", flush=True)
        print(f"Sleeping for {requestCooldown - (time.perf_counter() - lastRequest)} seconds", flush=True)
        time.sleep(requestCooldown - (t - lastRequest))
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
            time.sleep(sleepTime)
            sleepTime *= retryExponent
            print("Retrying...", flush=True)





