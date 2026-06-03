#!/usr/bin/env python3

import importlib.util
import sys
from pathlib import Path


UNIQUEDIR = "AN-25-092_ML_plots_limitcalc_privateprod_260528"
TARGETS = [
    "stop_M1000_975_ct0p2_BR0p1",
    "stop_M1000_975_ct0p2_BR0p5",
    "stop_M1000_975_ct0p2_BR1",
    "stop_M1000_980_ct2_BR0p1",
    "stop_M1000_980_ct2_BR0p5",
    "stop_M1000_980_ct2_BR1",
    "stop_M1000_985_ct20_BR0p1",
    "stop_M1000_985_ct20_BR0p5",
    "stop_M1000_985_ct20_BR1",
    "stop_M1000_988_ct200_BR0p1",
    "stop_M1000_988_ct200_BR0p5",
    "stop_M1000_988_ct200_BR1",
]


path = Path(__file__).with_name("AN-25-092_ABCD_scan_v2.py")
spec = importlib.util.spec_from_file_location("abcd_scan_v2", path)
abcd_scan_v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(abcd_scan_v2)

sys.argv = [
    str(path),
    "--uniquedir",
    UNIQUEDIR,
    "--skip-closure",
    "--background-source",
    "data",
    "--target",
    *TARGETS,
]
abcd_scan_v2.main()
