#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-

from template import PatternTemplate
from lib.expand import construct_macro_combinations
from lib.expand import expand_macro_snippet
from pattern.template import GetOutOfLoop
import lib.utils as utils
import re

class IfCondition(PatternTemplate):
    def __init__(self, file_name):
        super(IfCondition, self).__init__(file_name)
        from lib.parse import ifcondition
        self.parse_pattern = ifcondition

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
                if '#if ' in line:
                    utils.comment_out(lines, snippet_start, line_num)
                    raise GetOutOfLoop
                if '#ifdef' in line or '#ifndef' in line:
                    tmp = line.lstrip()
                    macro_command_neat = tmp.split()[0] + ' ' + tmp.split()[1]
                    macro_command.append(macro_command_neat)
                    macro = macro_command_neat.split(" ")[-1].strip()
                    macro_stack.append(macro)
            if pos > end_pos:
                break;
            pos += len(line)  # very important  because it may cause the double append the same command
            line_num += 1
        return snippet_start, line_num

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
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
                if not macro_stack:
                    if '}' in current_line: #   { ... }
                        snippet_end = line_num
                    else: #   { ...  \n }
                        snippet_end = utils.find_delimiter(lines, line_num+1, '{ }', 'forward')
                    break
                else: # macro not balanced case
                    snippet_end = utils.find_delimiter(lines, line_num+1, '{ }', 'forward')
                    for i in range(len(macro_stack)):
                        if macro_stack:
                            macro_command.pop(0)
                        else:
                            print 'Nested Error'
                            utils.comment_out(lines, match_start, match_end)
                            raise GetOutOfLoop
                    match_start += len(macro_stack)
                    break
            elif ';' in current_line: # if (...) \n    ... ;
                if not macro_stack:
                    snippet_end = line_num + 1 # search else from next line
                    break
            line_num += 1
        snippet_end = utils.delimit_down_if_else(snippet_end+1, lines)
        return match_start, snippet_end


class FunctionHead(PatternTemplate):
    def __init__(self, file_name):
        super(FunctionHead, self).__init__(file_name)
        from lib.parse import functionhead
        self.parse_pattern = functionhead

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        return super(FunctionHead, self).complete_snippet_down_brace(lines, match_start, match_end+1, macro_command, macro_stack)

class FunctionHeadTwoMacro(PatternTemplate):
    def __init__(self, file_name):
        super(FunctionHeadTwoMacro, self).__init__(file_name)
        from lib.parse import functionheadtwomacro
        self.parse_pattern = functionheadtwomacro

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        return super(FunctionHeadTwoMacro, self).complete_snippet_down_brace(lines, match_start, match_end+1, macro_command, macro_stack)

    def expand_snippet(self, span, macro_command, macro_comment_dict):
        expand_res = []
        macro_command.reverse()
        combinations = construct_macro_combinations(macro_command)
        for combination in combinations:
            defs = combination.macro[0]
            undefs = combination.macro[1]
            if len(defs) == 1 or len(undefs) == 1:
                prefix_macro_condition = []
                suffix_macro_condition = []
                for macro in defs:
                    prefix_macro_condition.append('#ifdef ' + macro + '\n')
                    suffix_macro_condition.append('#endif\n')
                for macro in undefs:
                    prefix_macro_condition.append('#ifndef ' + macro + '\n')
                    suffix_macro_condition.append('#endif\n')
                expanded_snippet = expand_macro_snippet(span, defs, undefs)
                expanded_snippet = prefix_macro_condition + expanded_snippet + suffix_macro_condition
                expand_res += expanded_snippet + ['\n']
        return expand_res

class IfHeadException(PatternTemplate):
    def __init__(self, file_name):
        super(IfHeadException, self).__init__(file_name)
        from lib.parse import ifhead_exception
        self.parse_pattern = ifhead_exception

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        snippet_start, snippet_end = super(IfHeadException, self).complete_snippet_down_brace(lines, match_start, match_end+1, macro_command, macro_stack) 
        return snippet_start, snippet_end

