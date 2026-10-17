#!/usr/bin/env python3
"""Offline, conservative OpenAPI response-header compatibility checks."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys

PREVIOUS = Path(__file__).resolve().with_name('idcheck.py')
spec = importlib.util.spec_from_file_location('headercheck_id', PREVIOUS)
ids = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ids)
api = ids.api
TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", re.ASCII)
MAX_HEADERS = 256
MAX_HEADER_VISITS = 20000


def headers(document, response):
    """Resolve and validate a bounded case-insensitive Header Object map.

    Content-Type is ignored by the Response Object rules. This deliberately
    validates only header structures we interpret, not the entire description.
    """
    response = document.resolve(response)
    api.require(isinstance(response, dict), 'response must be an object')
    raw = response.get('headers', {})
    api.require(isinstance(raw, dict) and len(raw) <= MAX_HEADERS,
                'response headers must be an object of at most 256 entries')
    result = {}
    for name, value in sorted(raw.items()):
        api.require(isinstance(name, str) and 0 < len(name) <= 256 and TOKEN.fullmatch(name),
                    'response header name must be an ASCII HTTP token of at most 256 characters')
        key = name.lower()
        if key == 'content-type':
            continue
        api.require(key not in result, 'duplicate case-insensitive response header: ' + key)
        item = document.resolve(value)
        api.require(isinstance(item, dict), 'header must resolve to an object')
        api.require(not (set(item) & {'name', 'in', 'allowReserved', 'allowEmptyValue'}),
                    'header has forbidden or unsupported non-header parameter fields')
        for field in ('required', 'deprecated', 'explode'):
            api.require(field not in item or type(item[field]) is bool,
                        'header ' + field + ' must be boolean')
        api.require(item.get('style', 'simple') == 'simple', 'header style must be simple')
        api.require(('schema' in item) != ('content' in item),
                    'header must contain exactly one of schema or content')
        if 'schema' in item:
            schema = document.resolve(item['schema'])
            api.require(isinstance(schema, (dict, bool)), 'header schema must be object or boolean')
        else:
            content = item['content']
            api.require(isinstance(content, dict) and len(content) == 1 and
                        all(isinstance(v, dict) for v in content.values()),
                        'header content must contain exactly one media type object')
            for media, entry in content.items():
                api.require(isinstance(media, str) and bool(media), 'header media type must be nonempty')
                schema = document.resolve(entry.get('schema', {}))
                api.require(isinstance(schema, (dict, bool)), 'header content schema must be object or boolean')
        result[key] = item
    return result


class Analyzer(ids.Analyzer):
    def __init__(self, old, new):
        super().__init__(old, new)
        self.header_visits = 0

    def response_headers(self, document, response):
        result = headers(document, response)
        self.header_visits += len(result)
        api.require(self.header_visits <= MAX_HEADER_VISITS,
                    'response header visits exceed 20000; compare a smaller description')
        return result

    def operation(self, path, method, old_item, new_item):
        super().operation(path, method, old_item, new_item)
        before = old_item[method].get('responses', {})
        after = new_item[method].get('responses', {})
        # Resolve every status of a common operation, including added/removed
        # statuses. No claim is made about status fallback or range containment.
        old_maps = {s: self.response_headers(self.old, r) for s, r in sorted(before.items())
                    if not s.startswith('x-')}
        new_maps = {s: self.response_headers(self.new, r) for s, r in sorted(after.items())
                    if not s.startswith('x-')}
        for status in sorted(old_maps.keys() & new_maps.keys()):
            a, b = old_maps[status], new_maps[status]
            loc = api.pointer(api.pointer('/paths', path) + '/' + method + '/responses', status) + '/headers'
            for name in sorted(a.keys() | b.keys()):
                hloc = api.pointer(loc, name)
                if name not in b:
                    required = a[name].get('required', False)
                    self.emit('breaking' if required else 'review', 'response_header_removed', hloc,
                              'A required response header is no longer guaranteed.' if required else
                              'An optional response header was removed; review client use.')
                elif name not in a:
                    self.emit('review', 'response_header_added', hloc,
                              'A response header was added; old behavior and client tolerance are unresolved.')
                else:
                    old, new = a[name], b[name]
                    if old.get('required', False) and not new.get('required', False):
                        self.emit('breaking', 'response_header_not_guaranteed', hloc + '/required',
                                  'An old required response header may now be omitted.')
                    if ('schema' in old) != ('schema' in new):
                        self.emit('review', 'response_header_representation_changed', hloc,
                                  'Header switched between schema and content; wire compatibility is unresolved.')
                    elif 'schema' in old:
                        self.schema(old['schema'], new['schema'], hloc + '/schema', 'response')
                        if old.get('explode', False) != new.get('explode', False):
                            self.emit('review', 'response_header_encoding_changed', hloc + '/explode',
                                      'Header simple-style explode changed; check actual serialized values.')
                    else:
                        self.content(old['content'], new['content'], hloc + '/content', 'response')
                    # Existing broad response metadata finding is retained.
                    # This gives a precise location even when a referenced
                    # Header Object changes without changing the response text.
                    omit = {'schema', 'content', 'required', 'style', 'explode'}
                    self.changed({k: v for k, v in old.items() if k not in omit},
                                 {k: v for k, v in new.items() if k not in omit}, hloc,
                                 'response_header_metadata_changed',
                                 'Header annotation or extension changed; check client assumptions.')


def compare(old, new):
    analyzer = Analyzer(old, new)
    result = analyzer.run()
    result['extension'] = 'headercheck-v1 (includes idcheck and all earlier line 4 analyzers)'
    result['header_scope'] = 'response headers of common inline paths operations; exact matching status keys'
    result['header_visits'] = analyzer.header_visits
    return result


def demo():
    capture = Path(__file__).resolve().parents[1] / 'imd-openapi.json'
    original, digest = api.load(capture)
    old = copy.deepcopy(original)
    path = sorted(old['paths'])[0]
    method = sorted(old['paths'][path].keys() & api.METHODS)[0]
    responses = old['paths'][path][method]['responses']
    status = sorted(responses)[0]
    response = api.Document(old).resolve(responses[status])
    # Both header declarations are hypothetical; the service never promised it.
    response.setdefault('headers', {})['X-Worker-Budget'] = {
        'required': True, 'schema': {'type': 'integer', 'minimum': 0}}
    new = copy.deepcopy(old)
    api.Document(new).resolve(new['paths'][path][method]['responses'][status])['headers'][
        'X-Worker-Budget']['required'] = False
    result = compare(old, new)
    api.require(any(f['code'] == 'response_header_not_guaranteed' for f in result['findings']),
                'demo did not detect hypothetical lost header guarantee')
    result.update(capture_sha256=digest, baseline_source='https://api.imd.fun/openapi.json',
                  demo='Real saved paths with a hypothetical required response header made optional; '
                       'both header declarations are invented in memory, no endpoint contacted.')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    diff = commands.add_parser('compare')
    diff.add_argument('old')
    diff.add_argument('new')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            old, oh = api.load(args.old)
            new, nh = api.load(args.new)
            result = compare(old, new)
            result.update(old_sha256=oh, new_sha256=nh)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if args.command == 'demo' else {
            'breaking': 1, 'review_required': 3, 'no_detected_breakage': 0}[result['status']]
    except (api.Invalid, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print('headercheck: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
