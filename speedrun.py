def check_script(filename: str):
    with open(filename, 'r') as file:
        crafts = file.readlines()

    # Format: ... + ... -> ...
    current = {"Earth": 0,
               "Fire": 0,
               "Water": 0,
               "Wind": 0}
    for i, craft in enumerate(crafts):
        if craft == '\n':
            continue
        ingredients, results = craft.split(' -> ')
        ing1, ing2 = ingredients.split(' + ')
        if ing1.strip() not in current:
            print(f"Ingredient {ing1.strip()} not found in line {i+1}")
        else:
            current[ing1.strip()] += 1
        if ing2.strip() not in current:
            print(f"Ingredient {ing2.strip()} not found in line {i+1}")
        else:
            current[ing2.strip()] += 1
        if results.strip() in current:
            print(f"Result {results.strip()} already exists in line {i+1}")

        current[results.strip()] = 0
        # print(f'{ing1} + {ing2} -> {results}')
    for ingredient, value in current.items():
        if value is False:
            print(f"Ingredient {ingredient} is not used in any recipe")
    print(current)


def count_uses(filename: str):
    # ONLY USE THIS FOR A CORRECT FILE
    with open(filename, 'r') as file:
        crafts = file.readlines()

    # Format: ... + ... -> ...
    current = {"Earth": 0,
               "Fire": 0,
               "Water": 0,
               "Wind": 0}
    for i, craft in enumerate(crafts):
        if craft == '\n':
            continue
        ingredients, results = craft.split(' -> ')
        ing1, ing2 = ingredients.split(' + ')
        current[ing1.strip()] += 1
        current[ing2.strip()] += 1
        current[results.strip()] = 0

    print(current)


if __name__ == '__main__':
    check_script('speedrun.txt')
