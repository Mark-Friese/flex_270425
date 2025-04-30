# Flexibility Analysis System Desktop Application

This desktop application provides a user-friendly interface for the Flexibility Analysis System, allowing users to analyze power network demand data and generate flexibility competition specifications.

## Features

- **Single Executable Application**: Runs without requiring Python installation or admin rights
- **Firm Capacity Analysis**: Calculate firm capacity metrics using both standard and peak-based methods
- **Competition Generation**: Create flexibility competitions based on analysis results
- **Interactive Visualization**: View plots, maps, and detailed competition specifications
- **Results Management**: Browse and compare results from multiple analyses

## Installation

### Running the Packaged Application

1. Download the latest release from the releases page
2. Extract the ZIP file (if provided in ZIP format)
3. Run the `FlexibilityAnalysisSystem.exe` file (Windows) or `FlexibilityAnalysisSystem` executable (macOS/Linux)

### Building from Source

#### Prerequisites

- Python 3.8 or newer
- pip (Python package installer)

#### Steps

1. Clone this repository:
   ```
   git clone <repository-url>
   cd flexibility_analysis_system
   ```

2. Install the required packages:
   ```
   pip install -r packaging_requirements.txt
   ```

3. Build the application:
   ```
   python build.py
   ```

4. The packaged application will be created in the `dist` directory.

## Usage

1. **Launch the Application**: Run the executable file.

2. **Load Configuration**: Click on the settings (gear) icon in the top-right corner and select "Load Configuration". Navigate to and select your `config.yaml` file.

3. **Select a Substation**: Choose a substation from the dropdown menu on the left sidebar.

4. **Set Analysis Options**:
   - Check/uncheck "Generate Competitions" based on your needs
   - Optionally set a target year for competition dates

5. **Run Analysis**: Click the "Run Analysis" button to start the analysis process.

6. **View Results**: Once the analysis completes, view the results in the tabs:
   - **Summary**: Key metrics from the analysis
   - **Plots**: Visualization of demand curves and capacity thresholds
   - **Competitions**: Generated competition specifications
   - **Map**: Geographical representation of results (placeholder in current version)

7. **Export or Save Results**: Results are automatically saved to the output directory specified in the configuration file.

## Configuration

The application uses YAML configuration files to specify:

- Input data locations
- Output directory
- Firm capacity parameters
- Substation details
- Competition generation settings

Example configuration file (`config.yaml`):

```yaml
input:
  demand_base_dir: "./data/samples/"
  in_substation_folder: false
  metadata_file: "./data/metadata.csv"

output:
  base_dir: "./output"

firm_capacity:
  target_mwh: 5016.6525
  tolerance: 0.10

competitions:
  procurement_window_size_minutes: 30
  daily_service_periods: true
  financial_year: "2025/26"

substations:
  - name: monktonhall
    demand_file: "demand.csv"
```

## Troubleshooting

- **Application won't start**: Ensure you have extracted all files from the ZIP archive if downloading a packaged release.
- **Missing dependencies**: The packaged application includes all required dependencies. If building from source, make sure all requirements are installed.
- **Data loading issues**: Check your configuration file and ensure all paths are correct. Data files should be in CSV format with 'Timestamp' and 'Demand (MW)' columns.

## License

[Specify your license here]

## Acknowledgments

This application integrates the firm capacity analysis and competition generation functionality developed for power network demand analysis.
