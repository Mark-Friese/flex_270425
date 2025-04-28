"""
service_windows.py - Service window generation for flexibility competitions

This module provides functions for generating service windows from demand data
using the same logic as energy_peak_based to ensure consistency.
"""

import pandas as pd
import numpy as np
import calendar
from datetime import datetime, time, timedelta
from typing import List, Dict, Tuple, Set, Optional, Union
import logging
import re

# Local imports
from competition_config import (
    ConfigMode,
    FieldLevel,
    FieldSelector,
    SERVICE_WINDOW_FIELDS
)

logger = logging.getLogger(__name__)

def round_to_half_hour(minutes: int) -> int:
    """Round a number of minutes to the nearest 30-minute increment."""
    return int(round(minutes / 30.0)) * 30

def format_time_window(
    hour: int, 
    minute: int, 
    window_duration_minutes: int = 120
) -> Tuple[str, str]:
    """
    Convert time bucket to start/end time strings.
    Ensures window duration is in 0.5h increments.
    
    Args:
        hour: Starting hour (0-23)
        minute: Starting minute (0-59)
        window_duration_minutes: Duration of window in minutes
        
    Returns:
        Tuple of (start_time, end_time) in HH:MM format
    """
    # Ensure window_duration_minutes is in 0.5h increments
    window_duration_minutes = round_to_half_hour(window_duration_minutes)
    
    start = f"{hour:02d}:{minute:02d}"
    
    # Calculate end time
    end_minutes = hour * 60 + minute + window_duration_minutes
    end_hour = int((end_minutes // 60) % 24)
    end_minute = int(end_minutes % 60)
    
    # Handle end time to ensure it doesn't exceed 23:59
    if end_hour < hour:  # Would roll over to next day
        end_hour = 23
        end_minute = 59
        
    end = f"{end_hour:02d}:{end_minute:02d}"
        
    return start, end

def get_service_days(is_weekend: int, day_of_week: Optional[int] = None, disaggregate: bool = False) -> List[str]:
    """
    Get list of service days based on weekend flag and day of week.
    
    Args:
        is_weekend: Flag indicating if it's a weekend
        day_of_week: Day of week (0 = Monday, 6 = Sunday)
        disaggregate: If True, return individual days rather than grouped lists
        
    Returns:
        List containing service days
    """
    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekdays = all_days[:5]
    weekend_days = all_days[5:]
    
    # For daily service periods, we only want the specific day
    if disaggregate and day_of_week is not None:
        return [all_days[day_of_week]]
    else:
        return weekend_days if is_weekend else weekdays

def split_assessment_window_for_procurement(
    window: Dict,
    assessment_window_size_minutes: int,
    procurement_window_size_minutes: int
) -> List[Dict]:
    """
    Split a single assessment window into multiple procurement windows.
    All procurement windows inherit the same capacity requirement.
    
    Args:
        window: Assessment window dictionary
        assessment_window_size_minutes: Size of assessment window in minutes
        procurement_window_size_minutes: Size of procurement windows in minutes
        
    Returns:
        List of procurement window dictionaries
    """
    # Ensure window sizes are in 0.5h increments
    procurement_window_size_minutes = round_to_half_hour(procurement_window_size_minutes)
    
    # Parse original window times
    start_time = window['start']
    end_time = window['end']
    
    hour_start, min_start = map(int, start_time.split(':'))
    hour_end, min_end = map(int, end_time.split(':'))
    
    start_minutes = hour_start * 60 + min_start
    end_minutes = hour_end * 60 + min_end
    
    # Handle overnight windows
    if end_minutes <= start_minutes:
        end_minutes += 24 * 60  # Add a day in minutes
    
    # Calculate window duration and ensure it's in 0.5h increments
    window_duration = end_minutes - start_minutes
    window_duration = round_to_half_hour(window_duration)
    end_minutes = start_minutes + window_duration
    
    # Calculate number of procurement windows
    num_windows = max(1, window_duration // procurement_window_size_minutes)
    
    procurement_windows = []
    
    # If there's only one window or their duration is the same, return the original
    if num_windows == 1 or assessment_window_size_minutes == procurement_window_size_minutes:
        return [window]
    
    # Calculate total energy in the original window
    original_energy = float(window.get('energy_mwh', 0))
    
    # Distribute energy proportionally based on duration
    energy_per_hour = original_energy / (window_duration / 60)
    
    for i in range(num_windows):
        # Calculate start/end for this procurement window
        w_start_minutes = start_minutes + (i * procurement_window_size_minutes)
        w_end_minutes = min(w_start_minutes + procurement_window_size_minutes, end_minutes)
        
        # Normalize times to 24-hour day
        w_start_hour = int((w_start_minutes // 60) % 24)
        w_start_min = int(w_start_minutes % 60)
        w_end_hour = int((w_end_minutes // 60) % 24)
        w_end_min = int(w_end_minutes % 60)
        
        # Format as HH:MM
        new_start = f"{w_start_hour:02d}:{w_start_min:02d}"
        new_end = f"{w_end_hour:02d}:{w_end_min:02d}"
        
        # Extract the day type (Weekday/Weekend/specific day)
        day_type = window['name'].split(' ')[0]
        new_name = f"{day_type} {new_start}-{new_end}"
        
        # Clone original window with new times but same capacity
        new_window = window.copy()
        new_window['start'] = new_start
        new_window['end'] = new_end
        new_window['name'] = new_name
        
        # Calculate duration in hours for this window
        window_duration_hours = (w_end_minutes - w_start_minutes) / 60.0
        
        # Add duration_hours field for later MWh calculations
        new_window['duration_hours'] = window_duration_hours
        
        # Calculate energy for this smaller window - proportional to duration
        if original_energy > 0:
            new_window['energy_mwh'] = energy_per_hour * window_duration_hours
        
        procurement_windows.append(new_window)
    
    # Verify that the total energy in procurement windows equals the original
    total_energy = sum(w.get('energy_mwh', 0) for w in procurement_windows)
    if abs(total_energy - original_energy) > 0.01:  # Allow small rounding differences
        # Adjust the last window to ensure total matches
        procurement_windows[-1]['energy_mwh'] += (original_energy - total_energy)
    
    return procurement_windows

def find_overload_segments(
    df: pd.DataFrame,
    firm_capacity: float,
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Identify contiguous segments where demand exceeds firm capacity.
    Uses the same logic as energy_peak_based to ensure consistency.
    
    Args:
        df: DataFrame with Timestamp and Demand (MW) columns
        firm_capacity: Firm capacity in MW
        delta_t: Time step in hours (default: 0.5 for half-hourly data)
        
    Returns:
        List of dictionaries with overload segment information
    """
    # Validate input DataFrame
    required_columns = ["Timestamp", "Demand (MW)"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Ensure timestamps are datetime
    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["Timestamp"]):
        data["Timestamp"] = pd.to_datetime(data["Timestamp"])
    
    # Sort by timestamp
    data = data.sort_values("Timestamp")
    
    # Generate overload indicator
    data['Overload'] = (data['Demand (MW)'] > firm_capacity)
    
    # Find contiguous segments
    segments = []
    i = 0
    N = len(data)
    
    # Track total energy for verification
    total_energy = 0.0
    
    while i < N:
        if data['Overload'].iloc[i]:
            # Start of an overload segment
            start_idx = i
            
            # Find end of segment
            j = i
            while j < N and data['Overload'].iloc[j]:
                j += 1
            
            end_idx = j
            
            # Extract segment data
            segment_data = data.iloc[start_idx:end_idx]
            
            # Calculate peak demand in this segment
            peak_demand = segment_data['Demand (MW)'].max()
            peak_idx = segment_data['Demand (MW)'].idxmax()
            peak_timestamp = data.loc[peak_idx, 'Timestamp']
            
            # Calculate required reduction
            required_reduction = peak_demand - firm_capacity
            
            # Extract time information
            start_timestamp = segment_data['Timestamp'].iloc[0]
            end_timestamp = segment_data['Timestamp'].iloc[-1]
            
            # Extract full date information
            start_date = start_timestamp.date()
            month = start_timestamp.month
            day = start_timestamp.day
            year = start_timestamp.year
            day_of_week = start_timestamp.dayofweek  # 0=Monday, 6=Sunday
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Calculate duration
            duration_periods = end_idx - start_idx
            duration_hours = duration_periods * delta_t
            
            # Calculate energy - this is the same calculation as in energy_peak_based
            energy_mwh = required_reduction * duration_hours  # peak above threshold × duration
            
            # Track total energy
            total_energy += energy_mwh
            
            # Create segment dictionary
            segment = {
                'start_idx': start_idx,
                'end_idx': end_idx,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
                'start_date': start_date,
                'peak_demand': peak_demand,
                'peak_timestamp': peak_timestamp,
                'firm_capacity': firm_capacity,
                'required_reduction': required_reduction,
                'duration_periods': duration_periods,
                'duration_hours': duration_hours,
                'month': month,
                'day': day,
                'year': year,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'energy_mwh': energy_mwh  # Same calculation as in energy_peak_based
            }
            
            segments.append(segment)
            
            # Move to the next segment
            i = j
        else:
            # Move to the next period
            i += 1
    
    # Verify total energy matches energy_peak_based calculation
    actual_energy = sum(segment['energy_mwh'] for segment in segments)
    if abs(actual_energy - total_energy) > 0.01:  # Allow small rounding differences
        logger.warning(f"Energy mismatch: expected {total_energy:.2f}, got {actual_energy:.2f}")
    else:
        logger.info(f"Total energy: {total_energy:.2f} MWh")
    
    return segments

def create_service_window_from_segment(
    segment: Dict
) -> Dict:
    """
    Create a service window from an overload segment.
    
    Args:
        segment: Overload segment dictionary
        
    Returns:
        Service window dictionary
    """
    # Extract time information
    start_hour = segment['start_timestamp'].hour
    start_minute = segment['start_timestamp'].minute
    end_hour = segment['end_timestamp'].hour
    end_minute = segment['end_timestamp'].minute
    
    # Format times
    start_time = f"{start_hour:02d}:{start_minute:02d}"
    
    # Handle end time (add 30 minutes to include the full period)
    # This is because end_timestamp is the start of the last period
    end_minutes = end_hour * 60 + end_minute + 30  # Add 30 minutes
    end_hour = end_minutes // 60
    end_minute = end_minutes % 60
    end_time = f"{end_hour:02d}:{end_minute:02d}"
    
    # Get day information
    day_of_week = segment['day_of_week']
    
    # Use the exact day of the week
    day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week]
    
    # IMPORTANT: For energy_peak_based matching, service_days must be just this specific day
    service_days = [day_name]
    
    # Format required reduction (ensure it's positive and reasonable)
    required_reduction = max(segment['required_reduction'], 0.1)
    
    # Create window name
    window_name = f"{day_name} {start_time}-{end_time}"
    
    # Create window with exact energy from this segment
    window = {
        "name": window_name,
        "start": start_time,
        "end": end_time,
        "service_days": service_days,
        "minimum_aggregate_asset_size": "0.100",
        "capacity_required": f"{required_reduction:.3f}",
        "duration_hours": segment['duration_hours'],
        "energy_mwh": segment['energy_mwh'],  # Save the exact energy from this segment
        "segment_date": segment['start_date']  # Store original segment date for grouping
    }
    
    return window

def generate_monthly_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate monthly service periods from service windows.
    Groups by month and includes only one instance of each window.
    
    Args:
        windows: List of service window dictionaries
        delta_t: Time step in hours (default: 0.5 for half-hourly data)
        
    Returns:
        List of service period dictionaries containing windows
    """
    if not windows:
        return []
    
    # Group windows by month
    windows_by_month = {}
    for window in windows:
        # Get the segment date
        segment_date = window.get('segment_date')
        if segment_date is None:
            continue
        
        month = segment_date.month
        year = segment_date.year
        
        key = (year, month)
        if key not in windows_by_month:
            windows_by_month[key] = []
        
        # Remove the segment_date field from the window
        window_copy = window.copy()
        if 'segment_date' in window_copy:
            del window_copy['segment_date']
        
        windows_by_month[key].append(window_copy)
    
    # Create service periods for each month
    service_periods = []
    for (year, month), month_windows in windows_by_month.items():
        # Get month details
        month_name = calendar.month_name[month]
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Format start and end dates
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{days_in_month:02d}"
        
        # Create service period
        service_period = {
            "name": month_name,
            "start": start_date,
            "end": end_date,
            "service_windows": month_windows
        }
        
        service_periods.append(service_period)
    
    return service_periods

def generate_daily_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate daily service periods from service windows.
    Creates a separate service period for each day with overloads.
    
    Args:
        windows: List of service window dictionaries
        delta_t: Time step in hours (default: 0.5 for half-hourly data)
        
    Returns:
        List of service period dictionaries containing windows
    """
    if not windows:
        return []
    
    # Group windows by date
    windows_by_date = {}
    for window in windows:
        # Get the segment date
        segment_date = window.get('segment_date')
        if segment_date is None:
            continue
        
        key = segment_date
        if key not in windows_by_date:
            windows_by_date[key] = []
        
        # Remove the segment_date field from the window
        window_copy = window.copy()
        if 'segment_date' in window_copy:
            del window_copy['segment_date']
        
        windows_by_date[key].append(window_copy)
    
    # Create service periods for each day
    service_periods = []
    for date, day_windows in windows_by_date.items():
        # Get day information
        year = date.year
        month = date.month
        day = date.day
        day_name = date.strftime("%A")
        month_name = calendar.month_name[month]
        
        # Format start and end dates (end is exclusive, so day+1)
        start_date = f"{year}-{month:02d}-{day:02d}"
        next_day = date + timedelta(days=1)
        end_date = next_day.strftime("%Y-%m-%d")
        
        # Create service period
        service_period = {
            "name": f"{month_name} {day} ({day_name})",
            "start": start_date,
            "end": end_date,
            "service_windows": day_windows
        }
        
        service_periods.append(service_period)
    
    return service_periods

def generate_service_windows_from_demand_data(
    df: pd.DataFrame,
    firm_capacity: float,
    procurement_window_size_minutes: int = 30,
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate service windows directly from demand data using energy_peak_based logic.
    
    Args:
        df: DataFrame with Timestamp and Demand (MW) columns
        firm_capacity: Firm capacity in MW
        procurement_window_size_minutes: Size of procurement windows in minutes
        delta_t: Time step in hours (default: 0.5 for half-hourly data)
        
    Returns:
        List of service window dictionaries
    """
    # Find overload segments directly using energy_peak_based logic
    segments = find_overload_segments(df, firm_capacity, delta_t)
    
    if not segments:
        logger.info(f"No overload segments found at firm capacity {firm_capacity} MW")
        return []
    
    # Create service windows directly from segments
    service_windows = [create_service_window_from_segment(segment) for segment in segments]
    
    # If procurement window size is smaller than delta_t, split windows
    if procurement_window_size_minutes < (delta_t * 60):
        procurement_windows = []
        for window in service_windows:
            split_windows = split_assessment_window_for_procurement(
                window, 
                int(delta_t * 60),  # Convert from hours to minutes
                procurement_window_size_minutes
            )
            procurement_windows.extend(split_windows)
        
        service_windows = procurement_windows
    
    return service_windows

def generate_competition_service_periods(
    df: pd.DataFrame,
    firm_capacity: float,
    risk_threshold: float = 0.05,  # Not used, kept for API compatibility
    assessment_window_size_minutes: int = 120,  # Not used for segment identification
    procurement_window_size_minutes: int = 30,
    disaggregate_days: bool = False,  # Not used, we always use specific days
    daily_service_periods: bool = False,
    group_by_day_type: bool = True,  # Not used, we always use specific segments
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate service periods directly matching energy_peak_based calculations.
    
    Args:
        df: DataFrame with Timestamp and Demand (MW) columns
        firm_capacity: Firm capacity in MW
        risk_threshold: Not used, kept for API compatibility
        assessment_window_size_minutes: Not used for segment identification
        procurement_window_size_minutes: Size of procurement windows in minutes
        disaggregate_days: Not used, we always use specific days
        daily_service_periods: Whether to create a service period per day instead of per month
        group_by_day_type: Not used, we always use specific segments
        delta_t: Time step in hours (default: 0.5 for half-hourly data)
        
    Returns:
        List of service period dictionaries
    """
    # Generate service windows directly from demand data
    service_windows = generate_service_windows_from_demand_data(
        df, 
        firm_capacity,
        procurement_window_size_minutes,
        delta_t
    )
    
    if not service_windows:
        return []
    
    # Create service periods based on daily or monthly grouping
    if daily_service_periods:
        return generate_daily_service_periods(service_windows, delta_t)
    else:
        return generate_monthly_service_periods(service_windows, delta_t)
