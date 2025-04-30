#!/usr/bin/env python3
"""
test_basic.py - Basic tests to ensure the testing framework is working
"""

import unittest
import os
from pathlib import Path

class BasicTest(unittest.TestCase):
    
    def test_reference_data_exists(self):
        """Test that reference data directories exist."""
        # Get the reference data directory
        reference_dir = Path("tests/reference_data")
        self.assertTrue(reference_dir.exists(), "Reference data directory does not exist")
        
        # Check for Monktonhall directory
        monktonhall_dir = reference_dir / "Monktonhall"
        self.assertTrue(monktonhall_dir.exists(), "Monktonhall reference directory does not exist")
        
        # Check for required files
        self.assertTrue((monktonhall_dir / "competitions.json").exists(), "competitions.json is missing")
        self.assertTrue((monktonhall_dir / "metadata.json").exists(), "metadata.json is missing")
        self.assertTrue((monktonhall_dir / "firm_capacity_results.csv").exists(), "firm_capacity_results.csv is missing")

    def test_output_directory_exists(self):
        """Test that output directories exist."""
        # Get the output directory
        output_dir = Path("output")
        self.assertTrue(output_dir.exists(), "Output directory does not exist")
        
        # Check for Monktonhall directory
        monktonhall_dir = output_dir / "Monktonhall"
        self.assertTrue(monktonhall_dir.exists(), "Monktonhall output directory does not exist")
        
        # Check for required files
        self.assertTrue((monktonhall_dir / "competitions.json").exists(), "competitions.json is missing in output")
        self.assertTrue((monktonhall_dir / "metadata.json").exists(), "metadata.json is missing in output")
        self.assertTrue((monktonhall_dir / "firm_capacity_results.csv").exists(), "firm_capacity_results.csv is missing in output")

if __name__ == '__main__':
    unittest.main()
