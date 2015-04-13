#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-

import logging
import lib.utils as utils
from lib.utils import timeit
from lib.utils import exception_catch
from lib.pyparsing import ParseBaseException
from lib.pyparsing import cStyleComment, Regex, cppStyleComment
from lib.expand import joint_possible_macro_snippet

class GetOutOfLoop(Exception):
    pass

class PatternTemplate(object):  # new-style classses  always inheritant from a class (object)
    def __init__(self, file_name):
        self.parse_pattern = None
        self.file_name = file_name

    def macro_handler(self):
        self.business_logic()

    @timeit
    def collect_match_info(self, lines, macro_command, macro_stack):
        res, start_pos, end_pos = next(self.parse_pattern.scanString("".join(lines)))
        #print "".join(lines)[start_pos:end_pos+1]
        snippet_start = -1
        line_num = 0
        pos = 0
        for line in lines:
            if pos >= start_pos or (pos + len(line)) > start_pos:
                if snippet_start == -1:
                    snippet_start = line_num
            if (pos >= start_pos or (pos + len(line) > start_pos) \
               and pos < end_pos):
                if '#ifdef' in line or '#ifndef' in line:
                    tmp = line.lstrip()
                    macro_command_neat = tmp.split()[0] + ' ' + tmp.split()[1]
                    macro_command.append(macro_command_neat)
                    macro = macro_command_neat.split(" ")[-1].strip()
                    macro_stack.append(macro)
                if '#else' in line:
                    macro_command.append(line.lstrip())
                if '#endif' in line:
                    macro_command.append(line.lstrip())
                    macro_stack.pop()
            pos += len(line) 
            if pos > end_pos:
                break;
            line_num += 1
        return snippet_start, line_num

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        pass

    def complete_snippet_down_brace(self, lines, match_start, match_end, macro_command, macro_stack):
        line_num = match_end
        file_size = len(lines)
        #print '===========macro_stack========='
        #print macro_stack
        #print '===========macro_command========='
        #print macro_command
        while line_num < file_size:
            current_line = lines[line_num]
            # handle nested or combined macro
            if '#ifdef' in current_line or '#ifndef' in current_line:
                tmp = current_line.lstrip()
                macro_command_neat = tmp.split()[0] + ' ' + tmp.split()[1]
                macro_command.append(macro_command_neat)
                macro = macro_command_neat.split(" ")[-1].strip()
                macro_stack.append(macro)
            elif '#else' in current_line:
                macro_command.append(current_line.lstrip())
            elif '#endif' in current_line:
                macro_command.append(current_line.lstrip())
                if macro_stack:
                    macro_stack.pop()
                else:
                    print 'Nested Error'
                    utils.comment_out(lines, match_start, match_end)
                    raise GetOutOfLoop
            elif '{' in current_line:
                snippet_end = utils.find_delimiter(lines, line_num+1, '{ }', 'forward')
                if not macro_stack:
                    break
                else: # macro not balanced case
                    for i in range(len(macro_stack)):
                        if macro_stack:
                            macro_command.pop(0)
                        else:
                            print 'Nested Error'
                            utils.comment_out(lines, match_start, match_end)
                            raise GetOutOfLoop
                    match_start += len(macro_stack)
                    break
            line_num += 1
        return match_start, snippet_end

    def complete_snippet_one_else_block(self, lines, match_start, match_end, macro_command, macro_stack):
        snippet_start = utils.delimit_up_if_else(match_start-1, lines)
        line_num = match_end
        file_size = len(lines)
        while line_num < file_size:
            current_line = lines[line_num]
            # handle nested or combined macro
            if '#ifdef' in current_line or '#ifndef' in current_line:
                tmp = current_line.lstrip()
                macro_command_neat = tmp.split()[0] + ' ' + tmp.split()[1]
                macro_command.append(macro_command_neat)
                macro = macro_command_neat.split(" ")[-1].strip()
                macro_stack.append(macro)
            elif '#endif' in current_line:
                macro_command.append(current_line.lstrip())
                macro_stack.pop()
                if not macro_stack:
                    snippet_end = line_num
                    break
            elif '{' in current_line:
                if not macro_stack:
                    line_num = utils.find_delimiter(lines, line_num+1, '{ }', 'forward')
            line_num += 1
        return snippet_start, snippet_end

    @exception_catch('./logging')
    @timeit
    def expand_snippet(self, span, macro_command, macro_comment_dict):
        return joint_possible_macro_snippet(macro_command, span, macro_comment_dict)

    def pyparsing_setting(self):
        self.parse_pattern.parseWithTabs()
        self.parse_pattern.ignore( cStyleComment ) 
        self.parse_pattern.ignore( cppStyleComment )

    def business_logic(self):
        self.pyparsing_setting()
        lines = utils.read_file_by_line(self.file_name)
        lines_expanded = []
        while True:
            try:
                macro_command = []  # for analyzing the combinations
                macro_stack = []  # for handling the nested macro in code
                macro_comment_dict = {}  # dict for handling comments
                match_start, match_end = \
                    self.collect_match_info(lines, macro_command, macro_stack)
                #print '----------business logic------ macro_stack'
                #print macro_stack
                snippet_start, snippet_end = \
                    self.complete_snippet\
                    (lines, match_start, match_end, macro_command, macro_stack) # easy to make a mistake: match_end + 1
                #print macro_command
                tmp = "".join(lines[snippet_start:snippet_end+1])
                #print tmp
                utils.mapping_macros_comments(tmp, macro_comment_dict)
                #for k,v in macro_comment_dict.iteritems():
                #    print "dict[%s]=" % k, v
                lines[snippet_start:snippet_end+1] = \
                    self.expand_snippet(lines[snippet_start:snippet_end+1], macro_command, macro_comment_dict) 
                lines_expanded += lines[:snippet_end+1]
                lines[:] = lines[snippet_end+1:]
            except StopIteration:
                print 'Iterator stop Normally'
                if len(lines_expanded) == 0:
                    lines_expanded[:] = lines[:]
                else:
                    lines_expanded += lines[:]
                pass
                break
            except ParseBaseException, e:
                print 'Iterator stop Due to ParseBaseException'
                logging.exception(e)
                pass
                break
            except GetOutOfLoop:
                print 'Iterator stop Due to Nested macro'
                pass
            except AttributeError:
                print 'Iterator stop Due to AttributeError, check macro_command'
                utils.comment_out(lines, match_start, match_end)
                pass
        utils.write_file(self.file_name, lines_expanded)
