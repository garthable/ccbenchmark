from typing import Generator, Any
from io import TextIOWrapper
from pathlib import Path
from collections.abc import Iterable
import logging
import subprocess

import json
import csv

from ccbenchmark.benchmark_data import BenchmarkTime, TimeUnit
from ccbenchmark.frameworks.util.metrics import MetricIndices
from ccbenchmark.frameworks.util.parse_result import ParseResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

SUPPORTED_FORMATS = {'json', 'csv', 'console'}

def run_single_benchmark(binary_path: Path, output_path: Path, output_format: str) -> int:
    """Runs a single benchmark binary and writes output to the given path."""
    cmd = [
        binary_path, 
        f'--benchmark_out={output_path}', 
        f'--benchmark_out_format={output_format}', 
        '--benchmark_report_aggregates_only=false'
    ]

    return subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=False)

def parse(file_stream: TextIOWrapper, file_path: Path) -> Generator[ParseResult, None, None]:
    if file_path.suffix == '.json':
        json_content: dict = json.load(file_stream)
        for parse_result in parse_json(json_content):
            yield parse_result
    elif file_path.suffix == '.csv':
        csv_reader = csv.reader(file_stream)
        for parse_result in parse_csv(csv_reader):
            yield parse_result
    elif file_path.suffix == '.console':
        for parse_result in parse_console(file_stream):
            yield parse_result
    else:
        raise NotImplementedError

class SkipBenchmark(Exception):
    pass

def parse_json(json_contents: dict) -> Generator[ParseResult, None, None]:
    """Adds json file to BenchmarkData"""
    try:
        benchmarks: list[dict] = json_contents['benchmarks']
    except KeyError:
        logger.warning(f"Missing 'benchmarks' in JSON file. Failed to add JSON file.")
        return

    for benchmark in benchmarks:
        def get_value(key: str) -> any:
            try:
                value = benchmark[key]
            except KeyError:
                logger.warning(f"Missing '{key}' in JSON file. Failed to add entry.")
                raise SkipBenchmark()
            return value
        
        try:
            name: str = get_value('run_name')
            real_time_value: float = get_value('real_time')
            cpu_time_value: float = get_value('cpu_time')
            time_unit: str = get_value('time_unit')
            repetitions: int = get_value('repetitions')
            run_type: str = get_value('run_type')
        except SkipBenchmark:
            continue

        aggregate_name = benchmark.get('aggregate_name')

        if repetitions > 1 and run_type == 'iteration':
            continue
        if aggregate_name is not None and aggregate_name == 'cv':
            cpu_time_value *= 100.0
            real_time_value *= 100.0
        result = create_parse_result(name, real_time_value, cpu_time_value, time_unit, aggregate_name)
        if result is None:
            continue
        yield result

def parse_csv(csv_reader: Iterable[list[str]]) -> Generator[ParseResult, None, None]:
    name_to_index: dict[str, int] = {}
    for row in csv_reader:
        if len(row) < 10:
            continue
        if name_to_index == {}:
            for i, entry in enumerate(row):
                name_to_index[entry] = i
            continue

        def get_value(key: str) -> any:
            try:
                index = name_to_index[key]
            except KeyError:
                logger.warning(f"Missing '{key}' in CSV file. Failed to add entry.")
                raise SkipBenchmark()
            
            try:
                value = row[index]
            except IndexError:
                logger.warning(f"Index '{index}' from key '{key}' is out of bounds. Failed to add entry.")
                raise SkipBenchmark()
            return value
        
        try:
            raw_name: str = get_value('name')
            real_time_value = float(get_value('real_time'))
            cpu_time_value = float(get_value('cpu_time'))
            time_unit: str = get_value('time_unit')
        except SkipBenchmark:
            continue

        repeats = 1
        for segment in raw_name.split('/'):
            key_value_pair = segment.split(':')
            if len(key_value_pair) <= 1:
                continue
            if key_value_pair[0] == 'repeats':
                repeats = int(key_value_pair[1].split('_')[0])
                break
        aggregated = repeats > 1
        
        split_raw_name = raw_name.split('_')
        if aggregated and split_raw_name[-1] in {'mean', 'median', 'stddev', 'cv'}:
            aggregate_name = split_raw_name[-1]
            name = '_'.join([segment for segment in split_raw_name[:-1]])
            if aggregate_name == 'cv':
                real_time_value *= 100.0
                cpu_time_value *= 100.0
        elif not aggregated:
            aggregate_name = None
            name = raw_name
        else:
            continue

        result = create_parse_result(name, real_time_value, cpu_time_value, time_unit, aggregate_name)
        if result is None:
            continue
        yield result

def parse_console(console_contents: TextIOWrapper) -> Generator[ParseResult, None, None]:
    dashed_lines = 0
    name_to_index: dict[str, int] = {'name': 0, 'real_time': 1, 'time_unit': 2, 'cpu_time': 3}
    for line in console_contents:
        if dashed_lines < 2:
            if len(line) > 0 and line[0] == '-':
                dashed_lines += 1
            continue
        split_line = list(filter(None, line.split(' ')))
        
        def get_value(key: str) -> any:
            try:
                index = name_to_index[key]
            except KeyError:
                logger.warning(f"Missing '{key}' in CSV file. Failed to add entry.")
                raise SkipBenchmark()
            
            try:
                value = split_line[index]
            except IndexError:
                logger.warning(f"Index '{index}' from key '{key}' is out of bounds. Failed to add entry.")
                raise SkipBenchmark()
            return value
        try:
            raw_name: str = get_value('name')
            real_time_value = float(get_value('real_time'))
            cpu_time_value = float(get_value('cpu_time'))
            time_unit: str = get_value('time_unit')
        except SkipBenchmark:
            continue

        repeats = 1
        for segment in raw_name.split('/'):
            key_value_pair = segment.split(':')
            if len(key_value_pair) <= 1:
                continue
            if key_value_pair[0] == 'repeats':
                repeats = int(key_value_pair[1].split('_')[0])
                break
        aggregated = repeats > 1
        
        split_raw_name = raw_name.split('_')
        if aggregated and split_raw_name[-1] in {'mean', 'median', 'stddev', 'cv'}:
            aggregate_name = split_raw_name[-1]
            name = '_'.join([segment for segment in split_raw_name[:-1]])
        elif not aggregated:
            aggregate_name = None
            name = raw_name
        else:
            continue

        result = create_parse_result(name, real_time_value, cpu_time_value, time_unit, aggregate_name)
        if result is None:
            continue
        yield result
        

def create_parse_result(name: str, real_time_value: float, cpu_time_value: float, 
                        time_unit: str, aggregate_name: str | None) -> ParseResult | None:
    
    real_time = BenchmarkTime(real_time_value, time_unit)
    cpu_time = BenchmarkTime(cpu_time_value, time_unit)

    if aggregate_name is None:
        return ParseResult(real_time, cpu_time, name, MetricIndices.Time.value)

    if aggregate_name == 'mean':
        return ParseResult(real_time, cpu_time, name, MetricIndices.Mean.value)
    elif aggregate_name == 'median':
        return ParseResult(real_time, cpu_time, name, MetricIndices.Median.value)
    elif aggregate_name == 'stddev':
        return ParseResult(real_time, cpu_time, name, MetricIndices.Stddev.value)
    elif aggregate_name == 'cv':
        real_time.time_unit = TimeUnit.PERCENTAGE
        cpu_time.time_unit = TimeUnit.PERCENTAGE

        return ParseResult(real_time, cpu_time, name, MetricIndices.CV.value)
    else:
        logger.warning(f"Unknown aggregate_name: {aggregate_name}")
        return None