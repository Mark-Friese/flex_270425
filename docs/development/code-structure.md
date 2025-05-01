# Code Structure

This document provides an overview of the Flexibility Analysis System's code structure to help developers understand and contribute to the project.

## Directory Structure

The project is organized into the following directory structure:

```
firm_capacity_analysis/
├── app.py                      # Desktop application
├── build.py                    # Build script for desktop app
├── competition_builder.py      # Core competition creation
├── competition_config.py       # Competition configuration
├── competition_dates.py        # Date utilities
├── config.yaml                 # Default configuration
├── config_with_competitions.yaml # Configuration with competitions
├── data/                       # Data directory
│   ├── raw/                    # Raw data files
│   │   └── *.parquet           # Parquet files
│   └── samples/                # Sample data files
│       └── *.csv               # CSV files
├── docs/                       # Documentation
├── firm_capacity_with_competitions.py # Main script
├── mkdocs.yml                  # MkDocs configuration
├── output/                     # Output directory
├── requirements.txt            # Core requirements
├── requirements-*.txt          # Additional requirements
├── RUN_COMMANDS.md             # Command reference
├── service_windows.py          # Service window generation
├── src/                        # Core modules
│   ├── calculations.py         # Mathematical calculations
│   ├── main.py                 # Original main script
│   ├── parquet_processor.py    # Parquet file handling
│   ├── plotting.py             # Visualization
│   └── utils.py                # Utility functions
├── tests/                      # Test modules
│   ├── conftest.py             # Pytest fixtures
│   ├── test_*.py               # Test files
│   └── *.py                    # Test utilities
└── ui/                         # User interface files
    ├── css/                    # CSS styles
    ├── index.html              # Main HTML file
    └── js/                     # JavaScript files
```

## Key Modules

### Core Calculation Modules

- **`src/calculations.py`**: Contains the mathematical functions for calculating energy above capacity and firm capacity inversion
- **`src/plotting.py`**: Handles visualization of energy curves and firm capacity
- **`src/utils.py`**: Provides utility functions for loading configuration, ensuring directories exist, etc.

### Main Scripts

- **`src/main.py`**: Original firm capacity analysis script
- **`firm_capacity_with_competitions.py`**: Enhanced script that also generates competitions

### Competition Generation Modules

- **`competition_builder.py`**: Core logic for creating competitions from firm capacity analysis
- **`competition_config.py`**: Configuration for competition generation, including field selection
- **`competition_dates.py`**: Utilities for handling dates in competitions
- **`service_windows.py`**: Service window generation from demand data

### Desktop Application

- **`app.py`**: Main desktop application script using PyWebView
- **`build.py`**: Script to build standalone executables using PyInstaller
- **`ui/`**: Web-based user interface files (HTML, CSS, JavaScript)

### Testing Framework

- **`tests/conftest.py`**: Pytest fixtures shared across tests
- **`tests/test_*.py`**: Individual test files for different components
- **`tests/make_reference_data.py`**: Creates minimal reference data for testing

## Module Dependencies

The project follows a modular architecture with the following dependencies:

```
main.py
  └── calculations.py
      └── utils.py
      └── plotting.py

firm_capacity_with_competitions.py
  ├── src/calculations.py
  ├── src/utils.py
  ├── src/plotting.py
  ├── competition_builder.py
  │   ├── competition_config.py
  │   └── competition_dates.py
  ├── service_windows.py
  └── src/parquet_processor.py

app.py
  ├── src/calculations.py
  ├── src/utils.py
  ├── src/plotting.py
  ├── competition_builder.py
  └── competition_dates.py
```

## Key Classes and Functions

### Firm Capacity Calculation

- **`energy_above_capacity(demand, capacity, delta_t)`**: Calculates total energy above capacity
- **`energy_peak_based(demand, capacity, delta_t)`**: Calculates peak-based energy above capacity
- **`invert_capacity(func, demand, target, tol, maxiter)`**: Inverts energy function to find capacity

### Service Window Generation

- **`find_overload_segments(df, firm_capacity, delta_t)`**: Identifies segments where demand exceeds capacity
- **`create_service_window_from_segment(segment)`**: Creates a service window from an overload segment
- **`generate_monthly_service_periods(windows, delta_t)`**: Groups windows into monthly periods
- **`generate_daily_service_periods(windows, delta_t)`**: Groups windows into daily periods

### Competition Generation

- **`create_competitions_from_df(df, firm_capacity, ...)`**: Creates competitions from demand data
- **`create_competition_template(...)`**: Creates a competition template
- **`sanitize_reference(...)`**: Generates a valid competition reference
- **`FieldSelector`**: Class for managing optional fields in competitions

### Data Processing

- **`load_config(path)`**: Loads configuration from YAML file
- **`process_network_groups_in_parquet(...)`**: Processes network groups from parquet files
- **`update_dates_in_dataframe(df, target_year, month_offset)`**: Updates dates in demand data

### Visualization

- **`plot_E_curve(demand, func, C_est, target, outpath, title)`**: Creates energy curve plots

## Data Flow

