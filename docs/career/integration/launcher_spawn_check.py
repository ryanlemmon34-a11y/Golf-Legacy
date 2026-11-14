"""Practical launcher check: tools/observer.py run as a script with 2 spawned simulation workers; create a world over
HTTP, advance one week (workers re-run observer.py as '__mp_main__'), confirm the week and no traceback."""
import json, re, subprocess, sys, tempfile, time, os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
ROOT = Path(sys.argv[1])
lib = Path(tempfile.mkdtemp(prefix='launch_')) / 'worlds'
p = subprocess.Popen([sys.executable, str(ROOT / 'tools' / 'observer.py'), '--worlds', str(lib), '--port', '0', '--workers', '2'],
                     cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=dict(os.environ, PYTHONUNBUFFERED='1'))
out = []
url = None
while url is None:
    line = p.stdout.readline(); out.append(line)
    if not line and p.poll() is not None: break
    m = re.search(r'(http://localhost:\d+)/', line); url = m and m.group(1)
print('server', url, flush=True)
get = lambda path: urlopen(url + path, timeout=600).read().decode()
post = lambda path, d: urlopen(Request(url + path, data=urlencode(d).encode()), timeout=600).read().decode()
t = time.time()
post('/worlds/create', {'name': 'spawncheck', 'seed': '7', 'start_year': '2027'})
for _ in range(600):
    st = json.loads(get('/api/status'))
    if not st.get('job') or st['job'].get('state') in ('done', 'failed', 'error'): break
    time.sleep(1)
page = get('/')
print('created in %.0fs; page shows' % (time.time() - t), re.findall(r'\b2027, week \d+', page)[:1], flush=True)
f = dict(re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">', page.split('action="/advance">')[1].split('<button')[0]))
f['weeks'] = '1'
t = time.time(); post('/advance', f)
for _ in range(900):
    st = json.loads(get('/api/status'))
    if st.get('job') and st['job'].get('state') in ('done', 'failed', 'error'): break
    time.sleep(1)
page = get('/')
print('advance job', st['job'].get('state'), 'in %.0fs; page shows' % (time.time() - t), re.findall(r'\b2027, week \d+', page)[:1], flush=True)
print('career page status', urlopen(url + '/career', timeout=60).status)
p.terminate(); p.wait(30)
rest = p.stdout.read(); out.append(rest)
log = ''.join(out)
print('Traceback in server output:', 'Traceback' in log)
print(log[-1500:])
