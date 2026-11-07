"""Opt-in SMTP and standards-based encrypted Web Push for local notifications.

All credentials are kept in a mode-0600 file excluded from portable backups.
The periodic notification worker calls dispatch() after generating dashboard notices.
"""
import base64
import hashlib
import hmac
import html
import ipaddress
import socket
import json
import os
import re
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from urllib.parse import urlsplit, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from common import DATA, connection

CONFIG_PATH = DATA / 'delivery-mail.json'
VAPID_PATH = DATA / 'delivery-vapid.json'
PUSH_CONFIG_PATH = DATA / 'delivery-push.json'
LINKS_CONFIG_PATH = DATA / 'delivery-links.json'
RETENTION_CONFIG_PATH = DATA / 'delivery-retention.json'
EMAIL_RE = re.compile(r'^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$')


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def valid_email(value):
    value = str(value or '').strip()
    if len(value)>254 or not EMAIL_RE.fullmatch(value) or parseaddr(value)[1]!=value:
        raise ValueError('Enter a valid email address (without a display name).')
    return value


def _private_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.'+secrets.token_hex(8)+'.tmp')
    fd=os.open(temp, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf8') as stream:
            json.dump(obj,stream)
            stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()


def _private_read(path):
    try:
        if path.is_symlink():raise ValueError('Refusing a symlink for private configuration.')
        return json.loads(path.read_text(encoding='utf8'))
    except FileNotFoundError:return {}


def smtp_settings():
    value = _private_read(CONFIG_PATH)
    return value if isinstance(value,dict) else {}


def save_smtp(host,port,username,secret,from_email,security='starttls',enabled=False):
    host=str(host or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9.-]{1,253}',host) or host.startswith('-'):
        raise ValueError('Enter an SMTP server hostname.')
    try:port=int(port)
    except (ValueError,TypeError):raise ValueError('Invalid SMTP port.')
    if not 1<=port<=65535:raise ValueError('Invalid SMTP port.')
    if security not in ('starttls','ssl'):raise ValueError('Choose STARTTLS or implicit TLS.')
    username=str(username or '').strip()
    if len(username)>254 or any(c in username for c in '\r\n'):raise ValueError('Invalid SMTP username.')
    old=smtp_settings()
    password=str(secret or '') if secret else str(old.get('password',''))
    if not username or not password:raise ValueError('Enter a username and SMTP app password or credential.')
    if len(password)>2048:raise ValueError('SMTP credential is too long.')
    obj={'host':host,'port':port,'username':username,'password':password,
         'from_email':valid_email(from_email),'security':security,'enabled':bool(enabled)}
    _private_write(CONFIG_PATH,obj)
    return obj


def _link_base(value, public=False):
    value=str(value or '').strip().rstrip('/')
    if not value:return ''
    uri=urlsplit(value)
    if (uri.scheme not in (('https',) if public else ('http','https'))
        or not uri.hostname or uri.username or uri.password or uri.path not in ('','/')
        or uri.query or uri.fragment or len(value)>260 or any(ch.isspace() for ch in value)):
        raise ValueError('Enter a plain http(s) local URL or an HTTPS domain without paths or credentials.')
    try:port=uri.port
    except ValueError:raise ValueError('Invalid dashboard URL port.') from None
    try:
        address=ipaddress.ip_address(uri.hostname)
    except ValueError:
        hostname=uri.hostname.lower()
        if not re.fullmatch(r'[a-z0-9.-]+',hostname):
            raise ValueError('Invalid dashboard hostname.')
        if public:
            if '.' not in hostname or hostname.endswith(('.local','.lan','.home.arpa')):
                raise ValueError('Enter a full HTTPS hostname for the public domain.')
        elif '.' in hostname and not hostname.endswith(('.local','.lan','.home.arpa')):
            raise ValueError('Local dashboard URL must use a private IP or local network hostname.')
    else:
        if public and not address.is_global:
            raise ValueError('Public dashboard address must be publicly reachable.')
        if not public and not (address.is_private or address.is_link_local or address.is_loopback):
            raise ValueError('Local dashboard URL must use a private LAN address.')
    return value


def save_dashboard_links(local_url,public_url):
    values={'local':_link_base(local_url),'public':_link_base(public_url,public=True)}
    _private_write(LINKS_CONFIG_PATH,values)
    return values


def dashboard_links():
    obj=_private_read(LINKS_CONFIG_PATH)
    return {'local':str(obj.get('local','')),'public':str(obj.get('public',''))}


def detected_local_url():
    """LAN-only default for email links; never trust client HTTP Host headers."""
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.connect(('1.1.1.1',80))  # Select local interface, no datagram transmitted.
            addr=ipaddress.ip_address(sock.getsockname()[0])
        if addr.is_private:return f'http://{addr}:8000'
    except (OSError,ValueError):pass
    return ''


def notice_path(key,category=None):
    match=re.fullmatch(r'observation-job:(\d+):[a-z_-]+',str(key or ''))
    if match:return '/observations/job/'+match.group(1)
    if str(key or '').startswith('digest:'):return '/notifications?category=digest'
    if category in ('fault','recovery'):return '/system'
    return '/notifications'


def dashboard_url(key='',category=None):
    links=dashboard_links()
    base=links['public'] or links['local'] or detected_local_url()
    if not base:return '',False
    return base+notice_path(key,category),bool(links['public'])


def notification_html(title,body,url='',remote=False):
    safe_title=html.escape(str(title))
    paragraphs=''.join('<p style="margin:7px 0;color:#334155;font-size:15px;line-height:1.6">'+html.escape(line)+'</p>'
                       for line in str(body).splitlines() if line.strip())
    action=''
    if url:
        label='Open in Moon Cheese' if remote else 'Open on home network'
        action='<p style="margin:24px 0"><a href="'+html.escape(url,quote=True)+'" style="background:#285b78;border-radius:7px;padding:12px 18px;color:white;text-decoration:none;font-weight:600">'+label+'</a></p>'
    label='' if remote else '<p style="font-size:12px;color:#64748b">Local-only link: connect to your home network or VPN to open it. Sign-in is required.</p>'
    return ('<!doctype html><html><body style="margin:0;padding:24px;background:#edf2f6;font-family:Arial,sans-serif">'
            '<div style="max-width:620px;margin:auto;background:#fff;border-radius:12px;overflow:hidden">'
            '<div style="padding:18px 24px;background:#12263a;color:#fff;font-weight:700">✦ MOON CHEESE</div>'
            '<div style="padding:24px"><h2 style="margin:0 0 14px;color:#172b45">'+safe_title+'</h2>'+paragraphs+action+label+
            '<p style="border-top:1px solid #ddd;padding-top:14px;color:#64748b;font-size:12px">Automated observation notification. Sign in to review details and manage delivery preferences.</p></div></div></body></html>')


def smtp_send(recipient,subject,body, config=None, *, notice_title=None, url='', remote=False):
    config=config or smtp_settings()
    if not config.get('enabled'):raise ValueError('Outgoing email is not enabled.')
    recipient=valid_email(recipient)
    message=EmailMessage()
    message['From']=config['from_email'];message['To']=recipient
    message['Subject']=str(subject).replace('\n',' ').replace('\r',' ')[:160]
    content=str(body)[:16000]
    if url:content+='\n\n'+('Open in Moon Cheese UAP Detector: ' if remote else 'Home network only — open in Moon Cheese UAP Detector: ')+url+'\nSign-in is required.'
    message.set_content(content)
    message.add_alternative(notification_html(notice_title or subject,body,url,remote),subtype='html')
    context=ssl.create_default_context()
    if config['security']=='ssl':
        client=smtplib.SMTP_SSL(config['host'],int(config['port']),timeout=15,context=context)
    else:
        client=smtplib.SMTP(config['host'],int(config['port']),timeout=15)
    with client:
        if config['security']=='starttls':
            client.ehlo();client.starttls(context=context);client.ehlo()
        client.login(config['username'],config['password'])
        client.send_message(message)


def migrate():
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS delivery_preferences (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            recipient_email TEXT NOT NULL DEFAULT '', email_enabled INTEGER NOT NULL DEFAULT 0,
            push_enabled INTEGER NOT NULL DEFAULT 0,
            email_since TEXT NOT NULL DEFAULT '', push_since TEXT NOT NULL DEFAULT '')''')
        db.execute('''CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            endpoint TEXT NOT NULL UNIQUE, p256dh TEXT NOT NULL, auth TEXT NOT NULL,
            device TEXT NOT NULL DEFAULT 'Browser', created_utc TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS notice_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_id INTEGER NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
            channel TEXT NOT NULL CHECK(channel IN ('email','push')),
            target TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0, next_try_utc TEXT NOT NULL,
            changed_utc TEXT NOT NULL, error TEXT NOT NULL DEFAULT '',
            UNIQUE(notice_id,channel,target))''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_delivery_retry ON notice_deliveries(state,next_try_utc)')


