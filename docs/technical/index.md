# Technical Documentation

This section provides detailed technical documentation on the internal workings of the Flexibility Analysis System, including mathematical models, algorithms, and parameter definitions.

## Core Components

The Flexibility Analysis System consists of several core components:

1. **Firm Capacity Analysis**: Calculates firm capacity values based on demand data
2. **Service Window Generation**: Identifies time windows when flexibility services may be needed
3. **Competition Generation**: Creates standardized flexibility competition specifications
4. **Visualization**: Generates plots and visualizations of results

## Mathematical Foundation

The system is built on a strong mathematical foundation that ensures consistency between:

1. The firm capacity calculation
2. The identified service windows
3. The generated competitions

Each component is mathematically linked to ensure that the energy values in the generated competitions match the energy above capacity from the firm capacity calculation.

## Key Documentation

- [Mathematical Models](mathematical-models.md): Detailed explanation of the mathematical models and algorithms
- [Firm Capacity Analysis](firm-capacity.md): How firm capacity is calculated
- [Service Window Generation](service-windows.md): How service windows are identified and created
- [Competition Generation](competitions.md): How competitions are generated from service windows
- [Dynamic vs Static Parameters](parameters.md): Which parameters are calculated from data vs fixed values

## Technical Diagrams

### System Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│   Demand Data   │─────▶│  Firm Capacity  │─────▶│ Service Windows │
│                 │      │    Analysis     │      │                 │
└─────────────────┘      └─────────────────┘      └────────┬────────┘
                                                           │
                                                           ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Visualization  │◀─────│   Output Data   │◀─────│   Competitions  │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Mathematical Relationship

```
                ┌─────────────────────────────────────┐
                │                                     │
                │   Energy Above Capacity E(C)        │
                │                                     │
                │   E(C) = ∑ max(D_t - C, 0) · Δt    │
                │                                     │
                └───────────────────┬─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   Peak-based Energy E_peak(C)                                       │
│                                                                     │
│   E_peak(C) = ∑ (P_s - C) · D_s · Δt                               │
│                                                                     │
│   where P_s is peak demand in segment s,                           │
│         D_s is duration of segment s                               │
│                                                                     │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   Service Windows                                                   │
│                                                                     │
│   Each service window w has:                                        │
│   - Capacity required = P_s - C                                     │
│   - Energy E_w = (P_s - C) · D_s · Δt                              │
│                                                                     │
│   Such that ∑ E_w = E_peak(C)                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Code Structure

The main code modules and their relationships:

- `calculations.py`: Core mathematical functions
- `plotting.py`: Visualization functions
- `service_windows.py`: Service window generation
- `competition_builder.py`: Competition generation
- `competition_config.py`: Configuration for competition generation
- `competition_dates.py`: Date handling for competitions
- `firm_capacity_with_competitions.py`: Main script for running the system

For more detailed information on the code structure, see the [Code Structure](../development/code-structure.md) documentation.