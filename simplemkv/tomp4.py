"""Convert H.264 mkv files to mp4 files playable on the PS3, and "correct" the
MPEG4/ISO/AVC profile for use on the PS3."""

try:
    from .version import __version__
except ImportError:
    __version__ = 'unknown'

import sys
import os
import re
import getopt
import subprocess as sp
import struct
import traceback
try:
    from shlex import quote
except:
    from pipes import quote

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
        if args[1:]:
            for arg in args[1:]:
                fobj.write(sep + arg)
    fobj.write(end)


def nullprint(*args, **kwargs):
    pass


def eprint(*args, **kwargs):
    kwargs['fobj'] = sys.stderr
    prin("error:", *args, **kwargs)


def die(*args, **kwargs):
    eprint(*args, **kwargs)
    sys.exit(1)


def wprint(*args, **kwargs):
    kwargs['fobj'] = sys.stderr
    prin("warning:", *args, **kwargs)


def vprint(level, *args, **kwargs):
    verbosity = kwargs.get('verbosity', 0)
    if verbosity >= level:
        prin('verbose:', *args, **kwargs)


def onlykeys(d, keys):
    newd = {}
    for k in keys:
        newd[k] = d[k]
    return newd


def __sq(one):
    if one == '':
        return "''"
    return quote(str(one))


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
    except OSError:
        et, ev, tb = sys.exc_info()
        estr = ''.join(traceback.format_exception_only(et, ev))
        die('command failed:', estr, ':', sq(cmd))
    chout, cherr = proc.communicate()
    if chout is not str:
        chout = chout.decode('utf_8')
    if cherr is not str:
        cherr = cherr.decode('utf_8')
    vprint(1, 'command: stdout:', chout, '\ncommand: stderr:', cherr, **verbose_kwargs)
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
        'a_lang': None,
        's_default': False,
        's_lang': None,
        'output': None,
        'hint': False,
        'video_track': None,
        'audio_track': None,
        'subtitles_track': None,
        'keep_temp_files': False,
        'dry_run': False,
        'profile_level': '4.1',
        'force_profile_level': False,
        'correct_prof_only': False,
        'stop_v_ex': False,
        'stop_correct': False,
        'stop_a_ex': False,
        'stop_a_conv': False,
        'stop_s_ex': False,
        'stop_mp4': False,
        'stop_s_add': False,
        'mp4box': 'MP4Box',
        'ffmpeg': 'ffmpeg',
        'summary': True,
    }


def mp4_add_cmd(mp4file, rawvideo, rawaudio, **opts):
    a_delay = opts.get('a_delay', None)
    if a_delay is not None:
        a_delay = ':delay=' + a_delay
    else:
        a_delay = ''
    a_lang = opts.get('a_lang', None)
    if a_lang is not None:
        a_lang = ':lang=' + a_lang
    else:
        a_lang = ''
    hint = ['-hint'] if opts.get('hint', False) else []
    return [
        opts.get('mp4box', 'MP4Box'),
        '-add', rawvideo + '#video:fps=' + str(opts['fps']),
        '-add', rawaudio + '#audio:default' + a_delay + a_lang] + \
        hint + ['-new', mp4file]


def ffmpeg_convert_audio_cmd(old, new, **opts):
    bitrate = opts.get('a_bitrate', '128')
    channels = opts.get('a_channels', '2')
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


def pretend_correct_rawh264_profile(rawh264, **opts):
    cmd = [opts['argv0'], '--correct-profile-only', '--profile-level']
    cmd.extend([opts.get('profile_level', '4.1')])
    if opts.get('force_profile_level', False):
        cmd.extend(['--force-profile-level'])
    prin(sq(cmd + [rawh264]))


