# TODO:
# Implementation of Mika's helper bot lineage generation
# to test and see if it works
import sys
import time
from typing import Optional

import util
from optimizers.optimizer_interface import OptimizerRecipeList, savefile_to_optimizer_recipes, \
    optimizer_recipes_to_savefile

NUM_RECIPES = 5
NUM_RETRIES = 1


class BubblingRecipe(object):
    def __init__(self, items: set[int], steps: list[tuple[int, int, int]]):
        # Note: steps are tuples of (item1, item2, result)
        self.items = items
        self.steps = steps
        self.bwd: dict[int, tuple[int, int]] = {}
        for a, b, c in steps:
            self.bwd[c] = (a, b)

    def add(self, recipe: tuple[int, int, int]):
        # Warning: This mutates the recipe
        if recipe[0] not in self.items or recipe[1] not in self.items:
            raise ValueError("Item not in recipe")
        self.items.add(recipe[2])
        self.steps.append(recipe)
        self.bwd[recipe[2]] = (recipe[0], recipe[1])
        return self

    @property
    def length(self):
        return len(self.steps)

    def pretty_print(self, recipe_list: OptimizerRecipeList, *, file=sys.stdout):
        for step in self.steps:
            print(f"{recipe_list.ids.inv[step[0]]}  +  {recipe_list.ids.inv[step[1]]}  =  {recipe_list.ids.inv[step[2]]}", file=file)


def merge_recipe(big_bubble: BubblingRecipe, small_bubble: BubblingRecipe, item2_id: int, base_elements: set[int]):
    # Note that this works because we're essentially crafting the small one after the big one
    # It's not "optimal" merging, like there's no A* step to shrink it

    all_items = big_bubble.items.copy()

    # print(all_items, new_items)
    all_steps = big_bubble.steps.copy()

    # print(small_bubble.steps)
    # print(small_bubble.bwd)

    required_items = {item2_id}
    steps_to_add = []

    while len(required_items) > 0:
        cur = required_items.pop()
        if cur in all_items:
            continue
        if cur in base_elements:
            all_items.add(cur)
            continue

        a, b = small_bubble.bwd[cur]
        required_items.add(a)
        required_items.add(b)
        steps_to_add.append((a, b, cur))
        all_items.add(cur)

    for a, b, cur in steps_to_add[::-1]:
        all_steps.append((a, b, cur))

    return BubblingRecipe(all_items, all_steps)


class BestBubblingRecipes(object):
    recipes: list[Optional[BubblingRecipe]]

    def __init__(self, item_name: str, item_id: int, *, num_recipes: int = NUM_RECIPES, base_element: bool=False, base_element_set: set[int]=None):
        self.item_name = item_name
        self.item_id = item_id
        self.base_element = base_element
        if self.base_element:
            self.recipes = [BubblingRecipe(base_element_set.copy(), [])]
        else:
            self.recipes = [None] * num_recipes

    def add_recipe(self, recipe: BubblingRecipe) -> bool:
        if self.base_element:
            return False

        for i, r in enumerate(self.recipes):
            if r is None:
                self.recipes.insert(i, recipe)
                self.recipes.pop()
                return True

            if r.items.issubset(recipe.items):
                return False

            if r.length > recipe.length:
                self.recipes.insert(i, recipe)
                self.recipes.pop()
                return True
        return False

    def add_recipe_craft(self, item1: "BestBubblingRecipes", item2: "BestBubblingRecipes", base_elements: set[int]) -> int:
        if self.base_element:
            return 0

        changes = 0
        # print(item1, item2)

        for j in item1.recipes:
            if j is None and not item1.base_element:
                continue
            for k in item2.recipes:
                if k is None and not item2.base_element:
                    continue
                new_recipe = merge_recipe(j, k, item2.item_id, base_elements).add((item1.item_id, item2.item_id, self.item_id))
                if self.add_recipe(new_recipe):
                    changes += 1
        return changes

    def __str__(self):
        return "\n".join(
            [f"{self.item_name} {'(base element)' if self.base_element else ''}"] + [str(r) for r in self.recipes])

    def pretty_print(self, recipe_list: OptimizerRecipeList, *, file=sys.stdout):
        if self.recipes[0] is None:
            print(f"No recipes found for {self.item_name}", file=file)
            return
        print("Best Recipe Length:", self.recipes[0].length, file=file)
        for i, r in enumerate(self.recipes):
            if r is not None:
                print(f"  Recipe {i}:", file=file)
                r.pretty_print(recipe_list, file=file)
        print("---" * 50, file=file)


def optimize(
        targets: list[str],
        recipe_list: OptimizerRecipeList,
        initial_items: list[int] = None,
        bubble_retries: int = NUM_RETRIES,
        default_recipes: int = NUM_RECIPES) -> list[int]:
    t0 = time.perf_counter()
    recipe_list.generate_generations()

    if initial_items is None:
        initial_items = [recipe_list.get_id(item) for item in util.DEFAULT_STARTING_ITEMS]
    print(initial_items)
    initial_items_set = set(initial_items)

    recipes_raw = recipe_list.fwd
    recipes = []
    items_best_recipes = {}
    for name, i in recipe_list.ids.items():
        if i in initial_items:
            items_best_recipes[i] = BestBubblingRecipes(name, i, num_recipes=1, base_element=True, base_element_set=initial_items_set)
        else:
            items_best_recipes[i] = BestBubblingRecipes(name, i)

    for i, r in recipes_raw.items():
        a, b = util.int_to_pair(i)
        recipes.append((a, b, r))

    t1 = time.perf_counter()

    def sorting_heuristic(recipe):
        try:
            return util.pair_to_int(recipe_list.gen[recipe[1]], recipe_list.gen[recipe[2]])
        except KeyError:
            return 1000000000000

    recipes.sort(key=lambda x: sorting_heuristic(x))

    for loop_count in range(bubble_retries):
        print(f"Loop {loop_count}")
        for i, r in enumerate(recipes):
            if i % 1000 == 0:
                print(f"Recipe {i}/{len(recipes)}")
            a, b, c = r
            if a == c or b == c:
                continue
            # print(f"{recipe_list.ids.inv[a]} + {recipe_list.ids.inv[b]} -> {recipe_list.ids.inv[c]}")
            items_best_recipes[c].add_recipe_craft(items_best_recipes[a], items_best_recipes[b], initial_items_set)
            # items_best_recipes[c].pretty_print(recipe_list)
            # input()

    t2 = time.perf_counter()

    with open("output.txt", "w", encoding='utf-8') as f:
        for item, recipes in items_best_recipes.items():
            f.write(f"Target: {recipes.item_name}\n")
            recipes.pretty_print(recipe_list, file=f)

    with open("output_condensed.txt", "w", encoding='utf-8') as f:
        for item, recipes in items_best_recipes.items():
            if recipes.recipes[0] is None:
                continue
            f.write(f"{recipes.item_name}={recipes.recipes[0].length}\n")

    t3 = time.perf_counter()
    print(f"Preprocessing: {t1 - t0:.2f}s")
    print(f"Optimizing: {t2 - t1:.2f}s")
    print(f"Output: {t3 - t2:.2f}s")

    return []


def main():
    # print(savefile_to_optimizer_recipes("../infinitecraft (34).json"))
    optimize("Firebird", savefile_to_optimizer_recipes("../infinitecraft (104).json"), bubble_retries=1)


if __name__ == "__main__":
    main()
