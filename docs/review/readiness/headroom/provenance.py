"""Provenance for the starting-ability study: what a validation stamp is bound to, and the checks that refuse to
run or report on anything that was not validated.

A stamp (results/validation_stamp.json) is written by validate.py and says passed = true only after a full,
unmodified validation in which every failure condition was checked and none occurred. It is bound to the SHA-256 of
study.py, validate.py and the input fixture and to a digest of the checkout's golfsim sources (the same digest run.py
writes into each run manifest). run.py and report.py refuse a missing, failed or stale stamp.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = os.path.join(HERE, 'results', 'validation_stamp.json')
BOUND = ('study.py', 'validate.py', 'fixture', 'golfsim_digest')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def golfsim_digest(checkout):
    """Every golfsim/*.py, by name and bytes, in name order (as run.py's manifests have recorded it since 60c962b)."""
    golf = hashlib.sha256()
    gdir = os.path.join(checkout, 'golfsim')
    for name in sorted(os.listdir(gdir)):
        if name.endswith('.py'):
            golf.update(name.encode() + b'\0' + open(os.path.join(gdir, name), 'rb').read())
    return golf.hexdigest()


def bindings(checkout, fixture, here=HERE):
    return {'study.py': sha256_file(os.path.join(here, 'study.py')),
            'validate.py': sha256_file(os.path.join(here, 'validate.py')),
            'fixture': sha256_file(fixture), 'golfsim_digest': golfsim_digest(checkout)}


def stamp_problems(want, stamp_path=STAMP):
    """[] if the stamp exists, passed, and is bound to exactly `want` (a dict over BOUND); otherwise the reasons."""
    if not os.path.exists(stamp_path):
        return [f'no validation stamp at {stamp_path}']
    try:
        st = json.load(open(stamp_path))
    except (OSError, ValueError) as e:
        return [f'unreadable validation stamp: {e}']
    out = []
    if st.get('passed') is not True:
        out.append(f'validation did not pass: {st.get("failures")}')
    for k in BOUND:
        if st.get('bound', {}).get(k) != want.get(k):
            out.append(f'stale validation: {k} {str(st.get("bound", {}).get(k))[:12]} != current {str(want.get(k))[:12]}')
    return out
