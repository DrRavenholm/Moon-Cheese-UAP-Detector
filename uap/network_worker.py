#!/usr/bin/python3
"""Root-only Moon Cheese networking worker, invoked by systemd.

This helper is never exposed as a web endpoint. File inputs are validated again;
Cloudflare credentials are kept in root-readable /etc/uap-detector/network.json.
"""
import ipaddress
import fcntl
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, '/opt/uap-detector/uap')
from network_setup import REQUESTS, STATUS, STATUS_DIR, PENDING, PUBLIC_MANAGED, valid_hostname, valid_id, valid_token, valid_ipv4, local_ip

ROOT=Path('/etc/uap-detector')
CONF=ROOT/'network.json'
NPM_PROFILE=ROOT/'network-npm.json'
TUNNEL_PROFILE=ROOT/'network-tunnel.json'
RUN=Path('/run/uap-network')
PUBLIC_PENDING=RUN/'pending-public.json'
NPM='http://127.0.0.1:8181/api'
CF='https://api.cloudflare.com/client/v4'
TIMEOUT=18
# NPM's Cloudflare DNS challenge waits at least 120 seconds before ACME
# validation. Allow sufficient time for NPM/Certbot to finish afterwards.
CERTIFICATE_TIMEOUT=420
CERTIFICATE_RECONCILE_SECONDS=90
DOMAIN_PREVIEW=ROOT/'network-domain-preview.json'
DOMAIN_PROGRESS=ROOT/'network-domain-progress.json'
TUNNEL_PROGRESS=ROOT/'network-tunnel-progress.json'
PUBLIC_TUNNEL=RUN/'tunnel-public.json'
CANDIDATE_TOKEN=ROOT/'cloudflared-candidate.token'
TUNNEL_REMOVE_PROGRESS=ROOT/'network-tunnel-removal.json'
TUNNEL_REPLACE_CLEANUP=ROOT/'network-tunnel-previous-cleanup.json'
NETWORK_LOCK=Path('/var/lib/uap-detector/network-safety/network-operation.lock')
ACTIVE_REQUEST_ID=''  # diagnostic correlation only; never authorisation
ACTIVE_REQUEST_ACTION=''


def write_json(path, content, mode=0o644):
    path.parent.mkdir(mode=0o700 if mode==0o600 else 0o755,parents=True,exist_ok=True)
    fd, temporary=tempfile.mkstemp(prefix='.network-',dir=path.parent)
    try:
        os.fchmod(fd,mode)
        with os.fdopen(fd,'w') as stream: json.dump(content,stream)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def status(action,state,message,**extra):
    # The underlying NPM/Tunnel installer reports its traditional action name.
    # Associate its terminal result with the new one-button operation, so the
    # browser can match the request ID and stop showing "Queued".
    if ACTIVE_REQUEST_ACTION=='npm_apply' and action in ('npm','npm_change'):
        action='npm_apply'
    elif ACTIVE_REQUEST_ACTION=='tunnel_apply' and action=='tunnel':
        action='tunnel_apply'
    # A short scrubbed result only; do not log or expose API tokens.
    entry={'action':action,'state':state,'message':message[:500],
           'time':time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime()),**extra}
    if ACTIVE_REQUEST_ID:entry['request_id']=ACTIVE_REQUEST_ID
    write_json(STATUS,entry)
    if re.fullmatch(r'[a-z_]+',action):write_json(STATUS_DIR/(action+'.json'),entry)


def load_config():
    try:return json.loads(CONF.read_text())
    except FileNotFoundError:return {}


def _save_access_profile(config):
    """Keep each authorised local access configuration separately, never export its token."""
    if not isinstance(config,dict):return
    if config.get('npm_host_id') and config.get('hostname') and config.get('zone'):
        write_json(NPM_PROFILE,config,0o600)
    elif config.get('tunnel_id') and config.get('hostname') and config.get('zone') and config.get('account'):
        write_json(TUNNEL_PROFILE,config,0o600)


def save_config(config):
    ROOT.mkdir(mode=0o750,parents=True,exist_ok=True)
    # Save previous method before replacing network.json. A switch to Local
    # mode doesn't erase either profile; both root files remain mode 0600.
    _save_access_profile(load_config())
    _save_access_profile(config)
    write_json(CONF,config,0o600)
    publish_managed_domain(config)


def publish_managed_domain(config=None):
    if config is None:config=load_config()
    profile=config if config.get('npm_host_id') else read_json_optional(NPM_PROFILE)
    if not isinstance(profile,dict):profile={}
    public={k:profile.get(k) for k in ('hostname','setup_step','npm_host_enabled','zone','certificate_contact_email')}
    public['mode']=config.get('mode','local')
    public['credentials_saved']=bool(profile.get('token'))
    previous=profile.get('previous_managed')
    if isinstance(previous,dict):public['previous_hostname']=previous.get('hostname')
    write_json(PUBLIC_MANAGED,public)
    publish_tunnel_state(config)


def publish_tunnel_state(config=None):
    """Public, non-secret state for the administrator page. Never export IDs/tokens."""
    if config is None:config=load_config()
    stage=read_json_optional(TUNNEL_PROGRESS)
    profile=config if config.get('tunnel_id') else read_json_optional(TUNNEL_PROFILE)
    if not isinstance(profile,dict):profile={}
    managed=bool(profile.get('tunnel_id') and profile.get('hostname') and
                 profile.get('account') and profile.get('zone'))
    value={'mode':config.get('mode','local'), 'managed':managed,
           'hostname':profile.get('hostname','') if managed else '',
           'stage_hostname':stage.get('hostname','') if stage else '',
           'stage_step':stage.get('setup_step','created') if stage else '',
           'unfinished':bool(stage),
           'previous_hostname':(profile.get('previous_tunnel') or {}).get('hostname',''),
           'account':stage.get('account') if stage else (profile.get('account','') if managed else ''),
           'zone':stage.get('zone') if stage else (profile.get('zone','') if managed else ''),
           'credentials_saved':bool(profile.get('token') and profile.get('account'))}
    write_json(PUBLIC_TUNNEL,value)


def persist_tunnel_stage(stage):
    write_json(TUNNEL_PROGRESS,stage,0o600)
    publish_tunnel_state()


def clear_tunnel_stage():
    TUNNEL_PROGRESS.unlink(missing_ok=True)
    publish_tunnel_state()


def _tunnel_details_match(account,token,hostname,tunnel_id):
    prefix='/accounts/'+account+'/cfd_tunnel'
    item=cloudflare(prefix+'/'+tunnel_id,token)
    if item.get('id') not in (None,tunnel_id) or item.get('name')!=tunnel_name(hostname) or item.get('config_src')!='cloudflare':
        raise ValueError('Cloudflare Tunnel identity does not match the managed hostname.')
    configuration=cloudflare(prefix+'/'+tunnel_id+'/configurations',token)
    if not tunnel_ingress_matches(configuration,hostname):
        raise ValueError('Tunnel route differs from the saved Moon Cheese origin; nothing was changed.')
    return item


def _tunnel_cname_matches(content,tunnel_id):
    # DNS canonical names may include a final dot; still require the exact ID.
    return (isinstance(content,str) and content.strip().lower().rstrip('.') ==
            tunnel_id.lower()+'.cfargotunnel.com')


def _exact_tunnel_dns(zone,token,name,tunnel_id,record_id=None):
    records=[d for d in dns_records(zone,token,name) if d.get('name','').lower()==name and
             d.get('type') in ('A','AAAA','CNAME')]
    if len(records)!=1 or records[0].get('type')!='CNAME' or (record_id and records[0].get('id')!=record_id) or \
       not _tunnel_cname_matches(records[0].get('content',''),tunnel_id):
        raise ValueError('Tunnel DNS record differs from the saved Moon Cheese route; nothing was changed.')
    return records[0]


def _token_file(path, value):
    fd,tmp=tempfile.mkstemp(prefix='.cloudflared-',dir=ROOT)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w') as stream: stream.write(value+'\n')
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def _tunnel_connected(account,token,tunnel_id,attempts=15):
    prefix='/accounts/'+account+'/cfd_tunnel'
    for attempt in range(attempts):
        item=cloudflare(prefix+'/'+tunnel_id,token)
        if item.get('status') in ('healthy','degraded'):return True
        if attempt<attempts-1:time.sleep(4)
    return False


def abandon_tunnel_progress(params):
    stage=read_json_optional(TUNNEL_PROGRESS)
    if not stage:
        status('tunnel_abandon','ok','There is no unfinished Tunnel setup to abandon.')
        return
    if params.get('hostname','').lower().strip()!=stage.get('hostname'):
        raise ValueError('Enter the exact unfinished Tunnel hostname to acknowledge which setup you are abandoning.')
    cfg=load_config()
    if cfg.get('mode')=='tunnel' and cfg.get('tunnel_id')==stage.get('tunnel_id'):
        raise ValueError('This is the active Tunnel. Disable it through Manage Tunnel, not Abandon unfinished setup.')
    # Abandonment never deletes Cloudflare-side resources. An existing active
    # connector is untouched; if the candidate was running, stop that only.
    if Path('/etc/systemd/system/uap-cloudflared-candidate.service').exists():
        run(['/usr/bin/systemctl','disable','--now','uap-cloudflared-candidate.service'],timeout=20)
    CANDIDATE_TOKEN.unlink(missing_ok=True)
    clear_tunnel_stage()
    status('tunnel_abandon','ok','Unfinished local Tunnel setup cleared. Any existing Cloudflare Tunnel and DNS record were preserved for manual review.')


def disable_tunnel(params):
    cfg=load_config()
    if not cfg.get('tunnel_id') or not cfg.get('hostname'):
        raise ValueError('No completed Moon Cheese Tunnel is stored.')
    if params.get('hostname','').strip().lower()!=cfg['hostname']:
        raise ValueError('The confirmation hostname does not match the saved Tunnel.')
    if Path('/etc/systemd/system/uap-cloudflared.service').exists():
        run(['/usr/bin/systemctl','disable','--now','uap-cloudflared.service'],timeout=30)
    cfg['mode']='local';save_config(cfg)
    status('tunnel_disable','ok','Tunnel connector stopped. The Cloudflare Tunnel, DNS record and saved credentials were preserved; local-only mode is now selected.')


def _tunnel_list(account,token,name):
    """Ask Cloudflare for undeleted tunnels, never infer deletion from local state."""
    query=urllib.parse.urlencode({'name':tunnel_name(name),'is_deleted':'false','per_page':100})
    items=cloudflare('/accounts/'+account+'/cfd_tunnel?'+query,token)
    if not isinstance(items,list):
        raise ValueError('Cloudflare did not return a verifiable Tunnel list.')
    return [t for t in items if isinstance(t,dict) and t.get('name')==tunnel_name(name)]


def _verify_provider_absent(account,zone,token,name,tunnel_id,dns_id=None,*,attempts=4):
    """Only report removal after Cloudflare returns neither target resource."""
    for attempt in range(attempts):
        records=dns_records(zone,token,name)
        if not isinstance(records,list):
            raise ValueError('Cloudflare did not return a verifiable DNS record list.')
        relevant=[r for r in records if r.get('name','').lower()==name and
                  (r.get('id')==dns_id or (r.get('type')=='CNAME' and
                   _tunnel_cname_matches(r.get('content',''),tunnel_id)))]
        present=[t for t in _tunnel_list(account,token,name) if t.get('id')==tunnel_id]
        if not relevant and not present:return True
        if attempt<attempts-1:time.sleep(2)
    return False


def _removable_tunnel_dns(account,zone,token,name,tunnel_id,record_id=None):
    """The exact managed CNAME, or an orphaned/predecessor Moon Cheese route.

    Refuse other DNS types, another record ID, and active/unrelated tunnel
    destinations. This is only used for authenticated explicit removal.
    """
    rows=[r for r in dns_records(zone,token,name) if r.get('name','').lower()==name and
          r.get('type') in ('A','AAAA','CNAME')]
    if not rows:return None
    if len(rows)!=1 or rows[0].get('type')!='CNAME' or (record_id and rows[0].get('id')!=record_id):
        raise ValueError('Another DNS record owns this hostname; no resources were removed.')
    prior=_tunnel_id_from_cname(rows[0].get('content',''))
    if prior==tunnel_id:return rows[0]
    if not prior or _safe_previous_tunnel(account,token,name,prior) not in ('missing','owned_inactive'):
        raise ValueError('An active or unrelated DNS Tunnel owns this hostname; it was not removed.')
    return rows[0]


