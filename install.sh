#!/usr/bin/env bash
# Moon Cheese UAP Detector v1.0.1.1: fresh installation, safe upgrade or same-version repair.
# Camera/OS capability checks rather than Raspberry Pi 4-only restrictions.
# Existing recordings, credentials and network/proxy configuration are preserved.
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
VERSION='1.0.1.1'
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP=/opt/uap-detector/uap
ETC=/etc/uap-detector
DATA=/var/lib/uap-detector
BACKUP_ROOT=/var/backups/uap-detector
fail(){ printf '\nERROR: %s\n' "$*" >&2; exit 1; }
info(){ printf '\n--- %s ---\n' "$*"; }
[[ $(id -u) -eq 0 ]] || fail 'Use: sudo bash install.sh'
cd "$HERE"
# In-archive hashes catch incomplete/corrupted copies (not a cryptographic publisher signature).
if [[ -f SHA256SUMS ]]; then
  sha256sum --check --quiet SHA256SUMS || fail 'Package checksum verification failed. Recopy the complete archive.'
fi
for file in dashboard.py detector.py common.py observation_jobs.py photography.py camera_profiles.py \
            draft_preview.py hardware.py scheduling.py delivery.py notifications.py \
            network_setup.py network_worker.py network_ui.py; do
  [[ -f "uap/$file" ]] || fail "Incomplete archive: missing uap/$file"
done
for file in uap-dashboard.service uap-detector.service uap-notifications.service \
            uap-notifications.timer uap-cleanup.service uap-cleanup.timer \
            uap-power-action.service uap-power-action.path \
            uap-network-worker.service uap-network-worker.path uap-ddns.service uap-ddns.timer \
            uap-network-recovery.service uap-network-recovery.timer uap-cloudflared.service uap-cloudflared-candidate.service uap-software-update.service uap-software-update.path; do
  [[ -f "systemd/$file" ]] || fail "Incomplete archive: missing systemd/$file"
done
for file in npm/compose.yaml npm/provision_npm.py; do
  [[ -f "$file" ]] || fail "Incomplete archive: missing $file"
