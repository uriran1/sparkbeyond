#!/usr/bin/env python3

import os
import re
import sys
import argparse
from enum        import Enum
from typing      import List, Tuple, Iterable # for type hints, see [https://docs.python.org/3/library/typing.html]
from collections import namedtuple
from operator    import attrgetter

TOP_N_DEFAULT = 5   # default number of output results
TOP_N_MIN     = 1   # minimum number of output results

Numr_TM_Window = namedtuple('Numr_TM_Window', 'start stop')

class Timetag(Enum):
    TT_NONE    = 0
    TT_NUMERIC = 1
    TT_HUMAN   = 2

class CLI_type(Enum):
    NONE            = 0
    BASIC           = 1
    TM_WIN_NUMERIC  = 2
    TM_WIN_HUMAN    = 3

class CLI:
    ''' parse command line
        save input parameters
    '''
    def check_file_dir_validity(self, file_list:List[str]) -> None:
        for f in file_list:
            if os.path.exists(f):
                self.valid_raw_file_list.append(f)
                continue
            else:
                self.cli_log.append('skipping {path}, does not exist'.format(path=f))

    def check_ttag_numeric_validity(self, numr_list:List[str]) -> None:
        for ttag in numr_list:   # numeric timetag window
            tw_obj = re.match(r'\s*(\d+)\s-\s+(\d+)', ttag)
            if tw_obj == None:
                self.cli_log.append("skipping, {s}, wrong input".format(s=ttag))
                continue
            t_start = tw_obj.group(1)
            t_end   = tw_obj.group(2)
            numr_tm_win = Numr_TM_Window(start=int(t_start), stop=int(t_end))
            if numr_tm_win.stop < numr_tm_win.start:
                self.cli_log.append("skipping, {s} > {e}".format(s=t_start, e=t_end))
                continue
            self.numr_tt_list.append(numr_tm_win)
        self.numr_tt_list.sort(key=attrgetter('start'))
        list_2 = sorted(self.numr_tt_list, key=attrgetter('stop'))
        for a, b in zip(self.numr_tt_list, list_2):
            if a is not b:
                print('time-windows overlap {} {} and {} {}'.format(a.start, a.end, b.start, b.end))
                return False
        return True

    def set_timetag_type(self, args) -> None:
        if args.time_numr != None:
            self.timetag = Timetag.TT_NUMERIC
        elif args.time_humn != None:
            self.timetag = Timetag.TT_HUMAN

    def set_cli_type(self, args) -> None:
        if args.time_numr == None and args.time_humn == None :
            self.cli_type = CLI_type.BASIC      # no type input, use the default
            if args.raw_files == None:
                self.cli_log.append('use CLI_type.BASIC as default')
        elif args.time_numr != None:
            self.cli_type = CLI_type.TM_WIN_NUMERIC
            if args.time_humn != None:
                self.cli_log.append('human readable time-windows ignored in numeric cli mode')

       #elif args.raw_files != None:
       #    self.cli_type = CLI_type.BASIC
       #    if args.time_numr != None:
       #        self.cli_log.append('numeric time-windows ignored in basic cli mode')
       #    if args.time_humn != None:
       #        self.cli_log.append('human readable time-windows ignored in basic cli mode')

    def ignore_directory(self, path:str) -> bool:
        for prefix in [ './.git', './bkup', './__pycache__' ]:
            if path.startswith(prefix):
                return True
        else:
            return False

    def walk_tree(self, path:str) -> None:
        if os.path.isdir(path):             # if it's a directory go through its content
            if self.ignore_directory(path):
                return
            try:
                for f in os.listdir(path):
                    pathname = os.path.join(path, f)
                    self.walk_tree(pathname)     # recursion
            except (PermissionError) as ex:
                self.cli_log.append("skipping(2) {e}".format(e=ex))
        elif os.path.isfile(path):
            self.fh(path, self.timetag, self.numr_tt_list)   # this file should be scanned later, call its handle method
        else:
            print("skipping(1) {}".format(path))

    def __init__(self, file_handle, version:str) -> None:   # CLI ctor
        self.cli_type = CLI_type.NONE
        self.timetag  = Timetag.TT_NONE
        self.fh       = file_handle
        self.cli_log             = []   # list of messages for the CLI.__init__() caller
        self.valid_raw_file_list = []   # list of file/dir names before testing their validity
        self.numr_tt_list        = []   # list of numeric timetags

        parser = argparse.ArgumentParser(description="Count number of word appearance in files")
        xor_group = parser.add_mutually_exclusive_group()
        parser.add_argument   ("-top", "--top_n"    , type=int, default=TOP_N_DEFAULT, help="number of most common words to display")
        parser.add_argument   ("-dbg", "--debug"    , action='store_true', help="print all the file names were parsed within the same time-window")
        parser.add_argument   ("-ver", "--version"  , action='version'   , version='{p} ver: {v}'.format(p=parser.prog, v=version), help="display version number")
        parser.add_argument   ("-f",   "--raw_files", action='append'    , help="file or directory name to be scanned for word appearance counting, default - current directory")
        xor_group.add_argument("-twn", "--time_numr", action='append'    , help="numeric time-window, example: -twn \"1506200432 - 1506286832\" -twn \"1505077232 - 1505250032\"")
        xor_group.add_argument("-twh", "--time_humn", action='append'    , help="human readable time-window, example: -twh Sat Sep 23 00:34:37 - Sun Sep 24 00:34:37")

        args = parser.parse_args()

        if args.top_n < TOP_N_MIN:
            self.top_n = TOP_N_MIN
            self.cli_log.append('invalid --top_n argument, use the minimum ({m})'.format(m=TOP_N_MIN))
        else:
            self.top_n = args.top_n
        self.bebug = args.debug

        self.set_cli_type(args)
        self.set_timetag_type(args)

        if args.raw_files == None:                          # no file/direcotry in the command line
            self.valid_raw_file_list = ['.']                # use the default - current directory
            self.cli_log.append('no file list input, use current directory as default file list')
        else:
            self.check_file_dir_validity(args.raw_files)    # is what appears as file really a file?

        if self.cli_type == CLI_type.TM_WIN_NUMERIC:
            if False == self.check_ttag_numeric_validity(args.time_numr):
                self.cli_type = CLI_type.NONE
        elif self.cli_type == CLI_type.TM_WIN_HUMAN:
            pass

        for path in self.valid_raw_file_list:   # iterate over CLI directories and files
            self.walk_tree(path)                # recursively go through directory trees
                                                # and get all containing files

