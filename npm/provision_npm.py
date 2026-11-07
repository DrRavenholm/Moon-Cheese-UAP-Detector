"""Set up one HTTP proxy host on a fresh, private NPM. Safe to rerun."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

api = 'http://127.0.0.1:8181/api'
username = os.environ['NPM_ADMIN_EMAIL']
password = os.environ['NPM_ADMIN_PASSWORD']
domain = os.environ['UAP_DOMAIN']


def http(method, path, obj=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(api + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.load(response)


last_exc = None
for attempt in range(30):
    try:
        token = http('POST', '/tokens', {'identity': username, 'secret': password})['token']
        break
    except (OSError, KeyError, ValueError, TimeoutError) as ex:
        last_exc = ex
        time.sleep(3)
else:
    print('NPM started but automatic proxy setup not ready. Run sudo uapctl status; see README.', last_exc)
    sys.exit(1)

hosts = http('GET', '/nginx/proxy-hosts', token=token)
if any(domain in host.get('domain_names', []) for host in hosts):
    print(f'NPM proxy for {domain} already exists.')
    sys.exit(0)

body = {
    'domain_names': [domain],
    'forward_scheme': 'http',
    'forward_host': 'host.docker.internal',
    'forward_port': 8000,
    'access_list_id': 0,
    'certificate_id': 0,
    'ssl_forced': False,
    'caching_enabled': False,
    'block_exploits': True,
    'allow_websocket_upgrade': False,
    'http2_support': False,
    'hsts_enabled': False,
    'hsts_subdomains': False,
    'advanced_config': '',
    'locations': [],
    'meta': {},
}
result = http('POST', '/nginx/proxy-hosts', body, token=token)
print(f'NPM configured HTTP proxy for {domain} (id={result.get("id", "unknown")}).')
