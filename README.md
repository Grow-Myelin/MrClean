# 🧹 Disk Space Cleanup Tool

Interactive CLI tool to find and clean up Python virtual environments and JavaScript node_modules folders, freeing up disk space while preserving your source code.

## Quick Start

```bash
# Scan current directory
python3 cleanup_tool.py

# Scan specific path
python3 cleanup_tool.py ~/Desktop

# Make it executable (one-time setup)
chmod +x cleanup_tool.py
./cleanup_tool.py
```

## Features

- ⚡ **Fast interactive scanning** - only scans current directory by default
- 🔍 **Recursive scan on demand** - check all subfolders when needed
- 🗂️ **Easy navigation** - move up/down folder hierarchy, cycle through siblings
- 🎯 **Selective cleaning** - clean current folder only or wipe entire trees
- 💾 **Space tracking** - see how much space you're freeing in real-time

## Commands

### Navigation
- `1-N` - Navigate into numbered subdirectory
- `u` - Go up one level (to parent folder)
- `n` - Next folder (same level)
- `p` - Previous folder (same level)

### Scanning
- `r` - Recursive scan (check all subfolders for packages)

### Cleaning
- `w` - Wipe all packages in current folder AND all subfolders recursively
- `c` - Clean only current folder (keep subfolders intact)

### Other
- `s` - Skip and continue
- `q` - Quit

## Usage Examples

### Clean up Desktop projects quickly
```bash
python3 cleanup_tool.py ~/Desktop
# Press 'r' to scan a folder recursively
# Press 'w' to wipe if packages found
# Press 'n' to move to next folder
# Repeat!
```

### Explore and clean selectively
```bash
python3 cleanup_tool.py ~/projects
# Press '1' to enter first subdirectory
# Press 'r' to check if it has packages
# Press 'c' to clean just this folder
# Press 'u' to go back up
# Press 'n' to check next sibling folder
```

## What Gets Cleaned

### Python Virtual Environments
Detects folders with:
- `pyvenv.cfg`
- `bin/activate`
- `Scripts/activate.bat` (Windows)

### JavaScript Dependencies
- `node_modules` folders

## Safety Features

- Only deletes venv and node_modules directories
- Source code, configs, and other files are preserved
- Shows size before deletion
- Real-time progress tracking
- Can reinstall packages anytime with `pip install -r requirements.txt` or `npm install`

## Tips

- Start with `r` (recursive scan) to see what's cleanable before diving in
- Use `n` to quickly cycle through many folders at the same level
- The tool is safe - your actual code is never touched!
- After cleanup, reinstall packages only in projects you're actively using

## Reinstalling Packages

After cleaning, you can always reinstall:

**Python:**
```bash
pip install -r requirements.txt
# or
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

**JavaScript:**
```bash
npm install
# or
yarn install
```