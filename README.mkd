mkvtomp4
========
Gavin Beatty <public@gavinbeatty.com>

Uses existing tools to convert troublesome mkv files to mp4,
that is playable on the PS3.
The conversion does not re-encode H.264 video.
If the H.264 profile level is not supported by the PS3,
we rewrite just some profile level information.
The default value is 4.1, but it can be set with `--profile-level=4.0`, etc.
The conversion only re-encodes audio if it doesn't already use AAC.
The resulting mp4 will be playable on the Sony PS3, and similar devices.
Tested on profile levels 3.x and 4.x,

Note that the PS4 Media Player has better support for mkv than mp4
(subtitles work only on mkv).

Check the manual in `doc/mkvtomp4.1.txt`.


Dependencies
------------

Tools:

* *mkvtoolnix*
* GPAC's *MP4Box*
* *ffmpeg* (optional)

To install these tools:

* On Linux, use your package manager.
* On Mac OS X, use MacPorts or homebrew.
* On Windows, go to each tools' individual websites.

Everything else is written using only fully cross-platform python 2/3, except

* pipes module on python 2, which adds a POSIX /bin/sh dependency.


Install
-------

Install code and documentation using setup.py in the standard way.

Install only code using codesetup.py.

