#!/usr/bin/env python3
"""post_photos.py — import a blog post's photo into the game.

Blog posts (GitHub issue bodies) embed photos as GitHub asset URLs, either
markdown images or raw <img> tags. The first one is downloaded and rendered
as a 160×144 pixel-art print (tools/photo_pixelize.py) to
assets/photos/<post_id>.png. blog_to_npc.py records it on the post's dated
NPC state as "photo": "<post_id>", and the dialogue box hangs it in a frame
next to the author (src/DialogueManager.js).

Photos are strictly best-effort: any failure here (no deps, dead URL,
unreadable image) logs and returns None so the NPC placement still lands.
"""
import os
import re
import tempfile
import urllib.error
import urllib.request

# markdown ![alt](url) and raw <img src="url"> — GitHub asset URLs carry no
# file extension, so being declared as an image is the only signal we get
IMAGE_MD = re.compile(r'!\[[^\]]*\]\((https?://[^)\s]+)\)')
IMAGE_TAG = re.compile(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', re.IGNORECASE)

MAX_DOWNLOAD_BYTES = 30 * 1024 * 1024


def first_image_url(content):
    """The post's first embedded image URL (by position), or None."""
    matches = [m for m in
               list(IMAGE_MD.finditer(content or '')) +
               list(IMAGE_TAG.finditer(content or ''))
               if not m.group(1).lower().endswith('.svg')]
    if not matches:
        return None
    return min(matches, key=lambda m: m.start()).group(1)


def _fetch(url, token=None):
    headers = {'User-Agent': 'devhouse-game-pipeline'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise ValueError(f'image larger than {MAX_DOWNLOAD_BYTES} bytes')
    return data


def download(url):
    """Fetch the image bytes. Anonymous first (post assets are public on a
    public repo); one authenticated retry via GITHUB_TOKEN for private ones."""
    try:
        return _fetch(url)
    except urllib.error.HTTPError as e:
        token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if e.code in (403, 404) and token:
            return _fetch(url, token)
        raise


def import_post_photo(post, out_dir='assets/photos', dry_run=False):
    """Download + pixelize the post's first photo. Returns the photo id
    (the post id — assets/photos/<id>.png) or None."""
    url = first_image_url(post.get('content'))
    if not url:
        return None

    photo_id = str(post.get('post_id'))
    dest = os.path.join(out_dir, f'{photo_id}.png')
    if dry_run:
        print(f'  photo: would import {url} -> {dest}')
        return photo_id

    try:
        import photo_pixelize
    except ImportError as e:
        print(f'  photo: renderer unavailable ({e}) — '
              f'pip install -r tools/requirements-photos.txt — skipped')
        return None

    tmp_path = None
    try:
        data = download(url)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        from pathlib import Path
        photo_pixelize.crisp_pixelize(Path(tmp_path), Path(dest))
    except Exception as e:
        print(f'  photo: {url} failed ({type(e).__name__}: {e}) — skipped')
        return None
    finally:
        if tmp_path:
            os.unlink(tmp_path)

    print(f'  photo: {url} -> {dest}')
    return photo_id
