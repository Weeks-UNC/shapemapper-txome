#!/usr/bin/env python

import sys, os, errno
from argparse import ArgumentParser as AP

from util import makedirs, gen_folder_names

# def makedirs(path):
#     """
#     Create path, and don't raise an error if the folder already exists
#     (similar to os.makedirs(path, exist_ok=True) in more recent versions of python)
#     """
#     try:
#         os.makedirs(path)
#     except OSError as exception:
#         if exception.errno != errno.EEXIST:
#             raise


def reverse_complement(seq):
    d = {'A':'T', 'T':'A', 'G':'C', 'C':'G'}
    return ''.join([d[c] if c in d else c for c in seq][::-1])

ap = AP()
ap.add_argument("--in", dest='input', type=str, required=True)
ap.add_argument("--out", type=str, required=True)
ap.add_argument("--selected-target-ids", type=str, default="")
ap.add_argument("--max-files-per-folder", type=int, default=2)

g = ap.add_mutually_exclusive_group(required=True)  # not sure if required supported for groups
g.add_argument("--paired", dest="paired", action="store_true")
g.add_argument("--unpaired", dest="paired", action="store_false")
ap.set_defaults(paired=True)

pa = ap.parse_args()

makedirs(pa.out)

folder_names = gen_folder_names()

selected_target_ids = None
if pa.selected_target_ids != "":
    selected_target_ids = set(open(pa.selected_target_ids, 'rU').read().strip().split())

f = open(pa.input, "rU")
o1 = None
o2 = None
o = None
folder_index = 0
file_in_folder_count = 0

def open_new_output_files(target_name):
    global o
    global o1
    global o2
    global folder_index
    global file_in_folder_count
    folder_name = folder_names[folder_index]
    makedirs(pa.out+'/'+folder_name)
    if pa.paired:
        o1 = open('{out}/{folder_name}/{target_name}_R1.fastq'.format(
            out=pa.out,
            folder_name=folder_name,
            target_name=target_name,
        ), 'w')
        o2 = open('{out}/{folder_name}/{target_name}_R2.fastq'.format(
            out=pa.out,
            folder_name=folder_name,
            target_name=target_name,
        ), 'w')
    else:
        o = open('{out}/{folder_name}/{target_name}.fastq'.format(
            out=pa.out,
            folder_name=folder_name,
            target_name=target_name,
        ), 'w')
    # FIXME: either have an off-by-one error here, or am not correctly
    # handling skipped targets
    file_in_folder_count += 1
    if pa.paired:
        file_in_folder_count += 1
    if file_in_folder_count >= pa.max_files_per_folder:
        folder_index += 1
        file_in_folder_count = 0


current_target = None

for line in f:
    fields = line.strip().split()
    ID = fields[0]
    flags = int(fields[1])
    target = fields[2]
    seq = fields[9]
    qual = fields[10]
    r2 = flags & 128
    reversed = flags & 16
    do_write = True
    if selected_target_ids is not None and target not in selected_target_ids:
        do_write = False
    if do_write and (current_target is None or target != current_target):
        open_new_output_files(target)
        current_target = target
    o_handle = o
    if pa.paired:
        o_handle = o1
        if r2:
            o_handle = o2
    if do_write:
        if reversed:
            seq = reverse_complement(seq)
            qual = qual[::-1]
        o_handle.write("@{}\n{}\n+\n{}\n".format(ID, seq, qual))
