"""Main file for ccbenchmark.

Contains ExitResult, entrypoint function, and main function.
ExitResult contains values returned on failure.
Exit codes:
    0: SUCCESS
    1: NO_ACTION
    2: INVALID_WORKDIR
    3: NO_BENCHMARKS_FOUND
    4: INVALID_REGEX
    5: NO_LOCAL_SETTINGS

Entrypoint function handles parsing arguments and runs main.
Main function acts on the result of the parser and runs the program.
"""

import logging
import textwrap
from enum import IntEnum
import sys
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

from ccbenchmark.benchmark_helpers import run_benchmarks, compare_benchmarks
from ccbenchmark.benchmark_settings import load_local_settings
from ccbenchmark.benchmark_framework import import_framework

RUN_ACTIONS = {'run', 'r', 'run_and_compare', 'rac'}
COMPARE_ACTIONS = {'compare', 'c', 'run_and_compare', 'rac'}
BENCHMARK_FILE = 'benchmarks.txt'

class ExitResult(IntEnum):
    SUCCESS = 0
    NO_ACTION = 1
    INVALID_WORKDIR = 2
    NO_BENCHMARKS_FOUND = 3
    INVALID_REGEX = 4
    NO_LOCAL_SETTINGS = 5

    def __str__(self):
        return self.name

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
    
    local_settings = load_local_settings()
    if local_settings is None:
        logger.error(f"Error: No local settings found!")
        return ExitResult.NO_LOCAL_SETTINGS
    
    frameworks = [
        import_framework(framework, output_format)
        for framework, output_format in zip(local_settings.framework_name_list, local_settings.output_format_list)
    ]

    if args.action in RUN_ACTIONS:
        zipped_inputs = zip(
            local_settings.benchmark_runnables_list, 
            local_settings.output_dir_list, 
            frameworks, 
            local_settings.output_format_list
        )
        for runnables, output_dir, framework, output_format in zipped_inputs:
            run_benchmarks(runnables, output_dir, framework, output_format, args.iteration_name)

    if args.action in COMPARE_ACTIONS:
        compare_benchmarks(local_settings.output_dir_list, frameworks)

    return ExitResult.SUCCESS

def entrypoint():
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

if __name__ == '__main__':
    entrypoint()