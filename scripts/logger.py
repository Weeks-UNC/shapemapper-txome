import os
from scripts.util import makedirs


class Logger:
    """
    Duplicate stream writes to a text file and
    flush on write.

    """

    def __init__(self,
                 filepath,
                 stream):
        self.file=None
        if filepath is not None:
            folder, filename = os.path.split(filepath)
            if len(folder) > 0:
                makedirs(folder)
            self.file = open(filepath, "a")
        self.stream = stream

    def write(self, s):
        if self.stream is not None:
            self.stream.write(s)
        if self.file is not None:
            self.file.write(s)
        self.flush()

    def flush(self):
        if self.stream is not None:
            self.stream.flush()
        if self.file is not None:
            self.file.flush()
