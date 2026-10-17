#!/usr/bin/env python3
"""Check the standalone shared handoff and the saved public description, offline."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    scratch = ROOT / 'test/scratch/gathering33/isolation'
    bundle_root = scratch / 'shared/api_bundle'
    shutil.copytree(ROOT / 'shared/api_bundle', bundle_root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    rows = []
    for name in ('selftest.py', 'parameter_selftest.py', 'demo.py', 'server_demo.py', 'parameter_demo.py'):
        result = subprocess.run([sys.executable, '-B', str(bundle_root / name)],
                            cwd=scratch, capture_output=True, text=True, timeout=60)
        rows.append(dict(command=name, exit=result.returncode, passed=result.returncode == 0,
                    evidence=(result.stderr or result.stdout)[-800:]))
    sys.path.insert(0, str(bundle_root))
    spec = importlib.util.spec_from_file_location('gathering33_bundle', bundle_root / 'api_bundle.py')
    bundle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bundle)
    snapshots = [ROOT/'shared/api_bundle/imd-openapi.json', ROOT/'gathering/imd-openapi-current-33.json']
    archives, hashes = [], []
    for n, capture in enumerate(snapshots):
        archive = scratch / f'capture-{n}.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr(zipfile.ZipInfo('docs/openapi.json'), capture.read_bytes())
        archives.append(archive)
        hashes.append(hashlib.sha256(archive.read_bytes()).hexdigest())
    live = bundle.compare(*archives, member='docs/openapi.json', old_sha256=hashes[0],
                           new_sha256=hashes[1], parameters=True, seconds=10)
    live.update(source='https://api.imd.fun/openapi.json',
                retrieval='Read-only GET with User-Agent Pepeolithic-Gathering/33.0 on 2026-10-17; no described API operation called.',
                capture_sha256=hashlib.sha256(snapshots[1].read_bytes()).hexdigest(),
                capture_bytes=snapshots[1].stat().st_size)
    (ROOT/'gathering/live-check-33.json').write_text(json.dumps(live, indent=2)+'\n')
    (ROOT/'gathering/shared-check-results-33.json').write_text(json.dumps(rows, indent=2)+'\n')
    for row in rows:
        print(row['command'], 'PASS' if row['passed'] else 'FAIL', row['evidence'][-150:])
    print('Saved public API comparison:',live['status'],live['operations_compared'],'operations')
    return int(not all(r['passed'] for r in rows) or live['status']!='no_detected_breakage')

if __name__ == '__main__':
    sys.exit(main())
