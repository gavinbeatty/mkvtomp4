
"""Convert H.264 mkv files to mp4 files playable on the PS3

Uses mpeg4ip, mkvtoolnix and ffmpeg to convert troublesome mkv files to mp4.
They will be playable on the Sony PS3.
"""

from distutils.core import setup
import mkvtomp4

# A list of classifiers can be found here:
#   http://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = """\
Natural Language :: English
Development Status :: 4 - Beta
Environment :: Console
Topic :: Multimedia
Topic :: Multimedia :: Sound/Audio :: Conversion
Topic :: Multimedia :: Video :: Conversion
Intended Audience :: End Users/Desktop
License :: OSI Approved :: MIT License
Programming Language :: Python
Operating System :: OS Independent
"""

from sys import version_info

if version_info < (2, 3):
    _setup = setup
    def setup(**kwargs):
        if kwargs.has_key("classifiers"):
            del kwargs["classifiers"]
        _setup(**kwargs)

doclines = __doc__.split("\n")

setup(name='mkvtomp4'
     ,description=doclines[0]
     ,long_description="\n".join(doclines[2:])
     ,author='Gavin Beatty'
     ,author_email='gavinbeatty@gmail.com'
     ,maintainer='Gavin Beatty'
     ,maintainer_email='gavinbeatty@gmail.com'
     ,license = 'http://opensource.org/licenses/MIT'
     ,platforms=["any"]
     ,classifiers=filter(None, classifiers.split("\n"))
     ,url='http://code.google.com/p/mkvtomp4/'
     ,version=mkvtomp4.__version__
     ,scripts=['mkvtomp4']
#      ,data_files=[('share/doc/mkvtomp4', ['README.md'])
#        , ('share/man/man1', ['doc/mkvtomp4.1', 'doc/mkvtomp4.1.html'])
#        ]
      )

