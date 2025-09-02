from enum import IntEnum

METRICS = ['Time', 'μ', 'Stddev', 'Med', 'Mad', 'Min', 'Max', 'CV']

class MetricIndices(IntEnum):
    Time   = 0
    Mean   = 1
    Stddev = 2
    Median = 3
    Mad    = 4
    Min    = 5
    Max    = 6
    CV     = 7