def user_settings(user_id):
    with connection() as db:
        row=db.execute('SELECT * FROM delivery_preferences WHERE user_id=?',(user_id,)).fetchone()
    return dict(row) if row else {'recipient_email':'','email_enabled':0,'push_enabled':0,
                                   'email_since':'','push_since':''}


def save_user_settings(user_id,email,email_enabled,push_enabled):
    email=valid_email(email) if email or email_enabled else ''
    if email_enabled and not email:raise ValueError('Enter a recipient email address before enabling email.')
    now=utc_now()
    with connection() as db:
        old=db.execute('SELECT * FROM delivery_preferences WHERE user_id=?',(user_id,)).fetchone()
        # A queued message must never be sent to an old address, or after opt-out.
        if not email_enabled or (old and old['recipient_email']!=email):
            db.execute('''DELETE FROM notice_deliveries WHERE channel='email'
                 AND state IN ('pending','retry','failed') AND notice_id IN
                 (SELECT id FROM notices WHERE user_id=?)''',(user_id,))
        if not push_enabled:
            db.execute('''DELETE FROM notice_deliveries WHERE channel='push'
                 AND state IN ('pending','retry','failed') AND notice_id IN
                 (SELECT id FROM notices WHERE user_id=?)''',(user_id,))
        email_since=old['email_since'] if old and old['email_enabled'] and old['recipient_email']==email else now
        push_since=old['push_since'] if old and old['push_enabled'] else now
        db.execute('''INSERT INTO delivery_preferences(user_id,recipient_email,email_enabled,push_enabled,email_since,push_since)
                      VALUES(?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
                      recipient_email=excluded.recipient_email,email_enabled=excluded.email_enabled,
                      push_enabled=excluded.push_enabled,email_since=excluded.email_since,push_since=excluded.push_since''',
                   (user_id,email,int(bool(email_enabled)),int(bool(push_enabled)),email_since,push_since))


