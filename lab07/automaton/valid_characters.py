from dataclasses import dataclass
import string


@dataclass
class ValidCharacters:
    #
    # UNIX regular expression
    #

    # These are valid symbols for regular expression to be matched
    SPACE = ' '
    ANY_SYMBOL = '.'

    DIGITS_SET = set(string.digits)
    ASCII_SET = set(string.ascii_letters)

    VALID_SYMBOLS = (
            ASCII_SET |
            DIGITS_SET |
            {
                SPACE,
                ANY_SYMBOL,
            })

    PARENTHESES = (
            set("()") |  # parentheses for grouping
            set("[]")  # parentheses for
    )

    # These are meta symbols, which describe patterns in
    # valid symbols
    KLEENE_CLOSURE = '*'
    ONE_OR_NONE = '?'
    ONE_CLOSURE = '+'

    META_SYMBOLS = {
        KLEENE_CLOSURE,  # 0 or more repetitions of preceding character
        ONE_OR_NONE,  # 0 or 1 of preceding character
        ONE_CLOSURE,  # 1 or more repetitions of preceding character
    }

    # Symbol for character classes
    BACK_SLASH = '\\'  # \ for \d (for any digit)
    DIGITS = 'd'
    DIGITS_CLASS = r"\d"
    WORD = 'w'
    WORD_CLASS = r"\w"
    ALPHA = 'a'
    ALPHA_CLASS = r"\a"
    CLASS_SYMBOLS = {
        DIGITS,
        WORD,
        ALPHA,
    }

    ALL_SYMBOLS = (VALID_SYMBOLS |
                   PARENTHESES |
                   META_SYMBOLS |
                   CLASS_SYMBOLS |
                   {
                       BACK_SLASH,
                       ANY_SYMBOL,
                   })

    #
    # Standard Regular Expression Symbols
    #

    STD_EPSILON = '?'  # This character simulates epsilon for standard re
    STD_SUM = '+'
    STD_KLEENE = '*'
