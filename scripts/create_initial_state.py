#!/usr/bin/env python3
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('notify_instagram', str(Path(__file__).resolve().parents[1] / 'notify_instagram.py'))
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)

posts = notify.get_latest_posts(limit=1)
if not posts:
    print('No posts found; no state file created.')
    sys.exit(0)
else:
    last = posts[0]['shortcode']
    state = {'last_shortcode': last}
    with open('last_seen.json', 'w', encoding='utf-8') as f:
        json.dump(state, f)
    print('Wrote last_seen.json with shortcode:', last)
