import argparse
import fnmatch
import json
import os
import re
from subprocess import run


def chunk_list(items, n):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def collect_root_files(sample_dir):
    root_files = []

    for root, dirs, files in os.walk(sample_dir):
        for filename in fnmatch.filter(files, "*.root"):
            root_files.append(os.path.join(root, filename))

    root_files.sort()
    return root_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--outDir", required=True)
    parser.add_argument("--files-per-job", type=int, required=True)
    parser.add_argument("--worker", default="process_metadata_chunk.py")
    parser.add_argument("--submit-script", default="submit_to_cpu_medium.sh")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    os.makedirs(args.outDir, exist_ok=True)

    filelist_base_dir = os.path.join(args.outDir, "filelists")
    os.makedirs(filelist_base_dir, exist_ok=True)

    with open(args.json) as f:
        sample_dirs = json.load(f)["CustomMiniAOD"]["dir"]

    total_jobs = 0
    job_dict = {}

    for sample, sample_dir in sample_dirs.items():
        root_files = collect_root_files(sample_dir)

        if len(root_files) == 0:
            print(f"[skip] {sample}: no ROOT files found")
            continue

        sample_filelist_dir = os.path.join(filelist_base_dir, sample)
        os.makedirs(sample_filelist_dir, exist_ok=True)

        for job_index, chunk in enumerate(chunk_list(root_files, args.files_per_job)):
            filelist_path = os.path.join(sample_filelist_dir, f"chunk_{job_index:05d}.txt")

            with open(filelist_path, "w") as f:
                for file_path in chunk:
                    f.write(file_path + "\n")

            python_command = (
                f'python3 -u {args.worker} '
                f'--sample {sample} '
                f'--filelist {filelist_path} '
                f'--outDir {args.outDir} '
                f'--job-index {job_index}'
            )

            command = f'{args.submit_script} "{python_command}"'
            full_command = f"sbatch {command}"

            chunk_name = f"{sample}_chunk_{job_index:05d}"

            if args.dry_run:
                print(full_command)
                job_dict[chunk_name] = {
                    "sample": sample,
                    "chunk": job_index,
                    "command": full_command,
                    "filelist": filelist_path,
                    "n_files": len(chunk),
                }
            else:
                result = run(full_command, shell=True, capture_output=True, text=True)
                job_id = re.search(r"\d+", result.stdout).group()

                job_dict[chunk_name] = {
                    "sample": sample,
                    "chunk": job_index,
                    "command": full_command,
                    "jobid": job_id,
                    "filelist": filelist_path,
                    "n_files": len(chunk),
                }

                print(result.stdout.strip())

            total_jobs += 1

        print(f"[submitted] {sample}: {len(root_files)} files")

    out_json_path = os.path.join(args.outDir, "job_ids.json")
    print(f"\nWriting to {out_json_path}...\n")
    with open(out_json_path, "w") as f:
        json.dump(job_dict, f, indent=2)

    print(f"\nFinished. Total jobs: {total_jobs}")
    print("Exiting...")


if __name__ == "__main__":
    main()