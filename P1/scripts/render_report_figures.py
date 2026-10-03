#!/usr/bin/env python3
"""Draw the three report figures from saved tables, without changing analysis."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_table(directory, name):
    with (directory / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def draw(directory, output):
    output.mkdir(parents=True, exist_ok=True)
    grid = read_table(directory, "grid_summary.csv")
    searches = read_table(directory, "search_summary.csv")
    curves = read_table(directory, "online_curves.csv")
    paired = read_table(directory, "comparison_paired.csv")
    blocks, opts = [8, 16, 24, 64, 128], ["O0", "O1", "O2", "O3"]
    indexed = {(int(r["s"]), r["opt"]): r for r in grid}
    figure, axes = plt.subplots(1, 2, figsize=(14, 5.5), layout="constrained")
    values = [[float(indexed[s, opt]["median_s"]) for opt in opts] for s in blocks]
    heatmap = axes[0].imshow(values, aspect="auto", cmap="YlOrRd", vmin=0)
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            axes[0].text(j, i, f"{value:.3f}", ha="center", va="center",
                         color="white" if value > 300 else "black")
    axes[0].set(xticks=range(4), xticklabels=opts, yticks=range(5), yticklabels=blocks,
                xlabel="GCC optimization", ylabel="Block size s", title="20 configurations: median of three runs")
    figure.colorbar(heatmap, ax=axes[0], label="Kernel RAW seconds")
    for i, row in enumerate(grid):
        low, mid, high = (float(row[k]) for k in ("min_s", "median_s", "max_s"))
        axes[1].plot([low, high], [i, i], color="C0")
        axes[1].scatter(mid, i, color="C0", s=22)
    axes[1].set(yticks=range(20), yticklabels=[f"s{r['s']}/{r['opt']}" for r in grid],
                xlabel="Kernel RAW seconds", title="Median and observed min / max")
    axes[1].invert_yaxis()
    axes[1].set_xlim(left=0)
    figure.savefig(output / "grid_median.png", dpi=160)
    plt.close(figure)

    seeds = [int(r["seed"]) for r in paired]
    algorithms = ["grid", "random", "greedy"]
    labels = {"grid": "Grid", "random": "Random", "greedy": "Greedy"}
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), layout="constrained")
    for color, algorithm in enumerate(algorithms):
        rows = {int(r["seed"]): r for r in searches
                if r["stage"] == "comparison" and r["algorithm"] == algorithm}
        axes[0, 0].plot(range(6), [float(rows[s]["gap_ref_pct"]) for s in seeds],
                        "o-", color=f"C{color}", label=labels[algorithm])
        axes[0, 1].plot(range(6), [float(rows[s]["search_driver_raw_s"]) for s in seeds],
                        "o-", color=f"C{color}", label=labels[algorithm])
        for seed in seeds:
            trajectory = sorted((r for r in curves if r["stage"] == "comparison"
                                 and r["algorithm"] == algorithm and int(r["seed"]) == seed),
                                key=lambda r: int(r["step"]))
            best = [float(r["best_so_far_s"]) for r in trajectory]
            axes[1, 0].step([int(r["actual_calls"]) for r in trajectory], best,
                            where="post", alpha=.45, color=f"C{color}")
            axes[1, 1].step([float(r["tuning_raw_elapsed_s"]) for r in trajectory], best,
                            where="post", alpha=.45, color=f"C{color}")
    for axis in axes[0]:
        axis.set(xticks=range(6), xticklabels=[str(s) for s in seeds], xlabel="Seed")
        axis.tick_params(axis="x", rotation=25)
        axis.legend()
    axes[0, 0].set_ylabel("Common reference gap (%)")
    axes[0, 1].set_ylabel("Search total RAW seconds")
    axes[1, 0].set(xlabel="Completed target calls", ylabel="Best observed kernel RAW seconds")
    axes[1, 1].set(xlabel="Online RAW elapsed seconds", ylabel="Best observed kernel RAW seconds")
    figure.suptitle("Grid / Random / Greedy: six searches per algorithm, at most eight calls each")
    figure.savefig(output / "online_search.png", dpi=160)
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    for i, row in enumerate(paired):
        gains = json.loads(row["gain_panel_rounds_pp"])
        axes[0].plot([i, i], [min(gains), max(gains)], color="C4")
        axes[0].scatter([i] * len(gains), gains, color="C4", alpha=.6)
    axes[0].axhline(-2, color="red", linestyle="--", label="Risk boundary: -2 percentage points")
    axes[0].set_ylabel("G: 100 x (Random - Recheck) / reference\n(percentage points)")
    axes[0].legend(fontsize=9)
    axes[1].bar(range(6), [100 * float(r["cost_saving_fraction"]) for r in paired])
    axes[1].axhline(10, color="green", linestyle="--", label="Cost saving target: 10%")
    axes[1].set_ylabel("Search total cost saving (%)")
    axes[1].legend(fontsize=9)
    for axis in axes:
        axis.set(xticks=range(6), xticklabels=[str(s) for s in seeds], xlabel="Matching seed")
        axis.tick_params(axis="x", rotation=25)
        axis.grid(axis="y", alpha=.2)
    figure.suptitle("Candidate recheck (6 + 2) vs Random (8): quality loss, strategy not retained")
    figure.savefig(output / "saved-search-results.png", dpi=160)
    plt.close(figure)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    draw(args.tables, args.output)
