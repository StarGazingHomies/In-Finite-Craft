import asyncio
import json
import math
import os
from functools import cache
from typing import Optional

import aiohttp
import bidict

import recipe


def result_key(a: str, b: str) -> str:
    if a > b:
        a, b = b, a
    return a + "\t" + b


def save(dictionary, file_name):
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


def remove_first_discoveries(savefile: str, new_savefile: str):
    with open(savefile, "r", encoding='utf-8') as f:
        data = json.load(f)

    elements = data['elements']
    for val in elements:
        if val['discovered']:
            val['discovered'] = False
    data["elements"] = elements

    with open(new_savefile, "w", encoding='utf-8') as f:
        json.dump(data, f)


def load_save_file(file: str):
    with open(file, "r", encoding='utf-8') as f:
        data = json.load(f)
    return data


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


def pair_to_int(i: int, j: int) -> int:
    if j < i:
        i, j = j, i
    return i + (j * (j + 1)) // 2


def convert_to_id(recipes_file: str, items_file: str, output_recipes: str, output_items: str):
    with open(recipes_file, "r") as f:
        recipes = json.load(f)
    with open(items_file, "r") as f:
        items = json.load(f)

    new_items = {"Water": ["", 0, False],
                 "Fire": ["", 1, False],
                 "Wind": ["", 2, False],
                 "Earth": ["", 3, False]}
    item_ids: bidict.bidict[str, int] = bidict.bidict()
    item_ids["Nothing\t"] = -2
    item_ids["Nothing"] = -1
    item_ids["Water"] = 0
    item_ids["Fire"] = 1
    item_ids["Wind"] = 2
    item_ids["Earth"] = 3
    new_recipes = {}
    items_count = 4
    for item in items:
        if item in ("Nothing", "Nothing\t"):
            continue
        if item in new_items:
            original_id = new_items[item][1]
            new_items[item] = [items[item][0], original_id, items[item][1]]
            continue

        new_items[item] = [items[item][0], items_count, items[item][1]]
        item_ids[item] = items_count
        items_count += 1

    def new_result_key(a: str, b: str) -> str:
        id1 = item_ids[a]
        id2 = item_ids[b]
        return str(pair_to_int(id1, id2))

    for key, value in recipes.items():
        u, v = key.split("\t")
        if u in ("Nothing", "Nothing\t") or v in ("Nothing", "Nothing\t"):
            continue
        if u not in item_ids:
            new_items[u] = ["", items_count, False]
            item_ids[u] = items_count
            items_count += 1
        if v not in item_ids:
            new_items[v] = ["", items_count, False]
            item_ids[v] = items_count
            items_count += 1
        if value not in item_ids:
            new_items[value] = ["", items_count, False]
            item_ids[value] = items_count
            items_count += 1
        # print(u, v, value, u in new_items, v in new_items, value in new_items)
        # if value == "Nothing" or value == "Nothing\t":
        #     print(item_ids[value])

        new_recipes[new_result_key(u, v)] = item_ids[value]

    with open(output_items, "w", encoding='utf-8') as f:
        json.dump(new_items, f, ensure_ascii=False)

    with open(output_recipes, "w", encoding='utf-8') as f:
        json.dump(new_recipes, f, ensure_ascii=False)


def merge_lapis(file2: str):
    recipe_handler = recipe.RecipeHandler(("Water", "Fire", "Wind", "Earth"))

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
            res = elements[v] if v != -1 else {"t": "Nothing\t", "e": ''}

            res_str = res["t"]
            if "e" in res:
                res_emote = res["e"]
            else:
                res_emote = None

            # print(f"Adding {i1['t']} + {i2['t']} -> {res_str} with emote {res_emote}")
            # input()
            result_id = recipe_handler.add_item(res_str, res_emote, False)
            recipe_handler.add_recipe(i1["t"], i2["t"], result_id)


def merge_old(file_r: str, file_i: str):
    recipe_handler = recipe.RecipeHandler(("Water", "Fire", "Wind", "Earth"))

    with open(file_r, "r") as f:
        recipes = json.load(f)
    with open(file_i, "r") as f:
        items = json.load(f)

    for key, value in items.items():
        recipe_handler.add_item(key, value[0], value[1])

    for key, value in recipes.items():
        u, v = key.split("\t")
        r = recipe_handler.add_item(value, "", False)
        recipe_handler.add_recipe(u, v, r)