def _delete_owned_tunnel(account,zone,token,name,tunnel_id,dns_id,progress_path):
    """Persist a repeatable removal transaction; never delete a different record."""
    stage=read_json_optional(progress_path) or {}
    if stage.get('tunnel_id')!=tunnel_id or stage.get('hostname')!=name:
        raise ValueError('The recorded removal is for a different Tunnel. No deletion attempted.')
    record=_removable_tunnel_dns(account,zone,token,name,tunnel_id,dns_id)
    if record:
        record_id=record['id']
        stage['dns_id']=record_id
        write_json(progress_path,stage,0o600)
        cloudflare('/zones/'+zone+'/dns_records/'+record_id,token,'DELETE')
    # Do not rely on a successful DELETE response as evidence of deletion.
    # Read-after-write may lag briefly; still never report success while the
    # exact record remains visible to Cloudflare.
    for attempt in range(4):
        rows_after=dns_records(zone,token,name)
        if not any(r.get('name','').lower()==name and
                   (r.get('id')==stage.get('dns_id') or
                    (r.get('type')=='CNAME' and _tunnel_cname_matches(r.get('content',''),tunnel_id)))
                   for r in rows_after):break
        if attempt<3:time.sleep(2)
    else:
        raise ValueError('Cloudflare still lists the selected DNS record. Removal is incomplete; retry after checking Cloudflare.')
    stage['dns_removed']=True;write_json(progress_path,stage,0o600)
    matching=[t for t in _tunnel_list(account,token,name) if t.get('id')==tunnel_id]
    if matching:
        if matching[0].get('status') in ('healthy','degraded'):
            raise ValueError('The Tunnel has an active connector. Stop it before requesting deletion.')
        cloudflare('/accounts/'+account+'/cfd_tunnel/'+tunnel_id,token,'DELETE')
    stage['tunnel_delete_requested']=True;write_json(progress_path,stage,0o600)
    if not _verify_provider_absent(account,zone,token,name,tunnel_id,stage.get('dns_id')):
        raise ValueError('Cloudflare still lists the Tunnel or its DNS record. Local ownership was retained for retry.')


def cleanup_unfinished_tunnel(params):
    """Explicitly remove only the exact saved unfinished Moon Cheese Tunnel."""
    stage=read_json_optional(TUNNEL_PROGRESS)
    if not stage or not stage.get('tunnel_id'):
        raise ValueError('No verified unfinished Tunnel identity is saved. Nothing was deleted.')
    name=stage.get('hostname','');tid=stage['tunnel_id'];zone=stage.get('zone','');account=stage.get('account','')
    if params.get('hostname','').strip().lower()!=name:
        raise ValueError('The confirmation hostname differs from the saved unfinished Tunnel.')
    token=valid_token(params.get('token'))
    validate_cloudflare(zone,token,name)
    cfg=load_config()
    if cfg.get('tunnel_id')==tid:
        raise ValueError('The unfinished identity is also saved as managed. Use Disable and Remove managed Tunnel instead.')
    # An incomplete Tunnel created before the origin route was published may
    # have no matching ingress yet; only a saved exact ID/name is eligible.
    items=[t for t in _tunnel_list(account,token,name) if t.get('id')==tid]
    if items:
        item=items[0]
        if item.get('config_src')!='cloudflare' or item.get('status') in ('healthy','degraded'):
            raise ValueError('This Tunnel is active or its identity differs. No resources were removed.')
        if stage.get('setup_step') not in (None,'created'):
            _tunnel_details_match(account,token,name,tid)
    record=_removable_tunnel_dns(account,zone,token,name,tid,stage.get('dns_id'))
    rows=[record] if record else []
    removal=read_json_optional(TUNNEL_REMOVE_PROGRESS)
    expected={'hostname':name,'tunnel_id':tid,'dns_id':stage.get('dns_id') or (rows[0]['id'] if rows else None),
              'zone':zone,'account':account,'kind':'unfinished'}
    if removal and any(removal.get(k)!=v for k,v in expected.items() if k!='dns_id'):
        raise ValueError('A different removal is unfinished. Resolve that removal first.')
    if not removal:write_json(TUNNEL_REMOVE_PROGRESS,expected,0o600)
    _delete_owned_tunnel(account,zone,token,name,tid,expected['dns_id'],TUNNEL_REMOVE_PROGRESS)
    # Local state is cleared only after independent Cloudflare read-back.
    if Path('/etc/systemd/system/uap-cloudflared-candidate.service').exists():
        run(['/usr/bin/systemctl','disable','--now','uap-cloudflared-candidate.service'],timeout=20)
    CANDIDATE_TOKEN.unlink(missing_ok=True)
    clear_tunnel_stage()
    TUNNEL_REMOVE_PROGRESS.unlink(missing_ok=True)
    status('tunnel_cleanup','ok','Cloudflare verified that this unfinished Tunnel and its matching DNS record are removed. Local progress was cleared.')


def remove_tunnel(params):
    active_config=load_config()
    cfg=active_config if active_config.get('tunnel_id') else (
        read_json_optional(TUNNEL_PROFILE) if active_config.get('mode')=='local' else {})
    if not cfg.get('tunnel_id') or not cfg.get('hostname') or not cfg.get('zone') or not cfg.get('account') or not cfg.get('token'):
        raise ValueError('No complete Moon Cheese Tunnel ownership record is available for removal.')
    if params.get('hostname','').strip().lower()!=cfg['hostname']:
        raise ValueError('The confirmation hostname does not match the managed Tunnel.')
    if cfg.get('mode')=='tunnel':
        raise ValueError('Disable the Tunnel first. Removal requires local-only mode to protect working remote access.')
    account=cfg['account'];token=cfg['token'];tid=cfg['tunnel_id'];name=cfg['hostname'];zone=cfg['zone']
    progress=read_json_optional(TUNNEL_REMOVE_PROGRESS)
    expected={'hostname':name,'tunnel_id':tid,'dns_id':cfg.get('dns_id'),'zone':zone,'account':account,'kind':'managed'}
    if progress and any(progress.get(k)!=v for k,v in expected.items() if k!='dns_id'):
        raise ValueError('A different removal is unfinished. Review the saved Cloudflare resources before continuing.')
    if not progress:
        details=_tunnel_details_match(account,token,name,tid)
        if details and details.get('status') in ('healthy','degraded'):
            raise ValueError('The Cloudflare Tunnel still has an active connector. Stop all replicas first.')
        _removable_tunnel_dns(account,zone,token,name,tid,cfg.get('dns_id'))
        write_json(TUNNEL_REMOVE_PROGRESS,expected,0o600)
    _delete_owned_tunnel(account,zone,token,name,tid,cfg.get('dns_id'),TUNNEL_REMOVE_PROGRESS)
    if Path('/etc/systemd/system/uap-cloudflared.service').exists():
        run(['/usr/bin/systemctl','disable','--now','uap-cloudflared.service'],timeout=20)
    (ROOT/'cloudflared.token').unlink(missing_ok=True)
    if active_config.get('tunnel_id')==tid:
        cleaned={k:v for k,v in active_config.items() if k not in
                 ('hostname','account','zone','token','dns_id','tunnel_id','previous_tunnel')}
        cleaned['mode']='local'
        save_config(cleaned)
    TUNNEL_PROFILE.unlink(missing_ok=True)
    publish_managed_domain(load_config())
    TUNNEL_REMOVE_PROGRESS.unlink(missing_ok=True)
    status('tunnel_remove','ok','Cloudflare confirmed removal of the exact managed Tunnel and DNS record. Local state cleared; unrelated resources untouched.')


def run(args, timeout=30):
    return subprocess.run(args,check=True,text=True,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,timeout=timeout)


def safe_provider_error(raw):
    """Return only bounded, well-known validation errors, never secrets/logs."""
    try:
        obj=json.loads(raw.decode('utf-8','replace')[:4096])
        error=obj.get('error',{})
        message=error.get('message','') if isinstance(error,dict) else ''
        if not message and isinstance(obj.get('message'),str):message=obj['message']
        if not message and isinstance(obj.get('errors'),list) and obj['errors']:
            first=obj['errors'][0]
            if isinstance(first,dict):message=first.get('message','')
        # Only simple human-scale validation text; don't expose certbot commands,
        # traceback text, DNS credentials or tokens from providers.
        if (isinstance(message,str) and len(message)<=160 and
            re.fullmatch(r"[A-Za-z0-9 .,()_/@:'-]+",message) and
            not any(word in message.lower() for word in
                    ('token','password','secret','credential','authorization','bearer','key='))):
            return message
    except (ValueError,AttributeError,TypeError):pass
    return ''


def http(url, method='GET', payload=None, token='',timeout=TIMEOUT):
    assert url.startswith((CF+'/',NPM+'/'))
    data=json.dumps(payload).encode() if payload is not None else None
    headers={'Accept':'application/json'}
    if data is not None:headers['Content-Type']='application/json'
    if token:headers['Authorization']='Bearer '+token
    req=urllib.request.Request(url,headers=headers,data=data,method=method)
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail=safe_provider_error(exc.read(4096))
        provider='Cloudflare' if url.startswith(CF) else 'local NPM'
        # The error code + API stage is essential for reproducing a real failure.
        hint=(' '+detail) if detail else ' Check local NPM logs or provider permissions.'
        raise ValueError(f'{provider} API HTTP {exc.code} ({method} {urllib.parse.urlsplit(url).path.split("/api")[-1]}).{hint}') from None
    except (urllib.error.URLError,TimeoutError):
        raise ValueError('The network provider could not be contacted. Check the connection and try again.') from None


def cloudflare(path,token,method='GET',body=None):
    result=http(CF+path,method,body,token)
    if not result.get('success'):
        raise ValueError('Cloudflare declined the request. Check your Zone ID and API token permissions.')
    return result.get('result')


def validate_cloudflare(zone, token, hostname):
    zone=valid_id(zone,'Zone ID');token=valid_token(token);hostname=valid_hostname(hostname)
    info=cloudflare('/zones/'+zone,token)
    zone_name=info.get('name','').lower()
    if not zone_name or (hostname != zone_name and not hostname.endswith('.'+zone_name)):
        raise ValueError('The selected hostname must be within the supplied Cloudflare zone.')
    return zone,token,hostname


def dns_records(zone,token,name):
    q=urllib.parse.urlencode({'name':name,'per_page':50})
    return cloudflare('/zones/'+zone+'/dns_records?'+q,token)


def ensure_dns(zone, token, name, record_type, content, proxied=True,
               managed_record_id=None, adopt_existing=False):
    """Manage one explicitly selected record, never a whole Cloudflare zone.

    Adoption requires an additional affirmative action from the administrator.
    The proxied flag of an existing A record is deliberately preserved.
    """
    existing=[r for r in dns_records(zone,token,name)
              if r.get('name','').lower()==name and r.get('type') in ('A','AAAA','CNAME')]
    if existing:
        if len(existing)!=1:
            raise ValueError('Multiple A/AAAA/CNAME records use this name. Review them in Cloudflare before proceeding.')
        record=existing[0]
        if record['type']!=record_type:
            raise ValueError('The hostname belongs to a different DNS record type. No record was changed.')
        if record.get('id')!=managed_record_id and not adopt_existing:
            # A perfectly matching record can be used without writing it; but
            # recording ownership requires explicit approval for later DDNS.
            raise ValueError('This hostname already exists in Cloudflare. Tick the explicit adoption checkbox to allow management of that record.')
        if record.get('content')!=content:
            cloudflare('/zones/'+zone+'/dns_records/'+record['id'],token,'PATCH',{'content':content})
        return record['id']
    record=cloudflare('/zones/'+zone+'/dns_records',token,'POST',
                      {'type':record_type,'name':name,'content':content,'proxied':proxied,'ttl':1})
    return record['id']

def public_ipv4():
    req=urllib.request.Request('https://api.ipify.org',headers={'User-Agent':'MoonCheeseDDNS/0.9.9.4.10'})
    with urllib.request.urlopen(req,timeout=12) as response:
        result=response.read(64).decode().strip()
    value=valid_ipv4(result,'public IP address')
    if not ipaddress.ip_address(value).is_global:
        raise ValueError('No usable public IPv4 detected (private address or CGNAT).')
    return value


