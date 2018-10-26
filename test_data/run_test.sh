#!/usr/bin/env bash

mkdir -p ../test
cd ../test

# FIXME: also try with python2 and 3 to check compatible with both

for mmode in exclude random all; do

../kallisto-wrapper \
--paired \
--modified test_data/modified \
--untreated test_data/untreated \
--multimapper-mode ${mmode} \
--platform local \
--min-reads 10 \
--out results_${mmode} \
--target test_data/16S.fa test_data/23S.fa test_data/TPP.fa

done
