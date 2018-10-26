import datetime, errno, os, sys


def timestamp():
    return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())


def makedirs(path):
    """
    Create path, and don't raise an error if the folder already exists
    (similar to os.makedirs(path, exist_ok=True) in more recent versions of python)
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def indent(s, n=4):
    lines = s.splitlines()
    for i in range(len(lines)):
        lines[i] = ''.join([' ']*n)+lines[i]+"\n"
    o = ''.join(lines)
    return o


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


def check_folder_exists(path):
    """
    Check folder exists, raise ValueError if not.

    """
    if not os.path.isdir(path):
        raise ValueError("Error: \"" + path + "\" is not a folder")


def parse_paired_input_folder(input_folder):
    check_folder_exists(input_folder)
    R1 = []
    R2 = []
    file_list = [f for f in os.listdir(input_folder) if not os.path.isdir(f)]
    exts = [".fastq", ".fq", ".fastq.gz"]
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
            msg += " underscore-separated R1 and R2 fields in the filename. Please rename these files to "
            msg += "identify paired reads, or provide unpaired reads with --unpaired-folder."
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

    return R1, R2


def parse_unpaired_input_folder(input_folder):
    check_folder_exists(input_folder)
    file_list = [f for f in os.listdir(input_folder) if not os.path.isdir(f)]
    exts = [".fastq", ".fq", ".fastq.gz"]
    file_list = [f for f in file_list if any([f.endswith(ext) for ext in exts])]
    file_list.sort()

    if len(file_list)==0:
        msg = "Error: no fastq reads found in folder {}".format(input_folder)
        raise RuntimeError(msg)
    U = [os.path.join(input_folder, f) for f in file_list]

    return U