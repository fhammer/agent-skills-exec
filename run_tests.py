#!/usr/bin/env python3
"""Test runner script for Agent Skills Framework."""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
        return True
    else:
        print(f"\n❌ {description} - FAILED")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for Agent Skills Framework")
    parser.add_argument("--type", choices=["unit", "integration", "e2e", "all"],
                       default="all", help="Type of tests to run")
    parser.add_argument("--marker", help="Run tests with specific marker")
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--failfast", "-x", action="store_true",
                       help="Stop on first failure")
    parser.add_argument("--parallel", "-n", type=int,
                       help="Number of parallel workers (requires pytest-xdist)")
    parser.add_argument("--report", help="Generate HTML report at specified path")

    args = parser.parse_args()

    # Build pytest command
    cmd = ["python3", "-m", "pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Add failfast
    if args.failfast:
        cmd.append("-x")

    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Add test type filter
    test_paths = []
    markers = []

    if args.type == "unit":
        test_paths.append("tests/test_*.py")
        markers.append("unit")
    elif args.type == "integration":
        test_paths.append("tests")
        markers.extend(["integration", "not e2e", "not slow"])
    elif args.type == "e2e":
        test_paths.append("tests")
        markers.extend(["e2e"])
    else:  # all
        test_paths.append("tests")

    # Add custom marker
    if args.marker:
        markers.append(args.marker)

    # Apply markers
    if markers:
        cmd.extend(["-m", " and ".join(markers)])

    # Add test paths
    cmd.extend(test_paths)

    # Add HTML report
    if args.report:
        cmd.extend([f"--html={args.report}", "--self-contained-html"])

    # Run tests
    success = run_command(cmd, f"Tests ({args.type})")

    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Type: {args.type}")
    print(f"Status: {'✅ PASSED' if success else '❌ FAILED'}")

    if args.coverage and success:
        print(f"\nCoverage report: {Path.cwd() / 'htmlcov' / 'index.html'}")

    if args.report:
        print(f"\nHTML report: {Path.cwd() / args.report}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
