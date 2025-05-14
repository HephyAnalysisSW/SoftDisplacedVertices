#!/usr/bin/python2
import subprocess

resubmit_list = [
    "crab_20250306_142547",
    "crab_20250306_143255",
    "crab_20250306_143959",
    "crab_20250306_144436"
]


for project in resubmit_list:
    print project
    subprocess.call(['crab', 'resubmit', 'crab_projects/' + project])
