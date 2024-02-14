import atexit
import json
import os
import sys
import time
import traceback
import urllib.error
# from multiprocessing import Lock
from typing import Optional
from urllib.parse import quote_plus, unquote_plus
from urllib.request import Request, urlopen

from urllib3 import HTTPResponse

# requestLock: Lock = Lock()    # Multiprocessing - not implemented yet


DELIMITER = "\t"
WORD_TOKEN_LIMIT = 20


def result_key(param1, param2):
    if param1 > param2:
        return param2 + DELIMITER + param1
    return param1 + DELIMITER + param2


def load_json(file_name):
    try:
        return json.load(open(file_name, 'r'))
    except FileNotFoundError:
        return {}


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
    sleep_default: float = 1.0
    retry_exponent: float = 2.0
    local_only: bool = False
    trust_cache_nothing: bool = True     # Trust the local cache for "Nothing" results
    nothing_verification: int = 3        # Verify "Nothing" n times with the API
    nothing_cooldown: float = 5.0        # Cooldown between "Nothing" verifications

    def __init__(self):
        self.recipes_cache = load_json(self.recipes_file)
        self.items_cache = load_json(self.items_file)
        if not self.trust_cache_nothing:
            l = frozenset(self.recipes_cache.items())
            for ingredients, result in l:
                if result == "Nothing":
                    self.recipes_cache.pop(ingredients)

        atexit.register(lambda: save_json(self.recipes_cache, self.recipes_file))
        atexit.register(lambda: save_json(self.items_cache, self.items_file))

    def save_response(self, a: str, b: str, response: dict):
        # print(a, b, result_key(a, b), response)
        result = response['result']
        emoji = response['emoji']
        new = response['isNew']
        print(f"New Recipe: {a} + {b} -> {result}")
        if new:
            print(f"FIRST DISCOVERY: {a} + {b} -> {result}")
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

    def get_local(self, a: str, b: str) -> Optional[str]:
        if result_key(a, b) not in self.recipes_cache:
            return None
        result = self.recipes_cache[result_key(a, b)]
        if result not in self.items_cache:
            # print(f"Missing {result} in cache!")
            # print(f"{result}!!")
            # Didn't get the emoji. Useful for upgrading from a previous version.
            return None
        return result

    def save_nothing(self, a: str, b: str, response: dict):
        file_name = f"cache/nothing/{a}+{b}.json"
        if not os.path.exists(file_name):
            os.mkdir("cache/nothing")
        with open(file_name, 'w') as file:
            json.dump(response, file)

    # Adapted from analog_hors on Discord
    def combine(self, a: str, b: str) -> str:
        # Query local cache
        local_result = self.get_local(a, b)
        if local_result:
            return local_result
        elif self.local_only:
            return "Nothing"

        # print(f"Requesting {a} + {b}", flush=True)
        r = self.request_pair(a, b)
        nothing_count = 1
        while r['result'] == "Nothing" and nothing_count < self.nothing_verification:
            # Request again to verify, just in case...
            # Increases time taken on requests but should be worth it.
            # Also note that this can't be asynchronous due to all the optimizations I made assuming a search order
            time.sleep(self.nothing_cooldown)
            print("Re-requesting Nothing result...", flush=True)
            last_r = r

            r = self.request_pair(a, b)

            if (r['result'] != "Nothing") and (r['result'] != last_r['result']):
                print(f"WARNING: Inconsistent Nothing result: {last_r['result']} -> {r['result']}")
                # Save the full Nothing response to a different file
                self.save_nothing(a, b, last_r)

            nothing_count += 1

        self.save_response(a, b, r)
        return r['result']

    def request_pair(self, a: str, b: str) -> HTTPResponse:
        # with requestLock:
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
                    # Reset exponential retrying
                    self.sleep_time = self.sleep_default
                    return json.load(response)
            except urllib.error.HTTPError as e:
                print(e, file=sys.stderr)
                time.sleep(self.sleep_time)
                self.sleep_time *= self.retry_exponent
                print("Retrying...", flush=True)
            except Exception as e:
                # Handling more than just that one error
                print("Unrecognized Error: ", e, file=sys.stderr)
                traceback.print_exc()
                time.sleep(self.sleep_time)
                self.sleep_time *= self.retry_exponent
                print("Retrying...", flush=True)
