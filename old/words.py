# Vector data from Jeffrey Pennington, Richard Socher, and Christopher D. Manning. 2014. GloVe: Global Vectors for
# Word Representation. Downloaded from https://nlp.stanford.edu/projects/glove/
from functools import cache

filePath = "../../glove.6B/glove.6B.200d.txt"

with open(filePath, 'r', encoding='utf-8') as file:
    words = file.readlines()
    wordVectors = {}
    for w in words:
        # print(w)
        word, vector = w.split(" ", 1)
        vector = [float(i) for i in vector.split()]
        wordVectors[word] = vector


def get_vector(wrd: str) -> list[float]:
    wrd = wrd.lower()
    if wrd not in wordVectors:
        return [2] * len(wordVectors["the"])
    return wordVectors[wrd]


def distance(word1: str, word2: str) -> float:
    return sum((a - b) ** 2 for a, b in zip(get_vector(word1), get_vector(word2))) ** 0.5


def phrase_vec(phrase: str) -> list[float]:
    phrase = phrase.split()
    return [sum(i) for i in zip(*[get_vector(w) for w in phrase])]


@cache
def phrase_distance(phrase1: str, phrase2: str) -> float:
    return sum((a - b) ** 2 for a, b in zip(phrase_vec(phrase1), phrase_vec(phrase2))) ** 0.5


def main():
    print(phrase_distance("hello world", "hello world"))
    print(phrase_distance("geometry dash", "rainbow dash"))
    print(phrase_distance("hug", "love"))
    print(phrase_distance("toad", "frog"))
    print(phrase_distance("twilight sparkle", "rainbow dash"))


if __name__ == '__main__':
    main()
