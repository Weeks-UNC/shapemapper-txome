#!/usr/bin/env bash

mkdir -p ../test
cd ../test

# run full dataset tests on longleaf (local mode, but submit this script as a job)
# FIXME: also try with python2 and 3 to check compatible with both
# FIXME: also run shapemapper directly to check comparable depths
# FIXME: check if shapemapper-args passed through correctly and
# update usage string to reflect quotes or whatever

for mmode in exclude random all; do

../kallisto-wrapper \
--paired \
--modified test_data/modified \
--untreated test_data/untreated \
--multimapper-mode ${mmode} \
--platform local \
--min-reads 10 \
--out results_${mmode} \
--target test_data/16S.fa test_data/23S.fa test_data/TPP.fa \
--shapemapper-args "--random-primer-len 9"

done
