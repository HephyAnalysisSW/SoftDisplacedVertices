#!/usr/bin/env python3

"""
Script to check job completion and create resubmission file for failed jobs
Usage: ./check_jobs.py /path/to/job
"""

import sys
import os
import re
from pathlib import Path


def extract_output_file(line):
    """Extract the output file path from the job command line."""
    # Pattern: cp <source> <destination>;
    # Find the last 'cp' command and extract the destination
    match = re.search(r'cp\s+\S+\s+([^;\s]+)', line)
    if match:
        return match.group(1)
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: ./check_jobs.py /path/to/job jobfile")
        sys.exit(1)
    
    job_dir = Path(sys.argv[1])
    jobs_file = job_dir / "input" / sys.argv[2]
    failed_jobs_file = job_dir / "input" / "failed_jobs.sh"
    
    # Check if the jobs.sh file exists
    if not jobs_file.exists():
        print(f"Error: jobs.sh file not found at {jobs_file}")
        sys.exit(1)
    
    print(f"Checking job completion for: {job_dir}")
    print(f"Reading jobs from: {jobs_file}")
    print()
    
    # Debug info
    file_size = jobs_file.stat().st_size
    print(f"Debug: File size: {file_size} bytes")
    print()
    
    failed_jobs = []
    total_jobs = 0
    failed_count = 0
    
    # Read and process the jobs file
    with open(jobs_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            # Strip whitespace and skip empty lines or comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            total_jobs += 1
            
            # Extract output file path
            output_file = extract_output_file(line)
            
            if not output_file:
                print(f"Warning: Could not extract output file from line {line_num}")
                print(f"  Line: {line[:100]}...")
                failed_jobs.append(line)
                failed_count += 1
                continue
            
            # Check if the output file exists
            if not Path(output_file).exists():
                print(f"FAILED [{failed_count + 1}]: Output file missing: {output_file}")
                failed_jobs.append(line)
                failed_count += 1
            else:
                print(f"OK [{total_jobs}]: {output_file}")
    
    print()
    print("=" * 42)
    print("Summary:")
    print(f"  Total jobs: {total_jobs}")
    print(f"  Successful: {total_jobs - failed_count}")
    print(f"  Failed: {failed_count}")
    print("=" * 42)
    
    # Write failed jobs to resubmission file
    if failed_count > 0:
        print()
        print(f"Writing failed jobs to: {failed_jobs_file}")
        
        with open(failed_jobs_file, 'w') as f:
            for job in failed_jobs:
                f.write(job + '\n')
        
        print(f"Done! You can resubmit failed jobs using: {failed_jobs_file}")
    else:
        print()
        if total_jobs == 0:
            print("Warning: No jobs were processed. Please check your jobs.sh file format.")
        else:
            print("All jobs completed successfully! No resubmission needed.")
            # Remove failed_jobs.sh if it exists
            if failed_jobs_file.exists():
                failed_jobs_file.unlink()
                print("Removed old failed_jobs.sh file.")


if __name__ == "__main__":
    main()
