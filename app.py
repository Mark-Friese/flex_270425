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
import math
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

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

class GisApiClient:
    """Client for interacting with the GIS API"""
    
    def __init__(self, base_url: str = "", api_key: Optional[str] = None):
        """Initialize the GIS API client
        
        Args:
            base_url: Base URL for the API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.endpoints = {
            "substations": "/api/gis/substations",
            "demand_groups": "/api/gis/demand-groups",
            "circuits": "/api/gis/circuits"
        }
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the API
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            Response JSON
        
        Raises:
            requests.RequestException: If the request fails
        """
        if not self.base_url:
            raise ValueError("API base URL not configured")
            
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        
        # Raise exception for error status codes
        response.raise_for_status()
        
        return response.json()
        
    def get_substations(self, area: Optional[str] = None, substation_type: Optional[str] = None) -> Dict:
        """Get substations from the API
        
        Args:
            area: Optional area filter
            substation_type: Optional substation type filter
            
        Returns:
            GeoJSON response with substation data
        """
        params = {}
        if area:
            params["area"] = area
        if substation_type:
            params["type"] = substation_type
            
        return self._make_request(self.endpoints["substations"], params)
        
    def get_demand_groups(self, group_ids: Optional[List[int]] = None) -> Dict:
        """Get demand groups from the API
        
        Args:
            group_ids: Optional list of group IDs to filter
            
        Returns:
            GeoJSON response with demand group data
        """
        params = {}
        if group_ids:
            params["group_ids"] = group_ids
            
        return self._make_request(self.endpoints["demand_groups"], params)
        
    def get_circuits(self, voltage: Optional[float] = None, from_substation: Optional[int] = None) -> Dict:
        """Get circuits from the API
        
        Args:
            voltage: Optional voltage level filter
            from_substation: Optional source substation ID filter
            
        Returns:
            GeoJSON response with circuit data
        """
        params = {}
        if voltage:
            params["voltage"] = voltage
        if from_substation:
            params["from_substation"] = from_substation
            
        return self._make_request(self.endpoints["circuits"], params)
        
    def _convert_substations_to_app_format(self, geojson: Dict) -> List[Dict]:
        """Convert substations GeoJSON to app format
        
        Args:
            geojson: GeoJSON from the API
            
        Returns:
            List of substation objects in app format
        """
        substations = []
        
        # Process each substation feature
        if "features" in geojson:
            for feature in geojson["features"]:
                if feature["geometry"]["type"] != "Point":
                    continue
                    
                properties = feature["properties"]
                coordinates = feature["geometry"]["coordinates"]
                
                # Create substation in app format
                substation = {
                    "name": properties.get("id") or properties.get("name"),
                    "display_name": properties.get("name") or properties.get("display_name") or properties.get("id"),
                    "coordinates": {
                        "lat": coordinates[1],  # GeoJSON uses [longitude, latitude]
                        "lng": coordinates[0]
                    },
                    "metadata": {
                        "voltage_level": properties.get("voltage_level") or properties.get("voltage") or "33/11kV",
                        "region": properties.get("region") or properties.get("area") or "Default",
                        "capacity_mw": properties.get("capacity") or properties.get("capacity_mw") or 30.0,
                        "transformer_count": properties.get("transformer_count") or 1,
                        "demand_group": properties.get("demand_group") or properties.get("group_id")
                    },
                    "icon": {
                        "color": "#0DA9FF" if "132" in str(properties.get("voltage_level") or "") else "#00A443",
                        "size": "large" if "132" in str(properties.get("voltage_level") or "") else "medium"
                    }
                }
                
                substations.append(substation)
                
        return substations
        
    def _convert_demand_groups_to_app_format(self, geojson: Dict) -> List[Dict]:
        """Convert demand groups GeoJSON to app format
        
        Args:
            geojson: GeoJSON from the API
            
        Returns:
            List of demand group objects in app format
        """
        demand_groups = []
        
        # Process each demand group feature
        if "features" in geojson:
            for feature in geojson["features"]:
                if feature["geometry"]["type"] != "Polygon":
                    continue
                    
                properties = feature["properties"]
                coordinates = feature["geometry"]["coordinates"]
                
                # Skip if no polygon data
                if not coordinates or not coordinates[0]:
                    continue
                    
                # Extract points from the first polygon ring
                points = [{"lat": coord[1], "lng": coord[0]} for coord in coordinates[0]]
                
                # Create demand group in app format
                demand_group = {
                    "id": properties.get("id") or properties.get("group_id"),
                    "name": properties.get("name") or properties.get("display_name") or f"Group {properties.get('id')}",
                    "polygon": {
                        "color": properties.get("color") or "#00A443",
                        "fillColor": properties.get("fillColor") or "#00A44333",
                        "weight": properties.get("weight") or 2,
                        "points": points
                    },
                    "metadata": {
                        "firm_capacity_mw": properties.get("firm_capacity") or properties.get("capacity") or 45.0,
                        "total_energy_mwh": properties.get("total_energy") or properties.get("energy") or 980.0,
                        "energy_above_capacity_mwh": properties.get("energy_above_capacity") or 18.0,
                        "substation_count": properties.get("substation_count") or 1,
                        "substations": properties.get("substations") or [],
                        "peak_demand_time": properties.get("peak_time") or "2025-01-15T18:30:00Z"
                    }
                }
                
                demand_groups.append(demand_group)
                
        return demand_groups
        
    def get_map_data(self) -> Dict:
        """Get complete map data (substations and demand groups)
        
        Returns:
            Map data in app format
        """
        try:
            # Get substations and demand groups
            substations_geojson = self.get_substations()
            demand_groups_geojson = self.get_demand_groups()
            
            # Convert to app format
            substations = self._convert_substations_to_app_format(substations_geojson)
            demand_groups = self._convert_demand_groups_to_app_format(demand_groups_geojson)
            
            # Calculate map center (average of substation coordinates)
            if substations:
                lat_sum = sum(s["coordinates"]["lat"] for s in substations)
                lng_sum = sum(s["coordinates"]["lng"] for s in substations)
                center = {
                    "lat": lat_sum / len(substations),
                    "lng": lng_sum / len(substations)
                }
            else:
                center = {"lat": 55.0500, "lng": -1.4500}  # Default UK center
                
            # Create complete map data structure
            map_data = {
                "substations": substations,
                "demand_groups": demand_groups,
                "layers": [
                    {
                        "id": "substations",
                        "name": "Substations",
                        "type": "marker",
                        "visible": True,
                        "source": "substations"
                    },
                    {
                        "id": "demand_groups",
                        "name": "Demand Groups",
                        "type": "polygon",
                        "visible": True,
                        "source": "demand_groups"
                    }
                ],
                "map_defaults": {
                    "center": center,
                    "zoom": 10,
                    "max_zoom": 18,
                    "min_zoom": 6
                }
            }
            
            return map_data
            
        except Exception as e:
            logger.error(f"Error getting map data from API: {str(e)}")
            raise

