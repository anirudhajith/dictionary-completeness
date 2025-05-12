# dictionary-completeness
What's the smallest number of words you need to know to be able to learn them all?

## Setup
1. Download [postprocessed data](https://kaikki.org/dictionary/English/index.html) extracted from the latest [Wiktionary](https://en.wiktionary.org/wiki/Wiktionary:Main_Page) dump.
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

Top 5 words with most incoming edges:
  draw: 700 predecessors
  drop: 469 predecessors
  run: 465 predecessors
  break: 428 predecessors
  line: 426 predecessors

Top 5 words with most outgoing edges:
  of: 714003 successors
  plural: 265469 successors
  A: 204612 successors
  the: 191037 successors
  a: 147549 successors

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
### Randomly pick a candidate grounding set (random + mandatory)
Call the graph $G = (V, E)$.

There are some words that necessarily have to be in any valid grounding set, namely 
1. words with empty definitions i.e. vertices with in-degree = 0.
2. words with self-referential definitions i.e. vertices which have self-loops.

If you collect these into a set $B$ and go on to randomly pick $k$ vertices from $V \backslash B$, call that set $A_k$ and compute the empirical probability of $A_k \cup B$ constituting a valid grounding for $G$, you get the following line plot for the success probability as a function of $|A_k \cup B| = |B| + k$.

```
python -m baselines.random_grounding --trials 1000
python -m analysis.plot_random_grounding_curve
```

<img src="https://github.com/anirudhajith/dictionary-completeness/blob/main/data/plots/random_grounding_curve.png" width="500">

So under this heuristic, even when you drop down to **970,000 ($\approx$ 97.1%)** vertices, you're already dead in the water. This is the number to beat. 

### Iteratively insert random (yet) unknown vertices into the candidate grounding set (random + mandatory + iterative)

Initialize the grounding set to $B$. Then alternate between 
1) Computing the set of all "known" words reachable from the current grounding set, and 
2) Adding a randomly chosen hitherto unknown vertex to the grounding set.
...until you obtain a valid grounding set.

```
python -m baselines.greedy_deductive_grounding --initial_grounding mandatory --strategy queue --backoff random
```
Wow, this works so much better! This greedy strategy finds a grounding set of size **500,623 (50.1%)**.


### Greedily pick vertices with the highest out-degrees (greedy + mandatory)
One simple baseline that could plausibly work better is to simply greedily pick vertices with the highest out-degrees until you first reach a valid grounding set (post including $B$). The intuition here is that you're choosing to include vertices in your grounding set that have maximal utility in that they enable maximal marginal reachability.

```
python -m baselines.greedy_out_degree_grounding
```

Okay, that's a pretty good! This greedy strategy finds a grounding set of size **389,576 (39.0%)**.

### Greedily pick vertices with the most unknown successors 
#### greedy + mandatory + iterative
One obvious flaw of the previous baseline is that it can end up wasting precious grounding set space by including words whose successors are already all/mostly known. The out-degree heurisic values are computed once at the start and never updated. 

What happens if instead, you maintain counts not simply of the number of successors (i.e. out-degree) each vertex has, but of the number of *unknown* successors they each have at any point. You can then do something slightly cleverer than the previous baseline by alternating between 1) Computing the set of all "known" words reachable from the current grounding set, and 2) Adding the unknown vertex with the highest number of unknown successors to the grounding set.

```
python -m baselines.greedy_deductive_grounding --initial_grounding mandatory --strategy queue --backoff max_out_degree
```

WHAT. This tiny tweak now finds a grounding set of size **36,255 (3.6%)**. How is that even possible? And valid grounding set must be a superset of $B$. And $B$ by itself contains $\approx$ 24,000 words...

#### greedy + empty + iterative
Also, if you start with an empty set as initial grounding instead of $B$ (i.e. greedy + empty + iterative), you do almost as well. 

```
python -m baselines.greedy_deductive_grounding --initial_grounding empty --strategy queue --backoff max_out_degree
```

You find a grounding set of size **38,669 (3.9%)**.

## Results

Call the set of undefined and self-referential words $B \subset V$.

| Baseline                                      | Grounding set size ↓ | %age words retained ↓ |
| --------------------------------------------- | --------------------:| ---------------------:|
| do nothing                                    | 998,669              | 100.0                 |
| random + mandatory                            | $\approx$ 970,000    | $\approx$ 97.1        |
| random + mandatory + iterative                | 500,623              | 50.1                  |
| greedy + mandatory                            | 389,576              | 39.0                  |
| greedy + empty + iterative                    | 38,669               | 3.9                   |
| greedy + mandatory + iterative                | 36,255               | 3.6                   |