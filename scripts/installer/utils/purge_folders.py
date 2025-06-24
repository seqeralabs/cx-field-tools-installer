import os
import shutil
from pathlib import Path


def delete_pycache_folders(start_path: str | Path) -> int:
    """
    Recursively traverse a directory and delete all __pycache__ folders.

    Args:
        start_path: The root directory to start the search from.
                   Can be either a string path or a Path object.

    Returns:
        int: Number of __pycache__ folders deleted

    Example:
        >>> deleted = delete_pycache_folders("./my_project")
        >>> print(f"Deleted {deleted} __pycache__ folders")
    """
    if isinstance(start_path, str):
        start_path = Path(start_path)

    count = 0

    try:
        # Walk through directory tree
        for root, dirs, _ in os.walk(start_path, topdown=True):
            if "__pycache__" in dirs:
                cache_path = Path(root) / "__pycache__"
                try:
                    shutil.rmtree(cache_path)
                    count += 1
                except PermissionError:
                    print(f"Permission denied: Could not delete {cache_path}")
                except Exception as e:
                    print(f"Error deleting {cache_path}: {e}")

        return count

    except Exception as e:
        print(f"Error traversing directory {start_path}: {e}")
        return count
