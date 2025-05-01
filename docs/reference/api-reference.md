# API Reference

This document provides a comprehensive reference for the key components, classes, and functions in the Flexibility Analysis System's API.

## Core Functions

### Firm Capacity Calculation

#### `energy_above_capacity`

```python
def energy_above_capacity(
    demand: np.ndarray, capacity: float, delta_t: float = 0.5
) -> float:
    """E(C) = ∑ max(demand - C,0) * Δt."""
    return np.sum(np.maximum(demand - capacity, 0.0)) * delta_t
```

**Parameters:**
- `demand`: NumPy array of demand values in MW
- `capacity`: Capacity threshold in MW
- `delta_t`: Time step in hours (default: 0.5 for half-hourly data)

**Returns:**
- Energy above capacity in MWh

#### `energy_peak_based`

```python
def energy_peak_based(
    demand: np.ndarray, capacity: float, delta_t: float = 0.5
) -> float:
    """
    E_peak(C): for each contiguous segment demand>C, 
    use (peak - C) * duration.
    """
    overload = demand > capacity
    total = 0.0
    i = 0
    N = len(demand)
    while i < N:
        if overload[i]:
            j = i
            while j < N and overload[j]:
                j += 1
            peak = demand[i:j].max()
            total += (peak - capacity) * (j - i) * delta_t
            i = j
        else:
            i += 1
    return total
```

**Parameters:**
- `demand`: NumPy array of demand values in MW
- `capacity`: Capacity threshold in MW
- `delta_t`: Time step in hours (default: 0.5 for half-hourly data)

**Returns:**
- Peak-based energy above capacity in MWh

#### `invert_capacity`

```python
def invert_capacity(
    func,           # either energy_above_capacity or energy_peak_based
    demand: np.ndarray,
    target: float,
    tol: float = 1e-3,
    maxiter: int = 50
) -> float:
    """Bisection search to find C so that func(demand,C)≈target."""
    low, high = 0.0, float(demand.max())
    for _ in range(maxiter):
        mid = 0.5 * (low + high)
        if func(demand, mid) > target:
            low = mid
        else:
            high = mid
        if high - low < tol:
            break
    return 0.5 * (low + high)
```

**Parameters:**
- `func`: Function to invert (either `energy_above_capacity` or `energy_peak_based`)
- `demand`: NumPy array of demand values in MW
- `target`: Target energy threshold in MWh
- `tol`: Tolerance for bisection search convergence
- `maxiter`: Maximum number of iterations for bisection search

**Returns:**
- Capacity value in MW that results in the target energy threshold

### Visualization

#### `plot_E_curve`

```python
def plot_E_curve(
    demand: np.ndarray,
    func,
    C_est: float,
    target: float,
    outpath: Path,
    title: str
):
    """Plot energy curve showing energy above capacity vs capacity."""
    Cs = np.linspace(0, demand.max(), 200)
    Es = [func(demand, c) for c in Cs]

    plt.figure(figsize=(8,5))
    plt.plot(Cs, Es, label="E(C)")
    plt.axhline(target, color="gray", linestyle="--")
    plt.axvline(C_est, color="gray", linestyle="--")
    plt.text(C_est, target, f" C≈{C_est:.2f} MW", va="bottom")
    plt.xlabel("Firm Capacity (MW)")
    plt.ylabel("Annual Energy Above Capacity (MWh)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()
```

**Parameters:**
- `demand`: NumPy array of demand values in MW
- `func`: Energy function to use (`energy_above_capacity` or `energy_peak_based`)
- `C_est`: Estimated capacity value to highlight on plot
- `target`: Target energy threshold to highlight on plot
- `outpath`: Path to save the plot
- `title`: Title for the plot

## Service Window Generation

### `find_overload_segments`

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
    # Implementation details...
