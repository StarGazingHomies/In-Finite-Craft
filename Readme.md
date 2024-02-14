# In Finite Craft

A tool that helps users optimize their Infinite Craft routes.

The algorithm used is a heavily optimized iterative deepening depth-first search.

Every time a new depth is completed, I will publish the recipes as a release.

## Usage

Requires Python 3.9~3.11 (I'm not that familiar with Python versions, but
there's a few different versions installed on each machine I've run this on)

Run `main.py` to search.

To edit any settings, edit `init_state` for your starting state if you
have an existing recipe, and `recipe.py` for how recipes are handled.

If you want to make sure your speedrun route has missing elements, 
repeats, or unused elements, run `speedrun.txt`. It must be in the format
of `x + y -> z`.

Currently, the script does not accept CLI arguments.
