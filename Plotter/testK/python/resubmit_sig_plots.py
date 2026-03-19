import os
import re
import json
from subprocess import run
import argparse

parser = argparse.ArgumentParser()

help_S = """All the jobs starting after this time/date will be searched. 
The argument will be passed to sacct.
Pass the date-time like this: 2024-11-14T00:00:00"""
parser.add_argument('-S', type=str, help=help_S)

args = parser.parse_args()


if __name__=="__main__":
    file_path = '/scratch-cbe/users/alikaan.gueven/AN_plots/tmp_checks/job_ids.json'
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
                    # If PENDING ==> notify
                    if (sacctOut_splitted[-1] == '0:0') and (sacctOut_splitted[-2] == 'PENDING'):
                        print(f'{sample} has not been submitted yet. Status: PENDING...')
                    elif (sacctOut_splitted[-1] == '0:0') and (sacctOut_splitted[-2] == 'RUNNING'):
                        print(f'{sample} has not been completed yet. Status: RUNNING...')
                    
                    # If FAILED ==> resubmit
                    elif (sacctOut_splitted[-1] != '0:0') and (sacctOut_splitted[-2] != 'COMPLETED'):
                        print(f'{sample} status: {sacctOut_splitted[-2]}!!!')
                        command = d[sample]['command']
                        result  = run(command, shell=True, capture_output = True, text = True)    # Resubmit.
                        print(result.stdout[:-1])

                        # Replace the jobid in the json file.
                        job_id = re.search("\d+", result.stdout).group()    # Get the new job_id
                        d[sample]['jobid'] = job_id                         # Replace the job_id in json.
                    
    # Write the modified json to the file.
    print("\nRewriting {os.path.join(outDir, 'job_ids.json')}...")
    with open(file_path, 'w') as f:
        json.dump(d, f)