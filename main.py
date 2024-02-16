import time
from functools import cache
from typing import Optional

import recipe

# import tracemalloc

recipe_handler = recipe.RecipeHandler()
# init_state: tuple[str, ...] = ("Fire", )
# init_state: tuple[str, ...] = ("Water", "Fire", "Wind", "Earth")
                               # "Lake", "Lava", "Stone", "Rock", "Lighthouse", "Hermit", "Sphinx", "Oedpius",
                               # "Oedipus Rex", "Sophocles")
init_state: tuple[str, ...] = ('Earth', 'Fire', 'Water', 'Wind', 'Dust', 'Ash', 'Phoenix', 'Rebirth', 'Fish', 'Dragon', 'Yin Yang', 'Feng Shui', 'Dust Bunny', 'Opposite')
# init_state: tuple[str, ...] = ('Earth', 'Fire', 'Water', 'Wind', 'Smoke', 'Plant', 'Incense', 'Prayer', 'Candle',
#                                'Oxygen', 'Hydrogen', 'Dandelion', 'Helium', 'Lava', 'Stone', 'Obsidian', 'Diamond',
#                                'Carbon', 'Wave', 'Fossil', 'Ammonite', 'Ammonia', 'Ammonium', 'Nitrogen', 'Ocean',
#                                'Dust', 'Ash', 'Salt', 'Sodium', 'Sandstorm', 'Oasis', 'Planet', 'Sun', 'Solar',
#                                'System', 'Computer', 'Silicon', 'Perfume', 'Smell', 'Sulfur', 'Emerald', 'Green',
#                                'Chlorine', 'Weed', 'Pot', 'Potash', 'Potassium', 'Swamp', 'Dragon', 'Sea Serpent',
#                                'Leviathan', 'Titan', 'Dragon Egg', 'Titanium', 'Steam', 'Engine', 'Rocket',
#                                'Satellite', 'Lake', 'Google', 'FireFox', 'Chrome', 'Chromium', 'Vacuum', 'Clean',
#                                'Iron', 'Wine', 'Poison', 'Murder', 'Arsenic', 'Fish', 'Starfish', 'Flying Starfish',
#                                'Superman', 'Krypton', 'Metal', 'Silver', 'Steel', 'Tin', 'Mountain', 'Dragonfly',
#                                'Ant', 'Antfly', 'Antimony', 'Gold', 'Mars', 'Venus', 'Mercury', 'Saturn', 'Lead',
#                                'Tobacco', 'Uranus', 'Urine', 'Uranium', 'Pluto', 'Plutonium', 'Platinum', 'Argentum',
#                                'Pewter', 'Periodic Table')



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

# Math, Number, Reality or Vacuum


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
                craft_result in self.items or
                craft_result in self.children):
            return None

        # Make sure we never craft this ever again
        self.children.add(craft_result)

        # Construct the new state
        new_state = self.state + [i,]
        new_items = self.items + [craft_result,]
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


best_recipes: dict[str, list[GameState]] = dict()
visited = set()
best_depths: dict[str, int] = dict()
best_recipes_file: str = "best_recipes.txt"
all_best_recipes_file: str = "expanded_recipes_depth_9.txt"
extra_depth = 0


def process_node(state: GameState):
    if state.tail_item() not in visited:
        visited.add(state.tail_item())
        #  Dumb writing to file
        # if state.tail_item() in elements:
        with open(best_recipes_file, "a", encoding="utf-8") as file:
            file.write(str(len(visited)) + ": " + str(state) + "\n\n")
    # Multiple recipes for the same item at same depth
    # depth = len(state) - len(init_state)
    # if state.tail_item() not in best_depths:
    #     best_depths[state.tail_item()] = depth
    #     best_recipes[state.tail_item()] = [state,]
    # elif depth <= best_depths[state.tail_item()] + extra_depth:
    #     best_recipes[state.tail_item()].append(state)


