"""
Exit codes:
    0: SUCCESS
    1: NO_ACTION
    2: INVALID_WORKDIR
    3: NO_BENCHMARKS_FOUND
    4: INVALID_REGEX
"""

import logging
import textwrap
import re
from enum import IntEnum
import sys
import argparse
from pathlib import Path

RUN_ACTIONS = {'run', 'r', 'run_and_compare', 'rac'}
COMPARE_ACTIONS = {'compare', 'c', 'run_and_compare', 'rac'}
BENCHMARK_FILE = 'benchmarks.txt'

class ExitResult(IntEnum):
    SUCCESS = 0
    NO_ACTION = 1
    INVALID_WORKDIR = 2
    NO_BENCHMARKS_FOUND = 3
    INVALID_REGEX = 4

    def __str__(self):
        return self.name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from benchmark_helpers.benchmark_helpers import run_benchmarks, compare_benchmarks
except ImportError as e:
    logger.critical(f"Failed to import benchmark_helpers: {e}")
    sys.exit(99)

def main(args: argparse.Namespace, parser: argparse.ArgumentParser) -> ExitResult:
    """Entry point for the benchmark CLI. Handles argument parsing and action dispatch."""
    if args.action is None:
        logger.error("Error: No action specified.\n")
        parser.print_help()
        return ExitResult.NO_ACTION

    working_dir = Path(args.working_directory)
    if not working_dir.exists() or not working_dir.is_dir():
        logger.error(f"Error: Working directory {working_dir} does not exist or is not a directory.")
        return ExitResult.INVALID_WORKDIR
    
    benchmark_path = working_dir / BENCHMARK_FILE
    if not benchmark_path.is_file():
        logger.error(f"Error: benchmarks.txt not found in {working_dir}")
        return ExitResult.NO_BENCHMARKS_FOUND

    if args.action in RUN_ACTIONS:
        run_benchmarks(benchmark_path, args.iteration_name)

    if args.action in COMPARE_ACTIONS:
        try:
            pattern = re.compile(args.compare_name)
        except re.error as e:
            logger.error(f"Invalid regex pattern for compare_name: {e}")
            return ExitResult.INVALID_REGEX
        compare_benchmarks(benchmark_path, pattern)

    return ExitResult.SUCCESS

if __name__ == "__main__":
    epilog = textwrap.dedent("""\
    Examples:
       benchmark run
       benchmark run switched_to_array
       benchmark compare
       benchmark compare ".*cache"
       benchmark run_and_compare switched_to_array ".*cache"
    """)
    
    parser = argparse.ArgumentParser(
        prog='benchmark',
        description='Run and compare project benchmarks.',
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--version', action='version', version='benchmark 1.0')
    parser.add_argument('-w', '--working_directory', nargs='?', default='.', help='Directory where benchmark data is located')

    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    run_parser = subparsers.add_parser('run', aliases=['r'], help='Run benchmarks')
    run_parser.add_argument('iteration_name', nargs='?', default='recent', help='Name of iteration')

    compare_parser = subparsers.add_parser('compare', aliases=['c'], help='Compare iterations of benchmarks')
    compare_parser.add_argument('compare_name', nargs='?', default='.*', help='Regex pattern for benchmark names to be compared')

    run_and_compare_parser = subparsers.add_parser('run_and_compare', aliases=['rac'], help='Run and compare benchmarks')
    run_and_compare_parser.add_argument('iteration_name', nargs='?', default='recent', help='Name of iteration')
    run_and_compare_parser.add_argument('compare_name', nargs='?', default='.*', help='Regex pattern for benchmark names to be compared')

    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(ExitResult.NO_ACTION)

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled.")

    sys.exit(main(args, parser))