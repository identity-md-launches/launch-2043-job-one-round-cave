#!/usr/bin/env python3
"""Report whether a ZIP's declared entries fit explicit count/byte budgets."""
import argparse
import json
import sys
import zipfile


def inspect(path, max_files, max_bytes):
    with zipfile.ZipFile(path) as archive:
        total = 0
        entries = []
        for info in archive.infolist():
            if info.is_dir():
                continue
            total += info.file_size
            entries.append({"name": info.filename, "bytes": info.file_size})
            if len(entries) > max_files or total > max_bytes:
                return {"ok": False, "reason": "budget exceeded", "files": len(entries), "bytes": total}
    return {"ok": True, "files": len(entries), "bytes": total, "entries": entries}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--max-bytes", type=int, default=1_000_000)
    args = parser.parse_args(argv)
    if args.max_files < 1 or args.max_bytes < 1:
        parser.error("budgets must be positive")
    try:
        result = inspect(args.archive, args.max_files, args.max_bytes)
    except (OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
