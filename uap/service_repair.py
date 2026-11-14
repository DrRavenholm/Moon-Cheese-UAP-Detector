#!/usr/bin/env python3
"""Read-only diagnostics and opt-in repair of Moon Cheese-owned systemd unit files.

No third-party units or network configuration are touched. Caller must opt in to
--apply; every changed unit file is backed up first. No service is restarted.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path('/opt/uap-detector/service-units')
TARGET = Path('/etc/systemd/system')
BACKUPS = Path('/var/backups/uap-detector/service-units')
ALLOWED = (
    'uap-dashboard.service', 'uap-detector.service',
    'uap-cleanup.service', 'uap-cleanup.timer',
    'uap-notifications.service', 'uap-notifications.timer',
    'uap-power-action.service', 'uap-power-action.path',
    'uap-network-worker.service', 'uap-network-worker.path',
    'uap-ddns.service', 'uap-ddns.timer',
    'uap-network-recovery.service', 'uap-network-recovery.timer',
    'uap-software-update.service', 'uap-software-update.path',
    'uap-cloudflared.service', 'uap-cloudflared-candidate.service',
)


def inspect(source=SOURCE, target=TARGET):
    result = {}
    for name in ALLOWED:
        a, b = source / name, target / name
        if not a.is_file() or a.is_symlink():
            raise RuntimeError(f'Missing or unsafe bundled Moon Cheese service template: {name}')
        if b.is_symlink():
            result[name] = 'symlink (manual investigation needed)'
        elif not b.is_file():
            result[name] = 'missing'
        elif hashlib.sha256(a.read_bytes()).digest() == hashlib.sha256(b.read_bytes()).digest():
            result[name] = 'ok'
        else:
            result[name] = 'modified'
    return result


def apply(items, source=SOURCE, target=TARGET, backups=BACKUPS):
    if os.geteuid() != 0:
        raise RuntimeError('Run this operation with sudo on the Raspberry Pi.')
    # No deletion or replacement of deliberately linked units, or modifications to drop-ins.
    if any(value.startswith('symlink') for value in items.values()):
        raise RuntimeError('One or more service files are symlinks. Inspect those manually; nothing changed.')
    changed = [name for name, state in items.items() if state != 'ok']
    if not changed:
        return 'All Moon Cheese unit templates already match; no repair needed.'
    folder = backups / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}')
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    restored = []
    try:
        for name in changed:
            current = target / name
            if current.exists():
                shutil.copy2(current, folder / name)
            else:
                (folder / f'{name}.missing').write_text('Missing before repair\n')
            temporary = target / f'.{name}.moon-cheese-{os.getpid()}'
            try:
                with temporary.open('xb') as out:
                    out.write((source / name).read_bytes())
                    out.flush()
                    os.fsync(out.fileno())
                os.chmod(temporary, 0o644)
                os.replace(temporary, current)
                restored.append(name)
            finally:
                temporary.unlink(missing_ok=True)
        subprocess.run(['systemctl', 'daemon-reload'], check=True, timeout=30)
    except Exception:
        # Recover the units this invocation modified; keep all backups untouched.
        for name in reversed(restored):
            previous = folder / name
            if previous.exists():
                shutil.copy2(previous, target / name)
            else:
                (target / name).unlink(missing_ok=True)
        try:
            subprocess.run(['systemctl', 'daemon-reload'], check=True, timeout=30)
        except Exception:
            pass
        raise
    return ('Restored ' + ', '.join(changed) + '\nBackups: ' + str(folder) + '\n'
            'systemd reloaded. Running services were NOT restarted. Review services with '
            'sudo systemctl --no-pager status uap-detector uap-dashboard and restart only when idle.')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inspect or safely restore Moon Cheese service unit files only.')
    opts = parser.add_mutually_exclusive_group(required=True)
    opts.add_argument('--check', action='store_true', help='Compare installed Moon Cheese units (read-only)')
    opts.add_argument('--apply', action='store_true', help='Back up and restore Moon Cheese units; no restarts')
    args = parser.parse_args(argv)
    try:
        items = inspect()
        for name, state in items.items():
            print(f'{name}: {state}')
        print(apply(items) if args.apply else 'Read-only check complete. --apply backs up and restores Moon Cheese units only.')
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'Service repair: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
