#!/usr/bin/env python

__doc__=="""Zippy"""
__author__ = "David Brawand"
__license__ = "MIT"
#__version__ = "2.3.4"
from zippy import __version__
__maintainer__ = "David Brawand"
__email__ = "dbrawand@nhs.net"
__status__ = "Production"

from .primer import Primer, PrimerPair
import time
import os
import subprocess

'''version string'''
# pipeline version string
def githash(prefix=None):
    taghash, headhash = {},{}
    gitrevision = [ prefix ] if prefix else []
    head = None
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    for i, line in enumerate(subprocess.check_output(['git', 'show-ref', '--head', '--abbrev=7'],cwd=APP_ROOT).split('\n')):
        f = line.split()
        if len(f)==2:
            if f[1] == 'HEAD':
                head = f[0]
            elif 'tags' in f[1]:
                taghash[f[0]] = f[1].split('/')[2]
            elif 'heads' in f[1]:
                headhash[f[0]] = '/'.join(f[1].split('/')[2:])
    # add head name
    try:
        gitrevision.append(headhash[head])
    except:
        gitrevision.append('detached')
    # add tag name
    try:
        gitrevision.append(taghash[head])  # return tag name
    except KeyError:
        gitrevision.append(head)  # return hash of revision
    return '-'.join(gitrevision)


'''static stuff'''
imageDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../static')

'''read configuration (convert unicode to ascii string)'''
def ww_ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii') if type(x) is str else x
    return dict(map(ascii_encode, pair) for pair in data.items())

'''banner'''
def banner(versionstring=''):
    return '''
    \033[1;37m    ZIPPY '''+versionstring+'''\033[0m
    \033[1;37m    Primer design tool and database  \033[0m
    \033[1;37m    (c) Viapath LLP                  \033[0m
    '''

'''recursive function to flatten arbitrarily nested containers (list,tuples)'''
def flatten(container):
    # put in a list if it isn't
    if type(container) is not list and type(container) is not tuple and type(container) is not PrimerPair:
        yield container
    else:
        for i in container:
            if isinstance(i, list) or isinstance(i, tuple):
                for j in flatten(i):
                    yield j
            else:
                yield i

"""Generates the characters from `c1` to `c2`, inclusive."""
def char_range(c1, c2):
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)

"""Generates a range string for the exon numbers"""
def _segment_str(segment):
    if segment[0] == segment[1]:
        return str(segment[0])
    else:
        return f"{segment[0]}-{segment[1]}"

def range_string(exon_numbers):
    #"_".join(sorted(exons))
    #assume exon_numbers is a sorted list of integers
    exon_numbers = list(map(int, exon_numbers))
    if len(exon_numbers)==0:
        return ""
    elif len(exon_numbers)==1:
        return str(exon_numbers[0])
    for (inumber, number) in enumerate(exon_numbers):
        if inumber == 0:
            chunks = [[number, number]]
        elif inumber == (len(exon_numbers) + 1) or number == (lastnum + 1):
            chunks[-1][1] = number
        else:
            #print("refill", lastnum, number)
            chunks[-1][1]= lastnum
            chunks.append([number, number])
        lastnum = number
    return ",".join(_segment_str(chunk) for chunk in chunks)

'''exception class for configuration errors'''
class ConfigError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "[!] CONFIGURATION ERROR\n\t", repr(self.value)

'''exception class for plate errors (full, ...)'''
class PlateError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "[!] PLATE ERROR \n\t", repr(self.value)

'''simple progress bar with time estimation'''
class Progressbar(object):
    def __init__(self,total,name='',maxlen=50,char='|'):
        self.start = time.time()
        self.total = total
        self.name = name
        self.maxlen = maxlen
        self.char = char

    def show(self,i):
        if i == 0:
            self.start = time.time()  # set new start time
        eta = str(int((self.total-i)*float(time.time()-self.start)/float(i))) if i and i/float(self.total)>0.02 else '?'
        return ("{name:} [{progress:<"+str(self.maxlen)+"}] {done:} (ETA {eta:>2}s)").format(\
            name=self.name, progress=self.char*( int(self.maxlen*i/float(self.total)) if self.total != 0 else self.maxlen), done=str(i)+'/'+str(self.total), eta=eta)