def get_results_for(results: list[str]):
    recipe_handler = recipe.RecipeHandler(("Water", "Fire", "Wind", "Earth"))
    for result in results:
        print(recipe_handler.get_local_results_for(result))


def get_recipes_using(elements: list[str]):
    recipe_handler = recipe.RecipeHandler(("Water", "Fire", "Wind", "Earth"))
    for element in elements:
        print(recipe_handler.get_local_results_using(element))


@cache
def limit(n: int) -> int:
    return n * (n + 1) // 2


@cache
def ordered_total(cur_limit, cur_step, max_steps, init_list_size=4):
    if cur_step == max_steps:
        return 1
    if cur_limit >= limit(cur_step + init_list_size):
        return 0
    # if cur_step == max_steps - 1 and cur_step != 0:
    #     return limit(cur_step + init_list_size + 1) - limit(cur_step + init_list_size)

    # print(f"Step {cur_step} with limit {cur_limit} has {s} recipes")
    return \
            ordered_total(cur_limit + 1, cur_step + 1, max_steps, init_list_size) + \
            ordered_total(cur_limit + 1, cur_step, max_steps, init_list_size)


def ordered_total_from_current(current_state: list[int]):
    init_list_size = 0
    count = 0
    for i, val in enumerate(current_state):
        if val == -1:
            init_list_size = i + 1
            continue

        print(f"{val} + 1, {i - init_list_size}, {len(current_state) - init_list_size}, {init_list_size}")
        count += ordered_total(val + 1, i - init_list_size, len(current_state) - init_list_size, init_list_size)
    return count


def get_items(file: str):
    with open(file, "r", encoding="utf-8") as f:
        items = json.load(f)
    return items


