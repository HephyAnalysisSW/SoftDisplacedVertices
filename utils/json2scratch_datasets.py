#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_JSON = Path(
    "/users/ang.li/public/SoftDV/Plotter/CMSSW_15_0_5/src/"
    "SoftDisplacedVertices/Samples/json/status_nanofinished.json"
)
DEFAULT_OUTPUT = Path("/scratch-cbe/users/alikaan.gueven/ML_KAAN/new_signals")
DEFAULT_REDIRECTOR = "root://eos.grid.vbc.ac.at/"
DEFAULT_DAS_INSTANCE = "prod/phys03"
MANIFEST_NAME = ".json2scratch_checksums.json"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Read a JSON map of sample keys to DAS datasets, retrieve LFNs with "
            "dasgoclient, and copy the files to scratch through xrdcp."
        )
    )
    parser.add_argument("--json", default=DEFAULT_JSON, type=Path, help="Input JSON file.")
    parser.add_argument(
        "--output-base",
        default=DEFAULT_OUTPUT,
        type=Path,
        help="Base output directory. Each JSON key gets one subdirectory.",
    )
    parser.add_argument(
        "--redirector",
        default=DEFAULT_REDIRECTOR,
        help="XRootD redirector used as the source prefix.",
    )
    parser.add_argument(
        "--das-instance",
        default=DEFAULT_DAS_INSTANCE,
        help="DAS instance appended to each dataset query.",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        help="Optional subset of JSON keys to process.",
    )
    parser.add_argument(
        "--max-datasets",
        type=int,
        help="Optional limit on the number of datasets to process.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Query DAS and print planned copies without running xrdcp.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Copy even when a valid checksum manifest entry already exists.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue with the next file or dataset after a failed copy.",
    )
    parser.add_argument(
        "--das-limit",
        type=int,
        default=0,
        help="Limit passed to dasgoclient. The default 0 means no DAS limit.",
    )
    return parser.parse_args()


def now_utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def run_command(command, check=True):
    print("CMD:", " ".join(command), flush=True)
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {message}")
    return result


def strip_dataset_quotes(value):
    dataset = str(value).strip()
    while len(dataset) >= 2 and dataset[0] == dataset[-1] and dataset[0] in ("'", '"'):
        dataset = dataset[1:-1].strip()
    return dataset


