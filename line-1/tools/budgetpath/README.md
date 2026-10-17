# Budgetpath

`budgetpath.py` computes the deterministic critical path of a small offline task plan, rejects missing dependencies and cycles, and reports whether the path fits the caller's minute budget. It uses only Python's standard library and does not execute tasks or predict real runtime.

Try it from the repository root:

```sh
python3 line-1/tools/budgetpath/budgetpath.py line-1/tools/budgetpath/example.json
```

The example reports an 18-minute critical path (`inspect`, `build`, `review`) within the 20-minute budget. This is a planning estimate supplied by the caller, not a claim about elapsed time.
