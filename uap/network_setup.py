"""Moon Cheese network wizard helpers. Dashboard remains unprivileged.

Privileged changes are queued for a separate root/systemd helper. Never include
Cloudflare tokens in status, diagnostics, rendered HTML, or settings exports.
"""
import ipaddress
import json
import os
import re
import secrets
import socket
import subprocess
import time
from pathlib import Path

REQUESTS = Path('/var/lib/uap-detector/network-requests')
STATUS = Path('/run/uap-network/status.json')
STATUS_DIR = Path('/run/uap-network/status')
PENDING = Path('/var/lib/uap-detector/network-safety/pending.json')
PUBLIC_PENDING = Path('/run/uap-network/pending-public.json')
PUBLIC_MANAGED = Path('/run/uap-network/managed-public.json')


def valid_hostname(hostname):
    name = (hostname or '').strip().lower().rstrip('.')
    # IP literals, hostnames ending in reserved local suffixes and names without
    # any alphabetic character are not valid public domain configuration.
    if (len(name) > 253 or len(name) < 4 or '.' not in name
        or name.endswith(('.local','.internal','.localhost'))
        or not any(ch.isalpha() for ch in name) or not all(
        re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', item)
        for item in name.split('.')
    )):
        raise ValueError('Enter a full hostname such as camera.example.com.')
    return name


def valid_id(value, label='Cloudflare ID'):
    value = (value or '').strip()
    if not re.fullmatch(r'[a-fA-F0-9]{32}', value):
        raise ValueError(f'{label} must be the 32-character ID shown in Cloudflare.')
    return value


def valid_token(value):
    value = (value or '').strip()
    if not 12 <= len(value) <= 512 or not re.fullmatch(r'[A-Za-z0-9_.\-]+',value):
        raise ValueError('Enter your Cloudflare API token. Do not include spaces or a Bearer prefix.')
    return value


def valid_ipv4(value, label='IP address'):
    try:
        address = ipaddress.IPv4Address(value)
        if address.is_multicast or address.is_unspecified or address.is_loopback or address.is_link_local:
            raise ValueError()
        return str(address)
    except (ipaddress.AddressValueError, ValueError):
        raise ValueError(f'Enter a valid {label.lower()}.')


def local_ip():
    # Socket connect does not send a packet; falls back safely when offline.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.connect(('1.1.1.1', 53))
            ip = client.getsockname()[0]
            return valid_ipv4(ip)
    except (OSError, ValueError):
        return ''


def public_status(action=None):
    """Separate sanitised results by action; never share secrets or passwords."""
    if action:
        if action not in {'npm','tunnel','ip_change','ip_confirm','ip_revert','ddns_check','local','external','wifi_scan','wifi_connect','wifi_radio','npm_preview','npm_change','npm_retire_old','tunnel_abandon','tunnel_cleanup','tunnel_disable','tunnel_remove','npm_apply','tunnel_apply'}:
            return {}
        path = STATUS_DIR / (action+'.json')
    else:
        path = STATUS
    try:
        value = json.loads(path.read_text())
        result={k: value.get(k) for k in ('action','state','message','time','mode','hostname','last_ip','checked','new_ip','expires','request_id','preview_id')}
        if action=='wifi_scan':result['networks']=value.get('networks',[])[:25]
        return result
    except (ValueError, OSError):
        return {}


def all_statuses():
    actions=('npm','ddns_check','tunnel','ip_change','ip_confirm','ip_revert','wifi_scan','wifi_connect','wifi_radio','npm_preview','npm_change','npm_retire_old','tunnel_abandon','tunnel_cleanup','tunnel_disable','tunnel_remove','npm_apply','tunnel_apply')
    return [entry for action in actions if (entry:=public_status(action))]


def pending_change():
    try:
        value = json.loads(PUBLIC_PENDING.read_text())
        if not isinstance(value.get('expires'), (int,float)):
            return {}
        return {k:value.get(k) for k in ('new_ip','old_ip','expires','mode')}
    except (OSError, ValueError, TypeError):
        return {}


