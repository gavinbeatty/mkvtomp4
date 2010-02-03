#!/bin/sh

set -u
set -e

if test $# -ne 2 ; then
    echo "usage: $(basename -- "$0") <tag> <prefix>" >&2
    exit 1
fi

tag="$1"
prefix="$2"
set -x
git archive --format tar --prefix="${prefix}/" "$tag" --output ../"$prefix".tar
bzip2 -9 ../"$prefix".tar
git archive --format zip --prefix="${prefix}/" "$tag" --output ../"$prefix".zip

