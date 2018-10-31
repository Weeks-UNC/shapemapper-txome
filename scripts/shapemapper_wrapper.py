import os

from util import gen_folder_names
from util import makedirs

def fmt_shapemapper_cmds(dir='',
                         fasta_locations_file='',
                         input_files=None,
                         fastq_dir='',
                         paired=True,
                         nproc=4,
                         shapemapper_args='',
                         done='',
                         max_files_per_folder=100):
    cmds = []

    # check for stage done file before loading fasta paths
    if os.path.isfile(done):
        return []

    # load fasta paths indexed by target name
    fa_paths = {}
    f = open(fasta_locations_file, 'rU')
    for line in f:
        s = line.strip().split('\t')
        fa_paths[s[0]] = s[1]

    folders = {}
    fastqs = {}
    for sample in input_files.keys():
        folders[sample] = None
        fastqs[sample] = {}  # key: folder name, contents: list of pairs of filenames
        if len(input_files[sample]) == 0:
            fastqs[sample] = None
            continue
        folders[sample] = [f for f in os.listdir(fastq_dir + '/' + sample)
                           if os.path.isdir(fastq_dir + '/' + sample + '/' + f)]
        for folder in folders[sample]:
            filenames = os.listdir(fastq_dir + '/' + sample + '/' + folder)
            if paired:
                r1_filenames = sorted([f for f in filenames
                                       if f.endswith("_R1.fastq")])
                r2_filenames = sorted([f for f in filenames
                                       if f.endswith("_R2.fastq")])
                fastqs[sample][folder] = list(zip(r1_filenames, r2_filenames))
            else:
                r1_filenames = sorted([f for f in filenames
                                       if f.endswith(".fastq")])
                r2_filenames = [None] * len(r1_filenames)
                fastqs[sample][folder] = list(zip(r1_filenames, r2_filenames))

    dest_folder_names = gen_folder_names()
    folder_index = 0
    file_in_folder_count = 0

    for folder in folders["modified"]:
        # FIXME: option to skip completed shapemapper jobs
        for i in range(len(fastqs["modified"][folder])):
            fastq_pair = fastqs["modified"][folder][i]
            if paired:
                target_name = fastq_pair[0].rstrip('_R1.fastq')
            else:
                target_name = fastq_pair[0].rstrip('.fastq')

            dest_folder = dest_folder_names[folder_index]
            makedirs(dir + '/' + dest_folder)
            file_in_folder_count += 1
            if file_in_folder_count >= max_files_per_folder:
                folder_index += 1
                file_in_folder_count = 0

            cmd = (
                "mkdir -p '{dir}/{folder}/{name}' "
                "&& "
                "shapemapper "
                "--name '{name}' "
                "--target '{target}' "
                "--out '{dir}/{dest_folder}/{name}' "
                "--temp '{dir}/{dest_folder}/{name}/temp' "
                "--log '{dir}/{dest_folder}/{name}/log.txt' "
                "--overwrite "
                "--nproc {nproc} "
                "{shapemapper_args} "
            )

            for sample in ["modified", "untreated"]:
                if fastqs[sample] is None:
                    continue
                if paired:
                    cmd += "--{sample} --R1 '{r1}' --R2 '{r2}' ".format(
                        r1=fastq_dir + '/' + sample + '/' + folder + '/' + fastq_pair[0],
                        r2=fastq_dir + '/' + sample + '/' + folder + '/' + fastq_pair[1],
                        sample=sample,
                    )
                else:
                    cmd += "--{sample} --U '{r1}' ".format(
                        r1=fastq_dir + '/' + sample + '/' + folder + '/' + fastq_pair[0],
                        sample=sample,
                    )
            cmd = cmd.format(
                name=target_name,
                dir=dir,
                folder=folder,
                target=fa_paths[target_name],
                nproc=nproc,
                shapemapper_args=shapemapper_args,
                dest_folder=dest_folder,
            )
            cmds.append(cmd)
    return cmds
