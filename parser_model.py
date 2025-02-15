#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CS114B Spring 2021 Programming Assignment 5
Neural Transition-Based Dependency Parsing
Adapted from:
CS224N 2019-20: Homework 3
parser_model.py: Feed-Forward Neural Network for Dependency Parsing
Sahil Chopra <schopra8@stanford.edu>
Haoshen Hong <haoshen@stanford.edu>
"""
import argparse
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

class ParserModel(nn.Module):
    """ Feedforward neural network with an embedding layer and one hidden layer.
    The ParserModel will predict which transition should be applied to a
    given partial parse configuration.

    PyTorch Notes:
        - Note that "ParserModel" is a subclass of the "nn.Module" class. In PyTorch all neural networks
            are a subclass of this "nn.Module".
        - The "__init__" method is where you define all the layers and parameters
            (embedding layers, linear layers, etc.).
        - "__init__" gets automatically called when you create a new instance of your class, e.g.
            when you write "m = ParserModel()".
        - Other methods of ParserModel can access variables that have "self." prefix. Thus,
            you should add the "self." prefix layers, values, etc. that you want to utilize
            in other ParserModel methods.
        - For further documentation on "nn.Module" please see https://pytorch.org/docs/stable/nn.html.
    """
    def __init__(self, embeddings, n_features=36,
        hidden_size=200, n_classes=3):
        """ Initialize the parser model.

        @param embeddings (ndarray): word embeddings (num_words, embedding_size)
        @param n_features (int): number of input features
        @param hidden_size (int): number of hidden units
        @param n_classes (int): number of output classes
        """
        if torch.cuda.is_available():
            print('GPU Available!!!')
            torch.set_default_tensor_type(torch.cuda.FloatTensor)

        super(ParserModel, self).__init__()
        self.n_features = n_features
        self.n_classes = n_classes
        self.embed_size = embeddings.shape[1]
        self.hidden_size = hidden_size
        self.embeddings = nn.Parameter(torch.tensor(embeddings))

        # Note: Trainable variables are declared as `nn.Parameter` which is a commonly used API
        #   to include a tensor into a computational graph to support updating w.r.t its gradient.
        #   Here, we use Xavier Uniform Initialization for our Weight initialization.
        #   It has been shown empirically, that this provides better initial weights
        #   for training networks than random uniform initialization.
        #   For more details checkout this great blogpost:
        #             http://andyljones.tumblr.com/post/110998971763/an-explanation-of-xavier-initialization

        # Please see the following docs for more:
        #   nn.Parameter: https://pytorch.org/docs/stable/generated/torch.nn.parameter.Parameter.html
        #   Initialization: https://pytorch.org/docs/stable/nn.init.html

        # create a parameter matrix (weights and bias) for the hidden layer
        embed_to_hidden = torch.empty(self.n_features * self.embed_size + 1, self.hidden_size)
        # initialize parameters with the `nn.init.xavier_uniform_` function with default parameters
        nn.init.xavier_uniform_(embed_to_hidden)
        # declare `self.embed_to_hidden_weight` as `nn.Parameter` with this as its data
        self.embed_to_hidden_weight = nn.Parameter(embed_to_hidden)
        # create a parameter matrix (weights and bias) for the output layer
        hidden_to_logits = torch.empty(self.hidden_size + 1, self.n_classes)
        # initialize parameters with the `nn.init.xavier_uniform_` function with default parameters
        nn.init.xavier_uniform_(hidden_to_logits)
        # declare `self.hidden_to_logits_weight` as `nn.Parameter` with this as its data
        self.hidden_to_logits_weight = nn.Parameter(hidden_to_logits)

    def embedding_lookup(self, w):
        """ Utilize `w` to select embeddings from embedding matrix `self.embeddings`
            @param w (Tensor): input tensor of word indices (batch_size, n_features)

            @return x (Tensor): tensor of embeddings for words represented in w
                                (batch_size, n_features * embed_size)
        """

        x = None
        ### YOUR CODE HERE (~1-3 Lines)
        ### TODO:
        ###     1) For each index `i` in `w`, select `i`th vector from self.embeddings
        ###     2) Reshape the tensor if necessary
        ###
        ### Note: All embedding vectors are stacked and stored as a matrix. The model receives
        ###       a list of indices representing a sequence of words, then it calls this lookup
        ###       function to map indices to sequence of embeddings.
        ###
        ###       This problem aims to test your understanding of embedding lookup,
        ###       so DO NOT use any high level API like nn.Embedding
        ###       (we are asking you to implement that!). Pay attention to tensor shapes
        ###       and reshape if necessary. Make sure you know each tensor's shape before you run the code!
        w_initial_shape = w.shape
        if torch.cuda.is_available():
            w = w.view(-1).to('cuda')
        else:
            w = w.view(-1)
        x = self.embeddings.index_select(0, w)
        x = x.view(w_initial_shape[0],  w_initial_shape[1] * self.embed_size)


        ### END YOUR CODE
        return x


    def forward(self, w):
        """ Run the model forward.

            Note that we will not apply the softmax function here because it is included in the loss function nn.CrossEntropyLoss

            PyTorch Notes:
                - Every nn.Module object (PyTorch model) has a `forward` function.
                - When you apply your nn.Module to an input tensor `w` this function is applied to the tensor.
                    For example, if you created an instance of your ParserModel and applied it to some `w` as follows,
                    the `forward` function would called on `w` and the result would be stored in the `output` variable:
                        model = ParserModel()
                        output = model(w) # this calls the forward function
                - For more details checkout: https://pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.forward

        @param w (Tensor): input tensor of tokens (batch_size, n_features)

        @return logits (Tensor): tensor of predictions (output after applying the layers of the network)
                                 without applying softmax (batch_size, n_classes)
        """
        
        logits = None
        ### YOUR CODE HERE (~3-5 lines)
        ### TODO:
        ###     Complete the forward computation as described in write-up.
        ###
        ### Note: We do not apply the softmax to the logits here, because
        ### the loss function (torch.nn.CrossEntropyLoss) applies it more efficiently.
        ###
        ### Please see the following docs for support:
        ###     Matrix product: https://pytorch.org/docs/stable/torch.html#torch.matmul
        ###     ReLU: https://pytorch.org/docs/stable/generated/torch.nn.ReLU.html#torch.nn.ReLU

        ### 1. Create the embedding vector with a one at the end of each row
        ### 2. Calculate the product of the embedding vector and the input weights
        ### 3. Apply ReLU activation to this
        ### 4. Multiply this by the hidden layer weights to get logits

        x = self.embedding_lookup(w)
        x_with_one_at_end = torch.cat((x, torch.ones(x.shape[0], 1)), dim=1)
        embedding_vector_and_input_weights = x_with_one_at_end@self.embed_to_hidden_weight
        m = nn.ReLU()
        h = m(embedding_vector_and_input_weights)
        h_with_one_at_end = torch.cat((h, torch.ones(h.shape[0], 1)), dim=1)
        logits = h_with_one_at_end@self.hidden_to_logits_weight

        ### END YOUR CODE
        return logits
        
    def check_embedding(self):
        passed = True
        inds = torch.randint(0, 100, (4, 36), dtype=torch.long)
        selected = self.embedding_lookup(inds)
        try:
            assert torch.all(selected.data == 0)
        except AssertionError:
            print("The result of embedding lookup: " \
                                      + repr(selected) + " contains non-zero elements.")
            passed = False
        except AttributeError:
            if selected is None:
                print("The result of embedding lookup is None")
                passed = False
        return passed

    def check_forward(self):
        passed = True
        inputs = torch.randint(0, 100, (4, 36), dtype=torch.long)
        out = self(inputs)
        expected_out_shape = (4, 3)
        try:
            assert out.shape == expected_out_shape
        except AssertionError:
            print("The result shape of forward is: " + repr(out.shape) + \
                                                " which doesn't match expected " + repr(expected_out_shape))
            passed = False
        except AttributeError:
            print("The result of forward is None")
            passed = False
        return passed


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Simple sanity check for parser_model.py')
    parser.add_argument('-e', '--embedding', action='store_true', help='sanity check for embeding_lookup function')
    parser.add_argument('-f', '--forward', action='store_true', help='sanity check for forward function')
    args = parser.parse_args()

    embeddings = np.zeros((100, 30), dtype=np.float32)
    model = ParserModel(embeddings)

    if args.embedding:
        if (model.check_embedding()):
            print("Embedding_lookup sanity check passes!")

    if args.forward:
        if (model.check_forward()):
            print("Forward sanity check passes!")
