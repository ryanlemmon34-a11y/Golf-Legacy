"""Collection-only: discover the suite exactly as `python3 -m unittest discover -s tests` does (no test is run), flatten it
in run order, and map each progress character of a finished log onto the test that printed it."""
import inspect, json, re, sys, time, unittest

log_path, out_path = sys.argv[1], sys.argv[2]
t0 = time.time()
suite = unittest.TestLoader().discover(start_dir='tests')
collect_s = time.time() - t0

def flat(s):
    for t in s:
        if isinstance(t, unittest.TestSuite):
            yield from flat(t)
        else:
            yield t
tests = list(flat(suite))
failed_imports = [t.id() for t in tests if type(t).__name__ in ('_FailedTest', 'ModuleImportFailure')]

# progress characters: the leading run of '.'/'s' on each line (the run said OK, so no E/F/x/u); printed text from
# tests and the DeprecationWarning interrupt lines, and the summary lines start with other characters
prog = ''
summary = False
for line in open(log_path, encoding='utf-8'):
    if line.startswith('-----'):
        summary = True
    if summary:
        continue
    prog += re.match(r'[.s]*', line).group(0)

def static_skip(t):
    cls = type(t)
    m = getattr(cls, t._testMethodName)
    for obj, where in ((cls, 'class'), (m, 'method')):
        if getattr(obj, '__unittest_skip__', False):
            return where, getattr(obj, '__unittest_skip_why__', '')
    return None

def runtime_skips(t):
    src = inspect.getsource(getattr(type(t), t._testMethodName))
    return re.findall(r"skipTest\((.*?)\)\s*$", src, re.M)

skips = []
for i, c in enumerate(prog):
    if c == 's':
        t = tests[i]
        skips.append({'index': i, 'id': t.id(), 'static_skip': static_skip(t), 'runtime_skipTest_in_body': runtime_skips(t)})

statics = [{'id': t.id(), 'where_why': static_skip(t)} for t in tests if static_skip(t)]
res = {'collected': len(tests), 'collect_seconds': round(collect_s, 1), 'failed_imports': failed_imports,
       'progress_chars': len(prog), 'dots': prog.count('.'), 's': prog.count('s'),
       'skips_by_position': skips, 'static_skips_at_collection': statics}
json.dump(res, open(out_path, 'w'), indent=1)
print(json.dumps(res, indent=1))
