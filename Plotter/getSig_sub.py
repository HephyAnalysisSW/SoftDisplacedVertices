import os
import uuid
import shutil
import itertools
import ctypes
import subprocess
import math
import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import matplotlib as mpl
import SoftDisplacedVertices.Plotter.plotter as p
import SoftDisplacedVertices.Plotter.plot_setting as ps
import SoftDisplacedVertices.Samples.Samples as s
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str,
                        help='input dir')
args = parser.parse_args()

def dict_product(dicts):
    return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))

def getbErr(b,uncert,l,syst):
  # Poisson statistical uncertainty
  # Pearson’s chi2 intervals
  b_low = math.sqrt(b*l+l*l/4)-l/2
  b_high = math.sqrt(b*l+l*l/4)+l/2
  b_stat = max(abs(b_high),(b_low))/b
  b_syst2 = syst*syst + (uncert/b)*(uncert/b)
  #return b*math.sqrt(b_stat*b_stat + b_syst*b_syst)
  return b*math.sqrt(b_syst2)

def sig(s,b,b_err):
  return math.sqrt(2*((s+b)*math.log(((s+b)*(b+b_err*b_err))/(b*b+(s+b)*b_err*b_err)) - (b*b/(b_err*b_err))*math.log(1+(b_err*b_err*s)/(b*(b+b_err*b_err)))))

if __name__=="__main__":
  scan_params = {
      '__DPHIMET__': [1.5],
      '__DPHIJET__': [1],
      '__LXYSIG__': [0,10,20],
      '__PANGLE__': [0,0.1,0.2],
      '__NGOODTK__': [0,1,2],
      '__TKDXYSIG__': [2,3,4],
      '__TKDXYDZ__': [0.1,0.15,0.2,0.25,0.3],
      '__ML__': [0.97,0.98,0.99],
      }

  sig_fns = [
      "stop_M600_580_ct2_2018_hist.root",
      "stop_M600_585_ct20_2018_hist.root",
      "stop_M600_588_ct200_2018_hist.root",
      "stop_M1000_980_ct2_2018_hist.root",
      "stop_M1000_985_ct20_2018_hist.root",
      "stop_M1000_988_ct200_2018_hist.root",
      ]

  SRname = "MLSR_evt/MET_pt"

  max_sig = [0] * len(sig_fns)
  max_sig_cuts = [''] * len(sig_fns)



  jobf = open('jobshadd.sh',"w")
  for d in os.listdir(args.input):
    #if not d=='cutscan__DPHIMET__1p5__DPHIJET__1__LXYSIG__20__PANGLE__0p2__NGOODTK__2__TKDXYSIG__4__TKDXYDZ__0p25':
    #  continue
    if not ("background_2018_hist.root" in os.listdir(os.path.join(args.input,d))):
      haddcmd = "hadd {} {}".format(os.path.join(args.input,d,"background_2018_hist.root"), os.path.join(args.input,d,"*jetsto*.root"))
      uuid_ =  str(uuid.uuid4())
      command = "mkdir /tmp/%s;" % (uuid_)
      command += "cd /tmp/%s;" %(uuid_)
      command += "%s;"%(haddcmd)
      command += "\n"
      jobf.write(command)
  jobf.close()
