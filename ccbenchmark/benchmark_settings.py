from dataclasses import dataclass
from pathlib import Path
import yaml

_local_settings_file = Path('./.ccbenchmark/settings.yaml')

@dataclass
class LocalSettings:
    __slots__ = ("bin_dirs", "output_dir")

    bin_dirs: list[Path]
    output_dir: Path

def save_local_settings(settings: LocalSettings):
    with open(_local_settings_file, 'x') as file:
        settings_dict = settings.__dict__
        yaml.safe_dump(file, settings_dict)

def load_local_settings() -> LocalSettings | None:
    local_settings = None
    try:
        with open(_local_settings_file, 'r') as file:
            local_settings_yaml: dict = yaml.safe_load(file)
            bin_dirs = [Path(bin_dir) for bin_dir in local_settings_yaml['bin_dirs']]

            local_settings = LocalSettings(
                bin_dirs=bin_dirs, 
                output_dir=Path(local_settings_yaml['output_dir'])
            )

    except FileNotFoundError:
        pass
    return local_settings