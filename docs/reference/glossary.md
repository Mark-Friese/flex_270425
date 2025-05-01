# Glossary

This document provides definitions for key terms and concepts used in the Flexibility Analysis System.

## Core Concepts

### Firm Capacity

**Firm Capacity** is the level of network capacity that can be reliably provided at all times without the need for flexibility services. It represents the threshold above which flexibility services may be required to manage demand peaks.

### Energy Above Capacity (E(C))

**Energy Above Capacity** is the total energy that exceeds a given capacity threshold over a time period. It is measured in megawatt-hours (MWh) and can be calculated using different methods.

### Peak-Based Energy Above Capacity (E_peak(C))

**Peak-Based Energy Above Capacity** is a method for calculating energy above capacity that identifies contiguous periods where demand exceeds capacity and uses the peak demand within each period for the calculation. This approach more closely aligns with how flexibility services operate.

### Service Window

A **Service Window** is a specific time period (e.g., "Monday 17:00-19:30") when demand is expected to exceed firm capacity and flexibility services may be required. Service windows define when, how much, and for how long flexibility is needed.

### Service Period

A **Service Period** is a collection of service windows grouped by a time frame, typically a month or a specific day. Service periods are used to organize service windows in flexibility competitions.

### Flexibility Competition

A **Flexibility Competition** is a standardized specification for procuring flexibility services in power networks. It defines when flexibility is needed, where it is needed, how much is required, and the terms and conditions for providing the service.

## Mathematical Terms

### Target Energy Threshold

The **Target Energy Threshold** is the amount of energy (in MWh) that would need to be provided by flexibility services over the analysis period. This parameter directly affects the calculated firm capacity value.

### Time Step (delta_t)

The **Time Step** (often denoted as Δt) is the time interval between consecutive demand data points, typically 0.5 hours for half-hourly data. This parameter is used in energy calculations and is measured in hours.

### Tolerance

**Tolerance** is the precision parameter used in the bisection search algorithm for inverting capacity functions. It determines how closely the algorithm approximates the target energy threshold.

### Bisection Search

**Bisection Search** is an algorithm used to find the firm capacity value that corresponds to a target energy threshold. It repeatedly divides the search interval in half until the capacity value is found within the specified tolerance.

## Service Window Parameters

### Capacity Required

**Capacity Required** is the amount of flexibility capacity needed during a service window, calculated as the peak demand minus the firm capacity. It is measured in megawatts (MW).

### Window Duration

**Window Duration** is the length of time a service window is active, typically measured in hours.

### Service Days

**Service Days** specify which days of the week a service window applies to, such as "Monday" or "Friday". This allows flexibility providers to plan their availability for specific days.

### Procurement Window Size

**Procurement Window Size** is the granularity of service windows, specified in minutes. This parameter controls whether larger windows are split into smaller ones, affecting the number and duration of service windows.

## Competition Parameters

### Competition Reference

A **Competition Reference** is a unique identifier for a flexibility competition, following a specific format (e.g., "T2504_SPEN_Monktonhall").

### Financial Year

A **Financial Year** is a 12-month period used for accounting and budgeting purposes, typically running from April to March (e.g., "2025/26" for April 2025 to March 2026).

### Qualification Period

The **Qualification Period** is the time frame during which potential providers can qualify to participate in a flexibility competition. It typically starts one month before the service period and lasts for two weeks.

### Bidding Period

The **Bidding Period** is the time frame during which qualified providers can submit bids for a flexibility competition. It typically occurs on the same day as the qualification period ends.

## Data Formats

### CSV (Comma-Separated Values)

**CSV** is a text file format that uses commas to separate values, used for storing tabular data. The system typically uses CSV files for demand data and results.

### Parquet

**Parquet** is a columnar storage file format designed for efficient data storage and retrieval. It is particularly useful for large datasets and supports advanced querying capabilities.

### JSON (JavaScript Object Notation)

**JSON** is a lightweight data-interchange format that is easy for humans to read and write and easy for machines to parse and generate. The system uses JSON for competition specifications and metadata.

## System Components

### Configuration Mode

**Configuration Mode** determines which optional fields are included in generated competitions:
- **REQUIRED_ONLY**: Only voltage requirements are included
- **STANDARD**: Commonly used optional fields are included
- **CUSTOM**: User-specified fields from available options

### Field Level

**Field Level** indicates where an optional field belongs in the competition structure:
- **ROOT**: Competition-wide fields
- **SERVICE_WINDOW**: Fields specific to service windows

### Network Group

A **Network Group** is a collection of network assets (typically substations) that are grouped together for analysis purposes. In parquet processing, each network group is processed separately.

## Technical Terms

### Overload Segment

An **Overload Segment** is a contiguous period where demand exceeds firm capacity. Overload segments are identified during service window generation and are converted into service windows.

### Required Reduction

**Required Reduction** is the amount by which demand needs to be reduced to stay within firm capacity, calculated as the peak demand minus the firm capacity. It is measured in megawatts (MW).

### Schema Validation

**Schema Validation** is the process of verifying that generated competitions conform to the required schema structure, ensuring compatibility with external systems.

## Application Terms

### Desktop Application

The **Desktop Application** is a graphical user interface for the Flexibility Analysis System, built using PyWebView to provide a user-friendly way to perform analyses and view results.

### Command Line Interface (CLI)

The **Command Line Interface** allows users to run the Flexibility Analysis System from a terminal or command prompt, providing more flexibility and automation capabilities.

### Site-Specific Targets

**Site-Specific Targets** are custom energy thresholds for individual substations, specified in a CSV file with substation names and target values. These override the default target from the configuration.

### Reference Data

**Reference Data** in the testing framework refers to known good outputs stored for comparison with new outputs during testing, ensuring that changes don't break existing functionality.