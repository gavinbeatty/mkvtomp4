#!/usr/bin/python

"""Convert H.264 mkv files to mp4 files playable on the PS3, and "correct" the
MPEG4/ISO/AVC profile for use on the PS3."""


__version__ = '1.3'


usage = 'usage: mkvtomp4 [options] [--] <file>'


import os
import sys
import re
import subprocess as sp
import struct
import getopt
import pipes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def prin(*args, **kwargs):
    fobj = kwargs.get('fobj', None)
    if fobj is None:
        fobj = sys.stdout
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    if len(args) > 0:
        fobj.write(args[0])
        if len(args) > 1:
            for arg in args[1:]:
                fobj.write(sep + arg)
    fobj.write(end)


def eprint(*args, **kwargs):
    kwargs['fobj'] = sys.stderr
    prin("error:", *args, **kwargs)


def die(*args, **kwargs):
    eprint(*args, **kwargs)
    sys.exit(1)


def wprint(*args, **kwargs):
    kwargs['fobj'] = sys.stderr
    prin("warning:", *args, **kwargs)


_verbosity = 0


def vprint(level, *args, **kwargs):
    global _verbosity
    local = kwargs.get('verbosity', 0)
    if _verbosity >= level or local >= level:
        prin('verbose:', *args, **kwargs)


def onlykeys(d, keys):
    newd = {}
    for k in keys:
        newd[k] = d[k]
    return newd


def __sq(one):
    squoted = pipes.quote(one)
    if squoted == '':
        return "''"
    return squoted


def sq(args):
    return " ".join([__sq(x) for x in args])


def command(cmd, **kwargs):
    verbose_kwargs = {}
    verbosity = kwargs.get('verbosity', None)
    if verbosity is not None:
        verbose_kwargs['verbosity'] = verbosity
    if len(kwargs) != 0:
        vprint(1, 'command: Popen kwargs: %s' % str(kwargs), **verbose_kwargs)
    try:
        vprint(1, 'command: %s' % str(cmd), **verbose_kwargs)
        proc = sp.Popen(
            cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True, **kwargs
        )
    except OSError, e:
        die('command failed:', str(e), ':', sq(cmd))
    chout, cherr = proc.communicate()
    vprint(1, 'command: stdout:', chout, '\ncommand: stderr:', cherr)
    if proc.returncode != 0:
        die('failure: %s' % cherr, end='')
    return chout


def dry_command(cmd, **opts):
    if opts['dry_run']:
        prin(sq(cmd))
    else:
        command(cmd, **opts)


def dry_system(cmd, **opts):
    quoted = sq(cmd)
    if opts['dry_run']:
        prin(quoted)
    else:
        os.system(quoted)


class MkvInfo(object):
    _impl = None

    class _Impl:
        def __init__(self):
            self.track_no_re = re.compile(r'^\|  \+ Track number: (\d+)$')
            self.track_type_re = re.compile(r'^\|  \+ Track type: (.*)$')
            self.codec_re = re.compile(r'^\|  \+ Codec ID: (.*)$')
            self.a_codec_re = re.compile(r'^(A_)?(DTS|AAC|AC3)$')
            self.v_codec_re = re.compile(r'^(V_)?(MPEG4/ISO/AVC)$')
            self.fps_re = re.compile(
                r'^\|  \+ Default duration: \d+\.\d+ms \((\d+\.\d+)'
                ' fps for a video track\)$')

    @classmethod
    def info(cls, mkv):
        if cls._impl is None:
            cls._impl = cls._Impl()
        i = {}
        i['track'] = {'audio': None, 'video': None}
        i['fullinfo'] = command(
            ['mkvinfo', mkv], env={'LC_ALL': 'C'}
        ).split('\n')
        in_track_number = None
        in_track_type = None
        for line in i['fullinfo']:
            match = cls._impl.track_no_re.search(line)
            if match is not None:
                in_track_number = match.group(1)
                in_track_type = None
                vprint(1, 'MkvInfo: in track number: %s' % in_track_number)
                continue
            if in_track_number is not None:
                match = cls._impl.track_type_re.search(line)
                if match is not None:
                    in_track_type = match.group(1)
                    vprint(1, 'MkvInfo: in track type: %s' % in_track_type)
                    i['track'][in_track_type] = in_track_number
                    if in_track_type != 'audio' and in_track_type != 'video':
                        wprint('ignoring track type: %s' % in_track_type)
            if in_track_number is not None:
                match = cls._impl.codec_re.search(line)
                if match is not None:
                    codec = match.group(1)
                    # unknown track types shouldn't have codec_match := None
                    codec_match = None
                    if in_track_type == 'audio':
                        codec_match = cls._impl.a_codec_re.search(codec)
                        if codec_match is None:
                            die('unrecognised codec: %s' % codec)
                    elif in_track_type == 'video':
                        codec_match = cls._impl.v_codec_re.search(codec)
                        if codec_match is None:
                            die('unrecognised codec: %s' % codec)
                    if codec_match is not None:
                        key = in_track_type + '_codec'
                        i['track'][key] = codec_match.group(2)
                        vprint(1, 'MkvInfo: found %s: %s'
                               % (key, i['track'][key]))
            if in_track_type == 'video':
                match = cls._impl.fps_re.search(line)
                if match is not None:
                    i['track']['fps'] = match.group(1)


