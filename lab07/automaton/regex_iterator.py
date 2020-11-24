import string
from .valid_characters import ValidCharacters


class RegexIterator:
    # Char parsing special characters
    END_OF_STRING = chr(0)

    # Conversion constants
    DIGITS_PATTERN = "(" + "+".join(list(string.digits)) + ")"

    ALPHA_PATTERN = "(" + "+".join(list(string.ascii_letters)) + ")"

    WORD_PATTERN = ("(" +
                    ALPHA_PATTERN +

                    ")")

    def __init__(self, regex: str):
        self.regex = regex
        self.char = None
        if (not regex):
            raise ValueError("Empty regex.")
        correct, error_str = self.__regex_correct(regex)
        if (not correct):
            raise ValueError("Regular expression invalid: " + error_str)
        self.__convert_to_standard_re()

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if (self.idx == len(self.regex)):
            return RegexIterator.END_OF_STRING
        next_elem = self.regex[self.idx]
        self.idx += 1
        return next_elem

    def next_char(self):
        self.char = next(self)

    def ended(self):
        return self.char == self.END_OF_STRING

    @classmethod
    def __regex_correct(cls, regex):
        r""" Checks if regular expression is correct.

        Valid regular expression should fulfill the following:
         - contain only characters from the set ValidCharacters.ALL_SYMBOLS
         - have the same amount of opening and closing parentheses,
         - have only VALID_SYMBOLS in square parentheses,
         - have no multiple ValidCharacters.META_SYMBOLS in a row,
         - have 'd' after '\' to complete '\d' (for any digit).
         - ValidCharacters.META_SYMBOLS always have their complementary
          sequence of symbols, which is not an empty pair of parentheses

        Note: This does not guarantee complete validity of an automaton built
            upon this re, but other types of incorrectness should be covered
            while building automaton f.e epsilon cycles.
        """

        parentheses_round = 0
        parentheses_square = 0
        in_square = False
        round_empty = False
        square_empty = False

        for i, letter in enumerate(regex):
            if (round_empty and letter != ')'):
                round_empty = False
            if (square_empty and letter != ']'):
                square_empty = False

            if (in_square and letter not in ValidCharacters.VALID_SYMBOLS and
                    letter != ']'):
                return (False,
                        f"Invalid symbol in parentheses [] at pos {i}")
            if (letter not in ValidCharacters.ALL_SYMBOLS):
                return False, f"Invalid symbol at pos {i}"

            if (letter == '('):
                if (not round_empty):
                    round_empty = True
                parentheses_round += 1
            if (letter == ')'):
                if (round_empty):
                    return False, f"Empty parentheses () at pos {i - 1}"
                parentheses_round -= 1
            if (letter == '['):
                if (not square_empty):
                    square_empty = True
                in_square = True
                parentheses_square += 1
            if (letter == ']'):
                if (square_empty):
                    return False, f"Empty parentheses [] at pos {i - 1}"
                in_square = False
                parentheses_square -= 1

            if (letter == ValidCharacters.BACK_SLASH):
                # Check class sign.
                if (len(regex) == i + 1 or
                        regex[i + 1] not in ValidCharacters.CLASS_SYMBOLS):
                    return (False,
                            f"Character {ValidCharacters.BACK_SLASH} "
                            f"not followed by valid class symbol at pos {i}")
            # Check for multiple meta symbols in a row.
            elif (letter in ValidCharacters.META_SYMBOLS and
                  ((len(regex) != i + 1 and
                    regex[i + 1] in ValidCharacters.META_SYMBOLS) or
                   i == 0)):
                return False, f"Repetition meta symbols in a row at pos {i}"

            if (letter in ValidCharacters.META_SYMBOLS and
                    i > 0 and
                    (regex[i - 1] not in ValidCharacters.VALID_SYMBOLS and
                     regex[i - 1] != ')' and regex[i - 1] != ']')):
                return False, f"Invalid use of symbol at pos {i}"

        return (parentheses_square == parentheses_round == 0,
                "Some parentheses are not enclosed")

    def __convert_to_standard_re(self):
        self.regex = self.__convert_to_standard_re_helper(self.regex)[0]

    @staticmethod
    def __convert_to_standard_re_helper(text):
        parenthesis_begin = {}
        i = 0

        while (i < len(text)):
            if (text[i] == '['):
                j = i + 1
                while (text[j] != ']'):
                    j += 1
                pattern = "(" + "+".join(list(text[i + 1: j])) + ")"
                text = (text[: i] +
                        pattern +
                        text[j + 1:])
                parenthesis_begin[i - 1 + len(pattern)] = i
                i = i - 1 + len(pattern)
            elif (text[i] == '('):
                j = i + 1
                num_of_parentheses = 1
                while (num_of_parentheses):
                    if (text[j] == '('):
                        num_of_parentheses += 1
                    if (text[j] == ')'):
                        num_of_parentheses -= 1
                    j += 1
                pattern, par_begs = (
                    RegexIterator.__convert_to_standard_re_helper(
                        text[i + 1: j - 1]))
                for end in par_begs.keys():
                    parenthesis_begin[end + i + 1] = par_begs[end] + i + 1
                text = (text[:i + 1] +
                        pattern +
                        text[j - 1:])
                parenthesis_begin[i + 1 + len(pattern)] = i
                i = i + 1 + len(pattern)
            elif (text[i] == ValidCharacters.ONE_CLOSURE):
                beg_idx = parenthesis_begin.get(i - 1, i - 1)
                if (i - 1 > 0 and text[i - 2] == '\\'):
                    beg_idx -= 1
                pattern = text[beg_idx:i]
                text = (text[: beg_idx] +
                        pattern +
                        pattern +
                        ValidCharacters.STD_KLEENE +
                        text[i + 1:])
                i += len(pattern)
            elif (text[i] == ValidCharacters.ONE_OR_NONE):
                beg_idx = parenthesis_begin.get(i - 1, i - 1)
                pattern = text[beg_idx:i]
                text = (text[: beg_idx] +
                        "(" +
                        pattern +
                        ValidCharacters.STD_SUM +
                        ValidCharacters.STD_EPSILON +
                        ")" +
                        text[i + 1:])
                i = beg_idx + len(pattern) + 3

            i += 1

        return text, parenthesis_begin