def push_contact():
    obj=_private_read(PUSH_CONFIG_PATH)
    return obj.get('contact_email','') if isinstance(obj,dict) else ''


def save_push_contact(address):
    obj={'contact_email':valid_email(address)}
    _private_write(PUSH_CONFIG_PATH,obj)
    return obj


def _b64(data):return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _unb64(value):
    value=str(value or '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,500}',value):raise ValueError('Invalid browser subscription key.')
    return base64.urlsafe_b64decode(value+'='*((-len(value))%4))


def _crypto():
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes,serialization
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    return ec,hashes,serialization,AESGCM,decode_dss_signature


def vapid_keys():
    obj=_private_read(VAPID_PATH)
    if obj:return obj
    ec,_,serialization,_,_=_crypto()
    key=ec.generate_private_key(ec.SECP256R1())
    obj={'private':_b64(key.private_numbers().private_value.to_bytes(32,'big')),
         'public':_b64(key.public_key().public_bytes(serialization.Encoding.X962,
                                                    serialization.PublicFormat.UncompressedPoint))}
    _private_write(VAPID_PATH,obj)
    return obj


def _endpoint_parts(url):
    url=str(url or '')
    value=urlsplit(url)
    host=(value.hostname or '').lower()
    trusted=(host in ('fcm.googleapis.com','fcm-xm.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com')
             or host.endswith('.push.apple.com') or host.endswith('.notify.windows.com'))
    if (value.scheme!='https' or not trusted or value.port not in (None,443) or value.username or value.password
            or not value.path or len(url)>2048 or value.fragment):
        raise ValueError('Unrecognised or unsafe browser push endpoint.')
    return value


