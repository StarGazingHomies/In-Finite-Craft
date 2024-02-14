import json
import os
from recipe import result_key


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
            if recipes1[key] == "Nothing":
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


if __name__ == '__main__':
    # new_recipes = convert_to_result_first("cache/v9.4/recipes_v9.4 nothing pruning.json")
    # save(new_recipes, "cache/v9.4/recipes_v9.4 nothing pruning result first.json")
    # for recipe in new_recipes["Sisyphus"]:
    #     u, v = recipe.split('\t')
    #     print(f"{u} + {v}, ", end = "")

    # with open("cache/v9.4/recipes_v9.4 nothing pruning.json") as file:
    #     txt = file.read()
    #     print(txt.count("Nothing"))
    # count_recipes("../cache/recipes.json")
    # print(load_analog_hors_json("../cache/db.json"))
    # check_crafts("../cache/recipes.json", load_analog_hors_json("../cache/db.json"))
    check_recipes("best_recipes_depth_9_v1.txt", "best_recipes_depth_9_v2.txt")
    # best_recipes_to_json("../best_recipes.txt", "../relevant_recipes.json")
    # remove_new("../cache/items.json", "../cache/emojis.json")
    # merge_recipe_files("../cache/recipes.json", "../cache/recipes_search.json", "../cache/recipes_merged.json")
    # merge_items_files("../cache/items.json", "../cache/items_search.json", "../cache/items_merged.json")
    # remove_plus_duplicates("../cache/recipes_merged.json", "../cache/recipes_trim.json")
    # change_delimiter("../cache/recipes_trim.json", "../cache/recipes_tab.json")
    # modify_save_file("../infinitecraft.json", "../cache/items.json", "../infinitecraft_modified.json")
