# Changelog
This document details the changes I made, 
and how they impact the performance of the program.


All benchmarks are ran on a personal system with the following specs:
i9-13950HX,
128GB RAM

## Version 1.2.1

Added a check for new discoveries. There's probably so many, and they're just
wasted by the program otherwise.

:(

## Version 1.2
Core idea: It's possible to use a naive iddfs to achieve 
polynomial memory complexity at the sacrifice of O((n!)^2)time complexity. 
However, if we can check for repetition in an effective way, 
we can achieve ~= O(10^n) time complexity as well. If I didn't do a dumb,
here are the theoretical complexity:
```
Memory requirement:  O(d^3                 (1 additional set for each level, n(n+1)/2 items at most in set)
                    +recipeBookSize(d)     (recipes, which dominates here)
                    +numWords(d)           (storing optimal words, or *d for shortest paths)
Time requirement:    O(d!^2)               (Worst case)
                   ~=O(9^d)                (Experimental, due to collisions)
```
Empirically, here are the results up to depth 8, only storing words
of a certain depth and not the recipe in memory.

    DEPTH   |   SIZE   |   TIME   |   MEMORY
     2            29       <0.001     0.01MiB
     3            81       <0.001     0.02MiB
     4           211        0.005     0.03MiB
     5           486        0.036     0.06MiB
     6          1114        0.278     0.06MiB
     7          2682        2.077     0.18MiB
     8          6566       17.031     0.65MiB

### ~~Idea 0~~
~~number all of the words based on discovery order, and then DFS only accepts paths
with an increasing word sequence. This would reduce memory requirement... uhh...~~

This is WRONG, since it's possible such that
```
A+B --> E
B+E --> R (R has depth 2)
```

```
B+C --> H
C+D --> I (I has depth 2)
H+I --> J (J has depth 3)
J+B --> R 
```
(R < J since its depth is lower, but this is valid since ABCDER and ABCDHIJR are different).


### Idea 1
To account for situations such as: (We start with ABCD)
A+B --> E
C+D --> F
vs
C+D --> F
A+B --> E
We can check for ordering, just for the order of crafted items.
This would mean {a_i} < {a_j} for all i < j, 
where a_i is the index of the parent items.

Example:
```
Recipe: [-1, -1, -1, -1, 6, 1, 20]
6: 2 + 2 = Wind + Wind = Tornado
1: 0 + 0 = Water + Water = Lake
20: 4 + 5 = Lake + Tornado = Tsunami
```
would be ignored, since 6 < 1. We can always sort the list and come up with the same result.
(Proof omitted)

This is also experimentally correct up to depth 7, 
where the number of recipes is 2682, identical to previously.

Note that for this benchmark, recipes are saved to memory by mistake. 
However, I would not like to re-run since, with tracemalloc, the time
taken was almost 1/2 an hour.
Also, note that the entire recipe file is ~6.5MiB.

    DEPTH   |   SIZE   |   TIME   |   MEMORY
     2            29        0.001    (6.61MiB)
     3            81        0.002    (6.63MiB)
     4           211        0.016    (6.69MiB)
     5           486        0.197    (6.81MiB)
     6          1114        2.515    (7.08MiB)
     7          2682       34.360    (7.79MiB)
     8          6566      490.420    (9.68MiB)


### Idea 2
Check, for every new word, if it's possible to reach the target word 
using other combinations at the current step.
This could be done using a set() and then checking if the target word is in the set.

    DEPTH   |   SIZE   |   TIME   |   MEMORY
     2            29       <0.001     6.63MiB
     3            81        0.002     6.61MiB
     4           211        0.010     6.61MiB
     5           486        0.069     6.62MiB
     6          1114        0.532     6.63MiB
     7          2682        4.066     6.63MiB
     8          6566       33.269     6.63MiB

As we can see, memory usage increased a tiny bit (due to the set), but time usage decreased by a lot.

### Idea 3
All new words must use all previously crafted elements in its recipe.

However, since I am too lazy to figure out a good way to implement this rn,
we can reduce the condition to that the last item must use the 2nd last item. 
(Memory usage should not change)

    DEPTH   |   SIZE   |   TIME   |   MEMORY
     2            29       <0.001     6.61MiB
     3            81       <0.001     6.61MiB
     4           211        0.005     6.61MiB
     5           486        0.035     6.62MiB
     6          1114        0.279     6.63MiB
     7          2682        2.063     6.63MiB
     8          6566       17.068     6.63MiB

Also, this is not a completed version of the code, since I still read in
old recipes to check if the newly generated ones are the same depth. By
removing this check, memory usage may decrease a fair bit.

Realistically, remember that all the crafting recipes are stored in memory as well.
This is just optimizing for the algorithm itself, and it's been quite successful.
Although time complexity is still O(9^n) ish, the constant is quite low.
Also, this is multithread-able, although I may optimize for # of requests next update.

## Version 1.1
After all the changes made before dfs, here's the benchmarks:

    DEPTH   |   SIZE   |   TIME   |   MEMORY
     2            29        0.002       53KiB
     3            81        0.013      261KiB
     4           211        0.078     1.51MiB
     5           486        0.721     10.7MiB
     6          1114        5.607     70.5MiB
     7          2682       51.326      477MiB
     8          6566      474.911     3.76GiB

## Version 1
Original code by analog_hors + cache to file vs New Code v1
100 recipes:

Memory Usage:               2.09 --> 0.48 MiB

Time:                       0.02 --> 0.012 seconds

486 recipes: (distance 5)

Memory Usage:                531 --> 9.9 MiB

Time:                       1.89 --> 0.27 seconds

1000 recipes: (~distance 6)

Memory Usage:             8623.3 --> 52.5 MiB

Time:                        103 --> 1.75 seconds

Note: Estimated memory and time usage is both ~O(k^n), where k is a constant. k<=10?
