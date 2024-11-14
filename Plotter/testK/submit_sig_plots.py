from subprocess import run, PIPE
samples = [
    
    "stop_M600_575_ct0p2_2018",
    "stop_M600_580_ct2_2018",
    "stop_M600_585_ct20_2018",
    "stop_M600_588_ct200_2018",

    "stop_M1000_975_ct0p2_2018",
    "stop_M1000_980_ct2_2018",
    "stop_M1000_985_ct20_2018",
    "stop_M1000_988_ct200_2018",
    
    "stop_M1400_1375_ct0p2_2018",
    "stop_M1400_1380_ct2_2018",
    "stop_M1400_1385_ct20_2018",
    "stop_M1400_1388_ct200_2018",
    
    "C1N2_M600_575_ct0p2_2018",
    "C1N2_M600_580_ct2_2018",
    "C1N2_M600_585_ct20_2018",
    "C1N2_M600_588_ct200_2018",
    
    "C1N2_M1000_975_ct0p2_2018",
    "C1N2_M1000_980_ct2_2018",
    "C1N2_M1000_985_ct20_2018",
    "C1N2_M1000_988_ct200_2018",
    
    "C1N2_M1400_1375_ct0p2_2018",
    "C1N2_M1400_1380_ct2_2018",
    "C1N2_M1400_1385_ct20_2018",
    "C1N2_M1400_1388_ct200_2018",
    
    
    
]


# sample = "wjetstolnuht0100_2018"
# outDir = "/scratch-cbe/users/alikaan.gueven/2018_limits/MET400/histograms"
outDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/vtx_reco/mc_data/sig/20241114"
# config = "../configs/mc_jetmet.yaml"
# config = "../configs/vtx_reco_unc_2018.yaml" # "../configs/plotconfig_MC2.yaml" # "../configs/mc_limits.yaml"
config = "../configs/vtx_reco_data_2018.yaml"
# config = "../configs/vtx_reco_data_genmatch_2018.yaml"
json_path = "PrivateSignal_v3.json"
tier = "CustomNanoAODv3"

for sample in samples:
    command = f'submit_to_cpu.sh "python3 ../autoplotter.py  --sample {sample} --output {outDir} --config {config} --lumi 59800 --json {json_path} --datalabel {tier}"'
    # print(command)
    result = run(f'sbatch {command}', shell=True)
    # print(result.stdout.read())