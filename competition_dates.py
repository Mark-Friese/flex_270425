"""
competition_dates.py - Utility functions for handling competition dates

This module provides functions for generating and formatting dates for flexibility competitions.
"""

import pandas as pd
from datetime import datetime, time, timedelta
from typing import Dict, Tuple, Optional, List

def get_first_weekday(year: int, month: int) -> datetime:
    """
    Get the first weekday (Mon-Fri) of a given month.
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        datetime: First weekday of the month
    """
    first_day = pd.Timestamp(year=year, month=month, day=1)
    
    # If it's a weekend, move to Monday
    while first_day.weekday() > 4:  # 5 = Saturday, 6 = Sunday
        first_day += pd.Timedelta(days=1)
        
    return first_day

def generate_competition_dates(service_window_date: pd.Timestamp) -> Dict[str, pd.Timestamp]:
    """
    Generate competition dates ensuring qualification period is exactly two weeks.
    
    Args:
        service_window_date: Date of the service window
        
    Returns:
        Dict containing all relevant dates
    """
    # Get month before service window
    dates_month = (service_window_date - pd.DateOffset(months=1))
    
    # Get first weekday for qualification open
    qual_open = get_first_weekday(dates_month.year, dates_month.month)
    qual_open = qual_open.replace(hour=12, minute=0)
    
    # Set qualification close to exactly two weeks later
    qual_close = qual_open + pd.Timedelta(days=14)  # Exactly 14 days
    qual_close = qual_close.replace(hour=8, minute=0)
    
    # Set bidding times on qualification close date
    bid_open = qual_close.replace(hour=8, minute=30)
    bid_close = qual_close.replace(hour=17, minute=0)
    
    return {
        'qualification_open': qual_open,
        'qualification_closed': qual_close,
        'bidding_open': bid_open,
        'bidding_closed': bid_close
    }

def validate_dates(dates: Dict[str, pd.Timestamp]) -> bool:
    """
    Validate that generated dates follow business rules.
    
    Args:
        dates: Dict of dates from generate_competition_dates
        
    Returns:
        bool: True if dates are valid
    """
    qual_open = dates['qualification_open']
    qual_close = dates['qualification_closed']
    bid_open = dates['bidding_open']
    bid_close = dates['bidding_closed']
    
    # Check qualification period is exactly two weeks
    qual_period = (qual_close.date() - qual_open.date()).days
    if qual_period != 14:
        return False
    
    # Check qualification open is at 12:00
    if qual_open.time() != time(12, 0):
        return False
    
    # Check qualification close is at 08:00
    if qual_close.time() != time(8, 0):
        return False
    
    # Check bidding times
    if bid_open.time() != time(8, 30):
        return False
    if bid_close.time() != time(17, 0):
        return False
    
    # Check bidding is on same day as qualification close
    if bid_open.date() != qual_close.date():
        return False
    
    return True

def format_dates_for_competition(dates: Dict[str, pd.Timestamp]) -> Dict[str, str]:
    """
    Format dates according to the competition schema format.
    
    Args:
        dates: Dict of dates from generate_competition_dates
        
    Returns:
        Dict with dates formatted as ISO strings
    """
    return {
        key: date.strftime('%Y-%m-%dT%H:%M:%SZ')
        for key, date in dates.items()
    }

def generate_dates_for_financial_year(financial_year: str) -> pd.DataFrame:
    """
    Generate all competition dates for a financial year.
    
    Args:
        financial_year: Financial year in format 'YYYY/YY' (e.g., '2025/26')
        
    Returns:
        DataFrame with dates for each month
    """
    if not isinstance(financial_year, str) or len(financial_year) != 7:
        raise ValueError("Financial year must be in format 'YYYY/YY'")
    
    start_year = int(financial_year[:4])
    dates_data = []
    
    # Generate dates for each month in the financial year
    for month in range(4, 13):  # April to December
        service_date = pd.Timestamp(year=start_year, month=month, day=1)
        dates = generate_competition_dates(service_date)
        dates['month'] = service_date.strftime('%B')
        dates['service_month'] = service_date
        dates_data.append(dates)
    
    for month in range(1, 4):  # January to March
        service_date = pd.Timestamp(year=start_year + 1, month=month, day=1)
        dates = generate_competition_dates(service_date)
        dates['month'] = service_date.strftime('%B')
        dates['service_month'] = service_date
        dates_data.append(dates)
    
    # Convert to DataFrame and sort
    df = pd.DataFrame(dates_data)
    df = df.sort_values('service_month')
    
    return df

def update_dates_in_dataframe(df: pd.DataFrame, target_year: Optional[int] = None, month_offset: int = 0) -> pd.DataFrame:
    """
    Update dates in a demand dataframe to a target year or by a month offset.
    Handles timezone-aware datetimes by converting to naive datetimes.
    
    Args:
        df: DataFrame with 'Timestamp' column
        target_year: Target year to move dates to (optional)
        month_offset: Number of months to shift dates (can be negative)
        
    Returns:
        DataFrame with updated timestamps
    """
    df = df.copy()
    
    # Ensure Timestamp is datetime, handling timezone-aware datetimes
    if not pd.api.types.is_datetime64_any_dtype(df["Timestamp"]):
        try:
            # First try with handling timezones by converting to UTC
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)
        except Exception:
            # If that fails, try without timezone info
            df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.tz_localize(None)
    elif df["Timestamp"].dt.tz is not None:
        # If already datetime but timezone-aware, convert to naive
        df["Timestamp"] = df["Timestamp"].dt.tz_localize(None)
    
    # Apply month offset if specified
    if month_offset != 0:
        df["Timestamp"] = df["Timestamp"] + pd.DateOffset(months=month_offset)
    
    # Change year if target_year is specified
    if target_year is not None:
        # Keep day, month, hour, minute, second but change year
        df["Timestamp"] = df["Timestamp"].apply(
            lambda x: x.replace(year=target_year)
        )
    
    # Update any date-derived columns if they exist
    if "Year" in df.columns:
        df["Year"] = df["Timestamp"].dt.year
    if "Month" in df.columns:
        df["Month"] = df["Timestamp"].dt.month
    if "Day" in df.columns:
        df["Day"] = df["Timestamp"].dt.day
    if "Hour" in df.columns:
        df["Hour"] = df["Timestamp"].dt.hour
    if "Minute" in df.columns:
        df["Minute"] = df["Timestamp"].dt.minute
    if "DayOfWeek" in df.columns:
        df["DayOfWeek"] = df["Timestamp"].dt.dayofweek
    if "IsWeekend" in df.columns:
        df["IsWeekend"] = df["Timestamp"].dt.dayofweek.isin([5, 6]).astype(int)
    
    return df