def normalise_adler32(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    if text.startswith("adler32:"):
        text = text.split(":", 1)[1]
    if text.startswith("0x"):
        text = text[2:]
    if not text:
        return None
    return text.zfill(8)


def join_xrootd_url(redirector, lfn):
    return redirector.rstrip("/") + "/" + lfn


def safe_local_name(lfn, duplicate_basenames):
    basename = Path(lfn).name
    if basename not in duplicate_basenames:
        return basename
    digest = hashlib.sha1(lfn.encode("utf-8")).hexdigest()[:10]
    stem = Path(basename).stem
    suffix = Path(basename).suffix
    return f"{stem}__{digest}{suffix}"


def load_json_map(path):
    with path.open() as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return data


def load_manifest(path):
    if not path.exists():
        return {"files": {}}
    with path.open() as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        return {"files": {}}
    manifest.setdefault("files", {})
    return manifest


def write_manifest(path, manifest):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(path)


def file_size(path):
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return None


def local_adler32(path):
    if shutil.which("xrdadler32") is None:
        raise RuntimeError("xrdadler32 is not available in PATH")
    result = run_command(["xrdadler32", str(path)])
    fields = result.stdout.replace("\n", " ").split()
    for field in fields:
        candidate = normalise_adler32(field)
        if candidate and all(char in "0123456789abcdef" for char in candidate):
            return candidate
    raise RuntimeError(f"Could not parse xrdadler32 output for {path}: {result.stdout!r}")


def extract_checksum(file_info):
    for key in ("adler32", "check_sum", "checksum"):
        if key in file_info:
            value = normalise_adler32(file_info.get(key))
            if value:
                return value

    checksums = file_info.get("checksums")
    if isinstance(checksums, list):
        for item in checksums:
            if not isinstance(item, dict):
                continue
            checksum_type = str(item.get("type") or item.get("cksumtype") or "").lower()
            if checksum_type == "adler32":
                value = normalise_adler32(item.get("value") or item.get("cksum"))
                if value:
                    return value
    return None


def extract_file_records(payload):
    records = {}

    def visit(obj):
        if isinstance(obj, dict):
            file_obj = obj.get("file")
            if isinstance(file_obj, list):
                for item in file_obj:
                    add_file_info(item)
            elif isinstance(file_obj, dict):
                add_file_info(file_obj)
            add_file_info(obj)
            for value in obj.values():
                visit(value)
        elif isinstance(obj, list):
            for item in obj:
                visit(item)

    def add_file_info(file_info):
        if not isinstance(file_info, dict):
            return
        name = file_info.get("name") or file_info.get("lfn") or file_info.get("logical_file_name")
        if not isinstance(name, str) or not name.startswith("/store/"):
            return
        size = file_info.get("size")
        if size is not None:
            try:
                size = int(size)
            except (TypeError, ValueError):
                size = None
        records[name] = {
            "lfn": name,
            "adler32": extract_checksum(file_info),
            "size": size,
        }

    visit(payload)
    return [records[name] for name in sorted(records)]


def das_file_records(dataset, instance, das_limit):
    query = f"file dataset={dataset} instance={instance}"
    command = [
        "dasgoclient",
        "-query",
        query,
        "-json",
    ]
    if das_limit is not None:
        command.extend(["-limit", str(das_limit)])
    result = run_command(command)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse dasgoclient JSON output for {dataset}: {exc}") from exc

    records = extract_file_records(payload)
    if not records:
        raise RuntimeError(f"No files found in DAS for dataset {dataset}")
    return records


def manifest_entry_is_valid(entry, local_path, record):
    if not entry or not local_path.exists():
        return False
    if entry.get("lfn") != record["lfn"]:
        return False
    expected_size = record.get("size")
    if expected_size is not None and file_size(local_path) != expected_size:
        return False
    expected_adler32 = record.get("adler32")
    if expected_adler32 and normalise_adler32(entry.get("adler32")) != expected_adler32:
        return False
    if expected_adler32 and normalise_adler32(entry.get("local_adler32")) != expected_adler32:
        return False
    return entry.get("status") == "ok"


def existing_file_is_valid(local_path, record):
    expected_size = record.get("size")
    if expected_size is not None and file_size(local_path) != expected_size:
        return False, None

    expected_adler32 = record.get("adler32")
    if expected_adler32:
        observed_adler32 = local_adler32(local_path)
        return observed_adler32 == expected_adler32, observed_adler32

    return True, None


def copy_one_file(record, local_path, source_url, dry_run):
    if dry_run:
        print(f"DRY-RUN: would copy {source_url} -> {local_path}", flush=True)
        return None

    tmp_path = local_path.with_name(local_path.name + ".part")
    if tmp_path.exists():
        tmp_path.unlink()

    run_command(["xrdcp", "-f", "-np", source_url, str(tmp_path)])

    expected_size = record.get("size")
    if expected_size is not None and file_size(tmp_path) != expected_size:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Size mismatch after copy for {record['lfn']}: "
            f"expected {expected_size}, got {file_size(tmp_path)}"
        )

    expected_adler32 = record.get("adler32")
    observed_adler32 = local_adler32(tmp_path) if expected_adler32 else None
    if expected_adler32 and observed_adler32 != expected_adler32:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Checksum mismatch after copy for {record['lfn']}: "
            f"expected {expected_adler32}, got {observed_adler32}"
        )

    tmp_path.replace(local_path)
    return observed_adler32


