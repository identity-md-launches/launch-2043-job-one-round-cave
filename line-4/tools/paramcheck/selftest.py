#!/usr/bin/env python3
"""Offline parameter wire-contract regressions."""
import contextlib
import copy
import io
import itertools
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import paramcheck as p


def param(location='query', **kwargs):
    return dict({'name': 'a~/b', 'in': location, 'schema': {
        'type': 'array', 'items': {'type': 'string'}}}, **kwargs)


def doc(item=None):
    return {'openapi': '3.1.0', 'paths': {'/a~b/c': {'get': {
        'parameters': [item or param()], 'responses': {'200': {'description': 'OK'}}}}}}


def findings(a, b):
    return p.compare(a, b)['findings']


def wire_codes(a, b):
    return {f['code'] for f in findings(a, b) if f['code'].startswith('parameter_wire_')}


class Checks(unittest.TestCase):
    def test_capture_demo(self):
        path = Path(__file__).resolve().parents[1] / 'apidelta/imd-openapi.json'
        a, _ = p.api.load(path)
        self.assertEqual(p.compare(a, a)['findings'], [])
        self.assertEqual(p.demo()['counts'], {'breaking': 1, 'review': 1, 'info': 0})

    def test_independent_array_wire_oracle(self):
        # Concrete serializer examples from the OpenAPI style table: compare
        # actual wire strings independently of the analyzer's tuple comparison.
        variants = [({}, 'a~/b=red&a~/b=blue'),
                    ({'style': 'form', 'explode': True}, 'a~/b=red&a~/b=blue'),
                    ({'explode': False}, 'a~/b=red,blue'),
                    ({'style': 'spaceDelimited', 'explode': False}, 'a~/b=red%20blue'),
                    ({'style': 'pipeDelimited', 'explode': False}, 'a~/b=red|blue')]
        for (a, aw), (b, bw) in itertools.product(variants, repeat=2):
            with self.subTest(a=a, b=b):
                self.assertEqual(bool(wire_codes(doc(param(**a)), doc(param(**b)))), aw != bw)

    def test_defaults_all_locations(self):
        for location, style in p.DEFAULTS.items():
            self.assertFalse(wire_codes(doc(param(location)), doc(param(
                location, style=style, explode=style == 'form'))))
        a = doc(param(style='deepObject'))
        self.assertFalse(wire_codes(a, doc(param(style='deepObject', explode=False))))
        # Default explode depends on effective style, not location alone.
        self.assertIn('parameter_wire_explode_changed', wire_codes(a, doc(param())))

    def test_style_and_reserved(self):
        for location, styles in p.STYLES.items():
            for style in styles:
                p.compare(doc(param(location, style=style)), doc(param(location, style=style)))
        self.assertEqual(wire_codes(doc(), doc(param(allowReserved=True))),
                         {'parameter_wire_allowReserved_changed'})
        self.assertFalse(wire_codes(doc(), doc(param(allowReserved=False))))

    def test_inheritance_override(self):
        a = doc()
        operation = a['paths']['/a~b/c']['get']
        a['paths']['/a~b/c']['parameters'] = [param(explode=False)]
        # Operation wins; the shadowed declaration must not trigger a wire break.
        b = copy.deepcopy(a)
        b['paths']['/a~b/c']['parameters'] = [param(style='pipeDelimited')]
        self.assertFalse(wire_codes(a, b))
        del operation['parameters']
        self.assertIn('parameter_wire_explode_changed', wire_codes(a, b))

    def test_reference_targets(self):
        a = doc({'$ref': '#/components/parameters/a~0~1b'})
        a['components'] = {'parameters': {'a~/b': param()}}
        b = copy.deepcopy(a)
        b['components']['parameters']['a~/b']['explode'] = False
        self.assertEqual(wire_codes(a, b), {'parameter_wire_explode_changed'})
        for ref in ('https://example.invalid/not-fetched', '#/missing', '#/components/parameters/loop'):
            bad = doc({'$ref': ref})
            bad['components'] = {'parameters': {'loop': {'$ref': '#/components/parameters/loop'}}}
            with self.subTest(ref=ref), self.assertRaises(p.api.Invalid):
                p.compare(bad, bad)

    def test_content_schema_variance(self):
        a = doc({'in': 'query', 'name': 'a', 'content': {
            'application/json': {'schema': {'type': 'integer', 'enum': [1, 2]}}}})
        b = copy.deepcopy(a)
        b['paths']['/a~b/c']['get']['parameters'][0]['content'][
            'application/json']['schema']['enum'] = [1]
        self.assertTrue(any(f['code'] == 'schema_enum_incompatible' for f in findings(a, b)))
        b = copy.deepcopy(a)
        content = b['paths']['/a~b/c']['get']['parameters'][0]['content']
        content['text/plain'] = content.pop('application/json')
        self.assertTrue(any(f['code'] == 'media_type_removed' for f in findings(a, b)))
        self.assertTrue(any(f['code'] == 'parameter_representation_changed' for f in findings(a, doc(
            {'in': 'query', 'name': 'a', 'schema': {}}))))

    def test_malformed_identical(self):
        bad = [dict(param(), style=[]), param(style='simple'), param(explode=1),
               param(allowReserved='true'), param(allowEmptyValue=0),
               param('header', allowReserved=False), param('path', allowEmptyValue=False),
               {'in': 'query', 'name': 'x'}, dict(param(), content={'a': {}}),
               dict(param(), schema=1), {'in': 'query', 'name': 'x', 'content': {}},
               {'in': 'query', 'name': 'x', 'content': {'a': {}, 'b': {}}},
               {'in': 'query', 'name': 'x', 'content': {'a': []}},
               {'in': 'query', 'name': 'x', 'content': {'a': {'schema': 1}}}]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(p.api.Invalid):
                p.compare(doc(item), doc(item))

    def test_special_headers_ignored_by_extension(self):
        for name in ('Accept', 'AUTHORIZATION', 'Content-Type'):
            a = doc(dict(param('header'), name=name))
            b = doc(dict(param('header', explode=True), name=name))
            self.assertFalse(wire_codes(a, b))

    def test_content_ignores_schema_serialization_fields(self):
        a = doc({'in': 'query', 'name': 'x', 'content': {'application/json': {'schema': {}}}})
        b = copy.deepcopy(a)
        b['paths']['/a~b/c']['get']['parameters'][0]['explode'] = True
        self.assertFalse(wire_codes(a, b))

    def test_scope_added_removed_parameters(self):
        a, b = doc(), doc(param('query', style='simple'))
        # Added parameters of common operations are validated, even without a pair.
        b['paths']['/a~b/c']['get']['parameters'][0]['name'] = 'new'
        with self.assertRaises(p.api.Invalid):
            p.compare(a, b)
        # Entirely new operations remain within inherited analysis only.
        b['paths']['/a~b/c']['post'] = b['paths']['/a~b/c'].pop('get')
        self.assertEqual(p.compare(a, b)['parameter_visits'], 0)

    def test_budget(self):
        with patch.object(p, 'MAX_PARAMETER_VISITS', 1), self.assertRaises(p.api.Invalid):
            p.compare(doc(), doc())

    def test_retention_determinism_immutability_pointer(self):
        a, b = doc(), doc(param(explode=False))
        snapshot = copy.deepcopy((a, b))
        result = p.compare(a, b)
        self.assertEqual((a, b), snapshot)
        self.assertEqual(result, p.compare(a, b))
        self.assertTrue(all(f in result['findings'] for f in p.previous.compare(a, b)['findings']))
        self.assertTrue(any(f['location'] == '/paths/~1a~0b~1c/get/parameters/query:a~0~1b/explode'
                            for f in result['findings']))

    def test_cli_exits_and_hashes(self):
        for old, new, expected in [(doc(), doc(), 0), (doc(), doc(param(explode=False)), 1),
                                   (doc(), doc(param(description='changed')), 3),
                                   (doc(param(style='simple')), doc(), 2)]:
            out, err = io.StringIO(), io.StringIO()
            with patch.object(p.api, 'load', side_effect=[(old, 'a'*64), (new, 'b'*64)]), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = p.main(['compare', 'old.json', 'new.json'])
            self.assertEqual(code, expected, err.getvalue())
            if expected == 2:
                self.assertEqual(out.getvalue(), '')
            else:
                self.assertEqual(json.loads(out.getvalue())['old_sha256'], 'a'*64)


if __name__ == '__main__':
    unittest.main()
