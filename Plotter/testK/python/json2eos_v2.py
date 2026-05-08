import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


DEFAULT_JSON = (
    "/users/alikaan.gueven/AOD_to_nanoAOD/Plotter_run3/"
    "CMSSW_15_0_5/src/SoftDisplacedVertices/Samples/json/scratch_data24.json"
)
DEFAULT_LOGICAL_DIRECTORY = "/store/user/aguven/scratch_backup"
DEFAULT_REDIRECTOR = "root://eos.grid.vbc.ac.at/"
DEFAULT_CHECKSUM_FILE = "json2eos_v2_checksums.json"
LEGACY_CHECKSUM_FILES = (".json2eos_v2_checksums.json",)
DEFAULT_SOURCE_PREFIX = "/scratch-cbe/"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Copy CustomNanoAOD scratch directories from a JSON file to EOS, "
            "file by file, using a checksum manifest to resume safely."
        )
    )
    parser.add_argument("--json", default=DEFAULT_JSON, help="JSON file containing CustomNanoAOD/dir.")
    parser.add_argument(
        "--logical-directory",
        default=DEFAULT_LOGICAL_DIRECTORY,
        help="EOS logical output directory under /store/...",
    )
    parser.add_argument(
        "--redirector",
        default=DEFAULT_REDIRECTOR,
        help="EOS redirector used for xrdcp/xrdfs.",
    )
    parser.add_argument(
        "--checksum-file",
        default=DEFAULT_CHECKSUM_FILE,
        help="Checksum manifest filename created under each top-level target directory.",
    )
    parser.add_argument(
        "--source-prefix",
        default=DEFAULT_SOURCE_PREFIX,
        help="Only source directories under this prefix are copied.",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Print commands and planned actions without running them.",
    )
    return parser.parse_args()


