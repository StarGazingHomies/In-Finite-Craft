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


def check_script(filename: str):
    with open(filename, 'r') as file:
        crafts = file.readlines()

    # Format: ... + ... -> ...
    current = {"Earth": 0,
               "Fire": 0,
               "Water": 0,
               "Wind": 0}
    craft_count = 0
    for i, craft in enumerate(crafts):
        # print(craft)
        if craft == '\n' or craft[0] == "#":
            continue
        ingredients, results = craft.split(' -> ')
        ing1, ing2 = ingredients.split(' + ')
        craft_count += 1
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
    element_count = 0
    for ingredient, value in current.items():
        if value == 0 and ingredient not in elements:
            print(f"Ingredient {ingredient} is not used in any recipe")
        if ingredient in elements:
            element_count += 1
            elements.remove(ingredient)
    print("\n".join([str(elements[i*10:i*10+10]) for i in range(11)]))
    print(craft_count)
    print(current)
    print(tuple(current.keys()))
    print(element_count)
    return current


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


def load_best_recipes(filename: str) ->  dict[str, list[list[tuple[str, str, str]]]]:
    # Loading the all best recipes file for easy element adding
    with open(filename, 'r') as file:
        lines = file.readlines()

    recipes: dict[str, list[list[tuple[str, str, str]]]] = {}

    current_element = ""
    rec_separator = "--"
    separator = "-----------------------------------------------"
    state = 0
    current_recipe = []
    for line in lines:
        try:
            line = line[:-1]  # Ignore last \n
            if state == 0:
                # Get current element
                current_element = line
                state = 1
                continue
            if state == 1:
                state = 2
                current_recipe = []
                continue
            if state == 2:
                if line == separator:
                    state = 0
                    if current_element in recipes:
                        recipes[current_element].append(current_recipe)
                    else:
                        recipes[current_element] = [current_recipe]
                    continue
                if line == rec_separator:
                    state = 1
                    if current_element in recipes:
                        recipes[current_element].append(current_recipe)
                    else:
                        recipes[current_element] = [current_recipe]
                    continue
                # Get recipe
                elem, w = line.split(" -> ")
                u, v = elem.split(" + ", 1)
                current_recipe.append((u, v, w))
        except Exception as e:
            print(line, state)

    return recipes


def find_best_element_recipe(filename: str, element: str, recipes: dict[str, list[list[tuple[str, str, str]]]]):
    if element not in recipes:
        print(f"Element {element} not found in recipes")
        return

    cur_elements = check_script(filename)

    best_recipe = []
    best_cost = 1e9
    speedy_recipe = []
    for r in recipes[element]:
        cost = len(r)
        for u, v, w in r:
            if w in cur_elements:
                cost -= 1
            else:
                speedy_recipe.append((u, v, w))
        # print(cost, r)
        if cost < best_cost:
            best_cost = cost
            best_recipe = speedy_recipe
        speedy_recipe = []
    print(f"Best recipe for {element} has cost {best_cost}:")
    for u, v, w in best_recipe:
        print(f"{u} + {v} -> {w}")


if __name__ == '__main__':
    # check_script('NewPeriodicTable.txt')
    find_best_element_recipe('-1.txt',
                             "Camera",
                             load_best_recipes('expanded_recipes_depth_9.txt'))
