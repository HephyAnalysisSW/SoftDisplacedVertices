import re
import json
import os
import argparse
from subprocess import run
import SoftDisplacedVertices.Samples.Samples as ss

parser = argparse.ArgumentParser()

help_S = """All the jobs starting after this time/date will be searched. 
The argument will be passed to sacct.
Pass the date-time like this: 2024-11-14T00:00:00"""
parser.add_argument('-S', type=str, help=help_S)

args = parser.parse_args()


if __name__=="__main__":
    outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
    work_subdir = "ParT_hists"
    unique_dir  = "vtx_2018"

    work_dir = os.path.join(outDir_base, work_subdir)
    outBaseDir = os.path.join(work_dir,str(unique_dir))
    
    file_paths = {'sig':  os.path.join(outBaseDir,   'sig/job_ids2018.json'),
                  'bkg':  os.path.join(outBaseDir,   'bkg/job_ids2018.json'),
                  # 'data': os.path.join(outBaseDir,  'data/job_ids2023.json'),
                }
    
    for key, file_path in file_paths.items():
        print('INFO:    Sample type:',  key)
        print('INFO:    Argument -S:',  args.S)

        with open(file_path) as f:
            d = json.load(f)

        if args.S:
            sacct_cmd = f'sacct -u $USER -S {args.S} --parsable2'
        else:
            sacct_cmd = f'sacct -u $USER --parsable2'
        # The output will look like:
        # 9095306|autoplotter|c|cms|6|COMPLETED|0:0

        sacctOut = run(sacct_cmd, shell=True, capture_output = True, text = True)
        sacctOut_splitted = sacctOut.stdout.split('|')

        for sample in d.keys():
            for sacctOut_line in sacctOut.stdout.splitlines():
                sacctOut_splitted = sacctOut_line.split('|')        # Get each column into a list.
                
                if sacctOut_splitted[0] == d[sample]['jobid']:
                    is_pending  = ((sacctOut_splitted[-1] == '0:0') and (sacctOut_splitted[-2] == 'PENDING'))
                    is_running  = ((sacctOut_splitted[-1] == '0:0') and (sacctOut_splitted[-2] == 'RUNNING'))
                    not_completed   = (sacctOut_splitted[-2] != 'COMPLETED')
                    # If PENDING ==> notify
                    if is_pending:
                        print(f'{sample} has not been submitted yet. Status: PENDING...')
                    elif is_running:
                        print(f'{sample} has not been completed yet. Status: RUNNING...')
                    
                    elif not_completed:
                        print(f'{sample} status: {sacctOut_splitted[-2]}!!!')
                        command = d[sample]['command']
                        result  = run(command, shell=True, capture_output = True, text = True)    # Resubmit.
                        print(result.stdout[:-1])

                        # Replace the jobid in the json file.
                        job_id = re.search("\d+", result.stdout).group()    # Get the new job_id
                        d[sample]['jobid'] = job_id                         # Replace the job_id in json.
                        
        # Write the modified json to the file.
        print(f"\nRewriting {file_path}...")
        print('-'*80)
        print()
        with open(file_path, 'w') as f:
            json.dump(d, f, indent=2)