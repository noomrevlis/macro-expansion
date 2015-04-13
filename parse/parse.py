#! /usr/bin/env python 2.6.6
# -*- coding:utf-8 -*-

import sys
from pyparsing import nestedExpr
import pprint

def tree(var, level=1, outstr=''):
    #Takes a var, prints it out as nested aligned list
    if var is None:
        #Just return a new line:
        outstr+=' \n'
    elif isinstance(var, (int, float, long, complex, str, bool, unicode)):
        #Single value, simply add the fucker
        outstr+=' '+str(var)
        outstr+=' \n'
    elif isinstance(var, (list, tuple)):
        #List with some specified order, print in order
        outstr+='\n'
        k=0    #Manually index this
        for valchild in var:
            for tab in range(level-1):    # Print key
                outstr+='\t'
            outstr+='['+str(k)+'] => '
            k+=1    #Increment index
            newlevel = level + 1
            outstr = tree(valchild,newlevel,outstr)
    elif isinstance(var,(dict)):
        #List with keys and values, no order
        outstr+='\n'
        for k,valchild in sorted(var.iteritems()):
            for tab in range(level-1):    # Print key
                outstr+='\t'
            outstr+='['+str(k)+'] => '
            newlevel = level + 1
            outstr = tree(valchild,newlevel,outstr)
    else:
        #It doesn't qualify as any of the above cases
        outstr+=' '+str(var)
        outstr+=' \n'
    return outstr


if __name__ == '__main__' :
    file_name = sys.argv[1]
    with open(file_name, 'r') as file_read:
        content = file_read.read()
    res = nestedExpr().parseString(content).asList()
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(res)
    out = tree(res)
    with open(file_name, 'w') as file_write:
        file_write.write(out)
