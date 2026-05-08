import argparse
import json
import os
import shlex
import subprocess
import zlib
from pathlib import Path


DEFAULT_JSON = (
    "/users/alikaan.gueven/AOD_to_nanoAOD/Plotter_run3/"
    "CMSSW_15_0_5/src/SoftDisplacedVertices/Samples/json/scratch_MC24.json"
)
DEFAULT_MOUNTDIR = "/eos/vbc/experiments/cms/store/user/aguven/scratch_backup"
DEFAULT_LOGICAL_DIRECTORY = "/store/user/aguven/scratch_backup"
DEFAULT_REDIRECTOR = "root://eos.grid.vbc.ac.at/"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy CustomNanoAOD scratch directories from a JSON file to EOS with xrdcp."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Pass --force to xrdcp and allow overwriting an existing destination.",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Print commands without running them.",
    )
    return parser.parse_args()


def load_dir_map():
    json_path = Path(DEFAULT_JSON).expanduser().resolve()
    with open(json_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    try:
        dir_map = payload["CustomNanoAOD"]["dir"]
    except KeyError as exc:
        raise KeyError(f"Missing JSON key path CustomNanoAOD/dir in {json_path}") from exc

    if not isinstance(dir_map, dict):
        raise TypeError(f"Expected CustomNanoAOD/dir to be a mapping in {json_path}")

    return dir_map


def build_xrdcp_cmd(source, destination, force=False, recursive=False):
    cmd = ["xrdcp"]
    if force:
        cmd.append("--force")
    cmd.extend(["--cksum", "auto"])
    if recursive:
        cmd.append("--recursive")
    cmd.extend([str(source), str(destination)])
    return cmd


def build_remote_base():
    if not DEFAULT_LOGICAL_DIRECTORY.startswith("/store/"):
        raise ValueError(
            f"DEFAULT_LOGICAL_DIRECTORY must start with /store/, got: {DEFAULT_LOGICAL_DIRECTORY}"
        )
    return DEFAULT_REDIRECTOR.rstrip("/") + "/" + DEFAULT_LOGICAL_DIRECTORY


def destination_suffix(source_path):
    if len(source_path.parts) < 2:
        raise ValueError(f"Source path is too short to preserve one parent directory: {source_path}")
    return Path(source_path.parts[-2]) / source_path.parts[-1]


def directory_snapshot(directory):
    snapshot = {}
    root = Path(directory)
    for current_root, _, files in os.walk(root):
        current_root = Path(current_root)
        for filename in files:
            path = current_root / filename
            snapshot[path.relative_to(root).as_posix()] = path.stat().st_size
    return snapshot


def directories_match(source, destination):
    source = Path(source)
    destination = Path(destination)
    if not source.is_dir() or not destination.is_dir():
        return False
    return directory_snapshot(source) == directory_snapshot(destination)


def file_checksum(path, chunk_size=1024 * 1024):
    checksum = 1
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            checksum = zlib.adler32(chunk, checksum)
    return checksum & 0xFFFFFFFF


def files_requiring_transfer(source, destination):
    source = Path(source)
    destination = Path(destination)
    files_to_copy = []
    extra_destination_files = []

    if not destination.exists():
        for current_root, _, files in os.walk(source):
            current_root = Path(current_root)
            for filename in files:
                path = current_root / filename
                files_to_copy.append(path.relative_to(source))
        return files_to_copy, extra_destination_files

    source_files = {}
    for current_root, _, files in os.walk(source):
        current_root = Path(current_root)
        for filename in files:
            path = current_root / filename
            source_files[path.relative_to(source)] = path

    destination_files = {}
    for current_root, _, files in os.walk(destination):
        current_root = Path(current_root)
        for filename in files:
            path = current_root / filename
            destination_files[path.relative_to(destination)] = path

    for relative_path, source_path in source_files.items():
        destination_path = destination_files.get(relative_path)
        if destination_path is None:
            files_to_copy.append(relative_path)
            continue

        source_size = source_path.stat().st_size
        destination_size = destination_path.stat().st_size
        if source_size != destination_size:
            files_to_copy.append(relative_path)
            continue

        if file_checksum(source_path) != file_checksum(destination_path):
            files_to_copy.append(relative_path)

    for relative_path in destination_files:
        if relative_path not in source_files:
            extra_destination_files.append(relative_path)

    return files_to_copy, extra_destination_files


def main():
    args = parse_args()
    json_path = Path(DEFAULT_JSON).expanduser().resolve()
    local_outdir = Path(DEFAULT_MOUNTDIR).expanduser().resolve()
    remote_outdir = build_remote_base()

    dir_map = load_dir_map()

    os.makedirs(local_outdir, exist_ok=True)
    print(f"Using JSON: {json_path}")
    print(f"Using EOS mount: {local_outdir}")
    print(f"Using logical directory: {DEFAULT_LOGICAL_DIRECTORY}")
    print(f"Using EOS redirector: {DEFAULT_REDIRECTOR}")
    print(f"Remote destination base: {remote_outdir}")
    print(f"Found {len(dir_map)} entries in {json_path}")

    failures = []
    for key, source in dir_map.items():
        if not str(source).startswith("/scratch-cbe/"):
            print(f"Skipping {key}: source is not under /scratch-cbe -> {source}")
            continue

        source_path = Path(source)
        if not source_path.exists():
            print(f"Missing source for {key}: {source}")
            failures.append(key)
            continue

        source_name = source_path.name
        if source_name != key:
            print(
                f"Warning for {key}: source directory name is {source_name}; "
                f"destination will use the source directory name."
            )

        suffix = destination_suffix(source_path)
        local_destination = local_outdir / suffix
        legacy_nested_destination = local_destination / source_name
        local_parent = local_destination.parent
        remote_parent = f"{remote_outdir.rstrip('/')}/{suffix.parent.as_posix()}"
        remote_destination = f"{remote_outdir.rstrip('/')}/{suffix.as_posix()}"

        if not args.dryrun:
            os.makedirs(local_parent, exist_ok=True)

        if local_destination.exists():
            if not local_destination.is_dir():
                print(
                    f"Refusing {key}: destination exists but is not a directory -> "
                    f"{local_destination}"
                )
                failures.append(key)
                continue

            if directories_match(source_path, local_destination):
                print(f"Skipping {key}: destination already matches source -> {local_destination}")
                continue

            if legacy_nested_destination.exists():
                if directories_match(source_path, legacy_nested_destination):
                    print(
                        f"Refusing {key}: found legacy nested output at "
                        f"{legacy_nested_destination}. Clean it manually before retrying."
                    )
                else:
                    print(
                        f"Refusing {key}: found incomplete legacy nested output at "
                        f"{legacy_nested_destination}. Clean it manually before retrying."
                    )
                failures.append(key)
                continue

            if not args.force:
                print(
                    f"Refusing {key}: destination exists but does not match source -> "
                    f"{local_destination} (use --force to overwrite)"
                )
                failures.append(key)
                continue
        if args.force and local_destination.exists():
            files_to_copy, extra_destination_files = files_requiring_transfer(
                source_path, local_destination
            )
            if not files_to_copy:
                print(
                    f"Skipping {key}: all source files already match destination -> "
                    f"{local_destination}"
                )
                if extra_destination_files:
                    print(
                        f"Note for {key}: destination contains {len(extra_destination_files)} "
                        "extra file(s) not present in source; leaving them untouched."
                    )
                continue

            print(
                f"{key} -> {remote_destination} "
                f"(copying {len(files_to_copy)} non-matching file(s))"
            )
            if extra_destination_files:
                print(
                    f"Note for {key}: destination contains {len(extra_destination_files)} "
                    "extra file(s) not present in source; leaving them untouched."
                )

            transfer_failed = False
            for relative_path in files_to_copy:
                source_file = source_path / relative_path
                local_target = local_destination / relative_path
                remote_target = f"{remote_destination.rstrip('/')}/{relative_path.as_posix()}"

                print(f"MKDIR: {local_target.parent}")
                cmd = build_xrdcp_cmd(source_file, remote_target, force=True)
                print("CMD:", shlex.join(cmd))

                if args.dryrun:
                    continue

                os.makedirs(local_target.parent, exist_ok=True)

                try:
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError as exc:
                    if local_target.is_file():
                        source_size = source_file.stat().st_size
                        target_size = local_target.stat().st_size
                        if source_size == target_size and (
                            file_checksum(source_file) == file_checksum(local_target)
                        ):
                            print(
                                f"Transfer for {key}:{relative_path.as_posix()} returned "
                                f"exit code {exc.returncode}, but the destination file matches "
                                "the source. Treating it as complete."
                            )
                            continue

                    print(f"Transfer failed for {key}:{relative_path.as_posix()}: {exc}")
                    transfer_failed = True

            if transfer_failed:
                failures.append(key)
            continue

        cmd = build_xrdcp_cmd(source, remote_parent, force=args.force, recursive=True)
        print(f"{key} -> {remote_destination}")
        print(f"MKDIR: {local_parent}")
        print("CMD:", shlex.join(cmd))

        if args.dryrun:
            continue

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            if directories_match(source_path, local_destination):
                print(
                    f"Transfer for {key} returned exit code {exc.returncode}, "
                    f"but the local destination matches the source. Treating it as complete."
                )
                continue

            print(f"Transfer failed for {key}: {exc}")
            failures.append(key)

    if failures:
        print(f"Completed with {len(failures)} failures:")
        for key in failures:
            print(f"  - {key}")
        raise SystemExit(1)

    print("All transfers completed successfully.")


if __name__ == "__main__":
    main()
