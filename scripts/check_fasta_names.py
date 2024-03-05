#!/usr/bin/env python

import string
from argparse import ArgumentParser as AP


ap = AP()
ap.add_argument("--target", type=str, nargs='+')

pa = ap.parse_args()


def parse_fasta(filename):
    f = open(filename, "rU")
    ID = ""
    seq = ""
    for line in f:
        if line[0] == '>':
            yield ID, seq
            ID = line[1:].split()[0] # truncate after first whitespace char
                                     # to be consistent with kallisto's behavior
            seq = ""
        else:
            seq += line.strip()
    # handle final sequence
    yield ID, seq

allowed_chars = set(string.uppercase + string.lowercase + string.digits + '-_=+.,')

for filename in pa.target:
    for name, seq in parse_fasta(filename):
        bad_chars = set()
        for c in name:
            if c not in allowed_chars:
                bad_chars.add(c)
        if len(bad_chars) > 0:
            msg = 'FASTA file {} target name "{}" contains disallowed chars: "{}"'
            msg = msg.format(filename, name, ''.join(list(bad_chars)))
            raise RuntimeError(msg)