# Depth limited search
def dls(state: GameState, depth: int) -> int:
    """
    Depth limited search
    :param state: The current state
    :param depth: The depth remaining
    :return: The number of states processed
    """
    if depth == 0:                          # We've reached the end of the crafts, process the node
        process_node(state)
        return 1

    # In the future, remove states with overly long words w/ lots of tokens
    # I'm nowhere near that token limit though

    count = 0  # States counter
    unused_items = state.unused_items()     # Unused items
    if len(unused_items) > depth + 1:       # Impossible to use all elements, since we have too few crafts left
        return 0
    elif len(unused_items) > depth:         # We must start using unused elements NOW.
        for j in range(len(unused_items)):  # For loop ordering is important. We want increasing pair_to_int order.
            for i in range(j):              # i != j. We have to use two for unused_items to decrease.
                child = state.child(pair_to_int(unused_items[i], unused_items[j]))
                if child is not None:
                    count += dls(child, depth - 1)
        return count
    # TODO: elif len(unused_items) == depth might be a useful pruning case. Not gonna bother right now.
    else:
        lower_limit = 0
        if depth == 1 and state.tail_index() != -1:      # Must use the 2nd last element, if it's not a default item.
            lower_limit = limit(len(state) - 1)

        for i in range(lower_limit, limit(len(state))):  # Regular ol' searching
            child = state.child(i)
            if child is not None:
                count += dls(child, depth - 1)

        return count


def iterative_deepening_dfs():
    open(best_recipes_file, "w").close()

    curDepth = 1

    start_time = time.perf_counter()

    # Recipe Analysis

    # with open("best_recipes_depth_9.txt", "r", encoding='utf-8') as fin:
    #     lines = fin.readlines()
    #
    # recipes = [set() for _ in range(10)]
    # cur_recipe = ""
    # cur_recipe_depth = -1
    # for line in lines:
    #     if line.strip() == "":
    #         output = cur_recipe.split(":")[1].strip()
    #         recipes[cur_recipe_depth].add(output)
    #
    #         cur_recipe = ""
    #         cur_recipe_depth = -1
    #     else:
    #         cur_recipe += line
    #         cur_recipe_depth += 1
    # sizes = [len(x) for x in recipes]
    # # print(recipes)
    # print([sum(sizes[:i+1]) for i in range(1, len(sizes))])

    while True:
        prev_visited = len(visited)
        print(dls(
            GameState(
                list(init_state),
                [-1 for _ in range(len(init_state))],
                set(),
                [0 for _ in range(len(init_state))]
            ),
            curDepth))

        # print(len(visited))
        #
        # for i in range(curDepth + 1):
        #     for v in recipes[i]:
        #         if v not in visited:
        #             print(f"Missing {v} at depth {i}")

        # Performance
        # current, peak = tracemalloc.get_traced_memory()
        # print(f"Current memory usage is {current / 2**20}MB; Peak was {peak / 2**20}MB")
        # print(f"Current time elapsed: {time.perf_counter() - start_time:.4f}")
        # print("Completed depth: ", curDepth)
        print(f"{curDepth}   {len(visited)}     {time.perf_counter() - start_time:.4f}")
        # print(best_recipes)
        # print(flush=True)
        # if curDepth == 10:
        #     break
        # Only relevant for local files - if exhausted the outputs, stop
        if len(visited) == prev_visited:
            break
        curDepth += 1

    # with open(all_best_recipes_file, "w", encoding="utf-8") as file:
    #     for key, value in best_recipes.items():
    #         # print(f"{key} has {len(value)} distinct minimal recipes")
    #         # file.write(f"{key} has {len(value)} distinct recipes that's 1 off from minimal:\n")
    #         file.write(f"{key}\n")
    #         # for r in value:
    #         #     items = list(r.items_set())
    #         #     items.sort()
    #         #     file.write("\n{" + ", ".join(items) + "} -> " + str(r) + "\n")
    #         file.write("\n--\n".join([str(r) for r in value]))
    #
    #         file.write("\n-----------------------------------------------\n")


def main():
    # tracemalloc.start()
    iterative_deepening_dfs()


if __name__ == "__main__":
    main()
    # print("\", \"".join(elements.split('\n')))
