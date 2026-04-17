"""Convert strings to numbers and numbers to strings.

Adapted and simplified for Treebeard from https://tabo.pe/projects/numconv/ by Gustavo Picon
"""

# from april fool's rfc 1924
BASE85 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~"


class NumConv:
    """Class to create converter objects.

    :param alphabet: A string that will be used as a encoding alphabet.

        The base for conversion is the length of the alphabet.

       The default value is :data:`numconv.BASE85`

    :raise ValueError: when *alphabet* has duplicated characters
    """

    def __init__(self, alphabet: str = BASE85):
        """basic validation and cached_map storage"""
        if len(set(alphabet)) != len(alphabet):
            raise ValueError(f"duplicate characters found in '{alphabet}'")

        self.radix = len(alphabet)
        self.alphabet = alphabet
        self.cached_map = dict(zip(self.alphabet, range(self.radix)))

    def int2str(self, num: int) -> str:
        """Converts an integer into a string.

        :param num: A numeric value to be converted to a string.

        :raise ValueError: when *num* isn't positive
        """
        pass

    def str2int(self, chars) -> int:
        """Converts a string into an integer.

        :param chars: A string that will be converted to an integer.

        :raise ValueError: when *chars* is invalid
        """
        pass