```

**Parameters:**
- `df`: DataFrame with timestamp and demand data
- `firm_capacity`: Firm capacity threshold in MW
- `delta_t`: Time step in hours (default: 0.5 for half-hourly data)

**Returns:**
- List of dictionaries representing overload segments

### `create_service_window_from_segment`

```python
def create_service_window_from_segment(
    segment: Dict
) -> Dict:
    """Create a service window from an overload segment."""
    # Implementation details...
```

**Parameters:**
- `segment`: Dictionary representing an overload segment

**Returns:**
- Dictionary representing a service window

### `generate_monthly_service_periods`

```python
def generate_monthly_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate monthly service periods from service windows.
    Groups by month and includes only one instance of each window.
    """
    # Implementation details...
```

**Parameters:**
- `windows`: List of service window dictionaries
- `delta_t`: Time step in hours (default: 0.5)

**Returns:**
- List of service period dictionaries grouped by month

### `generate_daily_service_periods`

```python
def generate_daily_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate daily service periods from service windows.
    Creates a separate service period for each day with overloads.
    """
    # Implementation details...
```

**Parameters:**
- `windows`: List of service window dictionaries
- `delta_t`: Time step in hours (default: 0.5)

**Returns:**
- List of service period dictionaries grouped by day

## Competition Generation

### `create_competitions_from_df`

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

**Parameters:**
- `df`: DataFrame with demand data
- `firm_capacity`: Firm capacity value in MW
- `schema_path`: Optional path to competition schema
- `config_mode`: Configuration mode (REQUIRED_ONLY, STANDARD, or CUSTOM)
- `custom_fields`: Optional set of custom fields to include
- `risk_threshold`: Risk threshold (not used, kept for API compatibility)
- `assessment_window_size_minutes`: Size of assessment windows (not used for segment identification)
- `procurement_window_size_minutes`: Size of procurement windows in minutes
- `disaggregate_days`: Whether to disaggregate days (not used, kept for API compatibility)
- `daily_service_periods`: Whether to group by day instead of month
- `group_by_day_type`: Whether to group by day type (not used, kept for API compatibility)
- `financial_year`: Optional financial year for competition dates
- `delta_t`: Time step in hours (default: 0.5)

**Returns:**
- List of competition dictionaries

### `create_competition_template`

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
    # Implementation details...
```

**Parameters:**
- `selected_fields`: Dictionary mapping FieldLevel to sets of field names
- `substation_name`: Name of the substation
- `service_periods`: List of service period dictionaries
- `reference`: Competition reference string
- `nominal_voltage`: Optional nominal voltage value
- `financial_year`: Optional financial year string

**Returns:**
- Competition dictionary

### `sanitize_reference`

```python
def sanitize_reference(
    substation_name: str,
    licence_area: str = "SPEN",
    year: int = None,
    month: int = None,
    day: Optional[int] = None
) -> str:
    """Create a valid competition reference string."""
    # Implementation details...
```

**Parameters:**
- `substation_name`: Name of the substation
- `licence_area`: License area code (default: "SPEN")
- `year`: Optional year (defaults to current year)
- `month`: Optional month (defaults to current month)
- `day`: Optional day of month

**Returns:**
- Valid competition reference string

### `validate_competitions_with_schema`

```python
def validate_competitions_with_schema(
    competitions: List[Dict],
    schema_path: str
) -> List[Dict]:
    """Validate competitions against the JSON schema."""
    # Implementation details...
```

**Parameters:**
- `competitions`: List of competition dictionaries
- `schema_path`: Path to the competition schema

**Returns:**
- List of validation errors (empty if all valid)

## Configuration Classes

### `ConfigMode`

```python
class ConfigMode(Enum):
    REQUIRED_ONLY = "required_only"
    STANDARD = "standard"
    CUSTOM = "custom"
```

**Values:**
- `REQUIRED_ONLY`: Include only required fields
- `STANDARD`: Include commonly used optional fields
- `CUSTOM`: Include custom-specified optional fields

