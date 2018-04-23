#!/usr/bin/env python3

import os
import time
import argparse
from pathlib import Path
from random  import randint
from typing  import List, Tuple, Iterable    # for type hints, see [https://docs.python.org/3/library/typing.html]
from multiprocessing import Pool

# run the command below to check the script's output
# find . -type f -name "*.txt" -exec wc -l {} +

VERSION = '0.1a-b-c'
MINIMUM_LEVELS  = 1
MINIMUM_SUBDIRS = 2
WORDS_POOL = "/usr/share/dict/words"    # a dictionary, used as source of words
g_words = []                            # holds the dictionary as a list for random access

PREFIX_NONE         = 0
PREFIX_NUMERIC_TIME = 1
PREFIX_ALPHA_TIME   = 2

class Task:
    word_dict = g_words                     # this is not a python dictionary, it's a regular English dictionary

    def prefix_none(self) -> str:
        return ''

    def next_prefix_numeric_time(self) -> str:
        self.next_t += randint(10, 60)
        return str(self.next_t) + ' '

    def next_prefix_alpha_time(self) -> str:
        return 'alpha'

    def __init__(self, file_name, prefix_type):
        self.file   = file_name
        self.lines  = randint(0, 1000)        # acquire number of lines in the current file
        self.next_t = randint(1000, 9999)
        self.prefix_funcs = [ self.prefix_none,
                              self.next_prefix_numeric_time,
                              self.next_prefix_alpha_time       ]
        self.prefix_type = prefix_type

class CLI:
    def __init__(self):
        ''' Parse command line
        '''
        parser = argparse.ArgumentParser(description="Generate a directory tree with text files with random readable words")
        parser.add_argument("-lvl", "--levels" , type=int,  default=3, help="number of tree levels, default: 3, minimum: 1")
        parser.add_argument("-sub", "--subdirs", type=int,  default=5, help="number of sub-directories at the top level, default: 5, minimum: 2")
        parser.add_argument("-prf", "--prefix" , type=int,  default=0, help="line prefix type: 0 - without (default), 1 - numeric time, 2 - alpha time")

        parser.add_argument("-ver", "--version", action='version', version='{} ver: {}'.format(parser.prog, VERSION), help="display the version ID and exit")

        cli_args = parser.parse_args()
        self.subdirs = (MINIMUM_SUBDIRS, cli_args.subdirs)[cli_args.subdirs > MINIMUM_SUBDIRS]  # set 'subdirs' after validity checking
        self.levels  = (MINIMUM_LEVELS,  cli_args.levels )[cli_args.levels  > MINIMUM_LEVELS ]  # set 'levels'  after validity checking
        self.prefix  = (PREFIX_NONE,     cli_args.prefix )[cli_args.prefix <= PREFIX_ALPHA_TIME and cli_args.prefix >= PREFIX_NONE]

def get_words():
    ''' convert the dictionary pointed by <WORDS_POOL> to a list
    '''
    global g_words
    with open(WORDS_POOL) as wp:
        g_words = wp.readlines()
    return g_words

def get_random_word():
    global g_words
    rnd = randint(0, len(g_words)-1)
    return g_words[rnd].strip()

def generate_task(dir_name, task_list, line_prefix):
    rnd = randint(0, 16)     # this will tell how many files are going to be created in this directory
    for f in range(rnd):
        fullpath = "{dname}/{num:02d}_{fname}.txt".format(dname=dir_name, num=f+1, fname=get_random_word())
        task_list.append(Task(fullpath, line_prefix))    # append a Task instance to the task list

def create_and_fill_file(t:Task) -> None:
    with open(t.file, 'w') as f:
        for line in range(t.lines):
            words_in_this_line = randint(0, 16)      # acquire number of words in the current line
            line_lst = [get_random_word() for n in range(words_in_this_line)]
            prefix_func = t.prefix_funcs[t.prefix_type]
            line_str = prefix_func() + " ".join(line_lst) + "\n"
            f.write(line_str)

def generate_dirs_and_files(root, subdirs, level, task_list_output, max_levels, line_prefix) -> None:
    if level > max_levels:
        return
    for sd in range(1, subdirs+1):
        dir_name = "{p}/{lvl}{sd}_{w}".format(p=root, lvl=level, sd=sd, w=get_random_word())
        path = Path(dir_name)
        path.mkdir(parents=True, exist_ok=True)
        generate_task(dir_name, task_list_output, line_prefix)
        generate_dirs_and_files(dir_name, subdirs, level+1, task_list_output, max_levels, line_prefix)   # recursion

def next_task(task_list):
    for t in task_list:
        yield t
    return

def main():
    global g_words
    task_lst = []           # list of tasks
    cli = CLI()             # parse command line
    g_words = get_words()   # fill the list 'words' with words, will be used later as the files' content source
    generate_dirs_and_files(root             = './generated_files',
                            subdirs          = cli.subdirs,
                            level            = 1,
                            task_list_output = task_lst,
                            max_levels       = cli.levels,
                            line_prefix      = cli.prefix)
    CPUs = os.cpu_count()
    with Pool(CPUs) as pool:
        scores = pool.map(create_and_fill_file, next_task(task_lst))

if __name__ == "__main__":
    started = time.time()
    main()
    elapsed = time.time() - started
    print("\ntime elapsed: {:.2f}s".format(elapsed))
    print("consider running:\n\tfind . -type f -name \"*.txt\" -exec wc -l {} +\nto check what the scrip has generated")

