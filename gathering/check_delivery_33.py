#!/usr/bin/env python3
"""Check delivered bytes, gallery records, provenance and unchanged line trees."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def png(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    at = 8
    dimensions = None
    while at < len(raw):
        length = int.from_bytes(raw[at:at+4], 'big')
        kind = raw[at+4:at+8]
        payload = raw[at+8:at+8+length]
        crc = int.from_bytes(raw[at+8+length:at+12+length], 'big')
        assert zlib.crc32(kind+payload) & 0xffffffff == crc
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB',payload)
            assert width == height == 1254 and depth == 8 and color == 2
            assert (compression, filtering, interlace) == (0,0,0)
            dimensions = [width, height]
        at += 12 + length
        if kind == b'IEND':
            break
    assert dimensions and at == len(raw)
    return dimensions


def jpeg(path):
    raw = path.read_bytes()
    assert raw[:2] == b'\xff\xd8' and raw[-2:] == b'\xff\xd9'
    at = 2
    while at < len(raw):
        assert raw[at] == 255
        kind = raw[at+1]
        size = int.from_bytes(raw[at+2:at+4], 'big')
        if kind in (192, 193, 194):
            height, width = struct.unpack('>HH',raw[at+5:at+9])
            assert width == height == 512
            return [width,height]
        at += 2+size
    raise AssertionError('JPEG has no dimensions')


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.records = []
        self.sections = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and re.fullmatch(r'(line-[1-4]|gathering)/\d{2}\.json', a.get('href','')):
            self.records.append(a['href'])
        if tag == 'section':
            self.sections.append(a.get('id'))


def main():
    wall = ROOT/'artifacts/gathering/wall-v14.png'
    record = json.loads((ROOT/'dist/gathering/33.json').read_text())
    assert set(record) == {'name','image','attributes'}
    attrs = {a['trait_type']:a['value'] for a in record['attributes']}
    assert set(attrs) == {'Cave','Wall','Number','Left behind','Meaning','One thing'}
    assert (attrs['Cave'],attrs['Wall'],attrs['Number'],attrs['One thing']) == ('Lava','Gathering',33,'Gathering')
    assert record['image'] == 'https://api.imd.fun/artifacts/'+sha(wall.read_bytes())
    dimensions = png(wall)
    preview = ROOT/'dist/gathering/33.jpg'
    thumb_dimensions = jpeg(preview)
    assert preview.stat().st_size <= 100000
    preservation = json.loads((ROOT/'gathering/preservation-33.json').read_text())
    assert preservation['wall_sha256'] == sha(wall.read_bytes())
    assert preservation['pixels_changed_outside'] == 0
    assert (ROOT/'artifacts/gathering/wall.png').read_bytes() == wall.read_bytes()
    goals = json.loads((ROOT/'dist/goals.json').read_text())
    assert goals == [{'line':n,'goal':(ROOT/f'line-{n}/GOAL.md').read_text().strip()} for n in range(1,5)]
    parser = Gallery()
    page = (ROOT/'dist/index.html').read_text()
    parser.feed(page)
    assert parser.sections == ['line-1','line-2','line-3','line-4','gathering']
    expected = []
    painted = 0
    for folder in parser.sections:
        paths = sorted((ROOT/'dist'/folder).glob('[0-9][0-9].json'),reverse=True)
        for path in paths:
            item = json.loads(path.read_text())
            expected.append(folder+'/'+path.name)
            assert re.fullmatch(r'https://api\.imd\.fun/artifacts/[0-9a-f]{64}',item['image'])
            if item['name'] != 'Not painted yet':
                painted += 1
    assert sorted(parser.records) == sorted(expected)
    # Painted entries precede the future-slot links and are newest first per section.
    for folder in parser.sections:
        actual = [p for p in parser.records if p.startswith(folder+'/') and
                  json.loads((ROOT/'dist'/p).read_text())['name']!='Not painted yet']
        assert actual == sorted(actual,reverse=True)
    for target, info in json.loads((ROOT/'shared/api_bundle/SOURCES.json').read_text()).items():
        assert sha((ROOT/'shared/api_bundle'/target).read_bytes()) == info['sha256']
    files = {str(p.relative_to(ROOT)):sha(p.read_bytes()) for n in range(1,5)
             for p in (ROOT/f'line-{n}').rglob('*') if p.is_file()}
    digest = sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode())
    integrity = json.loads((ROOT/'gathering/line-integrity-33.json').read_text())
    assert digest == integrity['before_sha256'] == integrity['after_sha256'] and integrity['passed']
    for name in ('REPORT.md','COINS.md','README.md'):
        assert (ROOT/'gathering'/name).stat().st_size > 100
    assert (ROOT/'gathering/COINS.md').read_text().startswith('none\n')
    for path in [ROOT/'dist/index.html',ROOT/'dist/goals.json',preview,*
                 [ROOT/'gathering'/n for n in ('REPORT.md','README.md','check-results-33.json')]]:
        assert path.stat().st_size <= 100000, str(path)
    result = dict(passed=True,wall_sha256=sha(wall.read_bytes()),png_dimensions=dimensions,
                  jpeg_dimensions=thumb_dimensions,jpeg_bytes=preview.stat().st_size,
                  records=len(expected),painted=painted,line_files_unchanged=len(files),
                  unmet_visual_requirements=[],visual_review='Manual inspection recorded in REPORT.md; byte checks do not certify visual quality.')
    (ROOT/'gathering/delivery-check-33.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
