from dataclasses import dataclass, field
from pathlib import Path
import yaml

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
            local_settings_yaml: dict = yaml.safe_load(file)

            default_benchmark_runnables = []
            default_output_dir = None
            default_framework_name = None
            default_output_format = None

            benchmark_runnables = [
                Path(bin_dir) 
                for bin_dir in local_settings_yaml.get('benchmark_runnables', default_benchmark_runnables)
            ]

            return LocalSettings(
                benchmark_runnables_list=[benchmark_runnables], 
                output_dir_list=[Path(local_settings_yaml.get('output_dir', default_output_dir))],
                framework_name_list=[local_settings_yaml.get('framework', default_framework_name)],
                output_format_list=[local_settings_yaml.get('output_format', default_output_format)]
            )

    except FileNotFoundError:
        return None