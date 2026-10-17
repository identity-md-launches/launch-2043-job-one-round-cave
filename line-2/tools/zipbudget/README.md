# ZipBudget

ZipBudget gives a worker a quick, offline preflight of a ZIP archive's file-count and declared-uncompressed-byte budgets. It uses only Python's standard library and never extracts or writes the archive.

Try it with one command:

```sh
python3 -c 'import zipfile; z=zipfile.ZipFile("/tmp/zipbudget-demo.zip", "w"); z.writestr("kept.txt", "hello"); z.close()' && python3 line-2/tools/zipbudget/zipbudget.py /tmp/zipbudget-demo.zip --max-files 2 --max-bytes 20
```

The command prints a JSON report with `ok`, file count, byte total, and entries. A limit breach returns status 1. This is a preflight, not a replacement for SafeZip's full validation: ZIP metadata can be hostile, so extraction must still use the established bounded extractor.

Checked locally: the demo reports one file and five bytes; a one-byte budget reports `ok: false` without extraction.
