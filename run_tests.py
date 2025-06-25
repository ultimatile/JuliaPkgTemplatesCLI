#!/usr/bin/env python3
"""
Simple test runner script for jugen tests
Usage: uvx pytest run_tests.py
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import pytest
    
    # Run pytest with the tests directory
    test_args = ["tests/", "-v"]
    if len(sys.argv) > 1:
        test_args.extend(sys.argv[1:])
    
    exit_code = pytest.main(test_args)
    sys.exit(exit_code)