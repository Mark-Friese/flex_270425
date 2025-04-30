"""
app.py - Desktop application for flexibility analysis system using PyWebView

This script creates a desktop application for the flexibility analysis system
using PyWebView to wrap a web-based UI around the existing Python functionality.
"""

import webview
import os
import json
import logging
import sys
import pandas as pd
import numpy as np
import traceback
from pathlib import Path
from datetime import datetime

# Import original firm capacity modules
from src.utils import load_config, ensure_dir, load_site_specific_targets
from src.calculations import (
    energy_above_capacity,
    energy_peak_based,
    invert_capacity,
)
from src.plotting import plot_E_curve

# Import competition modules
from competition_builder import (
    create_competitions_from_df,
    save_competitions_to_json,
    validate_competitions_with_schema
)
from competition_dates import update_dates_in_dataframe
from competition_config import ConfigMode
from firm_capacity_with_competitions import process_substation_with_competitions


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("flexibility_app.log")
    ]
)

logger = logging.getLogger('flexibility_app')

class FlexibilityAnalysisAPI:
    """API class to handle interaction between web UI and Python backend"""
    
    def __init__(self):
        self.config = None
        self.base_dir = Path(__file__).resolve().parent
        self.default_config_path = self.base_dir / "config.yaml"
        self.output_dir = self.base_dir / "output"
        
    def select_config_file(self):
        """Open a file dialog to select a configuration file"""
        try:
            file_types = ('YAML Files (*.yaml;*.yml)', 'All files (*.*)')
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG, 
                allow_multiple=False,
                file_types=file_types
            )
            
            if result and len(result) > 0:
                config_path = result[0]
                return {"status": "success", "path": config_path}
            else:
                return {"status": "cancelled"}
        except Exception as e:
            logger.error(f"Error selecting config file: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    def load_config(self, config_path=None):
        """Load application configuration file"""
        try:
            if not config_path:
                config_path = self.default_config_path
            else:
                config_path = Path(config_path)
                
            logger.info(f"Loading config from: {config_path}")
            self.config = load_config(config_path)
            
            # Ensure output directory exists
            self.output_dir = Path(self.config["output"]["base_dir"])
            if not self.output_dir.is_absolute():
                self.output_dir = self.base_dir / self.output_dir
            ensure_dir(self.output_dir)
            
            # Add default competitions section if not present
            if "competitions" not in self.config:
                self.config["competitions"] = {
                    "procurement_window_size_minutes": 30,
                    "daily_service_periods": False,
                    "financial_year": None
                }
                
            logger.info(f"Config loaded successfully from {config_path}")
            return {"status": "success", "config": self.config}
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_substations(self):
        """Get list of available substations from config"""
        if not self.config:
            return {"status": "error", "message": "Config not loaded"}
        
        try:
            substations = [s["name"] for s in self.config.get("substations", [])]
            return {
                "status": "success", 
                "substations": substations
            }
        except Exception as e:
            logger.error(f"Error getting substations: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    def select_output_directory(self):
        """Open a directory dialog to select output directory"""
        try:
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG, 
                directory=str(self.output_dir)
            )
            
            if result and len(result) > 0:
                output_dir = result[0]
                # Update config
                if self.config:
                    self.config["output"]["base_dir"] = output_dir
                    self.output_dir = Path(output_dir)
                return {"status": "success", "path": output_dir}
            else:
                return {"status": "cancelled"}
        except Exception as e:
            logger.error(f"Error selecting output directory: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def run_analysis(self, substation_name, params):
        """Run the flexibility analysis for a substation"""
        try:
            logger.info(f"Starting analysis for {substation_name} with params: {params}")
            
            # Find the substation config
            sub_config = next((s for s in self.config["substations"] if s["name"] == substation_name), None)
            if not sub_config:
                logger.error(f"Substation {substation_name} not found in config")
                return {"status": "error", "message": f"Substation {substation_name} not found in config"}
            
            # Process parameters
            generate_competitions = params.get("generate_competitions", True)
            target_year = params.get("target_year")
            if target_year and isinstance(target_year, str) and target_year.strip():
                try:
                    target_year = int(target_year)
                except ValueError:
                    target_year = None
            
            # Check for schema path
            schema_path = params.get("schema_path")
            if not schema_path:
                # Look for schema in current directory
                potential_schema = self.base_dir / "flexibility_competition_schema.json"
                if potential_schema.exists():
                    schema_path = str(potential_schema)
            
            # Run the analysis
            logger.info(f"Calling process_substation_with_competitions for {substation_name}")
            result = process_substation_with_competitions(
                self.config,
                sub_config,
                generate_competitions=generate_competitions,
                target_year=target_year,
                schema_path=schema_path
            )
            
            # Return results
            output_path = str(Path(self.config["output"]["base_dir"]) / substation_name)
            logger.info(f"Analysis completed successfully for {substation_name}")
            return {
                "status": "success", 
                "result": result,
                "output_path": output_path
            }
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Error in analysis: {str(e)}\n{error_details}")
            return {"status": "error", "message": str(e), "details": error_details}
    
    def get_results(self, substation_name):
        """Get analysis results for a substation"""
        try:
            logger.info(f"Getting results for {substation_name}")
            
            # Determine output directory
            if self.config and "output" in self.config and "base_dir" in self.config["output"]:
                output_base = Path(self.config["output"]["base_dir"]) / substation_name
            else:
                output_base = self.output_dir / substation_name
            
            # Check if results exist
            results_path = output_base / "firm_capacity_results.csv"
            if not results_path.exists():
                logger.warning(f"Results not found at {results_path}")
                return {"status": "error", "message": "Results not found"}
            
            # Read results
            results_df = pd.read_csv(results_path)
            results = results_df.to_dict(orient="records")[0]
            
            # Convert numpy types to Python native types for JSON serialization
            for key, value in results.items():
                if isinstance(value, (np.integer, np.floating)):
                    results[key] = float(value) if isinstance(value, np.floating) else int(value)
            
            # Check for plots
            plots = []
            for plot_file in ["E_curve_plain.png", "E_curve_peak.png"]:
                plot_path = output_base / plot_file
                if plot_path.exists():
                    plots.append({
                        "name": plot_file.replace(".png", ""),
                        "path": f"file:///{plot_path}"
                    })
            
            # Check for competitions
            competitions_path = output_base / "competitions.json"
            competitions = None
            if competitions_path.exists():
                with open(competitions_path, "r") as f:
                    competitions = json.load(f)
            
            logger.info(f"Successfully retrieved results for {substation_name}")
            return {
                "status": "success",
                "results": results,
                "plots": plots,
                "competitions": competitions
            }
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Error getting results: {str(e)}\n{error_details}")
            return {"status": "error", "message": str(e), "details": error_details}
    
    def get_all_results(self):
        """Get a summary of all processed substations"""
        try:
            if not self.config or "output" not in self.config or "base_dir" not in self.config["output"]:
                return {"status": "error", "message": "Config not loaded or output dir not specified"}
            
            output_dir = Path(self.config["output"]["base_dir"])
            
            # Look for summary.csv
            summary_path = output_dir / "summary.csv"
            if summary_path.exists():
                summary_df = pd.read_csv(summary_path)
                summary = summary_df.to_dict(orient="records")
                return {"status": "success", "summary": summary}
            
            # If no summary.csv, check for individual results
            results = []
            for substation_dir in output_dir.iterdir():
                if not substation_dir.is_dir():
                    continue
                    
                results_path = substation_dir / "firm_capacity_results.csv"
                if results_path.exists():
                    try:
                        result_df = pd.read_csv(results_path)
                        result = result_df.to_dict(orient="records")[0]
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Error reading results for {substation_dir.name}: {str(e)}")
            
            if results:
                return {"status": "success", "summary": results}
            else:
                return {"status": "error", "message": "No results found"}
        
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Error getting all results: {str(e)}\n{error_details}")
            return {"status": "error", "message": str(e), "details": error_details}

def main():
    """Main function to start the application"""
    api = FlexibilityAnalysisAPI()
    
    # Create UI directory if it doesn't exist
    ui_dir = Path(__file__).resolve().parent / "ui"
    if not ui_dir.exists():
        ui_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up window
    window = webview.create_window(
        'Flexibility Analysis System',
        'ui/index.html',
        js_api=api,
        width=1200,
        height=800,
        resizable=True,
        text_select=True,
        confirm_close=True,
        min_size=(800, 600)
    )
    
    # Start the application
    webview.start(debug=True)

if __name__ == "__main__":
    main()
