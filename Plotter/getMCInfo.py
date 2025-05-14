# Usage:
# python3 getMCInfo.py --sample_version CustomMiniAOD_v3 --json MC_Run3Summer23.json --outDir ./

# root [3] Events->Scan("GenEventInfoProduct_generator__SIM.obj->weight()")
# root [4] LuminosityBlocks->Scan("GenFilterInfo_genFilterEfficiencyProducer__SIM.obj->sumWeights()")

from DataFormats.FWLite import Lumis, Handle
import os
import fnmatch
import yaml,json
import SoftDisplacedVertices.Samples.Samples as s


def get_metadata(ss, sample_version):
    """
    Gets sum of event weights for each ROOT file in each subdirectory.
    Creates a metadata.yaml file.
    """
    yaml_dict = dict()
    json_dict = dict()
    json_dict['totalsumWeights'] = dict()
    
    for sp in ss:
      sample_dir = sp.getFileDirs(sample_version)

      yaml_dict[sp.name] = {'totalsumWeights': None,
                            'totalsumPassWeights': None,
                            'files': []}
      print('sp.name: ', sp.name)
      print('sample_dir: ', sample_dir)
      filename_list = []
      sumPassWeights = []
      sumWeights = []
      for root, dirnames, filenames in os.walk(sample_dir):
        

        for filename in fnmatch.filter(filenames, '*.root'):
            #print(filename)
            filename_list.append(filename)
            file_path = os.path.join(root, filename)
            lumis = Lumis(file_path)
            lumisumWeights = []
            lumisumPassWeights = []
            for lumi in lumis:
                handle = Handle("GenFilterInfo")
                lumi.getByLabel('genFilterEfficiencyProducer', handle)
                GenFilterInfo = handle.product()
                lumisumWeights.append(GenFilterInfo.sumWeights())
                lumisumPassWeights.append(GenFilterInfo.sumPassWeights())
            
            sumWeights.append(sum(lumisumWeights))
            sumPassWeights.append(sum(lumisumPassWeights))

            yaml_dict[sp.name]['files'].append({'filename': filename,
                                             'sumWeights': sum(lumisumWeights),
                                             'sumPassWeights': sum(lumisumPassWeights)})
            
            if lumis._tfile:
              lumis._tfile.Close()

        
      totalsumWeights = sum(sumWeights)
      totalsumPassWeights = sum(sumPassWeights)

      yaml_dict[sp.name]['totalsumWeights'] = totalsumWeights
      yaml_dict[sp.name]['totalsumPassWeights'] = totalsumPassWeights
      json_dict['totalsumWeights'][sp.name] = totalsumWeights

      if not yaml_dict[sp.name]['files']:
          yaml_dict.pop(sp.name)


    with open(args.outDir+'/metadata_'+sample_version+'.yaml', 'w') as outfile:
        yaml.safe_dump(yaml_dict, outfile, default_flow_style=False)
        
    with open(args.outDir+'/metadata_'+sample_version+'.json', 'w') as outfile:
        json.dump(json_dict, outfile, indent=2)

def get_metadata_dir(directory, outFileName):
    """
    Gets sum of event weights for each ROOT file in each subdirectory.
    Creates a metadata.yaml file.
    """
    yaml_dict = dict()
    json_dict = dict()
    json_dict['totalsumWeights'] = dict()
    
    for root, dirnames, filenames in os.walk(directory):
        filename_list = []
        sumPassWeights = []
        sumWeights = []
        yaml_dict[root] = {'totalsumWeights': None,
                           'totalsumPassWeights': None,
                           'files': []}

        
        for filename in fnmatch.filter(filenames, '*.root'):
            print(filename)
            filename_list.append(filename)
            file_path = os.path.join(root, filename)
            lumis = Lumis(file_path)
            lumisumWeights = []
            lumisumPassWeights = []
            for lumi in lumis:
                handle = Handle("GenFilterInfo")
                lumi.getByLabel('genFilterEfficiencyProducer', handle)
                GenFilterInfo = handle.product()
                lumisumWeights.append(GenFilterInfo.sumWeights())
                lumisumPassWeights.append(GenFilterInfo.sumPassWeights())
            
            sumWeights.append(sum(lumisumWeights))
            sumPassWeights.append(sum(lumisumPassWeights))

            yaml_dict[root]['files'].append({'filename': filename,
                                             'sumWeights': sum(lumisumWeights),
                                             'sumPassWeights': sum(lumisumPassWeights)})

        
        totalsumWeights = sum(sumWeights)
        totalsumPassWeights = sum(sumPassWeights)

        yaml_dict[root]['totalsumWeights'] = totalsumWeights
        yaml_dict[root]['totalsumPassWeights'] = totalsumPassWeights
        json_dict['totalsumWeights'][root] = totalsumWeights

        if not yaml_dict[root]['files']:
            yaml_dict.pop(root)


    with open(outFileName, 'w') as outfile:
        yaml.safe_dump(yaml_dict, outfile, default_flow_style=False)
        


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Get GenFilterInfo metadata.')
    parser.add_argument('--sample_version')
    parser.add_argument('--outDir')
    parser.add_argument('--json')
    args = parser.parse_args()
    if not os.path.exists(args.outDir):
      os.makedirs(args.outDir)
    # input_samples = s.all_bkg_bpix_2023
    input_samples = s.all_bkg_2023
    s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.json)),args.sample_version)
    get_metadata(input_samples,args.sample_version)
