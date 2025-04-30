#!/usr/bin/env python3
"""
data_review.py - Generate data review reports comparing reference and new outputs

This script generates detailed comparison reports between reference data and new outputs,
highlighting any significant changes in key metrics.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import logging
import matplotlib.pyplot as plt
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def summarize_competitions(competitions):
    """Generate summary metrics for a set of competitions."""
    # Count competitions, service periods, and windows
    num_competitions = len(competitions)
    num_periods = sum(len(comp["service_periods"]) for comp in competitions)
    num_windows = sum(
        sum(len(period["service_windows"]) for period in comp["service_periods"])
        for comp in competitions
    )
    
    # Calculate total capacity requirements
    total_capacity = 0
    for comp in competitions:
        for period in comp["service_periods"]:
            for window in period["service_windows"]:
                total_capacity += float(window["capacity_required"])
    
    # Calculate total MWh (if energy_mwh is present in windows)
    total_mwh = 0
    windows_with_mwh = 0
    for comp in competitions:
        for period in comp["service_periods"]:
            for window in period["service_windows"]:
                if "energy_mwh" in window:
                    total_mwh += window["energy_mwh"]
                    windows_with_mwh += 1
    
    # Return summary metrics
    return {
        "num_competitions": num_competitions,
        "num_periods": num_periods,
        "num_windows": num_windows,
        "total_capacity_mw": total_capacity,
        "avg_capacity_per_window": total_capacity / max(1, num_windows),
        "total_mwh": total_mwh if windows_with_mwh > 0 else None,
        "windows_with_mwh": windows_with_mwh
    }

def compare_competition_outputs(reference_dir, new_output_dir, substation, report_dir):
    """
    Generate a report comparing reference and new outputs.
    
    Args:
        reference_dir: Path to reference data directory
        new_output_dir: Path to new output directory
        substation: Substation name
        report_dir: Directory to save the report
    
    Returns:
        Report data dictionary
    """
    logger.info(f"Comparing outputs for {substation}")
    
    # Create report directory if it doesn't exist
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    
    # Load reference and new metadata
    ref_meta_path = Path(reference_dir) / substation / "metadata.json"
    new_meta_path = Path(new_output_dir) / substation / "metadata.json"
    
    if not ref_meta_path.exists():
        logger.error(f"Reference metadata not found for {substation}")
        return None
    
    if not new_meta_path.exists():
        logger.error(f"New metadata not found for {substation}")
        return None
    
    with open(ref_meta_path) as f:
        ref_meta = json.load(f)
    
    with open(new_meta_path) as f:
        new_meta = json.load(f)
    
    # Load reference and new competitions
    ref_comp_path = Path(reference_dir) / substation / "competitions.json"
    new_comp_path = Path(new_output_dir) / substation / "competitions.json"
    
    if not ref_comp_path.exists():
        logger.error(f"Reference competitions not found for {substation}")
        return None
    
    if not new_comp_path.exists():
        logger.error(f"New competitions not found for {substation}")
        return None
    
    with open(ref_comp_path) as f:
        ref_comps = json.load(f)
    
    with open(new_comp_path) as f:
        new_comps = json.load(f)
    
    # Calculate summary metrics
    ref_summary = summarize_competitions(ref_comps)
    new_summary = summarize_competitions(new_comps)
    
    # Calculate firm capacity metrics
    firm_capacity_metrics = {
        "C_plain_MW": {
            "reference": ref_meta["C_plain_MW"],
            "new": new_meta["C_plain_MW"],
            "change": new_meta["C_plain_MW"] - ref_meta["C_plain_MW"],
            "pct_change": (new_meta["C_plain_MW"] - ref_meta["C_plain_MW"]) / ref_meta["C_plain_MW"] * 100 if ref_meta["C_plain_MW"] != 0 else None
        },
        "C_peak_MW": {
            "reference": ref_meta["C_peak_MW"],
            "new": new_meta["C_peak_MW"],
            "change": new_meta["C_peak_MW"] - ref_meta["C_peak_MW"],
            "pct_change": (new_meta["C_peak_MW"] - ref_meta["C_peak_MW"]) / ref_meta["C_peak_MW"] * 100 if ref_meta["C_peak_MW"] != 0 else None
        },
        "mean_demand_MW": {
            "reference": ref_meta["mean_demand_MW"],
            "new": new_meta["mean_demand_MW"],
            "change": new_meta["mean_demand_MW"] - ref_meta["mean_demand_MW"],
            "pct_change": (new_meta["mean_demand_MW"] - ref_meta["mean_demand_MW"]) / ref_meta["mean_demand_MW"] * 100 if ref_meta["mean_demand_MW"] != 0 else None
        },
        "max_demand_MW": {
            "reference": ref_meta["max_demand_MW"],
            "new": new_meta["max_demand_MW"],
            "change": new_meta["max_demand_MW"] - ref_meta["max_demand_MW"],
            "pct_change": (new_meta["max_demand_MW"] - ref_meta["max_demand_MW"]) / ref_meta["max_demand_MW"] * 100 if ref_meta["max_demand_MW"] != 0 else None
        },
        "total_energy_MWh": {
            "reference": ref_meta["total_energy_MWh"],
            "new": new_meta["total_energy_MWh"],
            "change": new_meta["total_energy_MWh"] - ref_meta["total_energy_MWh"],
            "pct_change": (new_meta["total_energy_MWh"] - ref_meta["total_energy_MWh"]) / ref_meta["total_energy_MWh"] * 100 if ref_meta["total_energy_MWh"] != 0 else None
        }
    }
    
    # Calculate competition metrics
    competition_metrics = {}
    for key in ref_summary.keys():
        if ref_summary[key] is None or new_summary[key] is None:
            competition_metrics[key] = {
                "reference": ref_summary[key],
                "new": new_summary[key],
                "change": None,
                "pct_change": None
            }
        else:
            competition_metrics[key] = {
                "reference": ref_summary[key],
                "new": new_summary[key],
                "change": new_summary[key] - ref_summary[key],
                "pct_change": (new_summary[key] - ref_summary[key]) / ref_summary[key] * 100 if ref_summary[key] != 0 else None
            }
    
    # Generate report
    report = {
        "substation": substation,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "firm_capacity_metrics": firm_capacity_metrics,
        "competition_metrics": competition_metrics
    }
    
    # Save report to JSON
    with open(Path(report_dir) / f"{substation}_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Generate HTML report with tables and plots
    generate_html_report(report, Path(report_dir) / f"{substation}_report.html")
    
    # Also create a CSV summary
    metrics_rows = []
    
    # Add firm capacity metrics
    for metric, data in firm_capacity_metrics.items():
        row = {
            "Substation": substation,
            "Category": "Firm Capacity",
            "Metric": metric,
            "Reference": data["reference"],
            "New": data["new"],
            "Absolute Change": data["change"],
            "Percent Change": data["pct_change"]
        }
        metrics_rows.append(row)
    
    # Add competition metrics
    for metric, data in competition_metrics.items():
        row = {
            "Substation": substation,
            "Category": "Competition",
            "Metric": metric,
            "Reference": data["reference"],
            "New": data["new"],
            "Absolute Change": data["change"],
            "Percent Change": data["pct_change"]
        }
        metrics_rows.append(row)
    
    # Create DataFrame and save to CSV
    pd.DataFrame(metrics_rows).to_csv(Path(report_dir) / f"{substation}_metrics.csv", index=False)
    
    return report

def generate_html_report(report, output_path):
    """Generate HTML report from report data."""
    substation = report["substation"]
    timestamp = report["timestamp"]
    
    # Start building HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Review Report - {substation}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .highlight {{ background-color: #ffffcc; }}
            .significant-change {{ background-color: #ffcccc; }}
        </style>
    </head>
    <body>
        <h1>Data Review Report</h1>
        <p><strong>Substation:</strong> {substation}</p>
        <p><strong>Generated:</strong> {timestamp}</p>
        
        <h2>Firm Capacity Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Reference</th>
                <th>New</th>
                <th>Change</th>
                <th>% Change</th>
            </tr>
    """
    
    # Add firm capacity metrics
    for metric, data in report["firm_capacity_metrics"].items():
        css_class = ""
        if data["pct_change"] is not None and abs(data["pct_change"]) > 1.0:
            css_class = "significant-change"
        elif data["pct_change"] is not None and abs(data["pct_change"]) > 0.1:
            css_class = "highlight"
        
        pct_change = f"{data['pct_change']:.2f}%" if data["pct_change"] is not None else "N/A"
        change = f"{data['change']:.4f}" if data["change"] is not None else "N/A"
        
        html_content += f"""
            <tr class="{css_class}">
                <td>{metric}</td>
                <td>{data['reference']:.4f}</td>
                <td>{data['new']:.4f}</td>
                <td>{change}</td>
                <td>{pct_change}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Competition Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Reference</th>
                <th>New</th>
                <th>Change</th>
                <th>% Change</th>
            </tr>
    """
    
    # Add competition metrics
    for metric, data in report["competition_metrics"].items():
        css_class = ""
        if data["pct_change"] is not None and abs(data["pct_change"]) > 5.0:
            css_class = "significant-change"
        elif data["pct_change"] is not None and abs(data["pct_change"]) > 1.0:
            css_class = "highlight"
        
        # Format values appropriately
        if data["reference"] is None:
            ref_val = "N/A"
        elif isinstance(data["reference"], float):
            ref_val = f"{data['reference']:.4f}"
        else:
            ref_val = str(data["reference"])
            
        if data["new"] is None:
            new_val = "N/A"
        elif isinstance(data["new"], float):
            new_val = f"{data['new']:.4f}"
        else:
            new_val = str(data["new"])
            
        if data["change"] is None:
            change = "N/A"
        elif isinstance(data["change"], float):
            change = f"{data['change']:.4f}"
        else:
            change = str(data["change"])
            
        pct_change = f"{data['pct_change']:.2f}%" if data["pct_change"] is not None else "N/A"
        
        html_content += f"""
            <tr class="{css_class}">
                <td>{metric}</td>
                <td>{ref_val}</td>
                <td>{new_val}</td>
                <td>{change}</td>
                <td>{pct_change}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>Summary</h2>
        <p>
            This report shows the differences between reference data and new outputs.
            Highlighted rows indicate metrics that have changed significantly:
        </p>
        <ul>
            <li><span class="highlight">Yellow</span> - Minor changes (0.1% - 1% for firm capacity, 1% - 5% for competitions)</li>
            <li><span class="significant-change">Red</span> - Significant changes (>1% for firm capacity, >5% for competitions)</li>
        </ul>
    </body>
    </html>
    """
    
    # Write HTML to file
    with open(output_path, "w") as f:
        f.write(html_content)
    
    logger.info(f"HTML report generated: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate data review reports")
    parser.add_argument("--reference-dir", type=str, default="tests/reference_data", 
                        help="Path to reference data directory")
    parser.add_argument("--output-dir", type=str, default="output", 
                        help="Path to output directory")
    parser.add_argument("--report-dir", type=str, default="reports", 
                        help="Path to save reports")
    parser.add_argument("--substations", type=str, nargs="+", default=["Monktonhall"], 
                        help="List of substations to process")
    
    args = parser.parse_args()
    
    # Process each substation
    reports = []
    for sub in args.substations:
        logger.info(f"Processing substation: {sub}")
        report = compare_competition_outputs(
            args.reference_dir, 
            args.output_dir, 
            sub,
            args.report_dir
        )
        if report:
            reports.append(report)
    
    logger.info(f"Generated {len(reports)} reports in {args.report_dir}")

if __name__ == "__main__":
    main()