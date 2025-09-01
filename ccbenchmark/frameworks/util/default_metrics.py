from enum import IntEnum

NON_AGGREGATED_METRICS = ['Time']
AGGREGATED_METRICS = ['μ', 'Med', 'Stddev', 'CV']

class MetricIndices(IntEnum):
    Time = 0
    Mean = 1
    Median = 2
    Stddev = 3
    CV = 4