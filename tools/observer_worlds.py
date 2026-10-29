"""The observer's world library: list, inspect, copy and export worlds (folders under worlds/).

A world is a session directory (golfsim.session): CURRENT, checkpoint generations gen_NNNNNN/ and the
published history in archive/. A folder holding only a history archive (MANIFEST.json, or world.json for
archives written before manifests) can be browsed read-only.

Compatibility (shown for every world, decided before anything is opened):
- the save format and schema must be this version's (golf-legacy-session/1, schema 1);
- the engine that saved it (a fingerprint of the simulation code, golfsim/savegame.engine_id) must be
  this one to resume it. A world saved by another engine is never resumed in place: it can be browsed
  read-only, or copied with an explicit acceptance (ENGINE_ACCEPTED.json in the copy records which engine
  saved it, which engine continues it and when), and only that copy is opened with the guard lifted.
  Commits that change only the observer, tools, docs or persistence code keep the engine the same.

Copies and diagnostic packages are made under the world's lock (no advance can commit while they are
read), from the committed generation; the source is never changed (the lock file aside, which is removed
again; a read-only source is copied without it).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import session as SES                                    # noqa: E402
from golfsim.archive import MANIFEST, legacy_files, published_stamp, read_manifest   # noqa: E402
import observer_jobs as J                                            # noqa: E402

ENGINE_ACCEPTED = 'ENGINE_ACCEPTED.json'
DIAGNOSTICS = '_diagnostics'
NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 _.-]{0,59}$')
_ENGINE = {}


def engine_now():
    """(engine id, commit) of the code running now (computed once)."""
    if not _ENGINE:
        from golfsim.savegame import engine_commit, engine_id
        _ENGINE['id'], _ENGINE['commit'] = engine_id(), engine_commit()
    return _ENGINE['id'], _ENGINE['commit']


def check_name(lib, name):
    """A new world's folder: a plain name, not used yet."""
    name = (name or '').strip()
    if not NAME.match(name) or name in ('.', '..') or name.startswith(DIAGNOSTICS):
        raise ValueError('Use letters, digits, spaces, dots, dashes or underscores (up to 60), starting with a letter or digit.')
    d = Path(lib) / name
    if d.exists():
        raise FileExistsError(f'A world named “{name}” already exists: choose another name.')
    return d


def inspect(path):
    """What the library shows about a folder, read from small files only (nothing is loaded or changed):
    kind ('session' or 'archive'), date, generation, seed, engine and format compatibility. None if the
    folder is neither a world nor an archive."""
    p = Path(path)
    info = {'name': p.name, 'path': p, 'problems': []}
    if (p / 'CURRENT').exists():
        info['kind'] = 'session'
        try:
            cur = json.loads((p / 'CURRENT').read_text())
            meta = json.loads((p / cur['dir'] / 'meta.json').read_text())
        except (OSError, ValueError, KeyError):
            meta = {}
            info['problems'].append('Its current checkpoint could not be read: opening it will fall back to the last '
                                    'known good generation, if there is one.')
        engine, commit = engine_now()
        info.update({'generation': meta.get('generation'), 'cursor': meta.get('cursor'), 'world_id': meta.get('world_id'),
                     'engine': meta.get('engine'), 'commit': meta.get('commit'), 'written': meta.get('written'),
                     'weeks_played': meta.get('weeks_played'), 'format': meta.get('format'), 'schema': meta.get('schema'),
                     'history_gen': meta.get('history_gen')})
        wid = str(meta.get('world_id') or '')
        info['seed'] = int(wid.split('-')[0]) if wid.split('-')[0].isdigit() else None
        info['format_ok'] = meta.get('format') == SES.FORMAT and meta.get('schema') == SES.SCHEMA
        info['same_engine'] = meta.get('engine') == engine
        try:
            info['accepted'] = json.loads((p / ENGINE_ACCEPTED).read_text())
        except (OSError, ValueError):
            info['accepted'] = None
        info['can_resume'] = bool(meta) and info['format_ok'] and (info['same_engine'] or info['accepted'] is not None)
        try:                                            # a lock whose owner certainly died is taken over on opening
            info['busy'] = not SES._owner_gone((p / 'lock').read_text())
        except OSError:
            info['busy'] = False
        info['interrupted'] = J.interrupted_job(p)
        a = p / 'archive'
    elif (p / MANIFEST).exists() or (p / 'world.json').exists():
        info['kind'] = 'archive'
        a = p
        info['can_resume'] = False
    else:
        return None
    try:
        stamp = published_stamp(a)
        info['years'] = list(stamp[1])
        info['manifest'] = stamp[2] is not None
        if info['kind'] == 'archive' and stamp[1]:
            info['seed'] = json.loads((a / (read_manifest(a)['files']['world'] if stamp[2] else 'world.json')).read_text()).get('seed')
    except (OSError, ValueError, KeyError):
        info['years'], info['manifest'] = [], False
    return info


