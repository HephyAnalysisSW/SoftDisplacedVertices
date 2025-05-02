#!/usr/bin/python3
import subprocess

resubmit_list = [
    # "crab_20250306_142547",
    # "crab_20250306_143255",
    # "crab_20250306_143959",
    # "crab_20250306_144436",
    "crab_20250306_183641", "crab_20250306_184840", "crab_20250306_191521", "crab_20250306_185149", "crab_20250306_192224",
    "crab_20250306_190552", "crab_20250306_182957", "crab_20250306_185851", "crab_20250306_184613"
]


for project in resubmit_list:
    print(project)
    subprocess.call(['crab', 'resubmit', 'crab_projects/' + project])
