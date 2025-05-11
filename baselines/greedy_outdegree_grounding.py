import os
import json
import argparse
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

def find_min_outdegree_grounding_size(G, B):
    V_rest = list(set(G.nodes) - B)
    out_degrees = {node: G.out_degree(node) for node in V_rest}
    sorted_nodes = sorted(out_degrees, key=out_degrees.get, reverse=True)

    low, high = 0, len(sorted_nodes)
    final_result = {}

    print("Running binary search over top-k out-degree nodes")
    while low < high:
        mid = (low + high) // 2
        top_k = set(sorted_nodes[:mid])
        full_set = B | top_k
        print(f"Trying k = {mid} (total grounding set size = {len(full_set)})", end=": ")
        if simulate_grounding(G, full_set):
            final_result = {
                "k": mid,
                "grounding_set_size": len(full_set),
                "grounding_set": sorted(list(full_set)),
            }
            high = mid
            print("Success")
        else:
            low = mid + 1
            print("Failure")

    return final_result

def save_results(results, path):
    dirname = os.path.dirname(path); os.makedirs(dirname, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binary search for top-k out-degree grounding set")
    parser.add_argument("--input_path", type=str, default="data/graph/incoming_adj_list.json", help="Path to incoming adjacency list")
    parser.add_argument("--output_path", type=str, default="data/experiments/greedy_outdegree_grounding.json", help="Path to save grounding result")
    args = parser.parse_args()

    print(f"Loading graph from {args.input_path}")
    G = load_graph_from_json(args.input_path)
    print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    print("Computing mandatory grounding set B")
    B = compute_mandatory_grounding_set(G)
    print(f"Mandatory grounding set size: {len(B)}")

    result = find_min_outdegree_grounding_size(G, B)
    print(f"Found grounding set using top {result['k']} out-degree nodes")
    print(f"Total grounding set size: {result['grounding_set_size']}")

    save_results(result, args.output_path)
    print(f"Saved result to {args.output_path}")
