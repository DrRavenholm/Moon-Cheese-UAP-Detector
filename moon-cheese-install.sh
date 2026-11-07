#!/usr/bin/env bash
# Moon Cheese UAP Detector: GitHub Releases bootstrap installer.
# Downloads and verifies a public RELEASE ASSET, then runs its bundled install.sh.
# With no arguments selects latest stable; --prerelease TAG selects a named public prerelease.
# Does not contain or replace Moon Cheese's main installer.
# This bootstrap requires a publicly accessible GitHub repository and published release.
set -Eeuo pipefail

OWNER='DrRavenholm'
REPOSITORY='Moon-Cheese-UAP-Detector'
API_BASE="https://api.github.com/repos/${OWNER}/${REPOSITORY}/releases"
RELEASE_MODE='stable'
API="${API_BASE}/latest"

if [[ ${1:-} == '--help' || ${1:-} == '-h' ]]; then
  printf '%s\n' 'Moon Cheese UAP Detector GitHub installer' \
    'Usage: sudo bash moon-cheese-install.sh [--prerelease vX.Y.Z]' \
    'By default downloads the latest stable release. With --prerelease, downloads' \
    'the named publicly published test release (no GitHub login needed).' \
    'Verifies its SHA-256 digest,' \
    'extracts the complete package, and runs its original install.sh.' \
    'A public repository and published release are required; private and draft' \
    'assets cannot be downloaded anonymously.'
  exit 0
fi

