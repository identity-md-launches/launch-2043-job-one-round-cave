# ParamCheck

Find potential OpenAPI parameter wire-format breaks before updating an integration.
Python 3.9+, standard library only, offline. Keep this folder beside all the earlier
line 4 analyzer folders; no installation is needed. From the repository root:

```sh
python3 -B line-4/tools/paramcheck/paramcheck.py demo
```

The demo uses the bundled **real public IMD description** and adds an optional
array query parameter hypothetically in memory. It changes form serialization
from repeated keys (`workerTags33=a&workerTags33=b`) to a comma-separated value
(`workerTags33=a,b`). It reports one potential breaking change and one inherited
review across five operations, and exits 0. Neither parameter declaration is a
claim about the actual service. No described API operation is called.

Compare your own saved JSON descriptions:

```sh
python3 -B line-4/tools/paramcheck/paramcheck.py compare line-4/tools/apidelta/imd-openapi.json line-4/live-openapi-33.json
```

Replace the two paths with old/proposed descriptions inside the working directory.
Reports are deterministic JSON on stdout, with exact input-byte SHA-256 hashes.
Compare exits: **0** no detected break, **1** potential breaking change, **2**
invalid/unsupported input or resource/file error, **3** unresolved review only.
A successful demo exits 0 despite its illustrative findings. Only compare exit 0
is an automated pass in the supported subset; it is not a compatibility guarantee.

## What it adds

For common top-level inline paths operations, use the earlier parameter resolver
(path declarations, then operation overrides; header names case-insensitive).
Resolve local references independently on each side. Validate effective schema or
single-media content declarations on both sides, even when identical and including
added/removed parameters of common operations.

For schema parameters, compare effective `style`, `explode`, and query
`allowReserved`. Defaults follow the
[OpenAPI 3.1 Parameter Object](https://spec.openapis.org/oas/v3.1.0.html#parameter-object):
query/cookie style `form`, path/header style `simple`; explode defaults to true
for style `form`, false otherwise; allowReserved defaults to false. Explicit
spelling of a default adds no new wire finding. A changed effective value produces
a **potential** breaking finding at that field: an old serialized value may be
interpreted differently. All inherited generic reviews remain, even for explicit
defaults. `allowEmptyValue` is type-checked but has only inherited metadata review.
Query styles form/spaceDelimited/pipeDelimited/deepObject, path styles
matrix/label/simple, header simple and cookie form are recognized.

For content parameters, run the existing request-direction media/schema analysis:
a removed media type or a narrower request enum can now produce a precise breaking
finding. Schema/content switches require review. Schema-style serialization fields
are not interpreted for content parameters. Explicit Accept, Authorization, and
Content-Type header parameters are ignored by this extension as specified by
OpenAPI; inherited analyzers may still report them.

## Bounds and limits

This is conservative static comparison, not a serializer, a full OpenAPI validator
or a proof that a value can occur. A serialization-field change can be harmless
for a particular primitive, single-element array, enum or impossible schema.
Findings do not prove the server stopped accepting the old wire format. This tool
does not infer wire equivalence, evaluate percent encoding or reserved-character
sets, model parser quirks, validate style/type/explode combinations, or implement
undefined nested-object serialization. Review actual client/server behavior.

Only effective declarations of common operations are validated here. Shadowed
path parameters, unused components, entirely added/removed operations, callbacks
and webhooks are outside this extension's validation. Earlier operation-change
findings remain. Parameter objects must have exactly one schema or content;
content has exactly one media object. Local reference support/refusals and all
earlier analyzer limitations remain, including JSON float precision and unresolved
schema compositions. Schema/content mode-specific keyword completeness is not
fully validated.

At most 20,000 effective parameter visits (both sides combined) are allowed.
Inherited bounds include 1 MiB per input, 50,000 JSON nodes, depth 80, 20,000 schema
visits, 2,000 findings and the earlier security/server budgets. Limits refuse the
whole comparison, never return a partial pass. Inputs are bounded workspace files;
no external reference is fetched. No environment, configuration, wallet, secret,
signature, payment, transaction or deployment code is present. Static API comparison
needs no coin, price or balance.

## What happened when tried

On 2026-10-17, all **14 new tests** passed, including 25 independently enumerated
concrete array-wire comparisons, defaults, inheritance/override, reference-target
changes, request-content narrowing, malformed unchanged declarations, special
headers, budget refusal, inherited finding retention, exact locations, nonmutation,
determinism, and all four CLI exits. All **186 inherited tests** passed unchanged:
**200 tests in 13 suites**. These are local checks, not independent certification.

The demo found the intended change. Comparing the historical capture with itself
found five operations and zero findings. A read-only GET of
`https://api.imd.fun/openapi.json` with User-Agent `Pepeolithic-ParamCheck/33.0`
returned the same 23,132 bytes (SHA-256
`be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`).
Its comparison also found five operations and zero findings. No API operation
described in the document was executed. Saved input and evidence are
[the public capture](../../live-openapi-33.json) and
[check results](../../check-results-33.json).

```sh
python3 -B line-4/tools/paramcheck/selftest.py
python3 -B line-4/check-33.py
```

The second command reruns all 13 suites, the demo and the unchanged-capture
comparison offline. Optional `--live` repeats only the public-description GET
and refreshes this round's saved capture/evidence.
