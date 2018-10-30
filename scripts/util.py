import datetime, errno, os, sys, string


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


def gen_folder_names():
    folder_names = list(string.ascii_uppercase)
    # generate all possible 2-char folder names
    for i in range(len(string.ascii_uppercase)):
        for j in range(len(string.ascii_uppercase)):
            folder_names.append('{}{}'.format(string.ascii_uppercase[i],
                                              string.ascii_uppercase[j]))
    # generate all possible 3-char folder names just in case someone has a really large target set
    for i in range(len(string.ascii_uppercase)):
        for j in range(len(string.ascii_uppercase)):
            for k in range(len(string.ascii_uppercase)):
                folder_names.append('{}{}{}'.format(string.ascii_uppercase[i],
                                                    string.ascii_uppercase[j],
                                                    string.ascii_uppercase[k]))
    return folder_names


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

