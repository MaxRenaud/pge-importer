__author__ = 'Max Renaud'
from subprocess import check_output, call
import re


def find_next_ts(file_name):
    #Should be in the config file
    output = check_output(['/usr/bin/rrdtool', 'info', file_name])
    #So many things can do wrong here. TODO: Exception
    return int(re.search(r'last_update\s+=\s+(\d+)\n', output).group(1))


def update_rrd(file_name, timestamp, value):
    arg = "{0}:{1}".format(timestamp, value)
    #Should be in the config file
    return call(['/bin/rrdtool', 'update', file_name, arg])