# dictionary-completeness
What's the smallest number of words you need to know to be able to learn them all?

## Setup
1. Download postprocessed data extracted from the latest Wiktionary dump.
    ```
    mkdir -p data/raw_input
    wget -P data/raw_input https://kaikki.org/dictionary/English/words/kaikki.org-dictionary-English-words.jsonl
    ```

2. Construct the dictionary graph adjacency lists.
    ```
    pip install -r requirements.txt
    python constuct_graph.py
    ```

### Some graph statistics
```
=== Structure ===
# Nodes: 998669
# Edges: 7547019
Average in-degree: 7.56
Average out-degree: 7.56
# Root nodes (zero in-degree): 38
# Leaf nodes (zero out-degree): 597909

Top 10 words with most incoming edges:
  draw: 700 predecessors
  drop: 469 predecessors
  run: 465 predecessors
  break: 428 predecessors
  line: 426 predecessors
  set: 424 predecessors
  point: 410 predecessors
  lead: 410 predecessors
  cut: 400 predecessors
  stick: 400 predecessors

Top 10 words with most outgoing edges:
  of: 714003 successors
  plural: 265469 successors
  A: 204612 successors
  the: 191037 successors
  a: 147549 successors
  and: 141429 successors
  or: 128324 successors
  in: 122706 successors
  to: 111505 successors
  form: 76419 successors

=== Cycles ===
# Self-loops: 24035
Graph is acyclic (ignoring self-loops): False

=== Components ===
# Strongly connected components: 928098
Largest SCC size: 66368
# Weakly connected components: 6

=== Connectivity Metrics ===
Graph density: 0.00000757
Avg reachability (forward, from sample of 100 nodes): 0.0600
```

## Baselines
### An empirical curve
Call the graph $G = (V, E)$.

There are some words that necessarily have to be in any valid grounding set, namely 
1. words with empty definitions i.e. vertices with in-degree = 0.
2. words with self-referential definitions i.e. vertices which have self-loops.

If you collect these into a set $B$ and go on to randomly pick $k$ vertices from $V \backslash B$, call that set $A_k$ and plot the empirical probability of $A_k \cup B$ constituting a valid grounding for $G$, you get the following line plot for the success probability as a function of $|A_k \cup B| = |B| + k$.

```
python -m baselines.grounding_curve_sweep
python -m analysis.plot_grounding_curve
```

<img src="https://github.com/anirudhajith/dictionary-completeness/blob/main/data/plots/random_grounding_curve_plot.png" width="500">

So under this heuristic, even if you take away 25,000 $(\approx 2.5\\%)$ of the vertices, you're dead in the water. This is the number to beat. 

### A greedy strategy
One simple baseline that could plausibly work better is just greedily picking vertices with the highest out-degrees.

```
python -m baselines.topk_outdegree_grounding
```

Wow, this works so much better! This greedy strategy finds a grounding set of size 389,576 $(\approx 39.0\\%)$.
