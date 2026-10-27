import re
import json
import sys
import argparse
from collections import Counter


def parse_stopwords(s):
    """Parse stopwords argument: comma-separated strings become a set of lowercased tokens."""
    if s is None:
        return set()
    if isinstance(s, str):
        return {token.strip().lower() for token in s.split(",") if token.strip()}
    return set(s)


def top_words(text, n=10, stopwords=None, min_length=1):
    """
    Return a list of (word, count) tuples for the top n words in ``text``.

    - Words are extracted with ``re.findall(r"[a-z']+", text.lower())``.
    - Tokens present in ``stopwords`` are excluded.
    - Tokens shorter than ``min_length`` characters are excluded.
    - Items are ordered by decreasing count; ties are broken alphabetically by word.
    """
    if stopwords is None:
        stopwords = set()
    else:
        stopwords = parse_stopwords(stopwords)
    words = re.findall(r"[a-z']+", text.lower())
    filtered = [w for w in words if w not in stopwords and len(w) >= min_length]
    counter = Counter(filtered)
    result = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return result[:n]


def main():
    parser = argparse.ArgumentParser(
        description="Print the top word frequencies in a text file."
    )
    parser.add_argument("file", help="path to the text file to analyse")
    parser.add_argument("--top", type=int, default=10, help="number of top words to return")
    parser.add_argument("--stopwords", type=str, default="", help="comma-separated stopwords (e.g. a,b,c)")
    parser.add_argument("--min-length", type=int, default=1, help="minimum character length of a word")
    parser.add_argument("--json", action="store_true", help="emit JSON output as [[word, count], ...]")
    args = parser.parse_args()

    try:
        text = open(args.file, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"Error: file '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        result = top_words(text, n=args.top, stopwords=parse_stopwords(args.stopwords), min_length=args.min_length)
        print(json.dumps([list(item) for item in result]))
    else:
        result = top_words(text, n=args.top, stopwords=parse_stopwords(args.stopwords), min_length=args.min_length)
        for word, count in result:
            print(f"{word}\t{count}")


if __name__ == "__main__":
    main()