def managed_domain():
    """Only display the worker-published hostname, never network.json secrets."""
    try:
        value=json.loads(PUBLIC_MANAGED.read_text())
        return {k:value.get(k) for k in ('mode','hostname','setup_step','npm_host_enabled','previous_hostname','zone','certificate_contact_email','credentials_saved')}
    except (OSError, ValueError, TypeError):return {}


def network_interfaces():
    """Show eligible physical interfaces and connections; never Docker bridges."""
    try:
        completed=subprocess.run(['/usr/bin/nmcli','-t','-f','DEVICE,TYPE,STATE,CONNECTION','device','status'],
                                 check=True,capture_output=True,text=True,timeout=4)
    except (OSError,subprocess.SubprocessError):return []
    items=[]
    for line in completed.stdout.splitlines():
        parts=line.split(':',3)
        if len(parts)!=4 or parts[1] not in ('ethernet','wifi'):continue
        device,kind,state,conn=parts
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}',device):continue
        connection=conn if state=='connected' and conn!='--' else ''
        address=''; mode='unknown'
        if connection:
            try:
                result=subprocess.run(['/usr/bin/ip','-j','-4','addr','show','dev',device],
                    check=True,capture_output=True,text=True,timeout=3)
                for item in json.loads(result.stdout or '[]'):
                    for info in item.get('addr_info',[]):
                        if info.get('family')=='inet':
                            value=str(info.get('local',''))
                            try:
                                address=str(ipaddress.IPv4Address(value))
                                break
                            except ipaddress.AddressValueError:pass
                    if address:break
            except (OSError,subprocess.SubprocessError,ValueError,TypeError):pass
            try:
                method=subprocess.run(['/usr/bin/nmcli','-g','ipv4.method','connection','show',connection],
                    check=True,capture_output=True,text=True,timeout=3).stdout.strip()
                mode={'auto':'DHCP','manual':'Static'}.get(method,'Other')
            except (OSError,subprocess.SubprocessError):pass
        items.append({'device':device,'kind':kind,'state':state,'connection':connection,
                      'address':address,'address_mode':mode})
    return items


def queue_action(action, params):
    if action not in {'local','npm','tunnel','external','ip_change','ip_confirm','ip_revert','ddns_check','wifi_scan','wifi_connect','wifi_radio','npm_preview','npm_change','npm_retire_old','tunnel_abandon','tunnel_cleanup','tunnel_disable','tunnel_remove','npm_apply','tunnel_apply'}:
        raise ValueError('Unsupported network operation.')
    REQUESTS.mkdir(mode=0o700,parents=True,exist_ok=True)
    # The directory is accessible only to the dashboard service account and root.
    request_id=secrets.token_hex(12)
    filename = REQUESTS / (request_id+'.json')
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, 'O_NOFOLLOW'): flags |= os.O_NOFOLLOW
    fd = os.open(str(filename), flags, 0o600)
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump({'action':action,'params':params,'request_id':request_id},out)
    except Exception:
        filename.unlink(missing_ok=True)
        raise
    return request_id


def wifi_radio_state():
    """NetworkManager's actual radio state, never a hard-coded form default."""
    try:
        result=subprocess.run(['/usr/bin/nmcli','-t','-f','WIFI','general','status'],
                              capture_output=True,text=True,check=True,timeout=4)
        state=result.stdout.strip().lower()
        if state in ('enabled','disabled'):return state
    except (OSError,subprocess.SubprocessError):pass
    return 'unknown'


def managed_tunnel():
    """Non-secret Tunnel identity and unfinished-stage visibility for admins."""
    try:
        value=json.loads((Path('/run/uap-network/tunnel-public.json')).read_text())
        return {k:value.get(k) for k in ('mode','managed','hostname','stage_hostname','stage_step','unfinished','account','zone','previous_hostname','credentials_saved')}
    except (OSError,ValueError,TypeError):return {}