def register_subscription(user_id, endpoint, p256dh, auth, device='Browser'):
    _endpoint_parts(endpoint)
    if len(_unb64(p256dh))!=65 or len(_unb64(auth))!=16:raise ValueError('Browser push keys have an invalid size.')
    ec,_,_,_,_=_crypto()
    try:ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(),_unb64(p256dh))
    except ValueError:raise ValueError('Invalid browser push public key.') from None
    device=str(device or 'Browser').strip()[:72]
    with connection() as db:
        row=db.execute('SELECT user_id FROM push_subscriptions WHERE endpoint=?',(endpoint,)).fetchone()
        if row and row['user_id']!=user_id:raise ValueError('This browser is already registered to another user.')
        db.execute('''INSERT INTO push_subscriptions(user_id,endpoint,p256dh,auth,device,created_utc)
                     VALUES(?,?,?,?,?,?) ON CONFLICT(endpoint) DO UPDATE SET
                     p256dh=excluded.p256dh,auth=excluded.auth,device=excluded.device''',
                   (user_id,endpoint,p256dh,auth,device,utc_now()))


def remove_subscription(user_id,sub_id):
    with connection() as db:
        result=db.execute('DELETE FROM push_subscriptions WHERE id=? AND user_id=?',(sub_id,user_id)).rowcount
        if result:
            db.execute("DELETE FROM notice_deliveries WHERE channel='push' AND target=? AND state IN ('pending','retry','failed')",(str(sub_id),))
        return result


def subscriptions(user_id):
    with connection() as db:
        return [dict(r) for r in db.execute('SELECT id,device,created_utc FROM push_subscriptions WHERE user_id=? ORDER BY id',(user_id,))]


def _expand(prk, info, size):
    result=b''; previous=b''; counter=1
    while len(result)<size:
        previous=hmac.new(prk,previous+info+bytes([counter]),hashlib.sha256).digest()
        result+=previous;counter+=1
    return result[:size]


def _encrypt_webpush(text,pub,auth):
    """RFC 8291 + RFC 8188 aes128gcm content encoding."""
    ec,_,serialization,AESGCM,_=_crypto()
    receiver=ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(),_unb64(pub))
    sender=ec.generate_private_key(ec.SECP256R1())
    sender_pub=sender.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)
    receiver_pub=_unb64(pub)
    ecdh=sender.exchange(ec.ECDH(),receiver)
    prk_key=hmac.new(_unb64(auth),ecdh,hashlib.sha256).digest()
    ikm=_expand(prk_key,b'WebPush: info\x00'+receiver_pub+sender_pub,32)
    salt=secrets.token_bytes(16)
    prk=hmac.new(salt,ikm,hashlib.sha256).digest()
    key=_expand(prk,b'Content-Encoding: aes128gcm\x00',16)
    nonce=_expand(prk,b'Content-Encoding: nonce\x00',12)
    plaintext=text.encode('utf8')+b'\x02'
    if len(plaintext)>3900:raise ValueError('Notification too large.')
    ciphertext=AESGCM(key).encrypt(nonce,plaintext,None)
    return salt+(4096).to_bytes(4,'big')+bytes([65])+sender_pub+ciphertext


def _vapid_auth(endpoint, contact):
    ec,hashes,_,_,decode_dss_signature=_crypto()
    key=vapid_keys()
    private=ec.derive_private_key(int.from_bytes(_unb64(key['private']),'big'),ec.SECP256R1())
    uri=urlsplit(endpoint);aud=f'{uri.scheme}://{uri.netloc}'
    now=int(datetime.now(timezone.utc).timestamp())
    unsigned=_b64(b'{"typ":"JWT","alg":"ES256"}')+'.'+_b64(json.dumps({'aud':aud,'exp':now+3600,'sub':'mailto:'+valid_email(contact)},separators=(',',':')).encode())
    from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
    r,s=decode_dss_signature(private.sign(unsigned.encode(),ECDSA(hashes.SHA256())))
    return f'vapid t={unsigned}.{_b64(r.to_bytes(32,"big")+s.to_bytes(32,"big"))}, k={key["public"]}'


