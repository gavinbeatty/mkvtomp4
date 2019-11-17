"""Convert H.264 mkv files to mp4 files playable on the PS3, and "correct" the
MPEG4/ISO/AVC profile for use on the PS3."""

try:
    from .version import __version__
except ImportError:
    __version__ = 'unknown'
from . import info

import sys
import os
import re
import getopt
import subprocess as sp
import struct
import pipes

import simplemkv.info

simple_usage = 'usage: mkvtomp4 [options] [--] <file>'

def exit_if(bbool, value=0):
    if bbool:
        sys.exit(value)


class Kwargs(object):
    def __init__(self, f, **kwargs):
        self.f = f
        self.kwargs = kwargs
    def __call__(self, *args):
        return self.f(*args, **self.kwargs)


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
    if one == '':
        return "''"
    return pipes.quote(str(one))


def sq(args):
    return " ".join([__sq(x) for x in args])


def command(cmd, **kwargs):
    verbose_kwargs = {}
    verbosity = kwargs.get('verbosity', None)
    if verbosity is not None:
        verbose_kwargs['verbosity'] = verbosity
    spopts = kwargs.get('spopts', {})
    vprint(1, 'command: %s' % str(cmd), **verbose_kwargs)
    if spopts:
        vprint(1, 'command: options: %s' % str(spopts), **verbose_kwargs)
    try:
        proc = sp.Popen(
            cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True, **spopts
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


def default_options(argv0):
    return {
        'argv0': argv0,
        'verbosity': 0,
        'a_bitrate': '328',
        'a_channels': '5.1',
        'a_codec': 'aac',
        'a_delay': None,
        'output': None,
        'video_track': None,
        'audio_track': None,
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
        'mp4': 'mp4box',
        'mp4creator': 'mp4creator',
        'mp4box': 'MP4Box',
        'ffmpeg': 'ffmpeg',
        'summary': True,
    }


def mp4_add_audio_optimize_cmd(mp4file, audio, **opts):
    if opts['mp4'] == 'mp4creator':
        return [
            opts.get('mp4creator', 'mp4creator'),
            '-c', audio, '-interleave', '-optimize', mp4file
        ]
    elif opts['mp4'] == 'mp4box':
        delay = opts.get('a_delay', None)
        if delay is not None:
            delay = ':delay=' + delay
        else:
            delay = ''
        return [
            opts.get('mp4box', 'MP4Box'),
            '-add', audio + '#audio:trackID=2' + delay, mp4file
        ]
    elif opts['mp4'] == 'ffmpeg':
        return [
            opts.get('ffmpeg', 'ffmpeg'),
            '-i', mp4file,
            '-i', audio, '-codec', 'copy', '-shortest',
            mp4file + '.mp4'
        ]
    else:
        raise RuntimeError('Unknown mp4 option: {}'.format(opts['mp4']))


def mp4_add_hint_cmd(mp4file, **opts):
    if opts['mp4'] == 'mp4creator':
        return [opts.get('mp4creator', 'mp4creator'), '-hint=1', mp4file]
    elif opts['mp4'] in ('mp4box', 'ffmpeg'):
        return None
    else:
        raise RuntimeError('Unknown mp4 option: {}'.format(opts['mp4']))


def mp4_add_video_cmd(mp4file, video, fps, **opts):
    if opts['mp4'] == 'mp4creator':
        return [
            opts.get('mp4creator', 'mp4creator'),
            '-c', video, '-rate', str(fps), mp4file
        ]
    elif opts['mp4'] == 'mp4box':
        return [
            opts.get('mp4box', 'MP4Box'), '-add',
            video + '#video:trackID=1', '-hint', '-fps', str(fps), mp4file,
        ]
    elif opts['mp4'] == 'ffmpeg':
        return [
            opts.get('ffmpeg', 'ffmpeg'),
            # '-framerate', str(fps),
            '-i', video, '-c:v', 'copy',
            '-f', 'mp4', mp4file
        ]
    else:
        raise RuntimeError('Unknown mp4 option: {}'.format(opts['mp4']))


def ffmpeg_convert_audio_cmd(old, new, **opts):
    bitrate = opts.get('bitrate', '128')
    channels = opts.get('channels', '2')
    codec = opts.get('a_codec', 'aac')
    verbosity = opts.get('verbosity', 0)
    if str(channels) == '5.1':
        channels = '6'
    ffmpeg = opts.get('ffmpeg', 'ffmpeg')
    if verbosity > 1:
        cmd = [ffmpeg, '-v', str(verbosity - 1)]
    else:
        cmd = [ffmpeg]
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
        correct_rawmp4_profile(rawmp4)


def mkv_extract_track_cmd(mkv, out, track, verbosely=False, mkvextract=None):
    v = ['-v'] if verbosely else []
    if not mkvextract: mkvextract = 'mkvextract'
    return [mkvextract, 'tracks', mkv] + v + [str(track) + ':' + out]


def real_main(mkvfile, **opts):
    mkvinfo = opts.get('mkvinfo', None)
    infoopts = simplemkv.info.info_locale_opts('en_US')
    infoopts['mkvinfo'] = mkvinfo
    infostr = simplemkv.info.infostring(mkvfile, **infoopts)
    info = simplemkv.info.infodict(infostr.split('\n'))
    try:
        tracks = info['tracks']
    except Exception as ex:
        sys.exit('No tracks key in [{}]'.format(','.join(info)))
        raise
    def get_track(typ, codec_re):
        number = opts.get(typ + '_track', None)
        if number is not None:
            try:
                track = tracks[number]
            except IndexError:
                die('track %d not found: %s' % (number, str(tracks)))
            if not codec_re.search(track['codec']):
                die('track %d has incorrect codec: %s' % (number, str(track)))
        else:
            types = [
                t for t in tracks
                if t['type'] == typ # and codec_re.search(t['codec'])
            ]
            if not types:
                die('appropriate %s track not found: %s' % (typ, str(tracks)))
            return types[0]
    videotrack = get_track('video', re.compile(r'^(?!V_)?MPEG4/ISO/AVC\b'))
    audiotrack = get_track('audio', re.compile(r'^(?!A_)?(?!DTS|AAC|AC3)\b'))
    tempfiles = []
    succeeded = False
    try:
        # Extract video
        video = mkvfile + '.h264'
        exit_if(opts['stop_v_ex'])
        extract_cmd = mkv_extract_track_cmd(
            mkvfile, out=video, track=videotrack['number'],
            verbosely=(opts['verbosity'] > 0),
            mkvextract=opts.get('mkvextract', None),
        )
        tempfiles.append(video)
        dry_command(extract_cmd, **opts)
        exit_if(opts['stop_correct'])
        # Correct profile
        dry_correct_rawmp4_profile(video, **opts)
        a_codec = audiotrack['codec']
        if a_codec.lower().startswith('a_'):
            a_codec = a_codec[2:]
        audio = mkvfile + '.' + a_codec.lower()
        exit_if(opts['stop_a_ex'])
        # Extract audio
        extract_cmd = mkv_extract_track_cmd(
            mkvfile, out=audio, track=audiotrack['number'],
            verbosely=(opts['verbosity'] > 0),
            mkvextract=opts.get('mkvextract', None),
        )
        tempfiles.append(audio)
        dry_command(extract_cmd, **opts)
        exit_if(opts['stop_a_conv'])
        # Convert audio
        if str(a_codec).lower() not in ('a_aac', 'aac'):
            aacaudio, oldaudio = audio + '.aac', audio
            audio_cmd = ffmpeg_convert_audio_cmd(oldaudio, aacaudio, **opts)
            tempfiles.append(aacaudio)
            dry_system(audio_cmd, **opts)
        else:
            aacaudio = audio
        if opts['output'] is None:
            opts['output'] = os.path.splitext(mkvfile)[0] + '.mp4'
        exit_if(opts['stop_v_mp4'])
        # Create mp4 container with video
        opts['fps'] = videotrack['fps']
        mp4video_cmd = mp4_add_video_cmd(
            opts['output'], video,
            **opts
        )
        dry_command(mp4video_cmd, **opts)
        exit_if(opts['stop_hint_mp4'])
        # Hint mp4 container
        mp4hint_cmd = mp4_add_hint_cmd(opts['output'], **opts)
        if mp4hint_cmd is not None:
            dry_command(mp4hint_cmd, **opts)
        exit_if(opts['stop_a_mp4'])
        # Add audio to mp4 container and optimize
        mp4opt_cmd = mp4_add_audio_optimize_cmd(
            opts['output'], aacaudio,
            **opts
        )
        dry_command(mp4opt_cmd, **opts)
        if opts['mp4'] == 'ffmpeg':
            dry_command(['mv', opts['output'] + '.mp4', opts['output']], **opts)
        succeeded = True
    finally:
        if not succeeded:
            eprint('keeping temp files since we failed.')
        elif opts['dry_run']:
            prin(sq(['rm', '-f'] + tempfiles))
        elif not opts['keep_temp_files']:
            for f in tempfiles:
                try:
                    os.remove(f)
                except OSError:
                    pass

def usage(**kwargs):
    p = Kwargs(prin, **kwargs)
    p(simple_usage)
    p('options:')
    p(' -h|--help:')
    p('  Print this help message.')
    p(' --usage:')
    p('  Print a short help message.')
    p(' -v|--verbose:')
    p('  Print info about what is happening.')
    p(' --use-mp4box:')
    p('  Use mp4box when packaging the mp4.')
    p(' --use-mp4creator:')
    p('  Use mp4creator when packaging the mp4.')
    p(' --use-ffmpeg:')
    p('  Use ffmpeg when packaging the mp4.')
    p(' --mp4box=<mp4box>:')
    p('  Use this <mp4box> command.')
    p(' --mp4creator=<mp4creator>:')
    p('  Use this <mp4creator> command.')
    p(' --ffmpeg=<ffmpeg>:')
    p('  Use this <ffmpeg> command.')
    p(' --mkvinfo=<mkvinfo>:')
    p('  Use this <mkvinfo> command.')
    p(' --mkvextract=<mkvextract>:')
    p('  Use this <mkvextract> command.')
    p(' --video-track=<video-track>:')
    p('  Use this video track number.')
    p(' --audio-track=<audio-track>:')
    p('  Use this audio track number.')
    p(' --audio-delay-ms=<audio-delay-ms>:')
    p('  Use this many milliseconds of audio delay.')
    p(' --audio-bitrate=<audio-bitrate>:')
    p('  Use this audio bitrate.')
    p(' --audio-channels=<audio-channels>:')
    p('  Use this many audio channel.')
    p(' --audio-codec=<audio-codec>:')
    p('  Use this audio codec.')
    p(' -o <output>|--output=<output>:')
    p('  Write the mp4 to this file.')
    p(' --keep-temp-files:')
    p('  Keep all temporary files generated.')
    p(' -n|--dry-run:')
    p('  Don\'t actually run any commands.')
    p(' --correct-profile-only:')
    p('  Only correct the mp4 profile.')
    p(' --stop-before-extract-video:')
    p('  Don\'t do anything after extracting video.')
    p(' --stop-before-correct-profile:')
    p('  Don\'t do anything after correcting the mp4 profile.')
    p(' --stop-before-extract-audio:')
    p('  Don\'t do anything after extracting audio.')
    p(' --stop-before-convert-audio:')
    p('  Don\'t do anything after converting video.')
    p(' --stop-before-video-mp4:')
    p('  Don\'t do anything after adding video to mp4.')
    p(' --stop-before-hinting-mp4:')
    p('  Don\'t do anything after hinting the mp4.')
    p(' --stop-before-audio-mp4:')
    p('  Don\'t do anything after adding audio to mp4.')
    p(' --no-summary:')
    p('  Don\'t provide a summary.')

def parseopts(argv=None):
    opts = default_options(argv[0])
    try:
        options, arguments = getopt.gnu_getopt(
            argv[1:],
            'hvo:n',
            [
                'help', 'usage', 'version', 'verbose',
                'mp4box=', 'mp4creator=', 'ffmpeg=', 'mkvinfo=', 'mkvextract=',
                'use-mp4box', 'use-mp4creator', 'use-ffmpeg',
                'video-track=', 'audio-track=',
                'audio-delay-ms=', 'audio-bitrate=', 'audio-channels=',
                'audio-codec=',
                'output=', 'keep-temp-files', 'dry-run',
                'correct-profile-only',
                'stop-before-extract-video', 'stop-before-correct-profile',
                'stop-before-extract-audio', 'stop-before-convert-audio',
                'stop-before-video-mp4', 'stop-before-hinting-mp4',
                'stop-before-audio-mp4',
                'no-summary',
            ]
        )
    except getopt.GetoptError, err:
        die(str(err))
    for opt, optarg in options:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt == '--usage':
            prin(simple_usage)
            sys.exit(0)
        elif opt == '--version':
            prin(__version__)
            sys.exit(0)
        elif opt in ('-v', '--verbose'):
            opts['verbosity'] = opts['verbosity'] + 1
        elif opt == '--mp4box':
            opts['mp4box'] = optarg
        elif opt == '--mp4creator':
            opts['mp4creator'] = optarg
        elif opt == '--ffmpeg':
            opts['ffmpeg'] = optarg
        elif opt == '--mkvinfo':
            opts['mkvinfo'] = optarg
        elif opt == '--mkvextract':
            opts['mkvextract'] = optarg
        elif opt == '--use-mp4box':
            opts['mp4'] = 'mp4box'
        elif opt == '--use-mp4creator':
            opts['mp4'] = 'mp4creator'
        elif opt == '--use-ffmpeg':
            opts['mp4'] = 'ffmpeg'
        elif opt == '--video-track':
            opts['video_track'] = optarg
        elif opt == '--audio-track':
            opts['audio_track'] = optarg
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
        elif opt == '--no-summary':
            opts['summary'] = False
    return opts, arguments


def main(argv=None):
    if argv is None:
        argv = sys.argv
    opts, args = parseopts(argv)
    if len(args) != 1:
        die(simple_usage)
    if opts['a_delay'] is not None and opts['mp4'] == 'mp4creator':
        die("Cannot use --audio-delay-ms with mp4creator. Try --use-mp4box")
    if opts['correct_prof_only']:
        dry_correct_rawmp4_profile(args[0], **opts)
    else:
        if opts['summary'] and not opts['dry_run']:
            keep, dry_run = opts['keep_temp_files'], opts['dry_run']
            opts['keep_temp_files'], opts['dry_run'] = True, True
            real_main(args[0], **opts)
            opts['keep_temp_files'], opts['dry_run'] = keep, dry_run
        real_main(args[0], **opts)
