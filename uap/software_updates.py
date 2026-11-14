"""Official GitHub release metadata and local update request protocol.

Stable releases remain the default. An administrator can enable private
prerelease testing locally with a repository-scoped, read-only access token.
"""
import json
import os
import stat
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from release import VERSION, REPOSITORY

DATA = Path('/var/lib/uap-detector')
API = 'https://api.github.com/repos/' + REPOSITORY + '/releases'
REQUESTS = DATA / 'software-update-requests'
CHECK = DATA / 'software-release-check.json'
STATUS = DATA / 'software-update-status.json'
RELEASE_VERSION = re.compile(r'^v(\d+(?:\.\d+){2,4})$')
ARCHIVE_PATTERN = 'moon-cheese-uap-detector-v{}.tar.gz'
TEST_ACCESS = Path('/etc/uap-detector/github-release-test.json')



def version_parts(v):
    """Support older Moon Cheese multi-part versions without floating-point rounding."""
    m=RELEASE_VERSION.fullmatch('v'+str(v).removeprefix('v'))
    if not m: raise ValueError('Invalid release version.')
    return tuple(int(x) for x in m.group(1).split('.'))


def version_newer(a,b):
    x,y=version_parts(a),version_parts(b)
    length=max(len(x),len(y))
    return x+(0,)*(length-len(x)) > y+(0,)*(length-len(y))


def _test_token():
    """Read restricted local test credentials, never return them in UI data."""
    try:
        if TEST_ACCESS.is_symlink():
            return None
        st = TEST_ACCESS.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or (st.st_mode & 0o027):
            return None
        data = json.loads(TEST_ACCESS.read_text())
        if data.get('mode') != 'private-prerelease':
            return None
        token = data.get('token', '')
        if not isinstance(token, str) or not (20 <= len(token) <= 512) or '\n' in token or '\r' in token:
            return None
        return token
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def _fetch_json(path, timeout=10, token=None):
    headers = {'Accept':'application/vnd.github+json',
               'User-Agent':'Moon-Cheese-UAP-Detector/'+VERSION,
               'X-GitHub-Api-Version':'2022-11-28'}
    if token:
        if not path.startswith('https://api.github.com/repos/' + REPOSITORY + '/'):
            raise ValueError('Refusing to transmit the release credential outside the official GitHub repository.')
    req=Request(path, headers=headers)
    if token:
        # Never forward credentials if GitHub redirects the API request.
        req.add_unredirected_header('Authorization','Bearer '+token)
    with urlopen(req, timeout=timeout) as resp:
        if resp.status != 200: raise ValueError('GitHub did not return HTTP 200.')
        size=resp.headers.get('Content-Length')
        if size and int(size)>1024*1024:raise ValueError('Release metadata is too large.')
        raw=resp.read(1024*1024+1)
        if len(raw)>1024*1024:raise ValueError('Release metadata is too large.')
        return json.loads(raw)


def validate_release(data, *, requested_version=None, allow_prerelease=False):
    if not isinstance(data,dict) or data.get('draft') or (data.get('prerelease') and not allow_prerelease):
        raise ValueError('The release is not approved for the selected update channel.')
    tag=data.get('tag_name','')
    if not isinstance(tag,str) or not RELEASE_VERSION.fullmatch(tag):
        raise ValueError('Release tag is not a valid Moon Cheese version.')
    version=tag[1:]
    if requested_version and version!=requested_version:
        raise ValueError('The release does not match the requested version.')
    assets=data.get('assets',[])
    if not isinstance(assets,list): raise ValueError('Invalid release assets.')
    expected=ARCHIVE_PATTERN.format(version)
    names={}
    api_assets={}
    for item in assets:
        if isinstance(item,dict) and item.get('name') in (expected, 'SHA256SUMS'):
            name=item['name']
            if name in names:raise ValueError('Ambiguous duplicate release asset.')
            url=str(item.get('browser_download_url') or '')
            allowed=f'https://github.com/{REPOSITORY}/releases/download/{tag}/'
            if url != allowed+name:
                raise ValueError('Release asset URL does not match the official repository.')
            names[name]=url
            asset_id=item.get('id')
            if isinstance(asset_id,int) and asset_id>0:
                expected_api=f'https://api.github.com/repos/{REPOSITORY}/releases/assets/{asset_id}'
                if item.get('url') not in (None,expected_api):
                    raise ValueError('Unexpected GitHub release asset API URL.')
                api_assets[name]=expected_api
            elif allow_prerelease:
                raise ValueError('Private test release is missing an asset ID.')
    return {'version':version,'tag':tag,'archive':names.get(expected),
            'checksum':names.get('SHA256SUMS'),
            'archive_api':api_assets.get(expected), 'checksum_api':api_assets.get('SHA256SUMS'),
            'html_url':f'https://github.com/{REPOSITORY}/releases/tag/{tag}',
            'prerelease':bool(data.get('prerelease'))}