def push_send(subscription,title,body,url='/notifications'):
    endpoint=subscription['endpoint'];_endpoint_parts(endpoint)
    contact=push_contact() or smtp_settings().get('from_email')
    if not contact:raise ValueError('Configure the Web Push administrative contact email first.')
    data=json.dumps({'title':str(title)[:120],'body':str(body)[:1500],'url':url if url.startswith('/') and not url.startswith('//') else '/notifications'},ensure_ascii=False)
    encrypted=_encrypt_webpush(data,subscription['p256dh'],subscription['auth'])
    req=Request(endpoint,data=encrypted,headers={'Authorization':_vapid_auth(endpoint,contact),
                 'Content-Encoding':'aes128gcm','Content-Type':'application/octet-stream','TTL':'3600'},method='POST')
    try:
        with urlopen(req,timeout=15) as resp:
            if resp.status not in (201,202):raise ValueError(f'Push service rejected the message (HTTP {resp.status}).')
    except HTTPError as exc:
        if exc.code in (404,410):
            with connection() as db:db.execute('DELETE FROM push_subscriptions WHERE endpoint=?',(endpoint,))
        raise ValueError(f'Push service returned HTTP {exc.code}.') from None


def queue_due(now=None):
    """Queue only notices created after individual channel opt-in; deduplicate by unique key."""
    now=now or utc_now()
    with connection() as db:
        db.execute('DELETE FROM notice_deliveries WHERE notice_id NOT IN (SELECT id FROM notices)')
        users=db.execute('''SELECT u.id,p.* FROM users u JOIN delivery_preferences p ON p.user_id=u.id WHERE u.enabled=1''').fetchall()
        for user in users:
            for channel,enabled,since in (('email',user['email_enabled'],user['email_since']),
                                           ('push',user['push_enabled'],user['push_since'])):
                if not enabled or not since:continue
                if channel=='email':
                    targets=[(user['recipient_email'],since)] if user['recipient_email'] and smtp_settings().get('enabled') else []
                else:
                    targets=[(str(row['id']), max(since,row['created_utc'])) for row in db.execute(
                        'SELECT id,created_utc FROM push_subscriptions WHERE user_id=?',(user['id'],))]
                for target,eligible_since in targets:
                    db.execute('''INSERT OR IGNORE INTO notice_deliveries(notice_id,channel,target,next_try_utc,changed_utc)
                        SELECT n.id,?,?,?,? FROM notices n WHERE n.user_id=? AND n.created_utc>=?''',
                       (channel,target,now,now,user['id'],eligible_since))


def _claim_due(now):
    with connection() as db:
        # Recover an interrupted attempt (may mean one duplicate email after a crash).
        stale=(datetime.fromisoformat(now)-timedelta(minutes=10)).isoformat(timespec='seconds')
        db.execute("UPDATE notice_deliveries SET state='retry' WHERE state='sending' AND changed_utc<?",(stale,))
        ids=[r['id'] for r in db.execute('''SELECT id FROM notice_deliveries
            WHERE state IN ('pending','retry') AND next_try_utc<=? AND attempts<4 ORDER BY id LIMIT 12''',(now,))]
        for ident in ids:db.execute("UPDATE notice_deliveries SET state='sending',attempts=attempts+1,changed_utc=? WHERE id=?",(now,ident))
        return [dict(r) for r in db.execute('''SELECT d.*,n.title,n.body,n.user_id,n.unique_key,n.category FROM notice_deliveries d
            JOIN notices n ON n.id=d.notice_id WHERE d.id IN ('''+(','.join('?' for _ in ids) if ids else 'NULL')+')',ids)]


