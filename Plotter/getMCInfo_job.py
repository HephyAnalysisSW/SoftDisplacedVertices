from DataFormats.FWLite import Lumis, Handle
import argparse
import json
from pathlib import Path


def process_file(file_path):
    handle = Handle("GenFilterInfo")
    lumis = Lumis(str(file_path))

    sum_weights = 0.0
    sum_pass_weights = 0.0

    for lumi in lumis:
        lumi.getByLabel("genFilterEfficiencyProducer", handle)
        info = handle.product()
        sum_weights += info.sumWeights()
        sum_pass_weights += info.sumPassWeights()

    lumis._tfile.Close()

    return {
        "filename": str(file_path),
        "sumWeights": sum_weights,
        "sumPassWeights": sum_pass_weights,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--filelist", required=True)
    parser.add_argument("--outDir", required=True)
    parser.add_argument("--job-index", type=int, required=True)
    args = parser.parse_args()

    out_dir = Path(args.outDir) / "chunks" / args.sample
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.filelist) as f:
        files = [line.strip() for line in f if line.strip()]

    results = []
    total_sum_weights = 0.0
    total_sum_pass_weights = 0.0

    for file_path in files:
        file_result = process_file(file_path)
        results.append(file_result)
        total_sum_weights += file_result["sumWeights"]
        total_sum_pass_weights += file_result["sumPassWeights"]

    output = {
        "sample": args.sample,
        "job_index": args.job_index,
        "n_files": len(files),
        "totalsumWeights": total_sum_weights,
        "totalsumPassWeights": total_sum_pass_weights,
        "files": results,
    }

    output_path = out_dir / f"chunk_{args.job_index:05d}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()