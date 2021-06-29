#!/usr/bin/python

import sys
import fileinput
from sh import git

#Format: "oldref newref branch"
for line in fileinput.input():
    print("pre-receive: Trying to push ref: %s" % line)
    old, new, ref = line.split()
    author = ''
    committer = ''
    output = git.log('-1 --pretty=%an {0}'.format(ref))
    print('author', output)
    output = git.log('-1 --pretty=%cn {0}'.format(ref))
    print('committer', output)
