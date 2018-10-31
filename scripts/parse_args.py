import os
from argparse import ArgumentParser
import argparse
from collections import OrderedDict


def string_distance(s1, s2):
    """
    Calculate the number of characters that differ
    between two strings of identical length. Returns
    1 if lengths do not match.

    """
    if len(s1) != len(s2):
        return 1
    diff_count = 0
    for c1, c2, in zip(s1, s2):
        if c1 != c2:
            diff_count += 1
    return diff_count


def parse_paired_input_folder(input_folder):
    R1 = []
    R2 = []
    file_list = [f for f in os.listdir(input_folder) if not os.path.isdir(f)]
    exts = [".fastq", ".fq", ".fastq.gz", ".fq.gz"]
    file_list = [f for f in file_list if any([f.endswith(ext) for ext in exts])]
    for f in file_list:
        # try to locate "R1" or "R2" in filename, separated from other fields
        # by underscores or periods
        fields = os.path.splitext(os.path.split(f)[1])[0].replace('.','_').split('_')
        if "R1" in fields or "r1" in fields:
            R1.append(f)
        elif "R2" in fields or "r2" in fields:
            R2.append(f)
        else:
            msg = "Error: FASTQ file(s) present in folder \"{}\" that do not contain".format(input_folder)
            msg += " underscore-separated R1 and R2 fields in the filename."
            raise RuntimeError(msg)
    R1.sort()
    R2.sort()
    if len(R1)==0 and len(R2)==0:
        msg = "Error: no fastq reads found in folder \"{}\"".format(input_folder)
        raise RuntimeError(msg)
    for f1, f2 in zip(R1, R2):
        if string_distance(f1, f2) > 1:
            msg = "Error: unable to identify paired read FASTQ files in folder \"" + input_folder + "\""
            msg += ". Ensure that paired files contain underscore-separated R1 and R2 fields in the "
            msg += "filename, and that their filenames are otherwise identical."
            raise RuntimeError(msg)
    R1 = [os.path.join(input_folder, f) for f in R1]
    R2 = [os.path.join(input_folder, f) for f in R2]
    filenames = list(sum(zip(R1, R2), ())) # interleave
    return filenames


def parse_unpaired_input_folder(input_folder):
    file_list = [f for f in os.listdir(input_folder) if not os.path.isdir(f)]
    exts = [".fastq", ".fq", ".fastq.gz", ".fq.gz"]
    file_list = [f for f in file_list if any([f.endswith(ext) for ext in exts])]
    file_list.sort()

    if len(file_list)==0:
        msg = "Error: no FASTQ reads found in folder {}".format(input_folder)
        raise RuntimeError(msg)
    U = [os.path.join(input_folder, f) for f in file_list]

    return U


def check_fastq(path):
    exts = [".fastq", ".fq", ".fastq.gz", ".fq.gz"]
    if not any([path.endswith(ext) for ext in exts]):
        raise RuntimeError('{} does not have a recognized FASTQ extension'.format(path))
    if not os.path.isfile(path):
        raise RuntimeError('FASTQ file {} does not exist, or is not a regular file.'.format(path))


def parse_args(args):
    ap = ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True) # not sure if required supported for groups
    g.add_argument("--paired", dest="paired", action="store_true")
    g.add_argument("--unpaired", dest="paired", action="store_false")
    ap.set_defaults(paired=True)

    ap.add_argument("--modified", type=str, nargs='+', required=True, default=argparse.SUPPRESS,
                    help="Compressed or uncompressed FASTQ files, listed in pairs of R1 R2, or folders of the same (treated sample).")
    ap.add_argument("--untreated", type=str, nargs='+', required=False, default=argparse.SUPPRESS,
                    help="Compressed or uncompressed FASTQ files, listed in pairs of R1 R2, or folders of the same (untreated sample).")

    ap.add_argument("--target", type=str, nargs='+', required=True, default=argparse.SUPPRESS,
                    help="FASTA file(s) containing target sequences.")

    ap.add_argument("--out", type=str, help="Output folder", default="output")

    ap.add_argument("--min-reads", type=int,
                    help="Minimum reads pseudomapping to a target for target inclusion in shapemapper runs. (0 to disable).",
                    default=10)
    ap.add_argument("--min-mean-coverage", type=int,
                    help="Minumum estimated mean read depth (from pseudomapping) over the length of a given target for "
                         "target inclusion in shapemapper runs. (0 to disable).",
                    default=0)
    ap.add_argument("--multimapper-mode", type=str, default='exclude',
                    help='Behavior for a given read pseudomapping to multiple targets: '
                         '"exclude": discard all, '
                         '"first": use first listed target, '
                         '"random": randomly select target, '
                         '"all": duplicate read to all mapped targets.')

    # NOTE: these arguments are required by kallisto if input is unpaired
    ap.add_argument("--fragment-length", type=int, required=False, default=150,
                    help='Expected mean insert fragment size. Required if input '
                         'is unpaired, or if --min-mean-coverage is > 0.')
    ap.add_argument("--fragment-sd", type=int, required=False, default=20,
                    help="Expected fragment size standard deviation.")

    ap.add_argument("--platform", type=str,
                    help='Subprocess execution platform: "lsf", "local", or "sge"',
                    default='local')

    ap.add_argument("--max-jobs", type=int,
                    help="Maximum jobs that will be simultaneously submitted for execution.",
                    default=1)

    ap.add_argument("--shapemapper-args", type=str, required=False, default=argparse.SUPPRESS,
                    help=("Additional arguments to pass to each shapemapper "
                          "run (enclose these in quotes on the commandline)."))

    ap.add_argument("--nproc", type=int,
                    help="Number of CPUs available to bowtie2 and kallisto",
                    default=4)

    ap.add_argument("--max-files-per-folder", type=int,
                    help="Maximum number of files to create within any folder.",
                    default=100)

    pa = ap.parse_args(args)

    if pa.platform not in ['lsf', 'sge', 'local']:
        raise RuntimeError("Job execution platform ('--platform') must be one of: 'lsf','sge','local'.")

    if pa.max_jobs <= 0:
        raise RuntimeError("'--max-jobs' must be greater than 0.")

    if pa.multimapper_mode not in ["exclude", "random", "all", "first"]:
        raise RuntimeError("'--multimapper-mode' must be one of: 'exclude','random','first','all'.")

    pa.input_files = OrderedDict()
    pa.input_files["modified"] = []
    pa.input_files["untreated"] = []
    paths = {'modified':pa.modified, 'untreated':pa.untreated}
    for sample in paths.keys():
        for path in paths[sample]:
            if os.path.isdir(path):
                # process as folder of FASTQs
                if pa.paired:
                    pa.input_files[sample] += parse_paired_input_folder(path)
                else:
                    pa.input_files[sample] += parse_unpaired_input_folder(path)
            else:
                # process as FASTQ filename, assume pairs listed sequentially R1 R2 R1_a R2_b etc.
                check_fastq(path)
                pa.input_files[sample].append(path)
        if pa.paired and (len(pa.input_files[sample]) % 2 != 0):
            raise RuntimeError("Expected an even number of FASTQ files with '--paired' input.")

    return pa
