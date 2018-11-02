#!/usr/bin/env python
'''
Parse sam files, count reads, and filter
target IDs by read count requirements.
'''

import sys, os
from argparse import ArgumentParser as AP

ap = AP()
ap.add_argument("--min-reads", type=int, default=0)
ap.add_argument("--out", type=str, default="filtered_target_IDs.txt")
ap.add_argument("--in", dest="input", type=str, nargs='+', required=True)

pa = ap.parse_args()

filenames = {"modified":pa.input[0], "untreated":None}
if len(pa.input) > 1:
    filenames["untreated"] = pa.input[1]


def iter_sam(filename):
    field_lists = [None, None]
    for line in open(filename, "rU"):
        # skip headers
        if line[0] == '@':
            continue
        fields = line.strip().split()
        target = fields[2]
        # skip unmapped
        if target == '*':
            continue
        flags = int(fields[1])
        paired = flags & 1
        r2 = flags & 128
        if not r2:
            field_lists[0] = fields
        else:
            field_lists[1] = fields
        if paired:
            if field_lists[0] is not None and field_lists[1] is not None:
                yield field_lists
                field_lists = [None, None]
        else:
            yield field_lists
            field_lists = [None, None]
    if any([field_lists[i] is not None for i in [0,1]]):
        yield field_lists

target_read_counts = {}
samples = []
for n, sample in enumerate(['modified','untreated']):
    if filenames[sample][n] is None:
        continue
    samples.append(sample)
    target_read_counts[sample] = {}
    for pair in iter_sam(filenames[sample]):
        target = None
        for i in [0,1]:
            if pair[i] is not None:
                if pair[i][2] != '*':
                    target = pair[i][2]
        if target not in target_read_counts[sample]:
            target_read_counts[sample][target] = 0
        target_read_counts[sample][target] += 1

o = open(pa.out, "w")
for target in target_read_counts['modified']:
    keep_target = True
    for sample in samples:
        try:
            if target_read_counts[sample][target] < pa.min_reads:
                keep_target = False
        except KeyError:
            keep_target = False
    if keep_target:
        o.write("{}\n".format(target))

#from pprint import pprint
#pprint(target_read_counts)
#exit(1)


