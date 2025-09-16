"""
Local benchmark settings.

This module defines `LocalSettings`, a container for storing framework names, 
benchmark runnables, output directories, and output formats loaded from 
`.ccbenchmark/settings.yaml`. It also provides `load_local_settings()` to parse 
the YAML file and return a `LocalSettings` object.
"""

from dataclasses import dataclass, field
from pathlib import Path
import yaml

_LOCAL_SETTINGS_FILE = Path('./.ccbenchmark/settings.yaml')

@dataclass
class LocalSettings:
    """Stores local benchmark configuration loaded from `.ccbenchmark/settings.yaml`.

    Attributes:
        benchmark_runnables_list (list[list[Path]]): 
            List of lists of benchmark executable paths for each framework.
        output_dir_list (list[Path]): 
            List of output directories corresponding to each framework.
        framework_name_list (list[str]): 
            List of framework names.
        output_format_list (list[str]): 
            List of output formats (e.g., 'json', 'csv') for each framework.
    """
    benchmark_runnables_list: list[list[Path]] = field(default_factory=lambda: [])
    output_dir_list: list[Path] = field(default_factory=lambda: [])
    framework_name_list: list[str] = field(default_factory=lambda: [])
    output_format_list: list[str] = field(default_factory=lambda: [])

def load_local_settings() -> LocalSettings | None:
    """Load local benchmark settings from `.ccbenchmark/settings.yaml`.

    Parses the YAML file and constructs a `LocalSettings` object containing
    framework names, benchmark runnable paths, output directories, and output 
    formats. If the file does not exist, returns None.

    Returns:
        LocalSettings | None: 
            A `LocalSettings` object if the YAML file exists, otherwise `None`.
    """
    try:
        with open(_LOCAL_SETTINGS_FILE, 'r') as file:
            local_settings_yaml: dict[str, dict] = yaml.safe_load(file)
            local_settings = LocalSettings()

            default_benchmark_runnables = []
            default_output_dir = None
            default_output_format = None

            for framework_name, value in local_settings_yaml.items():
                benchmark_runnables = [
                    Path(bin_dir) 
                    for bin_dir in value.get('benchmark_runnables', default_benchmark_runnables)
                ]
                output_dir = Path(value.get('output_dir', default_output_dir))
                output_format = value.get('output_format', default_output_format)

                local_settings.benchmark_runnables_list.append(benchmark_runnables)
                local_settings.output_dir_list.append(output_dir)
                local_settings.framework_name_list.append(framework_name)
                local_settings.output_format_list.append(output_format)

        return local_settings

    except FileNotFoundError:
        return None