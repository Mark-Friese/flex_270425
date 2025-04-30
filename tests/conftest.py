#!/usr/bin/env python3
"""
conftest.py - Fixtures for pytest
"""

import pytest
import json
import pandas as pd
from pathlib import Path
import os

@pytest.fixture(scope="session")
def reference_dir():
    """Path to reference data directory."""
    return Path("tests/reference_data")

@pytest.fixture(scope="session")
def output_dir():
    """Path to output data directory."""
    return Path("output")

@pytest.fixture(scope="session")
def substations():
    """List of substations to test."""
    # This could be configured from an environment variable or config file
    # For now, we'll hard-code the list
    return ["Monktonhall"]  # Update with your substation names

@pytest.fixture(scope="session")
def reference_competitions(reference_dir, substations):
    """Load reference competition data for all substations."""
    competitions = {}
    for sub in substations:
        comp_path = reference_dir / sub / "competitions.json"
        if comp_path.exists():
            with open(comp_path) as f:
                competitions[sub] = json.load(f)
        else:
            competitions[sub] = None
    return competitions

@pytest.fixture(scope="session")
def new_competitions(output_dir, substations):
    """Load new competition data for all substations."""
    competitions = {}
    for sub in substations:
        comp_path = output_dir / sub / "competitions.json"
        if comp_path.exists():
            with open(comp_path) as f:
                competitions[sub] = json.load(f)
        else:
            competitions[sub] = None
    return competitions

@pytest.fixture(scope="session")
def reference_metadata(reference_dir, substations):
    """Load reference metadata for all substations."""
    metadata = {}
    for sub in substations:
        meta_path = reference_dir / sub / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                metadata[sub] = json.load(f)
        else:
            metadata[sub] = None
    return metadata

@pytest.fixture(scope="session")
def new_metadata(output_dir, substations):
    """Load new metadata for all substations."""
    metadata = {}
    for sub in substations:
        meta_path = output_dir / sub / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                metadata[sub] = json.load(f)
        else:
            metadata[sub] = None
    return metadata

@pytest.fixture(scope="session")
def test_output_dir():
    """Directory for test outputs and artifacts."""
    path = Path("tests/output")
    path.mkdir(parents=True, exist_ok=True)
    return path

@pytest.fixture(scope="session")
def extract_service_windows():
    """Function to extract service windows from competitions."""
    def _extract(competitions):
        windows = []
        for comp_idx, comp in enumerate(competitions):
            for period_idx, period in enumerate(comp["service_periods"]):
                for window_idx, window in enumerate(period["service_windows"]):
                    window_data = {
                        "competition_idx": comp_idx,
                        "competition_name": comp["name"],
                        "period_idx": period_idx,
                        "period_name": period["name"],
                        "window_idx": window_idx,
                        "window_name": window["name"],
                        "start": window["start"],
                        "end": window["end"],
                        "capacity_required": float(window["capacity_required"]),
                        "service_days": ','.join(window["service_days"])
                    }
                    windows.append(window_data)
        return pd.DataFrame(windows)
    
    return _extract