import json
import argparse
import networkx as nx
import time
import random
from itertools import islice

def load_graph_from_json(path):
    with open(path, "r", encoding="utf-8") as f:
        incoming_adj_list = json.load(f)
    G = nx.DiGraph()
    for word, defining_words in incoming_adj_list.items():
        for def_word in defining_words:
            G.add_edge(def_word, word)  # def_word → word
    return G

def analyze_structure(G):
    print("\n=== Structure ===")
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    print(f"# Nodes: {num_nodes}")
    print(f"# Edges: {num_edges}")
    print(f"Average in-degree: {num_edges / num_nodes:.2f}")
    print(f"Average out-degree: {num_edges / num_nodes:.2f}")

    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())

    roots = [n for n, deg in in_degrees.items() if deg == 0]
    leaves = [n for n, deg in out_degrees.items() if deg == 0]
    print(f"# Root nodes (zero in-degree): {len(roots)}")
    print(f"# Leaf nodes (zero out-degree): {len(leaves)}")

    # Find top 10 most defined and defining words
    most_defined = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
    most_defining = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 most defined words:")
    for word, deg in most_defined:
        print(f"  {word}: {deg} definitions")
    print("\nTop 10 most defining words:")
    for word, deg in most_defining:
        print(f"  {word}: {deg} defined words")

def analyze_cycles(G):
    print("\n=== Cycles ===")
    self_loops = list(nx.selfloop_edges(G))
    print(f"# Self-loops: {len(self_loops)}")

    G_noloops = G.copy()
    G_noloops.remove_edges_from(self_loops)
    is_dag = nx.is_directed_acyclic_graph(G_noloops)
    print(f"Graph is acyclic (ignoring self-loops): {is_dag}")

    try:
        cycle = nx.find_cycle(G_noloops, orientation="original")
        print("Found non-trivial cycle (sample):", " → ".join([u for u, _, _ in cycle]))
    except nx.NetworkXNoCycle:
        print("No non-trivial cycles detected (via find_cycle)")

    sampled = list(islice(nx.simple_cycles(G_noloops), 3))
    print(f"# Sampled {len(sampled)} non-trivial cycle(s):")
    for i, cycle in enumerate(sampled):
        print(f"  Cycle {i+1}: {' → '.join(cycle)}")

def analyze_components(G):
    print("\n=== Components ===")
    start = time.time()
    num_sccs = nx.number_strongly_connected_components(G)
    largest_scc = max(nx.strongly_connected_components(G), key=len)
    print(f"# Strongly connected components: {num_sccs}")
    print(f"Largest SCC size: {len(largest_scc)}")

    num_wccs = nx.number_weakly_connected_components(G)
    print(f"# Weakly connected components: {num_wccs}")
    print(f"(Computed in {time.time() - start:.2f} seconds)")

def analyze_connectivity(G):
    print("\n=== Connectivity Metrics ===")
    density = nx.density(G)
    print(f"Graph density: {density:.8f}")

    # Clustering: needs undirected graph
    #undirected = G.to_undirected()
    #clustering = nx.clustering(undirected)
    #print(f"Avg clustering coefficient (undirected): {sum(clustering.values()) / len(clustering):.4f}")

    # Reachability
    sample_nodes = random.sample(list(G.nodes), k=100)
    reach_ratios = []
    for node in sample_nodes:
        reachable = nx.descendants(G, node)
        reach_ratios.append(len(reachable) / G.number_of_nodes())
    avg_reach = sum(reach_ratios) / len(reach_ratios)
    print(f"Avg reachability (forward, from sample of 100 nodes): {avg_reach:.4f}")

    # Longest path (on DAG version only)
    G_noloops = G.copy()
    G_noloops.remove_edges_from(nx.selfloop_edges(G))
    if nx.is_directed_acyclic_graph(G_noloops):
        try:
            longest = max((nx.dag_longest_path_length(G_noloops, source=n) for n in G_noloops.nodes), default=0)
            print(f"Longest definitional chain (DAG path length): {longest}")
        except Exception as e:
            print("Could not compute longest path:", e)
    else:
        print("Graph is not acyclic — skipping longest path")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze statistics of a definitional graph")
    parser.add_argument("--incoming_adj_list_path", type=str, default="data/graph/incoming_adj_list.json", help="Path to the incoming adjacency list JSON file")
    parser.add_argument("--structure", action="store_true", help="Compute structure-level stats (nodes, degrees, roots/leaves)")
    parser.add_argument("--cycles", action="store_true", help="Analyze cycles and self-loops")
    parser.add_argument("--components", action="store_true", help="Analyze strongly/weakly connected components")
    parser.add_argument("--connectivity", action="store_true", help="Analyze connectivity and reachability metrics")
    args = parser.parse_args()

    print(f"Loading graph from {args.incoming_adj_list_path}")
    G = load_graph_from_json(args.incoming_adj_list_path)

    if args.structure:
        t0 = time.time()
        analyze_structure(G)
        print(f"(structure stats computed in {time.time() - t0:.2f} seconds)")

    if args.cycles:
        t0 = time.time()
        analyze_cycles(G)
        print(f"(cycle stats computed in {time.time() - t0:.2f} seconds)")

    if args.components:
        t0 = time.time()
        analyze_components(G)
        print(f"(component stats computed in {time.time() - t0:.2f} seconds)")

    if args.connectivity:
        t0 = time.time()
        analyze_connectivity(G)
        print(f"(connectivity metrics computed in {time.time() - t0:.2f} seconds)")

    if not (args.structure or args.cycles or args.components or args.connectivity):
        print("No analyses selected. Pass flags like --structure to enable specific sections.")
