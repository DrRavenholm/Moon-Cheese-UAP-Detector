"""Measured still-image storage estimate; a safety floor is maintained during capture."""
import shutil
import zipfile
from pathlib import Path
from common import DATA

GIB=1024**3
MIB=1024**2


def per_frame_bytes(root=None):
    """Read ZIP central-directory sizes; no photo decompressing or SD writes."""
    root=Path(root or DATA/'observation-jobs')
    recent=[]
    if root.is_dir():
        for path in root.glob('*/source-frames.zip'):
            if path.is_file() and not path.is_symlink():
                try:recent.append((path.stat().st_mtime,path))
                except OSError:pass
    samples=[]
    for _,path in sorted(recent,reverse=True)[:4]:
        try:
            with zipfile.ZipFile(path) as z:
                sizes=[info.file_size for info in z.infolist() if info.filename.lower().endswith(('.jpg','.jpeg'))]
                if len(sizes)>=10:samples.append(sum(sizes)/len(sizes))
        except (OSError,zipfile.BadZipFile):continue
    # Fallback on an ordinary full-resolution JPEG, not the 18 MB worst case.
    typical=max(2*MIB,min(9*MIB,(sum(samples)/len(samples))*1.6)) if samples else 3*MIB
    return round(typical),len(samples)


def estimate_space(frames=0,duration=0,kind='timelapse',free=None,root=None):
    per_frame,samples=per_frame_bytes(root) if kind=='timelapse' else (0,0)
    if kind=='timelapse':
        # loose JPEGs + essentially uncompressed ZIP + MP4 and temp overhead
        estimated=int(frames*(2*per_frame+0.5*MIB)+256*MIB)
    else:
        estimated=int(duration*650000+256*MIB)
    reserve=2*GIB
    available=shutil.disk_usage(DATA).free if free is None else free
    return {'bytes':estimated,'reserve':reserve,'required':estimated+reserve,
            'available':available,'bytes_per_frame':per_frame,'samples':samples,
            'fits':available>=estimated+reserve}