def list_worlds(lib):
    out = []
    for p in sorted(Path(lib).iterdir()) if Path(lib).is_dir() else []:
        if p.is_dir() and not p.name.startswith(('.', DIAGNOSTICS)) and not p.name.endswith('.copying'):
            i = inspect(p)
            if i is not None:
                out.append(i)
    return out


class _Locked:
    """The world's lock for reading it whole (Busy if someone is advancing it). A source we cannot write
    to (read-only media) cannot be advanced either: it is read without the lock."""

    def __init__(self, d):
        self.d = Path(d)
        self.lock = None

    def __enter__(self):
        if (self.d / 'CURRENT').exists():
            try:
                self.lock = SES._FileLock(self.d / 'lock').__enter__()
            except PermissionError:
                self.lock = None
        return self

    def __exit__(self, *exc):
        if self.lock is not None:
            self.lock.__exit__(*exc)


def _skip(name):
    return (name in ('lock', J.JOB_FILE, 'CURRENT.tmp', 'MANIFEST.tmp') or name.startswith('lock.stale.')
            or (name.startswith('gen_') and name.endswith('.tmp')))


def copy_world(src, dst, job=None, accept_engine=False):
    """Copy a world (or an archive) to a new folder, from its committed state; the source is not changed.
    `accept_engine`: the copy records that it will be continued by this engine (ENGINE_ACCEPTED.json)."""
    src, dst = Path(src), Path(dst)
    if dst.exists():
        raise FileExistsError(f'{dst.name} already exists')
    tmp = dst.with_name(dst.name + '.copying')
    if tmp.exists():
        shutil.rmtree(tmp)
    info = inspect(src)
    with _Locked(src):
        files = [p for p in src.rglob('*') if p.is_file() and not any(_skip(part) for part in p.relative_to(src).parts)]
        total = sum(p.stat().st_size for p in files)
        done = 0
        if job:
            job.update(phase='copying', total=None)
        for p in files:
            q = tmp / p.relative_to(src)
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)
            done += p.stat().st_size
            if job:
                job.update(phase=f'copying ({done / 1e6:,.0f} of {total / 1e6:,.0f} MB)')
    if accept_engine and info and info.get('kind') == 'session':
        engine, commit = engine_now()
        (tmp / ENGINE_ACCEPTED).write_text(json.dumps({
            'saved_by_engine': info.get('engine'), 'saved_by_commit': info.get('commit'),
            'continued_by_engine': engine, 'continued_by_commit': commit, 'copied_from': src.name,
            'accepted': time.strftime('%Y-%m-%d %H:%M:%S'),
            'note': 'This copy was made to continue a world saved by another engine. Its earlier history was made '
                    'by that engine; everything after this date by the one named here.'}, indent=1))
    os.replace(tmp, dst)
    J.log(dst, f'copied from {src.name}' + (' (engine accepted)' if accept_engine else ''))
    return dst


def _sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _scrub(text):
    """Local folder names out of a log (tracebacks name files)."""
    for path, mark in ((str(ROOT), '<golf-legacy>'), (str(Path.home()), '<home>')):
        text = text.replace(path, mark)
    return text


