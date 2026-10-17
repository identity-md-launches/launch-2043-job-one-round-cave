#!/usr/bin/env python3
"""Offline OpenAPI parameter wire-contract comparison, standard library only."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

PREVIOUS = Path(__file__).resolve().parents[1] / 'headercheck/headercheck.py'
spec = importlib.util.spec_from_file_location('paramcheck_header', PREVIOUS)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
api = previous.api
STYLES = {'query': {'form', 'spaceDelimited', 'pipeDelimited', 'deepObject'},
          'path': {'matrix', 'label', 'simple'}, 'header': {'simple'}, 'cookie': {'form'}}
DEFAULTS = {'query': 'form', 'path': 'simple', 'header': 'simple', 'cookie': 'form'}
MAX_PARAMETER_VISITS = 20000
IGNORED_HEADERS = {'accept', 'authorization', 'content-type'}


def representation(document, item):
    """Return effective schema encoding or single-media content representation."""
    location = item['in']
    api.require(('schema' in item) != ('content' in item),
                'parameter must contain exactly one of schema or content')
    if 'content' in item:
        content = item['content']
        api.require(isinstance(content, dict) and len(content) == 1,
                    'parameter content must have exactly one media type')
        for media, entry in content.items():
            api.require(isinstance(media, str) and bool(media) and isinstance(entry, dict),
                        'parameter content must contain a media type object')
            schema = document.resolve(entry.get('schema', {}))
            api.require(isinstance(schema, (dict, bool)), 'content schema must be object or boolean')
        return ('content',)
    schema = document.resolve(item['schema'])
    api.require(isinstance(schema, (dict, bool)), 'parameter schema must be object or boolean')
    style = item.get('style', DEFAULTS[location])
    api.require(isinstance(style, str) and style in STYLES[location],
                'unsupported parameter style for ' + location)
    for field in ('explode', 'allowReserved', 'allowEmptyValue'):
        api.require(field not in item or type(item[field]) is bool,
                    'parameter ' + field + ' must be boolean')
    api.require(location == 'query' or not (set(item) & {'allowReserved', 'allowEmptyValue'}),
                'allowReserved and allowEmptyValue are query-only fields')
    return ('schema', style, item.get('explode', style == 'form'),
            item.get('allowReserved', False) if location == 'query' else False)


class Analyzer(previous.Analyzer):
    def __init__(self, old, new):
        super().__init__(old, new)
        self.parameter_visits = 0

    def encodings(self, document, path_item, operation):
        parameters = self.parameters(document, path_item, operation)
        self.parameter_visits += len(parameters)
        api.require(self.parameter_visits <= MAX_PARAMETER_VISITS,
                    'parameter visits exceed 20000; compare a smaller description')
        return {key: (item, representation(document, item))
                for key, item in parameters.items()
                if not (key[0] == 'header' and key[1] in IGNORED_HEADERS)}

    def operation(self, path, method, old_item, new_item):
        super().operation(path, method, old_item, new_item)
        before = self.encodings(self.old, old_item, old_item[method])
        after = self.encodings(self.new, new_item, new_item[method])
        loc = api.pointer('/paths', path) + '/' + method + '/parameters'
        for key in sorted(before.keys() & after.keys()):
            a, ar = before[key]
            b, br = after[key]
            ploc = api.pointer(loc, key[0] + ':' + key[1])
            if ar[0] != br[0]:
                self.emit('review', 'parameter_representation_changed', ploc,
                          'Parameter switched between schema and content; inspect actual wire values.')
            elif ar[0] == 'content':
                self.content(a['content'], b['content'], ploc + '/content', 'request')
            else:
                for index, field in enumerate(('style', 'explode', 'allowReserved'), 1):
                    if ar[index] != br[index]:
                        self.emit('breaking', 'parameter_wire_' + field + '_changed', ploc + '/' + field,
                                  'Effective parameter ' + field + ' changed; previously serialized '
                                  'values may be interpreted differently. Check the concrete value domain.')


def compare(old, new):
    analyzer = Analyzer(old, new)
    result = analyzer.run()
    result.update(extension='paramcheck-v1 (includes headercheck and all earlier analyzers)',
                  parameter_visits=analyzer.parameter_visits,
                  parameter_scope='effective parameters of common inline top-level paths operations')
    return result


def demo():
    capture = Path(__file__).resolve().parents[1] / 'apidelta/imd-openapi.json'
    old, digest = api.load(capture)
    old = copy.deepcopy(old)
    path = sorted(old['paths'])[0]
    method = sorted(old['paths'][path].keys() & api.METHODS)[0]
    old['paths'][path][method].setdefault('parameters', []).append({
        'in': 'query', 'name': 'workerTags33', 'schema': {'type': 'array', 'items': {'type': 'string'}}})
    new = copy.deepcopy(old)
    new['paths'][path][method]['parameters'][-1]['explode'] = False
    result = compare(old, new)
    api.require(any(f['code'] == 'parameter_wire_explode_changed' for f in result['findings']),
                'demo failed to detect hypothetical serialization change')
    result.update(capture_sha256=digest, baseline_source='https://api.imd.fun/openapi.json',
                  demo='Hypothetical optional array parameter on a real saved IMD operation: '
                       'workerTags33=a&workerTags33=b becomes workerTags33=a,b. No endpoint contacted.')
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
        print('paramcheck: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