done
for file in uap/network_ui.js uap/network_confirm.js uap/camera_reset.js uap/investigator.js; do [[ -f "$file" ]] || fail "Incomplete archive: missing $file"; done
for file in uap/*.py; do python3 -m py_compile "$file"; done
if command -v node >/dev/null 2>&1; then
  for file in uap/*.js; do node --check "$file" >/dev/null; done
fi
[[ ${UAP_PACKAGE_VALIDATE_ONLY:-0} != 1 ]] || { echo 'Complete package source and syntax verified.'; exit 0; }
# Recognise model, architecture, camera dependency and available memory independently.
# Only Pi 4 is hardware-tested. Other devices must not be arbitrarily rejected,
# but unavailable packages are a real limitation and must be reported accurately.
ARCH=$(dpkg --print-architecture)
case "$ARCH" in arm64|armhf|amd64) ;; *) fail "Unsupported Debian package architecture: $ARCH. Hardware needs testing." ;; esac
MODEL='Unknown Linux device'
[[ ! -r /proc/device-tree/model ]] || MODEL=$(tr -d '\0' </proc/device-tree/model)
. /etc/os-release
[[ ${ID:-} == debian || ${ID:-} == raspbian ]] || fail 'A Debian-based Linux distribution with apt and systemd is required.'
[[ ${VERSION_CODENAME:-} == bookworm || ${VERSION_CODENAME:-} == trixie ]] || \
  fail 'This version is designed for Debian/Raspberry Pi OS Bookworm or Trixie. Other releases need dependency testing.'
command -v systemctl >/dev/null || fail 'Systemd is required to operate the detector services.'
RAM_MB=$(awk '/^MemTotal:/{print int($2/1024)}' /proc/meminfo)
LOW_RESOURCE=0
if [[ "$MODEL" == *'Raspberry Pi Zero'* ]] || (( RAM_MB < 1024 )); then LOW_RESOURCE=1;fi
info "Detected hardware: $MODEL · $ARCH · ${RAM_MB} MB RAM"
if (( LOW_RESOURCE )); then
  echo 'EXPERIMENTAL LOW-RESOURCE MODE: slow detection, video rendering and concurrent jobs are possible.'
  echo 'Docker and bundled NPM are disabled by default; use Raspberry Pi OS Lite on a Pi Zero 2 W.'
  : "${UAP_INSTALL_NPM:=0}"
else
  : "${UAP_INSTALL_NPM:=1}"
fi
if [[ "$MODEL" != *'Raspberry Pi 4'* ]]; then
  echo 'WARNING: This hardware is not the Pi 4 reference test platform. Camera capabilities will be checked at runtime.'
  [[ "$MODEL" != *'Raspberry Pi Zero'* ]] || echo 'WARNING: Original Pi Zero models may not support the required camera software; installation is experimental.'
fi
if [[ "$ARCH" != 'arm64' && "$UAP_INSTALL_NPM" == '1' ]]; then
  echo 'WARNING: bundled Docker/NPM installation is disabled on this non-arm64 setup.'
  UAP_INSTALL_NPM=0
fi
export UAP_INSTALL_NPM
EXISTING=0
if [[ -f "$APP/dashboard.py" || -e /etc/systemd/system/uap-dashboard.service ]]; then
  [[ -f "$APP/dashboard.py" && -f /etc/systemd/system/uap-dashboard.service ]] || fail 'Partial existing installation. No changes made. Review it before running the installer.'
  EXISTING=1
fi
# Avoid unsafe upgrades during camera ownership or active recording.
if (( EXISTING )) && [[ -f "$DATA/events.sqlite3" ]]; then
 python3 - "$DATA/events.sqlite3" <<'PY'
import sqlite3,sys
try:
    con=sqlite3.connect(f'file:{sys.argv[1]}?mode=ro',uri=True,timeout=5)
    table=con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='observation_jobs'").fetchone()
    if table:
        active=con.execute("SELECT count(*) FROM observation_jobs WHERE status IN ('capturing','rendering','archiving','finalising')").fetchone()[0]
        if active:sys.exit('A scheduled recording/time-lapse is active. Wait until it completes.')
except sqlite3.DatabaseError as exc:
    sys.exit(f'Cannot verify existing database safely: {exc}')
PY
fi
if (( EXISTING )) && [[ -e "$DATA/status.json" ]]; then
 python3 - "$DATA/status.json" <<'PY'
import json,sys
try: status=json.load(open(sys.argv[1])).get('state','').lower()
except (OSError,ValueError):status=''
if status in ('recording','capturing','rendering','archiving','finalising'):
    sys.exit('Recorder is actively writing media. Wait for it to finish before upgrading.')
PY
fi
if (( ! EXISTING )); then
  (( $(df -Pm / | awk 'NR==2{print $4}') > 2600 )) || fail 'At least 2.6 GB free required for a new installation.'
  info 'Installing camera/dashboard dependencies'
  apt-get update
  apt-cache show python3-picamera2 >/dev/null 2>&1 || \
    fail 'This operating system has no python3-picamera2 package. Enable the compatible camera repository or use Raspberry Pi OS; no application has been installed.'
  apt-get install -y ca-certificates curl gnupg python3-picamera2 python3-opencv \
    python3-numpy python3-flask python3-cryptography gunicorn ffmpeg sqlite3
else
  info 'Upgrading an existing installation; preserving its packages and proxy'
  # Existing installs may lack the cryptography package needed by email/push/backups.
  python3 -c 'import flask,werkzeug,cryptography' >/dev/null 2>&1 || \
    fail 'Python Flask/Werkzeug/cryptography missing; install required Raspberry Pi OS packages before upgrading. No application changes made.'
fi
# Do not reset an existing login, configuration, database, media or credentials.
if (( EXISTING )); then
  SERVICE_USER=$(systemctl show -p User --value uap-dashboard.service)
  [[ -n "$SERVICE_USER" && "$SERVICE_USER" != root ]] || fail 'Cannot safely determine existing dashboard service user.'
else
  SERVICE_USER=uapdetector
  id -u "$SERVICE_USER" >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin --user-group "$SERVICE_USER"
  for g in video render; do getent group "$g" >/dev/null && usermod -aG "$g" "$SERVICE_USER"; done
fi
SERVICE_GROUP=$(id -gn "$SERVICE_USER")
BACKUP=''
if (( EXISTING )); then
  BACKUP="$BACKUP_ROOT/v${VERSION}-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  info "Backing up application, system configuration and database to $BACKUP"
  install -d -m 0700 "$BACKUP"
  cp -a "$APP" "$BACKUP/uap"
  [[ ! -d "$ETC" ]] || cp -a "$ETC" "$BACKUP/etc"
  if [[ -f "$DATA/events.sqlite3" ]]; then
    python3 - "$DATA/events.sqlite3" "$BACKUP/events.sqlite3" <<'PY'
import sqlite3,sys
with sqlite3.connect(sys.argv[1],timeout=10) as src:
    with sqlite3.connect(sys.argv[2]) as dst:src.backup(dst)
PY
    chmod 0600 "$BACKUP/events.sqlite3"
  fi
fi
DETECTOR_CHANGED=1
if [[ -f "$APP/detector.py" ]] && cmp -s 'uap/detector.py' "$APP/detector.py"; then DETECTOR_CHANGED=0; fi
ROLLED_BACK=0
rollback(){
  local rc=$?
  trap - EXIT
  if (( rc && EXISTING && ! ROLLED_BACK )); then
    ROLLED_BACK=1
    echo "Upgrade failed (exit $rc). Restoring application code from $BACKUP/uap" >&2
    rm -rf "$APP"
    cp -a "$BACKUP/uap" "$APP"
    # Leave the live database and credentials alone. A root-only SQLite backup is available.
    # Publish only the non-secret existing managed hostname on upgrades before the page is opened.
/usr/local/libexec/uap-network-worker publish
systemctl restart uap-dashboard.service || true
    echo "Database backup: $BACKUP/events.sqlite3 (not restored automatically)." >&2
  fi
  exit "$rc"
}
trap rollback EXIT
info 'Installing complete application and runtime files'
install -d -m 0755 /opt/uap-detector "$APP" "$ETC"
install -d -m 0750 -o "$SERVICE_USER" -g "$SERVICE_GROUP" "$DATA"
for dir in recordings thumbnails photography draft-previews observation-jobs power-requests network-requests software-update-requests; do
  install -d -m 0750 -o "$SERVICE_USER" -g "$SERVICE_GROUP" "$DATA/$dir"
done
# Pending IP changes survive reboot; this folder is ROOT-ONLY, not readable by dashboard.
install -d -m 0700 -o root -g root "$DATA/network-safety"
for file in uap/*; do [[ -f "$file" ]] && install -m 0644 "$file" "$APP/$(basename "$file")"; done
if (( ! EXISTING )); then
  python3 - "$ETC" <<'PY'
import json,secrets,sys
from pathlib import Path
from werkzeug.security import generate_password_hash
p=Path(sys.argv[1]);p.mkdir(parents=True,exist_ok=True)
password=secrets.token_urlsafe(22)
(p/'config.json').write_text('{}\n')
(p/'secret.key').write_text(secrets.token_hex(32)+'\n')
(p/'auth.json').write_text(json.dumps({'username':'admin','password_hash':generate_password_hash(password)})+'\n')
(p/'environment').write_text('UAP_HTTPS_ONLY=0\n')
for f in ('config.json','secret.key','auth.json','environment'): (p/f).chmod(0o640)
cred=Path('/root/uap-credentials.txt')
if not cred.exists():
    cred.write_text('UAP Detector administrator\nUsername: admin\nPassword: '+password+'\n')
    cred.chmod(0o600)
PY
  chown root:"$SERVICE_GROUP" "$ETC"/{config.json,secret.key,auth.json,environment}
fi
# Save official Moon Cheese-only systemd unit templates for optional diagnostics/repair.
# The routine install/upgrade still does NOT overwrite any existing custom unit.
install -d -m 0755 /opt/uap-detector/service-units
for unit in systemd/*.service systemd/*.timer systemd/*.path; do
  [[ -f "$unit" ]] && install -m 0644 "$unit" "/opt/uap-detector/service-units/$(basename "$unit")"
done
# Existing custom service units are never overwritten. A fresh install uses bundled units.
for name in uap-dashboard.service uap-detector.service uap-cleanup.service uap-cleanup.timer \
            uap-notifications.service uap-notifications.timer uap-power-action.service uap-power-action.path \
            uap-network-worker.service uap-network-worker.path uap-ddns.service uap-ddns.timer \
            uap-network-recovery.service uap-network-recovery.timer uap-software-update.service uap-software-update.path; do
  if [[ ! -e "/etc/systemd/system/$name" ]]; then
    install -m 0644 "systemd/$name" "/etc/systemd/system/$name"
  fi
done
# Historical Gunicorn issue: without a writable TMPDIR, dashboard could crash.
# systemd creates /run/uap-dashboard with correct ownership at service startup.
install -d -m 0755 /etc/systemd/system/uap-dashboard.service.d
cat >/etc/systemd/system/uap-dashboard.service.d/20-runtime-directory.conf <<'EOF'
[Service]
RuntimeDirectory=uap-dashboard
RuntimeDirectoryMode=0700
Environment=TMPDIR=/run/uap-dashboard
EOF
install -d -m 0755 /usr/local/libexec
install -m 0755 systemd/uap-power-action.py /usr/local/libexec/uap-power-action
install -m 0755 uap/network_worker.py /usr/local/libexec/uap-network-worker
install -m 0755 uap/software_update_worker.py /usr/local/libexec/uap-software-update
# Publish non-secret managed networking state immediately after an upgrade.
/usr/local/libexec/uap-network-worker publish || info 'Network state will appear after the next network worker run'
# The systemd unit for Cloudflare Tunnel is installed but only enabled by the wizard.
if [[ ! -e /etc/systemd/system/uap-cloudflared.service ]]; then
  install -m 0644 systemd/uap-cloudflared.service /etc/systemd/system/uap-cloudflared.service
fi
# Candidate connector only starts during an explicitly authorised hostname switch.
if [[ ! -e /etc/systemd/system/uap-cloudflared-candidate.service ]]; then
  install -m 0644 systemd/uap-cloudflared-candidate.service /etc/systemd/system/uap-cloudflared-candidate.service
fi
if [[ ! -e /usr/local/sbin/uapctl ]]; then
  cat >/usr/local/sbin/uapctl <<'EOF'
#!/usr/bin/env bash
case "${1:-status}" in
  status) systemctl --no-pager status uap-detector uap-dashboard || : ;;
  logs) exec journalctl -u uap-detector -u uap-dashboard -n 100 --no-pager -f ;;
  credentials) exec cat /root/uap-credentials.txt ;;
  *) echo 'Usage: sudo uapctl [status|logs|credentials]'; exit 2 ;;
esac
EOF
  chmod 0750 /usr/local/sbin/uapctl
fi
# Override old recovery service timeout on upgrades without replacing other custom units.
install -d -m 0755 /etc/systemd/system/uap-network-recovery.service.d
cat > /etc/systemd/system/uap-network-recovery.service.d/30-moon-cheese-timeout.conf <<'EOF'
[Service]
TimeoutStartSec=240
EOF
systemctl daemon-reload
info 'Activating dashboard and background services'
systemctl enable uap-dashboard.service uap-detector.service >/dev/null
systemctl enable --now uap-cleanup.timer uap-notifications.timer uap-power-action.path uap-network-worker.path uap-network-recovery.timer uap-software-update.path >/dev/null
systemctl restart uap-dashboard.service
# The detector engine in v0.9.9.2 is unchanged in v0.9.9.3; no camera restart then.
if (( ! EXISTING )); then
  systemctl start uap-detector.service
elif (( DETECTOR_CHANGED )); then
  info 'Earlier recorder version detected; restarting the camera service to load its updated engine'
  systemctl restart uap-detector.service
else
  echo 'Camera recorder unchanged: leaving its running service uninterrupted.'
fi
READY=0
for n in $(seq 1 40); do
  if curl -fsS --max-time 2 http://127.0.0.1:8000/healthz >/dev/null 2>&1; then READY=1;break;fi
  sleep 1
done
if (( ! READY )); then journalctl -u uap-dashboard.service -n 40 --no-pager >&2 || :;fail 'Dashboard health check failed; see backup and logs.';fi
trap - EXIT
NPM_RESULT='Not configured (existing installation preserved).'
if (( ! EXISTING )); then
  NPM_RESULT='Bundled NPM not requested (use external access or configure later).'
fi
# NPM is installed on fresh machines only and is NEVER altered on upgrades.
if (( ! EXISTING )) && [[ ${UAP_INSTALL_NPM:-1} == 1 ]]; then
  info 'Installing optional Nginx Proxy Manager container (local administration only)'
  NPM_RESULT='Installation was requested; check Docker service status.'
  if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    install -d -m 0755 /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker-uap.asc
    chmod 0644 /etc/apt/keyrings/docker-uap.asc
    cat > /etc/apt/sources.list.d/uap-docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: ${VERSION_CODENAME}
Components: stable
Architectures: arm64
Signed-By: /etc/apt/keyrings/docker-uap.asc
EOF
    if dpkg-query -W -f='${Status}' docker.io 2>/dev/null | grep -q 'install ok installed'; then
      echo 'Existing distribution Docker detected. Skipping Docker replacement to protect other containers.' >&2
    else
      apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
  fi
  if docker compose version >/dev/null 2>&1; then
    systemctl enable --now docker
    install -d -m 0700 /opt/uap-detector/npm /opt/uap-detector/npm-data /opt/uap-detector/npm-letsencrypt
    install -m 0644 npm/compose.yaml /opt/uap-detector/npm/compose.yaml
    install -m 0644 npm/provision_npm.py /opt/uap-detector/npm/provision_npm.py
    if [[ ! -f /opt/uap-detector/npm/.env ]]; then
      python3 - <<'PY'
import secrets,os
from pathlib import Path
path=Path('/opt/uap-detector/npm/.env')
email=os.environ.get('UAP_NPM_ADMIN_EMAIL','admin@uap-detector.local')
assert '\n' not in email and '\r' not in email and '@' in email
password=secrets.token_urlsafe(25)
path.write_text('NPM_ADMIN_EMAIL='+email+'\nNPM_ADMIN_PASSWORD='+password+'\n')
path.chmod(0o600)
cred=Path('/root/uap-credentials.txt')
with cred.open('a') as f:f.write('\nLocal NPM username: '+email+'\nLocal NPM password: '+password+'\n')
PY
    fi
    ( cd /opt/uap-detector/npm && docker compose --env-file .env up -d ) || \
      echo 'WARNING: NPM container could not start. Dashboard remains installed; see Docker logs.' >&2
    if [[ -n ${UAP_DOMAIN:-} ]]; then
      if [[ ${UAP_DOMAIN} =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]{2,252}$ ]]; then
        (cd /opt/uap-detector/npm && set -a && source ./.env && set +a && UAP_DOMAIN="$UAP_DOMAIN" python3 provision_npm.py) || \
          echo 'WARNING: NPM domain provisioning did not complete; configure it locally later.' >&2
      else echo 'WARNING: UAP_DOMAIN invalid; NPM domain provisioning skipped.' >&2;fi
    fi
    NPM_RESULT='Local NPM: 127.0.0.1:8181 (SSH tunnel required); HTTP proxy: port 8080. Cloudflare DNS, TLS and router forwarding need configuration.'
  else
    NPM_RESULT='WARNING: Docker Compose unavailable; bundled NPM not installed. The dashboard remains operational.'
    echo "$NPM_RESULT" >&2
  fi
fi
# Official icon is also available to desktop application launchers.
install -d -m 0755 /usr/share/icons/hicolor/192x192/apps
install -m 0644 uap/moon-cheese-192.png /usr/share/icons/hicolor/192x192/apps/moon-cheese.png
# Desktop app-menu links use localhost, independent of router-assigned LAN IP.
if [[ -d /usr/share/applications ]]; then
  cat >/usr/share/applications/moon-cheese.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Moon Cheese Detector
Icon=moon-cheese
Comment=Open the detector dashboard on this Raspberry Pi
Exec=xdg-open http://127.0.0.1:8000/
Terminal=false
Categories=Network;Utility;
DESKTOP
  if [[ -f /opt/uap-detector/npm/compose.yaml ]]; then
    cat >/usr/share/applications/moon-cheese-npm.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Moon Cheese — Local NPM
Icon=moon-cheese
Comment=Open the private local Nginx Proxy Manager administrator
Exec=xdg-open http://127.0.0.1:8181/
Terminal=false
Categories=Network;Utility;
DESKTOP
  fi
  # Optional actual Desktop icons for Pi OS Desktop accounts; never overwrite
  # any user-created shortcut. On Pi OS Lite there is no Desktop directory.
  for desk in /home/*/Desktop; do
    [[ -d "$desk" ]] || continue
    owner_uid=$(stat -c '%u' "$desk")
    owner_gid=$(stat -c '%g' "$desk")
    if [[ ! -e "$desk/Moon Cheese Detector.desktop" ]]; then
      install -m 0755 /usr/share/applications/moon-cheese.desktop "$desk/Moon Cheese Detector.desktop"
      chown "$owner_uid:$owner_gid" "$desk/Moon Cheese Detector.desktop"
    fi
    if [[ -f /usr/share/applications/moon-cheese-npm.desktop && ! -e "$desk/Moon Cheese Local NPM.desktop" ]]; then
      install -m 0755 /usr/share/applications/moon-cheese-npm.desktop "$desk/Moon Cheese Local NPM.desktop"
      chown "$owner_uid:$owner_gid" "$desk/Moon Cheese Local NPM.desktop"
    fi
  done
fi
# Print access and credential details AFTER all optional installation steps.
info "Moon Cheese UAP Detector v$VERSION — installation complete"
if (( EXISTING )); then
  echo "Upgraded/repaired existing installation. Root-only application backup: $BACKUP"
  echo 'Existing users, media, settings, SMTP, Web Push and network configuration preserved.'
  echo 'To view the ORIGINAL installation credentials (if retained): sudo uapctl credentials'
else
  echo 'FIRST ADMINISTRATOR LOGIN: run sudo uapctl credentials to view the generated username and password.'
  echo 'Keep these credentials private; this command shows the ORIGINAL password, not subsequent password changes.'
fi
echo 'Local dashboard addresses:'
if command -v ip >/dev/null 2>&1; then
  ip -o -4 addr show scope global | awk '$2 !~ /^(docker|br-|veth|virbr|tun|tap)/ {split($4,a,"/");print "  http://" a[1] ":8000 (" $2 ")"}' | sort -u
else
  echo '  http://DEVICE-IP:8000 (find the assigned LAN IP on your router)'
fi
echo "Optional proxy: $NPM_RESULT"
echo 'First-run camera/configuration instructions: open the dashboard and read Help.'
printf '\nFinished. Read README.md for installation and deployment details.\n'
