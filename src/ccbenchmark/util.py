"""Utility functions shared across ccbenchmark modules."""

from pathlib import Path
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)

def strip_common_paths(paths: list[Path]) -> list[Path]:
    """Remove common leading path components from a list of paths.

    For example:
        ['/a/b/c', '/a/b/d'] -> ['c', 'd']

    Args:
        paths (list[Path]): List of paths to process.

    Returns:
        list[Path]: A new list of paths with the shared leading components removed.
        If the input is empty, returns an empty list.
    """
    paths_copy = deepcopy(paths)
    lengths = [len(path.parts) for path in paths_copy]
    if len(lengths) == 0:
        logger.warning(f'No paths!')
        return []
    max_iterations = min(lengths) - 1

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
    return paths_copy