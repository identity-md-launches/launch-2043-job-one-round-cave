"""Exercise the parameter analyzer through the real approved-ZIP boundary."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import api_bundle as bundle


class ParameterBundleTests(unittest.TestCase):
    def setUp(self):
        root = Path('test/scratch')
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='parameter-tests-', dir=root)
        self.root = Path(self.temp.name)
        self.doc = {'openapi': '3.1.0', 'paths': {'/items': {'get': {
            'operationId': 'listItems', 'parameters': [{
                'name': 'tags', 'in': 'query', 'schema': {
                    'type': 'array', 'items': {'type': 'string'}}}],
            'responses': {'200': {'description': 'OK', 'headers': {
                'X-Receipt': {'required': True, 'schema': {'type': 'string'}}}}}}}}}

    def tearDown(self):
        self.temp.cleanup()

    def archive(self, name, doc):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr(zipfile.ZipInfo('docs/openapi.json'), json.dumps(doc))
            z.writestr(zipfile.ZipInfo('inert.py'), 'raise RuntimeError("do not execute")')
        return path

    def compare(self, old, new, **kwargs):
        a, b = self.archive('old.zip', old), self.archive('new.zip', new)
        return bundle.compare(a, b, member='docs/openapi.json', parameters=True,
                   old_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),
                   new_sha256=hashlib.sha256(b.read_bytes()).hexdigest(), **kwargs)

    def codes(self, result):
        return {row['code'] for row in result['findings']}

    def test_approved_unchanged_capture_and_no_extraction(self):
        capture = json.loads(Path(__file__).with_name('imd-openapi.json').read_bytes())
        result = self.compare(capture, capture)
        self.assertEqual(result['operations_compared'], 5)
        self.assertEqual(result['status'], 'no_detected_breakage')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['new.zip', 'old.zip'])
        for side in ('old', 'new'):
            report = result['bundle_inputs'][side]
            self.assertTrue(report['approved_sha256_checked'])
            self.assertTrue(report['all_payloads_crc_checked'])
            self.assertEqual(len(report['checked_files']), 2)

    def test_wire_change_opt_in_and_exact_location(self):
        new = copy.deepcopy(self.doc)
        new['paths']['/items']['get']['parameters'][0]['explode'] = False
        result = self.compare(self.doc, new)
        finding = next(f for f in result['findings'] if f['code'] == 'parameter_wire_explode_changed')
        self.assertIn('explode', json.dumps(finding))
        self.assertEqual(result['status'], 'breaking')
        a, b = self.root / 'old.zip', self.root / 'new.zip'
        self.assertNotIn('parameter_wire_explode_changed', self.codes(
            bundle.compare(a, b, member='docs/openapi.json', servers=True)))

    def test_defaults_do_not_invent_wire_breakage(self):
        new = copy.deepcopy(self.doc)
        new['paths']['/items']['get']['parameters'][0].update(style='form', explode=True, allowReserved=False)
        result = self.compare(self.doc, new)
        self.assertFalse(any(c.startswith('parameter_wire_') for c in self.codes(result)))
        self.assertEqual(result['status'], 'review_required')

    def test_inherited_header_identifier_and_server_findings_survive(self):
        new = copy.deepcopy(self.doc)
        op = new['paths']['/items']['get']
        op['operationId'] = 'renamedItems'
        op['responses']['200']['headers']['X-Receipt']['required'] = False
        op['servers'] = [{'url': '/migrated'}]
        codes = self.codes(self.compare(self.doc, new))
        self.assertTrue({'operation_id_changed', 'response_header_not_guaranteed',
                         'server_destination_removed'} <= codes)

    def test_invalid_unchanged_parameter_refused(self):
        bad = copy.deepcopy(self.doc)
        bad['paths']['/items']['get']['parameters'][0]['explode'] = 'true'
        with self.assertRaisesRegex(ValueError, 'boolean'):
            self.compare(bad, bad)

    def test_approval_and_directory_gate_precede_analysis(self):
        path = self.archive('old.zip', self.doc)
        with mock.patch.object(bundle.paramcheck, 'compare') as analyzer:
            with self.assertRaisesRegex(ValueError, 'approved digest'):
                bundle.compare(path, path, member='docs/openapi.json', parameters=True,
                               old_sha256='1' * 64)
            with self.assertRaisesRegex(ValueError, 'directory'):
                bundle.compare(path, path, member='docs/openapi.json', parameters=True,
                               directory_bytes=1)
            analyzer.assert_not_called()

    def test_crc_checks_unselected_file_before_analysis(self):
        path = self.archive('damaged.zip', self.doc)
        raw = bytearray(path.read_bytes())
        marker = b'raise RuntimeError'
        offset = raw.index(marker)
        raw[offset] ^= 1
        path.write_bytes(raw)
        with mock.patch.object(bundle.paramcheck, 'compare') as analyzer:
            with self.assertRaises(zipfile.BadZipFile):
                bundle.compare(path, path, member='docs/openapi.json', parameters=True)
            analyzer.assert_not_called()

    def test_cli_all_four_exits(self):
        a = self.archive('a.zip', self.doc)
        cases = [(copy.deepcopy(self.doc), 0)]
        changed = copy.deepcopy(self.doc)
        changed['paths']['/items']['get']['parameters'][0]['explode'] = False
        cases.append((changed, 1))
        invalid = copy.deepcopy(self.doc)
        invalid['paths']['/items']['get']['parameters'][0]['explode'] = 'false'
        cases.append((invalid, 2))
        review = copy.deepcopy(self.doc)
        review['paths']['/items']['get']['parameters'][0]['description'] = 'new annotation'
        cases.append((review, 3))
        for doc, expected in cases:
            with self.subTest(expected=expected):
                b = self.archive('b.zip', doc)
                result = subprocess.run([sys.executable, '-B', bundle.__file__, str(a), str(b),
                            '--member', 'docs/openapi.json', '--parameters'],
                            capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                json.loads(result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
