#!/usr/bin/env python3
"""An offline, SHA-approved ZIP handoff for hypothetical parameter wire changes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

import api_bundle


def demo():
    capture = Path(__file__).with_name('imd-openapi.json').read_bytes()
    old = json.loads(capture)
    old['paths']['/requests/quote']['post']['parameters'] = [{
        'name': 'workerTags', 'in': 'query', 'schema': {'type': 'array',
        'items': {'type': 'string'}}, 'style': 'form', 'explode': True}]
    new = copy.deepcopy(old)
    new['paths']['/requests/quote']['post']['parameters'][0]['explode'] = False
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='parameter-bundle-', dir=scratch) as directory:
        paths, hashes = [], []
        for name, doc in [('old', old), ('new', new)]:
            path = Path(directory) / (name + '.zip')
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr(zipfile.ZipInfo('docs/openapi.json'), json.dumps(doc))
            paths.append(path)
            hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
        args = dict(member='docs/openapi.json', old_sha256=hashes[0], new_sha256=hashes[1],
                    parameters=True, seconds=10)
        changed = api_bundle.compare(*paths, **args)
        unchanged = api_bundle.compare(paths[0], paths[0], member=args['member'],
                        old_sha256=hashes[0], new_sha256=hashes[0], parameters=True)
        assert unchanged['findings'] == []
        assert changed['status'] == 'breaking'
        assert any(f['code'] == 'parameter_wire_explode_changed' for f in changed['findings'])
        return dict(baseline_source='https://api.imd.fun/openapi.json',
                    baseline_sha256=hashlib.sha256(capture).hexdigest(),
                    trial='Hypothetical query-array encoding: workerTags=a&workerTags=b becomes workerTags=a,b.',
                    network_used=False, files_extracted=0,
                    unchanged_status=unchanged['status'], changed=changed)


if __name__ == '__main__':
    print(json.dumps(demo(), indent=2))
