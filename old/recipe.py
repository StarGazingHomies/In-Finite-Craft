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
recipes_changes: int = 0
autosaveInterval: int = 100
localOnly: bool = False
sleepTime: float = 1.0
retryExponent: float = 2.0
recipes_file = "../cache/recipes.json"
items_file = "../cache/items.json"


def result_key(param1, param2):
    if param1 > param2:
        return param2 + "\t" + param1
    return param1 + "\t" + param2


def save(dictionary, file_name):
    try:
        json.dump(dictionary, open(file_name, 'w'))
    except FileNotFoundError:
        print(f"Could not write to {file_name}! Trying to create a folder...", flush=True)
        try:
            os.mkdir("../cache")
            json.dump(dictionary, open(file_name, 'w'))
        except Exception as e:
            print(f"Could not create folder or write to file: {e}", flush=True)
            print(dictionary)
    except Exception as e:
        print(f"Unrecognized Error: {e}", flush=True)
        print(dictionary)


def add_item(result: str, emoji: str, discovery: bool) -> None:
    try:
        discoveries = json.load(open(items_file, 'r'))
    except (IOError, ValueError):
        discoveries = {}

    if result in discoveries:
        return

    discoveries[result] = (emoji, discovery)
    json.dump(discoveries, open(items_file, 'w'))


# Based on a stackoverflow post, forgot to write down which one
def persist_to_file(file_name, key_func):
    try:
        resultsCache = json.load(open(file_name, 'r'))
    except (IOError, ValueError):
        resultsCache = {}

    atexit.register(lambda: save(resultsCache, file_name))

    def decorator(func):
        def new_func(*args):
            global recipes_changes, autosaveInterval, localOnly

            if key_func(*args) not in resultsCache:
                # For viewing existing data only
                if localOnly:
                    return "Nothing"
                resultsCache[key_func(*args)] = func(*args)

                recipes_changes += 1
                if recipes_changes % autosaveInterval == 0:
                    print("Autosaving...")
                    save(resultsCache, file_name)

            return resultsCache[key_func(*args)]

        return new_func

    return decorator


# Adapted from analog_hors on Discord
@persist_to_file(recipes_file, result_key)
def combine(a: str, b: str) -> str:
    global lastRequest, requestCooldown, recipes_changes, sleepTime, retryExponent

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
                add_item(r['result'], r['emoji'], r['isNew'])
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


def merge_items_files(file1: str, file2: str, output: str):
    try:
        items1 = json.load(open(file1, 'r'))
        items2 = json.load(open(file2, 'r'))
    except (IOError, ValueError):
        print("Could not load items files", flush=True)
        return

    for key in items2:
        if key not in items1:
            items1[key] = items2[key]
        if items2[key][1]:
            items1[key] = items2[key]

    save(items1, output)


def best_recipes_to_json(recipe_file: str, output_file: str):
    try:
        with open(recipe_file, "r") as fin:
            lines = fin.readlines()
    except (IOError, ValueError):
        print("Could not load recipe file", flush=True)
        return

    relevant_recipes = {}
    for line in lines:
        if '->' in line:
            output = line.split("->")[1].strip()
            inputs = line.split("->")[0].strip()
            u, v = inputs.split("+")
            if output in relevant_recipes:
                if (u.strip(), v.strip()) not in relevant_recipes[output]:
                    relevant_recipes[output].append((u.strip(), v.strip()))
            else:
                relevant_recipes[output] = [(u.strip(), v.strip())]

    save(relevant_recipes, output_file)


def best_recipes_to_tsv(recipe_file: str, output_file: str):
    try:
        with open(recipe_file, "r") as fin:
            lines = fin.readlines()
    except (IOError, ValueError):
        print("Could not load recipe file", flush=True)
        return

    relevant_recipes = []
    for line in lines:
        if '->' in line:
            output = line.split("->")[1].strip()
            inputs = line.split("->")[0].strip()
            u, v = inputs.split("+")
            relevant_recipes.append([u.strip(), v.strip(), output])

    with open(output_file, "w") as fout:
        for recipe in relevant_recipes:
            fout.write(f"{recipe[0]}\t{recipe[1]}\t{recipe[2]}\n")