def process_dataset(key, dataset, args):
    if "/" in key or key in ("", ".", ".."):
        raise ValueError(f"Refusing unsafe JSON key for output directory: {key!r}")

    output_dir = args.output_base / key
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / MANIFEST_NAME
    manifest = load_manifest(manifest_path)

    print(f"\nDataset key: {key}", flush=True)
    print(f"DAS dataset: {dataset}", flush=True)
    records = das_file_records(dataset, args.das_instance, args.das_limit)
    print(f"Found {len(records)} files", flush=True)

    basenames = [Path(record["lfn"]).name for record in records]
    duplicate_basenames = {name for name in basenames if basenames.count(name) > 1}

    manifest.update(
        {
            "key": key,
            "dataset": dataset,
            "das_instance": args.das_instance,
            "redirector": args.redirector,
            "updated_at": now_utc(),
        }
    )
    manifest.setdefault("files", {})

    copied = 0
    skipped = 0
    failed = 0

    for record in records:
        lfn = record["lfn"]
        local_name = safe_local_name(lfn, duplicate_basenames)
        local_path = output_dir / local_name
        source_url = join_xrootd_url(args.redirector, lfn)
        entry = manifest["files"].get(lfn)

        try:
            if not args.force and manifest_entry_is_valid(entry, local_path, record):
                skipped += 1
                print(f"SKIP: {local_path}", flush=True)
                continue

            if not args.force and local_path.exists():
                is_valid, observed_adler32 = existing_file_is_valid(local_path, record)
                if is_valid:
                    manifest["files"][lfn] = {
                        "lfn": lfn,
                        "source": source_url,
                        "local_path": str(local_path),
                        "size": record.get("size"),
                        "adler32": record.get("adler32"),
                        "local_adler32": observed_adler32 or record.get("adler32"),
                        "status": "ok",
                        "checked_at": now_utc(),
                    }
                    write_manifest(manifest_path, manifest)
                    skipped += 1
                    print(f"SKIP: {local_path}", flush=True)
                    continue

            observed_adler32 = copy_one_file(record, local_path, source_url, args.dry_run)
            if not args.dry_run:
                manifest["files"][lfn] = {
                    "lfn": lfn,
                    "source": source_url,
                    "local_path": str(local_path),
                    "size": record.get("size"),
                    "adler32": record.get("adler32"),
                    "local_adler32": observed_adler32 or record.get("adler32"),
                    "status": "ok",
                    "copied_at": now_utc(),
                }
                write_manifest(manifest_path, manifest)
            copied += 1
        except Exception as exc:
            failed += 1
            print(f"ERROR: {lfn}: {exc}", file=sys.stderr, flush=True)
            if not args.continue_on_error:
                raise

    if not args.dry_run:
        manifest["updated_at"] = now_utc()
        write_manifest(manifest_path, manifest)

    return copied, skipped, failed


def main():
    args = parse_args()

    missing_tools = [tool for tool in ("dasgoclient", "xrdcp") if shutil.which(tool) is None]
    if missing_tools:
        raise RuntimeError(
            "Required command(s) not found in PATH: "
            + ", ".join(missing_tools)
            + ". Run inside CMSSW EL9 after cmsenv."
        )

    data = load_json_map(args.json)
    selected_keys = args.keys or list(data)
    if args.max_datasets is not None:
        selected_keys = selected_keys[: args.max_datasets]

    total_copied = 0
    total_skipped = 0
    total_failed = 0

    for key in selected_keys:
        if key not in data:
            raise KeyError(f"JSON key not found: {key}")
        dataset = strip_dataset_quotes(data[key])
        copied, skipped, failed = process_dataset(key, dataset, args)
        total_copied += copied
        total_skipped += skipped
        total_failed += failed

    print(
        "\nSummary: "
        f"copied={total_copied}, skipped={total_skipped}, failed={total_failed}",
        flush=True,
    )
    if total_failed:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