def correct_rawh264_profile(rawh264, **opts):
    profile_str = opts.get('profile_level', '4.1')
    profile = int(round(float(profile_str) * 10.0))
    profile_bytes = struct.pack('b', profile)
    f = open(rawh264, 'r+b')
    try:
        f.seek(7)
        existing_profile_bytes = f.read(1)
        existing_profile = struct.unpack('b', existing_profile_bytes)[0]
        existing_profile_str = str(existing_profile / 10.0)
        if opts.get('force_profile_level', False) or existing_profile > profile:
            f.seek(7)
            vprint(1, 'correcting profile to ' + profile_str
                    + ' from ' + existing_profile_str + ':', rawh264, **opts)
            f.write(profile_bytes)
        else:
            vprint(1, 'leaving profile at ' + existing_profile_str
                    + ' which is not greater than ' + profile_str + ':', rawh264, **opts)
    finally:
        f.close()


def dry_correct_rawh264_profile(rawh264, **opts):
    if opts['dry_run']:
        pretend_correct_rawh264_profile(rawh264, **opts)
    else:
        correct_rawh264_profile(rawh264, **opts)


def mkv_extract_track_cmd(mkv, out, track, verbosely=False, mkvextract=None):
    v = ['-v'] if verbosely else []
    if not mkvextract:
        mkvextract = 'mkvextract'
    return [mkvextract, 'tracks', mkv] + v + [str(track) + ':' + out]


def mp4_extract_track_cmd(mp4, out, track, verbosely=False, mp4box=None):
    v = ['-v'] if verbosely else []
    if not mp4box:
        mp4box = 'MP4Box'
    return [mp4box, '-raw', str(track), mp4, '-out', out]


