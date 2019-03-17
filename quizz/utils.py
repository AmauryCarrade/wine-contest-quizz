# noinspection PyPep8Naming
def as_choices(Enum):
    """
    Converts an enum to a tuple of 2-tuples used by Django for choices.

    :param Enum: The enum.
    :return: The choices in a format usable by Django.
    """
    return ((key.value, key) for key in Enum)
