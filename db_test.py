# This entire file is basically Github Copilot and the occasional StackOverflow search
# I do not know sql :3
# (Postgresql)

import psycopg
from psycopg import IsolationLevel
from psycopg.sql import SQL

# Connect to an existing database
# Not a real password :3
with psycopg.connect(user='postgres', password='qtPieBlep:3') as conn:
    # Set the connection's autocommit mode to True
    conn.autocommit = True


    with conn.cursor() as cur:
        # Execute the DROP DATABASE command
        # cur.execute("DROP DATABASE IF EXISTS in_finite_craft")
        # Execute the CREATE DATABASE command
        # cur.execute("CREATE DATABASE in_finite_craft")

        # Reset tables
        # cur.execute("""DROP TABLE IF EXISTS recipes""")
        # cur.execute("""DROP TABLE IF EXISTS items""")

        # Items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id serial PRIMARY KEY,
                emoji text,
                name text UNIQUE,
                first_discovery boolean)
            """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS items_name_index ON items (name);
        """)

        # Recipes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                ingredient1_id integer REFERENCES items(id),
                ingredient2_id integer REFERENCES items(id),
                result_id integer REFERENCES items(id),
                PRIMARY KEY (ingredient1_id, ingredient2_id) )
            """)
        # For reverse searches. Necessary for stats and stuff, not for iddfs.
        cur.execute("""
            CREATE INDEX IF NOT EXISTS recipes_result_index ON recipes (result_id)
        """)

        # Put an example item in the table
        insert_item = SQL("INSERT INTO items (emoji, name, first_discovery) VALUES (%s, %s, %s) "
                          "ON CONFLICT (name) DO UPDATE SET "
                          "emoji = EXCLUDED.emoji,"
                          "first_discovery = items.first_discovery OR EXCLUDED.first_discovery")
        ensure_item = SQL("INSERT INTO items (emoji, name, first_discovery) VALUES (%s, %s, %s) "
                          "ON CONFLICT (name) DO NOTHING")
        # Water
        cur.execute(insert_item, ('💧', 'Water', False))
        # Fire
        cur.execute(insert_item, ('🔥', 'Fire', False))
        # Earth
        cur.execute(insert_item, ('🌎', 'Earth', False))
        # Wind
        cur.execute(insert_item, ('💨', 'Wind', False))
        # Steam
        cur.execute(insert_item, ('💨💧', 'Steam', False))
        # Ensure Mud is in the table
        cur.execute(ensure_item, ("", "Mud", False))
        insert_item_force = SQL("INSERT INTO items (id, emoji, name, first_discovery) VALUES (%s, %s, %s, %s)"
                                "ON CONFLICT (name) DO NOTHING")
        try:
            cur.execute(insert_item_force, (5, "💧🌎", "Mud", False))
        except psycopg.IntegrityError as e:
            print(e)

        cur.execute("SELECT * FROM items")
        result = cur.fetchall()
        print(result)
        cur.execute(insert_item_force, (6, "💧🔥", "Mud", True))
        cur.execute("SELECT * FROM items")
        result = cur.fetchall()
        print(result)
        cur.execute(insert_item_force, (7, "💧🔥", "Mud", False))
        cur.execute("SELECT * FROM items")
        result = cur.fetchall()
        print(result)
        # cur.execute(insert_item_force, (-1, "", "Nothing", False))
        # cur.execute("SELECT * FROM items")
        # result = cur.fetchall()
        # print(result)
        # cur.execute(insert_item_force, (-1, "", "Nothing2", False))


        # Items DB
        cur.execute("SELECT * FROM items")
        result = cur.fetchall()
        print(result)

        # Put an example recipe in the table
        # Water + Fire = Steam
        # cur.execute("INSERT INTO recipes (ingredient1_id, ingredient2_id, result_id) VALUES (%s, %s, %s)", (1, 2, 5))

        insert_recipe = SQL("""
            INSERT INTO recipes (ingredient1_id, ingredient2_id, result_id)
            SELECT ing1.id, ing2.id, result.id
            FROM items   AS result
            JOIN items   AS ing1   ON ing1.name = %s
            JOIN items   AS ing2   ON ing2.name = %s
            WHERE result.name = %s
            ON CONFLICT (ingredient1_id, ingredient2_id) DO UPDATE SET
            result_id = EXCLUDED.result_id
        """)
        cur.execute(insert_recipe, ("Water", "Fire", "Steam"))
        cur.execute(insert_recipe, ("Water", "Earth", "Mud"))

        cur.execute("SELECT * FROM recipes")
        result = cur.fetchall()
        print(result)

        # Join query that looks for water + fire, using the strings water and fire instead of the ids
        query_recipe = SQL("""
            SELECT result.name, result.emoji
            FROM recipes
            JOIN items   AS ing1   ON ing1.id = recipes.ingredient1_id
            JOIN items   AS ing2   ON ing2.id = recipes.ingredient2_id
            JOIN items   AS result ON result.id = recipes.result_id
            WHERE ing1.name = %s AND ing2.name = %s
        """)
        cur.execute(query_recipe, ("Water", "Fire"))
        result = cur.fetchall()
        print(result)

        # Make the changes to the database persistent
        conn.commit()
