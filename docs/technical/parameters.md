# Dynamic and Static Parameters in Service Windows and Competitions

This document outlines which parameters are dynamically calculated and which are static in the service window and competition generation processes. Understanding these parameters is crucial for configuring the system and interpreting its outputs.

## 1. Service Window Parameters

Service windows are time periods when flexibility services may be needed. They are generated from demand data segments where demand exceeds firm capacity.

### 1.1 Dynamic Parameters (Calculated from Data)

| Parameter | Description | Calculation Method |
|-----------|-------------|-------------------|
| `name` | Window name | Generated from day and time: `"{day_name} {start_time}-{end_time}"` |
| `start` | Start time (HH:MM) | Extracted directly from the start of the overload segment |
| `end` | End time (HH:MM) | Extracted from the end of the overload segment (with added time to include full period) |
| `service_days` | Days when service applies | Extracted from the segment date's day of week (e.g., "Monday") |
| `capacity_required` | MW capacity needed | Calculated as `peak_demand - firm_capacity` for the segment |
| `energy_mwh` | Energy in MWh | Calculated as `(peak_demand - firm_capacity) * duration_hours` |
| `duration_hours` | Duration in hours | Calculated from segment duration |

From `service_windows.py`:

```python
def create_service_window_from_segment(segment: Dict) -> Dict:
    """Create a service window from an overload segment."""
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
    
    # Format required reduction
    required_reduction = max(segment['required_reduction'], 0.1)
    
    # Create window name
    window_name = f"{day_name} {start_time}-{end_time}"
    
    window = {
        "name": window_name,
        "start": start_time,
        "end": end_time,
        "service_days": [day_name],
        "minimum_aggregate_asset_size": "0.100",
        "capacity_required": f"{required_reduction:.3f}",
        "duration_hours": segment['duration_hours'],
        "energy_mwh": segment['energy_mwh'],
        "segment_date": segment['start_date']
    }
    
    return window
```

### 1.2 Static Parameters (Fixed Values)

| Parameter | Description | Default Value | Configuration |
|-----------|-------------|--------------|--------------|
| `minimum_aggregate_asset_size` | Minimum aggregate asset size in MW | "0.100" | Hard-coded in service window creation |
| `procurement_window_size_minutes` | Size of procurement windows | 30 minutes | Configurable via `competitions.procurement_window_size_minutes` |

## 2. Service Period Parameters

Service periods group service windows, typically by month or by day.

### 2.1 Dynamic Parameters (Calculated from Data)

| Parameter | Description | Calculation Method |
|-----------|-------------|-------------------|
| `name` | Period name | For monthly: month name (e.g., "January") <br> For daily: `"{month_name} {day} ({day_name})"` |
| `start` | Start date (YYYY-MM-DD) | For monthly: first day of month <br> For daily: date of the service window |
| `end` | End date (YYYY-MM-DD) | For monthly: last day of month <br> For daily: next day after the service window |
| `service_windows` | List of service windows | Windows that belong to this period based on their date |

From `service_windows.py`:

```python
def generate_monthly_service_periods(windows: List[Dict], delta_t: float = 0.5) -> List[Dict]:
    """Generate monthly service periods from service windows."""
    # Group windows by month
    windows_by_month = {}
    for window in windows:
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

### 2.2 Static Parameters (Fixed Values)

| Parameter | Description | Default Value | Configuration |
|-----------|-------------|--------------|--------------|
| `daily_service_periods` | Whether to group by day instead of month | false | Configurable via `competitions.daily_service_periods` |

## 3. Competition Parameters

Competitions contain service periods and include additional parameters for scheduling and identification.

### 3.1 Dynamic Parameters (Calculated from Data)

| Parameter | Description | Calculation Method |
|-----------|-------------|-------------------|
| `reference` | Competition reference | Generated from date and substation: `"T{YY}{MM}_{licence_area}_{sanitized_name}"` |
| `name` | Competition name | Generated from substation and month: `"{substation_name.upper()} {month_name} {year}"` |
| `open` | Bidding open datetime | Generated based on service period start date |
| `closed` | Bidding closed datetime | Generated based on service period start date |
| `qualification_open` | Qualification open datetime | Generated based on service period start date |
| `qualification_closed` | Qualification closed datetime | Generated based on service period start date |
| `boundary.area_references` | Area references | Uses substation name: `[substation_name.upper()]` |
| `service_periods` | List of service periods | Service periods generated from demand data |

From `competition_builder.py`:

```python
def create_competition_template(
    selected_fields: Dict[FieldLevel, Set[str]],
    substation_name: str,
    service_periods: List[Dict],
    reference: str,
    nominal_voltage: Optional[float] = None,
    financial_year: Optional[str] = None
) -> Dict:
    # Get period dates from the collection of service periods
    period_starts = [pd.Timestamp(period['start']) for period in service_periods]
    period_ends = [pd.Timestamp(period['end']) for period in service_periods]
    
    period_start = min(period_starts)
    period_end = max(period_ends)

    # Generate competition dates
    if financial_year:
        # Use financial year dates if specified
        fy_dates = generate_dates_for_financial_year(financial_year)
        month_dates = fy_dates[fy_dates['month'] == period_start.strftime('%B')]
        competition_dates = {
            'qualification_open': month_dates['qualification_open'].iloc[0],
            'qualification_closed': month_dates['qualification_closed'].iloc[0],
            'bidding_open': month_dates['bidding_open'].iloc[0],
            'bidding_closed': month_dates['bidding_closed'].iloc[0]
        }
    else:
        # Generate dates based on service period start
        competition_dates = generate_competition_dates(period_start)
    
    # Format dates for competition
    formatted_dates = format_dates_for_competition(competition_dates)
    
    # Create a name for the competition that includes the month
    month_name = calendar.month_name[period_start.month]
    competition_name = f"{substation_name.upper()} {month_name} {period_start.year}"
    
    # Create competition with required fields
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
            "postcodes": []
        },
        "need_type": "Pre Fault",
        "type": "Utilisation",
        "need_direction": "Deficit",
        "power_type": "Active Power",
        "service_periods": service_periods
    }
    
    # Additional fields based on configuration...
    
    return competition
