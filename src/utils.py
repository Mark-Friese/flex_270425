# src/utils.py
import yaml
from pathlib import Path
from typing import Any, Dict
import pandas as pd

def load_config(path: Path) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def load_site_specific_targets(targets_file: Path) -> Dict[str, float]:
    """
    Load site-specific MWh targets from a CSV file.
    
    The CSV should have at least two columns: 'site_name' and 'target_mwh'
    
    Args:
        targets_file: Path to CSV file with site-specific targets
        
    Returns:
        Dictionary mapping site names to their MWh targets
    """
    try:
        df = pd.read_csv(targets_file)
        required_columns = ['site_name', 'target_mwh']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Target file must contain columns: {required_columns}")
        
        # Convert to dictionary
        targets_dict = dict(zip(df['site_name'], df['target_mwh']))
        return targets_dict
    except Exception as e:
        raise ValueError(f"Error loading targets file: {e}") 