def request_items(recipe_file: str):
    file = json.load(open(recipe_file, 'r'))
    # has_cinnamon = False
    for key, value in file.items():
        # if key == "Cinnamon":
        #     has_cinnamon = True
        # if not has_cinnamon:
        #     continue
        print(key)
        combine(value[0][0], value[0][1])


def remove_new(items_file: str, new_items_file: str):
    file = json.load(open(items_file, 'r'))
    new = {}
    for key, value in file.items():
        new[key] = value[0]
    json.dump(new, open(new_items_file, 'w'))


def recipe_to_csv(recipe_file: str, new_file: str):
    file = json.load(open(recipe_file, 'r'))
    with open(new_file, "w") as f:
        for items, result in file.items():
            try:
                u, v = items.split(" + ")
                u = u.replace("+", "")
                v = v.replace("+", "")
            except ValueError:
                print(items)
            f.write(f"{u}\t{v}\t{result}\n")


def remove_plus_duplicates(recipe_file: str, new_file: str):
    with open(recipe_file, "r") as f:
        recipes = json.load(f)
    new_recipes = {}
    for key, value in recipes.items():
        try:
            u, v = key.split(" + ")
            u = u.replace("+", " ")
            v = v.replace("+", " ")
        except ValueError:
            continue
        new_recipes[result_key(u, v)] = value
    with open(new_file, "w") as f:
        json.dump(new_recipes, f)


def change_delimiter(file: str, new_file: str):
    with open(file, "r") as f:
        recipes = json.load(f)

    new_recipes = {}
    for key, value in recipes.items():
        if key.count(" + ") > 1:
            continue # Sorry, but re-request
        u, v = key.split(" + ")
        new_recipes[u + "\t" + v] = value

    with open(new_file, "w") as f:
        json.dump(new_recipes, f)


def modify_save_file(file: str, items_file: str, new_file: str):
    with open(file, "r", encoding='utf-8') as f:
        data = json.load(f)
    with open(items_file, "r", encoding='utf-8') as f:
        items = json.load(f)

    elements = data['elements']
    new_data = {}
    for i in elements:
        print(i, i['text'])
        new_data[i['text']] = i
    for key, val in items.items():
        if key in new_data:
            new_data[key]['discovered'] = val[1] or new_data[key]['discovered']
        new_data[key] = {
            "text": key,
            "emoji": val[0],
            "discovered": val[1]
        }

    new_data_2 = {'elements': []}
    for val in new_data.values():
        new_data_2['elements'].append(val)
    print(new_data_2)

    with open(new_file, "w", encoding='utf-8') as f:
        json.dump(new_data_2, f)


def count_recipes(file: str):
    with open(file, "r") as f:
        recipes = json.load(f)
    print(len(recipes))


def combine_optimally(current: set[str], future: list[list[set[str]]]):
    pass


if __name__ == '__main__':
    count_recipes("../cache/recipes.json")
    # best_recipes_to_json("../best_recipes_depth_9.txt", "../relevant_recipes.json")
    # remove_new("../cache/items.json", "../cache/emojis.json")
    # merge_recipe_files("../cache/recipes.json", "../cache/recipes_search.json", "../cache/recipes_merged.json")
    # merge_items_files("../cache/items.json", "../cache/items_search.json", "../cache/items_merged.json")
    # remove_plus_duplicates("../cache/recipes_merged.json", "../cache/recipes_trim.json")
    # change_delimiter("../cache/recipes_trim.json", "../cache/recipes_tab.json")
    # modify_save_file("../infinitecraft.json", "../cache/items.json", "../infinitecraft_modified.json")
