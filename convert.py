import json
import math
import os
import sqlite3

from recipe import result_key
from functools import cache


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
        if key in recipes1 and recipes2[key] != recipes1[key]:
            print(f"Conflict: {key} -> {recipes1[key]} vs {recipes2[key]}")
            if recipes1[key] == "Nothing\t" or (recipes1[key] == "Nothing" and recipes2[key] != "Nothing\t"):
                recipes1[key] = recipes2[key]
            print(f"Resolved: {key} -> {recipes1[key]}")

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
            continue  # Sorry, but re-request
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
        else:
            new_data[key] = {
                "text": key,
                "emoji": val[0],
                "discovered": val[1]
            }

    new_data_2 = data.copy()
    new_data_2['elements'] = []
    new_cnt = 0
    for val in new_data.values():
        new_data_2['elements'].append(val)
        if val['discovered']:
            new_cnt += 1
    print(new_cnt)
    # print(new_data_2)

    print(len(new_data_2['elements']))

    with open(new_file, "w", encoding='utf-8') as f:
        json.dump(new_data_2, f)


def count_recipes(file: str):
    with open(file, "r") as f:
        recipes = json.load(f)
    print(len(recipes))


def load_analog_hors_json(file_name):
    try:
        db = json.load(open(file_name, 'r'))
    except FileNotFoundError:
        return {}

    new_db = {}
    for key, value in db.items():
        for u, v in value:
            new_db[result_key(u, v)] = key
    return new_db


def convert_to_result_first(file_name):
    with open(file_name, "r") as f:
        recipes = json.load(f)
    new_recipes = {}
    for key, value in recipes.items():
        if value not in new_recipes:
            new_recipes[value] = [key]
        else:
            new_recipes[value].append(key)
    return new_recipes


def check_crafts(file: str, db: dict[str, str]):
    with open(file) as f:
        recipes = json.load(f)

    for key, value in recipes.items():
        if key not in db:
            continue
        if db[key] != value:
            key_str = key.replace('\t', ' + ')
            if "Nothing" == value or "Nothing" == db[key]:
                print(f"Conflict: {key_str} -> (stargazing) {value} vs (analog_hors) {db[key]}")


def load_best_recipe_book(file: str) -> list[set]:
    with open(file, "r", encoding='utf-8') as fin:
        lines = fin.readlines()

    recipes = [set() for _ in range(11)]
    cur_recipe = ""
    cur_recipe_depth = -1
    for line in lines:
        if line.strip() == "":
            output = cur_recipe.split(":")[1].strip()
            recipes[cur_recipe_depth].add(output)

            cur_recipe = ""
            cur_recipe_depth = -1
        else:
            cur_recipe += line
            cur_recipe_depth += 1
    sizes = [len(x) for x in recipes]
    print([sum(sizes[:i + 1]) for i in range(1, len(sizes))])
    return recipes


def check_recipes(file1, file2):
    recipe_book1 = load_best_recipe_book(file1)
    recipe_book2 = load_best_recipe_book(file2)
    for i in range(10):
        for v in recipe_book1[i]:
            if v not in recipe_book2[i]:
                print(f"Missing {v} at depth {i} in 2nd book")
        for v in recipe_book2[i]:
            if v not in recipe_book1[i]:
                print(f"Missing {v} at depth {i} in 1st book")


@cache
def limit(n: int) -> int:
    return n * (n + 1) // 2


init_list_size = 4


@cache
def ordered_total(cur_limit, cur_step, max_steps):
    if cur_step == max_steps:
        return 1
    if cur_limit >= limit(cur_step + init_list_size):
        return 0

    # print(f"Step {cur_step} with limit {cur_limit} has {s} recipes")
    return \
        ordered_total(cur_limit + 1, cur_step + 1, max_steps) + \
        ordered_total(cur_limit + 1, cur_step, max_steps)



def pair_to_int(i: int, j: int) -> int:
    if j < i:
        i, j = j, i
    return i + (j * (j + 1)) // 2


# I don't know sql. Github copilot automatically generated this, and I did some google searches for modifications.
def to_sqlite(file: str, output: str):
    input("Warning: this will delete the existing recipes database. Press Enter to continue.")
    conn = sqlite3.connect(output)
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS recipes''')
    c.execute('''CREATE TABLE recipes 
                 (u TEXT, 
                 v TEXT, 
                 result TEXT,
                 PRIMARY KEY (u, v))''')
    c.execute('''CREATE INDEX recipe_index ON recipes (u, v, result)''')
    with open(file, "r") as f:
        recipes = json.load(f)

    print("File loading complete")
    err_count = 0
    skip_count = 0
    for i, recipe in enumerate(recipes.items()):
        if i % 10000 == 0:
            print(f"Processed {i} of {len(recipes)} recipes")
            conn.commit()

        key, value = recipe
        u, v = key.split("\t")
        if "@" in u or "@" in v:
            skip_count += 1
            continue
        if u > v:
            u, v = v, u
        try:
            c.execute("INSERT INTO recipes (u, v, result) VALUES (?, ?, ?)", (u, v, value))
        except TypeError:
            err_count += 1
            # print(u, v)
            pass
    print("Committing...")
    conn.commit()
    conn.close()
    print(f"Done with {err_count} errors and {skip_count} skips.")


def items_to_sqlite(file: str, output: str):
    input("Warning: this will delete the existing items database. Press Enter to continue.")
    conn = sqlite3.connect(output)
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS items''')
    c.execute('''CREATE TABLE items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT, 
                 emoji TEXT, 
                 discovered BOOLEAN)''')  # Autoincrement because we don't want reuse of IDs, even if nothing is deleted
    c.execute('''CREATE INDEX item_name_index ON items (name)''')
    with open(file, "r") as f:
        items = json.load(f)
    i = 0
    items_list = items.items()
    # Put water fire wind & earth in front
    items_list = sorted(items_list, key=lambda x: x[0] not in ("Water", "Fire", "Wind", "Earth"))
    for key, value in items_list:
        c.execute("INSERT INTO items (id, name, emoji, discovered) VALUES (?, ?, ?, ?)", (i, key, value[0], value[1]))
        i += 1
    conn.commit()
    conn.close()


