#!/usr/bin/env python3
"""
Unified test runner for all FantasyFootball test suites.

Usage:
    python test_runner.py                    # Run all tests
    python test_runner.py --schema           # Run schema tests only
    python test_runner.py --procedures       # Run procedure tests (seed + upsert + retrieval + analysis)
    python test_runner.py --api              # Run API endpoint tests
    python test_runner.py --data             # Run data validation tests
    python test_runner.py -v                 # Verbose output

All tests require a running PostgreSQL database with the NFL FantasyFootball schema.
"""

import argparse
import os
import sys
import subprocess
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PYTEST_PATH = os.path.join(SCRIPT_DIR, "pytest.ini")


def print_header(title):
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_section(title):
    print(f"\n{'=' * 40}")
    print(f"  {title}")
    print(f"{'=' * 40}")


def run_tests(test_paths, description, parallel=True):
    """Run pytest on the given test paths."""
    if not test_paths:
        return 0

    print_section(f"{description} ({len(test_paths)} file(s))")

    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "--color=yes",
        "--strict-markers",
    ]

    # Disable parallelism to prevent test interference
    if not parallel:
        cmd.extend(["-p", "no:xdist"])

    cmd.extend(test_paths)

    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run FantasyFootball test suites")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--schema", action="store_true", help="Run schema tests only")
    group.add_argument("--procedures", action="store_true", help="Run procedure tests only")
    group.add_argument("--api", action="store_true", help="Run API endpoint tests only")
    group.add_argument("--data", action="store_true", help="Run data validation tests only")
    group.add_argument("--espn", action="store_true", help="Run ESPN comparison tests only (optional)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output (passes shown)")
    parser.add_argument("--list", action="store_true", help="List available tests and exit")
    args = parser.parse_args()

    if args.list:
        print_header("Available Test Suites")
        for name, desc in [
            ("--schema", "Database schema integrity"),
            ("--procedures", "Stored procedure unit tests"),
            ("--api", "FastAPI endpoint integration tests"),
            ("--data", "Data validation & consistency"),
            ("--espn", "ESPN live data & DB comparison"),
        ]:
            print(f"  {name:<12} {desc}")
        print()
        print("Available test files:")
        for f in sorted(os.listdir(SCRIPT_DIR)):
            if f.startswith("test_") and f.endswith(".py"):
                filepath = os.path.join(SCRIPT_DIR, f)
                print(f"  {f}")
                # Print docstring class/method count
                with open(filepath, "r", encoding="utf-8") as fh:
                    content = fh.read()
                    class_count = content.count("class Test")
                    param_count = content.count("@pytest.mark.parametrize")
                    if class_count:
                        print(f"          {class_count} test class(es), {param_count} parameterized test(s)")
        return 0

    if args.verbose:
        verb = "-vv"
    else:
        verb = "-v"

    all_files = []
    for f in sorted(os.listdir(SCRIPT_DIR)):
        if f.startswith("test_") and f.endswith(".py") and f != "test_runner.py":
            all_files.append(os.path.join(SCRIPT_DIR, f))

    if args.list:
        print_header("Available Test Suites")
        for name, desc in [
            ("--schema", "Database schema integrity"),
            ("--procedures", "Stored procedure unit tests"),
            ("--api", "FastAPI endpoint integration tests"),
            ("--espn", "ESPN live data & DB comparison"),
        ]:
            print(f"  {name:<12} {desc}")
        return 0

    if args.schema:
        return run_tests(
            [os.path.join(SCRIPT_DIR, "test_schema.py")],
            "Schema Integrity Tests",
            parallel=False
        )
    if args.procedures:
        return run_tests(
            [
                os.path.join(SCRIPT_DIR, "test_seed_procedures.py"),
                os.path.join(SCRIPT_DIR, "test_upsert_procedures.py"),
                os.path.join(SCRIPT_DIR, "test_retrieval_procedures.py"),
                os.path.join(SCRIPT_DIR, "test_analysis_procedures.py"),
            ],
            "Procedure Unit Tests",
            parallel=False
        )
    if args.api:
        return run_tests(
            [os.path.join(SCRIPT_DIR, "test_api_endpoints.py")],
            "API Endpoint Tests",
            parallel=False
        )
    if args.data:
        return run_tests(
            [os.path.join(SCRIPT_DIR, "test_data_validation.py")],
            "Data Validation Tests",
            parallel=False
        )
    if args.espn:
        return run_tests(
            [os.path.join(SCRIPT_DIR, "test_espn_comparison.py")],
            "ESPN Data Comparison Tests",
            parallel=False
        )

    # Run all suites (including ESPN if not run separately)
    total_rc = 0
    suites = [
        (os.path.join(SCRIPT_DIR, "test_schema.py"), "Schema Integrity"),
        (os.path.join(SCRIPT_DIR, "test_seed_procedures.py"), "Seed Procedures"),
        (os.path.join(SCRIPT_DIR, "test_upsert_procedures.py"), "Upsert Procedures"),
        (os.path.join(SCRIPT_DIR, "test_retrieval_procedures.py"), "Retrieval Procedures"),
        (os.path.join(SCRIPT_DIR, "test_analysis_procedures.py"), "Analysis Procedures"),
        (os.path.join(SCRIPT_DIR, "test_data_validation.py"), "Data Validation"),
        (os.path.join(SCRIPT_DIR, "test_api_endpoints.py"), "API Endpoints"),
        (os.path.join(SCRIPT_DIR, "test_espn_comparison.py"), "ESPN Comparison"),
    ]

    for test_file, name in suites:
        rc = run_tests([test_file], name, parallel=False)
        total_rc = total_rc or rc

    return total_rc


if __name__ == "__main__":
    sys.exit(main())
