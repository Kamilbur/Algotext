from collections import defaultdict
from copy import deepcopy
from math import log
from queue import Queue

import netgraph as ng
import networkx as nx
from matplotlib.lines import Line2D
from termcolor import colored

from .regex_iterator import RegexIterator
from .state import State
from .valid_characters import ValidCharacters


class Automaton:
    """ Non-deterministic Finite Automaton for Pattern matching.
    """
    VIS_INITIAL_COLOUR = "mediumturquoise"
    VIS_FINAL_COLOUR = "crimson"

    def __init__(self, letter):
        """ Initialization of basic automaton for one letter matching.
        """
        self.initial = State()
        self.final = State()
        self.initial[letter] = self.final

        # For visualization.
        self.enumeration_proper = False

    def star(self):
        """ Kleene star of automaton.
        """
        return Automaton.__perform_star(self)

    def __mul__(self, other):
        """ Concatenation of 2 automatons.
        """
        return Automaton.__perform_concatenation(self, other)

    def __imul__(self, other):
        """ Concatenation of 2 automatons.
        """
        return Automaton.__perform_concatenation(self, other, copy_fst=False)

    def __add__(self, other):
        """ Alternative of 2 automatons.
        """
        return Automaton.__perform_alternative(self, other)

    def __iadd__(self, other):
        return Automaton.__perform_alternative(self, other, copy_fst=False)

    @staticmethod
    def __perform_star(automaton, copy=True):
        """ Automatons Kleene star.

        Important Note:
            It is build upon a automaton1 and automaton2, so not copying
            should be avoided, due to the fact that arguments are
            passed by reference and these objects are endangered by unwanted
            mutation. Option of not copying is left for implementation
            purposes.

        :param automaton: (Automaton obj)
            First automaton.
        :param copy: (boolean)
            If True, then automaton will be deepcopied.
        :return: (Automaton obj)
            Automaton being an Kleene star of arguments automatons.
        """
        automaton = deepcopy(automaton) if (copy) else automaton

        old_initial = automaton.initial
        old_final = automaton.final
        automaton.initial = State()
        automaton.final = State()
        automaton.initial[State.EPSILON] = old_initial
        automaton.initial[State.EPSILON] = automaton.final
        old_final[State.EPSILON] = automaton.initial
        old_final[State.EPSILON] = automaton.final

        # Mark enumeration as possibly improper.
        automaton.enumeration_proper = False
        return automaton

    @staticmethod
    def __perform_concatenation(aut1, aut2, copy_fst=True, copy_snd=True):
        """ Automatons concatenation.

        Important Note:
            It is build upon a automaton1 and automaton2, so not copying
            should be avoided, due to the fact that arguments are
            passed by reference and these objects are endangered by unwanted
            mutation. Option of not copying is left for implementation
            purposes.

        :param aut1: (Automaton obj)
            First automaton.
        :param aut2: (Automaton obj)
            Second automaton.
        :param copy_fst: (boolean)
            If True, then aut1 will be deepcopied.
        :param copy_snd: (boolean)
            If True, then aut2 will be deepcopied.
        :return: (Automaton obj)
            Automaton being an concatenation of arguments automatons.
        """

        automaton1 = deepcopy(aut1) if (copy_fst) else aut1
        automaton2 = deepcopy(aut2) if (copy_snd) else aut2
        automaton1.final[State.EPSILON] = automaton2.initial
        automaton1.final = automaton2.final

        # Resulting automaton is automaton number 1.
        # Mark enumeration as possibly improper.
        automaton1.enumeration_proper = False

        return automaton1

    @staticmethod
    def __perform_alternative(aut1, aut2, copy_fst=True, copy_snd=True):
        """ Automatons alternative.

        Important Note:
            It is build upon a automaton1 and automaton2, so not copying
            should be avoided, due to the fact that arguments are
            passed by reference and these objects are endangered by unwanted
            mutation. Option of not copying is left for implementation
            purposes.

        :param aut1: (Automaton obj)
            First automaton.
        :param aut2: (Automaton obj)
            Second automaton.
        :param copy_fst: (boolean)
            If True, then aut1 will be deepcopied. In the other case,
            the object aut1 is likely to change, as it is passed by
            reference.
        :param copy_snd: (boolean)
            If True, then aut2 will be deepcopied. In the other case,
            the object aut2 is likely to change, as it is passed by
            reference.
        :return: (Automaton obj)
            Automaton being an alternative of arguments automatons.
        """

        # Copy automatons
        automaton1 = deepcopy(aut1) if (copy_fst) else aut1
        automaton2 = deepcopy(aut2) if (copy_snd) else aut2

        old_initial = automaton1.initial
        old_final = automaton1.final
        automaton1.initial = State()
        automaton1.final = State()
        automaton1.initial[State.EPSILON] = old_initial
        automaton1.initial[State.EPSILON] = automaton2.initial
        old_final[State.EPSILON] = automaton1.final
        automaton2.final[State.EPSILON] = automaton1.final

        # Resulting automaton is automaton number 1.
        # Mark enumeration as possibly improper.
        automaton1.enumeration_proper = False

        return automaton1

    def draw(self, ax, legend=True, title="", edge_label_size=10,
             show_node_labels=False, node_label_font_size=12.0):
        """ Draw the automaton.

        Important Note:
            Try select right size of the figure for the ax to
            assure readability of the picture.
        Note:
            This can be very buggy and edges can have tendency to cross and
            cover others labels. Try to run it multiple times if this
            problem appears, yet it is not guaranteed this procedure
            will solve it.

        Examples:
          - This code draws automaton for regular expression ab*a. Note that
            size of the matplotlib figure can be changed, usually by
            figsize parameter. Often it is necessary to make the figure bigger
            to make it clear and readable.

            Matplotlib import:

            >>> import matplotlib.pyplot as plt

            Build automaton:

            >>> automaton = Automaton.build_from_regex("ab*a")

            Create pyplot figure and Axes object:

            >>> fig, ax = plt.subplots(1, figsize=(10, 10))

            Draw automaton:

            >>> automaton.draw(ax, title="Example automaton")
            >>> plt.show()

        :param show_node_labels: (boolean)
        :param node_label_font_size: (float)
        :param edge_label_size: (float)
        :param legend: (boolean)
            If True display legend.
        :param title: (str)
            Make this string the title of plot.
        :param ax: (matplotlib Axes obj)
            Axes to draw the automaton in.
        """
        graph = nx.DiGraph()
        if (not self.enumeration_proper):
            self.__bfs_enumerate()

        node_labels, edge_labels = self.__bfs_for_draw(graph)
        initial_pos = {self.initial.idx: (0, 0), self.final.idx: (1, 0)}
        pos = ng.spring_layout(graph.edges, pos=initial_pos, fixed=initial_pos,
                               iterations=2000)
        ng.draw(graph, node_positions=pos, ax=ax)

        # Simple heuristic for node label font size. Size of label is dependant
        # on the number of digits of the maximal number of states f.e.
        # if there are states from 0 to 15, the size of the font must decrease
        # to make possible for label to be inside the
        node_label_font_size /= (int(log(len(node_labels), 10) ** 2) + 1)
        if (show_node_labels):
            ng.draw_node_labels(node_labels=node_labels, node_positions=pos,
                                node_label_font_size=node_label_font_size,
                                ax=ax)

        ng.draw_nodes(graph=graph,
                      node_positions={self.initial.idx: pos[self.initial.idx]},
                      node_color=Automaton.VIS_INITIAL_COLOUR, ax=ax)

        ng.draw_nodes(graph=graph,
                      node_positions={self.final.idx: pos[self.final.idx]},
                      node_color=Automaton.VIS_FINAL_COLOUR, ax=ax)

        ng.draw_edge_labels(graph.edges, node_positions=pos,
                            edge_labels=edge_labels,
                            edge_label_font_size=edge_label_size,
                            ax=ax)

        if (title):
            ax.set(title=title)
        if (legend):
            self.__show_legend(ax)

    @staticmethod
    def __show_legend(ax):
        """ Make legend for a drawing of automaton.

        This solution is tricky: Make invisible lines with appropriate legend
        and put it onto the canvas. Also the size of the plot is shrunk
        to prevent legend from covering the graph.

        :param ax: (matplotlib Axes obj)
            Axes to draw the legend on.
        """
        legend_initial = Line2D(range(1), range(0),
                                markerfacecolor=Automaton.VIS_INITIAL_COLOUR,
                                markeredgecolor="black",
                                marker='o',
                                linewidth=0,
                                )
        legend_final = Line2D(range(1), range(0),
                              markerfacecolor=Automaton.VIS_FINAL_COLOUR,
                              markeredgecolor="black",
                              marker='o',
                              linewidth=0
                              )
        # Change size of an axes object to make legend not cover the graph.
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                         box.width, box.height * 0.9])

        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05),
                  fancybox=True, shadow=False, ncol=5,
                  handles=[legend_initial, legend_final],
                  labels=["initial", "final"])

    def __bfs_enumerate(self):
        """ Enumerate states.

        Note:
             Enumeration is necessary for drawing.
        """
        visited = defaultdict(lambda: False)
        visited[self.initial] = True
        global_idx = 1
        queue = Queue()
        queue.put((self.initial, 0))
        self.initial.idx = 0

        # Enumerate all states with unique index.
        while (not queue.empty()):
            node, dist = queue.get()

            for label in node.keys():
                trans_list = node[label]
                for nbh in trans_list:
                    if (not visited[nbh]):
                        visited[nbh] = True
                        nbh.idx = global_idx
                        global_idx += 1
                        queue.put((nbh, dist + 1))

        # Mark enumeration as proper one.
        self.enumeration_proper = True

    def __bfs_for_draw(self, graph):
        visited = defaultdict(lambda: False)
        visited[self.initial] = True
        queue = Queue()
        queue.put(self.initial)
        edge_labels = {}
        node_labels = {}

        while (not queue.empty()):
            node = queue.get()
            graph.add_node(node.idx)
            node_labels[node.idx] = node.idx

            for label in node.keys():
                trans_list = node[label]
                for nbh in trans_list:
                    if (label == State.EPSILON):
                        edge_label = r"$\epsilon$"
                    else:
                        edge_label = label
                    edge_labels[(node.idx, nbh.idx)] = edge_label
                    graph.add_edge(node.idx, nbh.idx)
                    if (not visited[nbh]):
                        visited[nbh] = True
                        queue.put(nbh)

        return node_labels, edge_labels

    def __bfs_generator(self):
        visited = defaultdict(lambda: False)
        visited[self.initial] = True

        queue = Queue()
        queue.put(self.initial)

        while (not queue.empty()):
            node = queue.get()
            yield node

            for label in node.keys():
                trans_list = node[label]
                for nbh in trans_list:
                    if (not visited[nbh]):
                        queue.put(nbh)
                        visited[nbh] = True

    @classmethod
    def build_from_regex(cls, regex: str, check_correctness=True):
        """ Build new automaton from string with regular expression.

        :param regex: (str)
        :param check_correctness: (boolean)
        :return: (Automaton obj)
        """
        regex = RegexIterator(regex)
        iter(regex)
        regex.next_char()
        automaton = cls.__expr(regex)
        if (check_correctness and not automaton.__is_acyclic()):
            raise Exception("Automaton has an epsilon cycle. That makes "
                            "it impossible to simulate with this particular "
                            "implementation.")
        return automaton

    @classmethod
    def __expr(cls, regex):
        automaton = cls.__term(regex)

        while (regex.char == ValidCharacters.STD_SUM):
            regex.next_char()
            automaton = cls.__perform_alternative(automaton, cls.__term(regex),
                                                  copy_fst=False,
                                                  copy_snd=False)

        return automaton

    @classmethod
    def __term(cls, regex):
        automaton = cls.__factor(regex)
        while (regex.char in ValidCharacters.VALID_SYMBOLS or
               regex.char == '(' or
               regex.char == '\\'):
            automaton = cls.__perform_concatenation(automaton,
                                                    cls.__factor(regex),
                                                    copy_fst=False,
                                                    copy_snd=False)

        return automaton

    @classmethod
    def __factor(cls, regex):
        if (regex.char == ValidCharacters.BACK_SLASH):
            letter = regex.char
            regex.next_char()
            letter += regex.char
            automaton = Automaton(letter=letter)
            regex.next_char()
        elif (regex.char == ValidCharacters.STD_EPSILON):
            automaton = Automaton(letter=State.EPSILON)
            regex.next_char()
        elif (regex.char in ValidCharacters.VALID_SYMBOLS):
            # Elementary expression automaton
            automaton = Automaton(letter=regex.char)
            regex.next_char()
        elif (regex.char == '('):
            regex.next_char()
            automaton = cls.__expr(regex)
            if (regex.char == ')'):
                regex.next_char()
        else:
            raise Exception
        if (regex.char == ValidCharacters.STD_KLEENE):
            automaton = cls.__perform_star(automaton, copy=False)
            regex.next_char()

        return automaton

    @staticmethod
    def __closure(state_dict):
        queue = Queue()
        for state in state_dict.keys():
            queue.put(state)

        while (not queue.empty()):
            state = queue.get()
            indexes_set = state_dict[state]

            if (State.EPSILON in state):
                for next_state in state[State.EPSILON]:
                    if (next_state not in state_dict):
                        state_dict[next_state] = indexes_set
                        queue.put(next_state)
                    else:
                        new_indexes = state_dict[next_state].union(indexes_set)
                        state_dict[next_state] = new_indexes
                        queue.put(next_state)

        return state_dict

    @staticmethod
    def __trans(state_dict, letter):
        result_dict = {}

        for state in state_dict.keys():
            indexes_set = state_dict[state]
            alternative_letter = letter
            if (ValidCharacters.ANY_SYMBOL in state):
                letter = ValidCharacters.ANY_SYMBOL
            if (ValidCharacters.DIGITS_CLASS in state and
                    letter in ValidCharacters.DIGITS_SET):
                alternative_letter = ValidCharacters.DIGITS_CLASS
            if (ValidCharacters.WORD_CLASS in state and
                    (letter in ValidCharacters.DIGITS_CLASS or
                     letter in ValidCharacters.ASCII_SET)):
                alternative_letter = ValidCharacters.WORD_CLASS
            if (ValidCharacters.ALPHA_CLASS in state and
                    letter in ValidCharacters.ASCII_SET):
                alternative_letter = ValidCharacters.ALPHA_CLASS

            if (alternative_letter in state):
                for new_state in state[alternative_letter]:
                    if (new_state in result_dict):
                        new_indexes = result_dict[new_state].union(indexes_set)
                        result_dict[new_state] = new_indexes
                    else:
                        result_dict[new_state] = indexes_set

        return result_dict

    def test_word(self, word):
        state_dict = Automaton.__closure({self.initial: {0}})

        for letter in word:
            trans_dict = Automaton.__trans(state_dict, letter)
            state_dict = Automaton.__closure(trans_dict)

        return self.final in state_dict

    def __matching(self, text):
        """ Helper procedure to match a pattern given by regular expression.

        :param text: (str)
            Text to search pattern in.
        :return: (dict)
            Dictionary, which keys are start indices of found subwords and
            values are respectively end indices of the given subword.
        """
        state_dict = Automaton.__closure({self.initial: {-1}})
        occurrences = {}

        for i, letter in enumerate(text):
            trans_dict = Automaton.__trans(state_dict, letter)

            if (self.initial in trans_dict):
                trans_dict[self.initial] = trans_dict[self.initial].union({i})
            else:
                trans_dict[self.initial] = {i}
            state_dict = Automaton.__closure(trans_dict)

            if (self.final in state_dict):
                start_idx = min(state_dict[self.final])
                word_to_test = text[start_idx + 1: i + 1]
                if (word_to_test and self.test_word(word_to_test)):
                    occurrences[start_idx + 1] = i + 1

        return occurrences

    @staticmethod
    def __highlight_found(text, occurrences, color, attrs):
        """ Mark parts of text specified by occurrences.

        It uses termcolor package(which assures portability between Windows
        and Unix) to highlight given parts of the text.

        :param text: (str)
            String with text to highlight found occurrences in.
        :param occurrences: (dict)
            Dictionary, which keys are start indices of subwords and
            values are respectively end indices of the given subword to
            highlight.
        :return: (str)
            String with special sequences of escapes codes, that notify
            where the occurrence was present in the text.
        """
        processed_text = ""
        rest_of_text = text
        beginning = 0

        for start_idx in sorted(occurrences.keys()):
            end_idx = occurrences[start_idx]

            # This condition deals with intersecting occurrences intervals
            if (start_idx < beginning):
                start_idx = beginning

            colored_pattern = colored(text[start_idx: end_idx],
                                      color=color, attrs=attrs)
            processed_text += text[beginning: start_idx] + colored_pattern
            rest_of_text += text[end_idx:]
            beginning = end_idx
        processed_text += text[beginning:]

        return processed_text

    def matching(self, text, verbose=True, **kwargs):
        """ Regular expression matching.

        :param verbose: (boolean)
            Show text with highlighted found words.
        :param text: (str)
            Text to search pattern in.
        :param **color: (str)
            kwargs for termcolor package colored function.
        :param **attrs: (list)
            kwargs for termcolor package colored function.
        :return: (dict)
            Dictionary, which keys are start indices of found subwords and
            values are respectively end indices of the given subword.
        """
        occurrences = self.__matching(text)

        if (verbose):
            color = kwargs["color"] if ("color" in kwargs) else "blue"
            attrs = kwargs["attrs"] if ("attrs" in kwargs) else ["underline"]
            text_result = Automaton.__highlight_found(text,
                                                      occurrences,
                                                      color=color,
                                                      attrs=attrs)
            # Print colored text.
            print(text_result)

        return [(start, occurrences[start]) for start in occurrences.keys()]

    def __is_acyclic(self):
        processed = set()
        visited = set()
        for node in self.__bfs_generator():
            if (node not in processed):
                if (Automaton.__has_epsilon_cycle(node, visited, processed)):
                    return False
        return True

    @staticmethod
    def __has_epsilon_cycle(node, visited, processed):
        neighbours = node.get(State.EPSILON, [])

        visited.add(node)
        for nbh in neighbours:
            if (nbh not in processed):
                if (nbh in visited):
                    return True
                elif (nbh not in visited):
                    if (Automaton.__has_epsilon_cycle(nbh,
                                                      visited, processed)):
                        return True
                    visited.add(nbh)

        processed.add(node)

        return False
