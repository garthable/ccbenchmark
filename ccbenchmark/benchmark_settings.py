from dataclasses import dataclass, field
from pathlib import Path
import yaml

_LOCAL_SETTINGS_FILE = Path('./.ccbenchmark/settings.yaml')

@dataclass
class LocalSettings:
    benchmark_runnables: list[Path] = field(default_factory=lambda: [])
    output_dir: Path = field(default_factory=lambda: Path())
    framework: str = field(default_factory=lambda: '')
    output_format: str = field(default_factory=lambda: '')

def load_local_settings() -> LocalSettings | None:
    try:
        with open(_LOCAL_SETTINGS_FILE, 'r') as file:
            local_settings_yaml: dict = yaml.safe_load(file)
            benchmark_runnables = [Path(bin_dir) for bin_dir in local_settings_yaml['benchmark_runnables']]

            return LocalSettings(
                benchmark_runnables=benchmark_runnables, 
                output_dir=Path(local_settings_yaml['output_dir']),
                framework=local_settings_yaml['framework'],
                output_format=local_settings_yaml['output_format']
            )

    except FileNotFoundError:
        return None