def dispatch(now=None):
    now=now or utc_now()
    queue_due(now)
    prune_delivery_history(now)
    results={'sent':0,'failed':0}
    for item in _claim_due(now):
        try:
            if item['channel']=='email':
                smtp_send(item['target'],'Moon Cheese UAP Detector: '+item['title'],item['body'],
                          notice_title=item['title'],url=dashboard_url(item['unique_key'],item['category'])[0],
                          remote=dashboard_url(item['unique_key'],item['category'])[1])
            else:
                with connection() as db:
                    sub=db.execute('SELECT * FROM push_subscriptions WHERE id=? AND user_id=?',(int(item['target']),item['user_id'])).fetchone()
                if not sub:raise ValueError('Browser subscription was removed.')
                push_send(dict(sub),item['title'],item['body'],url=notice_path(item['unique_key'],item['category']))
            state='sent';error='';results['sent']+=1
        except Exception as exc:
            # Do not leak credential material or remote server replies in the dashboard.
            state='failed' if item['attempts']>=4 else 'retry'
            error=type(exc).__name__+': Delivery failed; check provider credentials, connectivity, or device permission.'
            results['failed']+=1
        next_try=(datetime.fromisoformat(now)+timedelta(minutes=min(60,5*2**max(0,item['attempts']-1)))).isoformat(timespec='seconds')
        with connection() as db:
            db.execute('UPDATE notice_deliveries SET state=?,error=?,next_try_utc=?,changed_utc=? WHERE id=?',
                       (state,error,next_try,now,item['id']))
    return results


def recent_delivery(user_id=None,limit=10):
    with connection() as db:
        sql='''SELECT d.id,d.channel,d.state,d.attempts,d.changed_utc,d.error,n.title,u.username
            FROM notice_deliveries d JOIN notices n ON n.id=d.notice_id
            JOIN users u ON u.id=n.user_id'''
        args=[]
        if user_id is not None:sql+=' WHERE u.id=?';args.append(user_id)
        sql+=' ORDER BY d.id DESC LIMIT ?';args.append(limit)
        return [dict(r) for r in db.execute(sql,args)]


def retry_failed(delivery_id):
    """Admin-approved retry of a previously exhausted delivery attempt."""
    with connection() as db:
        return db.execute("""UPDATE notice_deliveries SET state='retry',attempts=0,error='',
                            next_try_utc=?,changed_utc=? WHERE id=? AND state='failed'""",
                          (utc_now(),utc_now(),int(delivery_id))).rowcount



def delivery_retention_days():
    value=_private_read(RETENTION_CONFIG_PATH).get('days',90)
    try:days=int(value)
    except (TypeError,ValueError):return 90
    return days if days in (30,60,90,180) else 90


def save_delivery_retention(days):
    try:value=int(days)
    except (TypeError,ValueError):raise ValueError('Choose a valid retention period.')
    if value not in (30,60,90,180):raise ValueError('Choose 30, 60, 90 or 180 days.')
    _private_write(RETENTION_CONFIG_PATH,{'days':value})
    return value

def delivery_history(page=1,channel='all',state='all',limit=20):
    page=max(1,int(page));limit=min(50,max(1,int(limit)))
    clauses=[];args=[]
    if channel in ('email','push'):
        clauses.append('d.channel=?');args.append(channel)
    if state in ('pending','retry','sending','sent','failed'):
        clauses.append('d.state=?');args.append(state)
    condition=' WHERE '+' AND '.join(clauses) if clauses else ''
    with connection() as db:
        base=' FROM notice_deliveries d JOIN notices n ON n.id=d.notice_id JOIN users u ON u.id=n.user_id'
        count=db.execute('SELECT COUNT(*)'+base+condition,args).fetchone()[0]
        max_page=max(1,(count+limit-1)//limit);page=min(page,max_page)
        sql='SELECT d.id,d.channel,d.state,d.attempts,d.changed_utc,d.error,n.title,u.username'+base+condition+' ORDER BY d.id DESC LIMIT ? OFFSET ?'
        rows=[dict(r) for r in db.execute(sql,(*args,limit,(page-1)*limit))]
    return {'rows':rows,'total':count,'page':page,'pages':max_page}


def prune_delivery_history(now=None,retention_days=None):
    """Remove only completed delivery metadata, never actual notices or queued work."""
    days=delivery_retention_days() if retention_days is None else retention_days
    timestamp=datetime.fromisoformat(now or utc_now())-timedelta(days=days)
    with connection() as db:
        return db.execute("DELETE FROM notice_deliveries WHERE state IN ('sent','failed') AND changed_utc<?",
                          (timestamp.isoformat(timespec='seconds'),)).rowcount
