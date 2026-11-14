#!/usr/bin/python3
"""Privileged GitHub release installation. Never trust URLs or paths in requests.

Only a hard-coded upstream repository is permitted. Installation runs the
existing complete release installer, preserving its own backup/repair logic.
HTTPS and release SHA256SUMS protect transport integrity; a future independent
publisher signature is required before claiming offline supply-chain security.
"""
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import Request,urlopen,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

TEST_CLI = len(sys.argv)==3 and sys.argv[1]=='--test-github-update'
sys.path.insert(0, str(Path(__file__).resolve().parent) if TEST_CLI else '/opt/uap-detector/uap')
try:
    from software_updates import DATA, REQUESTS, STATUS, VERSION, ARCHIVE_PATTERN, get_release, version_newer, version_parts, _write, _test_token
except ImportError:
    from software_updates import DATA, REQUESTS, STATUS, VERSION, ARCHIVE_PATTERN, get_release, version_newer, version_parts, _write, _test_token

CACHE=Path('/var/cache/uap-detector/releases')
MAX_ARCHIVE=100*1024*1024
MAX_EXTRACT=350*1024*1024


class _SafeGithubRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed=urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.hostname not in (
                'github.com','api.github.com',
                'release-assets.githubusercontent.com','objects.githubusercontent.com'):
            raise ValueError('GitHub release download redirected outside approved GitHub hosts.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def _asset_download(url,target,maxsize):
    token=_test_token()
    parsed=urlsplit(url)
    if parsed.scheme != 'https':raise ValueError('Release download requires HTTPS.')
    private_api=parsed.hostname=='api.github.com'
    if private_api:
        if not token or not re.fullmatch(
                r'/repos/DrRavenholm/Moon-Cheese-UAP-Detector/releases/assets/[1-9][0-9]*', parsed.path):
            raise ValueError('Private release asset is not an authorised Moon Cheese GitHub asset.')
    elif parsed.hostname != 'github.com':
        raise ValueError('Unexpected release download host.')
    req=Request(url,headers={'User-Agent':'Moon-Cheese-UAP-Detector/'+VERSION,
                             'Accept':'application/octet-stream'})
    if private_api:
        # An unredirected header does not follow GitHub's signed asset redirect.
        req.add_unredirected_header('Authorization','Bearer '+token)
    try:
        resp=build_opener(_SafeGithubRedirect()).open(req,timeout=90)
    except HTTPError as exc:
        raise ValueError(f'GitHub asset download failed: HTTP {exc.code}. Check release access and the read-only repository token.') from None
    except URLError as exc:
        raise ValueError('Cannot reach GitHub to download the release asset.') from exc
    with resp:
        if resp.status!=200:raise ValueError('GitHub download returned an unexpected HTTP status.')
        end=urlsplit(resp.url)
        if end.scheme!='https' or end.hostname not in (
                'github.com','api.github.com',
                'release-assets.githubusercontent.com','objects.githubusercontent.com'):
            raise ValueError('Release download redirected outside official GitHub hosts.')
        with open(target,'xb') as out:
            size=0
            while True:
                block=resp.read(1024*512)
                if not block:break
                size+=len(block)
                if size>maxsize:raise ValueError('Release download exceeds the allowed size.')
                out.write(block)
            out.flush();os.fsync(out.fileno())
    return size


def _checksum(checksum_file,filename):
    text=checksum_file.read_text(encoding='ascii')
    if len(text)>100_000:raise ValueError('Oversized checksum file.')
    checks=[]
    for line in text.splitlines():
        m=re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?([^/\\\x00-\x1f]+)',line)
        if m and m.group(2)==filename: checks.append(m.group(1).lower())
    if len(checks)!=1:raise ValueError('Release checksum file must contain exactly one matching archive entry.')
    return checks[0]


def _secure_extract(archive,path,version):
    prefix=f'moon-cheese-uap-detector-v{version}'
    expected=prefix+'/'
    with tarfile.open(archive,'r:gz') as tf:
        members=tf.getmembers()
        if not members or len(members)>3000:raise ValueError('Invalid release archive contents.')
        total=0
        for member in members:
            name=member.name.rstrip('/')
            if name!=prefix and not name.startswith(expected):
                raise ValueError('Archive contains files outside its versioned application folder.')
            parts=Path(name).parts
            if '..' in parts or Path(name).is_absolute() or member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError('Archive contains unsafe paths or file types.')
            if member.mode & 0o6000:raise ValueError('Archive contains privileged file permissions.')
            total+=max(member.size,0)
            if total>MAX_EXTRACT:raise ValueError('Unpacked release is too large.')
        try:
            tf.extractall(path,filter='data')
        except TypeError:
            # Some supported older Raspberry Pi OS Python builds lack the
            # backported tar extraction filter. All entries were validated.
            tf.extractall(path)
    folder=path/prefix
    if not (folder/'install.sh').is_file() or not (folder/'SHA256SUMS').is_file():
        raise ValueError('Release is missing the complete Moon Cheese installer or internal checksums.')
    # Release inside checksum manifest must pass before invoking root installer.
    result=subprocess.run(['sha256sum','-c','--quiet','SHA256SUMS'],cwd=folder,
                          capture_output=True,text=True,timeout=45)
    if result.returncode:
        raise ValueError('Internal release checksums are invalid.')
    return folder


def _busy():
    # Match the complete installer camera-job protection before downloading.
    p=DATA/'events.sqlite3'
    if p.exists():
        with sqlite3.connect(f'file:{p}?mode=ro',uri=True,timeout=5) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='observation_jobs'").fetchone():
                if db.execute("SELECT count(*) FROM observation_jobs WHERE status IN ('capturing','rendering','archiving','finalising')").fetchone()[0]:
                    return True
    try:
        state=json.loads((DATA/'status.json').read_text()).get('state','').lower()
        return state in ('recording','capturing','rendering','archiving','finalising')
    except (OSError,ValueError):return False


def perform(action,version,*,installed_version=None):
    installed_version=installed_version or VERSION
    version_parts(version)
    if action=='update' and not version_newer(version,installed_version):
        raise ValueError('Refusing to install a release that is not newer than the installed version.')
    if action=='repair' and version!=installed_version:
        raise ValueError('Repair must reinstall exactly the installed version.')
    if _busy():raise ValueError('Recording or rendering is active. Try again after the camera job finishes.')
    release=get_release(version)  # Resolves exact official tag, never accepts a request-provided URL
    if not release['archive'] or not release['checksum']:
        raise ValueError('GitHub release is missing its required archive or SHA256SUMS asset.')
    if _test_token() and not (release.get('archive_api') and release.get('checksum_api')):
        raise ValueError('GitHub release is missing its required archive or SHA256SUMS asset.')
    CACHE.mkdir(parents=True,exist_ok=True,mode=0o700)
    with tempfile.TemporaryDirectory(prefix='moon-cheese-update-',dir=str(CACHE)) as temp:
        root=Path(temp)
        name=ARCHIVE_PATTERN.format(version)
        archive=root/name
        checksum=root/'release-SHA256SUMS'
        _asset_download(release['checksum_api'] if _test_token() else release['checksum'],checksum,100_000)
        expected=_checksum(checksum,name)
        _asset_download(release['archive_api'] if _test_token() else release['archive'],archive,MAX_ARCHIVE)
        with archive.open('rb') as stream:
            sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if sha!=expected:raise ValueError('Downloaded archive SHA256 mismatch. Nothing was installed.')
        folder=_secure_extract(archive,root,version)
        if _busy():raise ValueError('Recording started during download. Installation postponed.')
        # Installation invokes the existing safe backup, upgrade and repair path.
        try:
            result=subprocess.run(['/bin/bash','install.sh'],cwd=folder,
                                  stdin=subprocess.DEVNULL,timeout=2700,check=False,
                                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        except subprocess.TimeoutExpired as e:
            raise ValueError('Installer timed out. Check the update service log and existing application backup.') from e
        if result.returncode:
            raise ValueError(f'Installer exited with code {result.returncode}. Consult the software update service log and preserved backup.')
        return 'Moon Cheese '+version+' installed and dashboard health verified by the existing installer.'


def process():
    jobs=sorted(REQUESTS.glob('*.json')) if REQUESTS.exists() else []
    if not jobs:return 0
    request=jobs[0]
    if request.is_symlink() or request.stat().st_size>4096:
        request.unlink(missing_ok=True);return 2
    try:
        data=json.loads(request.read_text())
    finally:request.unlink(missing_ok=True)
    action=data.get('action');version=data.get('version')
    state={'action':action,'version':version,'id':data.get('id',''),
           'updated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(timespec='seconds')}
    try:
        if action=='services':
            if version!=VERSION:
                raise ValueError('Service repair request does not match the installed version.')
            from service_repair import inspect as inspect_services, apply as restore_services
            _write(STATUS,dict(state,state='working',message='Inspecting official Moon Cheese service definitions.'))
            current=inspect_services()
            message=restore_services(current)
            # Do not include local backup paths in normal dashboard results.
            message='Moon Cheese service definitions checked and restored where needed. Backups retained; running services were not restarted.'
        else:
            if action not in ('update','repair') or not isinstance(version,str):
                raise ValueError('Unexpected software maintenance request.')
            _write(STATUS,dict(state,state='working',message='Downloading and verifying the official GitHub release.'))
            message=perform(action,version)
        _write(STATUS,dict(state,state='ok',message=message))
        print('Moon Cheese software operation successful:',action,version,flush=True)
        return 0
    except Exception as exc:
        # Never send raw HTTP responses, tokens, file paths or untrusted output to the UI.
        message=str(exc) if isinstance(exc,ValueError) else ('Service definitions could not be restored; inspect the maintenance service logs.' if action=='services' else f'{type(exc).__name__} during software installation; inspect privileged worker logs.')
        _write(STATUS,dict(state,state='error',message=message[:350]))
        print('Moon Cheese software operation failed:',action,type(exc).__name__,str(exc)[:350],file=sys.stderr)
        return 1

def run_test_update(version):
    """Manual first update: use the bundled v5.2 worker to update an older Pi
    straight from its private GitHub prerelease, without a partial hot patch.
    """
    if os.geteuid()!=0:raise ValueError('This update test must be run using sudo.')
    if not _test_token():
        raise ValueError('Configure private prerelease access first using software_updates.py.')
    installed=Path('/opt/uap-detector/uap/release.py')
    if not installed.is_file():raise ValueError('Moon Cheese is not installed.')
    match=re.search(r'^VERSION\s*=\s*[\'\"](\d+(?:\.\d+){2,4})[\'\"]\s*$',
                    installed.read_text(),re.MULTILINE)
    if not match:raise ValueError('Cannot identify the currently installed Moon Cheese version.')
    current=match.group(1)
    if not version_newer(version,current):
        raise ValueError(f'Cannot test an update from v{current} to v{version}: the release must be newer.')
    print(f'Testing complete GitHub update: v{current} -> v{version}',flush=True)
    result=perform('update',version,installed_version=current)
    print(result,flush=True)


if __name__=='__main__':
    if TEST_CLI:
        try:
            run_test_update(sys.argv[2].removeprefix('v'))
            sys.exit(0)
        except Exception as exc:
            print('GitHub update test failed:',str(exc) if isinstance(exc,ValueError) else type(exc).__name__,file=sys.stderr)
            sys.exit(1)
    sys.exit(process())
