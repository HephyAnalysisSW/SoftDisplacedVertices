"""
Various utility scripts

"""


import re
import numpy as np
from types import SimpleNamespace
# from pathlib import Path
# import numpy as np
# import pandas as pd
# import ROOT


# Just parses the sample name.

def parse_M(name):
    m = re.search(r"_M(\d+)", name)
    return int(m.group(1))


def parse_M2(name):
    m = re.search(r"_(\d+)_ct", name)
    return int(m.group(1))


def parse_ct(name):
    m = re.search(r"ct([0-9]+(?:p[0-9]+)?)", name)
    return float(m.group(1).replace("p", "."))


def model_group(name: str) -> str:
    if name.startswith("C1N2"):
        return "C1N2"
    if name.startswith("stop"):
        return "stop"


def parse_signal_name(name):
    M = parse_M(name)
    M2 = parse_M2(name)

    return SimpleNamespace(
        name=name,
        model=model_group(name),
        M=M,
        M2=M2,
        dM=M - M2,
        ct=parse_ct(name),
    )


def get_stop_4body_width(m, dm):
    # this calculates the 4-body partial decay width 
    # m is the LLP mass and dm is the mass splitting
    return (9 * 28 * (1.98 * 1e-14) * ((dm) / 30) ** 8 * (400 / m))

def get_stop_ctau_for_br(m, dm, br):
    # this calculates the proper length of the stop
    # m is the LLP mass and dm is the mass splitting
    width_4body = get_stop_4body_width(m, dm)
    width_total = width_4body / br
    return 1.973269788e-13 / width_total

def get_ctau_weight(ct, origin, target):
    clipct = np.clip(ct,a_min=0,a_max=origin)
    ratio = (origin / target) * np.exp(clipct * 10 * ((1 / origin) - (1 / target)))
    return ratio

def get_stop_decay_mode_br_weight(decaymode, origin=0.5, target=0.5):
    w4 = target / origin              # 4-body channel
    w2 = (1 - target) / (1 - origin)  # 2-body channel
    w = w4 * (decaymode == 1) + w2 * (decaymode == 2)
    return w