def real_main(mkvfile, **opts):
    mkvinfo = opts.get('mkvinfo', None)
    infoopts = simplemkv.info.info_locale_opts('en_US')
    infoopts['mkvinfo'] = mkvinfo
    infostr = simplemkv.info.infostring(mkvfile, **infoopts)
    info = simplemkv.info.infodict(infostr.split('\n'))
    try:
        tracks = info['tracks']
    except Exception:
        sys.exit('No tracks key in [' + ','.join(info) + ']')
        raise

    def get_track(typ, idx, codec_re, err=die):
        number = opts.get(typ + '_track', None)
        if number is not None and int(number) < 0:
            return
        if idx == 0 and number is not None:
            try:
                return tracks[int(number)]
            except IndexError:
                err('track %s not found: %s' % (number, str(tracks)))
                return
            if not codec_re.search(track['codec']):
                err('track %s has incorrect codec: %s' % (number, str(track)))
                return
        else:
            types = [
                t for t in tracks
                if t['type'] == typ and codec_re.search(t['codec'])
            ]
            if not types:
                err('appropriate %s track not found: %s' % (typ, str(tracks)))
                return
            if idx < len(types):
                return types[idx]
            return
    videore = re.compile(r'^(V_)?(MPEG4/ISO/AVC|MPEGH/ISO/HEVC)$')
    audiore = re.compile(r'^(A_)?(DTS|AAC|E?AC3|MPEG/L2|VORBIS|FLAC)$')
    subtitlesre = re.compile(r'^(S_)?(TEXT/UTF8|HDMV/PGS)$')
    videotrack = get_track('video', 0, videore, die)
    audiotrack = get_track('audio', 0, audiore, die)
    # audiotrack2 = get_track('audio', 1, audiore, nullprint)
    subtitlestrack = get_track('subtitles', 0, subtitlesre, eprint)
    # subtitlestrack2 = get_track('subtitles', 1, subtitlesre, nullprint)
    tempfiles = []
    succeeded = False
    try:
        # Extract video
        if videotrack['codec'] in ('MPEG4/ISO/AVC', 'MPEG4/ISO/AVC'):
            rawvideoext = '.h264'
        elif videotrack['codec'] in ('MPEGH/ISO/HEVC', 'MPEGH/ISO/HEVC'):
            rawvideoext = '.h265'
        else:
            raise RuntimeError('Unknown extension for codec: ' + videotrack['codec'])
        rawvideo = mkvfile + rawvideoext
        exit_if(opts['stop_v_ex'])
        extract_cmd = mkv_extract_track_cmd(
            mkvfile, out=rawvideo, track=videotrack['number'],
            verbosely=(opts['verbosity'] > 0),
            mkvextract=opts.get('mkvextract', None),
        )
        tempfiles.append(rawvideo)
        dry_command(extract_cmd, **opts)
        exit_if(opts['stop_correct'])
        if rawvideoext == '.h264':
            dry_correct_rawh264_profile(rawvideo, **opts)
        a_codec = audiotrack['codec']
        if a_codec.lower().startswith('a_'):
            a_codec = a_codec[2:]
        if a_codec.lower() == 'mpeg/l2':
            a_codec = 'mp2'
        clean_a_codec = re.sub(r'[\/:]', '-', a_codec.lower())
        rawaudio = mkvfile + '.' + clean_a_codec
        exit_if(opts['stop_a_ex'])
        # Extract audio
        extract_cmd = mkv_extract_track_cmd(
            mkvfile, out=rawaudio, track=audiotrack['number'],
            verbosely=(opts['verbosity'] > 0),
            mkvextract=opts.get('mkvextract', None),
        )
        tempfiles.append(rawaudio)
        dry_command(extract_cmd, **opts)
        exit_if(opts['stop_a_conv'])
        # Convert audio, if necessary
        if str(a_codec).lower() != 'aac':
            aacaudio = rawaudio + '.aac'
            audio_cmd = ffmpeg_convert_audio_cmd(rawaudio, aacaudio, **opts)
            tempfiles.append(aacaudio)
            dry_system(audio_cmd, **opts)
        else:
            aacaudio = rawaudio
        # Optional subtitle track
        exit_if(opts['stop_s_ex'])
        if subtitlestrack is not None:
            s_codec = subtitlestrack['codec']
            if s_codec == 'TEXT/UTF8':
                clean_s_codec = 'srt'
            elif s_codec == 'HDMV/PGS':
                clean_s_codec = 'sup'
            else:
                raise RuntimeError('Unknown extension for codec: ' + s_codec)
            rawsub = os.path.splitext(mkvfile)[0] + '.' + clean_s_codec
            extract_cmd = mkv_extract_track_cmd(
                mkvfile, out=rawsub, track=subtitlestrack['number'],
                verbosely=(opts['verbosity'] > 0),
                mkvextract=opts.get('mkvextract', None),
            )
            dry_command(extract_cmd, **opts)
        else:
            rawsub = None
        if opts['output'] is None:
            if rawsub is None:
                nosuboutput = os.path.splitext(mkvfile)[0] + '.mp4'
                suboutput = None
            else:
                noexoutput = os.path.splitext(mkvfile)[0]
                nosuboutput = noexoutput + '.nosub.mp4'
                suboutput = noexoutput + '.mp4'
                tempfiles.append(nosuboutput)
        else:
            if rawsub is None:
                nosuboutput = opts['output']
                suboutput = None
            else:
                nosuboutput = opts['output'] + '.nosub.mp4'
                suboutput = opts['output']
                tempfiles.append(nosuboutput)
        exit_if(opts['stop_mp4'])
        # Create mp4 container
        opts.setdefault('a_lang', audiotrack.get('language', None))
        opts['fps'] = videotrack['fps']
        mp4add_cmd = mp4_add_cmd(
            nosuboutput, rawvideo, aacaudio,
            **opts
        )
        dry_command(mp4add_cmd, **opts)
        if rawsub is not None:
            exit_if(opts['stop_s_add'])
            s_lang = subtitlestrack.get('language', opts.get('s_lang', None))
            if s_lang is not None:
                metadata = ['-metadata:s:s:0', 'language=' + s_lang]
            else:
                metadata = []
            s_default = opts.get('s_default', False)
            disposition = ['-disposition:s:0', 'default' if s_default else '0']
            sub_cmd = [opts.get('ffmpeg', 'ffmpeg'),
                '-i', nosuboutput, '-i', rawsub,
                '-c:v', 'copy', '-c:a', 'copy',
                '-c:s', 'mov_text'] + metadata + disposition + [suboutput]
            dry_system(sub_cmd, **opts)
        # TODO: add subtitles with:
        # ffmpeg -i v.mp4 -i s.srt -c:v copy -c:a copy \
        #   -c:s mov_text -metadata:s:s:0 language=eng \
        #   -disposition:s:0 default o.mp4
        # The disposition default stuff turns on subs by default.
        # Hard sub with: ffmpeg -i v.mp4 -vf subtitles=s.srt o.mp4
        # Rename with:
        # filebot.sh --action test -rename *.mp4 \
        #   --db TVmaze --q 'series if not auto-detected' \
        #   -no-xattr -non-strict \
        #   --format "TV Shows/{n.colon('_')}/Season {s}/{s00e00} - {t}"
        # filebot.sh --action test -rename *.mp4 \
        #   -no-xattr -non-strict \
        # or --format "Movies/{n.colon('_')}/{n.colon('_')} ({y} - {director})"
        # optionally add --db TVmaze --q 'series name'
        # or --db TheMovieDB
        # and --action move to actually rename
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
    p(' --mp4box=<mp4box>:')
    p('  Use this <mp4box> command.')
    p(' --ffmpeg=<ffmpeg>:')
    p('  Use this <ffmpeg> command.')
    p(' --mkvinfo=<mkvinfo>:')
    p('  Use this <mkvinfo> command.')
    p(' --mkvextract=<mkvextract>:')
    p('  Use this <mkvextract> command.')
    p(' --hint, --no-hint:')
    p('  Enable or disable hinting the mp4.')
    p(' --video-track=<video-track>:')
    p('  Use this video track number.')
    p(' --audio-track=<audio-track>:')
    p('  Use this audio track number.')
    p(' --audio-delay-ms=<audio-delay-ms>:')
    p('  Use this many milliseconds of audio delay.')
    p(' --audio-bitrate=<audio-bitrate>:')
    p('  Use this audio bitrate.')
    p(' --audio-channels=<audio-channels>:')
    p('  Use this many audio channels.')
    p(' --audio-codec=<audio-codec>:')
    p('  Use this audio codec.')
    p(' --audio-lang=<audio-lang>:')
    p('  Describe the audio as this language in the mp4.')
    p(' --subtitle-track=<subtitle-track>:')
    p('  Use this subtitles track number.')
    p(' --subtitle-lang=<subtitle-lang>:')
    p('  Describe any subtitle track as this language in the mp4.')
    p(' --subtitle-default, --subtitle-no-default:')
    p('  Set any subtitle track as appearing by default, or not.')
    p(' -o <output>|--output=<output>:')
    p('  Write the mp4 to this file.')
    p(' --keep-temp-files:')
    p('  Keep all temporary files generated.')
    p(' -n|--dry-run:')
    p('  Don\'t actually run any commands.')
    p(' --correct-profile-only:')
    p('  Only correct the mp4 profile.')
    p(' --profile-level=<profile-level>:')
    p('  Rewrite the H.264 profile level if it\'s higher than this.')
    p(' --force-profile-level, --no-force-profile-level:')
    p('  Always rewrite the H.264 profile level, or not.')
    p(' --stop-before-extract-video:')
    p('  Don\'t do anything after extracting video.')
    p(' --stop-before-correct-profile:')
    p('  Don\'t do anything after correcting the mp4 profile.')
    p(' --stop-before-extract-audio:')
    p('  Don\'t do anything after extracting audio.')
    p(' --stop-before-convert-audio:')
    p('  Don\'t do anything after converting video.')
    p(' --stop-before-mp4:')
    p('  Don\'t finally create the mp4.')
    p(' --no-summary:')
    p('  Don\'t provide a summary.')


