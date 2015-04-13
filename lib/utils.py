#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-

import os
import shlex
import subprocess
import re
import time
import functools
import traceback
import datetime

def exception_catch(log_path):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                filename, line, function, text = traceback.extract_stack(limit=1)[0]
                with open(log_path, 'a') as log:
                    log.write('time: {0} type: {1} function: {2} line: {3} \n'.format(
                        datetime.datetime.now(), 
                        type(e),
                        function,
                        line))
                raise e # raise e again to jump out external loop
        return wrapper
    return deco

def timeit(func):
    @functools.wraps(func)
    def timed(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print '*************** Time Statistics ***************' 
        print 'func:%r took: %2.4f sec' % (func.__name__, end-start)
        print '***********************************************' 
        return result
    return timed

def comment_out(lines, start, end):
    for linum in range(start, end+1):
        lines[linum] = '// expand tools can not handle ' + lines[linum]
        

def mapping_macros_comments(snippet, macro_comment_dict):
    from lib.parse import macrocomment
    macrocomment.parseWithTabs()
    for r,s,e in macrocomment.scanString(snippet):
        macro_comment_dict[r[1]] = "".join(r[-1]) # {macro:comment}
   
def call_meld(meld_path, orginal, target):
    if os.path.isfile(orginal):
        option = r' -n '
    elif os.path.isdir(orginal):
        option = r' '
    else:
        raise Exception('not a invalid input')
    command_line = meld_path + option + orginal + ' ' + target
    args =shlex.split(command_line)
    subprocess.Popen(args) 

def dedupe(items):
    seen = set()
    for item in items:
        if item not in seen:
            yield item
            seen.add(item)

def dedupe_functioncall(macro_command):
    li = []
    endif = '#endif \n'
    macro_list = set()
    ifdef_ifndef_macro = re.compile(r'^\s*#if(?:def|ndef)\s*')
    for command in macro_command:
        if ifdef_ifndef_macro.search(command) is not None:
            tmp = command.lstrip()
            command_neat = tmp.split()[0] + ' ' + tmp.split()[1]
            macro = command_neat.split(" ")[-1].strip()
            if macro not in macro_list:
                macro_list.add(macro)
                li.append(command)
                li.append(endif)
    return li

def create_directory_if_needed():
    path = './expanded/'
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    return path

def read_file_by_line(file_name):
    try:
        with open(file_name, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        print e
    return lines

def write_file_as_string(file_name, content):
    try:
        with open(file_name, 'w') as file_write:
            file_write.write(content)
    except IOError as e:
        print e

def write_file(file_name, lines):
    try:
        with open(file_name, 'w') as file_write:
            file_write.writelines(lines)
    except IOError as e:
        print e

def get_file_list(dir_path, file_suffix): 
    ''' file_suffix could be a tuple! '''
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for file_name in files:
            if file_name.endswith(file_suffix):
                abs_path = os.path.abspath(os.path.join(root,file_name))
                file_list.append(abs_path)
    return file_list

def find_delimiter(lines, line_num, delim, direction):
    ''' The format of delim { }, whitespace '''
    file_size = len(lines)
    if direction == "forward":
        left_delim, right_delim = delim.split()
    elif direction == "backward":
        right_delim, left_delim = delim.split()
    else:
        raise Exception('invalid search direction')
    bracket_depth = 1
    while bracket_depth != 0:
        for c in lines[line_num]:
            if c == right_delim:
                bracket_depth -= 1
                if bracket_depth == 0:
                    return line_num
            if c == left_delim:
                bracket_depth += 1
        if direction == "forward":
            if line_num >= file_size:
                break
            line_num += 1
        elif direction == "backward":
            if line_num <= 1:
                break
            line_num -= 1
    else:
        raise Exception('The delimiter is not balanced')

# delimit the end of if else statement: up to down
# check whether there is a 'else if' or 'else'  could check sevearl times
# stop condition: appear ';'
# isCodeBlockComplete, indicate the completion of code block
def delimit_down_if_else(line_num_if_condition_end, lines):
    if_brace = re.compile(r'^\s*if\s*\(')
    isCodeBlockComplete = False
    line_num_iter = line_num_if_condition_end
    line_num_iter_prev = line_num_if_condition_end # line position of a complete code block
    file_size = len(lines)
    # repeatedly call the function till the flag is changed
    while not isCodeBlockComplete and line_num_iter < file_size:
        if not isCodeBlockComplete:
            line_num_iter_prev = line_num_iter
        line_num_iter, isCodeBlockComplete = check_elseif_else(lines, line_num_iter)
    if '}' in lines[line_num_iter_prev]:
        return line_num_iter_prev
    if if_brace.search(lines[line_num_iter]) is not None:
        return line_num_if_condition_end
    else:
        return line_num_iter  # else with only one line statement

def check_elseif_else(lines, line_num):
    isCodeBlockComplete = False
    file_size = len(lines)
    if_brace = re.compile(r'^\s*if\s*\(')
    while line_num < file_size:
       current_line = lines[line_num]
       if '{' in current_line:
           if current_line.find('}', current_line.find('{')) == -1:
               # Special Case:
               # if {
               #    } else if {
               # search '}' from next line
               line_num = find_delimiter(lines, line_num+1, '{ }', 'forward')
           break
       # if block again
       elif if_brace.search(current_line) is not None:
           isCodeBlockComplete = True
           break
       elif ';' in current_line or '}' in current_line:
           isCodeBlockComplete = True
           break
       line_num += 1
    return line_num, isCodeBlockComplete

def check_elseif_else_forward(lines, line_num):
    isCodeBlockComplete = False
    if_brace = re.compile(r'^\s*if\s*\(')
    while line_num > 1 :
        current_line = lines[line_num]
        print current_line
        if '}' in current_line:
            if current_line.rfind('{', 0, current_line.rfind('}')) != -1\
                   and current_line.rfind('}', 0, current_line.rfind('{')) == -1:
                line_num -= 1
            else:
                line_num = find_delimiter(lines, line_num-1, '{ }', 'backward')
            break
        elif if_brace.search(current_line) is not None:
            isCodeBlockComplete = True
            break
        else:
            line_num -= 1
    return line_num, isCodeBlockComplete

# delimit the end of if else statement: down to up
# check whether there is a 'else if' or 'else'  could check sevearl times
# stop condition: appear 'if'
# isCodeBlockComplete, indicate the completion of code block
def delimit_up_if_else(line_num_if_condition_start, lines):
    isCodeBlockComplete = False
    line_num_iter = line_num_if_condition_start
    # repeatedly call the function till the flag is changed
    while not isCodeBlockComplete and line_num_iter > 1:
        line_num_iter, isCodeBlockComplete = check_elseif_else_forward(\
                                                    lines, line_num_iter)
    return line_num_iter
