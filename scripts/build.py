#!/usr/bin/env python3
"""
Build script for Banana Image MCP Server.

This script builds the distribution packages for PyPI upload using uv.
"""

from pathlib import Path
import shutil
import subprocess
import sys


def run_command(cmd: list[str], description: str, capture_output: bool = True) -> None:
    """Run a command and handle errors."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=capture_output, text=True)
        if result.stdout and capture_output:
            pass
    except subprocess.CalledProcessError as e:
        if e.stderr:
            pass
        sys.exit(1)


def clean_build_artifacts(root_dir: Path) -> None:
    """Clean previous build artifacts."""

    # Directories to clean
    dirs_to_clean = [
        root_dir / "dist",
        root_dir / "build",
        root_dir / "*.egg-info"
    ]

    for path in dirs_to_clean:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    # Also clean any .egg-info directories with glob
    for egg_info in root_dir.glob("*.egg-info"):
        if egg_info.is_dir():
            shutil.rmtree(egg_info)


def check_uv_available() -> bool:
    """Check if uv is available."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_build_deps(root_dir: Path) -> None:
    """Install build dependencies if not available."""

    if not check_uv_available():
        sys.exit(1)

    # Check if build is available
    try:
        subprocess.run(["uv", "run", "python", "-c", "import build"],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        run_command(["uv", "add", "--dev", "build"], "Installing build dependency")


def verify_package_config(root_dir: Path) -> None:
    """Verify package configuration is ready for build."""

    # Check required files
    required_files = [
        ("pyproject.toml", "Project configuration"),
        ("banana_image_mcp/__init__.py", "Package init"),
        ("banana_image_mcp/server.py", "Main server module"),
    ]

    for file_path, _description in required_files:
        full_path = root_dir / file_path
        if not full_path.exists():
            sys.exit(1)


def main():
    """Build the package."""
    root_dir = Path(__file__).parent.parent

    # Change to project root
    import os
    os.chdir(root_dir)

    # Verify configuration
    verify_package_config(root_dir)

    # Install build dependencies
    install_build_deps(root_dir)

    # Clean previous builds
    clean_build_artifacts(root_dir)

    # Build the package
    run_command(["uv", "run", "python", "-m", "build"], "Building source and wheel distributions")


    # List created files with details
    dist_dir = root_dir / "dist"
    if dist_dir.exists():
        total_size = 0
        for file in sorted(dist_dir.iterdir()):
            if file.is_file():
                size = file.stat().st_size
                total_size += size
                size / 1024




if __name__ == "__main__":
    main()
