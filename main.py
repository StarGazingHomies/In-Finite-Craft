import atexit
import os
import sys
import time
from functools import cache
from typing import Optional
from urllib.parse import quote_plus

import json
import asyncio
import aiohttp

import recipe

# import tracemalloc


init_state: tuple[str, ...] = ("Water", "Fire", "Wind", "Earth")

# For people who want to start with a lot more things
elements = ["Hydrogen", "Helium", "Lithium", "Beryllium", "Boron", "Carbon", "Nitrogen", "Oxygen", "Fluorine", "Neon",
            "Sodium", "Magnesium", "Aluminium", "Silicon", "Phosphorus", "Sulfur", "Chlorine", "Argon", "Potassium",
            "Calcium", "Scandium", "Titanium", "Vanadium", "Chromium", "Manganese", "Iron", "Cobalt", "Nickel",
            "Copper", "Zinc", "Gallium", "Germanium", "Arsenic", "Selenium", "Bromine", "Krypton", "Rubidium",
            "Strontium", "Yttrium", "Zirconium", "Niobium", "Molybdenum", "Technetium", "Ruthenium", "Rhodium",
            "Palladium", "Silver", "Cadmium", "Indium", "Tin", "Antimony", "Tellurium", "Iodine", "Xenon", "Cesium",
            "Barium", "Lanthanum", "Cerium", "Praseodymium", "Neodymium", "Promethium", "Samarium", "Europium",
            "Gadolinium", "Terbium", "Dysprosium", "Holmium", "Erbium", "Thulium", "Ytterbium", "Lutetium",
            "Hafnium", "Tantalum", "Tungsten", "Rhenium", "Osmium", "Iridium", "Platinum", "Gold", "Mercury",
            "Thallium", "Lead", "Bismuth", "Polonium", "Astatine", "Radon", "Francium", "Radium", "Actinium",
            "Thorium", "Protactinium", "Uranium", "Neptunium", "Plutonium", "Americium", "Curium", "Berkelium",
            "Californium", "Einsteinium", "Fermium", "Mendelevium", "Nobelium", "Lawrencium", "Rutherfordium",
            "Dubnium", "Seaborgium", "Bohrium", "Hassium", "Meitnerium", "Darmstadtium", "Roentgenium", "Copernicium",
            "Nihonium", "Flerovium", "Moscovium", "Livermorium", "Tennessine", "Oganesson"]

letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
           "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
           "U", "V", "W", "X", "Y", "Z"]

rearrange_words = ["Anagram", "Reverse", "Opposite", "Scramble", "Rearrange", "Palindrome", "Not"]

# If capitalization matters...
# letters2 = ["AA", "Ab", "Ac", "Ad", "AE", "AF", "Ag", "AH", "Ai", "Aj", "AK", "Al", "Am", "An", "AO", "AP", "AQ", "Ar", "As", "At", "Au", "Av", "AW", "Ax", "AY", "Az",
#             "BA", "Bb", "BC", "BD", "Be", "BF", "BG", "BH", "Bi", "BJ", "BK", "BL", "BM", "Bn", "BO", "BP", "BQ", "BR", "BS", "BT", "BU", "BV", "BW", "Bx", "BY", "Bz"]
# Not going to continue for now.

letters2 = []
for l1 in letters:
    for l2 in letters:
        letters2.append(l1 + l2)

# init_state = tuple(list(init_state) + elements + ["Periodic Table",])
# init_state = tuple(list(init_state) + letters + letters2)
recipe_handler = recipe.RecipeHandler(init_state)
depth_limit = 11

best_recipes: dict[str, list[list[tuple[str, str, str]]]] = dict()
visited = set()
best_depths: dict[str, int] = dict()
best_recipes_file: str = "best_recipes.txt"
all_best_recipes_file: str = "all_best_recipes_depth_10_filtered.json"
case_sensitive: bool = True
three_letter_search: bool = False
allow_starting_elements: bool = False
resume_last_run: bool = True
last_game_state: Optional['GameState'] = None
new_last_game_state: Optional['GameState'] = None
autosave_interval = 500     # Save every 500 new visited elements
autosave_counter = 0


@cache
def int_to_pair(n: int) -> tuple[int, int]:
    if n < 0:
        return -1, -1
    j = 0
    while n > j:
        n -= j + 1
        j += 1
    i = n
    return i, j


