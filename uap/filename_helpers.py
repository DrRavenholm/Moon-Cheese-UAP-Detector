"""Safe download names generated from observation metadata, never used as disk paths."""
import re
import unicodedata


def safe_title(title, limit=76):
    text = unicodedata.normalize('NFKD', str(title or 'Observation'))
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^A-Za-z0-9]+', '-', text).strip('-')[:limit].rstrip('-')
    return text or 'Observation'


def job_filename(job, stored_name):
    prefix = f"Time-lapse-{int(job['id'])}" if job['kind'] == 'timelapse' else f"Scheduled-Video-{int(job['id'])}"
    title = safe_title(job['title'])
    if stored_name == 'source-frames.zip' and job['kind'] == 'timelapse':
        return f'{prefix}-source-frames-{title}.zip'
    if stored_name == 'timelapse.mp4' and job['kind'] == 'timelapse':
        return f'{prefix}-Video-{title}.mp4'
    match = re.fullmatch(r'segment-(\d+)\.mp4', stored_name)
    if match and job['kind'] == 'scheduled_video':
        return f'{prefix}-Part-{int(match.group(1)):02d}-{title}.mp4'
    return stored_name


def photo_filename(photo_id, title, extension='jpg'):
    ext=extension.lower().lstrip('.')
    if ext not in ('jpg','jpeg','png'):ext='jpg'
    return f'Photo-{photo_id}-{safe_title(title)}.{ext}'
