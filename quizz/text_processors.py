import string

from Levenshtein import distance
from unidecode import unidecode


def gentle_levenshtein_distance(string1, string2):
    """
    Computes the Levenshtein distance between two strings, but ignoring
    punctuation, multi-spaces, line breaks and accents.

    :param string1: The first string.
    :param string2: The other string.
    :return: The Levenshtein distance.
    """
    return distance(normalize(string1), normalize(string2))


def normalize(raw_string):
    """
    Normalizes a string, removing accents, punctuation, multiple spaces,
    switching everything to lowercase, and replacing line breaks with spaces.

    :param raw_string:The raw string.
    :return: The normalized string.
    """
    return " ".join(
        unidecode(raw_string)
        .lower()
        .translate(str.maketrans("", "", string.punctuation))
        .split()
    )