The typical data flow through the system is:

1. **Load Configuration**: Configuration parameters are loaded from YAML files
2. **Read Demand Data**: Demand data is read from CSV or Parquet files
3. **Calculate Firm Capacity**: Firm capacity is calculated using the selected method
4. **Generate Service Windows**: Service windows are generated from demand data
5. **Create Competitions**: Competitions are created from service windows
6. **Validate and Save**: Results are validated and saved to output files

## Design Patterns

The codebase uses several design patterns:

### Strategy Pattern

The `invert_capacity` function uses the strategy pattern by accepting a function parameter (`energy_above_capacity` or `energy_peak_based`), allowing different energy calculation strategies.

```python
def invert_capacity(
    func,           # either energy_above_capacity or energy_peak_based
    demand: np.ndarray,
    target: float,
    tol: float = 1e-3,
    maxiter: int = 50
) -> float:
    """Bisection search to find C so that func(demand,C)≈target."""
    # Implementation...
```

### Factory Pattern

The `create_competition_template` function acts as a factory for creating competition objects:

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
    # Implementation...
```

### Configuration Pattern

The `FieldSelector` class uses a configuration pattern to determine which fields to include:

```python
class FieldSelector:
    """Enhanced field selector with support for field categorization."""
    
    def get_fields_for_mode(
        self,
        mode: ConfigMode,
        custom_fields: Optional[Set[str]] = None
    ) -> Dict[FieldLevel, Set[str]]:
        """Get the set of fields to include based on the configuration mode."""
        # Implementation...
```

## Type Hints and Documentation

The codebase uses type hints extensively for better IDE support and documentation:

```python
def energy_above_capacity(
    demand: np.ndarray, capacity: float, delta_t: float = 0.5
) -> float:
    """E(C) = ∑ max(demand - C,0) * Δt."""
    return np.sum(np.maximum(demand - capacity, 0.0)) * delta_t
```

## Error Handling

Error handling is implemented at multiple levels:

1. **Function-level validation**: Parameters are validated within functions
2. **Exception handling**: Exceptions are caught and logged
3. **Graceful degradation**: The system attempts to continue processing when possible

Example:
```python
try:
    result = process_substation_with_competitions(cfg, sub)
    logger.info(f"Successfully processed {sub['name']}")
except FileNotFoundError:
    logger.error(f"Error: Demand file not found for {sub['name']}.")
except Exception as e:
    logger.error(f"Error processing {sub['name']}: {e}", exc_info=True)
```

## Configuration System

The system uses YAML configuration files with several key sections:

```yaml
input:
  demand_base_dir: "./data/samples/"
  in_substation_folder: false

output:
  base_dir: "./output"

firm_capacity:
  target_mwh: 300.0
  tolerance: 0.01

competitions:
  procurement_window_size_minutes: 30
  daily_service_periods: true
  financial_year: "2025/26"

substations:
  - name: "substation1" 
    demand_file: "substation1.csv"
```

## Testing Approach

The testing framework uses pytest with fixtures for common testing needs:

```python
@pytest.fixture(scope="session")
def reference_dir():
    """Path to reference data directory."""
    return Path("tests/reference_data")

@pytest.fixture(scope="session")
def output_dir():
    """Path to output data directory."""
    return Path("output")
```

Tests focus on:
1. **Firm capacity calculation**: Ensuring calculations are correct
2. **Competition generation**: Verifying competitions have the correct structure
3. **Service window generation**: Testing service window features
4. **Reference data comparison**: Comparing against known good results

## Desktop Application Architecture

The desktop application follows a web-based architecture using PyWebView:

1. **Backend**: Python code for processing and analysis
2. **Frontend**: HTML/CSS/JavaScript for user interface
3. **API Bridge**: PyWebView's JavaScript API for communication

The `FlexibilityAnalysisAPI` class handles the bridge between frontend and backend:

```python
class FlexibilityAnalysisAPI:
    """API class to handle interaction between web UI and Python backend"""
    
    def __init__(self):
        self.config = None
        self.base_dir = Path(__file__).resolve().parent
        self.default_config_path = self.base_dir / "config.yaml"
        self.output_dir = self.base_dir / "output"
        
    def select_config_file(self):
        """Open a file dialog to select a configuration file"""
        # Implementation...
        
    def load_config(self, config_path=None):
        """Load application configuration file"""
        # Implementation...
    
    # Additional API methods...
```

## Adding New Features

When adding new features:

1. **Maintain modularity**: Add new modules or extend existing ones without breaking dependencies
2. **Follow type hints**: Use proper type annotations for new functions and classes
3. **Add tests**: Create tests for new functionality
4. **Update documentation**: Document new features in the appropriate section
5. **Consider backwards compatibility**: Ensure existing functionality continues to work

## Code Style and Standards

The codebase follows these standards:

1. **PEP 8**: Standard Python style guide
2. **Type annotations**: Used throughout the codebase
3. **Docstrings**: All functions and classes have docstrings
4. **Modular design**: Functionality is separated into appropriate modules
5. **Error handling**: Errors are caught and logged properly