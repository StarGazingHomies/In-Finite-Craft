# TODO

## Issues
- `main_new.py` - why is 5-step missing `Hot Spring`? (to debug)

## Optimizers
- Hybrid Step-Generation Preprocessing
- N-Step-Lookahead Generational Algorithm?
Maybe even alpha-beta pruning (using heuristic)?
- In-place Procedural Removal
- Visualization (trees!)
- Crafting Tree Location File Generation?
- OptimizerRecipeList and RecipeHandler common interface
- Queueing system for requests (instead of just locking)

## Main_New (Paralleization test)
- Note to self: Disk IO is the bottleneck, and so is compute for high-steps to an extent.
Removed disk IO in favour of keeping everything in ram again, but keeping
it an option when ram limitations are reached.

- See if there is a speed up by getting rid of async (and using requests instead of aiohttp)

- Add a threaded option (d2 then branch off and/or task based), 
to see if sacrificing a bit of "order" is worth it for access to more cores.
(Regardless of the runtime on my main pc, this will not be deployed 
because my old laptops only have <=6 cores, and they are needed for other stuff)



- Add saving and crash-handling logic to main_new
- Once 5-step is fixed, re-verify all low-step recipes up to 9-step.

### Main_New Shelved Ideas
- Lazy generation of recipes (not useful, unless the starting element set)
is very large (>1k elements), which almost never happens.
- Parallelize sqlite requests (if threading is helpful)