# Blog-post photos

160×144 pixel-art prints of blog-post photos, one per post (`<post id>.png`),
written by `tools/blog_to_npc.py` → `tools/post_photos.py` →
`tools/photo_pixelize.py` (the crisp-pixelize renderer: 16 colours from the
photo's own palette, sparse dark outlines, face-aware cleanup).

An NPC's dated state references one as `"photo": "<post id>"` and the
dialogue box (`src/DialogueManager.js`) hangs it in a wooden frame beside the
author. This directory is committed (and this file keeps the path present so
the pipeline's `git add` always has a target).
