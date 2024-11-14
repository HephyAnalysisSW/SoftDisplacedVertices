from subprocess import run, PIPE

samples = [
    "met2018a",
    "met2018b",
    "met2018c",
    "met2018d",
    "met2018d_rest"
]


# sample = "wjetstolnuht0100_2018"
outDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/vtx_reco/mc_data/data/20241114"
# config = "../configs/plotconfig_template.yaml" # "../configs/plotconfig_MC2.yaml" # "../configs/mc_limits.yaml"
config = "../configs/vtx_reco_data_2018.yaml"
json_path = "Data_production_20240326.json"
tier = "CustomNanoAOD"


for sample in samples:
    command = f'submit_to_cpu.sh "python3 ../autoplotter.py  --sample {sample} --output {outDir} --config {config} --lumi -1 --json {json_path} --datalabel {tier} --data"'
    # print(command)
    result = run(f'sbatch {command}', shell=True)
    # print(result.stdout.read())