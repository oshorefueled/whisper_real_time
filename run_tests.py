#!/usr/bin/env python3
"""
Test runner for the Whisper Real-Time project
"""

import unittest
import sys
import os

def run_tests():
    """Run all tests in the tests directory"""
    # Get the tests directory
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(tests_dir)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
