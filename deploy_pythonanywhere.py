"""Deploy HRMS to PythonAnywhere via API."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

USERNAME = os.environ.get('PA_USERNAME', 'MSyankombwe')
TOKEN = os.environ.get('PA_API_TOKEN', '').strip()
REGION = os.environ.get('PA_REGION', 'www').strip().lower()
PYTHON_VERSION = os.environ.get('PA_PYTHON', 'python310')

HOST = 'eu.pythonanywhere.com' if REGION == 'eu' else 'www.pythonanywhere.com'
DOMAIN = f'{USERNAME}.{"eu." if REGION == "eu" else ""}pythonanywhere.com'
API = f'https://{HOST}/api/v0/user/{USERNAME}'
PROJECT_DIR = f'/home/{USERNAME}/hrms'
VENV_DIR = f'/home/{USERNAME}/.virtualenvs/hrms'
WSGI_PATH = f'/var/www/{USERNAME}_pythonanywhere_com_wsgi.py'
if REGION == 'eu':
    WSGI_PATH = f'/var/www/{USERNAME}_eu_pythonanywhere_com_wsgi.py'

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'hrms-venv', 'staticfiles', 'media', '.idea', '.vscode'}
SKIP_SUFFIXES = {'.pyc', '.sqlite3'}
SKIP_NAMES = {'db.sqlite3', 'deploy_pythonanywhere.py', 'hrms_upload.zip'}


def headers():
    return {'Authorization': f'Token {TOKEN}'}


def api(method, path, **kwargs):
    return requests.request(method, f'{API}{path}', headers=headers(), timeout=180, **kwargs)


def die(msg: str):
    print(f'ERROR: {msg}')
    sys.exit(1)


def upload_bytes(remote_path: str, content: bytes):
    files = {'content': (Path(remote_path).name, content)}
    for attempt in range(8):
        r = api('POST', f'/files/path{remote_path}', files=files)
        if r.status_code in (200, 201):
            return
        if r.status_code == 429:
            wait = 12 + attempt * 3
            print(f'  rate limited, waiting {wait}s...')
            time.sleep(wait)
            continue
        die(f'Upload failed {remote_path}: {r.status_code} {r.text}')
    die(f'Upload failed after retries: {remote_path}')


def upload_project_as_zip():
    import zipfile
    from io import BytesIO

    print('Packaging project zip...')
    buf = BytesIO()
    count = 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in ROOT.rglob('*'):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if path.suffix in SKIP_SUFFIXES or path.name in SKIP_NAMES:
                continue
            zf.write(path, rel.as_posix())
            count += 1
    data = buf.getvalue()
    print(f'Uploading zip ({count} files, {len(data)} bytes)...')
    upload_bytes(f'/home/{USERNAME}/hrms_upload.zip', data)


def ensure_webapp(set_virtualenv: bool = False):
    r = api('GET', '/webapps/')
    if r.status_code != 200:
        die(f'List webapps failed: {r.status_code} {r.text}')
    apps = r.json() if isinstance(r.json(), list) else []
    domains = {a.get('domain_name') for a in apps}
    if DOMAIN in domains:
        print(f'Web app exists: https://{DOMAIN}')
    else:
        print(f'Creating web app {DOMAIN}...')
        r = api('POST', '/webapps/', data={'domain_name': DOMAIN, 'python_version': PYTHON_VERSION})
        if r.status_code not in (200, 201):
            for ver in ('python311', 'python312', 'python39'):
                r = api('POST', '/webapps/', data={'domain_name': DOMAIN, 'python_version': ver})
                if r.status_code in (200, 201):
                    print(f'Created with {ver}')
                    break
            else:
                die(f'Create webapp failed: {r.status_code} {r.text}')

    data = {'source_directory': PROJECT_DIR}
    if set_virtualenv:
        data['virtualenv_path'] = VENV_DIR
    r = api('PATCH', f'/webapps/{DOMAIN}/', data=data)
    if r.status_code not in (200, 201):
        # virtualenv warning sometimes returned as 400 even when path will exist soon
        if set_virtualenv and r.status_code == 400 and 'virtualenv' in r.text.lower():
            print(f'Note: {r.text}')
            return
        die(f'Configure webapp failed: {r.status_code} {r.text}')


def write_wsgi():
    wsgi = f'''import sys

path = '{PROJECT_DIR}'
if path not in sys.path:
    sys.path.insert(0, path)

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrms_project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
'''
    print('Writing WSGI file...')
    upload_bytes(WSGI_PATH, wsgi.encode())


def set_static_files():
    print('Configuring static file mappings...')
    r = api('GET', f'/webapps/{DOMAIN}/static_files/')
    existing = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    wanted = {
        '/static/': f'{PROJECT_DIR}/staticfiles',
        '/media/': f'{PROJECT_DIR}/media',
    }
    for url, directory in wanted.items():
        match = next((e for e in existing if e.get('url') == url), None)
        if match:
            api(
                'PATCH',
                f'/webapps/{DOMAIN}/static_files/{match["id"]}/',
                data={'url': url, 'path': directory},
            )
        else:
            api('POST', f'/webapps/{DOMAIN}/static_files/', data={'url': url, 'path': directory})


def write_setup_script():
    script = f'''#!/bin/bash
set -e
mkdir -p {PROJECT_DIR}/media {PROJECT_DIR}/staticfiles
mkdir -p /home/{USERNAME}/.virtualenvs
cd /home/{USERNAME}
python3 -c "import zipfile; zipfile.ZipFile('hrms_upload.zip').extractall('hrms')"
if [ ! -x {VENV_DIR}/bin/python ]; then
  python3.10 -m venv {VENV_DIR} || python3.11 -m venv {VENV_DIR} || python3.12 -m venv {VENV_DIR} || python3 -m venv {VENV_DIR}
fi
source {VENV_DIR}/bin/activate
pip install --upgrade pip
pip install -r {PROJECT_DIR}/requirements.txt
cd {PROJECT_DIR}
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py collectstatic --noinput
echo HRMS_SETUP_OK
'''
    upload_bytes(f'/home/{USERNAME}/hrms_setup.sh', script.encode())


def run_setup_via_schedule():
    """Run setup with a one-shot near-term scheduled task (works without browser console)."""
    write_setup_script()
    now = datetime.now(timezone.utc)
    minute = (now.minute + 2) % 60
    hour = now.hour if now.minute + 2 < 60 else (now.hour + 1) % 24
    cmd = f'bash /home/{USERNAME}/hrms_setup.sh > /home/{USERNAME}/hrms_setup.log 2>&1'
    print(f'Scheduling setup task at {hour:02d}:{minute:02d} UTC...')

    # Clear existing tasks to free the free-tier slot if needed
    r = api('GET', '/schedule/')
    if r.status_code == 200:
        for task in r.json():
            api('DELETE', f'/schedule/{task["id"]}/')

    r = api(
        'POST',
        '/schedule/',
        data={
            'command': cmd,
            'enabled': 'true',
            'interval': 'daily',
            'hour': str(hour),
            'minute': str(minute),
            'description': 'HRMS one-time setup',
        },
    )
    if r.status_code not in (200, 201):
        die(f'Schedule failed: {r.status_code} {r.text}')

    print('Waiting for setup task to finish (up to ~5 minutes)...')
    deadline = time.time() + 360
    while time.time() < deadline:
        time.sleep(15)
        r = api('GET', f'/files/path/home/{USERNAME}/hrms_setup.log')
        if r.status_code == 200:
            # binary or text
            try:
                text = r.content.decode('utf-8', errors='replace')
            except Exception:
                text = str(r.content)
            print('--- setup log (tail) ---')
            print(text[-1500:])
            if 'HRMS_SETUP_OK' in text:
                print('Setup completed.')
                # disable/delete the scheduled task
                r2 = api('GET', '/schedule/')
                if r2.status_code == 200:
                    for task in r2.json():
                        api('DELETE', f'/schedule/{task["id"]}/')
                return
            if 'Error' in text and 'Traceback' in text and 'HRMS_SETUP_OK' not in text:
                # keep waiting — may still be running
                pass
    die('Setup did not finish in time. Check /home/MSyankombwe/hrms_setup.log on PythonAnywhere.')


def try_console_setup():
    """Best-effort console setup; returns True on success."""
    write_setup_script()
    r = api(
        'POST',
        '/consoles/',
        data={'executable': 'bash', 'arguments': '', 'working_directory': f'/home/{USERNAME}'},
    )
    if r.status_code not in (200, 201):
        print(f'Console create failed ({r.status_code}); will use scheduled task.')
        return False
    console_id = r.json().get('id')
    if not console_id:
        return False
    time.sleep(2)
    r = api(
        'POST',
        f'/consoles/{console_id}/send_input/',
        data={'input': f'bash /home/{USERNAME}/hrms_setup.sh\n'},
    )
    if r.status_code not in (200, 201):
        print('Console send_input failed; will use scheduled task.')
        return False
    print('Waiting on console output...')
    for _ in range(40):
        time.sleep(8)
        r = api('GET', f'/consoles/{console_id}/get_latest_output/')
        if r.status_code != 200:
            continue
        out = r.json().get('output', '') if isinstance(r.json(), dict) else ''
        if 'HRMS_SETUP_OK' in out:
            print(out[-1000:])
            return True
        # empty output often means console never started in browser
        if _ == 3 and not out.strip():
            print('Console appears inactive; switching to scheduled task.')
            return False
    return False


def reload_webapp():
    print('Reloading web app...')
    r = api('POST', f'/webapps/{DOMAIN}/reload/')
    if r.status_code not in (200, 201):
        die(f'Reload failed: {r.status_code} {r.text}')


def main():
    if not TOKEN:
        die('PA_API_TOKEN is required')
    print(f'Deploying https://{DOMAIN}')
    r = api('GET', '/cpu/')
    if r.status_code != 200:
        die(f'Auth failed: {r.status_code} {r.text}')

    upload_project_as_zip()
    ensure_webapp(set_virtualenv=False)
    write_wsgi()
    set_static_files()

    if not try_console_setup():
        run_setup_via_schedule()

    ensure_webapp(set_virtualenv=True)
    reload_webapp()
    print()
    print('=' * 60)
    print(f'Live site: https://{DOMAIN}')
    print('Login: admin / demo1234')
    print('=' * 60)


if __name__ == '__main__':
    main()
