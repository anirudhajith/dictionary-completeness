import os
import json
import regex # important for unicode support
import argparse
import unicodedata
from tqdm import tqdm

def is_acceptable_word(word):
    for char in word:
        cat = unicodedata.category(char)
        if cat.startswith('C'):     # control, surrogate, etc.
            return False
        if cat.startswith('Z'):     # separators
            return False
        if cat.startswith('S'):     # symbols, including emoji
            return False
        if not (char.isalpha() or char in "-'"):
            return False
    return True

def read_file(filename: str) -> dict:
    num_lines = sum(1 for line in open(filename, "r", encoding="utf-8"))
    records_dict = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Loading JSONL file", total=num_lines):
            record = json.loads(line)
            word = record["word"]
            if is_acceptable_word(word):
                if word not in records_dict:
                    records_dict[word] = []
                if "senses" in record:
                    for s in record["senses"]:
                        if "glosses" in s:
                            records_dict[word].extend(s["glosses"])
    for k, v in records_dict.items():
        records_dict[k] = list(set(v))
    print(f"Loaded {len(records_dict)} records from {filename}")
    records_dict = {k: v for k, v in records_dict.items() if len(v) > 0}
    print(f"Retained {len(records_dict)} records after discarding words without glosses")
    records_dict = {k: v for k, v in records_dict.items() if len(k.split(" ")) == 1}
    print(f"Retained {len(records_dict)} records after discarding multi-word words")
    print(f"Sorting {len(records_dict)} records by word")
    records_dict = dict(sorted(records_dict.items(), key=lambda item: item[0]))
    return records_dict

def construct_incoming_adj_list(records_dict: dict) -> tuple:

    # Tokenizer: breaks on spaces, but preserves apostrophes and punctuation
    # "'ello there, matey!" --> ["'ello", "there", ",", "matey", "!"]
    # "What's the scene, buddy?" --> ["What's", 'the', 'scene', ',', 'buddy', '?']
    # "semi-conscious" --> ["semi-conscious"]
    TOKEN_RE = regex.compile(
        r"""
        [\'\-]?\p{L}+(?:['’]\p{L}+)?(?:-\p{L}+)*[\'\-]?  # Unicode letters, apostrophes, hyphens
        | [^\w\s]                                       # punctuation
        """,
        regex.VERBOSE
    )
    def tokenize(text):    
        return TOKEN_RE.findall(text)
    
    def match_to_defined_words(token, defined_words):
        if len(token) == 0:
            return []
        
        # original form
        if token in defined_words:
            return [token]
        
        # lowercased form
        lower_cased_token = token.lower()
        if lower_cased_token in defined_words:
            return [lower_cased_token]

        # possessives get handled below for free
        # hyphen-splitting and apostrophe-splitting
        for special_char in ["-", "'"]:
            if special_char in token:
                # I'm only bothered if there are at most two occurrences
                if token.count(special_char) == 1:
                    first, second = token.split(special_char) 
                    first_found = first in defined_words
                    second_found = second in defined_words
                    first_hyphen_found = (first + special_char) in defined_words
                    hyphen_second_found = (special_char + second) in defined_words
                    if first_found and hyphen_second_found:
                        return [first, special_char + second]
                    elif first_hyphen_found and second_found:
                        return [first + special_char, second]
                    elif first_found and second_found:
                        return [first, second]
                elif token.count(special_char) == 2:
                    first, second, third = token.split(special_char)
                    parts = [first, "-", second, "-", third]
                    for i in range(len(parts)):
                        chunk1 = "".join(parts[:i])
                        chunk2 = "".join(parts[i:])
                        if chunk1 in defined_words and chunk2 in defined_words:
                            return [chunk1, chunk2]
                    if first in defined_words and second in defined_words and third in defined_words:
                        return [first, second, third]

        if len(token) > 1:
            print("No match for token:", token)
        # if no match, return empty list
        return []

    graph_dict = {}
    defined_words = set(records_dict.keys())
    for word, glosses in tqdm(records_dict.items(), desc="Constructing graph"):
        all_gloss_words = set()
        for gloss in glosses:
            tokenized_gloss = tokenize(gloss)
            matched_tokens = []
            for token in tokenized_gloss:
                matched_tokens.extend(match_to_defined_words(token, defined_words))
            all_gloss_words.update(matched_tokens)
        graph_dict[word] = sorted(list(all_gloss_words))
    
    num_vertices = len(graph_dict)
    num_edges = sum(len(v) for v in graph_dict.values())
    return graph_dict, (num_vertices, num_edges)

