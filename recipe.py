import atexit
import json
import os
import sys
import time
import traceback
import urllib.error
from functools import cache
from typing import Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from bidict import bidict

DELIMITER = "\t"
WORD_TOKEN_LIMIT = 20
WORD_COMBINE_CHAR_LIMIT = 30


def pair_to_int(i: int, j: int) -> int:
    if j < i:
        i, j = j, i
    return i + (j * (j + 1)) // 2


def load_json(file_name):
    try:
        return json.load(open(file_name, 'r', encoding='utf-8'))
    except FileNotFoundError:
        return {}


def save_json(dictionary, file_name):
    try:
        json.dump(dictionary, open(file_name, 'w', encoding='utf-8'), ensure_ascii=False)
    except FileNotFoundError:
        print(f"Could not write to {file_name}! Trying to create cache folder...", flush=True)
        try:
            os.mkdir("cache")  # TODO: generalize
            json.dump(dictionary, open(file_name, 'w', encoding='utf-8'), ensure_ascii=False)
        except Exception as e:
            print(f"Could not create folder or write to file: {e}", flush=True)
            print(dictionary)
    except Exception as e:
        print(f"Unrecognized Error: {e}", flush=True)
        print(dictionary)


def save_nothing(a: str, b: str, response: dict):
    file_name = f"cache/nothing/{a}+{b}.json"
    try:
        with open(file_name, 'w') as file:
            json.dump(response, file)
    except FileNotFoundError:
        try:
            os.mkdir("cache/nothing")
            with open(file_name, 'w') as file:
                json.dump(response, file)
        except Exception as e:
            print(f"Could not create folder or write to file: {e}", flush=True)
            print(response)


