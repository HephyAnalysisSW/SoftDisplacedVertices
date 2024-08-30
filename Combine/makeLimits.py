# Don't run by yourself if your goal is not debugging.
# For production use submit_limit_calculations.py instead.

# Example usage: 
# python3 makeLimits.py --datacard {datacard} --limitdir {limitdir}


import argparse
import uuid
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--datacard', type=str,
                        help='path to the datacard')
parser.add_argument('--limitdir', type=str,
                        help='output dir')
args = parser.parse_args()


if __name__=="__main__":
    datacard = args.datacard
    limitdir = args.limitdir

    head_tail = os.path.split(datacard)
    root, filename = head_tail[0], head_tail[1]
    sample_name = '_'.join(filename.split('_')[:-2])
    sample_limitdir = os.path.join(limitdir, sample_name)

    random_outdir_name = str(uuid.uuid4())
    random_outdir = os.path.join(limitdir, random_outdir_name)
    os.makedirs(random_outdir, exist_ok=True)
    combine_cmd = f"combine -d {datacard} -M AsymptoticLimits -v 1 --run blind --rMin 0 --rMax 5"
    subprocess.run(combine_cmd.split(' '), cwd=random_outdir)

    combine_output = os.path.join(random_outdir, 'higgsCombineTest.AsymptoticLimits.mH120.root')
    new_rootfile_name = filename[:-4] + '.root'
    new_combine_output = os.path.join(sample_limitdir, new_rootfile_name)
    os.makedirs(sample_limitdir, exist_ok=True)
    os.rename(combine_output, new_combine_output)
    os.remove(os.path.join(random_outdir, 'combine_logger.out'))
    os.rmdir(random_outdir)
