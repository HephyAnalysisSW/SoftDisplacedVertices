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
    "ttbar_2018",
    "st_tch_tbar_2018",
    "st_tch_t_2018",
    "st_tW_tbar_2018",
    "st_tW_t_2018"
]


# sample = "wjetstolnuht0100_2018"
outDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/vtx_reco/mc_data/bkg/20241114"
# config = "../configs/vtx_reco_unc_2018.yaml" # "../configs/plotconfig_MC2.yaml" # "../configs/mc_limits.yaml"
config = "../configs/vtx_reco_data_2018.yaml"
json_path = "MC_RunIISummer20UL18.json"
tier = "CustomNanoAOD"


for sample in samples:
    command = f'submit_to_cpu.sh "python3 ../autoplotter.py  --sample {sample} --output {outDir} --config {config} --lumi 59800 --json {json_path} --datalabel {tier}"'
    # print(command)
    result = run(f'sbatch {command}', shell=True)
    # print(result.stdout.read())