def default_options(argv0):
    return {
        'argv0': argv0,
        'verbosity': 0,
        'a_bitrate': '328',
        'a_channels': '5.1',
        'a_codec': 'libfaac',
        'a_delay': None,
        'output': None,
        'keep_temp_files': False,
        'dry_run': False,
        'correct_prof_only': False,
        'stop_v_ex': False,
        'stop_correct': False,
        'stop_a_ex': False,
        'stop_a_conv': False,
        'stop_v_mp4': False,
        'stop_hint_mp4': False,
        'stop_a_mp4': False,
        'mp4': 'mp4creator',
    }


def mp4_add_audio_optimize_cmd(mp4, audio, **kwargs):
    if kwargs['mp4'] == 'mp4creator':
        return ['mp4creator', '-c', audio, '-interleave', '-optimize', mp4]
    elif kwargs['mp4'] == 'mp4box':
        delay = kwargs.get('delay', None)
        if delay is not None:
            delay = ':delay=' + delay
        else:
            delay = ''
        return ['MP4Box', '-add', audio + '#audio:trackID=2' + delay, mp4]


def mp4_add_hint_cmd(mp4, **kwargs):
    if kwargs['mp4'] == 'mp4creator':
        return ['mp4creator', '-hint=1', mp4]
    elif kwargs['mp4'] == 'mp4box':
        return None


def mp4_add_video_cmd(mp4, video, fps, **kwargs):
    if kwargs['mp4'] == 'mp4creator':
        return ['mp4creator', '-c', video, '-rate', fps, mp4]
    elif kwargs['mp4'] == 'mp4box':
        return [
            'MP4Box', '-add',
            video + '#video:trackID=1', '-hint', '-fps', fps, mp4,
        ]


def ffmpeg_convert_audio_cmd(old, new, **kwargs):
    bitrate = kwargs.get('bitrate', '128')
    channels = kwargs.get('channels', '2')
    codec = kwargs.get('codec', 'libfaac')
    verbosity = kwargs.get('verbosity', 0)
    if str(channels) == '5.1':
        channels = '6'
    if verbosity > 1:
        cmd = ['ffmpeg', '-v', str(verbosity - 1)]
    else:
        cmd = ['ffmpeg']
    return cmd + [
        '-i', old, '-ac', str(channels), '-acodec', codec,
        '-ab', str(bitrate) + 'k', new
    ]


def pretend_correct_rawmp4_profile(rawmp4, argv0):
    prin(sq([argv0, '--correct-profile-only', rawmp4]))


def correct_rawmp4_profile(rawmp4):
    level_string = struct.pack('b', int('29', 16))
    f = open(rawmp4, 'r+b')
    try:
        f.seek(7)
        vprint(1, 'correcting profile:', rawmp4)
        f.write(level_string)
    finally:
        f.close()


def dry_correct_rawmp4_profile(rawmp4, **opts):
    if opts['dry_run']:
        pretend_correct_rawmp4_profile(rawmp4, opts['argv0'])
    else:
        correct_rawmp4_profile(rawmp4, **opts)


def mkv_extract_track_cmd(mkv, out, track, verbosely=False):
    v = ['-v'] if verbosely else []
    return ['mkvextract', 'tracks', mkv] + v + [str(track) + ':' + out]


# XXX not used
#def mkv_split(mkv, pieces):
#    if pieces != 1:
#        split_size_MB = (((os.path.getsize(mkv) / pieces) + 1) / 1000) + 1
#        command(['mkvmerge', '-o', mkv, '--split', str(split_size_MB)])


def exit_if(bbool, value=0):
    if bbool:
        sys.exit(value)


