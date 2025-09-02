from pathlib import Path
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)

def time_to_str(time: float, unit: str) -> str:
    return f'{time:.2f} {unit}' if time is not None else 'N/A'

def strip_common_paths(paths: list[Path]) -> list[Path]:
    paths_copy = deepcopy(paths)
    lengths = [len(path.parts) for path in paths_copy]
    if len(lengths) == 0:
        logger.warning(f'No paths!')
        return []
    max_iterations = min(lengths)

    for _ in range(max_iterations):
        common_part = None
        for path in paths_copy:
            assert(len(path.parts) != 0)
            part = path.parts[0]
            if common_part is None:
                common_part = part
            elif common_part != part:
                return paths_copy

        for j in range(len(paths_copy)):
            parts = paths_copy[j].parts[1:]
            paths_copy[j] = Path(*parts)
    raise Exception("Reached maximum path part depth!")  