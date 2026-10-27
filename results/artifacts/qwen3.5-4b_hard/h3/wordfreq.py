import re, sys
from collections import Counter

def top_words(text, n=10):
    words = re.findall(r"[a-z']+", text.lower())
    return Counter(words).most_common(n)

def main(argv):
    text = open(argv[1]).read()
    for w, c in top_words(text):
        print(f"{w}\t{c}")

if __name__ == "__main__":
    main(sys.argv)
