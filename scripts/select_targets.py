#!/usr/bin/env python
'''
Parse kallisto-estimated transcript abundances and filter
target IDs by coverage requirements.
'''

import sys, os
from argparse import ArgumentParser as AP

ap = AP()
ap.add_argument("--frag-len", type=int, default=150)
ap.add_argument("--min-mean-coverage", type=int, default=0)
ap.add_argument("--min-reads", type=int, default=0)
ap.add_argument("--out", type=str, default="filtered_target_IDs.txt")
ap.add_argument("--in", dest='input', type=str, nargs='+', required=True)

pa = ap.parse_args()

plus_file = open(pa.input[0], "rU")
minus_file = None
if len(pa.input) > 1:
    minus_file = open(pa.input[1], "rU")

o = open(pa.out, "w")


headers = plus_file.readline().strip().split()
if minus_file is not None:
    minus_file.readline()
idi = headers.index('target_id')
li = headers.index('length')
ci = headers.index('est_counts')

def parse_line(f):
    dummy = (None, None, None)
    if f is None:
        return dummy
    line = f.readline()
    if line is None:
        return dummy
    s = line.strip().split()
    if len(s) < max(li, ci) + 1:
        return dummy
    id = s[idi]
    length = float(s[li])
    counts = float(s[ci])
    return id, length, counts


while True:
    id1, length1, counts1 = parse_line(plus_file)
    id2, length2, counts2 = parse_line(minus_file)
    if id1 is None:
        break

    if id2 is not None:
        assert (id1 == id2)

    mean_depth1 = pa.frag_len * counts1 / length1
    mean_depth2 = None
    if id2 is not None:
        mean_depth2 = pa.frag_len * counts2 / length2

    keep_ID = True

    # apply read count filter
    if pa.min_reads > 0:
        if counts1 < pa.min_reads:
            keep_ID = False
        if counts2 is not None and counts2 < pa.min_reads:
            keep_ID = False

    # apply mean coverage filter
    if pa.min_mean_coverage > 0:
        if mean_depth1 < pa.min_mean_coverage:
            keep_ID = False
        if mean_depth2 is not None and mean_depth2 < pa.min_mean_coverage:
            keep_ID = False

    if keep_ID:
        o.write("{}\n".format(id1))



