import getpass
import json
import re
import shlex
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LIMITCALC_DIR = SCRIPT_DIR.parent
LIMIT_SCRIPT = SCRIPT_DIR / "AN-25-092_run_limits_v2.py"
SUBMIT_WRAPPER = LIMITCALC_DIR / "submit_limitcalc.sh"
DEFAULT_BASEDIR = Path(f"/scratch-cbe/users/{getpass.getuser()}/AN_plots/ParT_hists")


def workdir_from_uniquedir(uniquedir):
    workdir = Path(uniquedir).expanduser()
    return workdir if workdir.is_absolute() else DEFAULT_BASEDIR / workdir


class CmsswJobCommand:
    def shell_join(self, parts):
        return " ".join(shlex.quote(str(part)) for part in parts)

    def wrap(self, inner_command):
        return self.shell_join(["sbatch", str(SUBMIT_WRAPPER), inner_command])

    def limit_job(self, datacard, limit_dir):
        command = [
            "python3",
            "-u",
            str(LIMIT_SCRIPT),
            "--datacard",
            str(datacard),
            "--limitdir",
            str(limit_dir),
        ]
        return self.wrap(self.shell_join(command))


class JobIds:
    def __init__(self, path):
        self.path = Path(path)

    def write(self, jobs):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(jobs, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(jobs)} jobs to {self.path}")

    def read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def submit_jobs_in_json(self):
        jobs = self.read()
        for key, info in jobs.items():
            if info.get("status") != "prepared":
                continue

            result = subprocess.run(info["command"], shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                info["status"] = "submit_failed"
                info["stderr"] = result.stderr.strip()
                print(f"FAILED: {key}")
                continue

            match = re.search(r"\d+", result.stdout)
            info["jobid"] = match.group() if match else None
            info["status"] = "submitted"
            info["stdout"] = result.stdout.strip()
            print(result.stdout.strip())

        self.write(jobs)
