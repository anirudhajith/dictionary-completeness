import os
import json
import argparse
import random
import networkx as nx
import numpy as np
from tqdm import tqdm
from collections import deque

def load_graph_from_json(path):
    with open(path, "r", encoding="utf-8") as f:
        incoming_adj_list = json.load(f)
    G = nx.DiGraph()
    for word, defining_words in incoming_adj_list.items():
        for def_word in defining_words:
            G.add_edge(def_word, word)
    return G

def compute_mandatory_grounding_set(G):
    mandatory = set()
    for node in tqdm(G.nodes, desc="Computing mandatory grounding set"):
        preds = set(G.predecessors(node))
        if len(preds) == 0 or node in preds:
            mandatory.add(node)
    return mandatory

def simulate_grounding(G, known_set):
    known = set(known_set)
    queue = deque()

    for node in G.nodes:
        if node not in known:
            preds = set(G.predecessors(node))
            if preds.issubset(known):
                queue.append(node)

    while queue:
        node = queue.popleft()
        if node in known:
            continue
        known.add(node)
        for succ in G.successors(node):
            if succ not in known and set(G.predecessors(succ)).issubset(known):
                queue.append(succ)

    return len(known) == G.number_of_nodes()

def run_grounding_sweep(G, B, ks, trials):
    def bootstrap_cis(successes, trials, alpha=0.05):
        ref_transcript = [1] * successes + [0] * (trials - successes)
        transcripts = []
        for _ in range(1000):
            sampled_transcript = np.random.choice(ref_transcript, size=trials, replace=True)
            transcripts.append(np.sum(sampled_transcript).item() / trials)
        lower_bound = np.percentile(transcripts, 100 * alpha / 2)
        upper_bound = np.percentile(transcripts, 100 * (1 - alpha / 2))
        return lower_bound, upper_bound

    V_rest = list(set(G.nodes) - B)
    results = {}

    for k in tqdm(ks, desc="Sweeping over ks"):
        print(f"Size of grounding set:{len(B) + k} / {len(G.nodes)}")
        successes = 0
        for _ in tqdm(range(trials), desc=f"Running trials for k={k}", leave=False):
            A_k = set(random.sample(V_rest, k))
            full_set = A_k | B
            if simulate_grounding(G, full_set):
                successes += 1
        prob = successes / trials
        ci_low, ci_high = bootstrap_cis(successes, trials, alpha=0.05)
        results[k] = {
            "grounding_set_size": len(B) + k,
            "trials": trials,
            "success_rate": prob,
            "lower_bound_95": ci_low,
            "upper_bound_95": ci_high
        }
        print(f"k={k}, success_rate={prob:.4f}, 95% CI=({ci_low:.4f}, {ci_high:.4f})")
    return results

def save_results(results, path):
    dirname = os.path.dirname(path); os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Empirical grounding curve sweep")
    parser.add_argument("--input_path", type=str, default="data/graph/incoming_adj_list.json", help="Path to incoming adjacency list")
    parser.add_argument("--output_path", type=str, default="data/experiments/random_grounding.json", help="Path to save sweep results")
    parser.add_argument("--min_k", type=int, default=950000, help="Minimum value of k to sweep")
    parser.add_argument("--max_k", type=int, default=974596, help="Maximum value of k to sweep")
    parser.add_argument("--step_k", type=int, default=1000, help="Step size for k sweep")
    parser.add_argument("--trials", type=int, default=100, help="Number of trials per k")
    args = parser.parse_args()

    print(f"Loading graph from {args.input_path}")
    G = load_graph_from_json(args.input_path)
    print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    print("Computing mandatory grounding set B")
    B = compute_mandatory_grounding_set(G)
    print(f"Mandatory grounding set size: {len(B)}")

    ks = list(range(args.min_k, args.max_k + 1, args.step_k))[::-1] # go from max to min because then you can weed out the ones that are too small
    print(f"Running grounding sweep for k in {ks} with {args.trials} trials each")

    results = run_grounding_sweep(G, B, ks, args.trials)
    save_results(results, args.output_path)

    print(f"Saved grounding sweep results to {args.output_path}")
