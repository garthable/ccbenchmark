from dataclasses import dataclass, field
from pathlib import Path
import yaml

_LOCAL_SETTINGS_FILE = Path('./.ccbenchmark/settings.yaml')

@dataclass
class LocalSettings:
    bin_dirs: list[Path] = field(default_factory=lambda: [])
    output_dir: Path = field(default_factory=lambda: Path())
    framework: str = field(default_factory=lambda: '')

local_settings: LocalSettings = None

def save_local_settings():
    with open(_LOCAL_SETTINGS_FILE, 'w+') as file:
        settings_dict = local_settings.__dict__
        yaml.safe_dump(file, settings_dict)

def load_local_settings() -> None:
    global local_settings
    try:
        with open(_LOCAL_SETTINGS_FILE, 'r') as file:
            local_settings_yaml: dict = yaml.safe_load(file)
            bin_dirs = [Path(bin_dir) for bin_dir in local_settings_yaml['bin_dirs']]

            local_settings = LocalSettings(
                bin_dirs=bin_dirs, 
                output_dir=Path(local_settings_yaml['output_dir']),
                framework=local_settings_yaml['framework']
            )

    except FileNotFoundError:
        local_settings = None