#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-

# third-party library
from lib.pyparsing import Word, alphas, OneOrMore, restOfLine, NotAny, LineEnd
from lib.pyparsing import delimitedList, Group, Keyword, nums, Regex, Suppress
from lib.pyparsing import dblQuotedString, operatorPrecedence, oneOf, opAssoc
from lib.pyparsing import Forward, Combine, Optional, alphanums, ZeroOrMore
from lib.pyparsing import ParserElement

# Enable Packrat, this is risky due to memory usage
ParserElement.enablePackrat()

# Symbol
LPAR,RPAR,LBRACK,RBRACK,LBRACE,RBRACE,SEMI,COMMA = map(Suppress, "()[]{};,")

# Macro Symbol
MACRO_HEAD = (Keyword("#ifdef") | Keyword("#ifndef")) + Word(alphas, alphanums + "_")
MACRO_ELSE = Keyword("#else")
MACRO_END = Keyword("#endif")

# Key Word
IF = Keyword("if")
ELSE = Keyword("else")
ELSEIF = Keyword("else if")
VOID = Keyword("void")
FOR = Keyword("for")


# General Common Concept  Ambigious
ident = Word(alphas, alphanums + "_")
vartype = Combine(ident + Optional(Word("*")), adjacent = False)
argdecl= vartype + ident
argdecllist = delimitedList(argdecl)
arg = (Word(nums) | Word(alphas, alphanums + "_"))
arglist = delimitedList(arg)

# exp in for statement
exp = (Word(nums) | Word(alphas, alphanums + " *_[]<>|&=+-"))
exp_re = Regex(r'.+')
explist = delimitedList(exp, delim=';')
forexp = FOR + LPAR + explist + RPAR
ifexp = IF + LPAR + exp + RPAR
ifexp_re = Regex(r'if\s*\(.+\)')
any_content = Regex(r'.+')

# Parse Rule
functionheadtwomacro = MACRO_HEAD + vartype + ident + LPAR + argdecllist + RPAR + MACRO_END + MACRO_HEAD

segregativebrace = MACRO_HEAD + MACRO_HEAD + RBRACE

macrocomment = MACRO_HEAD + NotAny(LineEnd()) + Group("//" + restOfLine) 

loopfor = OneOrMore(MACRO_HEAD) + ((forexp + MACRO_ELSE) | (MACRO_ELSE + forexp))

functioncall = ident + LPAR + ((MACRO_HEAD) | (arglist + COMMA + MACRO_HEAD))

functionhead = OneOrMore(MACRO_HEAD) + vartype + ident + LPAR + argdecllist + RPAR + MACRO_ELSE

macroelseif = MACRO_HEAD + ELSEIF

macroelse = MACRO_HEAD + ELSE + NotAny(IF)

ifhead = OneOrMore(MACRO_HEAD) + ((ifexp_re + MACRO_ELSE) | (MACRO_ELSE + Optional(MACRO_HEAD) + ifexp_re + NotAny('{')))
ifhead_exception = MACRO_HEAD + ifexp_re + MACRO_ELSE + ifexp_re + LBRACE + any_content + RBRACE + ELSE + ifexp_re + MACRO_END

# issue: mistake  #if macro condtion   #ifdef macro
ifcondition = Regex(r'\s*if\s*\((?:[^{;]|\n)*?#if(?:def|ndef)')





