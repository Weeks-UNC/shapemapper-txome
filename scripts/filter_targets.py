#!/usr/bin/env python

import sys, os
from argparse import ArgumentParser as AP

ap = AP()
ap.add_argument("--id-file", type=str, required=True)
ap.add_argument("--target", type=str, nargs='+')
ap.add_argument("--out", type=str, required=True)

pa = ap.parse_args()

ids = set(open(pa.id_file,"rU").read().strip().split())
out = open(pa.out, "w")


def parse_fasta(filename):
    f = open(fa, "rU")
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

selected_id_count = 0
total_id_count = 0
seqs = {ID:"" for ID in ids}
for fa in pa.target:
    for ID, seq in parse_fasta(fa):
        total_id_count += 1
        if ID in ids:
            selected_id_count += 1
            fmt_seq = '\n'.join([seq[i:i+80] for i in range(0, len(seq), 80)])
            out.write(">{}\n{}\n".format(ID, fmt_seq))

print("Wrote {} out of {} total sequences to {}".format(
    selected_id_count, total_id_count, pa.out
))