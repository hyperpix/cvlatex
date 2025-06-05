#!/usr/bin/env python3
"""Utility script for removing old generated files."""
import os
import time
import argparse

DEFAULT_DIRS = ["output", "temp_sessions"]
DEFAULT_DAYS = 7


def cleanup_dir(path: str, max_age_days: int):
    """Remove files older than `max_age_days` in `path`."""
    now = time.time()
    removed = []
    if not os.path.exists(path):
        return removed
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if os.path.isfile(file_path):
            try:
                if now - os.path.getmtime(file_path) > max_age_days * 86400:
                    os.remove(file_path)
                    removed.append(name)
            except Exception as err:
                print(f"Could not remove {file_path}: {err}")
    return removed


def main():
    parser = argparse.ArgumentParser(description="Clean up generated files")
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help="Delete files older than this many days",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=DEFAULT_DIRS,
        help="Directories to clean",
    )
    args = parser.parse_args()

    for path in args.paths:
        removed = cleanup_dir(path, args.days)
        if removed:
            print(f"Removed {len(removed)} files from {path}")
        else:
            print(f"No old files found in {path}")


if __name__ == "__main__":
    main()