@cache
def pair_to_int(i: int, j: int) -> int:
    if j < i:
        i, j = j, i
    return i + (j * (j + 1)) // 2


@cache
def limit(n: int) -> int:
    return n * (n + 1) // 2


class GameState:
    items: list[str]
    state: list[int]
    visited: list[set[str]]
    used: list[int]
    children: set[str]

    def __init__(self, items: list[str], state: list[int], children: set[str], used: list[int]):
        self.state = state
        self.items = items
        self.children = children
        self.used = used

    def __str__(self):
        steps = [self.items[-1] + ":"]
        for i in range(len(self.state)):
            left, right = int_to_pair(self.state[i])
            if (left < 0) or (right < 0):
                continue
            steps.append(f"{self.items[left]} + {self.items[right]} -> {self.items[i]}")
        return "\n".join(steps)

    def __len__(self):
        return len(self.state)

    def __eq__(self, other):
        return self.state == other.state

    def __lt__(self, other):
        for i in range(min(len(self.state), len(other.state))):
            if self.state[i] < other.state[i]:
                return True
            elif self.state[i] > other.state[i]:
                return False
            else:
                continue
        return False  # If it's the same starting elements, we still need to explore this state

    def __hash__(self):
        return hash(str(self.state))

    def to_list(self) -> list[tuple[str, str, str]]:
        l: list[tuple[str, str, str]] = []
        for i in range(len(self.state)):
            left, right = int_to_pair(self.state[i])
            if (left < 0) or (right < 0):
                continue
            l.append((self.items[left], self.items[right], self.items[i]))
        return l

    async def child(self, session: aiohttp.ClientSession, i: int) -> Optional['GameState']:
        # Invalid indices
        if i <= self.tail_index() or i >= limit(len(self)):
            return None

        # Craft the items
        u, v = int_to_pair(i)
        craft_result = await recipe_handler.combine(session, self.items[u], self.items[v])

        # Invalid crafts, items we already have, or items that can be crafted earlier are ignored.
        if (craft_result is None or
                craft_result == "Nothing" or
                (not allow_starting_elements and craft_result in self.items) or
                (allow_starting_elements and
                 (craft_result == self.items[u] or craft_result == self.items[v] or
                  (craft_result in self.items and self.used[self.items.index(craft_result)] != 0))) or
                # Even though we are looking for results in the original list, we still
                # Don't want to use the result itself in any craft
                craft_result in self.children):
            return None

        # Make sure we never craft this ever again
        self.children.add(craft_result)

        # Construct the new state
        new_state = self.state + [i, ]
        new_items = self.items + [craft_result, ]
        new_used = self.used.copy()
        new_used.append(0)
        new_used[u] += 1
        new_used[v] += 1
        return GameState(new_items, new_state, self.children.copy(), new_used)

    def unused_items(self) -> list[int]:
        return [i for i in range(len(init_state), len(self.items)) if 0 == self.used[i]]

    def items_set(self) -> frozenset[str]:
        return frozenset(self.items)

    def tail_item(self) -> str:
        return self.items[-1]

    def tail_index(self) -> int:
        return self.state[-1]


def process_node(state: GameState):
    global autosave_counter

    if three_letter_search:
        if len(state.tail_item()) != 3 or not state.tail_item().isalpha():
            return

    tail_item = state.tail_item()
    if not case_sensitive:
        tail_item = tail_item.upper()

    if tail_item not in visited:
        visited.add(tail_item)
        autosave_counter += 1
        if autosave_counter >= autosave_interval:
            autosave_counter = 0
            save_last_state()
        # Still write to best_recipes.txt file
        # with open(best_recipes_file, "a", encoding="utf-8") as file:
        #     file.write(f"{len(visited)}: {state}\n\n")

    # Multiple recipes for the same item at same depth
    depth = len(state) - len(init_state)
    if state.tail_item() not in best_depths:
        best_depths[state.tail_item()] = depth
        best_recipes[state.tail_item()] = [state.to_list(), ]
    elif depth == best_depths[state.tail_item()]:
        best_recipes[state.tail_item()].append(state.to_list())


