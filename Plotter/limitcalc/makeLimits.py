#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

def main(datacard: str, limitdir: str, DEBUG: bool = False):
    datacard = Path(datacard).resolve()
    limitdir = Path(limitdir).resolve()

    sampledir = datacard.stem                      # full name without .txt
    outdir = limitdir / sampledir
    outdir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "combine",
        str(datacard),
        "-M", "AsymptoticLimits",
        "-v", "1",
        "--run", "blind",
        "--rMin", "0",
        "--rMax", "5",
    ]
    print("Running:", " ".join(cmd))

    # Let combine write its output into outdir
    if DEBUG:
        subprocess.run(cmd, cwd=outdir, check=True)
    else:
        subprocess.run(
            cmd,
            cwd=outdir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    produced = outdir / "higgsCombineTest.AsymptoticLimits.mH120.root"
    if not produced.exists():
        raise FileNotFoundError(f"Missing combine output: {produced}")

    target = outdir / "limits.root"
    produced.replace(target)  # atomic rename on same filesystem

    print("Wrote:", target)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datacard", required=True, help="path to the datacard (.txt)")
    ap.add_argument("--limitdir", required=True, help="base output directory")
    ap.add_argument("--debug", action="store_true", help="show combine output")
    args = ap.parse_args()
    main(args.datacard, args.limitdir, DEBUG=args.debug)