class RecipeHandler:
    recipes_cache: dict[str, int]
    items_cache: dict[str, tuple[str, int, bool]]
    items_id: bidict[str, int]
    recipes_changes: int = 0
    recipe_autosave_interval: int = 10000000
    items_changes: int = 0
    items_autosave_interval: int = 100000
    item_count: int = 0
    recipes_file: str = "cache/recipes.json"
    items_file: str = "cache/items.json"

    last_request: float = 0
    request_cooldown: float = 0.5  # 0.5s is safe for this API
    sleep_time: float = 1.0
    sleep_default: float = 1.0
    retry_exponent: float = 2.0
    local_only: bool = False
    trust_cache_nothing: bool = True  # Trust the local cache for "Nothing" results
    trust_first_run_nothing: bool = False  # Save as "Nothing" in the first run
    local_nothing_indication: str = "Nothing\t"  # Indication of untrusted "Nothing" in the local cache
    nothing_verification: int = 3  # Verify "Nothing" n times with the API
    nothing_cooldown: float = 5.0  # Cooldown between "Nothing" verifications
    connection_timeout: float = 5.0  # Connection timeout

    def __init__(self, init_state):
        self.recipes_cache = load_json(self.recipes_file)
        self.items_cache = load_json(self.items_file)
        self.items_id = bidict()

        max_id = max(self.items_cache.values(), key=lambda x: x[1])[1] if self.items_cache else 0
        self.item_count = max_id + 1

        for item, (emoji, elem_id, _) in self.items_cache.items():
            self.items_id[item] = elem_id

        for elem in init_state:
            self.add_item(elem, '', False)

        # Nothing is -1, local_nothing_indication is -2
        if "Nothing" not in self.items_cache:
            self.add_item("Nothing", '', False, -1)
        if self.local_nothing_indication not in self.items_cache:
            self.add_item(self.local_nothing_indication, '', False, -2)

        # Get rid of "nothing"s, if we don't trust "nothing"s.
        if not self.trust_cache_nothing:
            temp_set = frozenset(self.recipes_cache.items())
            for ingredients, result in temp_set:
                if result < 0:
                    self.recipes_cache[ingredients] = -2
            save_json(self.recipes_cache, self.recipes_file)

        # If we're not adding anything, we don't need to save
        if not self.local_only:
            atexit.register(lambda: save_json(self.recipes_cache, self.recipes_file))
            atexit.register(lambda: save_json(self.items_cache, self.items_file))

    def result_key(self, param1: str, param2: str) -> str:
        id1 = self.items_id[param1]
        id2 = self.items_id[param2]
        return str(pair_to_int(id1, id2))

    def add_item(self, item: str, emoji: str, first_discovery: bool = False, force_id: Optional[int] = None) -> int:
        if item not in self.items_cache:
            new_id = force_id if force_id is not None else self.item_count
            self.items_cache[item] = (emoji, new_id, first_discovery)
            self.items_id[item] = new_id
            self.items_changes += 1
            if not force_id:
                self.item_count += 1
        # Add missing emoji
        elif self.items_cache[item][0] == '' and emoji != '':
            print(f"Adding missing emoji {emoji} to {item}")
            self.items_cache[item] = (emoji, self.items_cache[item][1], self.items_cache[item][2])
            self.items_changes += 1

        if self.items_changes == self.items_autosave_interval:
            print("Autosaving items file...")
            save_json(self.items_cache, self.items_file)
            self.items_changes = 0
        return self.items_cache[item][1]

    def add_recipe(self, a: str, b: str, result: int):
        if self.result_key(a, b) not in self.recipes_cache or \
                self.recipes_cache[self.result_key(a, b)] != result:
            self.recipes_cache[self.result_key(a, b)] = result
            self.recipes_changes += 1
            if self.recipes_changes % self.recipe_autosave_interval == 0:
                print("Autosaving recipes file...")
                save_json(self.recipes_cache, self.recipes_file)

    def save_response(self, a: str, b: str, response: dict):
        result = response['result']
        emoji = response['emoji']
        new = response['isNew']
        print(f"New Recipe: {a} + {b} -> {result}")
        if new:
            print(f"FIRST DISCOVERY: {a} + {b} -> {result}")

        # Items - emoji, new discovery
        result_id = self.add_item(result, emoji, new)

        # Save as the fake nothing if it's the first run
        if result == "Nothing" and result not in self.recipes_cache and self.trust_first_run_nothing:
            result = self.local_nothing_indication
            result_id = self.items_id[result]

        # Recipe: A + B --> C
        self.add_recipe(a, b, result_id)

    def get_local(self, a: str, b: str) -> Optional[str]:
        if self.result_key(a, b) not in self.recipes_cache:
            return None
        result = self.recipes_cache[self.result_key(a, b)]
        result_str = self.items_id.inverse[result]

        # Didn't get the emoji. Useful for upgrading from a previous version.
        if result >= 0 and self.items_cache[result_str][0] == '':
            # print(f"Missing {result} in cache!")
            # print(f"{result}!!")
            return None
        return result_str

    # Adapted from analog_hors on Discord
    def combine(self, a: str, b: str) -> str:
        # Query local cache
        local_result = self.get_local(a, b)
        if local_result and local_result != self.local_nothing_indication:
            return local_result

        if self.local_only:
            return "Nothing"

        # print(f"Requesting {a} + {b}", flush=True)
        with self.request_pair(a, b) as result:
            r = json.load(result)
            # last_result = result.__dict__
            # last_result['headers'] = str(last_result['headers'].__dict__)
            # last_r = r

        nothing_count = 1
        while (local_result != self.local_nothing_indication and  # "Nothing" in local cache is long, long ago
               r['result'] == "Nothing" and  # Still getting "Nothing" from the API
               nothing_count < self.nothing_verification):  # We haven't verified "Nothing" enough times
            # Request again to verify, just in case...
            # Increases time taken on requests but should be worth it.
            # Also note that this can't be asynchronous due to all the optimizations I made assuming a search order
            time.sleep(self.nothing_cooldown)
            print("Re-requesting Nothing result...", flush=True)

            with self.request_pair(a, b) as result:
                r = json.load(result)
                # if (r['result'] != "Nothing") and (r['result'] != last_r['result']):
                #     print(f"WARNING: Inconsistent Nothing result: {last_r['result']} -> {r['result']}")
                #     # Save the full Nothing response to a different file
                #     save_nothing(a, b, {"Resp": last_result,
                #                         "Result": last_r})
                # last_result = result.__dict__
                # last_r = r

            nothing_count += 1

        self.save_response(a, b, r)
        return r['result']

    def request_pair(self, a: str, b: str):
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
                response = urlopen(request, timeout=self.connection_timeout)
                # raise Exception(f"HTTP {response.getcode()}: {response.reason}")
                # Reset exponential retrying
                self.sleep_time = self.sleep_default
                return response
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
