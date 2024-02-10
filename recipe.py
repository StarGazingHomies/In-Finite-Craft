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
localOnly: bool = False
sleepTime: float = 1.0
retryExponent: float = 2.0


def result_key(param1, param2):
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


discovery_file = "cache/discoveries.json"


def add_discovery(a: str, b: str, result: str):
    try:
        discoveries = json.load(open(discovery_file, 'r'))
    except (IOError, ValueError):
        discoveries = {}

    discoveries[result] = result_key(a, b)
    json.dump(discoveries, open(discovery_file, 'w'))


# Based on a stackoverflow post, forgot to write down which one
def persist_to_file(file_name, key_func):
    try:
        resultsCache = json.load(open(file_name, 'r'))
    except (IOError, ValueError):
        resultsCache = {}

    atexit.register(lambda: save(resultsCache, file_name))

    def decorator(func):
        def new_func(*args):
            global changes, autosaveInterval, localOnly

            if key_func(*args) not in resultsCache:
                # For viewing existing data only
                if localOnly:
                    return "Nothing"
                resultsCache[key_func(*args)] = func(*args)

                changes += 1
                if changes % autosaveInterval == 0:
                    print("Autosaving...")
                    save(resultsCache, file_name)

            return resultsCache[key_func(*args)]

        return new_func

    return decorator


# Adapted from analog_hors on Discord
@persist_to_file('cache/recipes.json', result_key)
def combine(a: str, b: str) -> str:
    global lastRequest, requestCooldown, changes, sleepTime, retryExponent

    # with requestLock:
    print(f"Requesting {a} + {b}", flush=True)
    a = quote_plus(a)
    b = quote_plus(b)

    # Don't request too quickly. Have been 429'd way too many times
    t = time.perf_counter()
    if (t - lastRequest) < requestCooldown:
        # print("Sleeping...", flush=True)
        # print(f"Sleeping for {requestCooldown - (time.perf_counter() - lastRequest)} seconds", flush=True)
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
                r = json.load(response)
                if r['isNew']:
                    add_discovery(a, b, r['result'])
                return r["result"]
        except urllib.error.HTTPError:
            time.sleep(sleepTime)
            sleepTime *= retryExponent
            print("Retrying...", flush=True)


def merge_recipe_files(file1: str, file2: str, output: str):
    try:
        recipes1 = json.load(open(file1, 'r'))
        recipes2 = json.load(open(file2, 'r'))
    except (IOError, ValueError):
        print("Could not load recipe files", flush=True)
        return

    for key in recipes2:
        if key not in recipes1:
            recipes1[key] = recipes2[key]

    save(recipes1, output)
