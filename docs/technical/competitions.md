# Competition Generation

This document explains how the Flexibility Analysis System generates standardized flexibility competitions based on service windows and firm capacity analysis.

## What are Flexibility Competitions?

Flexibility competitions are standardized specifications for procuring flexibility services in power networks. They define:

- **When** flexibility is needed (service periods and windows)
- **Where** it is needed (network area)
- **How much** is required (capacity in MW)
- **Terms and conditions** for providing the service

## Competition Generation Process

The competition generation process follows these steps:

1. **Analyze Demand Data**: Calculate firm capacity using peak-based method
2. **Generate Service Windows**: Identify times when demand exceeds firm capacity
3. **Group into Service Periods**: Organize windows into periods (monthly or daily)
4. **Create Competition Templates**: Construct competitions from service periods
5. **Add Optional Fields**: Customize competitions based on configuration
6. **Validate**: Ensure competitions conform to the schema

## 1. Creating Competition Templates

Each competition is generated from service periods using the `create_competition_template` function:

```python
def create_competition_template(
    selected_fields: Dict[FieldLevel, Set[str]],
    substation_name: str,
    service_periods: List[Dict],
    reference: str,
    nominal_voltage: Optional[float] = None,
    financial_year: Optional[str] = None
) -> Dict:
    """Create a competition template with properly categorized fields."""
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
    
    # Add optional fields based on configuration
    # ... (additional fields)
    
    return competition
```

This function:
1. Derives dates for the competition from service periods
2. Generates appropriate scheduling dates for qualification and bidding
3. Creates a descriptive name for the competition
4. Constructs the competition with required fields
5. Adds optional fields based on configuration

## 2. Competition Reference Generation

Each competition needs a unique reference that follows a specific pattern:

```python
def sanitize_reference(
    substation_name: str, 
    licence_area: str = "SPEN", 
    year: int = None, 
    month: int = None, 
    day: Optional[int] = None
) -> str:
    """Create a valid competition reference string."""
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
```

Examples of generated references:
- `T2504_SPEN_Monktonhall` (April 2025 for Monktonhall)
- `T2505_SPEN_Substation2` (May 2025 for Substation2)

## 3. Competition Date Generation

Competition dates are generated to ensure proper scheduling:

```python
def generate_competition_dates(
    service_window_date: pd.Timestamp
) -> Dict[str, pd.Timestamp]:
    """Generate competition dates ensuring qualification period is exactly two weeks."""
    # Get month before service window
    dates_month = (service_window_date - pd.DateOffset(months=1))
    
    # Get first weekday for qualification open
    qual_open = get_first_weekday(dates_month.year, dates_month.month)
    qual_open = qual_open.replace(hour=12, minute=0)
    
    # Set qualification close to exactly two weeks later
    qual_close = qual_open + pd.Timedelta(days=14)
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
```

The dates follow these rules:
1. Qualification opens on the first weekday of the month before the service period
2. Qualification period is exactly 14 days
3. Bidding opens and closes on the same day as qualification closes
4. Specific times are set for each stage of the process

Alternatively, dates can be generated based on a financial year schedule:

```python
def generate_dates_for_financial_year(
    financial_year: str
) -> pd.DataFrame:
    """Generate all competition dates for a financial year."""
    # Implementation details...
```

This allows alignment with financial year planning cycles.

## 4. Adding Optional Fields

Competitions can include various optional fields based on configuration:

```python
class FieldSelector:
    """Enhanced field selector with support for field categorization."""
    
    def get_fields_for_mode(
        self,
        mode: ConfigMode,
        custom_fields: Optional[Set[str]] = None
    ) -> Dict[FieldLevel, Set[str]]:
        """Get the set of fields to include based on the configuration mode."""
        # Implementation details...
```

The system supports three configuration modes:
- `REQUIRED_ONLY`: Only includes voltage requirements
- `STANDARD`: Includes commonly used optional fields
- `CUSTOM`: Allows specification of exactly which optional fields to include

Optional fields are categorized by level:
- Root level (competition-wide fields)
- Service window level (fields specific to service windows)

## 5. Creating Multiple Competitions

For a given substation, multiple competitions may be created based on service periods:

