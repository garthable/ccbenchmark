import argparse
from pathlib import Path
from benchmark_helpers.benchmark_data import *
from benchmark_helpers.benchmark_helpers import run_benchmarks, compare_benchmarks

def main(args):
    working_dir = Path(args.working_directory)
    benchmark_path = working_dir / 'benchmarks.txt'
    if args.action in {'run', 'r', 'run_and_compare', 'rac'}:
        run_benchmarks(benchmark_path, args.tag)
    if args.action in {'compare', 'c', 'run_and_compare', 'rac'}:
        compare_benchmarks(benchmark_path, args.compare_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='benchmark'
    )

    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    run_parser = subparsers.add_parser('run', aliases=['r'])
    run_parser.add_argument('tag', nargs='?', default='recent')

    compare_parser = subparsers.add_parser('compare', aliases=['c'])
    compare_parser.add_argument('compare_name', nargs='?', default='.*')

    run_and_compare_parser = subparsers.add_parser('run_and_compare', aliases=['rac'])
    run_and_compare_parser.add_argument('tag', nargs='?', default='recent')
    run_and_compare_parser.add_argument('compare_name', nargs='?', default='.*')

    parser.add_argument('-w', '--working_directory', nargs='?', default='')

    args = parser.parse_args()

    main(args)