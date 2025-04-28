"""
parquet_processor.py - Process parquet files for substation demand analysis

This module provides utilities for loading parquet files containing demand data,
filtering by network group, and running the firm capacity analysis on each group.
"""

import os
import logging
import pandas as pd
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Dask (optional but recommended for large files)
try:
    import dask.dataframe as dd
    HAS_DASK = True
except ImportError:
    HAS_DASK = False
    logger.warning("Dask not available. Install with 'pip install dask[complete]' for better performance with large files.")

# Column mapping dictionary - modify this to match your data structure
COLUMN_MAPPINGS = {
    'group_name': 'Network Group Name',
    'timestamp': 'Timestamp',
    'network_group': 'Network Group Name',
    'demand_mw': 'Demand (MW)',
    'underlying_demand_mw': 'Demand (MW)',
    # Add other mappings as needed
}

def apply_column_mappings(df):
    """Apply standard column name mappings to dataframe."""
    rename_dict = {}
    for src, dest in COLUMN_MAPPINGS.items():
        if src in df.columns and dest not in df.columns:
            rename_dict[src] = dest
    if rename_dict:
        return df.rename(columns=rename_dict)
    return df

def get_unique_network_groups(parquet_path: str) -> List[str]:
    """
    Extract all unique network group names from a parquet file.
    
    Args:
        parquet_path: Path to the parquet file
        
    Returns:
        List of unique network group names
    """
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    logger.info(f"Getting unique network groups from {parquet_path}")
    start_time = time.time()
    
    try:
        if HAS_DASK:
            # Use Dask for more efficient processing with large files
            ddf = dd.read_parquet(parquet_path)
            
            # Check if we need to apply column mappings
            sample_cols = ddf.columns
            need_mapping = 'Network Group Name' not in sample_cols
            
            if need_mapping:
                # Find the right column to use
                group_col = None
                for src, dest in COLUMN_MAPPINGS.items():
                    if src in sample_cols and dest == 'Network Group Name':
                        group_col = src
                        break
                
                if not group_col:
                    raise ValueError("Could not find a column that maps to 'Network Group Name'")
                
                unique_groups = ddf[group_col].unique().compute().tolist()
            else:
                unique_groups = ddf['Network Group Name'].unique().compute().tolist()
        else:
            # Use pandas for smaller files
            df = pd.read_parquet(parquet_path)
            df = apply_column_mappings(df)
            unique_groups = df['Network Group Name'].unique().tolist()
        
        # Sort for consistent ordering
        unique_groups = sorted(unique_groups)
        
        logger.info(f"Found {len(unique_groups)} unique network groups in {time.time() - start_time:.2f} seconds")
        return unique_groups
    
    except Exception as e:
        logger.error(f"Error getting unique network groups: {str(e)}")
        raise

