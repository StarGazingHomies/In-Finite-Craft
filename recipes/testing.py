import asyncio
import os

import aiohttp

import recipes
import util


def remove_files(files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)

async def main():
    remove_files(["recipes.db", "recipes.json", "items.json"])
    async with aiohttp.ClientSession() as session:
        rdb = recipes.recipe_ram.RecipeRam(recipes_file="recipes.json", items_file="items.json")
        # db = recipes.recipe_sqlite.RecipeSqlite(util.DEFAULT_STARTING_ITEMS, db_location="recipes.db")

        persistent_config = util.load_json("../config.json")
        requester = recipes.recipe_requests.RecipeRequests(session, **persistent_config)

        # rdb.set_next(db).set_next(requester)
        rdb.set_next(requester)

        rdb.set_name("dict")
        # db.set_name("sql")
        requester.set_name("api")

        # print(await db2.combine("Water", "Fire"))
        # print(await db2.update("Water", "Fire", ("Steam", "💨", False)))
        # print(await db2.combine("Water", "Fire"))
        # print(await db.combine("Water", "Fire"))
        # print(await db.combine("Water", "Fire"))
        print(await rdb.combine("Water", "Fire"))
        print(await rdb.combine("Water", "Fire"))
        print(await rdb.combine_batch([("Water", "Fire"), ("Fire", "Water")]))
        print(await rdb.combine_batch([("Water", "Fire"), ("Water", "Water")]))
        print(await rdb.combine_batch([("Water", "Fire"), ("Water", "Water"), ("Earth", "Fire")]))


if __name__ == "__main__":
    asyncio.run(main())
