#!/usr/bin/env python3

import os
import time
import argparse
from pathlib import Path
from random import randint
from multiprocessing import Pool

# run the command below to check the script's output
# find . -type f -name "*.txt" -exec wc -l {} +

LEVELS  = 3
SUBDIRS = 5

g_version = 0.1

words_pool = "/usr/share/dict/words"    # a dictionary, used as source of words
g_words = []                            # holds the dictionary as a list for random access

class CLI:
    def __init__(self):
        ''' Parse command line
        '''
        parser = argparse.ArgumentParser(description="Generate directory tree with text files that contain random words")
        parser.add_argument("-lvl", "--levels" , type=int,  default=3, help="number of tree levels")
        parser.add_argument("-sub", "--subdirs", type=int,  default=5, help="number of sub-direcotries at the top level")

        parser.add_argument("-ver", "--version", action='version', version='{} ver: {}'.format(parser.prog, g_version), help="disply the version number")

        self.subdirs = parser.parse_args().subdirs
        self.levels  = parser.parse_args().levels

def get_words():
    ''' convert the dictionary pointed by <words_pool> to a list
    '''
    global g_words
    with open(words_pool) as wp:
        g_words = wp.readlines()
    return g_words

def get_random_word():
    global g_words
    rnd = randint(0, len(g_words)-1)
    return g_words[rnd].strip()

def generate_file_names(dir_name, files):
    rnd = randint(0, 16)     # this will tell how many files are going to be created in this directory
    for f in range(rnd):
        fullpath = "{dname}/{num:02d}_{fname}.txt".format(dname=dir_name, num=f+1, fname=get_random_word())
        files.append(fullpath)

def create_and_fill_file(fullpath):
    with open(fullpath, 'w') as f:
        lines_in_file = randint(0, 1000)        # acquire number of lines in the current file
        for line in range(lines_in_file):
            words_in_line = randint(0, 16)      # acquire number of words in the current line
            line_lst = [get_random_word() for n in range(words_in_line)]
            line_str = " ".join(line_lst) + "\n"
            f.write(line_str)

def generate_files(dir_name):
    rnd = randint(0, 16)     # this will tell how many files are going to be created in this directory
    for f in range(rnd):
        fullpath = "{dname}/{num:02d}_{fname}.txt".format(dname=dir_name, num=f+1, fname=get_random_word())
        print(fullpath)
        with open(fullpath, 'w') as gen_file:
            lines_in_file = randint(0, 1000)        # the number of lines in this file
            for line in range(lines_in_file):
                words_in_line = randint(0, 16)      # the number of words in this line
                line_lst = [get_random_word() for n in range(words_in_line)]
                line_str = " ".join(line_lst) + "\n"
                gen_file.write(line_str)

def generate_dirs_and_files(parent, level, file_list_output):
    if level > LEVELS:
        return
    for sd in range(1, SUBDIRS+1):
        dir_name = "{p}/{lvl}{sd}_{w}".format(p=parent, lvl=level, sd=sd, w=get_random_word())
        path = Path(dir_name)
        path.mkdir(parents=True, exist_ok=True)
       #generate_files(dir_name)
        generate_file_names(dir_name, file_list_output)
        generate_dirs_and_files(dir_name, level+1, file_list_output)

def next_file(files):
    for f in files:
        yield f
    return

def main():
    global g_words
    file_lst = []           # list of file names to create and fill with content
    cli = CLI()             # parse command line
    g_words = get_words()   # fill the list 'words' with words, will be used later as the files' content source
    generate_dirs_and_files('./gen_files', level=1, file_list_output=file_lst)     # :ur: move to command line
    CPUs = os.cpu_count()
    with Pool(CPUs) as pool:
        scores = pool.map(create_and_fill_file, next_file(file_lst))

if __name__ == "__main__":
    started = time.time()
    main()
    elapsed = time.time() - started
    print("\ntime elapsed: {:.2f}s".format(elapsed))

