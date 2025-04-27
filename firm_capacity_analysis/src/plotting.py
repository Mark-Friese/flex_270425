# src/plotting.py
import numpy as np
import matplotlib
matplotlib.use('Agg') # Set non-interactive backend BEFORE importing pyplot
import matplotlib.pyplot as plt
from pathlib import Path

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