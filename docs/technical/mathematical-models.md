# Mathematical Models and Analysis

This document explains the mathematical foundations of the Flexibility Analysis System, particularly the firm capacity calculations and service window generation methodology.

## 1. Firm Capacity Analysis

Firm capacity represents the power network capacity that can be reliably provided, with any demand exceeding this value representing potential flexibility needs. The system implements two methods for calculating firm capacity.

### 1.1 Energy Above Capacity (E(C))

The "plain" energy above capacity method calculates the total energy that exceeds a given capacity threshold over the entire time period:

$$E(C) = \sum_{t} \max(D_t - C, 0) \cdot \Delta t$$

Where:
- $D_t$ is the demand at time $t$ (in MW)
- $C$ is the firm capacity threshold (in MW)
- $\Delta t$ is the time step (typically 0.5 hours)
- The result $E(C)$ is in MWh

This is implemented in `energy_above_capacity()` in the `calculations.py` module:

```python
def energy_above_capacity(
    demand: np.ndarray, capacity: float, delta_t: float = 0.5
) -> float:
    """E(C) = ∑ max(demand - C,0) * Δt."""
    return np.sum(np.maximum(demand - capacity, 0.0)) * delta_t
```

### 1.2 Peak-Based Energy Above Capacity (E_peak(C))

The peak-based method takes a more sophisticated approach by identifying contiguous segments where demand exceeds capacity, then using the peak demand in each segment:

$$E_{peak}(C) = \sum_{s \in S} (P_s - C) \cdot D_s \cdot \Delta t$$

Where:
- $S$ is the set of all contiguous segments where demand exceeds capacity
- $P_s$ is the peak demand within segment $s$ (in MW)
- $D_s$ is the duration of segment $s$ (number of time periods)
- $C$ is the firm capacity threshold (in MW)
- $\Delta t$ is the time step (typically 0.5 hours)

This is implemented in `energy_peak_based()`:

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

The peak-based approach aligns better with how flexibility services operate, as it identifies specific time windows when demand peaks above capacity.

### 1.3 Capacity Inversion (Finding C for a Target Energy)

To determine the optimal firm capacity, the system uses a bisection search algorithm to find the capacity value that results in a target energy value:

1. Start with low bound = 0 and high bound = maximum demand
2. Calculate the midpoint capacity
3. Compute the energy above this capacity using one of the methods above
4. If energy > target, increase the low bound to the midpoint
5. If energy ≤ target, decrease the high bound to the midpoint
6. Repeat until the bounds converge within a tolerance

This is implemented in `invert_capacity()`:

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

## 2. Service Window Generation

Service windows represent specific time periods when flexibility services may be needed. Their generation directly relates to the peak-based energy calculation method.

### 2.1 Identifying Overload Segments

The system identifies contiguous segments where demand exceeds firm capacity using the same logic as the peak-based energy calculation:

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
    # ...implementation details...
```

For each segment, the following information is captured:
- Start and end timestamps
- Peak demand within the segment
- Required reduction (peak - firm capacity)
- Duration (in periods and hours)
- Energy (MWh) calculated as: required_reduction × duration_hours

### 2.2 Converting Segments to Service Windows

Each overload segment is converted to a service window with:

```python
def create_service_window_from_segment(
    segment: Dict
) -> Dict:
    """
    Create a service window from an overload segment.
    """
    # ...implementation details...
```

The service window contains:
- Name (based on day of week and time)
- Start and end times (HH:MM format)
- Service days (specific day of the week)
- Capacity required (peak - firm_capacity)
- Energy (MWh) directly from the segment calculation

### 2.3 Grouping Windows into Service Periods

Service windows are grouped into service periods, either by month or by day depending on configuration:

```python
def generate_monthly_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate monthly service periods from service windows.
    Groups by month and includes only one instance of each window.
    """
    # ...implementation details...
```

```python
def generate_daily_service_periods(
    windows: List[Dict],
    delta_t: float = 0.5
) -> List[Dict]:
    """
    Generate daily service periods from service windows.
    Creates a separate service period for each day with overloads.
    """
    # ...implementation details...
```

## 3. Mathematical Consistency

A key feature of the system is mathematical consistency between:
- The energy_peak_based calculation
- The identified service windows
- The total energy in the generated competitions

This ensures that the sum of energy (MWh) across all service windows should match the total energy above capacity from the peak-based calculation:

$$E_{peak}(C) = \sum_{w \in W} E_w$$

Where:
- $E_{peak}(C)$ is the total energy from the peak-based calculation
- $W$ is the set of all service windows
- $E_w$ is the energy (MWh) for service window $w$

This mathematical consistency is verified in the code with:

```python
total_mwh = 0
for comp in competitions:
    for period in comp['service_periods']:
        for window in period['service_windows']:
            if 'energy_mwh' in window:
                total_mwh += window['energy_mwh']

# Verify against the original energy_peak calculation
if abs(total_mwh - energy_peak_total) > 0.01:  # Allow small rounding differences
    logger.warning(f"MWh mismatch: energy_peak_based total = {energy_peak_total:.2f}, competition total = {total_mwh:.2f}")
else:
    logger.info(f"MWh totals match: {energy_peak_total:.2f} = {total_mwh:.2f}")
```

## 4. Visualization and Analysis

The system visualizes the energy curves (E(C) and E_peak(C)) to understand how energy exceeding capacity changes with different capacity values:

```python
def plot_E_curve(
    demand: np.ndarray,
    func,
    C_est: float,
    target: float,
    outpath: Path,
    title: str
):
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

These visualizations help users understand:
- The relationship between firm capacity and energy exceeding that capacity
- The impact of different capacity values on the amount of flexibility needed
- The identified target capacity that meets the specified energy threshold