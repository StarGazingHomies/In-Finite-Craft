# Performance Notes
This document details how I am / plan to optimize for performance in the recipe finder.

# Version 1.1
After all of the changes made before dfs, here's the benchmarks:
(Ran on a 13950HX, 128GiB RAM)

    DEPTH   |   SIZE   |   TIME   |   MEMORY
     2            29        0.002       53KiB
     3            81        0.013      261KiB
     4           211        0.078     1.51MiB
     5           486        0.721     10.7MiB
     6          1114        5.607     70.5MiB
     7          2682       51.326      477MiB
     8          6566      474.911     3.76GiB

# Version 1
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
