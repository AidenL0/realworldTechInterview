# Sample answer key

1. `average` divides by `len(values) - 1`; it should divide by `len(values)`.
   Caught by `test_average` (visible) and `test_average_single` (hidden).
2. `clamp` uses `low` as the upper bound; it should use `high`.
   Caught only by `test_clamp_inside_range` (hidden).
