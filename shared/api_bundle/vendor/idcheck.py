#!/usr/bin/env python3
"""Offline OpenAPI operation identifier checks for generated-client upgrades."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

PREVIOUS = Path(__file__).resolve().with_name('servercheck.py')
spec = importlib.util.spec_from_file_location('idcheck_server', PREVIOUS)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
api = server.api
MAX_ID_LENGTH = 4096
MAX_OPERATIONS = 10000


def identifiers(document):
    """Validate and index inline operations in paths, including added/removed ones.

    None means absent. Empty strings remain strings; no identifier grammar is
    invented. Case matters. Callbacks and webhooks are outside this index.
    """
    by_operation, by_id = {}, {}
    for path, item in sorted(document.obj['paths'].items()):
        for method in sorted(item.keys() & api.METHODS):
            operation = item[method]
            api.require(isinstance(operation, dict), 'operation must be an object')
            api.require('$ref' not in operation, 'operation $ref is unsupported; inline the operation')
            key = (path, method)
            api.require(len(by_operation) < MAX_OPERATIONS, 'operation index exceeds 10000 entries')
            identifier = operation.get('operationId')
            if 'operationId' in operation:
                api.require(isinstance(identifier, str) and len(identifier) <= MAX_ID_LENGTH,
                            'operationId must be a string of at most 4096 characters')
                api.require(identifier not in by_id,
                            'duplicate operationId among paths operations: ' + repr(identifier))
                by_id[identifier] = key
            by_operation[key] = identifier
    return by_operation


class Analyzer(server.Analyzer):
    def __init__(self, old, new):
        super().__init__(old, new)
        # Validate both full indexes before emitting any findings, even if an
        # invalid identifier is only on a newly added or removed operation.
        self.old_ids = identifiers(self.old)
        self.new_ids = identifiers(self.new)

    def operation(self, path, method, old_item, new_item):
        super().operation(path, method, old_item, new_item)
        before, after = self.old_ids[path, method], self.new_ids[path, method]
        if before == after:
            return
        loc = api.pointer('/paths', path) + '/' + method + '/operationId'
        if before is None:
            self.emit('review', 'operation_id_added', loc,
                      'An explicit operationId was added. Generated client naming may change; '
                      'compare the actual generated interface before upgrading.')
        else:
            self.emit('breaking', 'operation_id_removed' if after is None else 'operation_id_changed', loc,
                      'An existing operationId was removed or changed. Clients generated using it '
                      'may lose their callable symbol even if the HTTP endpoint still works.')


def compare(old, new):
    result = Analyzer(old, new).run()
    result['extension'] = 'idcheck-v1 (includes servercheck and all earlier line 4 analyzers)'
    result['identifier_scope'] = 'inline top-level paths operations; callbacks and webhooks excluded'
    return result


def demo():
    capture = Path(__file__).resolve().parents[1] / 'imd-openapi.json'
    old, digest = api.load(capture)
    new = copy.deepcopy(old)
    # Use a real saved operation that already declares an identifier. Change
    # only that label, not the endpoint, payload or service.
    candidates = [(path, method) for path, item in sorted(old['paths'].items())
                  for method in sorted(item.keys() & api.METHODS)
                  if isinstance(item[method].get('operationId'), str)]
    api.require(bool(candidates), 'saved capture has no named operation')
    path, method = candidates[0]
    used = {item[m].get('operationId') for item in old['paths'].values()
            for m in item.keys() & api.METHODS}
    label = new['paths'][path][method]['operationId'] + '_hypothetical_revision'
    while label in used:
        label += '_'
    new['paths'][path][method]['operationId'] = label
    result = compare(old, new)
    api.require(any(f['code'] == 'operation_id_changed' for f in result['findings']),
                'demo did not detect the hypothetical identifier rename')
    result.update(capture_sha256=digest, baseline_source='https://api.imd.fun/openapi.json',
                  demo='One identifier renamed hypothetically in the saved public description; no endpoint contacted.')
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
        print('idcheck: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