def alpha_3_tmp(file: str, new_file: str):
    exists = set()
    for i in range(26):
        first_letter = chr(ord('A') + i)
        with open("3 letter spreadsheet/" + first_letter + ".csv", "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            values = line.split(",")
            for i in range(0, len(values), 2):
                if values[i + 1].strip() != "Yes":
                    continue

                exists.add(values[i].strip().lower())

    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_result = []
    include_next_line = False
    count = 0

    current_result = []
    for line in lines:
        if line.strip() == "" and include_next_line:
            include_next_line = False
            new_result.append(current_result)
            print(current_result)

        if include_next_line:
            current_result[1] += line

        word = line.split(":")[0].strip().lower()
        if line.count(":") == 1 and len(word) == 3 and all([ord('a') <= ord(x) <= ord('z') for x in word.lower()]):
            # and word not in exists:
            result = line.split(":")[0].strip()
            current_result = [result, ""]
            current_result[1] += f"{result}: "
            include_next_line = True
            count += 1

    new_result.sort()

    with open(new_file, "w", encoding="utf-8") as f:
        f.write("\n".join([x[1] for x in new_result]))


def convert_to_savefile(savefile: str, items_file: str, recipes_file: Optional[str] = None):
    with open(items_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    items_reverse = {v[1]: [v[0], k, v[2]] for k, v in items.items()}

    item_count = 0
    first_discoveries_count = 0
    # ITEM_LIMIT = int(1e6)
    new_data = {"elements": [], "recipes": {}, "darkMode": True}
    for key, value in items.items():
        new_data["elements"].append({
            "text": key,
            "emoji": value[0],
            "discovered": value[2]
        })
        item_count += 1
        if value[2]:
            first_discoveries_count += 1
        # if item_count > ITEM_LIMIT:
        #     break
    print(f"Processed {item_count} items")

    recipes_limit = 6000000
    if recipes_file:
        with open(recipes_file, "r", encoding="utf-8") as f:
            recipes = json.load(f)
        i = 0
        for key, value in recipes.items():
            i += 1
            if i % 100000 == 0:
                print(f"Processed {i} of {len(recipes)} recipes")
            if i > recipes_limit:
                break
            if value < 0:
                continue
            key = int(key)
            value = int(value)
            u, v = recipe.int_to_pair(key)
            u_item = items_reverse[u]
            v_item = items_reverse[v]
            result = items_reverse[value][1]

            u_formatted = {
                "text": u_item[1],
                "emoji": u_item[0]
            }
            v_formatted = {
                "text": v_item[1],
                "emoji": v_item[0]
            }

            craft_formatted = [u_formatted, v_formatted]

            if result in new_data["recipes"]:
                new_data["recipes"][result].append(craft_formatted)
            else:
                new_data["recipes"][result] = [craft_formatted]

    with open(savefile, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False)


def add_to_recipe_handler(items_file: str, recipes_file: str):
    with open(items_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    with open(recipes_file, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    rh = recipe.RecipeHandler(("Water", "Fire", "Wind", "Earth"))

    items_reverse = {v[1]: [v[0], k, v[2]] for k, v in items.items()}
    items_reverse[-1] = ["", "Nothing", False]
    items_reverse[-2] = ["", "Nothing\t", False]

    for key, value in items.items():
        rh.add_item(key, value[0], value[2])

    i = 0
    for key, value in recipes.items():
        i += 1
        if i % 100000 == 0:
            print(f"Processed {i} of {len(recipes)} recipes")
        # if value < 0:
        #     continue
        key = int(key)
        value = int(value)
        u, v = recipe.int_to_pair(key)
        u_item = items_reverse[u][1]
        v_item = items_reverse[v][1]
        result = items_reverse[value][1]
        if u_item > v_item:
            u_item, v_item = v_item, u_item  # Swap to ensure u < v
        rh.add_recipe(u_item, v_item, result)


def filter_results(result: str) -> bool:
    # 3 letter search
    # if len(result) != 3:
    #     return False
    # for char in result.lower():
    #     if not ord("a") <= ord(char) <= ord("z"):
    #         return False

    return True


def generate_single_best_recipe(output_file: str):
    try:
        with open("persistent.json", "r", encoding="utf-8") as file:
            last_state_json = json.load(file)
        best_recipes = last_state_json["BestRecipes"]
    except FileNotFoundError:
        best_recipes = {}

    MAX_DEPTH = 11
    recipe_list = [[] for _ in range(MAX_DEPTH + 1)]
    for key, value in best_recipes.items():
        if filter_results(key):
            recipe_list[len(value[0])].append((key, value[0]))

    print("Recipes at each depth: ", [len(x) for x in recipe_list])
    print("Total recipes at each depth: ",
          [sum([len(x) for x in recipe_list[:i + 1]]) for i in range(1, len(recipe_list))])

    # visited = set()
    # count: int = 0
    # with open(output_file, "w", encoding="utf-8") as f:
    #     for i in range(MAX_DEPTH + 1):
    #         for key, value in recipe_list[i]:
    #             # if len(key) != 3 or not all([ord('a') <= ord(x) <= ord('z') for x in key.lower()]):
    #             #     continue
    #             # if key.lower() in visited:
    #             #     continue
    #             # visited.add(key.lower())
    #             value_str = "\n".join([f"{x[0]} + {x[1]} -> {x[2]}" for x in value])
    #             f.write(f"{count+1}: {key}:\n{value_str}\n\n")
    #             count += 1
    with open(output_file, "w", encoding="utf-8") as f:
        for i in range(10):
            for key, value in recipe_list[i]:
                # if len(key) != 3 or not all([ord('a') <= ord(x) <= ord('z') for x in key.lower()]):
                #     continue
                # if key.lower() in visited:
                #     continue
                # visited.add(key.lower())
                f.write(f"{key}\n")


def generate_json(output_file: str):
    try:
        with open("persistent.json", "r", encoding="utf-8") as file:
            last_state_json = json.load(file)
        best_recipes = last_state_json["BestRecipes"]
    except FileNotFoundError:
        best_recipes = {}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(best_recipes, f, ensure_ascii=False)


def parse_pbpbpb_cancer_list(file: str) -> list[str]:
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cancer_list = []
    for line in lines:
        starting_bit = line.split('[')[0]
        print(starting_bit)
        print(starting_bit.split(' ')[:-4])
        cancer_list.append(" ".join(starting_bit.split(' ')[:-4]))
        print(cancer_list[-1])

    return cancer_list


cancers = ['Swamp Thing', 'Werewolf', 'Venus Flytrap', 'Flying Fish', 'Giant Venus Flytrap', 'Sharknado', 'Dust Bunny', 'Muddy Wine', 'Steam Engine', 'Dandelion Wine', 'Dust Bowl', 'Steampunk Pirate', 'Dandelion Patch', 'Zombie King', 'Were-tree', 'Rocky Mountains', 'Monster Truck', 'Tornado', 'Dusty Springfield', 'Flat Earth', 'Fire Trap', 'Loch Ness Monster', 'Piranha Plant', 'Giant Dandelion', 'Flying Car', 'Funnel Cake', 'Steam Punk', 'Paper Boat', 'Mountain Dew', 'Pickle Rick', 'Hangover', 'Flying Sushi', 'Muddy Teapot', 'Balsamic Vinegar', 'Steamboat', 'Drunken Dragon', 'Fire Breathing Dragon', 'Flying Cow', 'Swamp Venus', 'Netherite Sword', 'Steam Robot', 'Muddy Sushi', 'Godzilla', 'Dust Storm', 'Poison Ivy', 'Darth Vader', 'Smoky Mountains', 'Chocolate Milk', 'Tsunami', 'Glasser', 'Flying Shark', 'Burning Man', 'Flying Frog', 'Soggy Toast', 'Hot Air Balloon', 'Niagara Falls', 'Wish Upon A Star', 'Mr. Potato Head', 'Swampasaurus', 'Zephyr Train', 'SpongeBob', 'Surf and Turf', 'Surfboard', 'Tea Party', 'Boiling Frog', 'Duck Sauce', 'Dandelion', 'Mecha Dragon', 'Flying Spaghetti Monster', 'Muddy Wind Farm', 'Piggyback', 'Pterodactyl', 'Surfing', 'Birthday Cake', 'Flying Plant', 'Flying Starfish', 'Beef Bourguignon', 'Dandelion Tea', 'Mars Rover', 'Venus Fly Trap', 'Gone With The Wind', 'Thunderbird', 'Flying Pig', 'Big Trouble in Little China', 'Amphibious Car', 'Cheese Wheel', 'Great Wall of China', 'Mudslide', 'Flying Soup', 'Dandelion Soup', 'Kite Surfing', 'Unicorn', 'Sperm Whale', 'Jellyfish', 'Amphicar', 'Chicken Noodle Soup', 'Mermaid', 'Water Rocket', 'Rainbow Trout', 'Lawnmower']
# PBPBPB: I'm just checking if first and last 2 tokens of an A or B are the same as the resulting element C.


async def try_cancer_combinations(rh: recipe.RecipeHandler, session: aiohttp.ClientSession, word1: str) -> list[tuple[str, str, str]]:
    results = []
    for word2 in cancers:
        result = await rh.combine(session, word1, word2)
        # print(f"Found {word1} + {word2} -> {result}")
        if word1.lower() in result.lower():
            # print(f"Found {word1} + {word2} -> {result}")
            results.append((word1, word2, result))
    return results


async def try_in_a_combinations(rh: recipe.RecipeHandler, session: aiohttp.ClientSession, wordlist: list[str]) -> list[tuple[str, str]]:
    results = []
    for word in wordlist:
        # print(word)
        result = await rh.combine(session, "In A", word)
        results.append((word, result))
        print(f"In A + {word} -> {result}")
        with open("in_a_results.txt", "a") as f:
            f.write(f"In A + {word} -> {result}\n")
    return results


async def main():
    async with aiohttp.ClientSession() as session:
        rh = recipe.RecipeHandler(("Water", "Fire", "Wind", "Earth"))
        # await rh.combine(session, "\"littleshy\"", "Delete the Quotation Marks")
        # await rh.combine(session, "\"littleshy\"", "Delete the Quotation Mark")
        # await rh.combine(session, "#littleshy", "Delete the Hyphen")
        with open("depth_9_items.txt", "r") as f:
            lines = f.readlines()
        items = [x.strip() for x in lines]
        await try_in_a_combinations(rh, session, items)
        # await rh.combine(session, "#TotallyNotFakeElement2", "With Spaces")
        # await rh.combine(session, "#IAmNotCreative", "With Spaces")
        # word1 = "Baby"
        # word2 = "Cake"
        # combined = f"{word1} {word2}"
        # show_combos = await try_cancer_combinations(rh, session, word1)
        # # print(show_combos)
        # stopper_combos = await try_cancer_combinations(rh, session, word2)
        # # print(stopper_combos)
        # for u1, u2, u in show_combos:
        #     for v1, v2, v in stopper_combos:
        #         result = await rh.combine(session, u, v)
        #         # print(f"Found {u} + {v} -> {result}")
        #         if combined in result:
        #             print(f"Found {combined} with {u} ({u2}) + {v} ({v2}) -> {result}")


if __name__ == '__main__':
    pass
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    # generate_single_best_recipe("best_recipes.txt")
    # generate_json("all_best_recipes_depth_11.json")
    # add_to_recipe_handler("cache/items.json", "cache/recipes.json")
    # convert_to_savefile("infinitecraft_large_with_partial_recipes.json", "cache/items.json", "cache/recipes.json")
    # cancers = parse_pbpbpb_cancer_list("top_cancer_a.txt")
    # print(cancers)
    # d = load_save_file("infinitecraft_main_old_save_58k.json")
    # print(len(d["elements"]))
    # for e in d["elements"]:
    #     if "mirror" in e["text"].lower():
    #         print(e)
    # print(d["recipes"]["The Ticket Masters"])
    # print(d["recipes"]["Ticket Master"])
    # print(d["recipes"]["Mirror Master"])
    # remove_first_discoveries("infinitecraft_with_tools.json", "infinitecraft_no_fd.json")
    # get_results_for(["Obama"])
    # print(ordered_total(0, 0, 2))
    # alpha_3_tmp("best_recipes_three_letter.txt", "three_letters.txt")
    # i = get_items("cache/items.json")
    # three_letter = set()
    # counter = 0
    # discoveries = 0
    # first_discoveries = 0
    # for key, value in i.items():
    #     discoveries += 1
    #     if value[2]:
    #         first_discoveries += 1
    # if key.isalnum() and len(key) == 3 and key.lower() not in three_letter:
    #     three_letter.add(key.lower())
    #     if value[2]:
    #         print(key, value)
    #         counter += 1
    # print(discoveries, first_discoveries)
    # pass
    # merge_old("cache/recipes_o.json", "cache/items_o.json")
    # get_recipes_using(["Ab", "AB", "Ac", "AC", "Lord of the Rings", "Lord Of The Rings"])
    # print(ordered_total(0, 0, 9))  # 26248400230
    # print(ordered_total(0, 0, 10))  # 667110736190
    # print(ordered_total(0, 0, 11))  # 18527307559355
    # print(ordered_total(6, 0, 11))  # 3204682702923
    # print(ordered_total(7, 1, 11))  # 1144649542152
    # print(ordered_total(11, 2, 11))  # 146909202170
    # print(ordered_total(16, 3, 11))  # 14715058266
    # print(ordered_total_from_current([-1, -1, -1, -1, 5, 6, 10, 15, 33, 40, 42, 50, 72, 88, 99]))
    # print(ordered_total_from_current([-1, -1, -1, -1, 5, 6, 10, 15, 33, 40, 42, 50, 72, 88, 99]) / ordered_total(0, 0, 11))
    # for i in range(15):
    #     print(i, ordered_total(0, 0, i))
    # other_save = json.load(open("infinitecraft (2).json", 'r', encoding='utf-8'))
    # print(len(other_save["elements"]))
    # counter = 0
    # for v in other_save["elements"]:
    #     if v["discovered"]:
    #         counter += 1
    # print(counter)
    # convert_to_id("cache/recipes.json", "cache/items.json", "cache/recipes_id.json", "cache/items_id.json")
