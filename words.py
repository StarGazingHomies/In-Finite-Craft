# Vector data from Jeffrey Pennington, Richard Socher, and Christopher D. Manning. 2014. GloVe: Global Vectors for
# Word Representation. Downloaded from https://nlp.stanford.edu/projects/glove/
from functools import cache

filePath = "../glove.6B/glove.6B.200d.txt"

with open(filePath, 'r', encoding='utf-8') as file:
    words = file.readlines()
    wordVectors = {}
    for w in words:
        # print(w)
        word, vector = w.split(" ", 1)
        vector = [float(i) for i in vector.split()]
        wordVectors[word] = vector


def getVector(wrd: str) -> list[float]:
    wrd = wrd.lower()
    if wrd not in wordVectors:
        return [2] * len(wordVectors["the"])
    return wordVectors[wrd]


def distance(word1: str, word2: str) -> float:
    return sum((a - b) ** 2 for a, b in zip(getVector(word1), getVector(word2))) ** 0.5


def phraseVec(phrase: str) -> list[float]:
    phrase = phrase.split()
    return [sum(i) for i in zip(*[getVector(w) for w in phrase])]


@cache
def phraseDistance(phrase1: str, phrase2: str) -> float:
    return sum((a - b) ** 2 for a, b in zip(phraseVec(phrase1), phraseVec(phrase2))) ** 0.5


def main():
    print(phraseDistance("hello world", "hello world"))
    print(phraseDistance("geometry dash", "rainbow dash"))
    print(phraseDistance("hug", "love"))
    print(phraseDistance("toad", "frog"))
    print(phraseDistance("twilight sparkle", "rainbow dash"))


if __name__ == '__main__':
    main()