def load_dir_map(json_path):
    with open(json_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    try:
        dir_map = payload["CustomNanoAOD"]["dir"]
    except KeyError as exc:
        raise KeyError(f"Missing JSON key path CustomNanoAOD/dir in {json_path}") from exc

    if not isinstance(dir_map, dict):
        raise TypeError(f"Expected CustomNanoAOD/dir to be a mapping in {json_path}")

    return dir_map


def destination_suffix(source_path):
    if len(source_path.parts) < 2:
        raise ValueError(f"Source path is too short to preserve one parent directory: {source_path}")
    return Path(source_path.parts[-2]) / source_path.parts[-1]


def iter_source_files(source_root):
    for current_root, dirnames, filenames in os.walk(source_root):
        dirnames.sort()
        filenames.sort()
        current_root = Path(current_root)
        for filename in filenames:
            yield current_root / filename


def file_checksum(path, chunk_size=1024 * 1024):
    checksum = 1
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            checksum = zlib.adler32(chunk, checksum)
    return f"{checksum & 0xFFFFFFFF:08x}"


def format_completed_output(completed):
    lines = []
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if stdout:
        lines.append(stdout)
    if stderr:
        lines.append(stderr)
    return "\n".join(lines)


def check_valid_proxy():
    checks = [
        ["voms-proxy-info", "-exists", "-valid", "0:05"],
        ["grid-proxy-info", "-exists", "-valid", "0:05"],
    ]
    failures = []

    for cmd in checks:
        if shutil.which(cmd[0]) is None:
            continue

        completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
        if completed.returncode == 0:
            return True, cmd[0]

        output = format_completed_output(completed)
        if output:
            failures.append(f"{cmd[0]}: {output}")
        else:
            failures.append(f"{cmd[0]} exited with code {completed.returncode}")

    return False, failures


def ensure_authentication_ready():
    proxy_ok, details = check_valid_proxy()
    if proxy_ok:
        print(f"Authentication preflight: valid proxy found via {details}.")
        return

    x509_user_proxy = os.environ.get("X509_USER_PROXY")
    x509_user_cert = os.environ.get("X509_USER_CERT")
    x509_user_key = os.environ.get("X509_USER_KEY")
    interactive = sys.stdin.isatty()
    cert_path = Path(x509_user_cert).expanduser() if x509_user_cert else None
    key_path = Path(x509_user_key).expanduser() if x509_user_key else None
    cert_ready = bool(cert_path and cert_path.is_file() and os.access(cert_path, os.R_OK))
    key_ready = bool(key_path and key_path.is_file() and os.access(key_path, os.R_OK))

    if interactive and cert_ready and key_ready:
        print(
            "Authentication preflight: no valid proxy found, but readable PEM cert/key are set "
            "in an interactive shell. xrdcp may prompt for the PEM passphrase."
        )
        return

    lines = ["Authentication preflight failed: no valid X509 proxy was found."]
    if details:
        lines.append("Proxy checks:")
        for detail in details:
            lines.append(f"  - {detail}")

    if x509_user_proxy:
        lines.append(f"X509_USER_PROXY is set to: {x509_user_proxy}")
    if x509_user_cert:
        lines.append(f"X509_USER_CERT is set to: {x509_user_cert}")
    if x509_user_key:
        lines.append(f"X509_USER_KEY is set to: {x509_user_key}")

    if x509_user_cert and x509_user_key:
        if not (cert_ready and key_ready):
            lines.append("The PEM certificate/key paths are not both readable files.")
        if not interactive:
            lines.append(
                "A PEM certificate/key is configured, but this run is non-interactive, "
                "so xrdcp cannot ask for the PEM passphrase."
            )
            lines.append(
                "Run this from an interactive shell to unlock the PEM key or create a valid "
                "proxy first, then rerun the batch job."
            )
        else:
            lines.append(
                "A PEM certificate/key is configured, but it is not usable as-is. "
                "Create a valid proxy first or fix the cert/key paths, then rerun."
            )
    else:
        lines.append(
            "Create or refresh a valid proxy first, then rerun. For example, use your normal "
            "grid proxy workflow such as voms-proxy-init."
        )

    raise SystemExit("\n".join(lines))


@dataclass
class FileRecord:
    size: int
    adler32: str

    @classmethod
    def from_payload(cls, payload):
        return cls(size=int(payload["size"]), adler32=str(payload["adler32"]).lower())

    def to_payload(self):
        return {"size": self.size, "adler32": self.adler32}


class ChecksumManifest:
    def __init__(self, group_name, logical_path, records=None):
        self.group_name = group_name
        self.logical_path = logical_path
        self.records = records or {}

    @classmethod
    def empty(cls, group_name, logical_path):
        return cls(group_name=group_name, logical_path=logical_path, records={})

    @classmethod
    def from_text(cls, group_name, logical_path, text):
        payload = json.loads(text)
        file_payload = payload.get("files", {})
        records = {
            relative_path: FileRecord.from_payload(record)
            for relative_path, record in file_payload.items()
        }
        return cls(group_name=group_name, logical_path=logical_path, records=records)

    def matches(self, relative_path, size, checksum):
        record = self.records.get(relative_path)
        if record is None:
            return False
        return record.size == size and record.adler32 == checksum

    def remove(self, relative_path):
        self.records.pop(relative_path, None)

    def record_success(self, relative_path, size, checksum):
        self.records[relative_path] = FileRecord(size=size, adler32=checksum)

    def prune_prefix(self, prefix, keep_paths):
        prefix_with_sep = f"{prefix}/"
        stale_paths = [
            path
            for path in self.records
            if path.startswith(prefix_with_sep) and path not in keep_paths
        ]
        for path in stale_paths:
            del self.records[path]

    def to_text(self):
        payload = {
            "version": 2,
            "group": self.group_name,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "files": {
                relative_path: self.records[relative_path].to_payload()
                for relative_path in sorted(self.records)
            },
        }
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"


class XRootDClient:
    def __init__(self, redirector, dryrun=False):
        self.redirector = redirector
        self.dryrun = dryrun
        self.host = self._extract_host(redirector)
        self._known_directories = set()

    def _extract_host(self, redirector):
        parsed = urlparse(redirector)
        host = parsed.netloc or parsed.path.strip("/")
        if not host:
            raise ValueError(f"Could not extract host from redirector: {redirector}")
        return host

    def _remote_url(self, logical_path):
        logical_path = str(PurePosixPath(logical_path))
        if not logical_path.startswith("/"):
            raise ValueError(f"Logical path must be absolute: {logical_path}")
        return self.redirector.rstrip("/") + "/" + logical_path

    def _run(self, cmd, capture_output=False, check=True):
        print("CMD:", shlex.join(cmd))
        if self.dryrun:
            return None
        return subprocess.run(
            cmd,
            check=check,
            text=True,
            capture_output=capture_output,
        )

    def _stat_is_dir(self, logical_path):
        if logical_path in self._known_directories:
            return True

        cmd = ["xrdfs", self.host, "stat", "-q", "IsDir", logical_path]
        print("CMD:", shlex.join(cmd))
        if self.dryrun:
            self._known_directories.add(logical_path)
            return True

        completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
        if completed.returncode == 0:
            self._known_directories.add(logical_path)
            return True
        return False

    def ensure_directory(self, logical_dir):
        logical_dir = str(PurePosixPath(logical_dir))
        current = PurePosixPath("/")
        for part in PurePosixPath(logical_dir).parts:
            if part == "/":
                continue
            current = current / part
            current_str = str(current)
            if current_str in self._known_directories:
                continue
            if self._stat_is_dir(current_str):
                continue
            mkdir_cmd = ["xrdfs", self.host, "mkdir", current_str]
            self._run(mkdir_cmd)
            self._known_directories.add(current_str)

    def read_text(self, logical_path):
        cmd = ["xrdfs", self.host, "cat", logical_path]
        print("CMD:", shlex.join(cmd))
        if self.dryrun:
            return None
        completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
        if completed.returncode != 0:
            return None
        return completed.stdout

    def query_checksum(self, logical_path):
        cmd = ["xrdfs", self.host, "query", "checksum", logical_path]
        print("CMD:", shlex.join(cmd))
        if self.dryrun:
            return None
        completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
        if completed.returncode != 0:
            return None

        parts = completed.stdout.strip().split()
        if not parts:
            return None
        return parts[-1].lower()

    def copy_file(self, local_source, logical_destination, expected_checksum=None):
        self.ensure_directory(str(PurePosixPath(logical_destination).parent))
        cmd = [
            "xrdcp",
            "--force",
            str(local_source),
            self._remote_url(logical_destination),
        ]
        print("CMD:", shlex.join(cmd))
        if self.dryrun:
            return

        completed = subprocess.run(cmd, check=False, text=True)
        if completed.returncode == 0:
            return

        if expected_checksum is not None:
            remote_checksum = self.query_checksum(logical_destination)
            if remote_checksum == expected_checksum:
                print(
                    f"Checksum on EOS matches after xrdcp exit code {completed.returncode} for "
                    f"{logical_destination}; treating file as complete."
                )
                return

        raise subprocess.CalledProcessError(
            completed.returncode,
            cmd,
        )

    def upload_text(self, text, logical_destination, staging_directory):
        staging_directory = Path(staging_directory)
        temp_path = staging_directory / "chksum_tmp.json"
        print(f"STAGE: {temp_path}")
        if self.dryrun:
            print(f"WRITE: {logical_destination}")
            return

        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(text)

        try:
            self.copy_file(temp_path, logical_destination)
            temp_path.unlink(missing_ok=True)
        except Exception:
            print(f"Keeping staged manifest for inspection: {temp_path}")
            raise


class DirectoryTransfer:
    def __init__(
        self,
        key,
        source_path,
        suffix,
        logical_base,
        checksum_file,
        legacy_checksum_files,
        xrootd,
    ):
        self.key = key
        self.source_path = source_path
        self.suffix = PurePosixPath(suffix.as_posix())
        self.logical_base = PurePosixPath(logical_base)
        self.checksum_file = checksum_file
        self.legacy_checksum_files = tuple(legacy_checksum_files)
        self.xrootd = xrootd

    @property
    def group_name(self):
        return self.suffix.parent.as_posix()

    @property
    def group_logical_dir(self):
        return str(self.logical_base / self.suffix.parent)

    @property
    def manifest_logical_path(self):
        return str(PurePosixPath(self.group_logical_dir) / self.checksum_file)

    @property
    def manifest_candidate_paths(self):
        candidates = [self.manifest_logical_path]
        for filename in self.legacy_checksum_files:
            candidate = str(PurePosixPath(self.group_logical_dir) / filename)
            if candidate not in candidates:
                candidates.append(candidate)
        return candidates

    @property
    def target_logical_dir(self):
        return str(self.logical_base / self.suffix)

    @property
    def source_group_dir(self):
        return self.source_path.parent

    def source_manifest_key(self, relative_path):
        return str(PurePosixPath(self.suffix.name) / PurePosixPath(relative_path))

    def load_manifest(self, manifest_cache):
        for candidate_path in self.manifest_candidate_paths:
            cached_manifest = manifest_cache.get(candidate_path)
            if cached_manifest is not None:
                if candidate_path != self.manifest_logical_path:
                    manifest_cache[self.manifest_logical_path] = cached_manifest
                return cached_manifest

        manifest = None
        for candidate_path in self.manifest_candidate_paths:
            manifest_text = self.xrootd.read_text(candidate_path)
            if manifest_text is None:
                continue

            try:
                manifest = ChecksumManifest.from_text(
                    self.group_name, self.manifest_logical_path, manifest_text
                )
                if candidate_path != self.manifest_logical_path:
                    print(
                        f"Using legacy checksum manifest {candidate_path} for {self.group_name}."
                    )
                manifest_cache[candidate_path] = manifest
                break
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                print(f"Warning: could not parse checksum manifest {candidate_path}: {exc}")

        if manifest is None:
            manifest = ChecksumManifest.empty(self.group_name, self.manifest_logical_path)

        manifest_cache[self.manifest_logical_path] = manifest
        return manifest

    def run(self, manifest_cache):
        manifest = self.load_manifest(manifest_cache)
        print(f"{self.key} -> {self.target_logical_dir}")
        print(f"Checksum manifest: {self.manifest_logical_path}")

        keep_paths = set()
        copied = 0
        skipped = 0
        failed = []

        for source_file in iter_source_files(self.source_path):
            relative_to_source = source_file.relative_to(self.source_path).as_posix()
            manifest_key = self.source_manifest_key(relative_to_source)
            keep_paths.add(manifest_key)

            size = source_file.stat().st_size
            checksum = file_checksum(source_file)
            if manifest.matches(manifest_key, size, checksum):
                print(f"SKIP: {manifest_key} (already present in checksum manifest)")
                skipped += 1
                continue

            manifest.remove(manifest_key)
            logical_destination = str(PurePosixPath(self.target_logical_dir) / relative_to_source)
            print(f"COPY: {source_file} -> {logical_destination}")

            try:
                self.xrootd.copy_file(
                    source_file,
                    logical_destination,
                    expected_checksum=checksum,
                )
            except subprocess.CalledProcessError as exc:
                print(f"Transfer failed for {manifest_key}: {exc}")
                failed.append(manifest_key)
                continue

            manifest.record_success(manifest_key, size, checksum)
            copied += 1

        manifest.prune_prefix(self.suffix.name, keep_paths)
        print(
            f"Summary for {self.key}: {skipped} skipped, {copied} copied, {len(failed)} failed"
        )

        should_upload_manifest = not failed or manifest.records
        if should_upload_manifest:
            if failed:
                print(
                    f"Partial success for {self.key}; uploading refreshed checksum manifest with "
                    "completed files only."
                )
            try:
                self.xrootd.upload_text(
                    manifest.to_text(),
                    self.manifest_logical_path,
                    staging_directory=self.source_group_dir,
                )
            except subprocess.CalledProcessError as exc:
                print(f"Checksum manifest upload failed for {self.key}: {exc}")
                failed.append(f"{self.key}:manifest")

        return failed


def main():
    args = parse_args()
    json_path = Path(args.json).expanduser().resolve()
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    logical_directory = PurePosixPath(args.logical_directory)
    if not str(logical_directory).startswith("/store/"):
        raise ValueError(
            f"--logical-directory must start with /store/, got: {args.logical_directory}"
        )

    xrootd = XRootDClient(args.redirector, dryrun=args.dryrun)
    dir_map = load_dir_map(json_path)

    print(f"Using JSON: {json_path}")
    print(f"Using logical directory: {logical_directory}")
    print(f"Using EOS redirector: {args.redirector}")
    print(f"Using checksum filename: {args.checksum_file}")
    print(f"Found {len(dir_map)} entries in {json_path}")

    if args.dryrun:
        print("Authentication preflight: skipped in --dryrun mode.")
    else:
        ensure_authentication_ready()

    manifest_cache = {}
    failures = []

    for key, source in dir_map.items():
        if not str(source).startswith(args.source_prefix):
            print(f"Skipping {key}: source is not under {args.source_prefix} -> {source}")
            continue

        source_path = Path(source)
        if not source_path.is_dir():
            print(f"Missing source directory for {key}: {source}")
            failures.append(key)
            continue

        source_name = source_path.name
        if source_name != key:
            print(
                f"Warning for {key}: source directory name is {source_name}; "
                "checksum keys and destination paths use the source directory name."
            )

        suffix = destination_suffix(source_path)
        transfer = DirectoryTransfer(
            key=key,
            source_path=source_path,
            suffix=suffix,
            logical_base=logical_directory,
            checksum_file=args.checksum_file,
            legacy_checksum_files=LEGACY_CHECKSUM_FILES,
            xrootd=xrootd,
        )
        failed_files = transfer.run(manifest_cache)
        if failed_files:
            failures.append(key)

    if failures:
        print(f"Completed with {len(failures)} failed director(ies):")
        for key in failures:
            print(f"  - {key}")
        raise SystemExit(1)

    print("All transfers completed successfully.")


if __name__ == "__main__":
    main()
