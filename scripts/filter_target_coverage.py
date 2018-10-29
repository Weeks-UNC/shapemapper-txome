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

def load_depths(abund, frag_length):
    depths = {}
    abund.readline()
    for line in abund:
        s = line.strip().split()
        if len(s) < 5:
            continue
        # FIXME: index by column header
        # FIXME: handle paired and unpaired input (not sure about kallisto's format),
        #        and the case when only one sample is provided
        ID = s[0]
        length = int(s[1])
        est_counts = float(s[3])
        est_mean_depth = frag_length * est_counts / length
        depths[ID] = est_mean_depth
        print str(est_mean_depth)
    return depths

plus_depths = load_depths(plus_abund, plus_frag_length)
minus_depths = load_depths(minus_abund, minus_frag_length)

selected = []
for ID in plus_depths:
    if plus_depths[ID] >= min_mean_depth and minus_depths[ID] >= min_mean_depth:
        selected.append(ID)
IDs = selected


for ID in IDs:
    o.write("{}\n".format(ID))
