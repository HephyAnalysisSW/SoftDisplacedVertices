from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory


DATACARDS_DIR = Path(
    "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/"
    "AN-25-092_ML_plots_limitcalc/datacards"
)

YEARS = [
    "2017",
    "2018",
    "2022Pre",
    "2022Post",
    "2023Pre",
    "2023Post",
    "2024",
]

LABELS = {
    "2017": "y2017",
    "2018": "y2018",
    "2022Pre": "y2022pre",
    "2022Post": "y2022post",
    "2023Pre": "y2023pre",
    "2023Post": "y2023post",
    "2024": "y2024",
}


def collect_cards():
    cards_by_sample = {}
    for year in YEARS:
        year_dir = DATACARDS_DIR / year
        if not year_dir.is_dir():
            raise FileNotFoundError(f"Missing datacard year directory: {year_dir}")

        for card_path in sorted(year_dir.glob("*.txt")):
            cards_by_sample.setdefault(card_path.name, {})[year] = card_path

    return cards_by_sample


def rewrite_rateparams(input_path, output_path, label):
    text = input_path.read_text(encoding="utf-8")
    rate_names = []
    lines = text.splitlines()

    for line in lines:
        fields = line.split()
        if len(fields) >= 2 and fields[0].startswith("rate_") and fields[1] == "rateParam":
            rate_names.append(fields[0])

    replacements = {
        rate_name: f"{label}_{rate_name}"
        for rate_name in sorted(rate_names, key=len, reverse=True)
    }

    rewritten_lines = []
    for line in lines:
        fields = line.split()
        if len(fields) >= 2 and fields[0].startswith("rate_") and fields[1] == "rateParam":
            for old_name, new_name in replacements.items():
                line = line.replace(old_name, new_name)
        rewritten_lines.append(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(rewritten_lines) + "\n", encoding="utf-8")


def rewrite_combination_header(output_path, cards):
    lines = output_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return

    source_cards = "  ".join(
        f"{LABELS[year]}={cards[year]}"
        for year in YEARS
    )
    lines[0] = f"Combination of {source_cards}"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def combine_sample(sample_name, cards, tmpdir):
    output_dir = DATACARDS_DIR / "combined"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / sample_name

    missing_years = [year for year in YEARS if year not in cards]
    if missing_years:
        print(f"Skipping {sample_name}: missing {', '.join(missing_years)}")
        return False

    cmd = ["combineCards.py"]
    for year in YEARS:
        label = LABELS[year]
        prepared_path = Path(tmpdir) / year / sample_name
        rewrite_rateparams(cards[year], prepared_path, label)
        cmd.append(f"{label}={prepared_path}")

    print("CMD:")
    print(" ".join(str(piece) for piece in cmd) + f" > {output_path}")
    print()

    with output_path.open("w", encoding="utf-8") as output_file:
        run(cmd, check=True, stdout=output_file)

    rewrite_combination_header(output_path, cards)

    print("-" * 80)
    print()
    return True


def main():
    cards_by_sample = collect_cards()
    combined = 0
    with TemporaryDirectory(prefix="combine_datacards_") as tmpdir:
        for sample_name, cards in sorted(cards_by_sample.items()):
            if combine_sample(sample_name, cards, tmpdir):
                combined += 1

    print(f"Combined {combined} datacards into {DATACARDS_DIR / 'combined'}")


if __name__ == "__main__":
    main()