def ddns():
    cfg=load_config()
    if cfg.get('mode')!='npm' or not all(cfg.get(x) for x in ('hostname','zone','token','dns_id')):
        status('ddns_check','inactive','DDNS is not configured. Complete the local NPM and Cloudflare setup first.')
        return 'DDNS inactive'
    current=public_ipv4()
    records=[r for r in dns_records(cfg['zone'],cfg['token'],cfg['hostname'])
             if r.get('type')=='A' and r.get('id')==cfg['dns_id']]
    if len(records)!=1:
        status('ddns_check','needs_setup','The previously managed DNS record has been removed or replaced. Run the authorised NPM + Cloudflare setup again to reattach it; no unrelated record was changed.',hostname=cfg['hostname'])
        return 'DDNS needs setup'
    previous=records[0].get('content')
    if previous!=current:
        cloudflare('/zones/'+cfg['zone']+'/dns_records/'+cfg['dns_id'],cfg['token'],
                   'PATCH',{'content':current})
    status('ddns_check','updated' if previous!=current else 'ok',
           'Public IPv4 changed; the detector DNS record was updated.' if previous!=current
           else 'Cloudflare DNS is already correct.',mode='npm',hostname=cfg['hostname'],
           last_ip=current,checked=int(time.time()))
    return 'Cloudflare DNS checked'

def npm_api(method,path,payload=None,token=''):
    return http(NPM+path,method,payload,token,timeout=CERTIFICATE_TIMEOUT if method=='POST' and path=='/nginx/certificates' else TIMEOUT)



def _exact_letsencrypt_certificate(cert, hostname):
    """Check NPM's certificate data without interpreting display names as ownership.

    NPM can normalise a requested nice_name to the bare hostname. A matching
    hostname alone is NOT authority to take over an existing certificate.
    """
    return (isinstance(cert,dict) and cert.get('provider')=='letsencrypt' and
            cert.get('domain_names')==[hostname] and
            isinstance(cert.get('id'),int) and cert['id']>0)


def _valid_certificate(cert):
    """Validate an NPM certificate's expiry, including NPM 2.16 SQLite dates.

    NPM 2.16 stores ``expires_on`` as ``YYYY-MM-DD HH:MM:SS`` in its UTC
    database. Its API may instead send a timezone-bearing ISO 8601 value.
    A missing offset in this *NPM-provided* field therefore denotes UTC, not
    the Raspberry Pi's local timezone. Never interpret arbitrary user input
    through this helper; hostname, provider, challenge and assignment checks
    remain separate and mandatory.
    """
    expiry=cert.get('expires_on') if isinstance(cert,dict) else None
    if not isinstance(expiry,str) or not expiry.strip():
        return False
    # Require the date and clock, not a date-only value or fuzzy input.
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?',expiry):
        return False
    try:
        when=datetime.fromisoformat(expiry.replace('Z','+00:00'))
        if when.tzinfo is None:
            when=when.replace(tzinfo=timezone.utc)
        return when.astimezone(timezone.utc)>datetime.now(timezone.utc)
    except (ValueError,OverflowError):
        return False


def _matching_cloudflare_certificate(cert, hostname):
    if not _exact_letsencrypt_certificate(cert,hostname) or not _valid_certificate(cert):
        return False
    meta=cert.get('meta')
    return (isinstance(meta,dict) and meta.get('dns_challenge') is True and
            meta.get('dns_provider')=='cloudflare' and
            cert.get('nice_name') in (hostname,'Moon Cheese '+hostname))


def _certificate_is_unused(cert_id, hosts, target_host_id=None):
    """No other proxy host may use a recovered certificate, even if disabled."""
    return not any(host.get('certificate_id')==cert_id and
                   host.get('id')!=target_host_id for host in hosts)


def matching_managed_certificate(certificates, hostname):
    """Legacy strict Moon Cheese naming (safe when the provider retains it)."""
    return next((c for c in certificates if
                 _exact_letsencrypt_certificate(c,hostname) and
                 c.get('nice_name')=='Moon Cheese '+hostname),None)


def recoverable_certificates(certificates, hostname, hosts, host_id):
    """Candidates for an explicitly authorised, exact-hostname orphan recovery.

    Never reuse another hostname, a non-Cloudflare certificate, an expired
    certificate, or a certificate assigned to some other NPM host. Nothing is
    deleted or modified by this discovery function.
    """
    return [c for c in certificates if
            _matching_cloudflare_certificate(c,hostname) and
            _certificate_is_unused(c['id'],hosts,host_id)]


def choose_recoverable_certificate(certificates, hostname, hosts, host_id, *,
                                   recorded_id=None, explicitly_authorised=False,
                                   previous_request=False):
    """Resolve only a uniquely matching orphan, with provenance or opt-in."""
    matches=recoverable_certificates(certificates,hostname,hosts,host_id)
    if recorded_id:
        matches=[c for c in matches if c['id']==recorded_id]
    if not (explicitly_authorised or recorded_id or previous_request):
        return None
    if len(matches)>1:
        raise ValueError('Multiple unused Let\'s Encrypt certificates match this hostname. Review NPM Certificates; no certificate was assigned.')
    return matches[0] if matches else None


def find_issued_certificate(api_token, hostname, wait_seconds=0):
    """Poll for a certificate from a request Moon Cheese itself just submitted.

    NPM can store the name as the hostname instead of the submitted nice_name.
    The caller must use this only after a *recorded* certificate request.
    """
    deadline=time.monotonic()+max(0,wait_seconds)
    while True:
        try:
            certificates=npm_api('GET','/nginx/certificates',token=api_token)
            found=matching_managed_certificate(certificates,hostname)
            if not found:
                # A successful ACME operation can produce a hostname-named
                # certificate; require Cloudflare DNS challenge metadata.
                eligible=[c for c in certificates if _matching_cloudflare_certificate(c,hostname)]
                if len(eligible)>1:
                    raise ValueError('More than one certificate matches this hostname; review NPM before retrying.')
                found=eligible[0] if eligible else None
            if found:return found['id']
        except (ValueError,KeyError,TypeError):
            if time.monotonic()>=deadline:raise
        if time.monotonic()>=deadline:return None
        time.sleep(min(5,max(0,deadline-time.monotonic())))


def request_or_recover_certificate(api_token, hostname, staged):
    """Wait for the existing issuance; do not create duplicates on retries."""
    issued=find_issued_certificate(api_token,hostname)
    if issued:return issued
    started=staged.get('certificate_requested_at')
    if isinstance(started,(int,float)) and time.time()-started<900:
        issued=find_issued_certificate(api_token,hostname,wait_seconds=CERTIFICATE_RECONCILE_SECONDS)
        if issued:return issued
        raise ValueError('The previous certificate request may still be completing in NPM. No second request was sent; wait a few minutes, then retry.')
    meta={'dns_challenge':True,'dns_provider':'cloudflare',
          'dns_provider_credentials':'dns_cloudflare_api_token = '+staged['token']+'\n',
          'propagation_seconds':120}
    staged.update({'setup_step':'certificate_request',
                   'certificate_requested_at':int(time.time())})
    save_config(staged)
    try:
        result=npm_api('POST','/nginx/certificates',
                 {'provider':'letsencrypt','nice_name':'Moon Cheese '+hostname,
                  'domain_names':[hostname],'meta':meta},api_token)
        issued=result.get('id') if isinstance(result,dict) else None
        if isinstance(issued,int) and issued>0:return issued
        raise ValueError('NPM returned no certificate ID. The host remains disabled.')
    except ValueError as exc:
        if not ('network provider could not be contacted' in str(exc).lower() or
                any(f'local NPM API HTTP {code}' in str(exc) for code in (502,503,504))):
            raise
        issued=find_issued_certificate(api_token,hostname,wait_seconds=CERTIFICATE_RECONCILE_SECONDS)
        if issued:return issued
        raise ValueError('NPM certificate request timed out, and no issued certificate was verified. The host remains disabled. Check NPM Certificates before retrying.') from None


def npm_token():
    # Only the isolated NPM deployed at /opt/uap-detector/npm may be managed.
    compose=Path('/opt/uap-detector/npm/compose.yaml')
    env=Path('/opt/uap-detector/npm/.env')
    if not compose.is_file() or not env.is_file():
        raise ValueError('No Moon Cheese-managed local NPM installation found. External NPM is not modified.')
    creds={}
    for line in env.read_text().splitlines():
        if '=' in line:
            key,value=line.split('=',1)
            if key in ('NPM_ADMIN_EMAIL','NPM_ADMIN_PASSWORD'):creds[key]=value
    if not all(creds.get(k) for k in ('NPM_ADMIN_EMAIL','NPM_ADMIN_PASSWORD')):
        raise ValueError('Local NPM credentials are unavailable; no proxy changes made.')
    result=npm_api('POST','/tokens',{'identity':creds['NPM_ADMIN_EMAIL'],'secret':creds['NPM_ADMIN_PASSWORD']})
    return result['token']


def sync_npm_contact(api_token, desired, configured, authorised):
    """Change only the locally bundled NPM administrator login, with opt-in.

    NPM 2.16 uses its account email for ACME; its certificate API accepts no
    separate letsencrypt_email. Never silently change an administrator login.
    """
    if desired == configured:
        return api_token
    if authorised != 'yes':
        raise ValueError("The entered Let's Encrypt email differs from the local NPM administrator email. Tick the explicit NPM contact-email authorisation, or use the current NPM email.")
    if not configured:
        raise ValueError('Local NPM administrator email cannot be verified. Set it in local NPM first.')
    env=Path('/opt/uap-detector/npm/.env')
    prior=env.read_text()
    lines=prior.splitlines()
    passwords=[line.split('=',1)[1] for line in lines if line.startswith('NPM_ADMIN_PASSWORD=')]
    if len(passwords)!=1:
        raise ValueError('The local NPM credentials file is incomplete; contact email was not changed.')
    current=npm_api('GET','/users/me',token=api_token)
    if not isinstance(current,dict) or current.get('email','').lower()!=configured:
        raise ValueError('NPM administrator contact does not match the local credentials file. Review the account in NPM before proceeding.')
    revised='\n'.join('NPM_ADMIN_EMAIL='+desired if line.startswith('NPM_ADMIN_EMAIL=') else line for line in lines)+'\n'
    # Validate the entire revised credentials file before modifying the login.
    if any('\r' in item for item in (desired,revised)):
        raise ValueError('Invalid NPM email formatting.')
    npm_api('PUT','/users/me',{'email':desired},api_token)
    try:
        write_text_atomic(env,revised,0o600)
        result=npm_api('POST','/tokens',{'identity':desired,'secret':passwords[0]})
        if not isinstance(result,dict) or not result.get('token'):
            raise ValueError('NPM did not accept the updated login email.')
        return result['token']
    except Exception:
        try:npm_api('PUT','/users/me',{'email':configured},api_token)
        except Exception:pass
        write_text_atomic(env,prior,0o600)
        raise ValueError('NPM contact-email update could not be verified and was restored where possible; check the local NPM account before retrying.') from None


def write_text_atomic(path, data, mode=0o600):
    fd,tmp=tempfile.mkstemp(prefix='.npm-env-',dir=path.parent)
    try:
        os.fchmod(fd,mode)
        with os.fdopen(fd,'w') as stream:
            stream.write(data)
            stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


