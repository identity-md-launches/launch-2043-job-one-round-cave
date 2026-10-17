#!/usr/bin/env python3
"""Read-only structural and scope checks for this round's delivery."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jpeg_size(data):
    assert data[:2] == b'\xff\xd8' and data[-2:] == b'\xff\xd9'
    i = 2
    while i < len(data):
        assert data[i] == 255
        while data[i] == 255:
            i += 1
        marker = data[i]
        i += 1
        length = int.from_bytes(data[i:i+2], 'big')
        if marker in (0xc0, 0xc1, 0xc2):
            height, width = struct.unpack('>HH', data[i+3:i+7])
            return width, height
        i += length
    raise AssertionError('JPEG dimensions missing')


r = json.loads(Path('line-4/review-33.json').read_text())
record = json.loads(Path('dist/line-4/33.json').read_text())
assert set(record) == {'name', 'image', 'attributes'}
assert record['image'] == 'https://api.imd.fun/artifacts/' + sha(r['wall'])
assert sha(r['wall']) == sha(r['canonical_wall']) == r['sha256']
png = Path(r['wall']).read_bytes()
assert png[:8] == b'\x89PNG\r\n\x1a\n'
assert struct.unpack('>II', png[16:24]) == (1254, 1254)
assert png[24:26] == bytes((8, 2))
assert jpeg_size(Path(r['preview']).read_bytes()) == (512, 512)
assert sha(r['preview']) == r['preview_sha256']
assert len(Path(r['preview']).read_bytes()) < 100000
assert r['pixels_changed_outside_addition'] == 0 and r['changed_pixels'] > 500
assert sha('artifacts/line-4/wall-v13.png') == r['ancestor_sha256']
assert len(list(Path('dist/line-4').glob('[0-9][0-9].json'))) == 33
assert [a['trait_type'] for a in record['attributes']] == [
    'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing']
assert record['attributes'][2]['value'] == 33
# Only these two tracked paths should change; all older records and GOAL.md stay.
tracked = subprocess.check_output(['git', 'diff', '--name-only'], text=True).splitlines()
assert set(tracked) == {'artifacts/line-4/wall.png', 'line-4/USED.md'}, tracked
new = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
allowed = ('line-4/', 'artifacts/line-4/', 'dist/line-4/')
assert all(name.startswith(allowed) for name in new), new
assert all(Path(name).stat().st_size <= 100000 for name in new if not name.startswith('artifacts/'))
results = json.loads(Path('line-4/check-results-33.json').read_text())
assert len(results['suites']) == 13 and all(s['exit'] == 0 for s in results['suites'])
assert results['live']['matches_capture'] and not results['live']['comparison']['findings']
report = {'passed': True, 'suites_passed': 13, 'wall_dimensions': [1254, 1254],
          'wall_format': 'RGB PNG', 'preview_dimensions': [512, 512],
          'preview_format': 'JPEG', 'record_number': 33,
          'goal_and_older_records_unchanged': True, 'scope_check_passed': True,
          'visual_limits': r['unmet_visual_requirements']}
print(json.dumps(report, indent=2))
