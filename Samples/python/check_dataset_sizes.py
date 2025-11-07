#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

def read_datasets(path: Path):
    ds = []
    with path.open() as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.endswith(":"):        # skip "2024:", "2023:", etc.
                continue
            if line.startswith("#"):      # skip comments if any
                continue
            ds.append(line)
    return ds

def query_filesize(dataset: str) -> int:
    """
    Returns file_size in bytes for a dataset using dasgoclient summary.
    If the result is an array of dicts, sum their file_size fields.
    """
    # No shell, so no quotes needed; pass the whole query as one arg
    cmd = ["dasgoclient", f'-query=summary dataset={dataset}']
    try:
        out = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] dasgoclient failed for {dataset}: {e}", file=sys.stderr)
        return 0

    out = out.strip()
    if not out:
        print(f"[WARN] Empty response for {dataset}", file=sys.stderr)
        return 0

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        print(f"[WARN] Could not parse JSON for {dataset}: {out[:200]}...", file=sys.stderr)
        return 0

    # Typical output is a single-element list with a dict; be tolerant
    total = 0
    if isinstance(data, dict) and "file_size" in data:
        total = int(data["file_size"] or 0)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "file_size" in item:
                total += int(item["file_size"] or 0)
    else:
        print(f"[WARN] Unexpected JSON structure for {dataset}: {type(data)}", file=sys.stderr)

    return total

def main():
    ap = argparse.ArgumentParser(description="Sum DAS dataset file sizes from a list and print total/1e12.")
    ap.add_argument("listfile", type=Path, help="Path to the text file containing dataset lines.")
    args = ap.parse_args()

    datasets = read_datasets(args.listfile)
    if not datasets:
        print("No datasets found in the file (after filtering).", file=sys.stderr)
        sys.exit(1)

    grand_total_bytes = 0
    for ds in datasets:
        size_b = query_filesize(ds)
        grand_total_bytes += size_b
        print(f"{ds}: {size_b/1e12:.6f} TB")

    print("-" * 40)
    print(f"Total bytes: {grand_total_bytes}")
    print(f"Total / 1e12 = {grand_total_bytes/1e12:.6f}")

if __name__ == "__main__":
    main()
