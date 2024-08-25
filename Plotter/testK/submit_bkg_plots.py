from subprocess import run, PIPE

samples = [
    "wjetstolnuht0100_2018",
    "wjetstolnuht0200_2018",
    "wjetstolnuht0400_2018",
    "wjetstolnuht0600_2018",
    "wjetstolnuht0800_2018",
    "wjetstolnuht1200_2018",
    "wjetstolnuht2500_2018",
    "zjetstonunuht0100_2018",
    "zjetstonunuht0200_2018",
    "zjetstonunuht0400_2018",
    "zjetstonunuht0600_2018",
    "zjetstonunuht0800_2018",
    "zjetstonunuht1200_2018",
    "zjetstonunuht2500_2018",
    "qcdht0050_2018",
    "qcdht0100_2018",
    "qcdht0200_2018",
    "qcdht0300_2018",
    "qcdht0500_2018",
    "qcdht0700_2018",
    "qcdht1000_2018",
    "qcdht1500_2018",
    "qcdht2000_2018",
]


# sample = "wjetstolnuht0100_2018"
outDir = "/scratch-cbe/users/alikaan.gueven/2018_limits"
config = "../configs/calc_limits.yaml"
json_path = "MC_RunIISummer20UL18.json"
tier = "CustomNanoAOD"


for sample in samples:
    command = f'submit_to_cpu.sh "python3 ../autoplotter.py  --sample {sample} --output {outDir} --config {config} --lumi 59800 --json {json_path} --datalabel {tier}"'
    # print(command)
    result = run(f'sbatch {command}', shell=True)
    # print(result.stdout.read())