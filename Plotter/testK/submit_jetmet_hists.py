import os
from subprocess import run, PIPE, Popen

import SoftDisplacedVertices.Samples.Samples as s

samples = []
# samples.extend(s.stop_2018)
# samples.extend(s.c1n2_2018)

samples.extend(s.stop_2017)

configs = [
    # "jet_jerdown_met_smear_jerdown.yaml",
    # "jet_jerup_met_smear_jerup.yaml",
    # "jet_jesdown_met_smear_jesdown.yaml",
    # "jet_jesup_met_smear_jesup.yaml",
    # "jet_nom_met_smear.yaml",
    # "jet_nom_met_smear_ueup.yaml",
    # "jet_nom_met_smear_uedown.yaml"
    "jet_jerdown_met_smear_jerdown_2017.yaml",
    "jet_jerup_met_smear_jerup_2017.yaml",
    "jet_jesdown_met_smear_jesdown_2017.yaml",
    "jet_jesup_met_smear_jesup_2017.yaml",
    "jet_nom_met_smear_2017.yaml",
    "jet_nom_met_smear_ueup_2017.yaml",
    "jet_nom_met_smear_uedown_2017.yaml"
]

for sample in samples:
    for config in configs:
        name = sample.name
        outDir = os.path.join("/scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms", config[:-5])
        config = os.path.join("../configs/", config)
        command = f'submit_to_cpu.sh "python3 ../autoplotter.py  --sample {name} --output {outDir} --config {config} --lumi 162440 --json PrivateSignal_v3_jetmet.json  --datalabel CustomNanoAODv3"'
        # command = f'submit_to_cpu.sh "python3 ../autoplotter.py  --sample {name} --output {outDir} --config {config} --lumi 59800 --json PrivateSignal_v3_jetmet.json  --datalabel CustomNanoAODv3"'

        # command = f'python3 ../autoplotter.py  --sample {name} --output {outDir} --config {config} --lumi 59800 --json PrivateSignal_v3_jetmet.json  --datalabel CustomNanoAODv3'
        # print(command)
        result = run(f'sbatch {command}', shell=True)
        # result = Popen(command, shell=True, stdin=None, stdout=None, stderr=None)