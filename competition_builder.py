"""
competition_builder.py - Creates flexibility competitions based on firm capacity analysis

This module adds competition generation functionality to the firm capacity analysis project.
"""

import pandas as pd
import json
import numpy as np
import calendar
from pathlib import Path
import uuid
from typing import List, Dict, Set, Optional, Tuple
import logging
from itertools import groupby
from datetime import datetime, timedelta

# Import local modules
from competition_dates import (
    generate_competition_dates,
    validate_dates,
    format_dates_for_competition,
    generate_dates_for_financial_year
)

from service_windows import (
    find_overload_segments,
    generate_service_windows_from_demand_data,
    generate_competition_service_periods
)

from competition_config import (
    ConfigMode,
    FieldLevel,
    FieldSelector,
    ROOT_LEVEL_FIELDS,
    SERVICE_WINDOW_FIELDS
)

logger = logging.getLogger(__name__)

def sanitize_reference(substation_name: str, licence_area: str = "SPEN", year: int = None, month: int = None, day: Optional[int] = None) -> str:
    """
    Create a valid competition reference string that matches the schema pattern ^[a-zA-Z0-9_]{1,40}$
    
    Args:
        substation_name: Name of the substation
        licence_area: Licence area code (default: "SPEN")
        year: Year (optional)
        month: Month number (1-12) (optional)
        day: Optional day of month (1-31)
        
    Returns:
        Reference string in required format
    """
    # If year/month not provided, use current date
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    # Remove any non-alphanumeric characters except underscores
    sanitized_name = ''.join(c for c in substation_name if c.isalnum() or c == '_')
    
    # Format year, month and day
    year_str = f"{year % 100:02d}"  # Get last 2 digits
    month_str = f"{month:02d}"
    
    # Construct reference with guaranteed valid format
    if day:
        day_str = f"{day:02d}"
        reference = f"T{year_str}{month_str}{day_str}_{licence_area}_{sanitized_name}"
    else:
        reference = f"T{year_str}{month_str}_{licence_area}_{sanitized_name}"
    
    # Ensure length is within 40 characters
    if len(reference) > 40:
        max_name_length = 40 - len(reference) + len(sanitized_name)
        sanitized_name = sanitized_name[:max_name_length]
        
        if day:
            reference = f"T{year_str}{month_str}{day_str}_{licence_area}_{sanitized_name}"
        else:
            reference = f"T{year_str}{month_str}_{licence_area}_{sanitized_name}"
    
    return reference