def get_release(version=None):
    token=_test_token()
    testing=bool(token)
    try:
        if version is not None:
            version_parts(version)
            return validate_release(_fetch_json(API+'/tags/v'+version,token=token),
                                    requested_version=version,allow_prerelease=testing)
        if testing:
            releases=_fetch_json(API+'?per_page=100',token=token)
            if not isinstance(releases,list):raise ValueError('Invalid GitHub release listing.')
            candidates=[]
            for item in releases:
                if isinstance(item,dict) and not item.get('draft'):
                    try:
                        result=validate_release(item,allow_prerelease=True)
                        candidates.append(result)
                    except ValueError:pass
            if not candidates:raise ValueError('No accessible Moon Cheese release is available in private testing.')
            return max(candidates,key=lambda r: version_parts(r['version']))
        return validate_release(_fetch_json(API+'/latest'))
    except HTTPError as e:
        if e.code in (401,403):
            raise ValueError('GitHub denied access. Check that the testing token has Contents: read-only access to the Moon Cheese repository.') from None
        if e.code==404:
            raise ValueError('GitHub release not found or inaccessible. Check the private testing token and version tag.') from None
        if e.code==429:
            raise ValueError('GitHub rate limit reached. Try again later.') from None
        raise ValueError(f'GitHub returned HTTP {e.code} when checking releases.') from None
    except (OSError,URLError,TimeoutError) as e:
        raise ValueError('Cannot reach GitHub. Check internet access and try again.') from e


def configure_private_testing():
    """Root-only interactive setup. Credentials never enter shell history or web logs."""
    import getpass
    if os.geteuid()!=0:raise ValueError('This operation requires sudo.')
    token=getpass.getpass('Paste GitHub fine-grained read-only token (input hidden): ').strip()
    if not token or len(token)>512 or any(x in token for x in ('\n','\r',' ')):
        raise ValueError('Invalid token format.')
    # Validate access to the intended repository before storing the token.
    listing=_fetch_json(API+'?per_page=5',token=token)
    if not isinstance(listing,list):raise ValueError('GitHub did not return a release listing.')
    permissions = Path('/etc/uap-detector/auth.json')
    if not permissions.is_file():raise ValueError('The Moon Cheese administrator account is not installed.')
    group=permissions.stat().st_gid
    TEST_ACCESS.parent.mkdir(parents=True,exist_ok=True)
    temporary=TEST_ACCESS.with_name(TEST_ACCESS.name+'.'+secrets.token_hex(6)+'.tmp')
    try:
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:
            json.dump({'mode':'private-prerelease','token':token},f)
            f.flush();os.fsync(f.fileno())
        os.chown(temporary,0,group)
        os.chmod(temporary,0o640)
        os.replace(temporary,TEST_ACCESS)
    finally:
        temporary.unlink(missing_ok=True)
    CHECK.unlink(missing_ok=True)
    print('Private prerelease testing enabled. The token is stored locally, not in the software package.')


def disable_private_testing():
    if os.geteuid()!=0:raise ValueError('This operation requires sudo.')
    TEST_ACCESS.unlink(missing_ok=True)
    CHECK.unlink(missing_ok=True)
    print('Private prerelease testing disabled. Normal public stable-release checking restored.')


def _read(path):
    try:
        if path.is_symlink():return {}
        v=json.loads(path.read_text())
        return v if isinstance(v,dict) else {}
    except (OSError, ValueError):return {}


