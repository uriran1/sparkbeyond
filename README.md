# sparkbeyond
Home task

`max-words.py` is a Python script that recuresively scan files and counts how many times each word appears in these files.

Usage: `max-words.py [-h] [-top TOP_N] [-dbg] [-ver] [-f RAW_FILES] [-twn TIME_NUMR | -twh TIME_HUMN]`

`TOP_N` is an integer, the number of words to display from the most common word to the less common\
`RAW_FILES` is a  / are file name(s) to be scanned by the script, more than one file can be listed\
if file is a directory it will be recursively scand for more files and sub-direcotries

The script skips non-utf-8 files\
The script was tested with Python 3.6.5 on MacOS 10.12.6

Example:   `max-words.py -top 5 -f /var/log`\
displays the 5 most common words in all text file in and below `/var/log`

`gen_files.py` is a Python script for building a test environment for `max-words.py`

Usage: `./gen_files.py`\
It creates a directory tree with files that contain random readable words\
The words are taken from the `/usr/share/dict/words` dictionary\
After running `gen_files.py` run the following command to check what was produced:\
`find . -type f -name "*.txt" -exec wc -l {} +`\
Now run `max-words.py ./gen_files` on the generated files and then check the resaults against the result of\
`grep -o WORD $(find . -name "*.txt") | wc -l`\
replace `WORD` with the tested word
