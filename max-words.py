#!/usr/bin/env python3

import sys
import time
import os
from collections import Counter
from multiprocessing import Pool
from typing import List, Tuple, Iterable    # for type hints, see [https://docs.python.org/3/library/typing.html]


def ignore_file(path:str) -> bool:
    for suffix in [ '.asl', '.gz', '.bz2', '.bin', '.pklg', 'StoreData' ]:
        if path.endswith(suffix):
            return True
    else:
        return False

def score_file_words(path:str) -> Counter:
    c = Counter()
    try:
        with open(path, 'r') as f:
            try:
                for line in f:
                    words = line.split()
                    c.update(Counter(words))
            except (UnicodeDecodeError, PermissionError) as ex:
                if not ignore_file(path):
                    print("skipping(4) {e} {p}".format(e=ex, p=path))
    except (PermissionError) as ex:
        if not ignore_file(path):
            print("skipping(3) {e} {p}".format(e=ex, p=path))
    return c

def walk_tree(path:str, files:List[str]) -> None:
    if os.path.isdir(path):             # if it's a directory go through its content
        try:
            for f in os.listdir(path):
                pathname = os.path.join(path, f)
                walk_tree(pathname, files)
        except (PermissionError) as ex:
            print("skipping(2) {e}".format(e=ex))
    elif os.path.isfile(path):
        files.append(path)
    else:
        print("skipping(1) {}".format(path))


class CLI:
    '''
        parse command line
        hold input parameters
    '''
    def __init__(self):
        usage_msg = "{line_1}{space}{line_2}{space}{line_3}".format(
                      line_1="usage: max-words TOP_N PATH [PATH ...]\n",
                      line_2="TOP_N - integer, display the TOP_N most frequent words in the PATH list files\n",
                      line_3="PATH  - file or directory name",
                      space =" " * 7)
        if len(sys.argv) < 3:
            print(usage_msg)
            return

        self.raw_file_list = None
        try:
            self.top_n = int(sys.argv[1])
        except (ValueError) as ex:
            print("{x}".format(x=ex))
            print(usage_msg)
            return

        if self.top_n < 1:
            print("ValueError, {} is not an integer with value > 0".format(sys.argv[1]))
            return

        self.raw_file_list = sys.argv[2:]

def next_file(files:Iterable[str]) -> str:
    for f in files:
        yield f
    return

def print_results(mc:List[Tuple[str,int]]) -> None:      # mc stands for 'most common'
    print('\nMaximum {N} words:'.format(N=len(mc)))
    maxlen = sorted(mc, key=lambda x: len(x[0]), reverse=True)[0]
    strlen = len(maxlen[0])
    maxval = sorted(mc, key=lambda x: x[1], reverse=True)[0]
    intlen = len(str(maxval[1]))
    for tup in mc:                  # mc is a list of tuples of (word, num-of-occurrences)
        print("Word {w:<{ind1}} occurred {n:>{ind2}} times".format(w=tup[0], n=tup[1], ind1=strlen, ind2=intlen))

def check_version() -> bool:
    major, minor, micro = sys.version_info.major, sys.version_info.minor, sys.version_info.micro
    if major == 3 and minor == 6 and micro >=5:
        return True
    if major == 3 and minor > 6:
        return True
    print("This script was tested with Python 3.6.5, can't run with the current Python version")
    return False


def main():
    if check_version() == False:
        return
    files = []                      # list of files to traverse
    cli = CLI()                     # the command line object
    if cli.raw_file_list == None:   # means that there was a problem while reading the command line
        return
    for path in cli.raw_file_list:  # iterate over CLI directories and files
        walk_tree(path, files)      # recursively go through directory trees and get all containing files

    CPUs = os.cpu_count()           # get number of cores
    with Pool(CPUs) as pool:
        scores = pool.map(score_file_words, next_file(files))
    total_count = Counter()
    for s in scores:
        total_count.update(s)       # aggregate all counts
    mc = total_count.most_common(cli.top_n)
    print_results(mc)               # print the top_n most common words along with their appearance counter

    print('\nPython {}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
    print('total {n:,} words'.format(n=sum(total_count.values())))

if __name__ == "__main__":
    started = time.time()
    main()
    elapsed = time.time() - started
    print("time elapsed: {:.2f}s".format(elapsed))

