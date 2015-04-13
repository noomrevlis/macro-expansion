#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-

import os
import multiprocessing
import sys
import logging
import shutil
import lib.utils as utils

logging.basicConfig(level=logging.INFO)

#TODO(Jay): Rewrite the delimit the range in template and patterns
#TODO(Jay): Log important info: familiar with logging module 
#TODO(Jay): for i in range(len(lines)): replace line_num: save tmp var
#TODO(Jay): Replace #ifdef in line with Robust Regex

MELD_PATH = r'/sandbox/Software/meld-1.8.4/bin/meld'
MELD_AVAILABLE = False

def execute_all(file_name):
    #from pattern.patterns import IfCondition
    #worker = IfCondition(file_name)
    #worker.macro_handler()

    from pattern.patterns import IfHeadException
    worker = IfHeadException(file_name)
    worker.macro_handler()

    from pattern.patterns import IfHead
    worker = IfHead(file_name)
    worker.macro_handler()

    from pattern.patterns import MacroElseIf
    worker = MacroElseIf(file_name)
    worker.macro_handler()

    from pattern.patterns import MacroElse
    worker = MacroElse(file_name)
    worker.macro_handler()

    from pattern.patterns import FunctionCall
    worker = FunctionCall(file_name)
    worker.macro_handler()

    from pattern.patterns import LoopFor
    worker = LoopFor(file_name)
    worker.macro_handler()

    from pattern.patterns import FunctionHead
    worker = FunctionHead(file_name)
    worker.macro_handler()

    from pattern.patterns import FunctionHeadTwoMacro
    worker = FunctionHeadTwoMacro(file_name)
    worker.macro_handler()

    from pattern.patterns import SegregativeBrace
    worker = SegregativeBrace(file_name)
    worker.macro_handler()

def parse_input(args):
    path = utils.create_directory_if_needed()
    for arg in args:
        if os.path.isfile(arg):
            target_filename = path + arg.split("/")[-1].strip()
            shutil.copy(arg, target_filename)
            execute_all(target_filename)
            if MELD_AVAILABLE:
                utils.call_meld(MELD_PATH, arg, target_filename)
        elif os.path.isdir(arg):
            current_dir = r'./'
            if arg == current_dir:
                print 'Please provide a directory that not includes the scripts.'
            else:
                target_dirname = path + 'src'
                if os.path.exists(target_dirname):
                    shutil.rmtree(target_dirname)
                shutil.copytree(arg, target_dirname)
                file_list = utils.get_file_list(target_dirname, (".c"))
                cpu_num = multiprocessing.cpu_count()
                pool = multiprocessing.Pool(processes=cpu_num, maxtasksperchild=2)
                result = []
                for file_name in file_list:
                    logging.info('-----------------------------')
                    logging.info('Current file is ' + file_name )
                    result.append(pool.apply_async(execute_all,(file_name,)))
                pool.close()
                pool.join()
                for res in result:
                    print res.get()
                print "Sub-process(es) done!"
                if MELD_AVAILABLE:
                    utils.call_meld(MELD_PATH, arg, target_dirname)
        else:
            logging.info('Input ' + arg + ' is not valid.')

if __name__ == '__main__' :
    from optparse import OptionParser
    USG = ' %prog [option,filename|dir[,arg1,arg2,arg3,[...]]]'
    parser = OptionParser(USG)
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        sys.exit(0)
    else:
        parse_input(args)
