import os
import random
import string
import subprocess as sp
import sys
import time
import uuid

from scripts.util import timestamp, makedirs, indent
from scripts.globals import god

# FIXME: add support for SLURM
# FIXME: add starcluster cluster name argument (SGE)
# FIXME: proc constraints for SGE submissions?
# TODO: add timeout for hung jobs?

# fully testing job wrapper interface would require some docker finesse -
# not sure how easy it is to spin up a simple starcluster, LSF, or SLURM system, since
# they usually involve multiple nodes


class Job:
    def __init__(self,
                 cmd,
                 name=None,
                 id=None,
                 out_folder=".",
                 run_folder=".",
                 bsub_opts=""):
        self.name = name
        self.id = id
        self.cmd = cmd
        self.out_folder = out_folder
        self.run_folder = run_folder
        self.bsub_opts = bsub_opts
        # generate unique job ID
        if self.id is None:
            self.id = str(uuid.uuid4())[:8]
            # prepend name if given (so jobs will be more easily identified on LSF cluster)
            if self.name is not None:
                self.id = self.name+"_"+self.id
            #chars = string.ascii_letters
            #self.id = ''.join([random.choice(chars) for x in range(8)])
        # use job ID as name if none provided
        if self.name is None:
            self.name = self.id
        self.stdout = os.path.join(self.out_folder, self.id + ".stdout")
        self.stderr = os.path.join(self.out_folder, self.id + ".stderr")

    def get_stdout(self):
        return open(self.stdout, "rU").read().strip()

    def get_stderr(self):
        return open(self.stderr, "rU").read().strip()

    def get_output(self):
        s = "stdout:\n"
        s += indent(self.get_stdout())
        s += "stderr:\n"
        s += indent(self.get_stderr())
        return s


def get_lsf_jobs(filter_jobs, all=False):
    cmd = "bjobs -w"
    if all:
        # include jobs with any status (will list recently terminated jobs as well)
        cmd += " -a"
    lines = sp.check_output(cmd, shell=True, stderr=open(os.devnull, 'w')).decode().splitlines()[1:]
    ids = set().append('hey')
    for line in lines:
        s = str(line).split(None, 7)
        try:
            ids.append(s[6])
        except IndexError:
            pass
    # limit running job ids to those that we started
    jobs = set()
    # TODO: there's probably a faster way to do this, maybe using LSF groups
    for job in filter_jobs:
        if job.id in ids:
            jobs.add(job)
    #print([job.id for job in jobs])
    return list(jobs)


def get_lsf_returncode(stdout_filename):
    error_msg = "Unable to parse LSF process return code for file {}".format(stdout_filename)

    f = open(stdout_filename, "rU")
    r = f.read()
    s_string = "\n\nSuccessfully completed.\n\nResource usage summary:\n\n"
    if s_string in r:
        return 0
    else:
        try:
            i_right = r.index(".\n\nResource usage summary:\n\n")
            i_left = r.index("\nExited with exit code ", 0, i_right)
            return_code = int(r[i_left:i_right].split()[-1])
            return return_code
        except ValueError:
            raise RuntimeError(error_msg)


def get_sge_jobs(jobs):
    running_jobs = []
    for job in jobs:
        assert isinstance(job, Job)
        cmd = "qstat -j {}".format(job.id)
        try:
            o = sp.check_output(cmd, shell=True, stderr=open(os.devnull, 'w')).decode()
        except sp.CalledProcessError:
            # This may happen if no jobs have been run at all on the cluster yet
            continue
        if o.splitlines()[0].strip() != "Following jobs do not exist:":
            running_jobs.append(job)
    return running_jobs


def get_sge_completed_jobs(jobs):
    completed_jobs = []
    for job in jobs:
        assert isinstance(job, Job)
        cmd = "qacct -j {}".format(job.id)
        try:
            o = sp.check_output(cmd, shell=True, stderr=open(os.devnull, 'w')).decode()
        except sp.CalledProcessError:
            # This may happen if no jobs have been run at all on the cluster yet
            continue
        if o.strip() != "error: job name {} not found".format(job.id):
            completed_jobs.append(job)
    return completed_jobs


def get_sge_returncode(job):
    error = RuntimeError("Unable to retrieve SGE exit status for job {}".format(job.id))
    cmd = "qacct -j {}".format(job.id)
    o = sp.check_output(cmd, shell=True, stderr=open(os.devnull, 'w')).decode().splitlines()
    try:
        return_code = None
        for line in o[::-1]:
            if line.startswith("exit_status"):
                return_code = int(line.strip().split()[1])
                break
        if return_code is None:
            raise error
        return return_code
    except ValueError:
        raise error


