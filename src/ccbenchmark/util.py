from pathlib import Path
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)

def strip_common_paths(paths: list[Path]) -> list[Path]:
    paths_copy = deepcopy(paths)
    lengths = [len(path.parts) for path in paths_copy]
    if len(lengths) == 0:
        logger.warning(f'No paths!')
        return []
    max_iterations = min(lengths)

    for i in range(max_iterations):
        if max_iterations - i == 1:
            return paths_copy
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