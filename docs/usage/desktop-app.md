# Desktop Application Usage Guide

This guide covers how to use the Flexibility Analysis System desktop application, which provides a user-friendly graphical interface for performing firm capacity analysis and generating flexibility competitions.

## Application Overview

The Flexibility Analysis System desktop application provides:

- A graphical interface for configuring and running analyses
- Interactive visualization of results
- Competition viewing and exploration
- Results management for multiple substations

## Getting Started

### Launch the Application

1. Start the application using one of these methods:
   - Double-click the executable (`FlexibilityAnalysisSystem.exe` on Windows)
   - Run from the command line: `python app.py`

### Load Configuration

When first launched, you'll need to load a configuration file:

1. Click the settings (gear) icon in the top-right corner
2. Select "Load Configuration" from the dropdown menu
3. Navigate to and select your `config.yaml` file
4. The status will update to "Config Loaded" when successful

![Load Configuration](../images/desktop_app_load_config.png)

### Select a Substation

Once the configuration is loaded:

1. Choose a substation from the dropdown menu on the left sidebar
2. If results already exist, they will be automatically loaded
3. If no results exist, you'll need to run an analysis

## Running an Analysis

To run an analysis for the selected substation:

1. Set analysis options:
   - Check/uncheck "Generate Competitions" based on your needs
   - Optionally set a target year for competition dates
2. Click the "Run Analysis" button
3. The status area will show progress and completion messages
4. Results will be displayed in the tabs when the analysis completes

![Run Analysis](../images/desktop_app_run_analysis.png)

## Exploring Results

The results are organized into several tabs:

### Summary Tab

The Summary tab provides an overview of the analysis results:

- Firm capacity values (both plain and peak-based)
- Demand statistics (mean, max, total energy)
- Competition metrics (if competitions were generated)
- Detailed table of all calculated values

![Summary Tab](../images/desktop_app_summary.png)

### Plots Tab

The Plots tab displays visualizations of the analysis:

- E(C) curve plots for both plain and peak-based methods
- Firm capacity thresholds and target energy levels
- Click on any plot to view it in full size

![Plots Tab](../images/desktop_app_plots.png)

### Competitions Tab

The Competitions tab shows generated flexibility competitions:

- Expandable list of competitions
- Service period details
- Service window information
- Option to view the raw JSON data

![Competitions Tab](../images/desktop_app_competitions.png)

### Map Tab

The Map tab provides a geographical representation:

- Substations displayed on an interactive map
- Firm capacity values indicated by circle size
- Click on stations for detailed information

![Map Tab](../images/desktop_app_map.png)

## Working with Multiple Substations

### Previous Results List

The application keeps track of previously analyzed substations:

1. The "Previous Results" panel on the left shows all substations with results
2. Click on any substation to load its results
3. The currently selected substation is highlighted

![Previous Results](../images/desktop_app_previous_results.png)

### Comparing Results

To compare results across substations:

1. Run analyses for multiple substations
2. Switch between substations to compare their results
3. Note that the application only displays one substation's results at a time

## Application Settings

### Setting Output Directory

To change where results are saved:

1. Click the settings (gear) icon in the top-right corner
2. Select "Set Output Directory" from the dropdown menu
3. Navigate to and select your desired output directory
4. All subsequent analyses will save results to this directory

### Viewing Logs

To view application logs:

1. Click the settings (gear) icon in the top-right corner
2. Select "View Logs" from the dropdown menu
3. A modal will appear showing the application logs
4. This can be helpful for troubleshooting issues

## Using the Desktop Application with Large Datasets

The desktop application is optimized for working with large datasets:

1. **Filtering**: When working with parquet files, use filtering to limit the substations processed
2. **Progress Tracking**: The application shows progress during long-running operations
3. **Resource Management**: The application manages memory efficiently for large datasets

## Tips and Tricks

### Keyboard Shortcuts

- `Ctrl+O`: Open configuration file
- `Ctrl+R`: Run analysis
- `Ctrl+Tab`: Navigate between tabs
- `Esc`: Close modals

### Performance Optimization

For optimal performance when working with large datasets:

1. Process one substation at a time
2. Close other memory-intensive applications
3. Set an appropriate target energy value to avoid excessive computations

### Exporting Results

While the application automatically saves results to the output directory, you can also:

1. Take screenshots of plots using the screenshot button
2. Copy data tables to the clipboard
3. Export competition data as JSON for further processing

## Troubleshooting

### Application Not Responding

If the application becomes unresponsive during analysis:

1. Wait for the current operation to complete
2. If it remains unresponsive, close and restart the application
3. Consider processing fewer substations at once

### Data Loading Issues

If you encounter issues loading data:

1. Check that your configuration file is correctly set up
2. Verify that your data files exist at the specified locations
3. Ensure your data files have the required columns:
   - `Timestamp`
   - `Demand (MW)`

### Visualization Problems

If plots or visualizations don't appear correctly:

1. Refresh the tab by clicking on another tab and then back
2. Restart the application
3. Check that your data has valid values (no `NaN` or extreme outliers)

## Additional Resources

For more information and help:

- Check the [detailed documentation](../index.md)
- View the [command-line interface guide](command-line.md) for alternative usage
- Consult the [configuration guide](configuration.md) for more options