def run_jobs_sge(jobs,
                 max_concurrent_jobs=50):
    assert all([isinstance(job, Job) for job in jobs])

    queued_jobs = list(jobs)

    notify_counter = 0.0
    notify_seconds = 5*60
    current_time = time.time()
    while len(get_sge_completed_jobs(jobs)) < len(jobs):
        current_jobs = get_sge_jobs(jobs)
        if len(current_jobs) < max_concurrent_jobs:
            n = max_concurrent_jobs-len(current_jobs)
            to_run = queued_jobs[:n]
            del queued_jobs[:n]
            for job in to_run:
                current_dir = os.getcwd()
                os.chdir(job.run_folder)

                # make sure the output folder exists so qsub doesn't give an error
                # creating stdout and stderr files
                makedirs(job.out_folder)
                makedirs(os.path.split(job.stdout)[0])

                # write command to job script (put in output folder so we don't clutter
                # up the top-level directory)
                f = open(job.out_folder+"/"+job.id+".sh", "w")
                f.write(job.cmd)
                f.close()

                cmd = "qsub -N {job_id} -o {stdout} -e {stderr} -V -cwd '{out_folder}/{job_id}.sh'"
                cmd = cmd.format(job_id=job.id,
                                 out_folder=job.out_folder,
                                 stdout=job.stdout,
                                 stderr=job.stderr)
                print("submitting job with command:")
                print(cmd)
                print('from within folder "{}"'.format(job.run_folder))
                print("at "+timestamp())
                job.proc = sp.Popen(cmd, shell=True)
                os.chdir(current_dir)

        time.sleep(0.1)
        t = time.time()
        time_delta = t - current_time
        current_time = t
        notify_counter += time_delta
        if notify_counter > notify_seconds:
            notify_counter = 0.0
            print("{} jobs not yet submitted, {} jobs running or waiting in SGE queue at {}".format(
                   len(queued_jobs), len(current_jobs), timestamp()))
    success = True
    for job in jobs:
        try:
            if get_sge_returncode(job) != 0:
                success = False
                print("Error: Job failed for command" +
                      "\n\t" + job.cmd)
                print("Stdout:\n"+open(job.stdout, "rU").read())
                print("Stderr:\n"+open(job.stderr, "rU").read())
        except AttributeError:
            success = False
            print("Error: failed to start process for command" +
                  "\n\t" + job.cmd)
        except IOError:
            success = False
            print("Error: failed to capture output for command" +
                  "\n\t" + job.cmd)
    return success


def run_jobs_lsf(jobs,
                 max_concurrent_jobs=50):
    assert all([isinstance(job, Job) for job in jobs])

    # FIXME: add "child" jobs to same group as parent job (is this even possible from inside this process?)
    #        - ideally all child jobs should be killed if the parent job is killed

    queued_jobs = list(jobs)

    current_jobs = []
    notify_counter = 0.0
    notify_seconds = 5*60
    current_time = time.time()
    # Note: if job.bsub_opts requests e.g. -n 4 R span[hosts=1], 
    # then the number of apparent jobs on the cluster will be 4x max_concurrent_jobs
    while len(queued_jobs)>0 or len(current_jobs)>0:
        if len(current_jobs) < max_concurrent_jobs:
            n = max_concurrent_jobs-len(current_jobs)
            to_run = queued_jobs[:n]
            del queued_jobs[:n]
            for job in to_run:
                current_dir = os.getcwd()
                os.chdir(job.run_folder)
                cmd = "bsub -q day -J '{}' -o '{}' -e '{}' "
                # FIXME: this is probably not needed
                if job.bsub_opts.strip() == "":
                    cmd += "-n1 "
                cmd += job.bsub_opts + " "
                cmd += job.cmd
                cmd = cmd.format(job.id, job.stdout, job.stderr)
                print("submitting job with command:")
                print(cmd)
                print('from within folder "{}"'.format(job.run_folder))
                print("at "+timestamp())
                job.proc = sp.Popen(cmd, shell=True)
                os.chdir(current_dir)
            # wait until LSF reflects the recently queued jobs
            # (otherwise the outer loop will sometimes terminate early)
            while len(get_lsf_jobs(filter_jobs=to_run, all=True)) != len(to_run):
                pass

        time.sleep(0.1)
        current_jobs = get_lsf_jobs(filter_jobs=jobs)
        t = time.time()
        time_delta = t - current_time
        current_time = t
        notify_counter += time_delta
        if notify_counter > notify_seconds:
            notify_counter = 0.0
            print("{} jobs not yet submitted, {} jobs running or pending in LSF queue at {}".format(
                   len(queued_jobs), len(current_jobs), timestamp(),))
    success = True
    for job in jobs:
        try:
            if get_lsf_returncode(job.stdout) != 0:
                success = False
                print("Error: Job failed for command" +
                      "\n\t" + job.cmd)
                print("Stdout:\n"+open(job.stdout, "rU").read())
                print("Stderr:\n"+open(job.stderr, "rU").read())
        except AttributeError:
            success = False
            print("Error: failed to start process for command" +
                  "\n\t" + job.cmd)
        except IOError:
            success = False
            print("Error: failed to capture output for command" +
                  "\n\t" + job.cmd)
    return success


