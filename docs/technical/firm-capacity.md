# Firm Capacity Analysis

This document provides a detailed explanation of firm capacity analysis as implemented in the Flexibility Analysis System.

## What is Firm Capacity?

In the context of power networks, firm capacity represents the level of demand that can be reliably served at all times. It is the threshold above which flexibility services may be needed to manage demand peaks.

## Firm Capacity Methods

The system implements two methods for calculating firm capacity:

### 1. Energy Above Capacity (Plain Method)

The plain energy above capacity method is straightforward:

$$E(C) = \sum_{t} \max(D_t - C, 0) \cdot \Delta t$$

Where:
- $D_t$ is the demand at time $t$ (in MW)
- $C$ is the firm capacity threshold (in MW)
- $\Delta t$ is the time step (typically 0.5 hours)
- The result $E(C)$ is in MWh

This method simply sums all energy that exceeds the capacity threshold over the entire time period.

**Implementation:**

```python
def energy_above_capacity(
    demand: np.ndarray, capacity: float, delta_t: float = 0.5
) -> float:
    """E(C) = ∑ max(demand - C,0) * Δt."""
    return np.sum(np.maximum(demand - capacity, 0.0)) * delta_t
```

**Key Characteristics:**

- Simple and computationally efficient
- Accounts for all energy above the threshold
- Does not distinguish between continuous and discontinuous periods
- Does not recognize peak demand within segments

### 2. Peak-Based Energy Above Capacity

The peak-based method is more sophisticated:

$$E_{peak}(C) = \sum_{s \in S} (P_s - C) \cdot D_s \cdot \Delta t$$

Where:
- $S$ is the set of all contiguous segments where demand exceeds capacity
- $P_s$ is the peak demand within segment $s$ (in MW)
- $D_s$ is the duration of segment $s$ (number of time periods)
- $C$ is the firm capacity threshold (in MW)
- $\Delta t$ is the time step (typically 0.5 hours)

This method identifies contiguous segments where demand exceeds capacity, then uses the peak demand within each segment for the calculation.

**Implementation:**

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

**Key Characteristics:**

- More aligned with how flexibility services operate
- Identifies specific time windows when demand peaks above capacity
- Focuses on the peak demand within continuous segments
- Maps directly to service window generation
- Generally results in the same or similar capacity value as the plain method

### Comparing the Methods

For a given target energy threshold, both methods can be inverted to determine firm capacity:

```python
C_plain = invert_capacity(energy_above_capacity, demand, target_mwh, tol=tol_C)
C_peak = invert_capacity(energy_peak_based, demand, target_mwh, tol=tol_C)
```

Visual comparison shows the difference between methods:

![Comparing E(C) Methods](../images/comparing_methods.png)

## Inverting Capacity Functions

To determine the optimal firm capacity, the system inverts the energy functions to find the capacity value that corresponds to a target energy threshold:

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

This function uses a bisection search algorithm:

1. Start with low bound = 0 and high bound = maximum demand
2. Calculate the midpoint capacity
3. Compute the energy above this capacity
4. If energy > target, increase the low bound to the midpoint
5. If energy ≤ target, decrease the high bound to the midpoint
6. Repeat until the bounds converge within a tolerance

## Firm Capacity Visualization

The system generates visualization plots to understand how energy above capacity varies with different capacity values:

![E_curve_peak Example](../images/E_curve_peak_example.png)

These plots show:
- The E(C) curve showing energy above capacity for different capacity values
- The target energy threshold (horizontal gray line)
- The estimated firm capacity (vertical gray line)
- The intersection point of the energy curve and target threshold

## Target Energy Threshold Selection

The target energy threshold (`target_mwh`) is a key parameter that directly affects the calculated firm capacity:

- Higher target values result in a lower firm capacity
- Lower target values result in a higher firm capacity

This threshold represents the amount of energy (in MWh) that would need to be provided by flexibility services over the analysis period.

## Site-Specific Targets

Different substations may require different target thresholds depending on their characteristics:

```csv
site_name,target_mwh
Monktonhall,150
Substation2,250
Substation3,500
```

These site-specific targets can be provided through a CSV file:

```bash
python firm_capacity_with_competitions.py --targets data/samples/site_targets.csv
```

## Practical Considerations

### Time Series Resolution

The system works with demand data at any resolution, but typically uses half-hourly data:

- $\Delta t = 0.5$ hours for half-hourly data
- $\Delta t = 1.0$ hours for hourly data
- $\Delta t = 0.25$ hours for 15-minute data

The time step is automatically determined from the data but can be manually specified.

### Analysis Period

The analysis typically covers one year of data to capture seasonal variations, but can be applied to any period:

- Annual analysis is standard for capturing seasonal patterns
- Monthly or quarterly analysis can be used for specific seasons
- Custom periods can be used for focused analysis

### Target Setting Guidelines

Guidelines for setting target energy thresholds:

1. **Percentage of Total Energy**: Target = X% of total energy consumed
2. **Historical Average**: Target = Average annual energy above historical firm capacity
3. **Cost-Benefit Analysis**: Target = Energy threshold that balances infrastructure costs vs. flexibility costs
4. **Regulatory Requirements**: Target based on security standards or regulatory frameworks

## Summary Statistics

The system calculates several summary statistics:

```python
stats = {
    "substation": name,
    "C_plain_MW": C_plain,
    "C_peak_MW": C_peak,
    "mean_demand_MW": float(demand.mean()),
    "max_demand_MW": float(demand.max()),
    "total_energy_MWh": float((demand * delta_t).sum()),
    "energy_above_capacity_MWh": float(energy_peak),
    "target_mwh": T
}
```

These statistics provide context for understanding the firm capacity values and the energy that exceeds them.

## References

For more information on firm capacity methodologies:

1. DNO Common Evaluation Methodology (CEM)
2. ENA Engineering Recommendation P2/7
3. Ofgem RIIO-ED2 Business Plan Guidance