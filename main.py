import multiprocessing
import os
import time
from functools import cache, partial
from typing import Optional

import json

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
depth_limit = 6
thread_preproc_depth = 3  # Nonpositive numbers turn it off
num_threads = 32

best_recipes: dict[str, list['GameState']] = dict()
visited = set()
best_depths: dict[str, int] = dict()
best_recipes_file: str = "best_recipes.txt"
all_best_recipes_file: str = "all_best_recipes_depth_10_filtered.json"
extra_depth = 0
save_all_best_recipes: bool = False
case_sensitive: bool = False
write_to_file: bool = False
three_letter_search: bool = False
allow_starting_elements: bool = False


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
    items: list[str, ...]
    state: list[int, ...]
    visited: list[set[str], ...]
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

    def child(self, i: int) -> Optional['GameState']:
        # Invalid indices
        if i <= self.tail_index() or i >= limit(len(self)):
            return None

        # Craft the items
        u, v = int_to_pair(i)
        craft_result = recipe_handler.combine(self.items[u], self.items[v])

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


def process_node(state: GameState) -> None:
    tail_item = state.tail_item()
    if three_letter_search:
        if len(tail_item) != 3 or not tail_item.isalpha():
            return

    if tail_item not in visited:
        visited.add(tail_item)

    if save_all_best_recipes:
        depth = len(state) - len(init_state)
        if state.tail_item() not in best_depths:
            best_depths[state.tail_item()] = depth
            best_recipes[state.tail_item()] = [state]
        elif depth <= best_depths[state.tail_item()] + extra_depth:
            best_recipes[state.tail_item()].append(state)


def filter_node(state: GameState) -> bool:
    tail_item = state.tail_item()
    if not case_sensitive:
        tail_item = tail_item.upper()

    if tail_item not in visited:
        # visited.add(tail_item)
        return True
        #  Dumb writing to file
        # if write_to_file:
        #     with open(best_recipes_file, "a", encoding="utf-8") as file:
        #         file.write(str(len(visited)) + ": " + str(state) + "\n\n")

    # Multiple recipes for the same item at same depth
    if save_all_best_recipes:
        depth = len(state) - len(init_state)
        if state.tail_item() not in best_depths:
            return True
        elif depth <= best_depths[state.tail_item()] + extra_depth:
            return False


def dls_pre_thread(state: GameState, depth: int) -> list[GameState]:
    if depth == 0:  # We've reached the end of the crafts, process the node
        return [state]

    # 30 char limit, confirmed by Neal
    if len(state.tail_item()) > recipe.WORD_COMBINE_CHAR_LIMIT:
        return []

    # Even if we allowed starting element results, we're still not going to continue from such a state
    if allow_starting_elements and state.tail_item() in state.items[:-1]:
        return []

    count: list[GameState] = []  # States
    # NO unused items check because this is for preprocessing states before threading
    # so the depth isn't meaningful here.
    lower_limit = 0
    for i in range(lower_limit, limit(len(state))):  # Regular ol' searching
        child = state.child(i)
        if child is not None:
            count += dls_pre_thread(child, depth - 1)

    return count


def dls_post_thread(state: GameState, depth: int) -> list[GameState]:
    """
    Depth limited search
    :param state: The current state
    :param depth: The depth remaining
    :return: The potentially optimal GameStates
    """
    if depth == 0:  # We've reached the end of the crafts, process the node
        if filter_node(state):
            return [state]
        return []

    # 30 char limit, according to PB and laurasia
    if len(state.tail_item()) > recipe.WORD_COMBINE_CHAR_LIMIT:
        return []

    # Even if we allowed starting element results, we're still not going to continue from such a state
    if allow_starting_elements and state.tail_item() in state.items[:-1]:
        return []

    states = []
    unused_items = state.unused_items()  # Unused items
    if len(unused_items) > depth + 1:  # Impossible to use all elements, since we have too few crafts left
        return []
    elif len(unused_items) > depth:  # We must start using unused elements NOW.
        for j in range(len(unused_items)):  # For loop ordering is important. We want increasing pair_to_int order.
            for i in range(j):  # i != j. We have to use two for unused_items to decrease.
                child = state.child(pair_to_int(unused_items[i], unused_items[j]))
                if child is not None:
                    states += dls_post_thread(child, depth - 1)
        return states
    else:
        lower_limit = 0
        if depth == 1 and state.tail_index() != -1:  # Must use the 2nd last element, if it's not a default item.
            lower_limit = limit(len(state) - 1)

        for i in range(lower_limit, limit(len(state))):  # Regular ol' searching
            child = state.child(i)
            if child is not None:
                states += dls_post_thread(child, depth - 1)

        return states


def iterative_deepening_dfs():
    # Clear best recipes file
    open(best_recipes_file, "w").close()

    curDepth = 1
    start_time = time.perf_counter()

    while True:
        prev_visited = len(visited)
        if curDepth > thread_preproc_depth > 0:
            states = dls_pre_thread(
                GameState(
                    list(init_state),
                    [-1 for _ in range(len(init_state))],
                    set(),
                    [0 for _ in range(len(init_state))]
                ),
                thread_preproc_depth)

            with multiprocessing.Pool(num_threads) as pool:
                new_states = pool.map(partial(dls_post_thread, depth=curDepth - thread_preproc_depth), states)

            # for state in states:
            #     # print(state)
            #     total_states += dls(state, curDepth - thread_preproc_depth)
            total_states = 0
            for batch in new_states:
                total_states += len(batch)
                for state in batch:
                    process_node(state)
            print(f"{total_states}")
        else:
            states = dls_post_thread(
                GameState(
                    list(init_state),
                    [-1 for _ in range(len(init_state))],
                    set(),
                    [0 for _ in range(len(init_state))]
                ), curDepth)
            print(len(states))
            for state in states:
                process_node(state)

        print(f"{curDepth}   {len(visited)}     {time.perf_counter() - start_time:.4f}")
        if curDepth >= depth_limit > 0:
            break
        # Only relevant for local files - if exhausted the outputs, stop
        if len(visited) == prev_visited:
            break
        curDepth += 1

    if save_all_best_recipes:
        best_recipes_json = {}
        for key, value in best_recipes.items():
            best_recipes_json[key] = [r.to_list() for r in value]
        with open(all_best_recipes_file, "w", encoding="utf-8") as file:
            json.dump(best_recipes_json, file, ensure_ascii=False, indent=4)


def main():
    # tracemalloc.start()
    iterative_deepening_dfs()


if __name__ == "__main__":
    main()
    # print("\", \"".join(elements.split('\n')))