```

### 3.2 Static Parameters (Fixed Values)

| Parameter | Description | Default Value | Configuration |
|-----------|-------------|--------------|--------------|
| `area_buffer` | Area buffer in km | "0.100" | Hard-coded in competition template |
| `need_type` | Type of network need | "Pre Fault" | Hard-coded in competition template |
| `type` | Competition type | "Utilisation" | Hard-coded in competition template |
| `need_direction` | Direction of need | "Deficit" | Hard-coded in competition template |
| `power_type` | Type of power | "Active Power" | Hard-coded in competition template |
| `boundary.postcodes` | List of postcodes | [] (empty array) | Hard-coded in competition template |
| `financial_year` | Financial year for scheduling | null | Configurable via `competitions.financial_year` |

## 4. Optional Fields

The system supports adding optional fields to competitions based on configuration. These are managed through the `FieldSelector` class in `competition_config.py`.

### 4.1 Root Level Optional Fields

| Field | Description | Default Value | Configuration Mode |
|-------|-------------|--------------|-------------------|
| `contact` | Email for communications | "flexibility@example.com" | `STANDARD` or `CUSTOM` |
| `archive_on` | Archive date | 7 days after bidding closes | `STANDARD` or `CUSTOM` |
| `dps_record_reference` | DPS record reference | f"flex_{reference.lower()}" | `STANDARD` or `CUSTOM` |
| `product_type` | Product type | "Scheduled Utilisation" | `STANDARD` or `CUSTOM` |
| `minimum_connection_voltage` | Min voltage in KV | Based on nominal_voltage or "0.24" | `REQUIRED_ONLY`, `STANDARD`, or `CUSTOM` |
| `maximum_connection_voltage` | Max voltage in KV | Based on nominal_voltage or "33" | `REQUIRED_ONLY`, `STANDARD`, or `CUSTOM` |
| `minimum_budget` | Min budget in £ | "5000.00" | `CUSTOM` |
| `maximum_budget` | Max budget in £ | "10000.00" | `CUSTOM` |
| `availability_guide_price` | Guide price for availability | "10.00" | `CUSTOM` |
| `utilisation_guide_price` | Guide price for utilisation | "240" | `CUSTOM` |
| `service_fee` | Annual fee for capacity | "9.45" | `CUSTOM` |
| `pricing_type` | Price determination method | "auction" | `CUSTOM` |

### 4.2 Service Window Level Optional Fields

| Field | Description | Default Value | Configuration Mode |
|-------|-------------|--------------|-------------------|
| `public_holiday_handling` | Holiday designation | Not set by default | `STANDARD` or `CUSTOM` |
| `minimum_run_time` | Min run time for assets | Not set by default | `CUSTOM` |
| `required_response_time` | Response time for utilisation | Not set by default | `CUSTOM` |
| `dispatch_estimate` | Estimated dispatch events | Not set by default | `CUSTOM` |
| `dispatch_duration` | Estimated dispatch duration | Not set by default | `CUSTOM` |

### 4.3 Configuration Modes

| Mode | Description |
|------|-------------|
| `REQUIRED_ONLY` | Only voltage requirements are included |
| `STANDARD` | Commonly used fields are included (`product_type`, `minimum_connection_voltage`, `maximum_connection_voltage`, `dps_record_reference`, `public_holiday_handling`) |
| `CUSTOM` | User-specified fields from available options |

## 5. Configuration Parameters

The main configuration parameters that control service window and competition generation are defined in `config.yaml`:

```yaml
firm_capacity:
  target_mwh: 300.0  # Target energy threshold in MWh
  tolerance: 0.01    # Tolerance for bisection search

competitions:
  procurement_window_size_minutes: 30  # Size of procurement windows
  disaggregate_days: true  # Whether to disaggregate days into separate windows
  daily_service_periods: true  # Whether to use daily instead of monthly periods
  financial_year: "2025/26"  # Financial year for competition dates
```

### 5.1 Core Configuration Options

| Parameter | Description | Default | Impact |
|-----------|-------------|---------|--------|
| `firm_capacity.target_mwh` | Target energy threshold in MWh | Varies | Determines the firm capacity value through inversion |
| `firm_capacity.tolerance` | Tolerance for bisection search | 0.01 | Controls the precision of firm capacity calculation |
| `competitions.procurement_window_size_minutes` | Size of service windows | 30 | Controls the granularity of service windows |
| `competitions.daily_service_periods` | Group by day instead of month | false | Changes how service windows are grouped |
| `competitions.financial_year` | Financial year for dates | null | Controls competition date generation |

Site-specific target MWh values can also be provided through a CSV file with `site_name` and `target_mwh` columns, which will override the default target from the configuration.

## 6. Date Manipulation Parameters

The system provides options to update the dates in the demand data:

| Parameter | Description | Default | Configuration |
|-----------|-------------|---------|--------------|
| `target_year` | Year to use for dates | null | Command-line parameter `--year` |

From `competition_dates.py`:

```python
def update_dates_in_dataframe(
    df: pd.DataFrame, 
    target_year: Optional[int] = None, 
    month_offset: int = 0
) -> pd.DataFrame:
    """
    Update dates in a demand dataframe to a target year or by a month offset.
    """
    # ...implementation details...
```

This allows simulation of future scenarios using historical demand data by shifting dates to a specific target year.