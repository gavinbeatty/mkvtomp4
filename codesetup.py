from setup import *
if __name__ == '__main__':
    __version__ = git_version()
    codeopts['version'] = __version__
    setup(**codeopts)
