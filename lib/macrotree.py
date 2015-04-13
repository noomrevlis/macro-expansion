#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-
import copy

class BinaryTreeNode:
    def __init__(self, data, left, right,parent):
        self.left = left
        self.right = right
        self.parent = parent
        self.macro = data  # [defs[], undefs[]]

    def __str__(self):
        return str(self)

    def get_macro(self):
        return self.macro

    def insert_node(self, pos, node):
        if pos == 'left':
            self.left = node
        elif pos == 'right':
            self.right = node
        else:
            raise Exception('invalid insert position!')

class BinaryTree:
    def __init__(self):
        self.root = None

    def build_tree(self, node):
        self.root = node

    def is_empty(self):
        if self.root is None:
            return True
        else:
            return False

    def find_leaf(self, node):
        # Recursion Base
        if node is None:
            return []
        if node.left == None and node.right == None:
            return [node]

        # Recursion Step
        leafs = []
        leafs += self.find_leaf(node.left)
        leafs += self.find_leaf(node.right)
        return leafs

