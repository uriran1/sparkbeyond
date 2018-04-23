#!/usr/bin/env python3

import sys
import time
import os
from collections import Counter
from multiprocessing import Pool
from typing import List, Tuple, Iterable    # for type hints, see [https://docs.python.org/3/library/typing.html]
from enum import Enum

from cli import CLI, CLI_type, Timetag, Numr_TM_Window

VERSION = '0.2'

class Timetag_State(Enum):
    TTS_NONE = 0             # not in time frame mode any more
    TTS_OFF  = 1             # not in the time frame window, seek for start timetag
    TTS_ON   = 2             #     in the time frame window, seek for stop  timetag

DO_NOT_SKIP = False
SKIP        = True
class Task:
    def __init__(self, file_name:str, timetag=None, tt_lst:List=None):
        self.file     = file_name
        self.timetag  = timetag
        self.tt_list  = tt_lst
        self.tt_state = Timetag_State.TTS_OFF
        self.tt_indx  = 0                       # index to the next tt_list item

    def skip_numeric_tt_line(self, tt:int) -> bool:
        if self.tt_state == Timetag_State.TTS_NONE:
            return SKIP         # no more active time-windows
        time_to_start = self.tt_list[self.tt_indx].start
        time_to_stop  = self.tt_list[self.tt_indx].stop
        if self.tt_state == Timetag_State.TTS_OFF:
            # is it time to read lines?
            if tt < time_to_start:
                return SKIP
            elif tt >= time_to_stop:
                return SKIP
            else:
                self.tt_state = Timetag_State.TTS_ON
                return DO_NOT_SKIP
        elif self.tt_state == Timetag_State.TTS_ON:
            # is it time to stop reading lines?
            if tt >= time_to_stop:
                self.tt_state = Timetag_State.TTS_OFF
                self.tt_indx += 1
                if self.tt_indx >= len(self.tt_list):
                    self.tt_state = Timetag_State.TTS_NONE
                return SKIP
            else:
                return DO_NOT_SKIP
        else:
            print("assert, unknown self.tt_state {}".format(self.tt_state))

class File_Handle:
    def __init__(self, task_lst):
        self.task_list = task_lst
        self.time_tag  = None
        self.tt_list   = None   # list of time frame windows

    def file_handle(self, file_name:str, timetag=None, tt_lst:List=None) -> None:
        self.task_list.append(Task(file_name, timetag, tt_lst))

def ignore_file(path:str) -> bool:
    for suffix in [ '.asl', '.gz', '.bz2', '.bin', '.pklg', 'StoreData', '.swp', '.pyc', '.pdf' ]:
        if path.endswith(suffix):
            return True
    else:
        return False

def score_file_words(t:Task) -> Counter:
    path = t.file
    c = Counter()
    try:
        with open(path, 'r') as f:
            try:
                for line in f:
                    words = line.split()
                    try:
                        if t.timetag == Timetag.TT_NUMERIC and words[0].isnumeric():
                            if SKIP == t.skip_numeric_tt_line(int(words[0])):
                                continue        # this is an out-of-time-window line
                            else:
                                words.pop(0)    # read line but do not count its timetag
                    except (IndexError):
                        continue                # means empty line, ignore
                    c.update(Counter(words))    # do the actual word counting
            except (UnicodeDecodeError, PermissionError) as ex:
                if not ignore_file(path):
                    print("skipping(4) {e} {p}".format(e=ex, p=path))
    except (PermissionError) as ex:
        if not ignore_file(path):
            print("skipping(3) {e} {p}".format(e=ex, p=path))
    return c

def next_task(tasks:Iterable[str]) -> str:
    for t in tasks:
        yield t
    return

def print_results(mc:List[Tuple[str,int]]) -> None:      # mc stands for 'most common'
    if len(mc) == 0:
        print("Nothing was found")
        return
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
    if check_version() == False:            # check for the right Python version
        return
    task_list = []                          # list of Task objects, one per input file
    fh  = File_Handle(task_list)
    cli = CLI(fh.file_handle, VERSION)      # the command line parser
    for msg in cli.cli_log:                 # print messages created by cli object
        print(msg)                          # during command line parsing

   #CPUs = os.cpu_count()                   # get number of cores
    CPUs = min(6, os.cpu_count())
    with Pool(CPUs) as pool:
   #with Pool(1) as pool:       # :ur: 1
        scores = pool.map(score_file_words, next_task(task_list))
    total_count = Counter()
    for s in scores:
        total_count.update(s)               # aggregate all counts
    mc = total_count.most_common(cli.top_n)
    print_results(mc)                       # print the top_n most common words
                                            # along with their appearance counter

    print('\nPython {}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
    print('total {n:,} words'.format(n=sum(total_count.values())))

if __name__ == "__main__":
    started = time.time()
    main()
    elapsed = time.time() - started
    print("time elapsed: {:.2f}s".format(elapsed))

