# Flexibility Analysis System

Welcome to the documentation for the Flexibility Analysis System, a comprehensive toolkit for analyzing power network demand data and generating flexibility service competitions.

## Overview

The Flexibility Analysis System helps network operators identify flexibility needs in power networks by:

1. Analyzing historical demand data to determine firm capacity requirements
2. Identifying specific time windows when flexibility services may be needed
3. Generating standardized flexibility competition specifications
4. Visualizing results with interactive plots and a desktop application interface

## Key Features

### Firm Capacity Analysis

* **Dual Analysis Methods**: Calculate firm capacity using both standard and peak-based approaches
* **Mathematical Models**: Rigorous mathematical foundation for calculating energy exceeding capacity
* **Visualization**: Generate intuitive plots showing energy curves and capacity thresholds

### Service Window Generation

* **Automated Identification**: Automatically identify time windows when demand exceeds firm capacity
* **Configurable Granularity**: Control window size and grouping (daily/monthly)
* **Mathematical Consistency**: Service windows directly correspond to peak-based energy calculation

### Competition Generation

* **Standardized Format**: Generate competitions compliant with the flexibility competition schema
* **Configurable Parameters**: Control both dynamic and static parameters in the generated competitions
* **Validation**: Validate generated competitions against the schema

### User Interfaces

* **Command Line Interface**: Process data and generate results through flexible command-line options
* **Desktop Application**: User-friendly desktop interface for visualization and analysis
* **Data Format Support**: Process both CSV and Parquet data formats

## Getting Started

* [Installation Guide](installation/index.md): Install the system and its dependencies
* [User Guide](usage/index.md): Learn how to use the system effectively
* [Configuration](usage/configuration.md): Configure the system for your needs

## For Developers

* [Mathematical Models](technical/mathematical-models.md): Understand the mathematical foundations
* [Developer Guide](development/index.md): Contribute to the project
* [API Reference](reference/api-reference.md): Reference for system components

## Example Use Cases

* **Distribution Network Operators**: Identify flexibility needs in distribution networks
* **Flexibility Service Providers**: Understand when and where flexibility services may be needed
* **Regulatory Compliance**: Generate standardized competition specifications
* **Network Planning**: Analyze the impact of changes in demand patterns on flexibility needs

## Project Status

This project is actively maintained and developed. Latest version: 1.0.0 (May 2025)