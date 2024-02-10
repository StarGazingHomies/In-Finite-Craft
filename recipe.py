import atexit
import json
import os
# import sys
import time
import urllib.error
# from multiprocessing import Lock
from typing import Optional
from urllib.parse import quote_plus, unquote_plus
from urllib.request import Request, urlopen

# Basically constants
# requestLock: Lock = Lock()    # Multiprocessing - not implemented yet


DELIMITER = "\t"


def result_key(param1, param2):
    if param1 > param2:
        return param2 + DELIMITER + param1
    return param1 + DELIMITER + param2


def load_json(file_name):
    return json.load(open(file_name, 'r'))


def save_json(dictionary, file_name):
    try:
        json.dump(dictionary, open(file_name, 'w'))
    except FileNotFoundError:
        print(f"Could not write to {file_name}! Trying to create cache folder...", flush=True)
        try:
            os.mkdir("cache")  # TODO: generalize
            json.dump(dictionary, open(file_name, 'w'))
        except Exception as e:
            print(f"Could not create folder or write to file: {e}", flush=True)
            print(dictionary)
    except Exception as e:
        print(f"Unrecognized Error: {e}", flush=True)
        print(dictionary)


class RecipeHandler:
    recipes_cache: dict[str, str]
    items_cache: dict[str, tuple[str, bool]]
    recipes_changes: int = 0
    recipe_autosave_interval: int = 200
    items_changes: int = 0
    items_autosave_interval: int = 50
    recipes_file: str = "cache/recipes.json"
    items_file: str = "cache/items.json"

    last_request: float = 0
    request_cooldown: float = 0.5  # 0.5s is safe for this API
    sleep_time: float = 1.0
    retry_exponent: float = 2.0
    local_only: bool = False

    def __init__(self):
        self.recipes_cache = json.load(open(self.recipes_file, 'r'))
        self.items_cache = json.load(open(self.items_file, 'r'))
        atexit.register(lambda: save_json(self.recipes_cache, self.recipes_file))
        atexit.register(lambda: save_json(self.items_cache, self.items_file))

    def save_response(self, a: str, b: str, response: dict):
        # print(a, b, result_key(a, b), response)
        result = response['result']
        emoji = response['emoji']
        new = response['isNew']
        # print(result)

        # Items - emoji, new discovery
        if result not in self.items_cache:
            # print(f"Adding {result} to items cache...")
            # print(self.items_cache[result])
            self.items_cache[result] = (emoji, new)
            self.items_changes += 1
            if self.items_changes % self.items_autosave_interval == 0:
                print("Autosaving items file...")
                save_json(self.items_cache, self.items_file)

        # Recipe: A + B --> C
        self.recipes_cache[result_key(a, b)] = result
        self.recipes_changes += 1
        if self.recipes_changes % self.recipe_autosave_interval == 0:
            print("Autosaving recipes file...")
            save_json(self.recipes_cache, self.recipes_file)

    def get_response(self, a: str, b: str) -> Optional[str]:
        if result_key(a, b) not in self.recipes_cache:
            return None
        result = self.recipes_cache[result_key(a, b)]
        if result not in self.items_cache:
            # print(f"Missing {result} in cache!")
            # print(f"{result}!!")
            # Didn't get the emoji. Useful for upgrading from a previous version.
            return None
        return result

    # Adapted from analog_hors on Discord
    def combine(self, a: str, b: str) -> str:
        # Query local cache
        local_result = self.get_response(a, b)
        if local_result:
            return local_result
        elif self.local_only:
            return "Nothing"

        # with requestLock:
        print(f"Requesting {a} + {b}", flush=True)
        a_req = quote_plus(a)
        b_req = quote_plus(b)

        # Don't request too quickly. Have been 429'd way too many times
        t = time.perf_counter()
        if (t - self.last_request) < self.request_cooldown:
            time.sleep(self.request_cooldown - (t - self.last_request))
        self.last_request = time.perf_counter()

        request = Request(
            f"https://neal.fun/api/infinite-craft/pair?first={a_req}&second={b_req}",
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
                    self.save_response(a, b, r)
                    return r["result"]
            except urllib.error.HTTPError:
                time.sleep(self.sleep_time)
                self.sleep_time *= self.retry_exponent
                print("Retrying...", flush=True)
