#!/usr/bin/env python3
"""
Run comprehensive test suite for GemFlush system.

Usage:
    python3 run_tests.py               # All tests
    python3 run_tests.py --unit        # Unit tests only
    python3 run_tests.py --integration # Integration tests
    python3 run_tests.py --e2e         # E2E tests
    python3 run_tests.py --coverage    # With coverage report
"""

import sys
import os
import subprocess
import argparse


def run_command(cmd):
    """Run command and return exit code."""
    print(f"\n{'='*70}")
    print(f"Running: {' '.join(cmd)}")
    print('='*70)
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run GemFlush test suite')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fast', action='store_true', help='Skip slow tests')
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ['python3', '-m', 'pytest', 'chatgpt-native-stack/tests/']
    
    # Add verbosity
    if args.verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')
    
    # Add coverage
    if args.coverage:
        cmd.extend(['--cov=chatgpt-native-stack', '--cov-report=html', '--cov-report=term'])
    
    # Filter by test type
    if args.unit:
        cmd.append('chatgpt-native-stack/tests/unit/')
    elif args.integration:
        cmd.append('chatgpt-native-stack/tests/integration/')
    elif args.e2e:
        cmd.append('chatgpt-native-stack/tests/e2e/')
    
    # Skip slow tests
    if args.fast:
        cmd.extend(['-m', 'not slow'])
    
    # Add short traceback
    cmd.append('--tb=short')
    
    # Run tests
    exit_code = run_command(cmd)
    
    # Print summary
    print(f"\n{'='*70}")
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {exit_code})")
    print('='*70)
    
    # Print coverage location if generated
    if args.coverage:
        print(f"\n📊 Coverage report generated:")
        print(f"   HTML: file://{os.getcwd()}/htmlcov/index.html")
        print(f"   Open with: open htmlcov/index.html")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())


