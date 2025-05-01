#!/usr/bin/env python3
"""
test_ci_compatibility.py - Tests for CI/CD environment compatibility
"""

import unittest
import json
import pandas as pd
from pathlib import Path
import os

class CICompatibilityTest(unittest.TestCase):
    
    def setUp(self):
        # Paths to reference data
        self.reference_dir = Path("tests/reference_data")
        self.substations = ["Monktonhall"]
    
    def test_reference_data(self):
        """Test that reference data exists and contains expected parameters."""
        for sub in self.substations:
            ref_meta_path = self.reference_dir / sub / "metadata.json"
            ref_comp_path = self.reference_dir / sub / "competitions.json"
            
            # Check that files exist
            self.assertTrue(ref_meta_path.exists(), f"Reference metadata not found for {sub}")
            self.assertTrue(ref_comp_path.exists(), f"Reference competitions not found for {sub}")
            
            # Load metadata
            with open(ref_meta_path) as f:
                metadata = json.load(f)
            
            # Verify target_mwh is set to the expected value (150 MWh)
            self.assertEqual(metadata["target_mwh"], 150, "Reference data target_mwh doesn't match expected value")
            
            # Load competitions
            with open(ref_comp_path) as f:
                competitions = json.load(f)
            
            # Verify competitions structure
            self.assertIsInstance(competitions, list, "Competitions should be a list")
            
    def test_directory_structure(self):
        """Test that required directories exist."""
        # Check reference data directory
        self.assertTrue(self.reference_dir.exists(), "Reference data directory not found")
        
        # Check output directory
        output_dir = Path("output")
        self.assertTrue(output_dir.exists(), "Output directory not found")
        
    def test_cross_platform_compatibility(self):
        """Test for potential cross-platform compatibility issues."""
        # Check for presence of files that might have platform-specific issues
        test_files = [
            Path("pytest.ini"),
            Path("tests/__init__.py")
        ]
        
        for file_path in test_files:
            if file_path.exists():
                # Check for Windows-specific line endings in text files
                with open(file_path, 'rb') as f:
                    content = f.read()
                    # Count Windows line endings
                    crlf_count = content.count(b'\r\n')
                    # Count Unix line endings
                    lf_count = content.count(b'\n') - crlf_count
                    
                    # If file has mixed line endings, it could cause issues
                    if crlf_count > 0 and lf_count > 0:
                        self.fail(f"File {file_path} has mixed line endings, which may cause issues in CI")

if __name__ == '__main__':
    unittest.main()
