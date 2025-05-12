import os
import json
import heapq
import argparse
import random
import networkx as nx
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

def greedy_deductive_grounding(G, initial_grounding, strategy, backoff):
    
    mandatory_set = set()
    if initial_grounding == "empty":
        grounding_set = set()
    elif initial_grounding == "mandatory":
        mandatory_set = compute_mandatory_grounding_set(G)
        grounding_set = set(mandatory_set)

    all_nodes = set(G.nodes)
    G_pred = {v: list(G.predecessors(v)) for v in G.nodes}
    G_succ = {v: list(G.successors(v)) for v in G.nodes}
    unknown_set = all_nodes - grounding_set
    remaining_pred_count = {v: G.in_degree(v) for v in G.nodes} # number of remaining predecessors that are unknown
    remaining_succ_count = {v: G.out_degree(v) for v in G.nodes} # number of remaining successors that are unknown
    to_explore = deque() # queue for exploring the known frontier (contains knowable but yet unknown nodes)

    for node in grounding_set:
        for pred in G_pred[node]:
            remaining_succ_count[pred] -= 1
        for succ in G_succ[node]:
            remaining_pred_count[succ] -= 1
            if (succ in unknown_set) and (remaining_pred_count[succ] == 0):
                to_explore.append(succ)

    pbar = tqdm(initial=len(all_nodes) - len(unknown_set), total=len(all_nodes), desc="# known nodes")
    while len(unknown_set) > 0:
        if len(to_explore) > 0:
            if strategy == "queue":
                current = to_explore.popleft()
            elif strategy == "stack":
                current = to_explore.pop()
        else:
            if backoff == "random":
                current = random.choice(list(unknown_set))
            elif backoff == "max_out_degree":
                current = max(unknown_set, key=lambda x: remaining_succ_count[x])
            grounding_set.add(current)
            
        unknown_set.remove(current)
        for succ in G_succ[current]:
            remaining_pred_count[succ] -= 1
            if (succ in unknown_set) and (remaining_pred_count[succ] == 0):
                to_explore.append(succ)
        for pred in G_pred[current]:
            remaining_succ_count[pred] -= 1

        pbar.update(1)

    extra_grounding_set = sorted(grounding_set - mandatory_set)

    return {
        "total_nodes": len(all_nodes),
        "initial_grounding": initial_grounding,
        "strategy": strategy,
        "backoff": backoff,
        "grounding_set_size": len(grounding_set),
        "grounding_set": sorted(grounding_set),
        "extra_grounding_set": extra_grounding_set,
    }

def save_results(results, path):
    dirname = os.path.dirname(path); os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Greedy deductive grounding")
    parser.add_argument("--input_path", type=str, default="data/graph/incoming_adj_list.json", help="Path to incoming adjacency list")
    parser.add_argument("--output_path", type=str, default="data/experiments/greedy_deductive_grounding.json", help="Path to save grounding result")
    parser.add_argument("--initial_grounding", choices=["empty", "mandatory"], default="mandatory", help="Initial grounding set")
    parser.add_argument("--strategy", choices=["queue", "stack"], default="queue", help="Strategy for exploring the known frontier")
    parser.add_argument("--backoff", choices=["random", "max_out_degree"], default="max_out_degree", help="Strategy for picking new grounding word when stuck")
    parser.add_argument("--random_seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.backoff == "random":
        print(f"Using random seed {args.random_seed}")
        random.seed(args.random_seed)

    print(f"Loading graph from {args.input_path}")
    G = load_graph_from_json(args.input_path)
    print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    print(f"Running greedy grounding with strategy='{args.strategy}', backoff='{args.backoff}', initial_grounding='{args.initial_grounding}'")
    results = greedy_deductive_grounding(
        G,
        initial_grounding=args.initial_grounding,
        strategy=args.strategy,
        backoff=args.backoff
    )

    print(f"Found grounding set of size {results['grounding_set_size']} out of {results['total_nodes']} total nodes")
    save_results(results, args.output_path)
    print(f"Saved result to {args.output_path}")
