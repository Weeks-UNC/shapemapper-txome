#!/usr/bin/env python

import sys,os
from argparse import ArgumentParser as AP
from random import choice

ap = AP()
ap.add_argument("--in", dest='input', type=str, required=True)
ap.add_argument("--out", type=str, required=True)
ap.add_argument("--multimapper-mode", type=str, default='exclude')

pa = ap.parse_args()

o = open(pa.out, "w")


def iter_sam(filename):
    field_lists = [[], []]
    current_ID = None
    for line in open(filename, "rU"):
        # skip headers
        if line[0] == '@':
            continue
        fields = line.strip().split('\t')
        target = fields[2].split()[0]
        # skip unmapped
        if target == '*':
            continue
        ID = fields[0]
        if ID != current_ID:
            if current_ID is not None:
                if len(field_lists[1]) == 0:
                    field_lists[1] = [None]*len(field_lists[0])
                yield field_lists
            field_lists = [[], []]
            current_ID = ID

        flags = int(fields[1])
        #if flags & 64:
        #    read = 'R1'
        r2 = flags & 128
        if not r2:
            field_lists[0].append(fields)
        else:
            field_lists[1].append(fields)

    if len(field_lists[1]) == 0:
        field_lists[1] = [None]*len(field_lists[0])
    yield field_lists


def filter_sam(filename):
    for field_lists in iter_sam(filename):
        #r1_field_lists = field_lists[0]
        #r2_field_lists = field_lists[1]
        if len(field_lists[0]) == 1:
            yield [field_lists[0][0], field_lists[1][0]]
        else:
            if pa.multimapper_mode == 'exclude':
                continue
            elif pa.multimapper_mode == 'first':
                # find alignment kallisto designated 'primary'
                # and yield only that one. This is usually the first one
                # by listed order in fasta files provided to kallisto, but
                # apparently not always.
                #for R1, R2 in zip(field_lists[0], field_lists[1]):
                #    flags = int(R1[1])
                #    if flags & 256:
                #        # NOTE: (FIXME: maybe submit a PR to kallisto eventually)
                #        # - kallisto's usage is the opposite of the SAM spec
                #        # - kallisto appears to set this flag to indicate the primary alignment
                #        yield [R1, R2]
                #        break

                # just yield first listed and check if that corresponds
                # to input order
                yield [field_lists[0][0], field_lists[1][0]]
            elif pa.multimapper_mode == 'random':
                ns = list(range(len(field_lists[0])))
                n = choice(ns)
                # FIXME: might be a considered a bug in kallisto.
                # kallisto sometimes doesn't output both mate pairs for
                # secondary alignments. can probably work around by
                # using the primary alignment and just swapping in the
                # randomly chosen target name for that field
                #print('\n')
                #print(field_lists[0][0][0])
                #print(len(field_lists[0]))
                #print(len(field_lists[1]))
                #print(ns)
                #print(n)
                #yield [field_lists[0][n], field_lists[1][n]]
                primary_index = 0
                for i, (R1, R2) in enumerate(zip(field_lists[0], field_lists[1])):
                    flags = int(R1[1])
                    if flags & 256:
                        primary_index = i
                        break
                # replace target name field
                target_name = None
                try:
                    target_name = field_lists[0][n][2]
                except (TypeError, IndexError):
                    pass
                try:
                    target_name = field_lists[1][n][2]
                except (TypeError, IndexError):
                    pass
                try:
                    field_lists[0][primary_index][2] = target_name
                except TypeError:
                    pass
                try:
                    field_lists[1][primary_index][2] = target_name
                except TypeError:
                    pass
                yield [field_lists[0][primary_index], field_lists[1][primary_index]]
            elif pa.multimapper_mode == 'all':
                interleaved = []
                for R1, R2 in zip(field_lists[0], field_lists[1]):
                    interleaved.append(R1)
                    interleaved.append(R2)
                yield interleaved


for field_lists in filter_sam(pa.input):
    for fields in field_lists:
        if fields is not None:
            o.write('\t'.join(fields)+'\n')

#print("{}/{} multimapping reads".format(multimapper_count, total_count))