def load_network_group_data(
    parquet_path: str,
    network_group: str,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load data for a specific network group from parquet file.
    
    Args:
        parquet_path: Path to the parquet file
        network_group: Network group name to filter
        columns: Optional list of columns to load (for performance)
        
    Returns:
        DataFrame with data for the specified network group
    """
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    logger.info(f"Loading data for network group: {network_group}")
    start_time = time.time()
    
    try:
        if HAS_DASK:
            # Use Dask for more efficient processing with large files
            ddf = dd.read_parquet(parquet_path, columns=columns)
            
            # Apply column mappings if needed
            sample_cols = ddf.columns
            need_mapping = 'Network Group Name' not in sample_cols
            
            if need_mapping:
                # Apply mappings to column names
                rename_dict = {}
                for src, dest in COLUMN_MAPPINGS.items():
                    if src in sample_cols and dest not in sample_cols:
                        rename_dict[src] = dest
                if rename_dict:
                    ddf = ddf.rename(columns=rename_dict)
            
            # Filter for this network group
            group_ddf = ddf[ddf['Network Group Name'] == network_group]
            
            # Convert to pandas for analysis
            df = group_ddf.compute()
        else:
            # Use pandas for smaller files
            if columns:
                df = pd.read_parquet(parquet_path, columns=columns)
            else:
                df = pd.read_parquet(parquet_path)
            
            # Apply column mappings
            df = apply_column_mappings(df)
            
            # Filter for this network group
            df = df[df['Network Group Name'] == network_group].copy()
        
        # Check if we got any data
        if df.empty:
            logger.warning(f"No data found for network group {network_group}")
            return df
        
        # Process timestamps if present
        if 'Timestamp' in df.columns:
            # Coerce errors and convert to UTC
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce', utc=True)
            invalid_timestamps = df['Timestamp'].isna().sum()
            if invalid_timestamps > 0:
                logger.warning(f"Found {invalid_timestamps} invalid timestamps in {network_group}")
        
        logger.info(f"Loaded {len(df)} rows for {network_group} in {time.time() - start_time:.2f} seconds")
        return df
    
    except Exception as e:
        logger.error(f"Error loading data for {network_group}: {str(e)}")
        raise

def save_filtered_demand_data(df: pd.DataFrame, output_path: Path):
    """
    Save filtered demand data to CSV file.
    
    Args:
        df: DataFrame with filtered demand data
        output_path: Path to save the data
    """
    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered demand data to {output_path}")

def process_network_groups_in_parquet(
    parquet_path: str,
    cfg: dict,
    process_function: Callable,
    network_groups: Optional[List[str]] = None,
    max_workers: int = 1,
    skip_existing: bool = True,
    **kwargs
) -> Dict:
    """
    Process all network groups (or specified ones) in parallel.
    
    Args:
        parquet_path: Path to the parquet file
        cfg: Configuration dictionary
        process_function: Function to call with each group
        network_groups: Optional list of specific groups to process
            If None, all groups in the file will be processed
        max_workers: Maximum number of parallel workers
        skip_existing: Skip groups that already have results
        **kwargs: Additional arguments to pass to the process function
        
    Returns:
        Dict with processing results for all groups
    """
    overall_start_time = time.time()
    
    # Get list of network groups if not provided
    if network_groups is None:
        network_groups = get_unique_network_groups(parquet_path)
    
    logger.info(f"Processing {len(network_groups)} network groups with {max_workers} workers")
    
    # Process in parallel using ThreadPoolExecutor
    results = {}
    successful = 0
    failed = 0
    skipped = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_group = {}
        
        for network_group in network_groups:
            # Create a modified substation config with this network group
            sub = {"name": network_group, "demand_source": "parquet"}
            
            # Define output base path for this network group
            out_base = Path(cfg["output"]["base_dir"]) / network_group
            
            # Check if we should skip this group
            if skip_existing and out_base.exists() and (out_base/"firm_capacity_results.csv").exists():
                logger.info(f"Skipping {network_group} as results already exist")
                skipped += 1
                results[network_group] = {
                    'status': 'skipped',
                    'network_group': network_group,
                    'message': 'Results already exist'
                }
                continue
            
            # Submit task to executor
            future = executor.submit(
                process_single_network_group,
                parquet_path, 
                network_group, 
                cfg, 
                sub, 
                process_function,
                **kwargs
            )
            future_to_group[future] = network_group
        
        # Process results as they complete
        for future in as_completed(future_to_group):
            group = future_to_group[future]
            try:
                result = future.result()
                results[group] = result
                
                if result['status'] == 'success':
                    successful += 1
                else:
                    failed += 1
                
                # Log progress
                completed = successful + failed + skipped
                logger.info(f"Processed {completed}/{len(network_groups)}: {group} - {result['status']}")
                
            except Exception as e:
                logger.error(f"Exception processing {group}: {str(e)}")
                results[group] = {
                    'status': 'error',
                    'network_group': group,
                    'error': str(e)
                }
                failed += 1
    
    # Calculate overall stats
    overall_time = time.time() - overall_start_time
    
    logger.info(f"Completed processing {len(network_groups)} network groups in {overall_time:.2f} seconds")
    logger.info(f"Success: {successful}, Failed: {failed}, Skipped: {skipped}")
    
    return {
        'results': results,
        'summary': {
            'total_groups': len(network_groups),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'processing_time': overall_time
        }
    }

def process_single_network_group(
    parquet_path: str,
    network_group: str,
    cfg: dict,
    sub: dict,
    process_function: Callable,
    **kwargs
) -> Dict:
    """
    Process a single network group from a parquet file.
    
    Args:
        parquet_path: Path to the parquet file
        network_group: Network group name to process
        cfg: Configuration dictionary
        sub: Substation configuration dictionary
        process_function: Function to call for processing
        **kwargs: Additional arguments to pass to the process function
        
    Returns:
        Dict with processing results
    """
    start_time = time.time()
    
    try:
        # Load data for this network group
        df = load_network_group_data(parquet_path, network_group)
        
        # Skip empty dataframes
        if df.empty:
            return {
                'status': 'error',
                'network_group': network_group,
                'error': f"No data found for network group {network_group}",
                'processing_time': time.time() - start_time
            }
        
        # Save filtered data to output folder
        out_base = Path(cfg["output"]["base_dir"]) / network_group
        out_base.mkdir(parents=True, exist_ok=True)
        save_filtered_demand_data(df, out_base / "demand.csv")
        
        # Process this network group
        result = process_function(
            cfg, 
            sub, 
            parquet_path=parquet_path,
            parquet_df=df,
            **kwargs
        )
        
        return {
            'status': 'success',
            'network_group': network_group,
            'results': result,
            'row_count': len(df),
            'processing_time': time.time() - start_time
        }
        
    except Exception as e:
        # Log the full traceback using exc_info=True
        logger.error(f"Error processing {network_group}", exc_info=True)
        return {
            'status': 'error',
            'network_group': network_group,
            'error': str(e),
            'processing_time': time.time() - start_time
        }

def save_summary_results(results: Dict, output_path: Path):
    """
    Save processing results summary to a file.
    
    Args:
        results: Dictionary of processing results
        output_path: Path to save the results
    """
    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create summary DataFrame
    rows = []
    for group, result in results['results'].items():
        if result['status'] == 'success':
            row = {
                'Network Group': group,
                'Status': 'success',
                'Row Count': result.get('row_count', 0),
                'Processing Time (s)': round(result.get('processing_time', 0), 2)
            }
            
            # Add any result metrics if they exist
            result_data = result.get('results', {})
            if isinstance(result_data, dict):
                for k, v in result_data.items():
                    if isinstance(v, (int, float, str, bool)):
                        row[k] = v
            
            rows.append(row)
        elif result['status'] == 'skipped':
            rows.append({
                'Network Group': group,
                'Status': 'skipped',
                'Message': result.get('message', 'Already processed')
            })
        else:
            rows.append({
                'Network Group': group,
                'Status': 'error',
                'Error': result.get('error', 'Unknown error'),
                'Processing Time (s)': round(result.get('processing_time', 0), 2) if 'processing_time' in result else 0
            })
    
    # Create DataFrame and save
    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(output_path, index=False)
    
    logger.info(f"Results summary saved to {output_path}")
    return summary_df