def export_diagnostic(src, out_dir, note='', steps='', expected='', include_index=True, include_previous=False,
                      job=None, last_job=None):
    """A zip of everything needed to reproduce what the world shows, from its committed state:

    required -- CURRENT and the committed generation (state, metadata, the history it stands on), the
    published manifest and every file it names (or an older archive's files), the world's log and job
    record, an engine acceptance record if there is one; optional -- the history index (rebuildable from
    the season files, large), the last known good generation. Plus DIAGNOSTIC.json (versions, engine,
    seed, date, generations, every file with its size and SHA-256) and ISSUE.md (your note). Local folder
    names are removed from the log; nothing is uploaded anywhere."""
    src, out_dir = Path(src), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    out = out_dir / f'{src.name}-{stamp}.zip'
    info = inspect(src)
    if info is None:
        raise ValueError(f'{src.name} is not a world')
    engine, commit = engine_now()
    with _Locked(src):
        entries = []                                    # (path in zip, file, required)
        a = src / 'archive' if info['kind'] == 'session' else src
        if info['kind'] == 'session':
            gen = SES._committed_generation(src)
            entries.append(('CURRENT', src / 'CURRENT', True))
            g = src / f'gen_{gen:06d}'
            entries += [(p.relative_to(src).as_posix(), p, True) for p in sorted(g.rglob('*')) if p.is_file()]
            if include_previous:
                for d in sorted(src.glob('gen_[0-9]*')):
                    if d.is_dir() and d != g and not d.name.endswith('.tmp'):
                        entries += [(p.relative_to(src).as_posix(), p, False) for p in sorted(d.rglob('*')) if p.is_file()]
            for name in (J.LOG_FILE, J.JOB_FILE, ENGINE_ACCEPTED):
                if (src / name).exists():
                    entries.append((name, src / name, True))
        prefix = 'archive/' if info['kind'] == 'session' else ''
        m = read_manifest(a) if a.exists() else None
        if m is not None:
            names = [MANIFEST] + [f for k, f in m['files'].items() if k != 'years'] + list(m['files']['years'].values())
        elif a.exists() and (a / 'world.json').exists():
            lf = legacy_files(a)
            names = [f for k, f in lf.items() if k != 'years'] + list(lf['years'].values()) + \
                [n for n in ('PUBLISHED',) if (a / n).exists()]
        else:
            names = []
        entries += [(prefix + n, a / n, True) for n in names if (a / n).exists()]
        if include_index:
            entries += [(prefix + n, a / n, False) for n in ('index.sqlite', 'index.sqlite-wal') if (a / n).exists()]
        total = sum(p.stat().st_size for _, p, _ in entries)
        listing, done = [], 0
        tmp = out.with_name(out.name + '.tmp')
        with zipfile.ZipFile(tmp, 'w', allowZip64=True) as z:
            for arc, p, required in entries:
                if job:
                    job.update(phase=f'packing ({done / 1e6:,.0f} of {total / 1e6:,.0f} MB)')
                if arc == J.LOG_FILE:
                    data = _scrub(p.read_text(encoding='utf-8', errors='replace')).encode()
                    z.writestr(arc, data, compress_type=zipfile.ZIP_DEFLATED)
                    size, digest = len(data), hashlib.sha256(data).hexdigest()
                else:
                    already = p.name.endswith('.gz')
                    z.write(p, arc, compress_type=zipfile.ZIP_STORED if already else zipfile.ZIP_DEFLATED)
                    size, digest = p.stat().st_size, _sha256(p)
                done += p.stat().st_size
                listing.append({'path': arc, 'bytes': size, 'sha256': digest, 'required': required})
            diag = {'format': 'golf-legacy-diagnostic/1', 'exported': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'world': src.name, 'kind': info['kind'], 'world_id': info.get('world_id'), 'seed': info.get('seed'),
                    'cursor': info.get('cursor'), 'generation': info.get('generation'),
                    'history_generation': info.get('history_gen'), 'archived_seasons': info.get('years'),
                    'published_generation': (m or {}).get('generation'),
                    'save_format': info.get('format'), 'save_schema': info.get('schema'),
                    'saved_by_engine': info.get('engine'), 'saved_by_commit': info.get('commit'),
                    'observer_engine': engine, 'observer_commit': commit, 'engine_accepted': info.get('accepted'),
                    'python': sys.version.split()[0], 'platform': platform.platform(),
                    'last_operation': last_job, 'files': listing,
                    'privacy': 'File paths are relative to the world folder. The log has local folder names replaced '
                               'by <golf-legacy> and <home>. The save holds the simulated world only.'}
            z.writestr('DIAGNOSTIC.json', json.dumps(diag, indent=1), compress_type=zipfile.ZIP_DEFLATED)
            cur = info.get('cursor') or {}
            issue = (f'# Problem report: {src.name}\n\nExported {diag["exported"]}. World at '
                     f'{cur.get("year")} week {cur.get("week")} ({cur.get("phase")}), generation {info.get("generation")}, '
                     f'seed {info.get("seed")}.\nSaved by engine {info.get("engine")} (commit {info.get("commit")}); '
                     f'observer engine {engine} (commit {commit}).\n\n## What happened\n\n{note.strip() or "(not given)"}\n\n'
                     f'## Steps to reproduce\n\n{steps.strip() or "(not given)"}\n\n## What I expected\n\n'
                     f'{expected.strip() or "(not given)"}\n\n## Last operation\n\n'
                     f'{json.dumps(last_job, indent=1) if last_job else "(none this session)"}\n\n'
                     '## Using this package\n\nUnzip into an empty folder and open that folder (a copy) with the engine '
                     'commit named above; review it read-only before resuming. Required files: CURRENT, the gen_ folder, '
                     'archive/MANIFEST.json and the files it names. Optional: archive/index.sqlite (rebuildable), older '
                     'gen_ folders.\n')
            z.writestr('ISSUE.md', issue, compress_type=zipfile.ZIP_DEFLATED)
        os.replace(tmp, out)
    J.log(src, f'diagnostic package written: {out.name} ({out.stat().st_size / 1e6:,.1f} MB)')
    return out
