#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CS114B Spring 2021 Programming Assignment 5
Neural Transition-Based Dependency Parsing
Adapted from:
CS224N 2019-20: Homework 3
parser_transitions.py: Algorithms for completing partial parsess.
Sahil Chopra <schopra8@stanford.edu>
Haoshen Hong <haoshen@stanford.edu>
"""
import sys

class PartialParse(object):
    def __init__(self, sentence):
        """Initializes this partial parse.

        @param sentence (list of str): The sentence to be parsed as a list of words.
        """
        # The sentence being parsed is kept for bookkeeping purposes.
        self.sentence = sentence

        # Initializes:
        #   self.stack: The current stack represented as a list with the top of the
        #       stack as the last element of the list.
        #   self.buffer: The current buffer represented as a list with the first
        #       item on the buffer as the first item of the list
        #   self.dependencies: The list of dependencies produced so far.
        #       Represented as a list of tuples where each tuple is of the form
        #       (head, dependent).
        # The root token is be represented with the string "ROOT"

        self.stack = ['ROOT']
        self.buffer = sentence[:]
        self.dependencies = []

    def parse_step(self, transition):
        """Performs a single parse step by applying the given transition to this partial parse

        @param transition (str): A string that equals "S", "LA", or "RA" representing the shift,
                                 left-arc, and right-arc transitions. You can assume the provided
                                 transition is a legal transition.
        """
        ### YOUR CODE HERE (~7 Lines)
        ### TODO:
        ###     Fill in the "if" statements to implement a single parsing step, i.e. the logic for the
        ###         following as described in the pdf handout:
        ###     1. Shift
        ###     2. Left Arc
        ###     3. Right Arc

        if transition == 'S':
            self.stack.append(self.buffer.pop(0))
        elif transition == 'LA':
            first_item_on_stack = self.stack[-1]
            second_item_on_stack_removed = self.stack.pop(-2)
            self.dependencies.append((first_item_on_stack, second_item_on_stack_removed))
        elif transition == 'RA':
            second_item_on_stack = self.stack[-2]
            first_item_on_stack_removed = self.stack.pop(-1)
            self.dependencies.append((second_item_on_stack, first_item_on_stack_removed))

        ### END YOUR CODE

    def parse(self, transitions):
        """Applies the provided transitions to this PartialParse

        @param transitions (list of str): The list of transitions in the order they should be applied

        @return dependencies (list of string tuples): The list of dependencies produced when
                                                      parsing the sentence. Represented as a list of
                                                      tuples where each tuple is of the form (head, dependent).
        """
        for transition in transitions:
            self.parse_step(transition)
        return self.dependencies


def minibatch_parse(sentences, model, batch_size):
    """Parses a list of sentences in minibatches using a model.

    @param sentences (list of list of str): A list of sentences to be parsed
                                            (each sentence is a list of words and each word is of type string)
    @param model (ParserModel): The model that makes parsing decisions. It is assumed to have a function
                                model.predict(partial_parses) that takes in a list of PartialParses as input and
                                returns a list of transitions predicted for each parse. That is, after calling
                                    transitions = model.predict(partial_parses)
                                transitions[i] will be the next transition to apply to partial_parses[i].
    @param batch_size (int): The number of PartialParses to include in each minibatch


    @return dependencies (list of dependency lists): A list where each element is the dependencies
                                                     list for a parsed sentence. Ordering should be the
                                                     same as in sentences (i.e., dependencies[i] should
                                                     contain the parse for sentences[i]).
    """
    dependencies = []

    ### YOUR CODE HERE (~8-10 Lines)
    ### TODO:
    ###     Implement the minibatch parse algorithm as described in the pdf handout
    ###
    ###     Note: A shallow copy (as denoted in the PDF) can be made with the "=" sign in python, e.g.
    ###                 unfinished_parses = partial_parses[:].
    ###             Here `unfinished_parses` is a shallow copy of `partial_parses`.
    ###             In Python, a shallow copied list like `unfinished_parses` does not contain new instances
    ###             of the object stored in `partial_parses`. Rather both lists refer to the same objects.
    ###             In our case, `partial_parses` contains a list of partial parses. `unfinished_parses`
    ###             contains references to the same objects. Thus, you should NOT use the `del` operator
    ###             to remove objects from the `unfinished_parses` list. This will free the underlying memory that
    ###             is being accessed by `partial_parses` and may cause your code to crash.

    partial_parses = [PartialParse(sentence) for sentence in sentences]
    unfinished_parses = partial_parses[:]
    
    while len(unfinished_parses) != 0:
        minibatch = unfinished_parses[:batch_size]
        transitions = model.predict(minibatch)
        for i in range(len(minibatch)):
            minibatch[i].parse_step(transitions[i])        
            # if len(minibatch[i].buffer) == 0 and len(minibatch[i].stack) == 1:
                # unfinished_parses.pop(i)
            unfinished_parses = [parse for parse in unfinished_parses if not (len(parse.stack) == 1 and len(parse.buffer) == 0)]
    
    dependencies = [partial_parse.dependencies for partial_parse in partial_parses]

    ### END YOUR CODE

    return dependencies


def test_step(name, transition, stack, buf, deps,
              ex_stack, ex_buf, ex_deps):
    """Tests that a single parse step returns the expected output"""
    passed = True
    pp = PartialParse([])
    pp.stack, pp.buffer, pp.dependencies = stack, buf, deps

    pp.parse_step(transition)
    stack, buf, deps = (tuple(pp.stack), tuple(pp.buffer), tuple(sorted(pp.dependencies)))
    try:
        assert stack == ex_stack
    except AssertionError:
        print("{:} test resulted in stack {:}, expected {:}".format(name, stack, ex_stack))
        passed = False
    
    try:
        assert buf == ex_buf
    except AssertionError:
        print("{:} test resulted in stack {:}, expected {:}".format(name, stack, ex_stack))
        passed = False
            
    try:
        assert deps == ex_deps
    except AssertionError:
        print("{:} test resulted in dependency list {:}, expected {:}".format(name, deps, ex_deps))
        passed = False
    
    if passed:
        print("{:} test passed!".format(name))
    return passed


def test_parse_step():
    """Simple tests for the PartialParse.parse_step function
    Warning: these are not exhaustive
    """
    if (test_step("SHIFT", "S", ["ROOT", "the"], ["cat", "sat"], [],
              ("ROOT", "the", "cat"), ("sat",), ()) and \
    test_step("LEFT-ARC", "LA", ["ROOT", "the", "cat"], ["sat"], [],
              ("ROOT", "cat",), ("sat",), (("cat", "the"),)) and \
    test_step("RIGHT-ARC", "RA", ["ROOT", "run", "fast"], [], [],
              ("ROOT", "run",), (), (("run", "fast"),))):
        return True


def test_parse():
    """Simple tests for the PartialParse.parse function
    Warning: these are not exhaustive
    """
    passed = True
    sentence = ["parse", "this", "sentence"]
    dependencies = PartialParse(sentence).parse(["S", "S", "S", "LA", "RA", "RA"])
    dependencies = tuple(sorted(dependencies))
    expected = (('ROOT', 'parse'), ('parse', 'sentence'), ('sentence', 'this'))
    
    try:
        assert dependencies == expected
    except AssertionError:
        print("parse test resulted in dependencies {:}, expected {:}".format(dependencies, expected))
        passed = False
        
    try:
        assert tuple(sentence) == ("parse", "this", "sentence")
    except AssertionError:
        print("parse test failed: the input sentence should not be modified")
        passed = False
    
    if passed:
        print("parse test passed!")
    return passed
    

class DummyModel(object):
    """Dummy model for testing the minibatch_parse function
    """
    def __init__(self, mode = "unidirectional"):
        self.mode = mode

    def predict(self, partial_parses):
        if self.mode == "unidirectional":
            return self.unidirectional_predict(partial_parses)
        elif self.mode == "interleave":
            return self.interleave_predict(partial_parses)
        else:
            raise NotImplementedError()

    def unidirectional_predict(self, partial_parses):
        """First shifts everything onto the stack and then does exclusively right arcs if the first word of
        the sentence is "right", "left" if otherwise.
        """
        return [("RA" if pp.stack[1] is "right" else "LA") if len(pp.buffer) == 0 else "S"
                for pp in partial_parses]

    def interleave_predict(self, partial_parses):
        """First shifts everything onto the stack and then interleaves "right" and "left".
        """
        return [("RA" if len(pp.stack) % 2 == 0 else "LA") if len(pp.buffer) == 0 else "S"
                for pp in partial_parses]


def test_dependencies(name, deps, ex_deps):
    """Tests the provided dependencies match the expected dependencies"""
    deps = tuple(sorted(deps))
    try:
        assert deps == ex_deps
        return True
    except AssertionError:
        print("{:} test resulted in dependency list {:}, expected {:}".format(name, deps, ex_deps))
        return False


def test_minibatch_parse():
    """Simple tests for the minibatch_parse function
    Warning: these are not exhaustive
    """

    passed = True

    # Unidirectional arcs test
    sentences = [["right", "arcs", "only"],
                 ["right", "arcs", "only", "again"],
                 ["left", "arcs", "only"],
                 ["left", "arcs", "only", "again"]]
    deps = minibatch_parse(sentences, DummyModel(), 2)
    if len(deps) > 0:
        if test_dependencies("minibatch_parse", deps[0],
                          (('ROOT', 'right'), ('arcs', 'only'), ('right', 'arcs'))) and \
        test_dependencies("minibatch_parse", deps[1],
                          (('ROOT', 'right'), ('arcs', 'only'), ('only', 'again'), ('right', 'arcs'))) and \
        test_dependencies("minibatch_parse", deps[2],
                          (('only', 'ROOT'), ('only', 'arcs'), ('only', 'left'))) and \
        test_dependencies("minibatch_parse", deps[3],
                          (('again', 'ROOT'), ('again', 'arcs'), ('again', 'left'), ('again', 'only'))):
            print("unidirectional arcs tests passed!")
    else:
        print("minibatch_parse returned empty deps {:}".format(deps))
        passed = False
        
    # Out-of-bound test
    sentences = [["right"]]
    deps = minibatch_parse(sentences, DummyModel(), 2)
    if len(deps) > 0:
        if test_dependencies("minibatch_parse", deps[0], (('ROOT', 'right'),)):
            print("out-of-bound test passed!")
    else:
        print("minibatch_parse returned empty deps {:}".format(deps))
        passed = False

    # Mixed arcs test
    sentences = [["this", "is", "interleaving", "dependency", "test"]]
    deps = minibatch_parse(sentences, DummyModel(mode="interleave"), 1)
    if len(deps) > 0:
        if test_dependencies("minibatch_parse", deps[0], \
            (('ROOT', 'is'), ('dependency', 'interleaving'), \
            ('dependency', 'test'), ('is', 'dependency'), ('is', 'this'))):
            print("mixed arcs test passed!")
            print("minibatch_parse test passed!")
    else:
        print("minibatch_parse returned empty deps {:}".format(deps))
        passed = False
    return passed


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        raise Exception("You did not provide a valid keyword. Either provide 'part_c' or 'part_d', when executing this script")
    elif args[1] == "part_a":
        test_parse_step()
        test_parse()
    elif args[1] == "part_b":
        test_minibatch_parse()
    else:
        raise Exception("You did not provide a valid keyword. Either provide 'part_c' or 'part_d', when executing this script")
