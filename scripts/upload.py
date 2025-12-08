#!/usr/bin/env python3
"""
Upload script for Nano Banana MCP Server.

This script uploads the built distribution packages to PyPI using uv and twine.
Supports both TestPyPI (for testing) and production PyPI.
"""

import os
from pathlib import Path
import subprocess
import sys


def run_command(cmd: list[str], description: str, capture_output: bool = True) -> str | None:
    """Run a command and handle errors."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=capture_output, text=True)
        if result.stdout and capture_output:
            return result.stdout.strip()
        return None
    except subprocess.CalledProcessError as e:
        if e.stderr:
            pass
        return None


def check_dependencies() -> bool:
    """Check if required dependencies are available."""

    # Check uv
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

    # Check twine
    try:
        subprocess.run(["uv", "run", "python", "-c", "import twine"],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        result = subprocess.run(["uv", "add", "--dev", "twine"], capture_output=True)
        if result.returncode != 0:
            return False

    return True


def check_dist_files(root_dir: Path) -> list[Path]:
    """Check if distribution files exist and list them."""
    dist_dir = root_dir / "dist"

    if not dist_dir.exists():
        return []

    dist_files = list(dist_dir.glob("*.tar.gz")) + list(dist_dir.glob("*.whl"))

    if not dist_files:
        return []

    for file in dist_files:
        file.stat().st_size / 1024

    return dist_files


def check_pypirc() -> tuple[bool, bool]:
    """Check if .pypirc is configured."""
    pypirc_path = Path.home() / ".pypirc"

    if not pypirc_path.exists():
        return False, False

    content = pypirc_path.read_text()
    has_testpypi = "[testpypi]" in content
    has_pypi = "[pypi]" in content


    return has_testpypi, has_pypi


def show_pypirc_help():
    """Show help for configuring .pypirc."""


def get_package_version(root_dir: Path) -> str | None:
    """Extract package version from pyproject.toml."""
    pyproject_path = root_dir / "pyproject.toml"

    if not pyproject_path.exists():
        return None

    try:
        content = pyproject_path.read_text()
        for line in content.split("\n"):
            if line.strip().startswith("version = "):
                # Extract version from 'version = "0.1.0"'
                version = line.split("=")[1].strip().strip('"\'')
                return version
    except Exception:
        pass

    return None


def upload_to_repository(repository: str, dist_files: list[Path]) -> bool:
    """Upload to specified repository."""


    # First, check the package
    check_result = subprocess.run(
        ["uv", "run", "twine", "check"] + [str(f) for f in dist_files],
        capture_output=True, text=True
    )

    if check_result.returncode != 0:
        return False

    # Prepare twine command
    cmd = ["uv", "run", "twine", "upload"]

    if repository == "testpypi":
        cmd.extend(["--repository", "testpypi"])

    # Add files
    cmd.extend([str(f) for f in dist_files])


    try:
        subprocess.run(cmd, check=True, text=True)
        return True
    except subprocess.CalledProcessError:
        return False


def show_next_steps(repository: str, version: str):
    """Show next steps after successful upload."""
    if repository == "testpypi":
        pass
    else:
        pass


def main():
    """Main upload workflow."""
    root_dir = Path(__file__).parent.parent

    # Change to project root
    os.chdir(root_dir)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check distribution files
    dist_files = check_dist_files(root_dir)
    if not dist_files:
        sys.exit(1)

    # Get package version
    version = get_package_version(root_dir)
    if version:
        pass

    # Check .pypirc configuration
    has_testpypi, has_pypi = check_pypirc()

    # Interactive menu

    while True:
        try:
            choice = input("\nSelect option (1-4): ").strip()

            if choice == "1":
                if upload_to_repository("testpypi", dist_files):
                    show_next_steps("testpypi", version or "latest")
                break

            elif choice == "2":
                # Confirm production upload
                confirm = input("Continue? (yes/no): ").strip().lower()

                if confirm in ("yes", "y"):
                    if upload_to_repository("pypi", dist_files):
                        show_next_steps("pypi", version or "latest")
                else:
                    pass
                break

            elif choice == "3":
                show_pypirc_help()
                continue

            elif choice == "4":
                break

            else:
                pass

        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    main()