def create_outgoing_adj_list(incoming_adj_list_dict: dict) -> tuple:
    outgoing_adj_list_dict = {}
    for word, incoming_words in tqdm(incoming_adj_list_dict.items(), desc="Creating outgoing adjacency list"):
        for incoming_word in incoming_words:
            if incoming_word not in outgoing_adj_list_dict:
                outgoing_adj_list_dict[incoming_word] = []
            outgoing_adj_list_dict[incoming_word].append(word)
    
    outgoing_adj_list_dict = {k: sorted(v) for k, v in outgoing_adj_list_dict.items()}
    outgoing_adj_list_dict = dict(sorted(outgoing_adj_list_dict.items(), key=lambda item: item[0]))

    num_vertices = len(outgoing_adj_list_dict)
    num_edges = sum(len(v) for v in outgoing_adj_list_dict.values())
    return outgoing_adj_list_dict, (num_vertices, num_edges)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construct a graph from the JSONL file")
    parser.add_argument("--input_path", type=str, default="data/raw_input/kaikki.org-dictionary-English-words.jsonl", help="Path to the input JSONL file")
    parser.add_argument("--glosses_path", type=str, default="data/intermediates/glosses.json", help="Path to the output JSON file")
    parser.add_argument("--incoming_adj_list_path", type=str, default="data/graph/incoming_adj_list.json", help="Path to the output incoming adjacency list JSON file")
    parser.add_argument("--outgoing_adj_list_path", type=str, default="data/graph/outgoing_adj_list.json", help="Path to the output outgoing adjacency list JSON file")
    args = parser.parse_args()

    records_dict = read_file(args.input_path)
    print(f"Writing {len(records_dict)} records to {args.glosses_path}")
    dirname = os.path.dirname(args.glosses_path); os.makedirs(dirname, exist_ok=True)
    with open(args.glosses_path, "w", encoding="utf-8") as f:
        json.dump(records_dict, f, ensure_ascii=False, indent=1)

    incoming_adj_list_dict, (num_vertices, num_edges) = construct_incoming_adj_list(records_dict)
    print(f"Average in-degree: {num_edges / num_vertices:.2f}")
    print(f"Writing incoming adjacency list with {num_vertices} vertices and {num_edges} edges to {args.incoming_adj_list_path}")
    dirname = os.path.dirname(args.incoming_adj_list_path); os.makedirs(dirname, exist_ok=True)
    with open(args.incoming_adj_list_path, "w", encoding="utf-8") as f:
        json.dump(incoming_adj_list_dict, f, ensure_ascii=False, indent=1)
    
    outgoing_adj_list_dict, (num_vertices, num_edges) = create_outgoing_adj_list(incoming_adj_list_dict)
    print(f"Average out-degree: {num_edges / num_vertices:.2f}")
    print(f"Writing outgoing adjacency list with {num_vertices} vertices and {num_edges} edges to {args.outgoing_adj_list_path}")
    dirname = os.path.dirname(args.outgoing_adj_list_path); os.makedirs(dirname, exist_ok=True)
    with open(args.outgoing_adj_list_path, "w", encoding="utf-8") as f:
        json.dump(outgoing_adj_list_dict, f, ensure_ascii=False, indent=1)
