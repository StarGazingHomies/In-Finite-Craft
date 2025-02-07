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
- IMPORTANT: See if disk I/O or compute is the bottleneck, and fix them
to get very, very close to 50rps
- IDEA: Cache results that might be immediately used in the next step
  (next step is by default local query which can be slow if there's a lot of them)
- Add a threaded option (d1 then branch off), 
to see if sacrificing a bit of "order" is worth it for 
computational power
- Add saving and crash-handling logic to main_new
- Revisit some of the old low-step data so I can verify
up to 8-step or 9-step, because more have been found since
revivals.
- Parallelize sqlite requests

`mane-parallel` Shelved Ideas:
- Lazy generation of recipes (not useful, unless the starting element set)
is very large (>1k elements), which almost never happens.