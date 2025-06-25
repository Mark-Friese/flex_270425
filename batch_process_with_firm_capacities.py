#!/usr/bin/env python3
"""
Batch processing script for multiple sites with known firm capacities

This script demonstrates how to efficiently process 100+ sites with pre-calculated
firm capacities using the existing parallel processing infrastructure.
"""

import pandas as pd
import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import Dict, List, Optional
import json

# Import the firm capacity functions
from firm_capacity_with_competitions import create_service_windows_with_known_capacity
from src.utils import load_config, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_firm_capacities(firm_capacities_file: str) -> Dict[str, float]:
    """
    Load firm capacities from CSV file.
    
    Expected format:
    Site,Firm_Capacity_MW
    Site1,25.5
    Site2,30.2
    ...
    
    Args:
        firm_capacities_file: Path to CSV file with firm capacities
        
    Returns:
        Dictionary mapping site names to firm capacities
    """
    logger.info(f"Loading firm capacities from {firm_capacities_file}")
    
    df = pd.read_csv(firm_capacities_file)
    
    # Validate required columns
    required_cols = ['Site', 'Firm_Capacity_MW']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in firm capacities file: {missing_cols}")
    
    # Convert to dictionary
    firm_capacities = dict(zip(df['Site'], df['Firm_Capacity_MW']))
    
    logger.info(f"Loaded firm capacities for {len(firm_capacities)} sites")
    return firm_capacities

def process_single_site(
    cfg: dict,
    site: str,
    firm_capacity: float,
    generate_competitions: bool = True,
    **kwargs
) -> Dict:
    """
    Process a single site with known firm capacity.
    
    Args:
        cfg: Configuration dictionary
        site: Site name
        firm_capacity: Firm capacity in MW
        generate_competitions: Whether to generate competitions
        **kwargs: Additional arguments
        
    Returns:
        Processing result dictionary
    """
    start_time = time.time()
    
    try:
        # Create substation config
        sub_config = {
            "name": site,
            "demand_file": f"{site}.csv"
        }
        
        # Process with known firm capacity
        result = create_service_windows_with_known_capacity(
            cfg=cfg,
            sub=sub_config,
            firm_capacity=firm_capacity,
            generate_competitions=generate_competitions,
            **kwargs
        )
        
        return {
            'status': 'success',
            'site': site,
            'firm_capacity': firm_capacity,
            'results': result,
            'processing_time': time.time() - start_time
        }
        
    except Exception as e:
        logger.error(f"Error processing {site}: {str(e)}")
        return {
            'status': 'error',
            'site': site,
            'firm_capacity': firm_capacity,
            'error': str(e),
            'processing_time': time.time() - start_time
        }

def batch_process_sites(
    firm_capacities: Dict[str, float],
    cfg: dict,
    max_workers: int = 8,
    skip_existing: bool = True,
    generate_competitions: bool = True,
    **kwargs
) -> Dict:
    """
    Process multiple sites in parallel with known firm capacities.
    
    Args:
        firm_capacities: Dictionary mapping site names to firm capacities
        cfg: Configuration dictionary
        max_workers: Maximum number of parallel workers
        skip_existing: Skip sites that already have results
        generate_competitions: Whether to generate competitions
        **kwargs: Additional arguments to pass to processing function
        
    Returns:
        Dictionary with processing results
    """
    overall_start_time = time.time()
    
    logger.info(f"Processing {len(firm_capacities)} sites with {max_workers} workers")
    
    results = {}
    successful = 0
    failed = 0
    skipped = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_site = {}
        
        for site, firm_capacity in firm_capacities.items():
            # Check if we should skip this site
            out_base = Path(cfg["output"]["base_dir"]) / site
            
            if skip_existing and out_base.exists() and (out_base/"firm_capacity_results.csv").exists():
                logger.info(f"Skipping {site} as results already exist")
                skipped += 1
                results[site] = {
                    'status': 'skipped',
                    'site': site,
                    'firm_capacity': firm_capacity,
                    'message': 'Results already exist'
                }
                continue
            
            # Submit task to executor
            future = executor.submit(
                process_single_site,
                cfg,
                site,
                firm_capacity,
                generate_competitions,
                **kwargs
            )
            future_to_site[future] = site
        
        # Process results as they complete
        for future in as_completed(future_to_site):
            site = future_to_site[future]
            try:
                result = future.result()
                results[site] = result
                
                if result['status'] == 'success':
                    successful += 1
                    logger.info(f"✅ {site}: {result['firm_capacity']:.2f} MW - Success")
                else:
                    failed += 1
                    logger.error(f"❌ {site}: {result['firm_capacity']:.2f} MW - Failed: {result.get('error', 'Unknown error')}")
                
                # Log progress
                completed = successful + failed + skipped
                logger.info(f"Progress: {completed}/{len(firm_capacities)} sites processed")
                
            except Exception as e:
                logger.error(f"Exception processing {site}: {str(e)}")
                results[site] = {
                    'status': 'error',
                    'site': site,
                    'firm_capacity': firm_capacities[site],
                    'error': str(e)
                }
                failed += 1
    
    # Calculate overall stats
    overall_time = time.time() - overall_start_time
    
    logger.info(f"🏁 Completed processing {len(firm_capacities)} sites in {overall_time:.2f} seconds")
    logger.info(f"📊 Success: {successful}, Failed: {failed}, Skipped: {skipped}")
    
    return {
        'results': results,
        'summary': {
            'total_sites': len(firm_capacities),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'processing_time': overall_time,
            'avg_time_per_site': overall_time / len(firm_capacities) if firm_capacities else 0
        }
    }