### `FieldLevel`

```python
class FieldLevel(Enum):
    ROOT = "root"
    SERVICE_WINDOW = "service_window"
```

**Values:**
- `ROOT`: Root-level fields in a competition
- `SERVICE_WINDOW`: Service window-level fields

### `FieldSelector`

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

**Methods:**
- `get_fields_for_mode`: Get fields to include based on the configuration mode
- `validate_field_placement`: Validate that fields are properly categorized
- `get_field_description`: Get the description for a field
- `get_field_level`: Get the level for a field
- `generate_ui_template`: Generate a template for UI configuration

## Utility Functions

### `load_config`

```python
def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)
```

**Parameters:**
- `path`: Path to the configuration file

**Returns:**
- Configuration dictionary

### `ensure_dir`

```python
def ensure_dir(path: Path) -> None:
    """Ensure directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
```

**Parameters:**
- `path`: Directory path to ensure exists

### `load_site_specific_targets`

```python
def load_site_specific_targets(targets_file: Path) -> Dict[str, float]:
    """
    Load site-specific MWh targets from a CSV file.
    
    The CSV should have at least two columns: 'site_name' and 'target_mwh'
    """
    # Implementation details...
```

**Parameters:**
- `targets_file`: Path to CSV file with site-specific targets

**Returns:**
- Dictionary mapping site names to target values

## Parquet Processing

### `process_network_groups_in_parquet`

```python
def process_network_groups_in_parquet(
    parquet_path: str,
    cfg: dict,
    process_function: Callable,
    network_groups: Optional[List[str]] = None,
    max_workers: int = 1,
    skip_existing: bool = True,
    **kwargs
) -> Dict:
    """
    Process all network groups (or specified ones) in parallel.
    """
    # Implementation details...
```

**Parameters:**
- `parquet_path`: Path to the parquet file
- `cfg`: Configuration dictionary
- `process_function`: Function to call with each group
- `network_groups`: Optional list of specific groups to process
- `max_workers`: Maximum number of parallel workers
- `skip_existing`: Skip groups that already have results
- `**kwargs`: Additional arguments to pass to the process function

**Returns:**
- Dictionary with processing results for all groups

### `get_unique_network_groups`

```python
def get_unique_network_groups(parquet_path: str) -> List[str]:
    """
    Extract all unique network group names from a parquet file.
    """
    # Implementation details...
```

**Parameters:**
- `parquet_path`: Path to the parquet file

**Returns:**
- List of unique network group names

### `load_network_group_data`

```python
def load_network_group_data(
    parquet_path: str,
    network_group: str,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load data for a specific network group from parquet file.
    """
    # Implementation details...
```

**Parameters:**
- `parquet_path`: Path to the parquet file
- `network_group`: Network group name to filter
- `columns`: Optional list of columns to load

**Returns:**
- DataFrame with data for the specified network group

## Desktop Application API

### `FlexibilityAnalysisAPI`

```python
class FlexibilityAnalysisAPI:
    """API class to handle interaction between web UI and Python backend"""
    
    def __init__(self):
        self.config = None
        self.base_dir = Path(__file__).resolve().parent
        self.default_config_path = self.base_dir / "config.yaml"
        self.output_dir = self.base_dir / "output"
```

**Methods:**
- `select_config_file`: Open a file dialog to select a configuration file
- `load_config`: Load application configuration file
- `get_substations`: Get list of available substations from config
- `select_output_directory`: Open a directory dialog to select output directory
- `run_analysis`: Run the flexibility analysis for a substation
- `get_results`: Get analysis results for a substation
- `get_all_results`: Get a summary of all processed substations
- `save_map_data`: Save map data to the substation_coordinates.json file
- `load_map_data`: Load map data from the substation_coordinates.json file
- `match_substations_to_coordinates`: Match substations in config with coordinates in the map data
- `generate_default_map_data`: Generate default map data based on current config