import os


def try_remove_files(*fnames):
    for fname in fnames:
        try:
            os.remove(fname)
        except FileNotFoundError:
            pass
