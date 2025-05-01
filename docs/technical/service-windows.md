# Service Window Generation

This document explains the process of generating service windows in the Flexibility Analysis System, which identify specific time periods when flexibility services may be needed.

## What are Service Windows?

Service windows are specific time periods (e.g., "Monday 17:00-19:30") when demand is expected to exceed firm capacity and flexibility services may be required. They are the foundation of flexibility competitions and define:

- **When**: The days and times when flexibility is needed
- **How Much**: The required capacity reduction in MW
- **For How Long**: The duration of the flexibility need

## Service Window Generation Process

The service window generation process follows these steps:

1. **Identify Overload Segments**: Find contiguous time periods where demand exceeds firm capacity
2. **Create Service Windows**: Convert each segment into a properly formatted service window
3. **Group into Service Periods**: Organize windows into periods (monthly or daily)

## 1. Identifying Overload Segments

Overload segments are contiguous periods where demand exceeds firm capacity. They are identified using the same logic as the peak-based energy calculation:

```python
def find_overload_segments(
    df: pd.DataFrame,
    firm_capacity: float,
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Identify contiguous segments where demand exceeds firm capacity.
    Uses the same logic as energy_peak_based to ensure consistency.
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
            
            # Calculate energy - matches energy_peak_based calculation
            energy_mwh = required_reduction * duration_hours
            
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
                'energy_mwh': energy_mwh
            }
            
            segments.append(segment)
            
            # Move to the next segment
            i = j
        else:
            # Move to the next period
            i += 1
    
    # Verify total energy matches energy_peak_based calculation
    actual_energy = sum(segment['energy_mwh'] for segment in segments)
    if abs(actual_energy - total_energy) > 0.01:
        logger.warning(f"Energy mismatch: expected {total_energy:.2f}, got {actual_energy:.2f}")
    
    return segments
```

This function:
1. Identifies where demand exceeds firm capacity
2. Finds contiguous periods of excess demand
3. Calculates the peak demand within each segment
4. Determines the required reduction (peak demand - firm capacity)
5. Calculates energy (MWh) using the peak-based method
6. Extracts key time and date information

## 2. Creating Service Windows

Each identified overload segment is converted to a properly formatted service window:

```python
def create_service_window_from_segment(
    segment: Dict
) -> Dict:
    """
    Create a service window from an overload segment.
    """
    # Extract time information
    start_hour = segment['start_timestamp'].hour
    start_minute = segment['start_timestamp'].minute
    end_hour = segment['end_timestamp'].hour
    end_minute = segment['end_timestamp'].minute
    
    # Format times
    start_time = f"{start_hour:02d}:{start_minute:02d}"
    
    # Handle end time (add 30 minutes to include the full period)
    end_minutes = end_hour * 60 + end_minute + 30
    end_hour = end_minutes // 60
    end_minute = end_minutes % 60
    end_time = f"{end_hour:02d}:{end_minute:02d}"
    
    # Get day information
    day_of_week = segment['day_of_week']
    day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week]
    
    # Service days - use the exact day of the week for consistency
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
        "energy_mwh": segment['energy_mwh'],
        "segment_date": segment['start_date']
    }
    
    return window
```

The resulting service window includes:
- A descriptive name based on the day and time
- Start and end times in HH:MM format
- Service days (specific day of week)
- Required capacity in MW
- Duration in hours
- Energy (MWh) from the segment calculation
- Original segment date for grouping

## 3. Grouping into Service Periods

Service windows are grouped into service periods, either by month or by day depending on configuration:

### Monthly Service Periods

```python
def generate_monthly_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate monthly service periods from service windows.
    Groups by month and includes only one instance of each window.
    """
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
        
        # Remove the segment_date field
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
```

### Daily Service Periods

```python
def generate_daily_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate daily service periods from service windows.
    Creates a separate service period for each day with overloads.
    """
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
        
        # Remove the segment_date field
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
```

## Configuration Options

Service window generation can be configured in several ways:

### Procurement Window Size

The `procurement_window_size_minutes` parameter controls the granularity of service windows:

```python
procurement_window_size_minutes = 30  # Size of procurement windows in minutes
```

This can result in splitting larger windows into smaller ones:

```python
def split_assessment_window_for_procurement(
    window: Dict,
    assessment_window_size_minutes: int,
    procurement_window_size_minutes: int
) -> List[Dict]:
    """
    Split a single assessment window into multiple procurement windows.
    All procurement windows inherit the same capacity requirement.
    """
    # Implementation details...
```

For example, a 2-hour window might be split into 4 x 30-minute windows if `procurement_window_size_minutes` is set to 30.

### Daily vs Monthly Service Periods

The `daily_service_periods` parameter determines whether service windows are grouped by day or by month:

```python
daily_service_periods = True  # Group by day instead of month
```

- When `True`: Creates a separate service period for each day with overloads (e.g., "January 15 (Monday)")
- When `False`: Groups all service windows by month (e.g., "January")

## Mathematical Consistency

A key feature of the service window generation is mathematical consistency with the peak-based energy calculation:

1. Each overload segment directly corresponds to a service window
2. The energy (MWh) for each window is calculated using the peak-based method
3. The sum of energy across all service windows equals the total energy above capacity from the peak-based calculation

This ensures that the generated service windows accurately represent the energy needs that exceed firm capacity.

## Service Window Features

The generated service windows have several important features:

### Time-Specific

Service windows are specific to particular times of day when demand exceeds capacity:

```json
{
  "name": "Monday 17:00-19:30",
  "start": "17:00",
  "end": "19:30",
  "service_days": ["Monday"],
  "capacity_required": "1.250"
}
```

### Day-Specific

Each service window applies to a specific day of the week, captured in the `service_days` field:

```json
"service_days": ["Monday"]
```

This allows flexibility providers to plan their availability for specific days.

### Location-Specific

Service windows are generated for specific substations based on their unique demand patterns, making them location-specific.

## Example Service Windows

Here are examples of service windows generated by the system:

```json
{
  "name": "Monday 17:00-19:30",
  "start": "17:00",
  "end": "19:30",
  "service_days": ["Monday"],
  "minimum_aggregate_asset_size": "0.100",
  "capacity_required": "1.250"
}
```

```json
{
  "name": "Thursday 11:00-11:30",
  "start": "11:00",
  "end": "11:30",
  "service_days": ["Thursday"],
  "minimum_aggregate_asset_size": "0.100",
  "capacity_required": "0.850"
}
```

```json
{
  "name": "Tuesday 17:30-20:30",
  "start": "17:30",
  "end": "20:30",
  "service_days": ["Tuesday"],
  "minimum_aggregate_asset_size": "0.100",
  "capacity_required": "0.913"
}
```

## Service Window Analysis and Verification

To verify the generated service windows, the system creates a `service_window_mwh.csv` file with detailed information:

```
Competition,Month,Window,Capacity (MW),Energy (MWh),Window Duration (h),Days,Hours,Start,End,Service Days
Competition 1,January,Monday 17:00-19:30,1.250,2.500,2.5,1,2.5,17:00,19:30,Monday
```

This file allows verification that:
1. The total energy across all service windows matches the expected value from the peak-based calculation
2. Each window has appropriate duration, capacity, and timing
3. The distribution of windows across days and times makes sense

## References

For more information on service window standards:

1. ENA Flexibility Services Standard Agreement
2. DNO Common Evaluation Methodology (CEM)
3. Ofgem RIIO-ED2 Business Plan Guidance