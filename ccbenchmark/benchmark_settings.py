from dataclasses import dataclass, field
from pathlib import Path
import yaml
from typing import Any

_LOCAL_SETTINGS_FILE = Path('./.ccbenchmark/settings.yaml')

@dataclass
class LocalSettings:
    benchmark_runnables_list: list[list[Path]] = field(default_factory=lambda: [])
    output_dir_list: list[Path] = field(default_factory=lambda: [])
    framework_name_list: list[str] = field(default_factory=lambda: [])
    output_format_list: list[str] = field(default_factory=lambda: [])

def load_local_settings() -> LocalSettings | None:
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