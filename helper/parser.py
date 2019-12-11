from random import random


def is_hashtag(s: str) -> bool or ValueError:
    """
    Decides whether the given string is a hashtag or not.

    :param s: The input string.
    :rtype: bool
    :return: True for a hashtag.
    """
    if len(s) > 0:
        return True if s[0] == '#' else False
    else:
        raise ValueError("Input string must contain characters.")


def should_do_action(probability: float) -> bool:
    return random() < probability