class IfHead(PatternTemplate):
    def __init__(self, file_name):
        super(IfHead, self).__init__(file_name)
        from lib.parse import ifhead
        self.parse_pattern = ifhead

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        snippet_start, snippet_end = super(IfHead, self).complete_snippet_down_brace(lines, match_start, match_end+1, macro_command, macro_stack) 
        snippet_end = utils.delimit_down_if_else(snippet_end+1, lines)
        return snippet_start, snippet_end

class LoopFor(PatternTemplate):
    def __init__(self, file_name):
        super(LoopFor, self).__init__(file_name)
        from lib.parse import loopfor
        self.parse_pattern = loopfor

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        # old styple class
        #return PatternTemplate.complete_snippet_down_brace(self, lines, match_start, match_end, macro_command, macro_stack)
        # easy to make a mistake: match_end + 1
        return super(LoopFor, self).complete_snippet_down_brace(lines, match_start, match_end+1, macro_command, macro_stack)

class FunctionCall(PatternTemplate):
    def __init__(self, file_name):
        super(FunctionCall, self).__init__(file_name)
        from lib.parse import functioncall
        self.parse_pattern = functioncall

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
                if '(' in line:
                        snippet_end = utils.find_delimiter(lines, line_num+1, '( )', 'forward')
            pos = pos + len(line) 
            if pos > end_pos:
                break;
            line_num += 1
        # collection the information for the rest part
        line_num += 1 # start from next line of match_end
        while line_num < snippet_end:
            current_line = lines[line_num]
            if '#ifdef' in current_line or '#ifndef' in current_line:
                tmp = current_line.lstrip()
                macro_command_neat = tmp.split()[0] + ' ' + tmp.split()[1]
                macro_command.append(macro_command_neat)
            if '#else' in current_line:
                macro_command.append(current_line.lstrip())
            elif '#endif' in current_line:
                macro_command.append(current_line.lstrip())
            line_num += 1
        # modify the list inside a function, or could return this list
        macro_command[:] = utils.dedupe_functioncall(macro_command)
        return snippet_start, snippet_end

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        return match_start, match_end

class MacroElse(PatternTemplate):
    def __init__(self, file_name):
        super(MacroElse, self).__init__(file_name)
        from lib.parse import macroelse
        self.parse_pattern = macroelse

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        return super(MacroElse, self).complete_snippet_one_else_block(lines, match_start, match_end+1, macro_command, macro_stack)

class MacroElseIf(PatternTemplate):
    def __init__(self, file_name):
        super(MacroElseIf, self).__init__(file_name)
        from lib.parse import macroelseif
        self.parse_pattern = macroelseif

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        snippet_start, snippet_end = super(MacroElseIf, self).complete_snippet_one_else_block(lines, match_start, match_end+1, macro_command, macro_stack)
        snippet_end = utils.delimit_down_if_else(snippet_end, lines)
        return snippet_start, snippet_end

class SegregativeBrace(PatternTemplate):
    def __init__(self, file_name):
        super(SegregativeBrace, self).__init__(file_name)
        from lib.parse import segregativebrace
        self.parse_pattern = segregativebrace

    def collect_match_info(self, lines, macro_command, macro_stack):
        res, start_pos, end_pos = next(self.parse_pattern.scanString("".join(lines)))
        snippet_start = -1
        line_num = 0
        file_size = len(lines)
        pos = 0
        ifdef_ifndef_macro = re.compile(r'^\s*#if(?:def|ndef)\s*')
        for line in lines:
            if pos >= start_pos or (pos + len(line)) > start_pos:
                if '}' in lines[line_num]:
                    break;
            pos = pos + len(line)
            line_num += 1
        snippet_start = utils.find_delimiter(lines, line_num-1, '{ }', 'backward')
        while line_num < file_size:
            current_line = lines[line_num]
            if '#endif' in current_line:
                macro_command.append(current_line)
            else:
                if macro_command:
                    break
            line_num += 1
        snippet_end = line_num
        macro_num = len(macro_command)
        while snippet_start > 1 and macro_num > 0:
            current_line = lines[snippet_start]
            if ifdef_ifndef_macro.search(current_line) is not None:
                macro_command.insert(0, current_line)
                macro_num -= 1
            snippet_start -= 1
        return snippet_start, snippet_end

    def complete_snippet(self, lines, match_start, match_end, macro_command, macro_stack):
        return match_start, match_end