def save_batch_summary(results: Dict, output_path: Path):
    """
    Save batch processing summary to CSV and JSON files.
    
    Args:
        results: Processing results dictionary
        output_path: Path to save the summary
    """
    # Create summary DataFrame
    rows = []
    for site, result in results['results'].items():
        row = {
            'Site': site,
            'Status': result['status'],
            'Firm_Capacity_MW': result.get('firm_capacity', 0),
            'Processing_Time_s': round(result.get('processing_time', 0), 2)
        }
        
        if result['status'] == 'success':
            # Add result metrics if they exist
            result_data = result.get('results', {})
            if isinstance(result_data, dict):
                for k, v in result_data.items():
                    if isinstance(v, (int, float, str, bool)):
                        row[k] = v
        elif result['status'] == 'error':
            row['Error'] = result.get('error', 'Unknown error')
        elif result['status'] == 'skipped':
            row['Message'] = result.get('message', 'Already processed')
        
        rows.append(row)
    
    # Save CSV summary
    summary_df = pd.DataFrame(rows)
    csv_path = output_path.with_suffix('.csv')
    summary_df.to_csv(csv_path, index=False)
    
    # Save JSON summary (with full details)
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📋 Summary saved to {csv_path} and {json_path}")
    return summary_df

def main():
    """Main function for batch processing"""
    parser = argparse.ArgumentParser(description="Batch process multiple sites with known firm capacities")
    
    # Required arguments
    parser.add_argument('--firm-capacities', type=str, required=True,
                        help='Path to CSV file with site names and firm capacities')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to configuration file')
    
    # Optional arguments
    parser.add_argument('--workers', type=int, default=8,
                        help='Number of parallel workers (default: 8)')
    parser.add_argument('--skip-existing', action='store_true',
                        help='Skip sites with existing results')
    parser.add_argument('--competitions', action='store_true',
                        help='Generate competitions')
    parser.add_argument('--schema', type=str,
                        help='Path to competition schema for validation')
    parser.add_argument('--year', type=int,
                        help='Target year for competition dates')
    parser.add_argument('--filter', type=str,
                        help='Process only specific sites (comma-separated)')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = Path(__file__).resolve().parent / args.config
        
        cfg = load_config(config_path)
        
        # Load firm capacities
        firm_capacities = load_firm_capacities(args.firm_capacities)
        
        # Filter sites if requested
        if args.filter:
            filter_sites = [s.strip() for s in args.filter.split(',')]
            firm_capacities = {site: cap for site, cap in firm_capacities.items() 
                             if site in filter_sites}
            logger.info(f"Filtered to {len(firm_capacities)} sites: {list(firm_capacities.keys())}")
        
        # Ensure output directory exists
        output_dir = Path(cfg["output"]["base_dir"])
        ensure_dir(output_dir)
        
        # Process sites in parallel
        results = batch_process_sites(
            firm_capacities=firm_capacities,
            cfg=cfg,
            max_workers=args.workers,
            skip_existing=args.skip_existing,
            generate_competitions=args.competitions,
            schema_path=args.schema,
            target_year=args.year
        )
        
        # Save summary
        summary_path = output_dir / "batch_processing_summary"
        summary_df = save_batch_summary(results, summary_path)
        
        # Print final results
        summary = results['summary']
        print(f"\n🎯 Batch Processing Complete!")
        print(f"📁 Results saved to: {output_dir}/")
        print(f"⏱️  Total time: {summary['processing_time']:.1f} seconds")
        print(f"⚡ Average per site: {summary['avg_time_per_site']:.2f} seconds")
        print(f"✅ Successful: {summary['successful']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⏭️  Skipped: {summary['skipped']}")
        
        # Show some statistics if available
        if summary['successful'] > 0:
            success_results = [r for r in results['results'].values() if r['status'] == 'success']
            if success_results:
                firm_caps = [r['firm_capacity'] for r in success_results]
                print(f"📊 Firm capacity range: {min(firm_caps):.1f} - {max(firm_caps):.1f} MW")
                print(f"📊 Average firm capacity: {sum(firm_caps)/len(firm_caps):.1f} MW")
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 