def create_competition_template(
    selected_fields: Dict[FieldLevel, Set[str]],
    substation_name: str,
    service_periods: List[Dict],
    reference: str,
    nominal_voltage: Optional[float] = None,
    financial_year: Optional[str] = None
) -> Dict:
    """
    Create a competition template with properly categorized fields.
    
    Args:
        selected_fields: Dictionary mapping FieldLevel to sets of field names
        substation_name: Name of the substation
        service_periods: List of service period dictionaries
        reference: Competition reference string
        nominal_voltage: Optional nominal voltage value
        financial_year: Optional financial year string (e.g., "2025/26")
    """
    # Get period dates from the collection of service periods
    if not service_periods:
        raise ValueError("No service periods provided for competition creation")
    
    # For monthly competitions with daily service periods, use the first and last day of the month
    period_starts = [pd.Timestamp(period['start']) for period in service_periods]
    period_ends = [pd.Timestamp(period['end']) for period in service_periods]
    
    period_start = min(period_starts)
    period_end = max(period_ends)

    # Generate competition dates
    if financial_year:
        # Use financial year dates if specified
        fy_dates = generate_dates_for_financial_year(financial_year)
        month_dates = fy_dates[fy_dates['month'] == period_start.strftime('%B')]
        if month_dates.empty:
            raise ValueError(f"No dates found for {period_start.strftime('%B')} in financial year {financial_year}")
        competition_dates = {
            'qualification_open': month_dates['qualification_open'].iloc[0],
            'qualification_closed': month_dates['qualification_closed'].iloc[0],
            'bidding_open': month_dates['bidding_open'].iloc[0],
            'bidding_closed': month_dates['bidding_closed'].iloc[0]
        }
    else:
        # Generate dates based on service period start
        competition_dates = generate_competition_dates(period_start)
    
    # Validate the generated dates
    if not validate_dates(competition_dates):
        raise ValueError(f"Invalid competition dates generated for {period_start}")
    
    # Format dates for competition
    formatted_dates = format_dates_for_competition(competition_dates)
    
    # Create a name for the competition that includes the month
    month_name = calendar.month_name[period_start.month]
    competition_name = f"{substation_name.upper()} {month_name} {period_start.year}"
    
    # Start with required fields
    competition = {
        "reference": reference,
        "name": competition_name,
        "open": formatted_dates['bidding_open'],
        "closed": formatted_dates['bidding_closed'],
        "area_buffer": "0.100",
        "qualification_open": formatted_dates['qualification_open'],
        "qualification_closed": formatted_dates['qualification_closed'],
        "boundary": {
            "area_references": [substation_name.upper()],
            "postcodes": []  # Required by schema
        },
        "need_type": "Pre Fault",
        "type": "Utilisation",
        "need_direction": "Deficit",
        "power_type": "Active Power",
        "service_periods": service_periods
    }

    # Handle voltage fields
    max_voltage = "33"  # Default if no nominal voltage provided
    min_voltage = "0.24"   
    
    # If nominal voltage is provided, use it to determine max_voltage
    if nominal_voltage is not None:
        try:
            if nominal_voltage == "HV":
                nominal_voltage = float("11")  # Default HV voltage

            # Convert to float if it's a string
            nominal_voltage_float = float(nominal_voltage)
            
            if nominal_voltage_float <= 0.4:
                max_voltage = "0.4"
            elif nominal_voltage_float <= 6.6:
                max_voltage = "6.6"
            elif nominal_voltage_float <= 11:
                max_voltage = "11"
            elif nominal_voltage_float <= 22:
                max_voltage = "22"
            elif nominal_voltage_float <= 33:
                max_voltage = "33"
            elif nominal_voltage_float <= 66:
                max_voltage = "66"
            elif nominal_voltage_float <= 132:
                max_voltage = "132"
        except (ValueError, TypeError):
            # If conversion fails, use default
            logger.warning(f"Could not convert nominal voltage '{nominal_voltage}' to float. Using default.")
    
    # Root level field defaults
    root_level_defaults = {
        "contact": "flexibility@example.com",
        "archive_on": (pd.Timestamp(formatted_dates['bidding_closed']) + pd.Timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dps_record_reference": f"flex_{reference.lower()}",
        "product_type": "Scheduled Utilisation",
        "minimum_connection_voltage": min_voltage,
        "maximum_connection_voltage": max_voltage,
        "minimum_budget": "5000.00",
        "maximum_budget": "10000.00",
        "availability_guide_price": "10.00",
        "utilisation_guide_price": "240",
        "service_fee": "9.45",
        "pricing_type": "auction"
    }
    
    # Add root level optional fields
    root_fields = selected_fields.get(FieldLevel.ROOT, set())
    for field in root_fields:
        if field in root_level_defaults:
            competition[field] = root_level_defaults[field]
    
    return competition

def create_competitions_from_df(
    df: pd.DataFrame,
    firm_capacity: float,
    schema_path: Optional[str] = None,
    config_mode: ConfigMode = ConfigMode.STANDARD,
    custom_fields: Optional[Set[str]] = None,
    risk_threshold: float = 0.05,  # Not used, kept for API compatibility
    assessment_window_size_minutes: int = 120,  # Not used for segment identification 
    procurement_window_size_minutes: int = 30,
    disaggregate_days: bool = False,  # Not used, we always use specific days
    daily_service_periods: bool = False,
    group_by_day_type: bool = True,  # Not used, we always use specific segments
    financial_year: Optional[str] = None,
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Creates competitions based on the demand data and firm capacity.
    Uses same logic as energy_peak_based for service window generation.
    
    Args:
        df: DataFrame with timestamps and demand data
        firm_capacity: Firm capacity in MW
        schema_path: Optional path to the competition schema 
        config_mode: Configuration mode (REQUIRED_ONLY, STANDARD, or CUSTOM)
        custom_fields: Set of optional fields to include when using CUSTOM mode
        risk_threshold: Not used, kept for API compatibility
        assessment_window_size_minutes: Not used for segment identification
        procurement_window_size_minutes: Size of procurement windows in minutes
        disaggregate_days: Not used, we always use specific days
        daily_service_periods: Whether to create a service period per day instead of per month
        group_by_day_type: Not used, we always use specific segments
        financial_year: Optional financial year string (e.g., "2025/26")
        delta_t: Time step in hours (default: 0.5 for half-hourly data)
    """
    # Validate the dataframe format and columns
    required_columns = ["Timestamp", "Demand (MW)"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Ensure timestamps are in datetime format
    df = df.copy()
    
    # Check if we have timezone-aware datetime objects
    timestamp_col = df["Timestamp"]
    
    if pd.api.types.is_datetime64_any_dtype(timestamp_col):
        # Already datetime64 dtype - check for timezone
        if hasattr(timestamp_col.dtype, 'tz') and timestamp_col.dtype.tz is not None:
            # Convert timezone-aware datetime64 to naive
            df["Timestamp"] = timestamp_col.dt.tz_localize(None)
    elif timestamp_col.dtype == 'object':
        # Object dtype - could be timezone-aware datetime objects
        sample_values = timestamp_col.dropna().head(5)
        if len(sample_values) > 0:
            first_value = sample_values.iloc[0]
            # Check if it's already a datetime object with timezone info
            if hasattr(first_value, 'tzinfo') and first_value.tzinfo is not None:
                # These are timezone-aware datetime objects - convert them safely
                df["Timestamp"] = pd.to_datetime(timestamp_col, utc=True).dt.tz_localize(None)
            elif isinstance(first_value, str):
                # String timestamps - let pandas parse them
                df["Timestamp"] = pd.to_datetime(timestamp_col)
            else:
                # Some other format - try basic conversion
                df["Timestamp"] = pd.to_datetime(timestamp_col)
    else:
        # Non-datetime, non-object dtype - convert normally
        df["Timestamp"] = pd.to_datetime(timestamp_col)
    
    # Sort by timestamp
    df = df.sort_values("Timestamp")
    
    # Extract substation name from the first part of the file or from config
    substation_name = df.get("Substation", None)
    if substation_name is None:
        # Use the first part of the filename or a default
        substation_name = "Substation"  # Default name
    elif isinstance(substation_name, pd.Series):
        substation_name = substation_name.iloc[0]
    
    # Extract nominal voltage if available
    nominal_voltage = df.get("Nominal Voltage", None)
    if nominal_voltage is not None and isinstance(nominal_voltage, pd.Series):
        nominal_voltage = nominal_voltage.iloc[0]
    
    # Initialize field selector and get categorized fields
    field_selector = FieldSelector()
    selected_fields = field_selector.get_fields_for_mode(config_mode, custom_fields)
    
    # Calculate total energy above capacity using energy_peak_based logic
    segments = find_overload_segments(df, firm_capacity, delta_t)
    total_mwh = sum(segment['energy_mwh'] for segment in segments)
    logger.info(f"Total energy above capacity: {total_mwh:.2f} MWh")
    
    # Generate service periods
    service_periods = generate_competition_service_periods(
        df,
        firm_capacity,
        risk_threshold=risk_threshold,  # Not used but kept for API compatibility
        assessment_window_size_minutes=assessment_window_size_minutes,  # Not used for segment identification
        procurement_window_size_minutes=procurement_window_size_minutes,
        disaggregate_days=disaggregate_days,  # Not used, we always use specific days
        daily_service_periods=daily_service_periods,
        group_by_day_type=group_by_day_type,  # Not used, we always use specific segments
        delta_t=delta_t
    )
    
    if not service_periods:
        logger.info(f"No service periods generated for {substation_name}")
        return []
    
    competitions = []
    
    # Group service periods by month and create competitions
    period_by_month = {}
    for period in service_periods:
        start_date = pd.Timestamp(period['start'])
        month = start_date.month
        year = start_date.year
        
        key = (year, month)
        if key not in period_by_month:
            period_by_month[key] = []
        period_by_month[key].append(period)
    
    # Create a competition for each month
    for (year, month), periods in period_by_month.items():
        reference = sanitize_reference(
            substation_name=substation_name,
            year=year,
            month=month
        )
        
        competition = create_competition_template(
            selected_fields,
            substation_name,
            periods,
            reference,
            nominal_voltage,
            financial_year
        )
        
        competitions.append(competition)
    
    # Verify the total energy is preserved
    if competitions:
        # Calculate total MWh in all competitions
        total_competition_mwh = 0
        for comp in competitions:
            for period in comp['service_periods']:
                for window in period['service_windows']:
                    if 'energy_mwh' in window:
                        total_competition_mwh += window['energy_mwh']
        
        logger.info(f"Total MWh in competitions: {total_competition_mwh:.2f}")
        
        # Check if totals match
        if abs(total_mwh - total_competition_mwh) > 0.01:  # Allow small rounding differences
            logger.warning(f"MWh mismatch: energy_peak_based total = {total_mwh:.2f}, competition total = {total_competition_mwh:.2f}")
        else:
            logger.info(f"MWh totals match: {total_mwh:.2f} = {total_competition_mwh:.2f}")
    
    return competitions

def save_competitions_to_json(competitions: List[Dict], output_path: str):
    """
    Save competitions to JSON file
    
    Args:
        competitions: List of competition dictionaries
        output_path: Path to save the output file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Remove calculation fields before saving
    clean_competitions = []
    for comp in competitions:
        clean_comp = comp.copy()
        for period in clean_comp['service_periods']:
            for window in period['service_windows']:
                # Remove calculation fields
                if 'energy_mwh' in window:
                    del window['energy_mwh']
                if 'duration_hours' in window:
                    del window['duration_hours']
        clean_competitions.append(clean_comp)
    
    with open(output_path, "w") as f:
        json.dump(clean_competitions, f, indent=2)
        
    logger.info(f"Saved {len(competitions)} competitions to {output_path}")

def validate_competitions_with_schema(competitions: List[Dict], schema_path: str) -> List[Dict]:
    """
    Validate competitions against the JSON schema
    
    Args:
        competitions: List of competition dictionaries
        schema_path: Path to the JSON schema file
        
    Returns:
        List of validation errors, empty if all competitions are valid
    """
    try:
        import jsonschema
        from jsonschema import validate
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        errors = []
        
        for i, comp in enumerate(competitions):
            try:
                validate(instance=comp, schema=schema)
            except jsonschema.exceptions.ValidationError as e:
                errors.append({
                    'competition_index': i,
                    'competition_name': comp.get('name', 'Unnamed'),
                    'error_message': str(e),
                    'error_path': list(e.absolute_path),
                    'schema_path': list(e.absolute_schema_path)
                })
        
        return errors
    
    except ImportError:
        logger.warning("jsonschema package not installed. Skipping validation.")
        return []