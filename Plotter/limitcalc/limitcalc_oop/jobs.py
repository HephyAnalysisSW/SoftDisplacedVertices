import getpass
import itertools
import json
import re
import shlex
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LIMITCALC_DIR = SCRIPT_DIR.parent
DATACARD_SCRIPT = SCRIPT_DIR / "AN-25-092_make_multiplane_datacards_v3.py"
LIMIT_SCRIPT = SCRIPT_DIR / "AN-25-092_run_limits_v3.py"
SUBMIT_WRAPPER = LIMITCALC_DIR / "submit_limitcalc.sh"
DEFAULT_SCRATCH_BASE = Path(f"/scratch-cbe/users/{getpass.getuser()}/AN_plots/ParT_hists")
DEFAULT_UNIQUEDIR = DEFAULT_SCRATCH_BASE / "AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3"


class ABCDScan:
    def __init__(
        self,
        uniquedir=DEFAULT_UNIQUEDIR,
        x_min=350.0,
        x_max=700.0,
        x_step=50.0,
        y_min=0.990,
        y_max=1.0,
        y_step=0.0002,
    ):
        self.uniquedir = self.resolve_uniquedir(uniquedir)
        self.base = self.uniquedir / "ABCDscan"
        self.x_values = self.scan_values(x_min, x_max, x_step)
        self.y_values = self.scan_values(y_min, y_max, y_step)

    def resolve_uniquedir(self, value):
        path = Path(value).expanduser()
        if path.is_absolute():
            return path
        return DEFAULT_SCRATCH_BASE / path

    def scan_values(self, scan_min, scan_max, scan_step):
        if scan_step <= 0:
            raise ValueError("Scan step must be positive.")
        if scan_max < scan_min:
            raise ValueError("Scan max must be greater than or equal to scan min.")

        # Same convention as the grid-search script: include the endpoint when
        # it lies on the grid, like np.arange(min, max + 0.5*step, step).
        values = []
        value = scan_min
        stop = scan_max + 0.5 * scan_step
        while value <= stop:
            values.append(round(value, 8))
            value += scan_step
        return values

    def points(self):
        return itertools.product(self.x_values, self.y_values)

    def scan_name(self, xcut, ycut):
        return f"MET{self.threshold_token(xcut)}_ML{self.threshold_token(ycut)}"

    def threshold_token(self, value):
        return f"{value:g}".replace("-", "m").replace(".", "p")

    def datacard_dir(self, xcut, ycut, mode):
        return self.base / self.scan_name(xcut, ycut) / "datacards" / mode

    def limit_dir(self, xcut, ycut, mode):
        return self.base / self.scan_name(xcut, ycut) / "limits" / mode


class CmsswJobCommand:
    def shell_join(self, parts):
        return " ".join(shlex.quote(str(part)) for part in parts)

    def wrap(self, inner_command):
        # Submission happens outside cmssw-el9. The wrapper enters cmssw-el9 and
        # runs the command there, so sbatch itself is never called in Singularity.
        return self.shell_join(["sbatch", str(SUBMIT_WRAPPER), inner_command])

    def datacard_job(self, uniquedir, output_dir, xcut, xlo, ycut, ylo, mode, use_data):
        command = [
            "python3",
            "-u",
            str(DATACARD_SCRIPT),
            "--histdir",
            str(uniquedir),
            "--output-dir",
            str(output_dir),
            "--xcut",
            str(xcut),
            "--xlo",
            str(xlo),
            "--ycut",
            str(ycut),
            "--ylo",
            str(ylo),
            "--mode",
            mode,
        ]
        if use_data:
            command.append("--data")
        return self.wrap(self.shell_join(command))

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

            # Keep the job_ids.json file as the source of truth for what was
            # submitted and what failed to submit.
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
