# dictionary-completeness
## What's the smallest number of words you need to know to be able to learn them all?





#### Setup
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