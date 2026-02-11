#!/usr/bin/env python3
"""Script to copy feature files from openCypher TCK to the runner.

Usage:
    python setup_features.py /path/to/openCypher/tck/features
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def copy_features(source_dir: Path, target_dir: Path) -> None:
    """Copy feature files from source to target directory.

    Args:
        source_dir: Source directory containing .feature files
        target_dir: Target directory where features should be copied
    """
    if not source_dir.exists():
        print(f"Error: Source directory does not exist: {source_dir}")
        sys.exit(1)

    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Find all .feature files
    feature_files = list(source_dir.rglob("*.feature"))

    if not feature_files:
        print(f"Warning: No .feature files found in {source_dir}")
        return

    print(f"Found {len(feature_files)} feature files")

    # Copy each feature file, preserving directory structure
    for feature_file in feature_files:
        # Get relative path from source_dir
        rel_path = feature_file.relative_to(source_dir)

        # Create target path
        target_file = target_dir / rel_path

        # Create parent directories
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(feature_file, target_file)
        print(f"Copied: {rel_path}")

    print(f"\nSuccessfully copied {len(feature_files)} feature files to {target_dir}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python setup_features.py /path/to/openCypher/tck/features")
        print("\nExample:")
        print("  python setup_features.py ../tck/features")
        sys.exit(1)

    source_dir = Path(sys.argv[1]).resolve()
    target_dir = Path(__file__).parent / "features"

    print(f"Source directory: {source_dir}")
    print(f"Target directory: {target_dir}")
    print()

    copy_features(source_dir, target_dir)


if __name__ == "__main__":
    main()