def run_jobs_local(jobs,
                   max_concurrent_jobs=1):
    assert all([isinstance(job, Job) for job in jobs])

    queued_jobs = list(jobs)

    running_jobs = []
    notify_counter = 0.0
    notify_seconds = 5*60
    current_time = time.time()
    while len(queued_jobs)>0 or len(running_jobs)>0:
        if len(running_jobs) < max_concurrent_jobs:
            n = max_concurrent_jobs-len(running_jobs)
            to_run = queued_jobs[:n]
            del queued_jobs[:n]
            for job in to_run:
                current_dir = os.getcwd()
                os.chdir(job.run_folder)
                stdout = open(job.stdout, "w")
                stderr = open(job.stderr, "w")
                print("\nRunning local job with command:")
                print(job.cmd)
                print('from within folder "{}"'.format(job.run_folder))
                print("at "+timestamp())
                job.proc = sp.Popen(job.cmd, shell=True,
                                    stdout=stdout, stderr=stderr)
                os.chdir(current_dir)
        time.sleep(0.1)
        running_jobs = []
        for job in jobs:
            try:
                if job.proc.poll() is None:
                    running_jobs.append(job)
            except AttributeError:
                pass
        t = time.time()
        time_delta = t - current_time
        current_time = t
        notify_counter += time_delta
        if notify_counter > notify_seconds:
            notify_counter = 0.0
            print("{} jobs remaining, {} jobs running".format(len(queued_jobs),
                                                              len(running_jobs),
                                                              ))
            sys.stdout.flush()

    success = True
    for job in jobs:
        try:
            if job.proc.returncode != 0:
                success = False
                print("Error: Job failed for command"+
                      "\n\t"+job.cmd)
                print("Stdout:")
                print(open(job.stdout,"rU").read())
                print("Stderr:")
                print(open(job.stderr, "rU").read())
        except AttributeError:
            success = False
            print("Error: failed to start process for command"+
                  "\n\t"+job.cmd)
    return success


def run_jobs(jobs,
             max_concurrent_jobs=50,
             platform="local"):
    assert all([isinstance(job, Job) for job in jobs])
    assert platform in ["local", "lsf", "sge"]

    if platform == "local":
        return run_jobs_local(jobs, max_concurrent_jobs=max_concurrent_jobs)
    elif platform == "lsf":
        return run_jobs_lsf(jobs, max_concurrent_jobs=max_concurrent_jobs)
    elif platform == "sge":
        return run_jobs_sge(jobs, max_concurrent_jobs=max_concurrent_jobs)


def stage(dir="out",
          done="done",
          cmd=None,
          cmds=None,
          dirs=None,
          name="job"):
    global god
    platform = god.platform
    max_jobs = god.max_jobs
    if os.path.isfile(done):
        print("Skipping {} stage and using previous results.".format(name))
    else:
        s = "Running {} stage . . .".format(name)
        print('_' * len(s))
        print(s)
        jobs = []
        if cmds is None:
            cmds = []
        if cmd is not None:
            cmds.append(cmd)
        for i, cmd in enumerate(cmds):
            if dirs is not None:
                dir = dirs[i]
            makedirs(dir)                
            jobs.append(Job(cmd,
                      name=name,
                      out_folder=dir,
                      bsub_opts=god.bsub_opts))
        success = run_jobs(jobs,
                           platform=platform,
                           max_concurrent_jobs=max_jobs)
        if success:
            os.mknod(done)
            print(". . . successfully completed {} at {}.".format(name, timestamp()))
        else:
            sys.exit(1)