def parseopts(argv=None):
    opts = default_options(argv[0])
    sopts = 'hvo:n'
    lopts = [
        'help', 'usage', 'version', 'verbose',
        'mp4box=', 'ffmpeg=', 'mkvinfo=', 'mkvextract=',
        'hint', 'no-hint',
        'video-track=', 'audio-track=',
        'audio-delay-ms=', 'audio-bitrate=', 'audio-channels=',
        'audio-codec=', 'audio-lang=',
        'subtitle-track=', 'subtitle-lang=',
        'subtitle-default', 'subtitle-no-default',
        'output=', 'keep-temp-files', 'dry-run',
        'correct-profile-only', 'profile-level=',
        'force-profile-level', 'no-force-profile-level',
        'stop-before-extract-video', 'stop-before-correct-profile',
        'stop-before-extract-audio', 'stop-before-convert-audio',
        'stop-before-extract-sub',
        'stop-before-mp4',
        'stop-before-add-sub',
        'no-summary',
    ]
    try:
        options, arguments = getopt.gnu_getopt(argv[1:], sopts, lopts)
    except getopt.GetoptError:
        et, ev, tb = sys.exc_info()
        die(''.join(traceback.format_exception_only(et, ev)))
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
        elif opt == '--ffmpeg':
            opts['ffmpeg'] = optarg
        elif opt == '--mkvinfo':
            opts['mkvinfo'] = optarg
        elif opt == '--mkvextract':
            opts['mkvextract'] = optarg
        elif opt == '--no-hint':
            opts['hint'] = False
        elif opt == '--hint':
            opts['hint'] = True
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
        elif opt == '--audio-lang':
            opts['a_lang'] = optarg
        elif opt == '--subtitle-track':
            opts['subtitles_track'] = optarg
        elif opt == '--subtitle-lang':
            opts['s_lang'] = optarg
        elif opt == '--subtitle-default':
            opts['s_default'] = True
        elif opt == '--subtitle-no-default':
            opts['s_default'] = False
        elif opt in ('-o', '--output'):
            opts['output'] = optarg
        elif opt == '--keep-temp-files':
            opts['keep_temp_files'] = True
        elif opt in ('-n', '--dry-run'):
            opts['dry_run'] = True
        elif opt == '--correct-profile-only':
            opts['correct_prof_only'] = True
        elif opt == '--profile-level':
            opts['profile_level'] = optarg
        elif opt == '--force-profile-level':
            opts['force_profile_level'] = True
        elif opt == '--no-force-profile-level':
            opts['force_profile_level'] = False
        elif opt == '--stop-before-extract-video':
            opts['stop_v_ex'] = True
        elif opt == '--stop-before-correct-profile':
            opts['stop_correct'] = True
        elif opt == '--stop-before-extract-audio':
            opts['stop_a_ex'] = True
        elif opt == '--stop-before-convert-audio':
            opts['stop_a_conv'] = True
        elif opt == '--stop-before-extract-sub':
            opts['stop_s_ex'] = True
        elif opt == '--stop-before-mp4':
            opts['stop_mp4'] = True
        elif opt == '--stop-before-add-sub':
            opts['stop_s_add'] = True
        elif opt == '--no-summary':
            opts['summary'] = False
    return opts, arguments


def main(argv=None):
    if argv is None:
        argv = sys.argv
    opts, args = parseopts(argv)
    if len(args) != 1:
        die(simple_usage)
    if opts['correct_prof_only']:
        dry_correct_rawh264_profile(args[0], **opts)
    else:
        if opts['summary'] and not opts['dry_run']:
            keep, dry_run = opts['keep_temp_files'], opts['dry_run']
            opts['keep_temp_files'], opts['dry_run'] = True, True
            real_main(args[0], **opts)
            opts['keep_temp_files'], opts['dry_run'] = keep, dry_run
        real_main(args[0], **opts)
