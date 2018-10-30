#!/usr/bin/env python

import sys, os
from argparse import ArgumentParser as AP

from util import gen_folder_names, makedirs

ap = AP()
ap.add_argument("--id-file", type=str, required=True)
ap.add_argument("--target", type=str, nargs='+')
ap.add_argument("--out", type=str, required=True)
ap.add_argument("--out-dir", type=str, required=True)
ap.add_argument("--out-fasta-paths", type=str, required=True)
ap.add_argument("--max-files-per-folder", type=int, default=100)

pa = ap.parse_args()

ids = set(open(pa.id_file,"rU").read().strip().split())
out = open(pa.out, "w")


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

makedirs(pa.out_dir)
fa_paths = open(pa.out_fasta_paths, "w")

folder_names = gen_folder_names()

indiv_out = None
folder_index = 0
file_in_folder_count = 0
fa_path = None

def open_new_indiv_out(target_name):
    global indiv_out
    global folder_index
    global file_in_folder_count
    global fa_path
    folder_name = folder_names[folder_index]
    makedirs(pa.out_dir+'/'+folder_name)
    fa_path = '{out}/{folder_name}/{target_name}.fa'.format(
        out=pa.out_dir,
        folder_name=folder_name,
        target_name=target_name,
    )
    indiv_out = open(fa_path, 'w')
    file_in_folder_count += 1
    if file_in_folder_count >= pa.max_files_per_folder:
        folder_index += 1
        file_in_folder_count = 0


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
            open_new_indiv_out(ID)
            indiv_out.write(">{}\n{}\n".format(ID, fmt_seq))
            fa_paths.write("{}\t{}\n".format(ID, fa_path))

print("Wrote {} out of {} total sequences to {}".format(
    selected_id_count, total_id_count, pa.out
))