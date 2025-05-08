import os
import SoftDisplacedVertices.Plotter.plotter as p
import SoftDisplacedVertices.Plotter.plot_setting as ps
import SoftDisplacedVertices.Samples.Samples as s

if __name__=="__main__":

  #if 'submit' in sys.argv:


  lumi = 59683. # units in pb-1
  label = "MLNanoAODv2"
  outputDir = '/eos/vbc/group/cms/ang.li/MLhists/{}'.format(label)
  
  input_json = "MLNanoAOD.json"
  #ss = s.stop_2018
  ss = s.wlnu_2018 + s.znunu_2018
  s.loadData(ss,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(input_json)),label)
  info_path = os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Plotter/metadata_CustomMiniAOD_v3.yaml')

  plotter = p.Plotter(datalabel=label,outputDir=outputDir,lumi=lumi,info_path=info_path,config="/users/ang.li/public/SoftDV/CMSSW_13_3_0/src/SoftDisplacedVertices/Plotter/plotconfig_bkg.yaml")

  for sample in ss:
    plotter.setSample(sample)
    plotter.makeHistFiles()
