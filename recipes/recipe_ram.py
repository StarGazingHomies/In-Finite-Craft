import atexit
from typing import Optional

import util
from recipes.recipe_base import RecipeBase, RecipeResponse


def get_key(a, b):
    return f"{a.lower()}={b.lower()}"


class RecipeRam(RecipeBase):

    recipes_cache: dict[str, str]
    items_cache: dict[str, tuple[str, bool]]
    recipes_file: str = "cache/recipes.json"
    items_file: str = "cache/items.json"

    # TODO: Items bidict + compression using pair-to-int?
    # TODO: Smart "caching" to operate in limited memory scenarios, such as Noms and Nibbles

    # Auto-commit settings
    auto_commit: bool = True
    auto_commit_interval: int = 100000  # Commit every 100000 updates
    current_response_count: int = 0

    def __init__(self, **kwargs):
        super().__init__()
        # Key word arguments
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.recipes_cache = util.load_json(self.recipes_file)
        self.items_cache = util.load_json(self.items_file)

        atexit.register(lambda: util.save_json(self.recipes_file, self.recipes_cache))
        atexit.register(lambda: util.save_json(self.items_file, self.items_cache))

    async def _combine(self, a, b, *args, **kwargs) -> RecipeResponse:
        key = get_key(a, b)
        if key in self.recipes_cache:
            item = self.recipes_cache[key]
            emoji, new = self.items_cache[item]
            return item, emoji, new

        return None

    async def _combine_batch(self, batch: list[tuple[str, str]], *args, **kwargs) \
            -> list[tuple[str, str, RecipeResponse]]:
        results = []
        for a, b in batch:
            result = await self._combine(a, b, *args, **kwargs)
            results.append((a, b, result))
        return results

    async def _update(self, a, b, result: RecipeResponse):
        if result == util.LOCAL_NOTHING_INDICATION:
            return
        if result == "Nothing" and get_key(a, b) not in self.recipes_cache:
            self.recipes_cache[get_key(a, b)] = util.LOCAL_NOTHING_INDICATION
        self.current_response_count += 1
        key = get_key(a, b)
        self.recipes_cache[key] = result[0]
        self.items_cache[result[0]] = (result[1], result[2])

        # Autosave check
        if self.auto_commit and self.current_response_count >= self.auto_commit_interval:
            print("Auto committing recipes to dictionary database...", flush=True)
            util.save_json(self.recipes_file, self.recipes_cache)
            util.save_json(self.items_file, self.items_cache)
            self.current_response_count = 0

        return