```python
def create_competitions_from_df(
    df: pd.DataFrame,
    firm_capacity: float,
    schema_path: Optional[str] = None,
    config_mode: ConfigMode = ConfigMode.STANDARD,
    custom_fields: Optional[Set[str]] = None,
    risk_threshold: float = 0.05,
    assessment_window_size_minutes: int = 120,
    procurement_window_size_minutes: int = 30,
    disaggregate_days: bool = False,
    daily_service_periods: bool = False,
    group_by_day_type: bool = True,
    financial_year: Optional[str] = None,
    delta_t: float = 0.5
) -> List[Dict]:
    """Creates competitions based on the demand data and firm capacity."""
    # Implementation details...
```

This function:
1. Processes demand data to identify service windows
2. Groups windows into service periods (monthly or daily)
3. Creates a competition for each month with service periods
4. Adds optional fields based on configuration
5. Optionally validates competitions against a schema

## 6. Validation Against Schema

The system can validate generated competitions against a JSON schema:

```python
def validate_competitions_with_schema(
    competitions: List[Dict], 
    schema_path: str
) -> List[Dict]:
    """Validate competitions against the JSON schema."""
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
```

This validation ensures that generated competitions comply with the required schema.

## Example Competition Structure

A generated competition has the following structure:

```json
{
  "reference": "T2504_SPEN_Monktonhall",
  "name": "MONKTONHALL April 2025",
  "open": "2025-03-10T08:30:00Z",
  "closed": "2025-03-10T17:00:00Z",
  "area_buffer": "0.100",
  "qualification_open": "2025-02-24T12:00:00Z",
  "qualification_closed": "2025-03-10T08:00:00Z",
  "boundary": {
    "area_references": ["MONKTONHALL"],
    "postcodes": []
  },
  "need_type": "Pre Fault",
  "type": "Utilisation",
  "need_direction": "Deficit",
  "power_type": "Active Power",
  "service_periods": [
    {
      "name": "April",
      "start": "2025-04-01",
      "end": "2025-04-30",
      "service_windows": [
        {
          "name": "Monday 17:00-19:30",
          "start": "17:00",
          "end": "19:30",
          "service_days": ["Monday"],
          "minimum_aggregate_asset_size": "0.100",
          "capacity_required": "1.250"
        },
        {
          "name": "Thursday 11:00-11:30",
          "start": "11:00",
          "end": "11:30",
          "service_days": ["Thursday"],
          "minimum_aggregate_asset_size": "0.100",
          "capacity_required": "0.850"
        }
      ]
    }
  ]
}
```

## Additional Features

### Target Year Specification

The system allows specifying a target year for competitions, which shifts dates in the demand data:

```python
def update_dates_in_dataframe(
    df: pd.DataFrame,
    target_year: Optional[int] = None,
    month_offset: int = 0
) -> pd.DataFrame:
    """Update dates in a demand dataframe to a target year or by a month offset."""
    # Implementation details...
```

This enables:
- Simulating future scenarios using historical demand data
- Creating competitions for specific planning years
- Aligning competition dates with financial years

### Saving and Exporting

Generated competitions are saved to a JSON file:

```python
def save_competitions_to_json(
    competitions: List[Dict], 
    output_path: str
):
    """Save competitions to JSON file."""
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
```

This creates a clean JSON file with all required competition fields.

## Configuration Options

Competition generation can be configured in several ways:

```yaml
competitions:
  procurement_window_size_minutes: 30  # Size of procurement windows
  disaggregate_days: true  # Whether to disaggregate days
  daily_service_periods: true  # Group by day instead of month
  financial_year: "2025/26"  # Financial year for dates
```

### Procurement Window Size

The `procurement_window_size_minutes` parameter controls the granularity of service windows:

- Smaller values (e.g., 30 minutes) create more, shorter windows
- Larger values (e.g., 120 minutes) create fewer, longer windows

### Service Period Grouping

The `daily_service_periods` parameter determines whether service windows are grouped by day or by month:

- When `True`: Creates a separate service period for each day with overloads
- When `False`: Groups all service windows by month

### Financial Year Scheduling

The `financial_year` parameter allows alignment with financial year planning cycles:

- Format: "YYYY/YY" (e.g., "2025/26")
- Generates appropriate dates for all months in the financial year

## Practical Usage

Generating competitions from the command line:

```bash
python firm_capacity_with_competitions.py --competitions --year 2025
```

With specific targets:

```bash
python firm_capacity_with_competitions.py --competitions --targets data/samples/site_targets.csv
```

Processing multiple substations from parquet data:

```bash
python firm_capacity_with_competitions.py --competitions --parquet data/raw/substations.parquet
```

## References

For more information on flexibility competitions:

1. ENA Flexibility Services Standard Agreement
2. DNO Common Evaluation Methodology (CEM)
3. Piclo Flex competition specifications