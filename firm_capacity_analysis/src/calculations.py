# src/calculations.py
import numpy as np
from typing import Tuple, List

def energy_above_capacity(
    demand: np.ndarray, capacity: float, delta_t: float = 0.5
) -> float:
    """E(C) = ∑ max(demand - C,0) * Δt."""
    return np.sum(np.maximum(demand - capacity, 0.0)) * delta_t

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