def merge_lapis(file1: str, file1_i: str, file2: str, output: str, output_i: str):
    try:
        recipes1 = json.load(open(file1, 'r'))
        items1 = json.load(open(file1_i, 'r'))
    except (IOError, ValueError):
        print("Could not load recipe files", flush=True)
        return

    items2 = {}
    with open(file2, "r", encoding="utf-8") as file:
        data = json.loads(file.read())
        elements = data["elements"]
        recipes = data["recipes"]
        for i, v in enumerate(recipes):
            if (i + 1) % 100000 == 0:
                print(f"Processed {i + 1} of {len(recipes)} recipes")
            if v is None:
                continue
            i1_index = math.floor(0.5 * (math.sqrt(8 * i + 1) - 1))
            i2_index = math.floor(i - (0.5 * i1_index * (i1_index + 1)))
            i1 = elements[i1_index]
            i2 = elements[i2_index]
            res = elements[v] if v != -1 else {"t": "Nothing", "e": None}

            key = result_key(i1["t"], i2["t"])
            res_str = res["t"]
            if "e" in res:
                res_emote = [res["e"], False]
            else:
                res_emote = None

            if key in recipes1:
                if recipes1[key] != res_str:
                    # key_pretty = key.replace('\t', ' + ')
                    # print(f"Conflict: {key_pretty} -> {recipes1[key]} vs {res_str}")
                    if recipes1[key] == "Nothing" or (recipes1[key] == "Nothing\t" and res_str != "Nothing"):
                        recipes1[key] = res_str
            else:
                recipes1[key] = res_str

            if res_str != "Nothing" and res_emote and res_str not in items2:
                items2[res_str] = res_emote

    for key, value in items2.items():
        if key in items1:
            pass
            # if items1[key] != res_emote:
            #     print(f"Conflict: {res_str} -> {items1[res_str]} vs {res_emote}")
            # Prefer mine!
        else:
            items1[key] = value

    save(recipes1, output)
    save(items1, output_i)


if __name__ == '__main__':
    # merge_lapis(
    #     "cache/recipes.json", "cache/items.json",
    #     "cache/data3.json",
    #     "cache/recipes_merged.json", "cache/items_merged.json"
    # )
    # items_to_sqlite("cache/items_merged.json", "cache/recipes.db")
    to_sqlite("cache/recipes_merged.json", "cache/recipes.db")
    # print(ordered_total(0, 0, 9))  # 26248400230
    # print(ordered_total(4, 0, 9))
    # new_recipes = convert_to_result_first("cache/relevant_recipes.json")
    # new_recipes_list = list(new_recipes.items())
    # new_recipes_list.sort(key=lambda x: len(x[1]), reverse=True)
    # for key, value in new_recipes_list[:20]:
    #     print(f"{key}: {len(value)}")
    # save(new_recipes, "cache/v9.4/recipes_v9.4 nothing pruning result first.json")
    # for recipe in new_recipes["Blue"]:
    #     u, v = recipe.split('\t')
    #     if u in ("Blue", "Cobalt") or v in ("Blue", "Cobalt"):
    #         continue
    #     print(f"{u} + {v}, ")

    # with open("cache/v9.4/recipes_v9.4 nothing pruning.json") as file:
    #     txt = file.read()
    #     print(txt.count("Nothing"))
    # count_recipes("../cache/relevant_recipes.json")
    # print(load_analog_hors_json("../cache/db.json"))
    # check_crafts("../cache/relevant_recipes.json", load_analog_hors_json("../cache/db.json"))
    # check_recipes("best_recipes_depth_9_v1.txt", "best_recipes_depth_9_v2.txt")
    # best_recipes_to_json("Depth 10/best_recipes.txt", "relevant_recipes.json")
    # remove_new("cache/items.json", "cache/emojis.json")
    # merge_recipe_files("cache/relevant_recipes.json", "cache/recipes_periodic.json", "cache/recipes_merged.json")
    # merge_items_files("cache/items.json", "cache/items_periodic.json", "cache/items_merged.json")
    # remove_plus_duplicates("../cache/recipes_merged.json", "../cache/recipes_trim.json")
    # change_delimiter("../cache/recipes_trim.json", "../cache/recipes_tab.json")
    # modify_save_file("infinitecraft_save.json", "cache/items.json", "infinitecraft_modified.json")
