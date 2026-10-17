#!/usr/bin/env python3
"""Reproduce round 33 checks; optional public-description GET only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('round33_paramcheck', ROOT / 'tools/paramcheck/paramcheck.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    results = []
    for name in ('apidelta', 'boundcheck', 'multiplecheck', 'constcheck', 'uniquecheck',
                 'dependcheck', 'authcheck', 'schemecheck', 'oauthcheck', 'servercheck', 'idcheck', 'headercheck', 'paramcheck'):
        script = ROOT / 'tools' / name / 'selftest.py'
        run = subprocess.run([sys.executable, '-B', str(script)], text=True,
                             capture_output=True, timeout=90)
        results.append({'tool': name, 'exit': run.returncode,
                        'stdout': run.stdout, 'stderr': run.stderr})
    capture = ROOT / 'tools/apidelta/imd-openapi.json'
    old, digest = module.api.load(capture)
    report = {'suites': results, 'demo': module.demo(),
              'unchanged_capture': module.compare(old, old), 'capture_sha256': digest}
    if args.live:
        request = urllib.request.Request('https://api.imd.fun/openapi.json',
                                         headers={'User-Agent': 'Pepeolithic-ParamCheck/33.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(module.api.MAX_BYTES + 1)
        module.api.require(len(raw) <= module.api.MAX_BYTES, 'live input exceeds 1 MiB')
        # Parse/validate before saving. No described operation is ever called.
        obj = json.loads(raw, object_pairs_hook=module.api.pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        module.api.validate(obj)
        module.api.require(len(raw) < 100000, 'live input exceeds delivery size limit')
        (ROOT / 'live-openapi-33.json').write_bytes(raw)
        report['live'] = {'sha256': hashlib.sha256(raw).hexdigest(),
                          'matches_capture': raw == capture.read_bytes(),
                          'comparison': module.compare(old, obj)}
    (ROOT / 'check-results-33.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'suites': len(results), 'failed': sum(r['exit'] != 0 for r in results),
                      'demo': report['demo']['counts'],
                      'capture_findings': len(report['unchanged_capture']['findings']),
                      'live': report.get('live')}, indent=2))
    return int(any(r['exit'] for r in results))


if __name__ == '__main__':
    sys.exit(main())
