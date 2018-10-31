#!/usr/bin/env bash

mkdir -p ../test
cd ../test

for mmode in exclude first random all; do

../kallisto-txome \
--paired \
--modified test_data/modified \
--untreated test_data/untreated \
--multimapper-mode ${mmode} \
--platform local \
--min-reads 10 \
--out results_${mmode} \
--target test_data/16S.fa test_data/16S_dup.fa test_data/23S.fa test_data/TPP.fa test_data/U1.fa \
--shapemapper-args "--random-primer-len 9"

done