if [[ $# -eq 2 && $1 == '--prerelease' ]]; then
  RELEASE_TAG="$2"
  if [[ ! $RELEASE_TAG =~ ^v[0-9]+(\.[0-9]+){2,5}$ ]]; then
    echo 'The prerelease tag must be a version, such as v0.9.9.5.3.' >&2
    exit 2
  fi
  RELEASE_MODE='prerelease'
  API="${API_BASE}/tags/${RELEASE_TAG}"
elif [[ $# -ne 0 ]]; then
  echo 'Unknown argument. Try --help.' >&2
  exit 2
fi
[[ $EUID -eq 0 ]] || { echo 'Please run this installer using sudo.' >&2; exit 1; }

for command_name in curl python3 tar sha256sum mktemp; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Missing dependency: %s\n' "$command_name" >&2
    exit 1
  }
done

WORK_DIR="$(mktemp -d -t moon-cheese-download.XXXXXXXX)"
trap 'rm -rf -- "$WORK_DIR"' EXIT

if [[ $RELEASE_MODE == 'stable' ]]; then
  printf '%s\n' 'Checking GitHub for the latest stable Moon Cheese release...'
else
  printf 'Checking GitHub for published Moon Cheese prerelease %s...\n' "$RELEASE_TAG"
fi
if ! curl --fail --silent --show-error --location --retry 2 \
     --connect-timeout 10 --max-time 45 \
     --header 'Accept: application/vnd.github+json' \
     --header 'User-Agent: Moon-Cheese-Installer' \
     --output "$WORK_DIR/release.json" "$API"; then
  cat >&2 <<'MSG'
Could not retrieve the selected Moon Cheese release.
The repository may still be private, or the requested release may not be published.
No installation changes were made.
MSG
  exit 1
fi

# The release must contain the exact versioned *installer package* asset,
# not the automatic source code archive created by GitHub.
if ! python3 - "$WORK_DIR/release.json" "$RELEASE_MODE" "${RELEASE_TAG:-}" > "$WORK_DIR/release-fields.txt" <<'PY'
import json
import re
import sys
from urllib.parse import urlsplit

try:
    with open(sys.argv[1], encoding='utf-8') as handle:
        release = json.load(handle)
    mode, requested_tag = sys.argv[2], sys.argv[3]
    if release.get('draft'):
        raise ValueError('Draft releases are not installable.')
    if mode == 'stable' and release.get('prerelease'):
        raise ValueError('The latest-stable endpoint returned a prerelease.')
    if mode == 'prerelease' and not release.get('prerelease'):
        raise ValueError('The requested release is not marked as a prerelease.')
    tag = release['tag_name']
    if mode == 'prerelease' and tag != requested_tag:
        raise ValueError('The returned prerelease tag does not match the requested tag.')
    if not isinstance(tag, str) or not re.fullmatch(r'v\d+(?:\.\d+){2,5}', tag):
        raise ValueError('The release tag is not a supported version number.')
    package_name = 'moon-cheese-uap-detector-' + tag + '.tar.gz'
    matches = [a for a in release.get('assets', []) if a.get('name') == package_name]
    if len(matches) != 1:
        raise ValueError('The release is missing its complete versioned installation archive.')
    asset = matches[0]
    url = asset['browser_download_url']
    parsed = urlsplit(url)
    expected_path = '/DrRavenholm/Moon-Cheese-UAP-Detector/releases/download/' + tag + '/' + package_name
    if parsed.scheme != 'https' or parsed.hostname != 'github.com' or parsed.path != expected_path:
        raise ValueError('The installation asset has an unexpected download address.')
    digest = asset.get('digest') or ''
    if not re.fullmatch(r'sha256:[a-fA-F0-9]{64}', digest):
        raise ValueError('GitHub did not supply a SHA-256 digest for the release asset.')
    print(tag)
    print(package_name)
    print(url)
    print(digest.split(':', 1)[1].lower())
except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
    print('Invalid or incomplete GitHub release: ' + str(exc), file=sys.stderr)
    sys.exit(1)
PY
then
  echo 'No installation changes were made.' >&2
  exit 1
fi

mapfile -t RELEASE_FIELDS < "$WORK_DIR/release-fields.txt"
TAG="${RELEASE_FIELDS[0]}"
PACKAGE="${RELEASE_FIELDS[1]}"
DOWNLOAD_URL="${RELEASE_FIELDS[2]}"
EXPECTED_SHA256="${RELEASE_FIELDS[3]}"

printf 'Downloading %s (%s)...\n' "$PACKAGE" "$TAG"
curl --fail --silent --show-error --location --retry 3 --retry-delay 2 \
  --connect-timeout 10 --max-time 180 \
  --output "$WORK_DIR/$PACKAGE" "$DOWNLOAD_URL"

printf 'Verifying downloaded package SHA-256...\n'
printf '%s  %s\n' "$EXPECTED_SHA256" "$WORK_DIR/$PACKAGE" | sha256sum --check --status || {
  echo 'The release package failed SHA-256 verification. Installation cancelled.' >&2
  exit 1
}

# Reject absolute paths, traversal, links and special device nodes before extraction.
if ! python3 - "$WORK_DIR/$PACKAGE" > "$WORK_DIR/root.txt" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

try:
    with tarfile.open(sys.argv[1], 'r:gz') as archive:
        members = archive.getmembers()
        if not members or len(members) > 10000:
            raise ValueError('Archive is empty or has too many files.')
        roots = set()
        names = set()
        for member in members:
            raw = member.name.rstrip('/')
            path = PurePosixPath(raw)
            if (not raw or path.is_absolute() or
                    any(part in ('..', '.') for part in raw.split('/')) or
                    not (member.isfile() or member.isdir())):
                raise ValueError('Unsafe archive entry detected.')
            if raw in names:
                raise ValueError('Duplicate archive path detected.')
            names.add(raw)
            roots.add(path.parts[0])
        if len(roots) != 1:
            raise ValueError('Archive must contain one application directory.')
        root = next(iter(roots))
        if root + '/install.sh' not in names:
            raise ValueError('Archive does not contain its installer.')
        if not next(m for m in members if m.name == root + '/install.sh').isfile():
            raise ValueError('The installer is not a regular file.')
        print(root)
except (OSError, ValueError, tarfile.TarError) as exc:
    print('Package structure validation failed: ' + str(exc), file=sys.stderr)
    sys.exit(1)
PY
then
  echo 'No installation changes were made.' >&2
  exit 1
fi

ROOT="$(cat "$WORK_DIR/root.txt")"
mkdir -p "$WORK_DIR/extracted"
tar -xzf "$WORK_DIR/$PACKAGE" -C "$WORK_DIR/extracted" \
  --no-same-owner --no-same-permissions

printf '%s\n' 'Running the original Moon Cheese installation / upgrade / repair script...'
cd "$WORK_DIR/extracted/$ROOT"
bash ./install.sh
