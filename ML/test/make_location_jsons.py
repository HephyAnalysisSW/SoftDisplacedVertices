"""Write eos/scratch location JSONs (style of Samples/json/eos_MC.json) for the NanoAOD_ParTScore_K production.
Sample lists and source JSONs are the ones in ML/test/submit_jobs_ParTScore_K.py; MC totalsumWeights come from
the source JSONs' CustomNanoAOD totalsumWeights."""
import os, json
from collections import OrderedDict
import SoftDisplacedVertices.Samples.Samples as s

label = "CustomNanoAOD"
jsondir = os.path.join(os.environ['CMSSW_BASE'], 'src/SoftDisplacedVertices/Samples/json')
locations = {
    "eos": "/eos/vbc/experiments/cms/store/user/lian/NanoAOD_ParTScore_K",
    "scratch": "/scratch-cbe/users/ang.li/SoftDV/NanoAOD_ParTScore_K",
}

# copied from era_config in ML/test/submit_jobs_ParTScore_K.py
mc = [
    (s.znunu_2017+s.wlnu_2017+s.qcd_2017+s.top_2017, "MC_RunIISummer20UL17_20241003.json"),
    (s.znunu_2018+s.wlnu_2018+s.qcd_2018+s.top_2018, "MC_RunIISummer20UL18_20241003.json"),
    (s.znunu_2022Pre+s.wlnu_2022Pre+s.qcd_2022Pre+s.top_2022Pre
     + s.znunu_2022Post+s.wlnu_2022Post+s.qcd_2022Post+s.top_2022Post, "MC_Run3Summer22_20250621.json"),
    (s.znunu_2023Pre+s.wlnu_2023Pre+s.qcd_2023Pre+s.top_2023Pre
     + s.znunu_2023Post+s.wlnu_2023Post+s.qcd_2023Post+s.top_2023Post, "MC_Run3Summer23_20250409.json"),
    (s.znunu_2024+s.wlnu_2024+s.qcd_2024+s.top_2024, "MC_Run3Summer24_20260330.json"),
]
data = [
    (s.met_2017, "Data_MET2017.json"),
    (s.met_2018, "Data_production_20240326.json"),
    (s.met_2022Pre+s.met_2022Post+s.met_2023Pre+s.met_2023Post, "Data_Run3_jetmet_official.json"),
    (s.met_2024, "Data_Run3_jetmet_official.json"),
]


def build(groups, base, with_weights):
    dirs, weights = OrderedDict(), OrderedDict()
    for samples, jsonfn in groups:
        src = json.load(open(os.path.join(jsondir, jsonfn)))[label]
        for sp in samples:
            assert sp.name not in dirs, sp.name
            dirs[sp.name] = os.path.join(base, sp.name)
            if with_weights:
                weights[sp.name] = src["totalsumWeights"][sp.name]
    out = OrderedDict(dir=dirs)
    if with_weights:
        out["totalsumWeights"] = weights
    return OrderedDict([(label, out)])


outdir = os.environ["OUTDIR"]
for loc, base in locations.items():
    for kind, groups in (("MC", mc), ("data", data)):
        fn = os.path.join(outdir, "%s_%s_ParTScore_K.json" % (loc, kind))
        assert not os.path.exists(fn), fn
        d = build(groups, base, kind == "MC")
        with open(fn, "w") as f:
            json.dump(d, f, indent=4)
            f.write("\n")
        print(fn, len(d[label]["dir"]), "samples")
