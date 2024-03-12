# This is a temporary script to fill out the 3-letter combinations forms.
# Because apparently, no one is going to go through my 1.8k new elements text file :(
import os
from typing import Optional

import aiohttp, asyncio

url = "https://docs.google.com/forms/d/e/1FAIpQLSeAUAH0FLeXO9agNcFPCSuqcbBQth_soRGQOlRBoN7zqnBQQw/formResponse"
my_recipes = "https://cdn.discordapp.com/attachments/1211185679846088704/1214747561492094996/3_letters.txt?ex=65fa3cd3&is=65e7c7d3&hm=151e34b761ee01e85947e1a58db9731e19f9a14951375b9caf9257fa8dc62e88&"

form = {
    # What is the FIRST element you have found? Please only include the SINGLE element in ALL CAPS. Ex: ABC (required)
    "entry.1748793802": "",
    # Send a discord image link of how you got the element. Make sure your link contains /attachments/. (required)
    "entry.342060576": "",
    # What is the SECOND element you have found? Please only include the SINGLE element in ALL CAPS. Ex: XYZ (Do not answer if you don't have a second element)
    "entry.926567830": "",
    # Send a discord image link of how you got the element. Make sure your link contains /attachments/. (Do not answer if you don't have a second element)
    "entry.1819669091": "",
    # What is the THIRD element you have found? Please only include the SINGLE element in ALL CAPS. Ex: XYZ (Do not answer if you don't have a third element)
    "entry.1101441597": "",
    # Send a discord image link of how you got the element. Make sure your link contains /attachments/. (Do not answer if you don't have a third element)
    "entry.387485739": "",
}


def fill_form_dict(elem_1: str, elem_2: Optional[str], elem_3: Optional[str]):
    f = form.copy()
    f["entry.1748793802"] = elem_1
    f["entry.342060576"] = "https://cdn.discordapp.com/attachments/1211185679846088704/1214747561492094996/3_letters.txt?ex=65fa3cd3&is=65e7c7d3&hm=151e34b761ee01e85947e1a58db9731e19f9a14951375b9caf9257fa8dc62e88&"

    if elem_2:
        f["entry.926567830"] = elem_2
        f["entry.1819669091"] = "https://cdn.discordapp.com/attachments/1211185679846088704/1214747561492094996/3_letters.txt?ex=65fa3cd3&is=65e7c7d3&hm=151e34b761ee01e85947e1a58db9731e19f9a14951375b9caf9257fa8dc62e88&"

    if elem_3:
        f["entry.1101441597"] = elem_3
        f["entry.387485739"] = "https://cdn.discordapp.com/attachments/1211185679846088704/1214747561492094996/3_letters.txt?ex=65fa3cd3&is=65e7c7d3&hm=151e34b761ee01e85947e1a58db9731e19f9a14951375b9caf9257fa8dc62e88&"

    return f

async def post(session: aiohttp.ClientSession, f: dict[str, str]):
    async with session.post(url, data=f) as resp:
        print(resp.status)
        print(await resp.text())


async def main():
    with open("../best_recipes_o.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    all_results = set()
    for line in lines:
        if line.count(":") == 2:
            all_results.add(line.split(":")[1].strip().upper())
    print(all_results)
    all_results_list = list(all_results)
    all_results_list.sort()
    print(all_results_list)
    # async with aiohttp.ClientSession() as session:
    #     for i in range(3, len(all_results_list), 3):
    #         elem_1 = all_results_list[i]
    #         elem_2 = all_results_list[i+1] if i+1 < len(all_results_list) else None
    #         elem_3 = all_results_list[i+2] if i+2 < len(all_results_list) else None
    #         print(elem_1, elem_2, elem_3)
    #         temp_form = fill_form_dict(elem_1, elem_2, elem_3)
    #         await post(session, temp_form)


if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
