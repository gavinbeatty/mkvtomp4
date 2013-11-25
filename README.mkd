mkvtomp4
========
Gavin Beatty <gavinbeatty@gmail.com>

<http://code.google.com/p/mkvtomp4/>

mkvtomp4: Uses mpeg4ip or GPAC's MP4Box, mkvtoolnix and ffmpeg to convert
troublesome mkv files to mp4.
The conversion does not re-encode the video and only re-encodes the audio if
it doesn't use AAC codec (one can override this behaviour using
`--audio-codec`).
They will be playable on the Sony PS3.

Check the manual in `doc/mkvtomp4.1.txt`.


Dependencies
------------

Tools:
* mkvtoolnix
* mpeg4ip or GPAC's MP4Box
* ffmpeg

On Linux, use your package manager to install.
On Mac OS X, use MacPorts to install.
On Windows, go to the tools' individual websites and find windows binaries.

Everything else is written using only fully cross-platform python, except:

* pipes module. This means we depend on POSIX /bin/sh for the time being.

If you want to help eliminate this dependency, help solve issue 0001.


Install
-------

Install code and documentation using setup.py in the standard way.

Install only code using codesetup.py.

