# Generate systematic-variation copies of a nominal plotter config.
#
# For each nominal config this produces:
#   <name>_puUp.yaml / <name>_puDown.yaml       -- PU weight mode "up"/"down"
#   <name>_jesUp.yaml / <name>_jesDown.yaml     -- corrections: JERC_syst: jes_up/jes_down
#   <name>_jerUp.yaml / <name>_jerDown.yaml     -- corrections: JERC_syst: jer_up/jer_down
#   <name>_unclUp.yaml / <name>_unclDown.yaml   -- corrections: JERC_syst: unclust_up/unclust_down
#
# Example (nominal analysis configs):
#   python3 make_syst_configs.py --config configs/AN-25-092_limitcalc_Run2.yaml configs/AN-25-092_limitcalc_Run3.yaml
#
# The variant configs are MC(signal)-only: do not use them to run on data.

import os
import copy
import yaml
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, nargs='+', required=True,
                    help='nominal config(s) to generate variations from')
parser.add_argument('--outdir', type=str, default='',
                    help='output directory (default: same directory as the nominal config)')
args = parser.parse_args()

variations = {
    'puUp':     ('PU', 'up'),
    'puDown':   ('PU', 'down'),
    'jesUp':    ('JERC_syst', 'jes_up'),
    'jesDown':  ('JERC_syst', 'jes_down'),
    'jerUp':    ('JERC_syst', 'jer_up'),
    'jerDown':  ('JERC_syst', 'jer_down'),
    'unclUp':   ('JERC_syst', 'unclust_up'),
    'unclDown': ('JERC_syst', 'unclust_down'),
}

for config in args.config:
    with open(config) as f:
        nominal = yaml.load(f, Loader=yaml.FullLoader)
    assert nominal.get('corrections'), "{}: no corrections block, nothing to vary!".format(config)
    outdir = args.outdir if args.outdir else os.path.dirname(config)
    base = os.path.splitext(os.path.basename(config))[0]
    for label, (key, value) in variations.items():
        cfg = copy.deepcopy(nominal)
        if key == 'PU':
            assert cfg['corrections'].get('PU'), "{}: no PU correction configured!".format(config)
            for year in cfg['corrections']['PU']:
                assert 'mode' in cfg['corrections']['PU'][year], \
                    "{}: PU block for {} has no mode key!".format(config, year)
                cfg['corrections']['PU'][year]['mode'] = value
        else:
            cfg['corrections']['JERC_syst'] = value
        outpath = os.path.join(outdir, '{}_{}.yaml'.format(base, label))
        with open(outpath, 'w') as f:
            yaml.dump(cfg, f, default_flow_style=None, sort_keys=False, width=200)
        print('Wrote', outpath)
