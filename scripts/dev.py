#!/usr/bin/env python3
"""Development utility script for Starship project."""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests."""
    print("Running tests...")
    subprocess.run(["uv", "run", "pytest", "tests/"], check=True)


def run_linting():
    """Run code linting."""
    print("Running linting...")
    subprocess.run(["uv", "run", "ruff", "check", "src/"], check=True)
    subprocess.run(["uv", "run", "mypy", "src/"], check=True)


def format_code():
    """Format code."""
    print("Formatting code...")
    subprocess.run(["uv", "run", "ruff", "format", "src/", "tests/"], check=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Development utilities")
    parser.add_argument("command", choices=["test", "lint", "format"], help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "test":
        run_tests()
    elif args.command == "lint":
        run_linting()
    elif args.command == "format":
        format_code()


if __name__ == "__main__":
    main()