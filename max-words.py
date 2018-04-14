#!/usr/bin/env python3

import re
import os
import sys
import time
from enum import Enum
from collections import Counter
from datetime import datetime
from collections import namedtuple
from multiprocessing import Pool
from typing import List, Tuple, Iterable    # for type hints, see [https://docs.python.org/3/library/typing.html]


class CLI_type(Enum):
    NONE            = 0
    BASIC           = 1
    ADV_TIMESTAMP   = 2
    ADV_HUMAN       = 3

g_cli_type = CLI_type.NONE

month_val = { 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr':  4, 'May':  5, 'Jun':  6,
              'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12 }

class Adv_Human_State(Enum):
    HAVENT_STARTED  = 0
    READING         = 1
    STOPPED_READING = 2

Timestamp_alpha = namedtuple('Timestamp_alpha', 'start end')
def next_timestamp(ts:Iterable[Timestamp_alpha]) -> Timestamp_alpha:
    for dt in ts:
        yield dt
    return

MINYEAR = 2018
class Adv_Human:
    time_windows    = []                    # timestamp tuples
    start_timestamp = datetime(MINYEAR,1,1) # timestamp of the current block
    stop_timestamp  = datetime(MINYEAR,1,1) # timestamp of the current block
    state           = Adv_Human_State.HAVENT_STARTED
    get_next_twind  = next_timestamp(time_windows)
    def should_start(line:str) -> bool:
        return False

    def should_stop(line:str) -> bool:
        return False

    def update_datetime():
        t_window = Adv_Human.get_next_twind()
        if t_window:
            print("px {}".format(t_window))
           #Adv_Human.start_timestamp = 
           #Adv_Human.stop_timestamp = 

def ignore_file(path:str) -> bool:
    for suffix in [ '.asl', '.gz', '.bz2', '.bin', '.pklg', 'StoreData' ]:
        if path.endswith(suffix):
            return True
    else:
        return False

def should_read_line(line:str) -> bool:
    global g_cli_type
    if g_cli_type == CLI_type.BASIC:
        return True
    if g_cli_type == CLI_type.ADV_HUMAN:
        if Adv_Human.state == Adv_Human_State.STOPPED_READING:
            return False
        if Adv_Human.state == Adv_Human_State.HAVENT_STARTED:
            if Adv_Human.should_start(line):
                Adv_Human.state = Adv_Human_State.READING
                return True
            else:
                return False
        if Adv_Human.state == Adv_Human_State.READING:
            if Adv_Human.should_stop(line):
                Adv_Human.state = Adv_Human_State.STOPPED_READING
                return False
            else:
                return True
    return False

def score_file_words(path:str) -> Counter:
    c = Counter()
    try:
        with open(path, 'r') as f:
            if g_cli_type == CLI_type.ADV_HUMAN:
               #Adv_Human.update_datetime()
                pass
            try:
                for line in f:
                    if should_read_line(line):
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
    ''' parse command line
        determine cli type (basic, adv_timestamp, or adv_human)
        hold input parameters
    '''
    def is_valid_time_window(self, time_win:str) -> bool:
        # Sat Sep 23 00:34:37 - Sun Sep 24 00:34:37
        WD = 'Sun|Mon|Tue|Wed|Thu|Fri|Sat'
        MO = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'
        MD = '[0-3]\d'   # month day 00, 01, ... 31
        HR = '[012]\d'
        MI = '[0-5]\d'
        SE = MI
        #        1        2        3        4      5      6            7        8        9        10     11     12
        pat = r'({wd})\s+({mo})\s+({md})\s+({hr}):({mi}):({se})\s+-\s+({wd})\s+({mo})\s+({md})\s+({hr}):({mi}):({se})'.format(wd=WD, mo=MO, md=MD, hr=HR, mi=MI, se=SE)
        tw = re.compile(pat, flags=re.ASCII)
        is_tw = tw.match(time_win)
        if not is_tw:
            print("p5 wrong time window: {tw}".format(tw=time_win))
            return False
       #print("P2 time_window: {tw}, match: {b}".format(tw=time_win, b=is_tw))
        hr1 = int(is_tw.group(4))
        hr2 = int(is_tw.group(10))
        if hr1 > 23 or hr2 > 23:
            print("p6 wrong time window: {tw}".format(tw=time_win))
            return False
        md1 = int(is_tw.group(3))
        md2 = int(is_tw.group(9))
        if md1 > 31 or md2 > 31:
            print("p7 wrong time window: {tw}".format(tw=time_win))
            return False

        return True

    def get_cli_type(self, args:List[str]) -> CLI_type:
        arg = args[0]
        if os.path.isdir(arg) or os.path.isfile(arg):
            return CLI_type.BASIC
        try:                    # maybe it's a timestamp number?
            int(arg)            # try to convert the argument to a number
            #:ur: continue... check and save arguments
            return CLI_type.ADV_TIMESTAMP
        except ValueError:
            pass                # no, it's not a timestamp

        time_window_str = ' '.join(args).strip()    # list of strings to one long string
        time_windows = time_window_str.split(',')   # make a list of time windows
        time_windows = [tw.strip() for tw in time_windows]
        for tw in time_windows:
            if self.is_valid_time_window(tw):
                tws = tw.split(' - ')
                tsa = Timestamp_alpha(start=tws[0], end=tws[1])
               #print("p8 {} {}".format(tw, tsa))
                Adv_Human.time_windows.append(tsa)
            else:
                return CLI_type.NONE
        else:
            return CLI_type.ADV_HUMAN

        return CLI_type.NONE

    def __init__(self):
        usage_msg = "{line_1}{space}{line_2}{space}{line_3}".format(
                      line_1="usage: max-words TOP_N PATH [PATH ...]\n",
                      line_2="TOP_N - integer, display the TOP_N most frequent words in the PATH list files\n",
                      line_3="PATH  - file or directory name",
                      space =" " * 7)
        self.type = CLI_type.NONE

        if len(sys.argv) < 3:
            print(usage_msg)
            return

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
        self.type = self.get_cli_type(sys.argv[2:])

def next_file(files:Iterable[str]) -> str:
    for f in files:
        yield f
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
    global g_cli_type
    if check_version() == False:
        return
    files = []                      # list of files to traverse
    cli = CLI()                     # the command line object
    if cli.type == None:            # means that there was a problem while reading the command line
        return

    if cli.type != CLI_type.BASIC and cli.type != CLI_type.ADV_HUMAN:
        print('p1, CLI_type: {t}'.format(t=cli.type))
        return

    if cli.type == CLI_type.BASIC:
        for path in cli.raw_file_list:  # iterate over CLI directories and files
            walk_tree(path, files)      # recursively go through directory trees and get all containing files
    elif cli.type == CLI_type.ADV_HUMAN:
        files.append("/var/log/wifi.log")
        files.append("/var/log/jamf.log")
    else:
        print("p3 cli type {t} is not supported".format(cli.type))
        return

    g_cli_type = cli.type

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

