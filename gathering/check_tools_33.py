#!/usr/bin/env python3
"""Run the reviewed offline tool checks; evidence only, never execute task labels."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent

def commands(n):
    jobs = []
    for folder in sorted((ROOT / f'line-{n}/tools').iterdir()):
        if not folder.is_dir():
            continue
        main = folder / (folder.name + '.py')
        test = folder / 'selftest.py'
        if test.exists():
            jobs.append((test, [], 0, 'check'))
        elif folder.name in ('workplan', 'gatecheck'):
            jobs.append((main, ['--self-test'], 0, 'check'))
        if (folder / 'demo.py').exists():
            jobs.append((folder / 'demo.py', [], 0, 'demo'))
        elif (folder / 'swarm_demo.py').exists():
            jobs.append((folder / 'swarm_demo.py', [], 0, 'demo'))
        elif n == 1 and folder.name != 'budgetpath':
            jobs.append((main, ['--demo'], 0, 'demo'))
        elif n in (3, 4):
            jobs.append((main, ['demo'], 1 if folder.name == 'rewardcompare' else 0, 'demo'))
        elif folder.name == 'budgetpath':
            jobs.append((main, [str(folder / 'example.json')], 0, 'demo'))
        elif folder.name == 'zipbudget':
            archive = ROOT / 'test/scratch/gathering33/budget.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('kept.txt', 'hello')
            jobs.append((main, [str(archive), '--max-files', '2', '--max-bytes', '20'], 0, 'demo'))
            jobs.append((main, [str(archive), '--max-bytes', '1'], 1, 'refusal'))
    return jobs

def run_line(n):
    rows = []
    for script, args, expected, kind in commands(n):
        cmd = [sys.executable, '-B', str(script.relative_to(ROOT)), *args]
        try:
            done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
            text = done.stdout + done.stderr
            match = re.search(r'Ran (\d+) tests?', text)
            rows.append(dict(line=n, kind=kind, command=cmd[2:], exit=done.returncode,
                             expected_exit=expected, passed=done.returncode == expected,
                             unittest_cases=int(match.group(1)) if match else 0,
                             stdout_sha256=hashlib.sha256(done.stdout.encode()).hexdigest(),
                             evidence=text[-450:]))
        except subprocess.TimeoutExpired:
            rows.append(dict(line=n, command=cmd[2:], passed=False, error='60 second timeout'))
    return rows

def main():
    (ROOT / 'test/scratch/gathering33').mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = [row for result in pool.map(run_line, range(1, 5)) for row in result]
    # Keep every evidence document within the assignment's 100 KB cap.
    raw = json.dumps(rows, indent=2) + '\n'
    if len(raw.encode()) > 100000:
        raise ValueError('evidence exceeds byte cap')
    (ROOT / 'gathering/check-results-33.json').write_text(raw)
    for n in range(1, 5):
        group = [r for r in rows if r['line'] == n]
        print('Line', n, len(group), 'commands;', sum(r['unittest_cases'] for r in group),
              'unittest cases;', sum(not r['passed'] for r in group), 'failures')
    for row in rows:
        if not row['passed']:
            print(json.dumps(row, indent=2))
    return int(not all(r['passed'] for r in rows))

if __name__ == '__main__':
    sys.exit(main())
