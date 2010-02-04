mkvtomp4
========
Gavin Beatty <gavinbeatty@gmail.com>

mkvtomp4: Uses mpeg4ip, mkvtoolnix and ffmpeg to convert troublesome mkv files
to mp4. The conversion does not re-encode the video and only re-encodes the
audio if it doesn't use AAC codec (one can override this behaviour using
--audio-codec). They will be playable on the Sony PS3.

    Usage: mkvtomp4.py [OPTIONS] [--] <mkvfile>

For more usage details, see the manual.


Dependencies
------------

Tools:
* mkvtoolnix
* mpeg4ip
* ffmpeg

On Linux, use your package manager to install.
On Mac OS X, use MacPorts to install.
On Windows, go to the tools' individual websites and find windows binaries.

Everything else is written using only fully cross-platform python, except:

* pipes module. This means we depend on POSIX /bin/sh for the time being.

If you want to help eliminate this dependency, help solve issue 0001.


License
-------

mkvtomp4 Copyright 2010 Gavin Beatty <gavinbeatty@gmail.com>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You can find the GNU General Public License at:
http://www.gnu.org/licenses/


Install
-------

Use setuptools in the usual way:
    sudo python setup.py install

To install only for the current user:
    python setup.py install --user

For additional help:
    python setup.py --help


Install documentation
---------------------

Default installation prefix is /usr/local

    sudo make install-docs

Install to your own prefix:

    make install-docs prefix=~/.local


Website
-------
http://code.google.com/p/mkvtomp4/


