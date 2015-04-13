#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-

import copy
from .macrotree import BinaryTree, BinaryTreeNode

def expand_macro_snippet(macro_snippet, defs, undefs):
    keywords = ('if', 'ifdef', 'ifndef', 'else', 'endif')
    is_contained = 1
    stack = []
    expanded_snippet = []
    macro_snippet_reverse = copy.deepcopy(macro_snippet)
    macro_snippet_reverse.reverse()
    while 1:
        if not macro_snippet_reverse: break
        line = macro_snippet_reverse.pop()
        while line[-2:] == '\\\n': # blank lines
            nextline = macro_snippet_reverse.pop()
            if not nextline: break
            line = line + nextline
        tmp = line.strip()
        if tmp[:1] != '#':
            if is_contained: expanded_snippet.append(line)
            continue
        tmp = tmp[1:].strip()
        words = tmp.split()
        keyword = words[0]
        if keyword not in keywords:
            if is_contained: expanded_snippet.append(line)
            continue
        #if keyword in ('ifdef', 'ifndef') and len(words) == 2: 
        if keyword in ('ifdef', 'ifndef'):  # fix the issue of comments //
            if keyword == 'ifdef':
                is_keyword_ifdef = 1
            else:
                is_keyword_ifdef = 0
            word = words[1]
            if word in defs:
                # Push current status in stack
                stack.append((is_contained, is_keyword_ifdef, word))
                if not is_keyword_ifdef: is_contained = 0
            elif word in undefs:
                stack.append((is_contained, not is_keyword_ifdef, word))
                if is_keyword_ifdef: is_contained = 0
            else:
                stack.append((is_contained, -1, word))
                if is_contained: expanded_snippet.append(line)
        elif keyword == 'if':
            stack.append((is_contained, -1, ''))
            if is_contained: expanded_snippet.append(line)
        elif keyword == 'else' and stack:
            s_is_contained, s_is_keyword_ifdef, s_word = stack[-1]
            if s_is_keyword_ifdef < 0:  # no macro, maybe commented else  excepiton case, (is_contained, -1, '')
                if is_contained: expanded_snippet.append(line)
            else:
                s_is_keyword_ifdef = not s_is_keyword_ifdef # reverse macro condition
                is_contained = s_is_contained
                if not s_is_keyword_ifdef: is_contained = 0
                stack[-1] = s_is_contained, s_is_keyword_ifdef, s_word
        elif keyword == 'endif' and stack:
            s_is_contained, s_is_keyword_ifdef, s_word = stack[-1]
            if s_is_keyword_ifdef < 0:
                if is_contained: expanded_snippet.append(line) # exception case
            del stack[-1]
            is_contained = s_is_contained
        else:
            print 'Unknown keyword %s\n' % keyword
    return expanded_snippet
    if stack:
        print 'stack: %s\n' % stack

# according the macro_command, calculate the possible combinations.
def joint_possible_macro_snippet(macro_command, span, macro_comment_dict):
    expand_res = []
    macro_command.reverse()
    combinations = construct_macro_combinations(macro_command)
    for combination in combinations:
        defs = combination.macro[0]
        undefs = combination.macro[1]
        prefix_macro_condition = []
        suffix_macro_condition = []
        for macro in defs:
            comment = macro_comment_dict.get(macro)
            if comment is None:
                prefix_macro_condition.append('#ifdef ' + macro + '\n')
            else:
                prefix_macro_condition.append('#ifdef ' + macro + ' ' + comment + '\n')
            suffix_macro_condition.append('#endif\n')
        for macro in undefs:
            comment = macro_comment_dict.get(macro)
            if comment is None:
                prefix_macro_condition.append('#ifndef ' + macro + '\n')
            else:
                prefix_macro_condition.append('#ifndef ' + macro + ' ' + comment + '\n')
            suffix_macro_condition.append('#endif\n')
        expanded_snippet = expand_macro_snippet(span, defs, undefs)
        expanded_snippet = prefix_macro_condition + expanded_snippet + suffix_macro_condition
        expand_res += expanded_snippet + ['\n']
    return expand_res

def create_brother_node(node):
    parent = node.parent
    macro_context = copy.deepcopy(parent.get_macro()) #parent node macro
    current_macro_context = copy.deepcopy(node.get_macro()) # current node macro
    self_pos = -1 
    insert_pos = ''
    if parent.left is None: #right child
        self_pos = 1  
        insert_pos = 'left'
    if parent.right is None: #left child 
        self_pos = 0  
        insert_pos = 'right'
    if self_pos != -1:  # have #else, then #endif. there is a chance, insert_pos = -1
        macro = current_macro_context[self_pos].pop()
        macro_context[abs(self_pos-1)].append(macro)
        child_node = BinaryTreeNode(macro_context, None, None, parent)
        parent.insert_node(insert_pos, child_node)
        return child_node
    else:
        return None

def create_a_node(parent, macro_command):
    macro = macro_command.split(" ")[-1].strip()
    macro_context = copy.deepcopy(parent.get_macro()) 
    if '#ifdef' in macro_command:
        isifndef = 0
        insert_pos = 'left'
    if '#ifndef' in macro_command:
        isifndef = 1
        insert_pos = 'right'
    macro_context[isifndef].append(macro)
    child_node = BinaryTreeNode(macro_context, None, None, parent)
    parent.insert_node(insert_pos, child_node)
    return child_node
    

#Algorithm:
# parse macro command in a function, build a binary tree
# create two nodes: def_macro and undef_macro according to pervious operation node
# search leaf node
# modify context_node_list
# macro list need to be reversed before function be called
# use the stack to handle the nested structure

def construct_macro_combinations(macro_list):
    tree = BinaryTree()
    root = BinaryTreeNode([[],[]], None, None, None)
    tree.build_tree(root)

    # stack store the macro leaf node search_level
    context_nodes_list = [[root]]

    while len(macro_list) > 0 :
        macro_command = macro_list.pop()
        if '#ifdef' in macro_command or '#ifndef' in macro_command:
            context_nodes = context_nodes_list[-1]
            operation_node_list = []
            for node in context_nodes:
                operation_node_list.extend(tree.find_leaf(node))
            context_nodes_next = []
            for node in operation_node_list:
                context_nodes_next.append(create_a_node(node, macro_command))
            context_nodes_list.append(context_nodes_next) 

        if '#else' in macro_command:
            context_nodes = context_nodes_list.pop()
            context_nodes_next = []
            for node in context_nodes:
                context_nodes_next.append(create_brother_node(node))
            context_nodes_list.append(context_nodes_next) 

        if '#endif' in macro_command:
            context_nodes = context_nodes_list.pop()
            for node in context_nodes:
                create_brother_node(node)
    return tree.find_leaf(root)