@contextmanager
def network_lock():
    """Serialise network changes with the timer; never hold this during SSL issuance."""
    NETWORK_LOCK.parent.mkdir(parents=True,exist_ok=True)
    with open(NETWORK_LOCK,'a+') as handle:
        fcntl.flock(handle.fileno(),fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(handle.fileno(),fcntl.LOCK_UN)


def preview_domain_change(params):
    """Read-only preview; creates no DNS, certificate, NPM host or DDNS change."""
    old=load_config()
    if old.get('mode') not in ('npm','local') or old.get('setup_step')!='complete' or not old.get('npm_host_enabled'):
        raise ValueError('First complete a working managed NPM hostname before changing it.')
    name=valid_hostname(params.get('hostname'))
    if name==old.get('hostname'):
        raise ValueError('The replacement must be different from the current hostname.')
    zone,token,name=validate_cloudflare(params.get('zone'),params.get('token'),name)
    npm=npm_token()
    hosts=npm_api('GET','/nginx/proxy-hosts',token=npm)
    prior=next((h for h in hosts if h.get('id')==old.get('npm_host_id') and old.get('hostname') in h.get('domain_names',[])),None)
    if not prior or not prior.get('enabled'):
        raise ValueError('The current managed NPM proxy could not be verified; no switch was prepared.')
    new_hosts=[h for h in hosts if name in h.get('domain_names',[])]
    progress=read_json_optional(DOMAIN_PROGRESS)
    if new_hosts and not (len(new_hosts)==1 and
                          progress.get('hostname')==name and
                          new_hosts[0].get('id')==progress.get('npm_host_id')):
        raise ValueError('The replacement hostname already belongs to an NPM proxy. Review that host; it will not be overwritten.')
    records=[r for r in dns_records(zone,token,name)
             if r.get('name','').lower()==name and r.get('type') in ('A','AAAA','CNAME')]
    if len(records)>1 or (records and records[0].get('type')!='A'):
        raise ValueError('The replacement hostname has incompatible or multiple DNS records.')
    if records and params.get('adopt_dns')!='yes':
        raise ValueError('The replacement already has a Cloudflare A record. Tick explicit DNS adoption to review and manage it.')
    # No token in the preview artifact or any public response.
    ident=secrets.token_hex(16)
    write_json(DOMAIN_PREVIEW,{'id':ident,'name':name,'zone':zone,
                'old_hostname':old['hostname'],'old_host_id':old['npm_host_id'],
                'contact':(params.get('email') or '').strip().lower(),
                'created':time.time()},0o600)
    dns_message=('An existing A record will be adopted.' if records else 'A new A record will be created.')
    status('npm_preview','ready',f'Current: {old["hostname"]}. Replacement: {name}. {dns_message} '
           'NPM will obtain/reuse SSL and verify the enabled proxy settings before switching DDNS. '
           'Old DNS and certificate will be retained.',preview_id=ident,hostname=name)


def read_json_optional(path):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return {}


def change_managed_domain(params):
    old=load_config()
    preview=read_json_optional(DOMAIN_PREVIEW)
    name=valid_hostname(params.get('hostname'))
    if (params.get('ack')!='yes' or old.get('mode') not in ('npm','local') or old.get('setup_step')!='complete'
        or not old.get('npm_host_enabled') or not preview
        or not secrets.compare_digest(params.get('preview_id',''),str(preview.get('id','')))
        or preview.get('created',0)+900<time.time()
        or name!=preview.get('name') or params.get('zone')!=preview.get('zone')
        or preview.get('old_hostname')!=old.get('hostname')
        or preview.get('old_host_id')!=old.get('npm_host_id')
        or (params.get('email') or '').strip().lower()!=preview.get('contact')):
        raise ValueError('The reviewed domain-change authorisation has expired or changed. Check the replacement again.')
    if name==old['hostname']:
        raise ValueError('The domain is already configured.')
    try:
        setup_npm(params,migrating=True)
    except Exception:
        # The existing active proxy and DDNS target stay untouched. Any new
        # host enabled during the last stage is disabled if its identity is
        # already recorded by this attempt, so partial setup isn't exposed.
        partial=read_json_optional(DOMAIN_PROGRESS)
        if partial.get('hostname')==name and partial.get('npm_host_id'):
            try:
                token=npm_token()
                current=npm_api('GET','/nginx/proxy-hosts',token=token)
                candidate=next((h for h in current if h.get('id')==partial['npm_host_id']
                                and h.get('domain_names')==[name]),None)
                if candidate and candidate.get('enabled'):
                    safe_fields=('domain_names','forward_scheme','forward_host','forward_port',
                                 'access_list_id','certificate_id','ssl_forced','caching_enabled',
                                 'block_exploits','allow_websocket_upgrade','http2_support',
                                 'hsts_enabled','hsts_subdomains','advanced_config','locations','meta','enabled')
                    contents={k:v for k,v in candidate.items() if k in safe_fields}
                    contents['enabled']=False
                    npm_api('PUT',f'/nginx/proxy-hosts/{candidate["id"]}',contents,token)
            except Exception:
                status('npm_change','warning','Replacement failed and its proxy state could not be verified. Existing hostname remains configured.')
        raise
    DOMAIN_PREVIEW.unlink(missing_ok=True)


def apply_npm(params):
    """One authenticated NPM save operation; safety checks stay in the worker.

    Domain migration still uses the existing read-only preview and protected
    staged installer, but does not demand multiple user checkboxes.
    """
    old=load_config()
    if old.get('mode')=='local' and not old.get('npm_host_id'):
        saved=read_json_optional(NPM_PROFILE)
        if saved.get('npm_host_id') and saved.get('zone') and saved.get('hostname'):
            old=dict(saved,mode='local')
            save_config(old)
    params=dict(params)
    params.update({'ack':'yes','adopt_dns':'yes','replace_incomplete':'yes',
                   'reuse_certificate':'yes','sync_contact':'yes'})
    if not params.get('token'):
        # Secret is never returned to the browser. A saved token can be reused
        # only when the selected Cloudflare zone is the same.
        if old.get('zone')==params.get('zone') and old.get('token'):
            params['token']=old['token']
        else:
            raise ValueError('Enter the scoped Cloudflare token for this zone.')
    if not params.get('email'):
        params['email']=old.get('certificate_contact_email','')
    changing=(old.get('hostname')!=valid_hostname(params.get('hostname')) and
              old.get('setup_step')=='complete' and old.get('npm_host_enabled') and
              old.get('npm_host_id'))
    if changing:
        if old.get('mode') not in ('npm','local'):
            raise ValueError('Switch to local mode before changing from another remote-access method.')
        preview_domain_change(params)
        preview=read_json_optional(DOMAIN_PREVIEW)
        params['preview_id']=preview.get('id','')
        return change_managed_domain(params)
    return setup_npm(params)


def setup_npm(params, *, migrating=False):
    """Incremental, auditable setup with safe retry after a partial prior attempt.

    The proxy host stays DISABLED until HTTPS certificate provisioning succeeds.
    A failed certificate leaves the selected DNS record/DDNS configured and an
    *inactive* proxy host that can be resumed; never exposes unsecured HTTP.
    """
    name=valid_hostname(params.get('hostname'))
    zone,token,name=validate_cloudflare(params.get('zone'),params.get('token'),name)
    lan=local_ip()
    if not lan:raise ValueError('Cannot discover a working local IPv4 address. Check Ethernet or Wi-Fi.')
    previous=load_config()
    if previous.get('mode') not in (None,'local','npm'):
        raise ValueError('Another remote-access mode is configured. Switch to local-only first.')
    changing=(previous.get('mode')=='npm' and previous.get('hostname')!=name)
    if migrating and not (changing and previous.get('setup_step')=='complete' and previous.get('npm_host_enabled')):
        raise ValueError('The previous managed domain is no longer in a verified active state.')
    # No implicit takeover of a deployed (enabled) proxy or an issued certificate.
    if changing and not migrating and (previous.get('npm_host_enabled') or previous.get('setup_step')=='complete'):
        raise ValueError('A previous working NPM hostname is configured. Switch to local-only and review that host first.')
    # An old failed setup may have written a hostname and ACL ID before any
    # proxy host was actually created. Do not lock out a new hostname over it.
    if changing and not migrating and params.get('replace_incomplete')!='yes':
        raise ValueError('An unfinished Moon Cheese setup still names a different hostname. Tick the unfinished-setup authorisation to switch safely; existing working hosts are protected.')
    # Rebind without adopting the old host ID: leave any previous disabled proxy
    # untouched for manual inspection. The new hostname gets a separate host.
    staged=(read_json_optional(DOMAIN_PROGRESS) if migrating else
            previous.copy() if (not changing and previous.get('mode') in ('npm','local') and previous.get('npm_host_id')) else {})
    if migrating and staged.get('hostname')!=name:staged={}
    persist=(lambda data:write_json(DOMAIN_PROGRESS,data,0o600)) if migrating else save_config
    if changing and previous.get('npm_acl_id'):
        staged['npm_acl_id']=previous['npm_acl_id']
    was_enabled=bool(staged.get('npm_host_enabled') and staged.get('setup_step')=='complete')
    # The contact field is validated before staging anything.
    contact=(params.get('email') or '').strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",contact) or len(contact)>254:
        raise ValueError("Enter a valid Let's Encrypt contact email address.")
    # NPM 2.16 no longer accepts a per-certificate letsencrypt_email field;
    # it uses its configured administrator email. Verify correspondence BEFORE
    # editing DNS/NPM, rather than showing an email field that does nothing.
    admin_env=Path('/opt/uap-detector/npm/.env')
    configured_contact=''
    if admin_env.is_file():
        for line in admin_env.read_text().splitlines():
            if line.startswith('NPM_ADMIN_EMAIL='):
                configured_contact=line.split('=',1)[1].strip().strip('"').strip("'").lower()
    # Authenticate before any contact change. The update is separately opted-in.
    api_token=npm_token()
    api_token=sync_npm_contact(api_token,contact,configured_contact,params.get('sync_contact'))
    staged.update({'mode':'npm','hostname':name,'zone':zone,'token':token,'lan_ip':lan,
                   'certificate_contact_email':contact,
                   'npm_host_enabled':was_enabled,'setup_step':'preflight'})
    hosts=npm_api('GET','/nginx/proxy-hosts',token=api_token)
    existing=[h for h in hosts if name in h.get('domain_names',[])]
    if len(existing)>1:
        raise ValueError('Multiple NPM proxy hosts own this hostname. No host was changed.')
    if existing and existing[0].get('id')!=staged.get('npm_host_id'):
        candidate=existing[0]
        # Recovery may only reattach an exact, DISABLED Moon Cheese-style host,
        # explicitly authorised by the administrator. Never take an active one.
        safe_recovery=((params.get('replace_incomplete')=='yes' or migrating) and
                       not candidate.get('enabled') and
                       candidate.get('domain_names')==[name] and
                       candidate.get('forward_scheme')=='http' and
                       candidate.get('forward_port')==8000 and
                       candidate.get('certificate_id') in (0,None) and
                       candidate.get('access_list_id') in
                       [item.get('id') for item in npm_api('GET','/nginx/access-lists',token=api_token)
                        if item.get('name')=='Moon Cheese - Cloudflare ranges'])
        if not safe_recovery:
            raise ValueError('A pre-existing NPM proxy host owns that hostname. Moon Cheese will not change a host that is not an authorised, disabled previous setup.')
        staged['npm_host_id']=candidate['id']
    acls=npm_api('GET','/nginx/access-lists',token=api_token)
    wanted='Moon Cheese - Cloudflare ranges'
    old_acl=next((a for a in acls if a.get('name')==wanted),None)
    if old_acl and old_acl.get('id')!=staged.get('npm_acl_id'):
        if params.get('replace_incomplete')!='yes' and not migrating:
            raise ValueError('A previous Moon Cheese Access List exists but is not tracked. Tick the unfinished-setup authorisation to reuse it; unrelated lists remain untouched.')
        staged['npm_acl_id']=old_acl['id']
    existing_dns=[r for r in dns_records(zone,token,name) if r.get('name','').lower()==name and r.get('type') in ('A','AAAA','CNAME')]
    if len(existing_dns)>1 or (existing_dns and existing_dns[0].get('type')!='A'):
        raise ValueError('The selected hostname has multiple or incompatible DNS records. No changes were made.')
    adopted=bool(existing_dns and existing_dns[0].get('id')!=staged.get('dns_id'))
    if adopted and params.get('adopt_dns')!='yes':
        raise ValueError('Existing Cloudflare A record: '+str(existing_dns[0].get('content','unknown'))+
                         '. Approve adoption of this exact record. Nothing has been changed.')
    public=public_ipv4()
    # The administrator explicitly authorised this record. DDNS is independent
    # of certificate issuance, which can fail due to DNS propagation or Certbot.
    dns_id=ensure_dns(zone,token,name,'A',public,managed_record_id=staged.get('dns_id'),
                      adopt_existing=params.get('adopt_dns')=='yes')
    staged.update({'dns_id':dns_id,'setup_step':'dns'})
    persist(staged)
    if not migrating:
        status('ddns_check','updated','The selected Cloudflare A record is configured for DDNS.',
               hostname=name,last_ip=public,checked=int(time.time()))
        run(['/usr/bin/systemctl','enable','--now','uap-ddns.timer'])
    # Fetch official ranges and reuse only our own access-list record.
    with urllib.request.urlopen('https://api.cloudflare.com/client/v4/ips',timeout=TIMEOUT) as reply:
        ips=json.load(reply)['result']
    networks=ips['ipv4_cidrs']+ips['ipv6_cidrs']
    if not networks or len(networks)>128:
        raise ValueError('Official Cloudflare ranges unavailable; no new Access List created.')
    clients=[{'address':str(ipaddress.ip_network(item,strict=True)),'directive':'allow'} for item in networks]
    clients.append({'address':'all','directive':'deny'})
    acl={'name':wanted,'satisfy_any':False,'pass_auth':False,'items':[],'clients':clients}
    if old_acl:
        acl_id=old_acl['id']
        npm_api('PUT',f'/nginx/access-lists/{acl_id}',acl,api_token)
    else:
        acl_id=npm_api('POST','/nginx/access-lists',acl,api_token)['id']
    staged.update({'npm_acl_id':acl_id,'setup_step':'access_list'})
    persist(staged)
    # Create a DISABLED host first. The user can see it in NPM if certificate
    # provisioning fails, without publishing a non-TLS login endpoint.
    base_host={'domain_names':[name],'forward_scheme':'http','forward_host':lan,
               'forward_port':8000,'access_list_id':acl_id,'certificate_id':0,
               'ssl_forced':False,'caching_enabled':False,'block_exploits':True,
               'allow_websocket_upgrade':True,'http2_support':True,'hsts_enabled':False,
               'hsts_subdomains':False,'advanced_config':'','locations':[],'meta':{},
               'enabled':was_enabled}
    if was_enabled:
        base_host.update({'certificate_id':staged.get('npm_cert_id') or 0,'ssl_forced':True})
    if existing:
        host_id=existing[0]['id']
        if existing[0].get('enabled') and not was_enabled:
            raise ValueError('The existing managed host is enabled unexpectedly. Review it before changing it.')
        npm_api('PUT',f'/nginx/proxy-hosts/{host_id}',base_host,api_token)
    else:
        host_id=npm_api('POST','/nginx/proxy-hosts',base_host,api_token)['id']
    staged.update({'npm_host_id':host_id,'setup_step':'proxy_disabled'})
    persist(staged)
    certificates=npm_api('GET','/nginx/certificates',token=api_token)
    cert_id=staged.get('npm_cert_id')
    previous_issuance=bool(staged.get('certificate_requested_at'))
    # Avoid trusting a stale ID: recheck the exact hostname, issuer, DNS method,
    # expiry and that no unrelated proxy is using the certificate.
    recovered=choose_recoverable_certificate(
        certificates,name,hosts,host_id,
        recorded_id=cert_id,
        explicitly_authorised=params.get('reuse_certificate')=='yes',
        previous_request=previous_issuance)
    if cert_id and not recovered:
        raise ValueError('The previously recorded certificate cannot be verified for this hostname. No certificate was reassigned; review NPM Certificates.')
    # The provider may rename Moon Cheese's issued certificate to its hostname.
    # Reuse an eligible, unassigned exact-hostname certificate only with proof
    # of an earlier request or the administrator's separate consent.
    if not recovered:
        recovered=choose_recoverable_certificate(
            certificates,name,hosts,host_id,
            explicitly_authorised=params.get('reuse_certificate')=='yes',
            previous_request=previous_issuance)
    if not recovered:
        legacy=matching_managed_certificate(certificates,name)
        if legacy and _matching_cloudflare_certificate(legacy,name) and _certificate_is_unused(legacy['id'],hosts,host_id):
            recovered=legacy  # The original Moon Cheese-specific name proves the intended setup.
    if recovered:
        cert_id=recovered['id']
    else:
        if any(_exact_letsencrypt_certificate(c,name) for c in certificates):
            raise ValueError('A certificate for this hostname already exists but is not authorised or eligible for recovery. Tick the unused-certificate authorisation if it is yours; no unrelated certificate was changed.')
        cert_id=request_or_recover_certificate(api_token,name,staged)
    # Re-read the NPM certificate list to verify the recorded ID and that no
    # unrelated NPM host has claimed it while the request was in progress.
    certificates=npm_api('GET','/nginx/certificates',token=api_token)
    verified_cert=choose_recoverable_certificate(
        certificates,name,hosts,host_id,recorded_id=cert_id)
    if not verified_cert:
        raise ValueError('NPM has not verified an eligible issued certificate for this hostname; the proxy remains disabled.')
    staged.update({'npm_cert_id':cert_id,'setup_step':'certificate_ready'})
    persist(staged)
    base_host.update({'certificate_id':cert_id,'ssl_forced':True,'enabled':True})
    npm_api('PUT',f'/nginx/proxy-hosts/{host_id}',base_host,api_token)
    # NPM must acknowledge that TLS/force-SSL/enablement were applied.
    updated=npm_api('GET','/nginx/proxy-hosts',token=api_token)
    verified=next((h for h in updated if h.get('id')==host_id),None)
    if not verified or not (verified.get('enabled') and verified.get('ssl_forced') and
                            verified.get('certificate_id')==cert_id and
                            verified.get('access_list_id')==acl_id):
        raise ValueError('NPM did not verify the enabled HTTPS proxy; check the local NPM dashboard. No success was recorded.')
    staged.update({'npm_host_enabled':True,'setup_step':'complete'})
    if migrating:
        staged['previous_managed']={'hostname':previous['hostname'],
                                   'npm_host_id':previous.get('npm_host_id'),
                                   'dns_id':previous.get('dns_id'),
                                   'npm_cert_id':previous.get('npm_cert_id')}
        save_config(staged)  # switch DDNS target atomically only after verified HTTPS
        DOMAIN_PROGRESS.unlink(missing_ok=True)
        status('ddns_check','updated','Managed DDNS target switched to the replacement hostname.',
               hostname=name,last_ip=public,checked=int(time.time()))
    else:
        persist(staged)

    status('npm_change' if migrating else 'npm','ok',
           'Replacement NPM HTTPS settings verified and managed DDNS target switched; previous DNS and certificate preserved. Check external HTTPS separately.' if migrating else
           'SSL certificate assigned and NPM proxy enabled with Force SSL and the Cloudflare Access List. Check external HTTPS.',
           mode='npm',hostname=name,last_ip=public)


def retire_previous_proxy(params):
    """Explicit second operation, after the admin verifies new public HTTPS."""
    if params.get('ack')!='yes':
        raise ValueError('Explicit confirmation is required to disable the earlier proxy.')
    cfg=load_config()
    previous=cfg.get('previous_managed')
    if cfg.get('mode')!='npm' or cfg.get('setup_step')!='complete' or not cfg.get('npm_host_enabled') or not isinstance(previous,dict):
        raise ValueError('No previously managed proxy is available to retire.')
    current=cfg.get('npm_host_id');old_id=previous.get('npm_host_id')
    if not old_id or old_id==current:
        raise ValueError('The previous host cannot be identified safely.')
    token=npm_token()
    hosts=npm_api('GET','/nginx/proxy-hosts',token=token)
    new=next((h for h in hosts if h.get('id')==current and cfg['hostname'] in h.get('domain_names',[])),None)
    old=next((h for h in hosts if h.get('id')==old_id and previous.get('hostname') in h.get('domain_names',[])),None)
    if not new or not new.get('enabled') or not new.get('ssl_forced') or not new.get('certificate_id'):
        raise ValueError('Replacement proxy HTTPS configuration is not currently verified. No existing host was changed.')
    if not old:
        raise ValueError('The previously managed host has changed or disappeared. Review NPM; no action taken.')
    if old.get('enabled'):
        fields=('domain_names','forward_scheme','forward_host','forward_port','access_list_id',
                'certificate_id','ssl_forced','caching_enabled','block_exploits',
                'allow_websocket_upgrade','http2_support','hsts_enabled',
                'hsts_subdomains','advanced_config','locations','meta','enabled')
        payload={k:v for k,v in old.items() if k in fields}
        payload['enabled']=False
        npm_api('PUT',f'/nginx/proxy-hosts/{old_id}',payload,token)
        verified=npm_api('GET','/nginx/proxy-hosts',token=token)
        confirmed=next((h for h in verified if h.get('id')==old_id),None)
        if not confirmed or confirmed.get('enabled'):
            raise ValueError('NPM did not confirm that the previous proxy was disabled.')
    # Persist the prior hostname for clarity even after disablement.
    status('npm_retire_old','ok','Previous Moon Cheese proxy disabled. Its DNS record and SSL certificate were retained.',hostname=previous['hostname'])


def install_cloudflared():
    """Install official Cloudflare Debian release using the tested curl route.

    Python urllib's default User-Agent received 403 from pkg.cloudflare.com
    on the ARM64 test Pi. This uses the GitHub release Debian asset proven on
    that hardware; it never executes a downloaded shell script.
    """
    if shutil.which('cloudflared'):
        return
    if not shutil.which('curl'):
        raise ValueError('Connector installation: curl is missing. Install curl using the system package manager and retry.')
    arch=run(['/usr/bin/dpkg','--print-architecture']).stdout.strip()
    packages={'arm64':'cloudflared-linux-arm64.deb',
              'armhf':'cloudflared-linux-arm.deb',
              'amd64':'cloudflared-linux-amd64.deb'}
    package=packages.get(arch)
    if not package:
        raise ValueError('Connector installation: unsupported Debian CPU architecture '+re.sub(r'[^a-z0-9_-]','',arch)[:32]+'.')
    url='https://github.com/cloudflare/cloudflared/releases/latest/download/'+package
    with tempfile.TemporaryDirectory(prefix='moon-cheese-cloudflared-') as directory:
        destination=Path(directory)/package
        try:
            run(['/usr/bin/curl','--fail','--location','--silent','--show-error',
                 '--connect-timeout','20','--max-time','150','--output',str(destination),url],timeout=160)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError('Connector installation: official Cloudflare Debian package download failed. Check internet access to GitHub releases.') from exc
        if not (1000000 < destination.stat().st_size < 100000000):
            raise ValueError('Connector installation: downloaded Debian package has an unexpected size.')
        try:
            package_name=run(['/usr/bin/dpkg-deb','--field',str(destination),'Package']).stdout.strip()
            package_arch=run(['/usr/bin/dpkg-deb','--field',str(destination),'Architecture']).stdout.strip()
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
            raise ValueError('Connector installation: downloaded file is not a valid Debian package.') from exc
        if package_name!='cloudflared' or package_arch not in (arch,'all'):
            raise ValueError('Connector installation: package name or CPU architecture does not match this device.')
        try:
            run(['/usr/bin/dpkg','-i',str(destination)],timeout=180)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
            raise ValueError('Connector installation: Debian package installation failed. Check the system package manager.') from exc
    if not shutil.which('cloudflared'):
        raise ValueError('Connector installation: the package installed but the cloudflared command is unavailable.')
    try:
        run([shutil.which('cloudflared'),'--version'],timeout=15)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        raise ValueError('Connector installation: cloudflared failed its version check.') from exc


def _retire_superseded_tunnel(config):
    """Retire only the *saved* previous managed route after new health passes.

    Success of the new Tunnel is not rolled back if Cloudflare rejects a safe
    old-resource deletion. Instead keep the exact previous identity and surface
    a warning; a future setup retry may finish that cleanup.
    """
    prior=config.get('previous_tunnel')
    if not isinstance(prior,dict) or not prior.get('tunnel_id'):
        return ''
    if (not config.get('tunnel_id') or prior.get('tunnel_id')==config['tunnel_id'] or
        prior.get('hostname')==config.get('hostname')):
        return 'Previous Tunnel cleanup pending: saved identity overlaps the active Tunnel; no deletion attempted.'
    if prior.get('account')!=config.get('account') or prior.get('zone')!=config.get('zone'):
        return 'Previous Tunnel cleanup pending: the old account or DNS zone differs; no deletion attempted.'
    # Protect against deleting an active replica. Only the exact prior Tunnel
    # and its exact recorded DNS record are eligible for removal.
    try:
        # Cloudflare may take a few seconds to see that our old service was
        # replaced. Do not delete a connector while the provider says healthy.
        for attempt in range(10):
            try:
                item=_tunnel_details_match(prior['account'],config['token'],prior['hostname'],prior['tunnel_id'])
                old_active=item.get('status') in ('healthy','degraded')
            except ValueError as exc:
                if 'API HTTP 404' not in str(exc):raise
                old_active=False  # A deleted prior Tunnel may still have stale DNS.
            if not old_active:break
            if attempt<9:time.sleep(4)
        if old_active:
            return 'Previous Tunnel cleanup pending: its connector still appears active in Cloudflare.'
        cleanup=read_json_optional(TUNNEL_REPLACE_CLEANUP)
        if not (cleanup and cleanup.get('dns_removed')):
            _exact_tunnel_dns(prior['zone'],config['token'],prior['hostname'],prior['tunnel_id'],prior.get('dns_id'))
        expected={'hostname':prior['hostname'],'tunnel_id':prior['tunnel_id'],
                  'dns_id':prior.get('dns_id'),'zone':prior['zone'],
                  'account':prior['account'],'kind':'superseded'}
        if cleanup and any(cleanup.get(k)!=v for k,v in expected.items() if k!='dns_id'):
            return 'Previous Tunnel cleanup pending: another unfinished removal must be reviewed.'
        if not cleanup:write_json(TUNNEL_REPLACE_CLEANUP,expected,0o600)
        _delete_owned_tunnel(prior['account'],prior['zone'],config['token'],prior['hostname'],
                             prior['tunnel_id'],prior.get('dns_id'),TUNNEL_REPLACE_CLEANUP)
    except (ValueError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        # No raw exception detail: the provider may expose account identifiers.
        return 'Previous Tunnel cleanup pending: Cloudflare could not verify safe removal. The active connection remains in place.'
    TUNNEL_REPLACE_CLEANUP.unlink(missing_ok=True)
    updated=load_config()
    if updated.get('tunnel_id')==config['tunnel_id'] and updated.get('hostname')==config['hostname']:
        updated.pop('previous_tunnel',None)
        save_config(updated)
    return 'Previous Moon Cheese Tunnel and DNS record removed and verified.'

def connector_service(*args):
    """Report the failed connector unit operation, not an opaque HTTPError.

    We do not relay raw process output: cloudflared and systemd may include
    environment information that must not reach the administrator browser.
    """
    command=['/usr/bin/systemctl',*args]
    try:
        return run(command,timeout=45)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        operation=' '.join(str(arg) for arg in args if not str(arg).startswith('--'))[:120]
        raise ValueError('Cloudflare connector service operation failed: '+operation+'. Check System Health and retry.') from exc


def valid_connector_token(value):
    """Cloudflare remotely managed tunnel tokens may contain Base64 padding.

    Treat the connector token only as an opaque secret. Permit the known
    Base64/Base64URL alphabet and dot-separated formats; reject whitespace,
    shell delimiters and any token large enough to exhaust the worker.
    """
    return (isinstance(value,str) and 24<=len(value)<=8192 and
            re.fullmatch(r'[A-Za-z0-9_./+\-=]+',value) is not None)


def tunnel_name(hostname):
    return 'moon-cheese-'+hostname.replace('.','-')[:38]


def tunnel_ingress_matches(configuration, hostname):
    config=configuration.get('config') if isinstance(configuration,dict) else None
    rules=config.get('ingress') if isinstance(config,dict) else None
    return (isinstance(rules,list) and len(rules)==2 and
            rules[0].get('hostname')==hostname and
            rules[0].get('service')=='http://127.0.0.1:8000' and
            rules[1].get('service')=='http_status:404')


def recover_legacy_tunnel(account, zone, token, name):
    """Adopt only a verified, *inactive*, previously built Moon Cheese route.

    The matching name alone never establishes ownership. A legacy installation
    may have created a remotely configured tunnel and CNAME without recording
    them because token retrieval failed. Require administrator consent plus
    proof of its exact ingress and DNS destination before reusing its identity.
    """
    prefix='/accounts/'+account+'/cfd_tunnel'
    query=urllib.parse.urlencode({'name':tunnel_name(name),'is_deleted':'false','per_page':50})
    candidates=cloudflare(prefix+'?'+query,token)
    candidates=[t for t in candidates if t.get('name')==tunnel_name(name) and
                t.get('config_src')=='cloudflare' and t.get('status')=='inactive' and
                t.get('account_tag') in (None,account)]
    if len(candidates)!=1:
        raise ValueError('Cannot identify one inactive Moon Cheese tunnel for safe recovery. Review your Cloudflare Tunnels before retrying.')
    tid=candidates[0].get('id','')
    if not re.fullmatch(r'[a-fA-F0-9-]{36}',tid):
        raise ValueError('The inactive tunnel did not return a valid ID.')
    details=cloudflare(prefix+'/'+tid+'/configurations',token)
    if not tunnel_ingress_matches(details,name):
        raise ValueError('The existing tunnel route does not match this detector; no resources were changed.')
    dns=[d for d in dns_records(zone,token,name) if d.get('name','').lower()==name and
         d.get('type') in ('A','AAAA','CNAME')]
    if len(dns)!=1 or dns[0].get('type')!='CNAME' or not _tunnel_cname_matches(dns[0].get('content',''),tid):
        raise ValueError('The tunnel DNS record does not match this detector; no resources were changed.')
    return {'tunnel_id':tid,'dns_id':dns[0]['id']}


def _tunnel_id_from_cname(content):
    """Only an actual Cloudflare Tunnel CNAME; not arbitrary domain records."""
    if not isinstance(content,str):return ''
    match=re.fullmatch(r'([0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})\.cfargotunnel\.com\.?',content.strip(),re.I)
    return match.group(1).lower() if match else ''


def _matching_named_tunnels(account,token,hostname):
    """Get inactive/active exact Moon Cheese-named tunnels in the given account."""
    items=_tunnel_list(account,token,hostname)
    return [item for item in items if item.get('config_src')=='cloudflare' and
            item.get('account_tag') in (None,account)]


def _safe_previous_tunnel(account,token,hostname,tunnel_id):
    """Only a Cloudflare resource bearing our exact name and matching origin.

    Absence means an orphaned CNAME; we don't assert ownership based on name
    alone when the remote tunnel still exists.
    """
    if not tunnel_id:return 'none'
    try:
        item=cloudflare('/accounts/'+account+'/cfd_tunnel/'+tunnel_id,token)
    except ValueError as exc:
        if 'API HTTP 404' in str(exc):return 'missing'
        raise
    if item.get('id') not in (None,tunnel_id) or item.get('name')!=tunnel_name(hostname) or item.get('config_src')!='cloudflare':
        return 'unrelated'
    if item.get('status') in ('healthy','degraded'):return 'active'
    try:
        configuration=cloudflare('/accounts/'+account+'/cfd_tunnel/'+tunnel_id+'/configurations',token)
    except ValueError as exc:
        if 'API HTTP 404' in str(exc):return 'missing'
        raise
    if not tunnel_ingress_matches(configuration,hostname):return 'unrelated'
    return 'owned_inactive'


def apply_tunnel(params):
    """One administrator action: setup, resume or replace exact owned resources."""
    old=load_config()
    if old.get('mode')=='local' and not old.get('tunnel_id'):
        saved=read_json_optional(TUNNEL_PROFILE)
        if saved.get('tunnel_id') and saved.get('zone') and saved.get('hostname'):
            old=dict(saved,mode='local')
            save_config(old)
    params=dict(params)
    params['recover_tunnel']='yes'
    params['replace_tunnel']='yes'
    if not params.get('token'):
        if (old.get('mode') in ('tunnel','local') and old.get('account')==params.get('account') and
            old.get('zone')==params.get('zone') and old.get('tunnel_id') and old.get('token')):
            params['token']=old['token']
        else:
            raise ValueError('Enter a Cloudflare API token with Tunnel Edit and DNS Edit permissions.')
    return setup_tunnel(params)


def setup_tunnel(params):
    name=valid_hostname(params.get('hostname'))
    zone,token,name=validate_cloudflare(params.get('zone'),params.get('token'),name)
    account=valid_id(params.get('account'),'Account ID')
    old=load_config()
    if old.get('mode') not in (None,'local','tunnel'):
        raise ValueError('A different remote access mode is active. Switch to local-only first.')
    changing=old.get('mode')=='tunnel' and old.get('hostname')!=name
    if changing and params.get('replace_tunnel')!='yes':
        raise ValueError('Another Tunnel hostname is active. Authorise Change managed Tunnel to prepare a replacement.')
    if any(Path(x).exists() for x in ('/etc/systemd/system/cloudflared.service',
                                       '/usr/lib/systemd/system/cloudflared.service',
                                       '/lib/systemd/system/cloudflared.service')):
        raise ValueError('An unrelated cloudflared service exists and will not be modified.')
    stage=read_json_optional(TUNNEL_PROGRESS)
    # Starting another hostname must not be blocked by an old failed setup.
    # Preserve the old Cloudflare resources for an explicit later cleanup,
    # while the requested new hostname is configured independently.
    if stage and any(stage.get(k)!=v for k,v in (('hostname',name),('zone',zone),('account',account))):
        if old.get('mode')=='tunnel' and old.get('tunnel_id')==stage.get('tunnel_id'):
            raise ValueError('The unfinished setup is the active Tunnel; keep the working connection.')
        stage={}
    stage=stage or {'hostname':name,'zone':zone,'account':account}
    prefix='/accounts/'+account+'/cfd_tunnel'
    current_records=[d for d in dns_records(zone,token,name)
                     if d.get('name','').lower()==name and d.get('type') in ('A','AAAA','CNAME')]
    if len(current_records)>1 or (current_records and current_records[0].get('type')!='CNAME'):
        raise ValueError('This hostname has another DNS service (A/AAAA or multiple records). Choose an unused Tunnel hostname; no unrelated service was changed.')
    prior_dns=current_records[0] if current_records else None
    previous_dns_tunnel=_tunnel_id_from_cname(prior_dns.get('content','')) if prior_dns else ''
    if prior_dns and not previous_dns_tunnel:
        raise ValueError('This hostname already points to a different service, not a Cloudflare Tunnel.')
    # Verify ownership of an existing CNAME BEFORE creating a Tunnel. A
    # deleted remote ID is an orphan that an authenticated administrator may
    # repoint, but never overwrite an active/unrelated Tunnel destination.
    previous_state=_safe_previous_tunnel(account,token,name,previous_dns_tunnel) if previous_dns_tunnel else 'none'
    if previous_state in ('active','unrelated'):
        if not (old.get('mode')=='tunnel' and old.get('tunnel_id')==previous_dns_tunnel and
                old.get('hostname')==name):
            raise ValueError('This hostname is in use by another active or unrelated Cloudflare Tunnel. It was not changed.')
    same_saved=(old.get('hostname')==name and old.get('tunnel_id') and
                old.get('account')==account and old.get('zone')==zone)
    tunnel_id=stage.get('tunnel_id') or (old.get('tunnel_id') if same_saved else None)
    matches=_matching_named_tunnels(account,token,name)
    if tunnel_id:
        # If the saved ID has been removed at Cloudflare, use a verified
        # same-name inactive candidate or create the new Tunnel below.
        try:
            item=cloudflare(prefix+'/'+tunnel_id,token)
            if item.get('name')!=tunnel_name(name) or item.get('config_src')!='cloudflare':
                raise ValueError('A saved Tunnel ID now identifies an unrelated Cloudflare resource.')
        except ValueError as exc:
            if 'API HTTP 404' in str(exc):tunnel_id=None
            else:raise
    if not tunnel_id and previous_dns_tunnel and previous_state=='owned_inactive':
        tunnel_id=previous_dns_tunnel
    if not tunnel_id:
        candidates=[t for t in matches if t.get('status') not in ('healthy','degraded')]
        if len(candidates)>1:
            raise ValueError('Multiple inactive Moon Cheese Tunnels use this hostname. Review the duplicate Tunnels in Cloudflare.')
        if candidates:
            tunnel_id=candidates[0]['id']
        elif matches:
            raise ValueError('An existing active Tunnel uses this hostname. No connection was replaced.')
        else:
            value=cloudflare(prefix,token,'POST',{'name':tunnel_name(name),'config_src':'cloudflare'})
            tunnel_id=value['id']
    stage.update({'tunnel_id':tunnel_id,'setup_step':'created'})
    persist_tunnel_stage(stage)
    config={'config':{'ingress':[{'hostname':name,'service':'http://127.0.0.1:8000','originRequest':{}},
                                 {'service':'http_status:404'}]}}
    cloudflare(prefix+'/'+tunnel_id+'/configurations',token,'PUT',config)
    stage['setup_step']='route';persist_tunnel_stage(stage)
    # The selected hostname is the administrator's explicit configuration.
    # An orphaned Tunnel CNAME or a verified inactive Moon Cheese predecessor
    # can be pointed at the prepared Tunnel. No A/AAAA/other records change.
    existing=[d for d in dns_records(zone,token,name) if d.get('name','').lower()==name and
              d.get('type') in ('A','AAAA','CNAME')]
    if len(existing)>1 or (existing and existing[0].get('type')!='CNAME'):
        raise ValueError('The hostname was taken by another DNS service during setup; no record was changed.')
    if existing and not _tunnel_cname_matches(existing[0].get('content',''),tunnel_id):
        previous=_tunnel_id_from_cname(existing[0].get('content',''))
        if not previous or _safe_previous_tunnel(account,token,name,previous) not in ('missing','owned_inactive'):
            raise ValueError('An unrelated active Tunnel owns this DNS record; Moon Cheese has not overwritten it.')
    dns_id=ensure_dns(zone,token,name,'CNAME',tunnel_id+'.cfargotunnel.com',
                      managed_record_id=existing[0].get('id') if existing else None,
                      adopt_existing=True)
    stage.update({'dns_id':dns_id,'setup_step':'dns_ready'})
    persist_tunnel_stage(stage)
    tunnel_token=cloudflare(prefix+'/'+tunnel_id+'/token',token)
    if not valid_connector_token(tunnel_token):
        raise ValueError('Cloudflare did not return a usable Tunnel token. The saved Tunnel and DNS route remain available for recovery.')
    install_cloudflared()
    stage['setup_step']='connector_installed';persist_tunnel_stage(stage)
    unit=Path('/etc/systemd/system/uap-cloudflared.service')
    if not unit.exists():raise ValueError('Missing Moon Cheese Cloudflare connector service; rerun the installer.')
    connector_service('daemon-reload')
    tokenfile=ROOT/'cloudflared.token'
    # For a live hostname switch, run the candidate connector alongside the
    # existing working one until Cloudflare verifies the replacement.
    if changing:
        candidate_unit=Path('/etc/systemd/system/uap-cloudflared-candidate.service')
        if not candidate_unit.exists():raise ValueError('Missing staged Tunnel connector service; rerun the complete installer.')
        _token_file(CANDIDATE_TOKEN,tunnel_token)
        connector_service('enable','--now','uap-cloudflared-candidate.service')
        stage['setup_step']='candidate_started';persist_tunnel_stage(stage)
        if not _tunnel_connected(account,token,tunnel_id):
            connector_service('disable','--now','uap-cloudflared-candidate.service')
            raise ValueError('Replacement Tunnel connector was not verified. The previous working connector remains active.')
        prior_token=tokenfile.read_text() if tokenfile.exists() else ''
        if not prior_token:raise ValueError('The active connector token is unavailable; refusing to replace the working Tunnel.')
        try:
            _token_file(tokenfile,tunnel_token)
            connector_service('restart','uap-cloudflared.service')
            if not _tunnel_connected(account,token,tunnel_id,attempts=5):
                raise ValueError('Replacement connector did not stay healthy after activation.')
        except Exception:
            if prior_token:
                _token_file(tokenfile,prior_token.rstrip('\n'))
                connector_service('restart','uap-cloudflared.service')
            raise
        finally:
            connector_service('disable','--now','uap-cloudflared-candidate.service')
            CANDIDATE_TOKEN.unlink(missing_ok=True)
    else:
        _token_file(tokenfile,tunnel_token)
        connector_service('enable','uap-cloudflared.service')
        connector_service('restart','uap-cloudflared.service')
        stage['setup_step']='connector_started';persist_tunnel_stage(stage)
        if not _tunnel_connected(account,token,tunnel_id):
            raise ValueError('Tunnel connector has not become active. Details are saved for recovery; check the local cloudflared service and retry.')
    previous={'hostname':old.get('hostname'),'tunnel_id':old.get('tunnel_id'),
              'dns_id':old.get('dns_id'),'zone':old.get('zone'),'account':old.get('account')}
    config={'mode':'tunnel','hostname':name,'zone':zone,'token':token,'account':account,
            'dns_id':dns_id,'tunnel_id':tunnel_id,'setup_step':'complete'}
    if changing or (old.get('tunnel_id') and old.get('hostname')!=name):config['previous_tunnel']=previous
    elif old.get('previous_tunnel'):config['previous_tunnel']=old['previous_tunnel']
    save_config(config)
    clear_tunnel_stage()
    run(['/usr/bin/systemctl','disable','--now','uap-ddns.timer'])
    old_cleanup=_retire_superseded_tunnel(config) if config.get('previous_tunnel') else ''
    message='Tunnel connector verified active and DNS route configured. Check public HTTPS accessibility separately.'
    if old_cleanup:message+=' '+old_cleanup
    status('tunnel','ok',message,mode='tunnel',hostname=name)

def network_devices():
    """Only physical NetworkManager Ethernet/Wi-Fi; never Docker virtual NICs."""
    result=run(['/usr/bin/nmcli','-t','-f','DEVICE,TYPE,STATE,CONNECTION','device','status'])
    entries=[]
    for line in result.stdout.splitlines():
        parts=line.split(':',3)
        if len(parts)==4 and parts[1] in ('ethernet','wifi'):
            device,kind,state,connection=parts
            if not re.fullmatch(r'[a-zA-Z0-9_.:-]{1,32}',device):continue
            entries.append({'device':device,'type':kind,'state':state,
                            'connection':connection if state=='connected' and connection!='--' else ''})
    return entries


def device_address(device):
    output=run(['/usr/bin/nmcli','-g','IP4.ADDRESS','device','show',device]).stdout
    addresses=[]
    for line in output.splitlines():
        try:addresses.append(str(ipaddress.ip_interface(line.strip()).ip))
        except ValueError:pass
    return addresses


def selected_connection(params):
    interface=params.get('interface','').strip()
    choices=[d for d in network_devices() if d['connection'] and d['state']=='connected']
    if not interface and len(choices)==1:interface=choices[0]['device']
    found=next((d for d in choices if d['device']==interface),None)
    if not found:raise ValueError('Choose an active Ethernet or Wi-Fi connection. No changes made.')
    return found['device'],found['connection']


def ipv4_properties(conn):
    return [run(['/usr/bin/nmcli','-g',key,'connection','show',conn]).stdout.strip()
            for key in ('ipv4.method','ipv4.addresses','ipv4.gateway','ipv4.dns')]


def apply_connection(device,conn,expect=None):
    """Reapply may not support switching DHCP/manual: activate explicitly then VERIFY."""
    try:
        run(['/usr/bin/nmcli','device','reapply',device],timeout=25)
    except subprocess.CalledProcessError:
        pass
    current=ipv4_properties(conn)[0]
    ips=device_address(device)
    if expect=='auto' and (current!='auto' or not ips):
        run(['/usr/bin/nmcli','--wait','40','connection','up','id',conn,'ifname',device],timeout=50)
    elif expect=='manual' and not ips:
        run(['/usr/bin/nmcli','--wait','40','connection','up','id',conn,'ifname',device],timeout=50)
    return device_address(device)


def rollback():
    if not PENDING.exists():return
    item=json.loads(PENDING.read_text())
    prior=item['previous'];conn=item['connection'];device=item['device']
    values=['ipv4.method',prior[0] or 'auto','ipv4.addresses',prior[1],
            'ipv4.gateway',prior[2],'ipv4.dns',prior[3]]
    try:
        run(['/usr/bin/nmcli','connection','modify','id',conn,*values],timeout=20)
        apply_connection(device,conn,prior[0])
        current=device_address(device)
        observed=ipv4_properties(conn)
        expected=item.get('old_ip')
        # Returning to DHCP may legitimately obtain a different lease.
        if observed!=prior or (not current or (prior[0]=='manual' and expected not in current)):
            run(['/usr/bin/nmcli','--wait','40','connection','up','id',conn,'ifname',device],timeout=50)
            current=device_address(device)
            observed=ipv4_properties(conn)
        if observed!=prior or not current or (prior[0]=='manual' and expected not in current):
            raise ValueError('The previous network configuration could not be verified on the selected interface.')
        status('ip_change','restored','Previous IP settings were automatically restored after the confirmation deadline.',
               new_ip=current[0],mode=item.get('mode',''))
        status('ip_revert','ok','Previous network settings restored and verified.',new_ip=current[0])
        PENDING.unlink(missing_ok=True)
        PUBLIC_PENDING.unlink(missing_ok=True)
    except Exception:
        # Keep the pending file so the independent systemd timer can retry.
        status('ip_change','recovery_error','Automatic restoration could not be verified; the recovery timer will retry. Use local access.')
        status('ip_revert','error','Restoration could not be verified. Inspect NetworkManager locally.')
        raise


def read_status_state(action):
    try:return json.loads((RUN/'status'/(action+'.json')).read_text()).get('state')
    except (OSError,ValueError):return ''


def recover_expired():
    if not PENDING.exists():return
    try:
        item=json.loads(PENDING.read_text())
        if item.get('expires',0)<=time.time():rollback()
    except (OSError,ValueError) as exc:
        status('ip_revert','error','Recovery failed; pending change retained for inspection.')
        print('Network recovery requires attention:',type(exc).__name__,file=sys.stderr)


def change_ip(params):
    if PENDING.exists():
        existing=json.loads(PENDING.read_text())
        if existing.get('expires',0)>time.time():
            raise ValueError('Another network change is awaiting confirmation.')
        recover_expired()
        if PENDING.exists():raise ValueError('Earlier rollback requires local attention; no new change was attempted.')
    mode=params.get('mode')
    if mode not in ('dhcp','static'):raise ValueError('Choose DHCP or static IPv4.')
    device,conn=selected_connection(params)
    addresses=device_address(device)
    old_ip=addresses[0] if addresses else ''
    previous=ipv4_properties(conn)
    if previous[0] not in ('auto','manual'):
        raise ValueError('Unsupported NetworkManager IPv4 method. No changes made.')
    if mode=='static':
        ip=valid_ipv4(params.get('ip'))
        gateway=valid_ipv4(params.get('gateway'),'gateway')
        try:prefix=int(params.get('prefix',24))
        except (TypeError,ValueError):raise ValueError('Enter a valid subnet prefix.')
        if not 1<=prefix<=30:raise ValueError('Invalid prefix; choose 1–30.')
        if ipaddress.IPv4Address(gateway) not in ipaddress.ip_network(f'{ip}/{prefix}',strict=False):
            raise ValueError('Gateway is outside the new address subnet.')
        dns=[valid_ipv4(x,'DNS address') for x in (params.get('dns') or '').replace(',',' ').split()]
        if len(dns)>3:raise ValueError('No more than three DNS servers.')
        proposed=ip
    else:proposed=''
    # A periodic root service watches this snapshot independently of the browser,
    # the dashboard and the network worker request queue, including after reboot.
    deadline=int(time.time())+150  # allow network commands time to complete
    payload={'connection':conn,'device':device,'previous':previous,'old_ip':old_ip,
             'new_ip':proposed,'mode':mode,'expires':deadline}
    run(['/usr/bin/systemctl','start','uap-network-recovery.timer'],timeout=15)
    write_json(PENDING,payload,0o600)
    write_json(PUBLIC_PENDING,{k:payload[k] for k in ('new_ip','old_ip','mode','expires')},0o644)
    try:
        if mode=='dhcp':
            run(['/usr/bin/nmcli','connection','modify','id',conn,'ipv4.method','auto',
                 'ipv4.addresses','','ipv4.gateway','','ipv4.dns',''],timeout=20)
        else:
            run(['/usr/bin/nmcli','connection','modify','id',conn,'ipv4.method','manual',
                 'ipv4.addresses',f'{ip}/{prefix}','ipv4.gateway',gateway,
                 'ipv4.dns',','.join(dns)],timeout=20)
        current_ips=apply_connection(device,conn,'auto' if mode=='dhcp' else 'manual')
        # Changing MANUAL -> DHCP requires a fresh lease, not just the old
        # address left on the interface by a successful 'device reapply'.
        if mode=='dhcp' and previous[0]=='manual':
            run(['/usr/bin/nmcli','--wait','40','connection','up','id',conn,'ifname',device],timeout=50)
            current_ips=device_address(device)
        # Transition may require reactivation even when the old lease is still held.
        if mode=='static' and proposed not in current_ips:
            run(['/usr/bin/nmcli','--wait','40','connection','up','id',conn,'ifname',device],timeout=50)
            current_ips=device_address(device)
        if mode=='static' and proposed not in current_ips:
            raise ValueError('The new address was not applied. The original settings will be restored.')
        if mode=='dhcp' and (not current_ips or ipv4_properties(conn)[0]!='auto'):
            raise ValueError('DHCP did not assign an address. The original settings will be restored.')
        payload['new_ip']=proposed if mode=='static' else current_ips[0]
        payload['expires']=int(time.time())+120  # full 120 seconds after verification
        write_json(PENDING,payload,0o600)
        write_json(PUBLIC_PENDING,{k:payload[k] for k in ('new_ip','old_ip','mode','expires')},0o644)
        status('ip_change','pending','New address applied. Sign in through the new address and confirm before the deadline.',
               new_ip=payload['new_ip'],old_ip=old_ip,mode=mode,expires=payload['expires'])
    except subprocess.CalledProcessError as exc:
        rollback()
        detail=safe_nmcli_error(exc)
        raise ValueError(f'NetworkManager refused the IP address change (exit {exc.returncode}). '+
                         (detail if detail else 'Inspect the local NetworkManager logs.')+
                         ' The previous configuration was restored.') from None
    except Exception:
        rollback()
        raise


def confirm_ip(params):
    if not PENDING.exists():raise ValueError('No network change awaits confirmation.')
    pending=json.loads(PENDING.read_text())
    if pending['expires']<time.time():raise ValueError('The network confirmation deadline has expired.')
    if not pending.get('new_ip') or params.get('new_ip')!=pending['new_ip']:
        raise ValueError('Confirmation must come through the new LAN address.')
    if pending['new_ip'] not in device_address(pending['device']):
        raise ValueError('The selected network interface does not currently have the new address.')
    if ipv4_properties(pending['connection'])[0]!=('auto' if pending['mode']=='dhcp' else 'manual'):
        raise ValueError('Network configuration does not match the requested mode.')
    PENDING.unlink()
    PUBLIC_PENDING.unlink(missing_ok=True)
    message='Network address change confirmed.'
    cfg=load_config()
    if cfg.get('mode')=='npm' and cfg.get('npm_host_id'):
        try:
            npm=npm_token();host_id=cfg['npm_host_id']
            hosts=npm_api('GET','/nginx/proxy-hosts',token=npm)
            matching=[h for h in hosts if h.get('id')==host_id and cfg.get('hostname') in h.get('domain_names',[])]
            if matching and matching[0].get('forward_host')==pending.get('old_ip'):
                host=matching[0];host['forward_host']=pending['new_ip']
                keys=('domain_names','forward_scheme','forward_host','forward_port','access_list_id',
                      'certificate_id','ssl_forced','caching_enabled','block_exploits',
                      'allow_websocket_upgrade','http2_support','hsts_enabled',
                      'hsts_subdomains','advanced_config','locations','meta')
                npm_api('PUT',f'/nginx/proxy-hosts/{host_id}',{k:v for k,v in host.items() if k in keys},npm)
                cfg['lan_ip']=pending['new_ip'];save_config(cfg)
                message+=' Managed NPM proxy target updated.'
            elif matching:
                message+=' The managed NPM proxy already points to a different, unchanged network address; it was not modified.'
            else:message+=' Verify the NPM proxy target manually.'
        except Exception:
            message+=' Automatic NPM target update failed. Check NPM before using the domain.'
    status('ip_change','confirmed',message,new_ip=pending['new_ip'],mode=pending['mode'])
    status('ip_confirm','ok',message,new_ip=pending['new_ip'])


def wifi_interface(params):
    name=(params.get('interface') or '').strip()
    options=[d for d in network_devices() if d['type']=='wifi']
    if not name and len(options)==1:name=options[0]['device']
    if not any(d['device']==name for d in options):
        raise ValueError('No compatible wireless interface was found.')
    return name


def wifi_scan(params):
    iface=wifi_interface(params)
    try:
        radio=run(['/usr/bin/nmcli','-t','-f','WIFI','general','status'],timeout=8).stdout.strip().lower()
        if radio=='disabled':
            raise ValueError('Wi-Fi is switched off. Enable the wireless radio before scanning.')
    except subprocess.CalledProcessError:
        raise ValueError('Cannot read the wireless radio state from NetworkManager.') from None
    result=run(['/usr/bin/nmcli','-t','-f','SSID,SIGNAL,SECURITY','device','wifi','list',
                'ifname',iface,'--rescan','yes'],timeout=40)
    found=[]
    for line in result.stdout.splitlines():
        parts=re.split(r'(?<!\\):',line)  # nmcli escapes literal colons in SSIDs
        if len(parts)<3:continue
        ssid=':'.join(parts[:-2]).replace('\\:',':')[:64]
        if ssid and ssid not in [entry['ssid'] for entry in found]:
            found.append({'ssid':ssid,'signal':parts[-2][:3], 'security':parts[-1][:45]})
    state='ok' if found else 'warning'
    message=(f'Found {len(found[:25])} visible networks on {iface}.' if found else
             'Scan completed, but no networks were returned. Check radio state and try again.')
    status('wifi_scan',state,message,interface=iface,networks=found[:25])


def wifi_radio(params):
    power=params.get('enabled')
    if power not in ('yes','no'):raise ValueError('Select enable or disable Wi-Fi.')
    if power=='no':
        devices=network_devices()
        wifi_online=any(d['type']=='wifi' and d['state']=='connected' for d in devices)
        ethernet_online=any(d['type']=='ethernet' and d['state']=='connected' for d in devices)
        if wifi_online and not ethernet_online:
            raise ValueError('Wi-Fi is the only working connection. Disable it locally or connect Ethernet first; refusing remote lockout.')
    run(['/usr/bin/nmcli','radio','wifi','on' if power=='yes' else 'off'])
    actual=run(['/usr/bin/nmcli','-t','-f','WIFI','general','status']).stdout.strip().lower()
    target='enabled' if power=='yes' else 'disabled'
    if actual!=target:
        raise ValueError('NetworkManager did not report the requested Wi-Fi state. Check radio and RF-kill status.')
    status('wifi_radio','ok',f'Wi-Fi {actual}.')


def safe_nmcli_error(error):
    """Keep only generic NetworkManager failure information; never a PSK."""
    message=(getattr(error,'stderr','') or '').strip().split('\n')[0][:160]
    if (len(message)<=160 and re.fullmatch(r'[A-Za-z0-9 .,():_/-]+',message)
            and not any(word in message.lower() for word in ('password','secret','psk','token','key='))):
        return message
    return ''


def wifi_connect(params):
    device=wifi_interface(params)
    ssid=(params.get('ssid') or '').strip()
    password=params.get('wifi_password') or ''
    if not 1<=len(ssid.encode('utf-8'))<=32 or any(ord(ch)<32 for ch in ssid):
        raise ValueError('Wi-Fi name must contain 1–32 bytes without control characters.')
    if not (8<=len(password)<=63 or len(password)==64 and re.fullmatch('[0-9A-Fa-f]{64}',password)):
        raise ValueError('Enter a valid WPA2/WPA3 personal password (8–63 characters).')
    # Don't interrupt an active Wi-Fi session used to administer the detector.
    if any(d['device']==device and d['state']=='connected' for d in network_devices()):
        raise ValueError('Wi-Fi is already connected. To switch wireless networks, use a wired maintenance connection and disconnect the old Wi-Fi locally.')
    # Supply secrets only through a mode-0600 file, never the process command
    # line, worker status or journal. A temporary profile does not autoconnect
    # until a verified connection succeeds.
    profile='moon-cheese-wifi-'+os.urandom(4).hex()
    key_fd,key_path=tempfile.mkstemp(prefix='.wifi-key-',dir='/run')
    created=False
    try:
        os.fchmod(key_fd,0o600)
        with os.fdopen(key_fd,'w') as output:
            output.write('802-11-wireless-security.psk:'+password+'\n')
        run(['/usr/bin/nmcli','connection','add','type','wifi','con-name',profile,
             'ifname',device,'ssid',ssid,'802-11-wireless-security.key-mgmt','wpa-psk',
             'connection.autoconnect','no'],timeout=25)
        created=True
        # A remote AP with roaming/DHCP delays needs more than the old 45sec.
        run(['/usr/bin/nmcli','--wait','110','connection','up','id',profile,
             'ifname',device,'passwd-file',key_path],timeout=120)
        devices=network_devices()
        if not any(d['device']==device and d['connection']==profile and d['state']=='connected' for d in devices):
            raise ValueError('NetworkManager did not establish the selected Wi-Fi connection.')
        acquired=device_address(device)
        if not acquired:
            raise ValueError('Wi-Fi associated but did not receive an IPv4 address via DHCP.')
        run(['/usr/bin/nmcli','connection','modify','id',profile,'connection.autoconnect','yes'],timeout=15)
    except subprocess.CalledProcessError as exc:
        # Only share a generic actionable error; stderr may include SSID or
        # external plugin data and must not be posted without sanitisation.
        if created:
            try:run(['/usr/bin/nmcli','connection','delete','id',profile],timeout=12)
            except Exception:pass
        detail=safe_nmcli_error(exc)
        raise ValueError(f'NetworkManager could not activate Wi-Fi (exit {exc.returncode}). '+
                         (detail if detail else 'Check Wi-Fi security, DHCP and local NetworkManager logs.')+
                         ' The unsuccessful connection profile was removed.') from None
    except Exception:
        if created:
            try:run(['/usr/bin/nmcli','connection','delete','id',profile],timeout=12)
            except Exception:pass
        raise
    finally:
        os.unlink(key_path)
    status('wifi_connect','ok',f'Wi-Fi connected to the selected network and assigned {acquired[0]}.',interface=device)


def set_local(params):
    cfg=load_config()
    # Intentionally never shut down user's reverse proxy, Docker, DNS records
    # or tunnel without separate explicit approval.
    cfg['mode']='local';save_config(cfg)
    run(['/usr/bin/systemctl','disable','--now','uap-ddns.timer'])
    # Only our named tunnel service; never disable an unrelated service.
    if Path('/etc/systemd/system/uap-cloudflared.service').exists():
        run(['/usr/bin/systemctl','disable','--now','uap-cloudflared.service'])
    status('local','ok','Local-only selected. Existing external proxy/tunnel resources were not removed; review them separately.',mode='local')


def handle(action,params):
    if action=='npm_apply':apply_npm(params)
    elif action=='tunnel_apply':apply_tunnel(params)
    elif action=='npm':setup_npm(params)
    elif action=='npm_preview':preview_domain_change(params)
    elif action=='npm_change':change_managed_domain(params)
    elif action=='npm_retire_old':retire_previous_proxy(params)
    elif action=='tunnel':setup_tunnel(params)
    elif action=='tunnel_abandon':abandon_tunnel_progress(params)
    elif action=='tunnel_cleanup':cleanup_unfinished_tunnel(params)
    elif action=='tunnel_disable':disable_tunnel(params)
    elif action=='tunnel_remove':remove_tunnel(params)
    elif action=='ip_change':
        with network_lock():change_ip(params)
    elif action=='ip_confirm':
        with network_lock():confirm_ip(params)
    elif action=='ip_revert':
        with network_lock():rollback()
    elif action=='ddns_check':ddns()
    elif action=='wifi_scan':wifi_scan(params)
    elif action=='wifi_connect':wifi_connect(params)
    elif action=='wifi_radio':wifi_radio(params)
    elif action=='local':set_local(params)
    elif action=='external':
        # Only links in delivery's existing Optional HTTPS domain; no proxy contact.
        status('external','ok','Existing external proxy is managed outside Moon Cheese. Enter its HTTPS URL in Notification email links.',mode='external')
    else:raise ValueError('Unknown operation.')


def process_requests():
    for path in sorted(REQUESTS.glob('*.json'))[:8]:
        try:
            if path.is_symlink() or path.stat().st_size>8192:raise ValueError('Invalid network request.')
            data=json.loads(path.read_text())
        except Exception:
            path.unlink(missing_ok=True)
            continue
        path.unlink(missing_ok=True)
        action=data.get('action','')
        global ACTIVE_REQUEST_ID, ACTIVE_REQUEST_ACTION
        ACTIVE_REQUEST_ACTION=action
        ACTIVE_REQUEST_ID=data.get('request_id','') if re.fullmatch(r'[a-f0-9]{24}',data.get('request_id','')) else ''
        try:
            status(action,'working','Processing the administrator’s network request.')
            handle(action,data.get('params') or {})
            if action not in ('npm','npm_apply','tunnel_apply','npm_preview','npm_change','npm_retire_old','tunnel','tunnel_abandon','tunnel_disable','tunnel_remove','ip_change','ip_revert','ip_confirm','ddns_check','local','external','wifi_scan','wifi_connect','wifi_radio'):
                status(action,'ok','Operation completed.')
        except Exception as exc:
            # Never expose credentials, network command arguments or raw certbot output.
            safe = str(exc) if isinstance(exc,ValueError) else 'Network operation failed at '+(action or 'worker')+' ('+type(exc).__name__+'). Check the saved setup stage and retry; no credentials are displayed.'
            stage=''
            if action in ('tunnel','tunnel_apply'):
                cfg=read_json_optional(TUNNEL_PROGRESS)
                stage=cfg.get('setup_step','preflight')
                safe=f'Tunnel step {stage}: '+safe
            if action in ('npm','npm_apply','npm_change'):
                cfg=read_json_optional(DOMAIN_PROGRESS) if action=='npm_change' else load_config()
                stage=cfg.get('setup_step','preflight') if cfg.get('mode')=='npm' else 'preflight'
                safe=f'Step {stage}: '+safe
            status(action,'error',safe[:360])
            print(f'Network action {action} failed at {stage or "worker"}: {type(exc).__name__}',file=sys.stderr)
        finally:
            ACTIVE_REQUEST_ID=''
            ACTIVE_REQUEST_ACTION=''


def main():
    if os.geteuid()!=0:raise SystemExit('root/systemd only')
    RUN.mkdir(mode=0o755,parents=True,exist_ok=True)
    if len(sys.argv)>1 and sys.argv[1]=='rollback':
        with network_lock():rollback()
        return
    if len(sys.argv)>1 and sys.argv[1]=='recover':
        with network_lock():recover_expired()
        return
    if len(sys.argv)>1 and sys.argv[1]=='publish':
        publish_managed_domain();return
    if len(sys.argv)>1 and sys.argv[1]=='ddns':
        try:ddns()
        except Exception as exc:
            status('ddns_check','error',str(exc) if isinstance(exc,ValueError) else 'Cloudflare DDNS could not update. Check internet and token permissions.')
        return
    publish_managed_domain()
    process_requests()

if __name__=='__main__':main()
