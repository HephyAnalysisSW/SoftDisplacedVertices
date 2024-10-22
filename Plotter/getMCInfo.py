# Usage:
# python3 getMCInfo.py --sample_version CustomMiniAOD_v3 --json CustomMiniAOD_v3.json --outDir ./


from DataFormats.FWLite import Lumis, Handle
import os
import fnmatch
import yaml,json
import SoftDisplacedVertices.Samples.Samples as s
import subprocess


def get_metadata(ss, sample_version, outDir="./", useDAS=True):
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

      if not useDAS:
        for root, dirnames, filenames in os.walk(sample_dir):
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

                yaml_dict[sp.name]['files'].append({'filename': filename,
                                                'sumWeights': sum(lumisumWeights),
                                                'sumPassWeights': sum(lumisumPassWeights)})
                
                if lumis._tfile:
                    lumis._tfile.Close()
      elif useDAS:
        files = sp.getFileList(sample_version, "")
        for i, file in enumerate(files):
            print(i, "files are read.") if i%10 == 0 else None
            lumis = Lumis(file)
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

            yaml_dict[sp.name]['files'].append({'filename': file,
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

    os.makedirs(outDir, exist_ok=True)
    with open(os.path.join(outDir, 'metadata_'+sample_version+'.yaml'), 'w') as outfile:
        yaml.safe_dump(yaml_dict, outfile, default_flow_style=False)
        
    with open(os.path.join(outDir, 'metadata_'+sample_version+'.json'), 'w') as outfile:
        json.dump(json_dict, outfile)

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
    # print(s.__dir__())
    input_samples = s.wlnu_2017_100
    # print(input_samples)
    s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.json)),args.sample_version)
    print(input_samples[0].__dict__)
    get_metadata(input_samples,args.sample_version, args.outDir)