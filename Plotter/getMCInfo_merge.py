import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    chunks_dir = os.path.join(args.input_dir, "chunks")

    merged = {
        "totalsumWeights": {},
        "totalsumPassWeights": {},
        "samples": {},
    }

    for sample in sorted(os.listdir(chunks_dir)):
        sample_dir = os.path.join(chunks_dir, sample)
        if not os.path.isdir(sample_dir):
            continue

        total_sum_weights = 0.0
        total_sum_pass_weights = 0.0
        files = []

        for filename in sorted(os.listdir(sample_dir)):
            if not filename.endswith(".json"):
                continue

            chunk_path = os.path.join(sample_dir, filename)

            with open(chunk_path) as f:
                chunk = json.load(f)

            total_sum_weights += chunk["totalsumWeights"]
            total_sum_pass_weights += chunk["totalsumPassWeights"]
            files.extend(chunk["files"])

        merged["totalsumWeights"][sample] = total_sum_weights
        merged["totalsumPassWeights"][sample] = total_sum_pass_weights
        merged["samples"][sample] = {
            "totalsumWeights": total_sum_weights,
            "totalsumPassWeights": total_sum_pass_weights,
            "files": files,
        }

    with open(args.output, "w") as f:
        json.dump(merged, f, indent=2)


if __name__ == "__main__":
    main()