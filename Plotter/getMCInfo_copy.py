from DataFormats.FWLite import Lumis, Handle
import os
import fnmatch
import yaml, json
import SoftDisplacedVertices.Samples.Samples as s


def get_metadata(ss, sample_version):
    """
    Gets sum of event weights for each ROOT file in each subdirectory.
    Writes YAML incrementally, JSON at the end.
    """
    yaml_path = os.path.join(args.outDir, f'metadata_{sample_version}_copy.yaml')
    json_path = os.path.join(args.outDir, f'metadata_{sample_version}_copy.json')

    json_dict = {'totalsumWeights': {}}

    # create/clear yaml file first
    with open(yaml_path, 'w') as outfile:
        outfile.write('')  # just truncate/create the file

    for sp in ss:
        sample_dir = sp.getFileDirs(sample_version)

        sample_yaml = {
            sp.name: {
                'totalsumWeights': None,
                'totalsumPassWeights': None,
                'files': []
            }
        }

        print('sp.name: ', sp.name)
        print('sample_dir: ', sample_dir)

        sumPassWeights = []
        sumWeights = []

        for root, dirnames, filenames in os.walk(sample_dir):
            for filename in fnmatch.filter(filenames, '*.root'):
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

                file_sumWeights = sum(lumisumWeights)
                file_sumPassWeights = sum(lumisumPassWeights)

                sumWeights.append(file_sumWeights)
                sumPassWeights.append(file_sumPassWeights)

                sample_yaml[sp.name]['files'].append({
                    'filename': filename,
                    'sumWeights': file_sumWeights,
                    'sumPassWeights': file_sumPassWeights
                })

                if lumis._tfile:
                    lumis._tfile.Close()

        if not sample_yaml[sp.name]['files']:
            continue

        totalsumWeights = sum(sumWeights)
        totalsumPassWeights = sum(sumPassWeights)

        sample_yaml[sp.name]['totalsumWeights'] = totalsumWeights
        sample_yaml[sp.name]['totalsumPassWeights'] = totalsumPassWeights
        json_dict['totalsumWeights'][sp.name] = totalsumWeights

        # append this sample block to yaml
        with open(yaml_path, 'a') as outfile:
            yaml.safe_dump(
                sample_yaml,
                outfile,
                default_flow_style=False,
                sort_keys=False
            )

    # write json only once at the end
    with open(json_path, 'w') as outfile:
        json.dump(json_dict, outfile, indent=2)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Get GenFilterInfo metadata.')
    parser.add_argument('--sample_version')
    parser.add_argument('--outDir')
    parser.add_argument('--json')
    args = parser.parse_args()
    if not os.path.exists(args.outDir):
      os.makedirs(args.outDir)
    
    input_samples = s.all_bkg_2024
    s.loadData(input_samples,
               os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.json)),
               args.sample_version)
    get_metadata(input_samples,args.sample_version)
