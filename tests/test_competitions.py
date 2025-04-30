#!/usr/bin/env python3
"""
test_competitions.py - Tests for competition generation
"""

import unittest
import json
from pathlib import Path
from datetime import datetime

class CompetitionsTest(unittest.TestCase):
    
    def setUp(self):
        # Paths to reference and output directories
        self.reference_dir = Path("tests/reference_data")
        self.output_dir = Path("output")
        
        # Substations to test - can be made configurable
        self.substations = ["Monktonhall"]  # Update with the substations you're testing
    
    def test_competition_structure(self):
        """Test that competition structure is consistent with reference data."""
        for sub in self.substations:
            # Load reference and new competition files
            ref_comp_path = self.reference_dir / sub / "competitions.json"
            new_comp_path = self.output_dir / sub / "competitions.json"
            
            self.assertTrue(ref_comp_path.exists(), f"Reference competitions not found for {sub}")
            self.assertTrue(new_comp_path.exists(), f"New competitions not found for {sub}")
            
            with open(ref_comp_path) as f:
                ref_comps = json.load(f)
            
            with open(new_comp_path) as f:
                new_comps = json.load(f)
            
            # Check number of competitions
            self.assertEqual(
                len(ref_comps), 
                len(new_comps),
                f"Number of competitions changed for {sub}"
            )
            
            # Check competition details
            for i, (ref_comp, new_comp) in enumerate(zip(ref_comps, new_comps)):
                # Check competition name
                self.assertEqual(
                    ref_comp["name"], 
                    new_comp["name"],
                    f"Competition name changed for competition {i} in {sub}"
                )
                
                # Check reference
                self.assertEqual(
                    ref_comp["reference"], 
                    new_comp["reference"],
                    f"Competition reference changed for competition {i} in {sub}"
                )
                
                # Check boundary data
                self.assertEqual(
                    ref_comp["boundary"]["area_references"], 
                    new_comp["boundary"]["area_references"],
                    f"Boundary area references changed for competition {i} in {sub}"
                )
                
                # Check need_type, type, need_direction, power_type
                for field in ["need_type", "type", "need_direction", "power_type"]:
                    self.assertEqual(
                        ref_comp[field], 
                        new_comp[field],
                        f"Field {field} changed for competition {i} in {sub}"
                    )
    
    def test_service_periods(self):
        """Test that service periods are consistent with reference data."""
        for sub in self.substations:
            # Load reference and new competition files
            ref_comp_path = self.reference_dir / sub / "competitions.json"
            new_comp_path = self.output_dir / sub / "competitions.json"
            
            with open(ref_comp_path) as f:
                ref_comps = json.load(f)
            
            with open(new_comp_path) as f:
                new_comps = json.load(f)
            
            # Check service periods
            for i, (ref_comp, new_comp) in enumerate(zip(ref_comps, new_comps)):
                # Check number of service periods
                self.assertEqual(
                    len(ref_comp["service_periods"]), 
                    len(new_comp["service_periods"]),
                    f"Number of service periods changed for competition {i} in {sub}"
                )
                
                # Check service period details
                for j, (ref_period, new_period) in enumerate(zip(ref_comp["service_periods"], new_comp["service_periods"])):
                    # Check period name
                    self.assertEqual(
                        ref_period["name"], 
                        new_period["name"],
                        f"Service period name changed for period {j} in competition {i} for {sub}"
                    )
                    
                    # Check period start and end dates
                    self.assertEqual(
                        ref_period["start"], 
                        new_period["start"],
                        f"Service period start date changed for period {j} in competition {i} for {sub}"
                    )
                    
                    self.assertEqual(
                        ref_period["end"], 
                        new_period["end"],
                        f"Service period end date changed for period {j} in competition {i} for {sub}"
                    )
    
    def test_service_windows(self):
        """Test that service windows are consistent with reference data."""
        for sub in self.substations:
            # Load reference and new competition files
            ref_comp_path = self.reference_dir / sub / "competitions.json"
            new_comp_path = self.output_dir / sub / "competitions.json"
            
            with open(ref_comp_path) as f:
                ref_comps = json.load(f)
            
            with open(new_comp_path) as f:
                new_comps = json.load(f)
            
            # Compare all service windows in each service period
            for i, (ref_comp, new_comp) in enumerate(zip(ref_comps, new_comps)):
                for j, (ref_period, new_period) in enumerate(zip(ref_comp["service_periods"], new_comp["service_periods"])):
                    # Check number of service windows
                    self.assertEqual(
                        len(ref_period["service_windows"]), 
                        len(new_period["service_windows"]),
                        f"Number of service windows changed in period {j} of competition {i} for {sub}"
                    )
                    
                    # Check service window details
                    for k, (ref_window, new_window) in enumerate(zip(ref_period["service_windows"], new_period["service_windows"])):
                        # Check window name
                        self.assertEqual(
                            ref_window["name"], 
                            new_window["name"],
                            f"Window name changed in window {k} of period {j} in competition {i} for {sub}"
                        )
                        
                        # Check window start and end times
                        self.assertEqual(
                            ref_window["start"], 
                            new_window["start"],
                            f"Window start time changed in window {k} of period {j} in competition {i} for {sub}"
                        )
                        
                        self.assertEqual(
                            ref_window["end"], 
                            new_window["end"],
                            f"Window end time changed in window {k} of period {j} in competition {i} for {sub}"
                        )
                        
                        # Check capacity requirements
                        self.assertEqual(
                            float(ref_window["capacity_required"]), 
                            float(new_window["capacity_required"]),
                            f"Capacity requirement changed in window {k} of period {j} in competition {i} for {sub}"
                        )
                        
                        # Check service days
                        self.assertEqual(
                            ref_window["service_days"], 
                            new_window["service_days"],
                            f"Service days changed in window {k} of period {j} in competition {i} for {sub}"
                        )
    
    def test_total_competition_mwh(self):
        """
        Calculate and compare total MWh across all service windows in competitions.
        This test requires adding energy_mwh fields during processing.
        """
        # This test would require additional energy_mwh fields to be preserved in the competitions
        # For now, we'll just note this as a TODO
        self.skipTest("This test requires energy_mwh fields to be preserved in competitions")

if __name__ == '__main__':
    unittest.main()