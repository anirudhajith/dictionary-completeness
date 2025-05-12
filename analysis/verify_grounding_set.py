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

def get_grounding_closure(G, grounding_set):
    known = set(grounding_set)
    queue = deque()

    pbar = tqdm(initial=len(known), total=len(G.nodes), desc="# known nodes")

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
        pbar.update(1)
        for succ in G.successors(node):
            if succ not in known and set(G.predecessors(succ)).issubset(known):
                queue.append(succ)

    return set(known)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify the completeness of a candidate grounding set.")
    parser.add_argument("--input_path", type=str, default="data/graph/incoming_adj_list.json", help="Path to incoming adjacency list")
    parser.add_argument("--grounding_file", type=str, required=True, help="Path to the grounding set JSON file.")
    args = parser.parse_args()

    print(f"Loading graph from {args.input_path}")
    G = load_graph_from_json(args.input_path)
    print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    print(f"Loading grounding set from {args.grounding_file}")
    with open(args.grounding_file, "r", encoding="utf-8") as f:
        candidate_grounding_set = json.load(f)["grounding_set"]
    candidate_grounding_set = set(candidate_grounding_set)
    print(f"Loaded grounding set with {len(candidate_grounding_set)} nodes")
    
    print("Verifying completeness of the grounding set...")
    grounding_closure = get_grounding_closure(G, candidate_grounding_set)
    missing_nodes = set(G.nodes) - grounding_closure
    
    if len(missing_nodes) == 0:
        print("The grounding set is valid.")
    else:
        print("The grounding set is invalid. Unreachable nodes:")
        print(missing_nodes)