class FlexibilityAnalysisAPI:
    """API class to handle interaction between web UI and Python backend"""
    
    def __init__(self):
        self.config = None
        self.base_dir = Path(__file__).resolve().parent
        self.default_config_path = self.base_dir / "config.yaml"
        self.output_dir = self.base_dir / "output"
        
        # Ensure assets directory exists
        self.assets_dir = self.base_dir / "ui" / "assets"
        if not self.assets_dir.exists():
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            
        # Ensure documentation directory exists
        self.docs_dir = self.base_dir / "ui" / "docs"
        if not self.docs_dir.exists():
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            
        # Load API settings
        self.api_settings = self.get_api_settings()
        
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
    
    def save_map_data(self, data):
        """Save map data to the substation_coordinates.json file
        
        Args:
            data (dict): Map data with substations and demand groups
            
        Returns:
            dict: Result of the operation
        """
        try:
            coords_path = self.assets_dir / "substation_coordinates.json"
            
            # Validate basic structure
            required_keys = ["substations"]
            for key in required_keys:
                if key not in data:
                    return {"status": "error", "message": f"Missing required key: {key}"}
            
            # Save data to file
            with open(coords_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved map data to {coords_path} with {len(data['substations'])} substations and {len(data.get('demand_groups', []))} demand groups")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error saving map data: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def load_map_data(self):
        """Load map data from the substation_coordinates.json file
        
        Returns:
            dict: Map data or error message
        """
        try:
            coords_path = self.assets_dir / "substation_coordinates.json"
            
            if not coords_path.exists():
                logger.warning(f"Map data file not found at {coords_path}")
                return {"status": "error", "message": "Map data file not found"}
            
            with open(coords_path, "r") as f:
                data = json.load(f)
            
            logger.info(f"Loaded map data with {len(data['substations'])} substations and {len(data.get('demand_groups', []))} demand groups")
            return {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"Error loading map data: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def match_substations_to_coordinates(self):
        """Match substations in config with coordinates in the map data
        
        Returns:
            dict: Mapping of matched and unmatched substations
        """
        try:
            if not self.config:
                return {"status": "error", "message": "No configuration loaded"}
            
            # Load map data
            map_data_result = self.load_map_data()
            if map_data_result["status"] != "success":
                return map_data_result
            
            map_data = map_data_result["data"]
            
            # Get substations from config
            config_substations = self.config.get("substations", [])
            
            # Match substations
            matched = []
            unmatched = []
            
            for sub in config_substations:
                sub_name = sub["name"].lower()
                
                # Check if it exists in map data
                map_sub = next((s for s in map_data["substations"] if s["name"].lower() == sub_name), None)
                
                if map_sub:
                    matched.append({
                        "name": sub["name"],
                        "display_name": map_sub.get("display_name", sub["name"]),
                        "coordinates": map_sub["coordinates"]
                    })
                else:
                    unmatched.append(sub["name"])
            
            return {
                "status": "success",
                "matched": matched,
                "unmatched": unmatched,
                "match_percentage": len(matched) / len(config_substations) * 100 if config_substations else 0
            }
        except Exception as e:
            logger.error(f"Error matching substations: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def generate_default_map_data(self):
        """Generate default map data based on current config
        
        Returns:
            dict: Generated map data
        """
        try:
            if not self.config:
                return {"status": "error", "message": "No configuration loaded"}
            
            # Get substations from config
            config_substations = self.config.get("substations", [])
            
            if not config_substations:
                return {"status": "error", "message": "No substations in configuration"}
            
            # Create basic map data structure
            map_data = {
                "substations": [],
                "demand_groups": [],
                "layers": [
                    {
                        "id": "substations",
                        "name": "Substations",
                        "type": "marker",
                        "visible": True,
                        "source": "substations"
                    },
                    {
                        "id": "demand_groups",
                        "name": "Demand Groups",
                        "type": "polygon",
                        "visible": True,
                        "source": "demand_groups"
                    }
                ],
                "map_defaults": {
                    "center": {
                        "lat": 55.378,
                        "lng": -3.436
                    },
                    "zoom": 6,
                    "max_zoom": 18,
                    "min_zoom": 5
                }
            }
            
            # Generate dummy coordinates for demonstration
            # In a real application, these could be geocoded from address data
            base_lat = 55.378
            base_lng = -3.436
            
            for i, sub in enumerate(config_substations):
                # Generate a somewhat distributed set of points
                angle = (i / len(config_substations)) * 2 * math.pi  # Full circle distribution
                distance = 0.5 + (i % 3) * 0.2  # Varying distances
                
                # Calculate coordinates using a simple offset pattern
                lat = base_lat + distance * math.cos(angle)
                lng = base_lng + distance * math.sin(angle)
                
                # Create substation entry
                map_data["substations"].append({
                    "name": sub["name"],
                    "display_name": sub["name"].replace("_", " ").title(),
                    "coordinates": {
                        "lat": lat,
                        "lng": lng
                    },
                    "metadata": {
                        "voltage_level": "33/11kV",  # Default
                        "region": "Default Region",
                        "capacity_mw": 30.0,  # Default
                        "demand_group": f"default_group_{i // 3}"  # Group every 3 substations
                    },
                    "icon": {
                        "color": "#00A443",
                        "size": "medium"
                    }
                })
            
            # Create demand groups
            group_counts = {}
            for sub in map_data["substations"]:
                group_id = sub["metadata"]["demand_group"]
                if group_id not in group_counts:
                    group_counts[group_id] = {
                        "count": 0,
                        "substations": [],
                        "center": {"lat": 0, "lng": 0}
                    }
                
                group_counts[group_id]["count"] += 1
                group_counts[group_id]["substations"].append(sub["name"])
                group_counts[group_id]["center"]["lat"] += sub["coordinates"]["lat"]
                group_counts[group_id]["center"]["lng"] += sub["coordinates"]["lng"]
            
            # Finalize demand groups
            for group_id, data in group_counts.items():
                # Calculate center
                center_lat = data["center"]["lat"] / data["count"]
                center_lng = data["center"]["lng"] / data["count"]
                
                # Create simple polygon around center
                points = []
                for i in range(6):  # Hexagon
                    angle = (i / 6) * 2 * math.pi
                    # Size based on number of substations
                    size = 0.1 + (data["count"] * 0.05)
                    point_lat = center_lat + size * math.cos(angle)
                    point_lng = center_lng + size * math.sin(angle)
                    points.append({"lat": point_lat, "lng": point_lng})
                
                # Add closing point
                points.append(points[0])
                
                # Create demand group
                map_data["demand_groups"].append({
                    "id": group_id,
                    "name": group_id.replace("_", " ").title(),
                    "polygon": {
                        "color": "#0DA9FF",
                        "fillColor": "#0DA9FF33",
                        "weight": 2,
                        "points": points
                    },
                    "metadata": {
                        "firm_capacity_mw": 30.0 * data["count"],  # Example calculation
                        "total_energy_mwh": 800.0 * data["count"],
                        "energy_above_capacity_mwh": 20.0 * data["count"],
                        "substation_count": data["count"],
                        "substations": data["substations"]
                    }
                })
            
            # Save the generated data
            save_result = self.save_map_data(map_data)
            if save_result["status"] != "success":
                return save_result
            
            return {"status": "success", "data": map_data}
        except Exception as e:
            logger.error(f"Error generating map data: {str(e)}")
            return {"status": "error", "message": str(e)}

    # API-related methods
    def get_api_settings(self):
        """Get current API settings
        
        Returns:
            Dict with API settings
        """
        # Find config file location
        settings_path = self.base_dir / "api_settings.json"
        
        if not settings_path.exists():
            return {
                "use_api": False,
                "base_url": "",
                "api_key": ""
            }
            
        try:
            with open(settings_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading API settings: {str(e)}")
            return {
                "use_api": False,
                "base_url": "",
                "api_key": ""
            }
    
    def save_api_settings(self, settings):
        """Save API settings
        
        Args:
            settings: Dict with API settings
        
        Returns:
            Dict with result status
        """
        try:
            # Validate settings
            if not isinstance(settings, dict):
                return {"status": "error", "message": "Invalid settings format"}
                
            # Ensure directory exists
            settings_path = self.base_dir / "api_settings.json"
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write settings
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
                
            # Update internal settings
            self.api_settings = settings
                
            logger.info(f"Saved API settings: {settings.get('base_url')}")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error saving API settings: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def load_map_data_from_api(self):
        """Load map data from the GIS API
        
        Returns:
            Dict with map data or error status
        """
        try:
            # Check if API is configured
            if not self.api_settings.get("use_api") or not self.api_settings.get("base_url"):
                return {"status": "error", "message": "API not configured"}
                
            # Create API client
            client = GisApiClient(
                base_url=self.api_settings.get("base_url"),
                api_key=self.api_settings.get("api_key")
            )
            
            logger.info(f"Fetching map data from API: {self.api_settings.get('base_url')}")
            
            # Get map data
            map_data = client.get_map_data()
            
            # Save to file for caching
            coords_path = self.assets_dir / "substation_coordinates.json"
            with open(coords_path, "w") as f:
                json.dump(map_data, f, indent=2)
                
            logger.info(f"Loaded map data from API: {len(map_data.get('substations', []))} substations, {len(map_data.get('demand_groups', []))} demand groups")
            return {"status": "success", "data": map_data}
        except Exception as e:
            logger.error(f"Error loading map data from API: {str(e)}")
            return {"status": "error", "message": str(e)}

def copy_documentation():
    """Copy built documentation from 'site' folder to 'ui/docs'.
    
    This makes the documentation available for offline viewing in the app.
    """
    site_dir = Path(__file__).resolve().parent / "site"
    docs_dir = Path(__file__).resolve().parent / "ui" / "site"
    
    if not site_dir.exists():
        logger.warning(f"Documentation source directory '{site_dir}' not found.")
        return False
    
    # Create docs directory if it doesn't exist
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Remove existing documentation files to ensure a clean copy
        import shutil
        if docs_dir.exists():
            for item in docs_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        # Copy all contents of site directory to docs directory
        for item in site_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, docs_dir / item.name)
            else:
                shutil.copy2(item, docs_dir / item.name)
        
        logger.info(f"Documentation copied successfully from {site_dir} to {docs_dir}")
        return True
    except Exception as e:
        logger.error(f"Error copying documentation: {str(e)}")
        return False

def main():
    """Main function to start the application"""
    # Copy documentation for offline use
    copy_documentation()
    
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