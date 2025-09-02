import pyperf

def bm_6():
    for i in range(1_000_000):
        pass

def bm_7():
    for i in range(10_000_000):
        pass

runner = pyperf.Runner()

runner.bench_func('bm_6', bm_6)
runner.bench_func('bm_7', bm_7)