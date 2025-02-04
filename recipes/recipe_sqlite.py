import atexit
import sqlite3
from typing import Optional

import util
from recipes.recipe_base import RecipeBase, RecipeResponse

# Insert a recipe into the database
insert_recipe = ("""
    INSERT INTO recipes (ingredient1_id, ingredient2_id, result_id)
    SELECT ing1.id, ing2.id, result.id
    FROM items   AS result
    JOIN items   AS ing1   ON ing1.name = ?
    JOIN items   AS ing2   ON ing2.name = ?
    WHERE result.name = ?
    ON CONFLICT (ingredient1_id, ingredient2_id) DO UPDATE SET
    result_id = EXCLUDED.result_id
    """)

# Query for a recipe
query_recipe = ("""
    SELECT result.name, result.emoji, result.first_discovery
    FROM recipes
    JOIN items   AS ing1   ON ing1.id = recipes.ingredient1_id
    JOIN items   AS ing2   ON ing2.id = recipes.ingredient2_id
    JOIN items   AS result ON result.id = recipes.result_id
    WHERE ing1.name = ? AND ing2.name = ?
    """)


class RecipeSqlite(RecipeBase):
    # Database
    db: sqlite3.Connection
    db_location: str = "cache/recipes.db"
    closed: bool = False

    # Auto-commit settings
    auto_commit: bool = True
    auto_commit_interval: int = 1000  # Commit every 1000 requests
    current_response_count: int = 0

    print_new_recipes: bool = True

    def __init__(self, init_state, **kwargs):
        super(RecipeSqlite, self).__init__()
        # Key word arguments
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Open database
        self.db = sqlite3.connect(self.db_location, isolation_level=None)
        self.db.execute('pragma journal_mode=wal')

        # Just in case
        atexit.register(lambda: (self.close()))

        # Formatting checks
        # Items table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                emoji text,
                name text UNIQUE,
                first_discovery boolean)
            """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS items_name_index ON items (name);
        """)

        # Recipes table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                ingredient1_id integer REFERENCES items(id),
                ingredient2_id integer REFERENCES items(id),
                result_id integer REFERENCES items(id),
                PRIMARY KEY (ingredient1_id, ingredient2_id) )
            """)
        # For reverse searches only, so not useful for me. May be useful for other people though.
        # cur.execute("""
        #     CREATE INDEX IF NOT EXISTS recipes_result_index ON recipes (result_id)
        # """)

        # Add starting items
        for item in init_state:
            self.add_starting_item(item, "", False)

        # # Nothing is -1, local_nothing_indication is -2
        self.add_item_force_id("Nothing", '', False, -1)
        self.add_item_force_id(util.LOCAL_NOTHING_INDICATION, '', False, -2)

        # # Get rid of "nothing"s, if we don't trust "nothing"s.
        # TODO: Configuration?
        # if not self.trust_cache_nothing:
        #     cur = self.db.cursor()
        #     cur.execute("UPDATE recipes SET result_id = -2 WHERE result_id = -1")
        #     self.db.commit()

    def close(self):
        if self.closed:
            return
        self.db.commit()
        self.db.close()
        self.closed = True

    def add_item(self, item: str, emoji: str, first_discovery: bool = False):
        # print(f"Adding: {item} ({emoji})")
        cur = self.db.cursor()
        cur.execute("INSERT INTO items (emoji, name, first_discovery) VALUES (?, ?, ?) "
                    "ON CONFLICT (name) DO UPDATE SET "
                    "emoji = EXCLUDED.emoji, "
                    "first_discovery = items.first_discovery OR EXCLUDED.first_discovery",
                    (emoji, item, first_discovery))

    def add_starting_item(self, item: str, emoji: str, first_discovery: bool = False):
        # print(f"Adding: {item} ({emoji})")
        cur = self.db.cursor()
        cur.execute("INSERT INTO items (emoji, name, first_discovery) VALUES (?, ?, ?) "
                    "ON CONFLICT (name) DO NOTHING",
                    (emoji, item, first_discovery))

    def add_item_force_id(self, item: str, emoji: str, first_discovery: bool = False, overwrite_id: int = None):
        cur = self.db.cursor()
        try:
            cur.execute("INSERT INTO items (id, emoji, name, first_discovery) VALUES (?, ?, ?, ?)"
                        "ON CONFLICT (id) DO NOTHING",
                        (overwrite_id, emoji, item, first_discovery))
            self.db.commit()
        except Exception as e:
            print(e)

    def get_item(self, item: str) -> Optional[tuple[str, str]]:
        cur = self.db.cursor()
        cur.execute("SELECT emoji, first_discovery FROM items WHERE name = ?", (item,))
        return cur.fetchone()

    def add_recipe(self, a: str, b: str, result: str):
        a = util.to_start_case(a)
        b = util.to_start_case(b)
        if a > b:
            a, b = b, a

        # Note that only the *INGREDIENT* will be converted to start case element.
        # because ingredient case does not matter.
        # The results will not, since the case of the resultant item may be significant.
        self.add_starting_item(a, "", False)
        self.add_starting_item(b, "", False)

        # print(f"Adding: {a} + {b} -> {result}")
        cur = self.db.cursor()
        cur.execute(insert_recipe, (a, b, result))

    def delete_recipe(self, a: str, b: str):
        if a > b:
            a, b = b, a
        cur = self.db.cursor()
        cur.execute("DELETE FROM recipes"
                    "JOIN items   AS ing1   ON ing1.id = recipes.ingredient1_id"
                    "JOIN items   AS ing2   ON ing2.id = recipes.ingredient2_id"
                    "WHERE ing1.name = ? AND ing2.name = ?", (a, b))

    def get_uses(self, a: str) -> list[tuple[str, str]]:
        cur = self.db.cursor()
        cur.execute("""
            SELECT ing2.name, result.name
            FROM recipes
            JOIN items   AS ing1   ON ing1.id = recipes.ingredient1_id
            JOIN items   AS ing2   ON ing2.id = recipes.ingredient2_id
            JOIN items   AS result ON result.id = recipes.result_id
            WHERE ing1.name = ?
            """, (a,))
        part1 = cur.fetchall()
        cur.execute("""
            SELECT ing1.name, result.name
            FROM recipes
            JOIN items   AS ing1   ON ing1.id = recipes.ingredient1_id
            JOIN items   AS ing2   ON ing2.id = recipes.ingredient2_id
            JOIN items   AS result ON result.id = recipes.result_id
            WHERE ing2.name = ?
            """, (a,))
        part2 = cur.fetchall()
        return part1 + part2

    def get_crafts(self, result: str) -> list[tuple[str, str]]:
        cur = self.db.cursor()
        cur.execute("""
            SELECT ing1.name, ing2.name
            FROM recipes
            JOIN items   AS ing1   ON ing1.id = recipes.ingredient1_id
            JOIN items   AS ing2   ON ing2.id = recipes.ingredient2_id
            JOIN items   AS result ON result.id = recipes.result_id
            WHERE result.name = ?
            """, (result,))
        return cur.fetchall()

    def _get_local(self, a: str, b: str) -> RecipeResponse:
        a = util.to_start_case(a)
        b = util.to_start_case(b)
        if a > b:
            a, b = b, a

        cur = self.db.cursor()
        cur.execute(query_recipe, (a, b))
        result = cur.fetchone()
        if result:
            return result[0], result[1], (result[2] == 1)
        else:
            return None

    async def _combine(self, a, b, *args, **kwargs) -> RecipeResponse:
        result = self._get_local(a, b)

        if result == util.LOCAL_NOTHING_INDICATION:
            # TODO: Configuration can change if this is "Nothing" (i.e. definitive)
            # or if this becomes None (i.e. keep requesting)
            result = None

        return result

    async def _combine_batch(self, batch: list[tuple[str, str]], *args, **kwargs) \
            -> list[tuple[str, str, RecipeResponse]]:
        return [(a, b, await self._combine(a, b)) for a, b in batch]

    async def _update(self, a, b, r):
        self.current_response_count += 1
        result = r[0]
        emoji = r[1]
        new = r[2]

        if self.print_new_recipes:
            print(f"New Recipe: {a} + {b} -> {result}")
        if new:
            print(f"FIRST DISCOVERY: {a} + {b} -> {result}")

        # Items - emoji, new discovery
        self.add_item(result, emoji, new)

        # Save as the fake nothing if it's the first run
        if result == "Nothing" and not self._get_local(a, b):
            # TODO: Again, configuration for this?
            result = util.LOCAL_NOTHING_INDICATION

        # Recipe: A + B --> C
        self.add_recipe(a, b, result)

        # Autosave check
        if self.auto_commit and self.current_response_count >= self.auto_commit_interval:
            print("Auto committing recipes to sqlite database...", flush=True)
            self.db.commit()
            self.current_response_count = 0
