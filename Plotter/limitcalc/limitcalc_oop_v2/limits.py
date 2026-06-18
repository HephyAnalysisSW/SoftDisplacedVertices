import subprocess
from pathlib import Path


class LimitRunner:
    def __init__(self, datacard, limitdir, debug=False):
        self.datacard = Path(datacard).resolve()
        self.limitdir = Path(limitdir).resolve()
        self.debug = debug

    def run(self):
        outdir = self.limitdir / self.datacard.stem
        outdir.mkdir(parents=True, exist_ok=True)

        # This script is run inside cmssw-el9 by submit_limitcalc.sh.
        command = [
            "combine",
            str(self.datacard),
            "-M", "AsymptoticLimits",
            "-v", "1",
#             "--run", "blind",
#             "--rMin", "0",
#             "--rMax", "5",
        ]

        print("Running:", " ".join(command))
        if self.debug:
            subprocess.run(command, cwd=outdir, check=True)
        else:
            subprocess.run(
                command,
                cwd=outdir,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        produced = outdir / "higgsCombineTest.AsymptoticLimits.mH120.root"
        if not produced.exists():
            raise FileNotFoundError(f"Missing combine output: {produced}")

        target = outdir / "limits.root"
        # Use a stable file name for downstream table-making scripts.
        produced.replace(target)
        print("Wrote:", target)
