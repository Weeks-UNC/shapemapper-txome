# kallisto-txome

Wrapper scripts for running [ShapeMapper2](https://github.com/Weeks-UNC/shapemapper2) 
on large numbers of transcript targets. Performs a fast
pseudoalignment with `kallisto`, then sorts and splits output by target and runs
separate `shapemapper` instances on each target and associated reads.


### Dependencies

- 64-bit Linux
- Python >= 2.7 (tested with 2.7.6, 2.7.15, and 3.5.5)
- [Kallisto](https://pachterlab.github.io/kallisto/) (tested with 0.44.0)
- [samtools](http://www.htslib.org/) (tested with 1.2 and 1.8)
- sort (tested with GNU coreutils sort 8.21 and 8.22)
- [ShapeMapper2]() (tested with 2.1.2 and 2.1.3)


### Parameters

    -h, --help          show help message and exit

    --paired
    --unpaired

    --modified <file|folder> [<fileB|folderB> ...] 
                        Compressed or uncompressed FASTQ files, listed in
                        pairs of R1 R2, or folders of the same (treated
                        sample).
    --untreated <file|folder> [<fileB|folderB> ...]
                        Compressed or uncompressed FASTQ files, listed in
                        pairs of R1 R2, or folders of the same (untreated
                        sample).

    --target <target1.fa> [<target2.fa> ...]
                        FASTA file(s) containing target sequences.

    --out <str>         Output folder (default: output)

    --min-reads <int>
                        Minimum reads pseudomapping to a target for target
                        inclusion in shapemapper runs. (0 to disable).
                        (default: 10)

    --min-mean-coverage <int>
                        Minumum estimated mean read depth (from pseudomapping)
                        over the length of a given target for target inclusion
                        in shapemapper runs. (0 to disable). (default: 0)

    --multimapper-mode <str>
                        Behavior for a given read pseudomapping to multiple
                        targets. 
                           "exclude": discard all
                           "first": use first listed target
                           "random": randomly select target
                           "all": duplicate read to all mapped targets
                        (default: "exclude")

    --fragment-length <int>
                        Expected mean insert fragment size. Required if input
                        is unpaired, or if '--min-mean-coverage' > 0.
                        (default: 150)

    --fragment-sd <int>
                        Expected insert fragment size standard deviation.
                        (default: 20)

    --platform <str>    Subprocess execution platform: "lsf", "local", or
                        "sge" (default: local)

    --max-jobs <int>    Maximum jobs that will be simultaneously submitted for
                        execution. (default: 1)

    --shapemapper-args <str>
                        Additional arguments to pass to each shapemapper run
                        (enclose these in quotes on the commandline).

    --nproc <int>       Number of CPUs available to bowtie2 and kallisto
                        (default: 4)

    --max-files-per-folder <int>
                        Maximum number of files to create within any folder.
                        (default: 100)


### Example usage

    kallisto-txome --paired --modified modified_sample --untreated untreated_sample --target 16S.fa 23S.fa TPP.fa --shapemapper-args '--random-primer-len 9'


### Notes

Unpaired inputs are currently untested.

Job submission platform support is currently untested (that is, 
setting `--platform` to anything other than `local`).
SGE is probably broken; LSF might be functional.
