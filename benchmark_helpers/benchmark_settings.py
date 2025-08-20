from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class GlobalSettings:
    __slots__ = ()

global_settings: GlobalSettings

_local_settings_file = Path('./.ccbenchmark/settings.yaml')
_global_settings_file = Path(f'{__file__}/../.settings/settings.yaml')

@dataclass
class LocalSettings:
    __slots__ = ("bin_directory", "output_directory")

    bin_directory: Path
    output_directory: Path

def save_global_settings():
    with open(_global_settings_file, 'x') as file:
        settings_dict = global_settings.__dict__
        yaml.safe_dump(file, settings_dict)

def save_local_settings(settings: LocalSettings):
    with open(_local_settings_file, 'x') as file:
        settings_dict = settings.__dict__
        yaml.safe_dump(file, settings_dict)

def load_global_settings() -> GlobalSettings | None:
    global_settings = None
    try:
        with open(_global_settings_file, 'r') as file:
            global_settings = GlobalSettings()
            global_settings_yaml: dict = yaml.safe_load(file)
            for k, v in global_settings_yaml.items():
                global_settings.__setattr__(k, v)
    except FileNotFoundError:
        pass
    return global_settings

def load_local_settings() -> LocalSettings | None:
    local_settings = None
    try:
        with open(_local_settings_file, 'r') as file:
            local_settings_yaml: dict = yaml.safe_load(file)
            local_settings = LocalSettings(
                bin_directory=Path(local_settings_yaml['bin_directory']), 
                output_directory=Path(local_settings_yaml['output_directory'])
            )

    except FileNotFoundError:
        pass
    return local_settings