def _write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+secrets.token_hex(6)+'.tmp')
    with tmp.open('x') as f:
        os.chmod(tmp,0o644 if path==STATUS else 0o600)
        json.dump(obj,f)
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def latest_info(force=False):
    info=_read(CHECK)
    if force:
        try:
            release=get_release()
            message=('A newer private testing release is available.' if _test_token() else 'A newer stable version is available.') if version_newer(release['version'],VERSION) else 'The installed version is up to date.'
            info={'checked_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                  'latest':release['version'],'available':version_newer(release['version'],VERSION),
                  'has_assets':bool(release['archive'] and release['checksum']),
                  'message':message,'release_url':release['html_url'], 'channel':'private-prerelease' if _test_token() else 'stable'}
            if _test_token() and not (release.get('archive_api') and release.get('checksum_api')):
                info['has_assets']=False
            if not info['has_assets']:
                info['message']='The selected GitHub release lacks the required archive and SHA256SUMS asset.'
            try:
                same=get_release(VERSION)
                info['repair_ready']=bool(same['archive'] and same['checksum'] and
                                          (not _test_token() or (same.get('archive_api') and same.get('checksum_api'))))
            except (ValueError,HTTPError):
                info['repair_ready']=False
        except (ValueError,HTTPError) as exc:
            info={'checked_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                  'latest':None,'available':False,'has_assets':False,'repair_ready':False,'message':str(exc), 'channel':'private-prerelease' if _test_token() else 'stable'}
        _write(CHECK,info)
    # A previously cached check may refer to an older installed version. Recompute
    # availability from the actual code version instead of trusting the cache.
    info=dict(info)
    if info.get('latest'):
        try:
            newer=version_newer(info['latest'],VERSION)
            info['available']=newer
            if not newer:
                info['message']='The installed version is up to date.'
        except ValueError:
            info['available']=False
            info['message']='Stored release information is invalid. Select Check for updates.'
    return dict(info,worker=_read(STATUS),installed=VERSION,channel='private-prerelease' if _test_token() else 'stable')


def enqueue_service_repair(admin):
    """Queue opt-in owned-unit restore using the existing root-owned worker path."""
    from service_repair import inspect
    current=inspect()
    if any(x.startswith('symlink') for x in current.values()):
        raise ValueError('A service definition is a symbolic link; investigate manually before repairing.')
    if not any(x in ('missing','modified') for x in current.values()):
        raise ValueError('All installed Moon Cheese service definitions match; no repair is needed.')
    from datetime import timedelta
    last=_read(STATUS)
    try: age=datetime.now(timezone.utc)-datetime.fromisoformat(last['updated_utc'])
    except (KeyError,TypeError,ValueError): age=timedelta(days=1)
    REQUESTS.mkdir(mode=0o750,parents=True,exist_ok=True)
    if any(REQUESTS.glob('*.json')) or (last.get('state') in ('queued','working') and age<timedelta(minutes=60)):
        raise ValueError('Another software maintenance operation is already queued.')
    jobid=secrets.token_hex(16)
    _write(STATUS,{'state':'queued','action':'services','version':VERSION,
                   'message':'Inspecting and restoring Moon Cheese-owned systemd definitions only.',
                   'updated_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'id':jobid})
    _write(REQUESTS/(jobid+'.json'),{'action':'services','version':VERSION,
                                    'admin':str(admin)[:64],'id':jobid})
    return jobid


def enqueue(action, admin):
    if action not in ('update','repair'):raise ValueError('Unknown software operation.')
    if action=='update':
        info=latest_info(force=True)
        if not info.get('available') or not info.get('has_assets'):
            raise ValueError(info.get('message') or 'No installable update available.')
        version=info['latest']
    else:
        version=VERSION
        release=get_release(VERSION)
        if not release['archive'] or not release['checksum']:
            raise ValueError('This installed version is not available as a complete GitHub Release. Repair is unavailable.')
    REQUESTS.mkdir(mode=0o750,parents=True,exist_ok=True)
    last=_read(STATUS)
    from datetime import timedelta
    try:age=datetime.now(timezone.utc)-datetime.fromisoformat(last['updated_utc'])
    except (KeyError,TypeError,ValueError):age=timedelta(days=1)
    if any(REQUESTS.glob('*.json')) or (last.get('state') in ('working','queued') and age<timedelta(minutes=60)):
        raise ValueError('A software installation is already pending. Check its status first.')
    jobid=secrets.token_hex(16)
    _write(STATUS,{'state':'queued','action':action,'version':version,
                   'message':'Request queued. Waiting for the privileged update service.',
                   'updated_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'id':jobid})
    _write(REQUESTS/(jobid+'.json'),{'action':action,'version':version,
                                    'admin':str(admin)[:64],'id':jobid})
    return jobid


if __name__=='__main__':
    import sys
    try:
        if sys.argv[1:]==['enable-private-testing']:
            configure_private_testing()
        elif sys.argv[1:]==['disable-private-testing']:
            disable_private_testing()
        else:
            raise ValueError('Use: sudo python3 /opt/uap-detector/uap/software_updates.py [enable-private-testing|disable-private-testing]')
    except (ValueError,HTTPError,URLError) as exc:
        print('GitHub configuration failed:',str(exc) if not isinstance(exc,HTTPError) else 'GitHub returned HTTP '+str(exc.code),file=sys.stderr)
        sys.exit(1)
