#!/usr/bin/env python3
"""
Interactive tool to find and clean up Python venvs and JavaScript node_modules
to free up disk space while keeping your source code intact.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def get_dir_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    return total


def format_size(bytes_size: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def is_venv(path: Path) -> bool:
    """Check if directory is a Python virtual environment."""
    if not path.is_dir():
        return False
    # Check for common venv indicators
    indicators = [
        path / 'pyvenv.cfg',
        path / 'bin' / 'activate',
        path / 'Scripts' / 'activate.bat'  # Windows
    ]
    return any(indicator.exists() for indicator in indicators)


def is_node_modules(path: Path) -> bool:
    """Check if directory is a node_modules folder."""
    return path.is_dir() and path.name == 'node_modules'


def find_cleanable_in_dir(directory: Path) -> List[Tuple[Path, str, int]]:
    """
    Find cleanable directories (venvs and node_modules) directly in the given directory.
    Only scans one level deep, returns list of tuples: (path, type, size_in_bytes)
    """
    results = []
    try:
        for entry in directory.iterdir():
            if not entry.is_dir():
                continue

            # Check if it's a cleanable directory
            if is_venv(entry):
                size = get_dir_size(entry)
                results.append((entry, 'venv', size))
            elif is_node_modules(entry):
                size = get_dir_size(entry)
                results.append((entry, 'node_modules', size))
    except (PermissionError, OSError):
        pass

    return results


def get_subdirs(directory: Path) -> List[Path]:
    """Get all subdirectories in the given directory."""
    subdirs = []
    try:
        for entry in directory.iterdir():
            if entry.is_dir() and not is_venv(entry) and not is_node_modules(entry):
                subdirs.append(entry)
    except (PermissionError, OSError):
        pass
    return sorted(subdirs)


def scan_recursive(directory: Path, max_depth: int = 10) -> Tuple[int, int]:
    """
    Recursively scan for cleanable directories in subdirectories.
    Returns tuple of (total_count, total_size_bytes)
    """
    count = 0
    total_size = 0

    def scan_dir(current_path: Path, depth: int = 0):
        nonlocal count, total_size
        if depth > max_depth:
            return

        try:
            for entry in current_path.iterdir():
                if not entry.is_dir():
                    continue

                # Check if it's a cleanable directory
                if is_venv(entry) or is_node_modules(entry):
                    size = get_dir_size(entry)
                    count += 1
                    total_size += size
                    continue  # Don't scan inside cleanable dirs

                # Recursively scan subdirectories
                scan_dir(entry, depth + 1)
        except (PermissionError, OSError):
            pass

    scan_dir(directory)
    return count, total_size


def delete_directory(path: Path) -> bool:
    """Safely delete a directory and return success status."""
    try:
        shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"  ❌ Error deleting {path}: {e}")
        return False


def wipe_all_cleanable(directory: Path, stats: dict) -> int:
    """
    Recursively wipe all venvs and node_modules in directory and subdirectories.
    Returns bytes freed.
    """
    freed = 0

    # Find and delete cleanable dirs in current directory
    cleanable = find_cleanable_in_dir(directory)
    for path, type_, size in cleanable:
        if delete_directory(path):
            print(f"   ✅ Deleted {path.relative_to(directory.parent)} ({format_size(size)})")
            freed += size
            stats['deleted_count'] += 1

    # Recursively process subdirectories
    subdirs = get_subdirs(directory)
    for subdir in subdirs:
        freed += wipe_all_cleanable(subdir, stats)

    return freed


def navigate_directory(directory: Path, stats: dict, start_path: Path, parent_subdirs: Optional[List[Path]] = None, current_idx: Optional[int] = None):
    """
    Interactively navigate and explore a directory tree with full control.
    parent_subdirs: list of sibling directories at this level
    current_idx: index of current directory in parent_subdirs
    """
    # Track if recursive scan found items
    has_recursive_items = None
    recursive_count = 0
    recursive_size = 0

    while True:
        # Find cleanable items in current directory
        cleanable = find_cleanable_in_dir(directory)
        cleanable_size = sum(size for _, _, size in cleanable)

        # Get subdirectories
        subdirs = get_subdirs(directory)

        # Display current directory info
        print(f"\n{'=' * 60}")
        print(f"📁 Current: {directory}")
        print(f"{'=' * 60}")

        if cleanable:
            print(f"\n🗑️  Cleanable items:")
            for path, type_, size in cleanable:
                print(f"   • {path.name} ({type_}) - {format_size(size)}")
            print(f"   Subtotal: {format_size(cleanable_size)}")
        else:
            print(f"\n✨ No cleanable items in this directory")

        # Show recursive scan results if available
        if has_recursive_items:
            print(f"\n🔍 Recursive scan: {recursive_count} items in subfolders ({format_size(recursive_size)})")

        if subdirs:
            print(f"\n📂 Subdirectories ({len(subdirs)}):")
            for idx, subdir in enumerate(subdirs, 1):
                print(f"   {idx}. {subdir.name}")
        else:
            print(f"\n📂 No subdirectories")

        # Determine if we can wipe (either local cleanable items or recursive items found)
        can_wipe = cleanable or has_recursive_items

        # Check if we can navigate to next/previous sibling
        has_next = parent_subdirs and current_idx is not None and current_idx < len(parent_subdirs) - 1
        has_prev = parent_subdirs and current_idx is not None and current_idx > 0

        # Show options
        print(f"\n{'─' * 60}")
        print("Actions:")
        if can_wipe:
            print("   w - Wipe all packages here and in ALL subfolders")
        if cleanable:
            print("   c - Clean only this folder")
        if subdirs:
            print("   1-{} - Navigate into subdirectory (enter number)".format(len(subdirs)))
            print("   r - Recursive scan (check all subfolders for packages)")
        if directory != start_path:
            print("   u - Go up one level")
        if has_next:
            print("   n - Next folder (same level)")
        if has_prev:
            print("   p - Previous folder (same level)")
        print("   s - Skip and continue")
        print("   q - Quit")
        print(f"{'─' * 60}")

        # Get user input
        choice = input("Choice: ").lower().strip()

        if choice == 'q':
            print("\n👋 Quitting...")
            sys.exit(0)

        elif choice == 's':
            return

        elif choice == 'u' and directory != start_path:
            # Go up one level
            return 'up'

        elif choice == 'n' and has_next:
            # Go to next sibling folder
            return 'next'

        elif choice == 'p' and has_prev:
            # Go to previous sibling folder
            return 'prev'

        elif choice == 'r' and subdirs:
            # Recursive scan
            print(f"\n🔍 Scanning all subfolders recursively...")
            count, size = scan_recursive(directory)
            if count > 0:
                print(f"📊 Found {count} cleanable items in subfolders")
                print(f"💾 Total potential space: {format_size(size)}")
                # Store results for wipe option
                has_recursive_items = True
                recursive_count = count
                recursive_size = size
            else:
                print(f"✨ No cleanable items found in any subfolders")
                has_recursive_items = False
            input("\nPress Enter to continue...")
            continue

        elif choice == 'w' and can_wipe:
            # Wipe everything recursively
            print(f"🧹 Wiping all packages from {directory.name}/ and subfolders...")
            freed = wipe_all_cleanable(directory, stats)
            stats['total_freed'] += freed
            print(f"✨ Freed {format_size(freed)} from this tree")
            # Reset recursive scan state after wiping
            has_recursive_items = None
            recursive_count = 0
            recursive_size = 0
            continue

        elif choice == 'c' and cleanable:
            # Clean only current directory
            freed = 0
            for path, type_, size in cleanable:
                if delete_directory(path):
                    print(f"   ✅ Deleted {path.name}")
                    freed += size
                    stats['deleted_count'] += 1
            stats['total_freed'] += freed
            print(f"✨ Freed {format_size(freed)}")
            # Stay in current directory (will re-scan and show updated state)
            continue

        elif choice.isdigit() and subdirs:
            idx = int(choice) - 1
            if 0 <= idx < len(subdirs):
                # Navigate into subdirectory, pass sibling info
                subdir_idx = 0
                while subdir_idx < len(subdirs):
                    result = navigate_directory(subdirs[subdir_idx], stats, start_path, subdirs, subdir_idx)
                    if result == 'up':
                        # User went up from child, stay here
                        break
                    elif result == 'next':
                        # Move to next sibling
                        subdir_idx += 1
                        if subdir_idx >= len(subdirs):
                            print("   ℹ️  No more folders at this level")
                            subdir_idx = len(subdirs) - 1  # Stay at last
                    elif result == 'prev':
                        # Move to previous sibling
                        subdir_idx -= 1
                        if subdir_idx < 0:
                            print("   ℹ️  Already at first folder")
                            subdir_idx = 0  # Stay at first
                    else:
                        # User skipped, move to next
                        subdir_idx += 1
                continue
            else:
                print(f"❌ Invalid number. Choose 1-{len(subdirs)}")
                continue

        else:
            print("❌ Invalid choice. Try again.")
            continue


def main():
    print("🧹 Interactive Disk Space Cleanup Tool")
    print("=" * 60)
    print("Navigate folders freely - list subdirs, go up/down levels.\n")

    # Get search path
    if len(sys.argv) > 1:
        search_path = Path(sys.argv[1]).resolve()
    else:
        search_path = Path.cwd()

    if not search_path.exists():
        print(f"❌ Error: Path '{search_path}' does not exist.")
        sys.exit(1)

    # Track statistics
    stats = {
        'total_freed': 0,
        'deleted_count': 0
    }

    # Get siblings if we're not at root
    if search_path.parent != search_path:
        parent_subdirs = get_subdirs(search_path.parent)
        try:
            current_idx = parent_subdirs.index(search_path)
        except ValueError:
            parent_subdirs = None
            current_idx = None
    else:
        parent_subdirs = None
        current_idx = None

    # Start interactive navigation
    navigate_directory(search_path, stats, search_path, parent_subdirs, current_idx)

    # Summary
    print("\n" + "=" * 60)
    print(f"🎉 Cleanup complete!")
    print(f"   Deleted: {stats['deleted_count']} directories")
    print(f"   Freed up: {format_size(stats['total_freed'])}")


if __name__ == "__main__":
    main()