def real_main(mkv, **opts):
    mkvinfo = MkvInfo.info(mkv)
    mkvtracks = mkvinfo['track']
    if mkvtracks.get('video', None) is None:
        die('no video track found in info:\n' + mkvinfo['fullinfo'])
    if mkvtracks.get('audio', None) is None:
        die('no audio track found in info:\n' + mkvinfo['fullinfo'])
    tempfiles = []
    try:
        # Extract video
        video = mkv + '.h264'
        exit_if(opts['stop_v_ex'])
        extract_cmd = mkv_extract_track_cmd(
            mkv, out=video, track=mkvtracks['video'],
            verbosely=(opts['verbosity'] > 0),
        )
        tempfiles.append(video)
        dry_command(extract_cmd, **opts)
        exit_if(opts['stop_correct'])
        # Correct profile
        dry_correct_rawmp4_profile(video, **opts)
        a_codec = mkvtracks['audio_codec']
        audio = mkv + '.' + a_codec.lower()
        exit_if(opts['stop_a_ex'])
        # Extract audio
        extract_cmd = mkv_extract_track_cmd(
            mkv, out=audio, track=mkvtracks['audio'],
            verbosely=(opts['verbosity'] > 0)
        )
        tempfiles.append(audio)
        dry_command(extract_cmd, **opts)
        exit_if(opts['stop_a_conv'])
        # Convert audio
        if str(a_codec).lower() != 'aac':
            aacaudio, oldaudio = audio + '.aac', audio
            audio_cmd = ffmpeg_convert_audio_cmd(oldaudio, aacaudio, **opts)
            tempfiles.append(aacaudio)
            dry_system(audio_cmd, **opts)
        if opts['output'] is None:
            opts['output'] = os.path.splitext(mkv)[0] + '.mp4'
        exit_if(opts['stop_v_mp4'])
        # Create mp4 container with video
        mp4video_cmd = mp4_add_video_cmd(
            opts['output'], video,
            fps=mkvtracks['fps']
        )
        dry_command(mp4video_cmd, **opts)
        exit_if(opts['stop_hint_mp4'])
        # Hint mp4 container
        mp4hint_cmd = mp4_add_hint_cmd(opts['output'], **opts)
        dry_command(mp4hint_cmd, **opts)
        exit_if(opts['stop_a_mp4'])
        # Add audio to mp4 container and optimize
        mp4opt_cmd = mp4_add_audio_optimize_cmd(
            opts['output'], aacaudio,
            **opts
        )
        dry_command(mp4opt_cmd, **opts)
    finally:
        if not opts['keep_temp_files']:
            for f in tempfiles:
                try:
                    os.remove(f)
                except OSError:
                    pass


def parseopts(argv=None):
    opts = default_options(argv[0])
    try:
        options, arguments = getopt.gnu_getopt(
            argv[1:],
            'hvo:n',
            [
                'help', 'usage', 'version', 'verbose',
                'use-mp4box', 'use-mp4creator',
                'audio-delay-ms=', 'audio-bitrate=', 'audio-channels=',
                'audio-codec=',
                'output=', 'keep-temp-files', 'dry-run',
                'correct-profile-only',
                'stop-before-extract-video', 'stop-before-correct-profile',
                'stop-before-extract-audio', 'stop-before-convert-audio',
                'stop-before-video-mp4', 'stop-before-hinting-mp4',
                'stop-before-audio-mp4',
            ]
        )
    except getopt.GetoptError, err:
        die(str(err))
    for opt, optarg in options:
        if opt in ('-h', '--help', '--usage'):
            prin(usage)
            sys.exit(0)
        elif opt == '--version':
            prin(__version__)
            sys.exit(0)
        elif opt in ('-v', '--verbose'):
            opts['verbosity'] = opts['verbosity'] + 1
        elif opt == '--use-mp4creator':
            opts['mp4'] = 'mp4creator'
        elif opt == '--use-mp4box':
            opts['mp4'] = 'mp4box'
        elif opt == '--audio-delay-ms':
            opts['a_delay'] = optarg
        elif opt == '--audio-bitrate':
            opts['a_bitrate'] = optarg
        elif opt == '--audio-channels':
            opts['a_channels'] = optarg
        elif opt == '--audio-codec':
            opts['a_codec'] = optarg
        elif opt in ('-o', '--output'):
            opts['output'] = optarg
        elif opt == '--keep-temp-files':
            opts['keep_temp_files'] = True
        elif opt in ('-n', '--dry-run'):
            opts['dry_run'] = True
        elif opt == '--correct-profile-only':
            opts['correct_prof_only'] = True
        elif opt == '--stop-before-extract-video':
            opts['stop_v_ex'] = True
        elif opt == '--stop-before-correct-profile':
            opts['stop_correct'] = True
        elif opt == '--stop-before-extract-audio':
            opts['stop_a_ex'] = True
        elif opt == '--stop-before-convert-audio':
            opts['stop_a_conv'] = True
        elif opt == '--stop-before-video-mp4':
            opts['stop_v_mp4'] = True
        elif opt == '--stop-before-hinting-mp4':
            opts['stop_hint_mp4'] = True
        elif opt == '--stop-before-audio-mp4':
            opts['stop_a_mp4'] = True
    return opts, arguments


def main(argv=None):
    if argv is None:
        argv = sys.argv
    opts, args = parseopts(argv)
    if len(args) != 1:
        die(usage)
    if opts['a_delay'] is not None and opts['mp4'] == 'mp4creator':
        die("Cannot use --audio-delay-ms with mp4creator. Try --use-mp4box")
    try:
        if opts['correct_prof_only']:
            dry_correct_rawmp4_profile(args[0], **opts)
        else:
            real_main(args[0], **opts)
    except Exception, e:
        die('failed with exception:', str(e))


if __name__ == "__main__":
    sys.exit(main())