# Depth limited search
async def dls(session: aiohttp.ClientSession, state: GameState, depth: int) -> int:
    global last_game_state, new_last_game_state
    """
    Depth limited search
    :param session: The session to use
    :param state: The current state
    :param depth: The depth remaining
    :return: The number of states processed
    """
    # Resuming
    if last_game_state is not None and len(last_game_state) >= len(state) + depth and state < last_game_state:
        # print(f"Skipping state {state}")
        return 0

    if depth == 0:  # We've reached the end of the crafts, process the node
        new_last_game_state = state
        process_node(state)
        return 1

    # 30 char limit, according to PB and laurasia
    if len(state.tail_item()) > recipe.WORD_COMBINE_CHAR_LIMIT:
        return 0

    # Even if we allowed starting element results, we're still not going to continue from such a state
    if allow_starting_elements and state.tail_item() in state.items[:-1]:
        return 0

    count = 0  # States counter
    unused_items = state.unused_items()  # Unused items
    if len(unused_items) > depth + 1:  # Impossible to use all elements, since we have too few crafts left
        return 0
    elif len(unused_items) > depth:  # We must start using unused elements NOW.
        for j in range(len(unused_items)):  # For loop ordering is important. We want increasing pair_to_int order.
            for i in range(j):  # i != j. We have to use two for unused_items to decrease.
                child = await state.child(session, pair_to_int(unused_items[i], unused_items[j]))
                if child is not None:
                    count += await dls(session, child, depth - 1)
        return count
    else:
        lower_limit = 0
        if depth == 1 and state.tail_index() != -1:  # Must use the 2nd last element, if it's not a default item.
            lower_limit = limit(len(state) - 1)

        for i in range(lower_limit, limit(len(state))):  # Regular ol' searching
            child = await state.child(session, i)
            if child is not None:
                count += await dls(session, child, depth - 1)

        return count


async def iterative_deepening_dfs(session: aiohttp.ClientSession):
    # Clear best recipes file
    if not resume_last_run:
        open(best_recipes_file, "w").close()

    curDepth = 1
    start_time = time.perf_counter()
    if last_game_state is not None:
        curDepth = len(last_game_state) - len(init_state)
        print(f"Resuming from depth {curDepth}")
        print(last_game_state.state)

    while True:
        prev_visited = len(visited)
        print(await dls(
            session,
            GameState(
                list(init_state),
                [-1 for _ in range(len(init_state))],
                set(),
                [0 for _ in range(len(init_state))]
            ),
            curDepth))

        print(f"{curDepth}   {len(visited)}     {time.perf_counter() - start_time:.4f}")
        if curDepth >= depth_limit > 0:
            break
        # Only relevant for local files - if exhausted the outputs, stop
        if len(visited) == prev_visited and curDepth > len(last_game_state) - len(init_state):
            break
        curDepth += 1


async def main():
    # tracemalloc.start()
    headers = {
        "Referer": "https://neal.fun/infinite-craft/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get("https://neal.fun/infinite-craft/") as resp:
            # print("Status:", resp.status)
            # print("Content-type:", resp.headers['content-type'])

            html = await resp.text()
            # print("Body:", html[:15], "...")
            # cookies = session.cookie_jar.filter_cookies('https://neal.fun/infinite-craft/')
            # for key, cookie in cookies.items():
            #     print('Key: "%s", Value: "%s"' % (cookie.key, cookie.value))

        await iterative_deepening_dfs(session)


def load_last_state():
    global new_last_game_state, last_game_state, visited, best_depths, best_recipes
    try:
        with open("persistent.json", "r", encoding="utf-8") as file:
            last_state_json = json.load(file)
        last_game_state = GameState(
            [],
            last_state_json["GameState"],
            set(),
            []
        )
        new_last_game_state = last_game_state
        visited = set(last_state_json["Visited"])
        best_recipes = last_state_json["BestRecipes"]
        best_depths = last_state_json["BestDepths"]
    except FileNotFoundError:
        last_game_state = None


if resume_last_run:
    load_last_state()


@atexit.register
def save_last_state():
    print("Autosaving progress...")
    if new_last_game_state is None:
        return
    last_state_json = {
        "GameState": new_last_game_state.state,
        "Visited": list(visited),
        "BestDepths": best_depths,
        "BestRecipes": best_recipes
    }
    with open("persistent2.json", "w", encoding="utf-8") as file:
        json.dump(last_state_json, file, ensure_ascii=False, indent=4)
    os.replace("persistent2.json", "persistent.json")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
