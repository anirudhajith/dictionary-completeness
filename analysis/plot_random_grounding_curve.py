import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt

def load_grounding_sweep_results(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_grounding_curve(results, output_path):
    plt.figure(figsize=(12, 8))

    x, y, y_lo, y_hi = [], [], [], []
    for k, stats in sorted(results.items()):
        x.append(stats["grounding_set_size"])
        y.append(stats["success_rate"])
        y_lo.append(stats["lower_bound_95"])
        y_hi.append(stats["upper_bound_95"])

    x = np.array(x)
    y = np.array(y)
    y_lo = np.array(y_lo)
    y_hi = np.array(y_hi)

    plt.plot(x, y, label="Success Rate")
    plt.fill_between(x, y_lo, y_hi, alpha=0.2, label="95% CI")
    plt.title("Empirical Random Grounding Curve (|V|=998669)", fontsize=20)
    plt.xlabel("Grounding Set Size", fontsize=16)
    plt.ylabel("Success Rate", fontsize=16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid(axis='both', linestyle='--', alpha=0.7)
    plt.ylim(-0.05, 1.05)
    plt.legend(fontsize=14)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    print(f"Saved plot to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot empirical grounding sweep results")
    parser.add_argument("--input_path", type=str, default="data/experiments/random_grounding.json", help="Path to grounding sweep JSON results")
    parser.add_argument("--output_path", type=str, default="data/plots/random_grounding_curve.png", help="Path to save the plot image")
    args = parser.parse_args()

    results = load_grounding_sweep_results(args.input_path)
    plot_grounding_curve(results, args.output_path)
