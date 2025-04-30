#!/usr/bin/env python3
"""
test_ci_compatibility.py - Tests to verify CI environment compatibility
"""

import unittest
import sys
import os
import platform
from pathlib import Path

class CICompatibilityTest(unittest.TestCase):
    
    def test_directory_structure(self):
        """Test that required directories exist."""
        # Check for necessary directories
        directories = [
            Path("tests/reference_data"),
            Path("tests/output"),
            Path("output")
        ]
        
        for directory in directories:
            self.assertTrue(directory.exists(), f"Required directory {directory} does not exist")
            
    def test_reference_data(self):
        """Test that reference data exists for the test substation."""
        # Monktonhall is our test substation
        reference_dir = Path("tests/reference_data/Monktonhall")
        
        self.assertTrue(reference_dir.exists(), "Reference data directory for Monktonhall does not exist")
        
        # Check for required reference files
        reference_files = [
            reference_dir / "metadata.json",
            reference_dir / "firm_capacity_results.csv"
        ]
        
        for ref_file in reference_files:
            self.assertTrue(ref_file.exists(), f"Required reference file {ref_file} does not exist")
    
    def test_cross_platform_compatibility(self):
        """Test that the code handles platform differences."""
        # We should be able to run on all platforms
        current_platform = platform.system()
        print(f"Running on platform: {current_platform}")
        
        # Verify import of required packages works
        import numpy
        import pandas
        import matplotlib
        import yaml
        
        # On Windows, we should have pywin32 if it's required
        if current_platform == "Windows":
            try:
                import win32com
                print("Successfully imported win32com on Windows")
            except ImportError:
                # This is not a critical error if win32com isn't actually used in tests
                print("Warning: win32com not available on Windows")

if __name__ == '__main__':
    unittest.main()
