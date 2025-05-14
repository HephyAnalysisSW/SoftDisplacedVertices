"""
Custom built DAS API for SDV.

Usage Examples
--------------
Simple query (e.g., run,lumi for a given dataset and instance):

    import das_api
    das_api.DASAPI.query_type = "run,lumi"
    das_api.DASAPI.dataset = "/JetMET1/aguven-Run2023D1_part1_nano_v1-00000000000000000000000000000000/USER"
    das_api.DASAPI.instance = "prod/phys03"
    result = das_api.DASAPI.query
    print(result.stdout)

Complex query using an operator (for example, run between two numbers):
    import das_api
    das_api.DASAPI.query_type = "run"
    # Here, by passing a tuple, the API formats it as: "run between [160910,160920]"
    das_api.DASAPI.run = ("between", "[160910,160920]")
    result = das_api.DASAPI.query
    print(result.stdout)

Using a pipe:
    import das_api
    das_api.DASAPI.query_type = "run"
    das_api.DASAPI.dataset = "/Some/Dataset/Path"
    das_api.DASAPI.pipe_cmd = "sum(run.delivered_lumi), sum(run.nevents)"
    result = das_api.DASAPI.query
    print(result.stdout)

Providing the entire query “raw” (useful when your query doesn’t follow simple key=value rules):
    import das_api
    das_api.DASAPI.raw_query = "dataset=/Cosmics/Run2010B-TkAlCosmics0T-v1/ALCARECO site=T1_US_FNAL_Buffer"
    result = das_api.DASAPI.query
    print(result.stdout)

Resetting the API between queries:
    das_api.DASAPI.reset()
"""

import subprocess
import time
import ast

class DASAPIClass:
    def __init__(self):
        # Reserved attributes:
        object.__setattr__(self, "query_type", "")  # e.g., "run,lumi", "block", "file", etc.
        object.__setattr__(self, "pipe_cmd", "")      # e.g., "grep file.nevents" or aggregation commands
        object.__setattr__(self, "raw_query", None)     # if set, used instead of building the query from parts
        object.__setattr__(self, "params", {})        # holds all parameters (e.g., dataset, instance, run, etc.)

    def __setattr__(self, name, value):
        # Reserved names (internal attributes)
        if name in ("query_type", "pipe_cmd", "raw_query", "params"):
            object.__setattr__(self, name, value)
        else:
            self.params[name] = value

    def __getattr__(self, name):
        # Return the parameter if it exists
        if name in self.params:
            return self.params[name]
        raise AttributeError(f"'DASAPI' object has no attribute '{name}'")

    @property
    def query(self):
        """
        Constructs the complete DAS query string and runs dasgoclient.
        
        The query is built as follows:
          - If `raw_query` is set, it is used directly.
          - Otherwise, the query string is:
            
                <query_type> <key>=<value> <key2>=<value2> ... [| <pipe_cmd>]
            
            For any parameter whose value is a tuple, it is formatted as:
            
                key operator operand
                
            (For example, if you do: DASAPI.run = ("between", "[160910,160920]"),
             the result will include "run between [160910,160920]".)
        """
        if self.raw_query:
            full_query = self.raw_query
        else:
            parts = []
            if self.query_type:
                parts.append(self.query_type)
            # Add each parameter from the internal params dictionary.
            # Note: The order is arbitrary. If order matters, consider using an OrderedDict.
            for key, value in self.params.items():
                if isinstance(value, tuple):
                    # Format as: key <operator> <operand>
                    parts.append(f"{key} {value[0]} {value[1]}")
                else:
                    parts.append(f"{key}={value}")
            full_query = " ".join(parts)
            if self.pipe_cmd:
                full_query += " | " + self.pipe_cmd

        # Build the complete dasgoclient command.
        arg = f"-query={full_query.strip()}"
        command = ["dasgoclient", arg]
        max_retries = 3
        timeout_seconds = 10

        for attempt in range(1, max_retries + 1):
            # Execute the command while capturing output as text.
            try:
                result = subprocess.run(command,
                                        capture_output=True,
                                        text=True,
                                        timeout=10  # seconds
                                        )
                print("Success!")
                break
            except subprocess.TimeoutExpired:
                print(f"Attempt {attempt} timed out.")
                if attempt < max_retries:
                    time.sleep(3)  # optional: wait a bit before retrying
                else:
                    print("All retries failed.")
                    exit()
        return result

    def reset(self):
        """
        Resets the stored query_type, pipe command, raw_query and parameters.
        Useful for starting a fresh query.
        """
        self.query_type = ""
        self.pipe_cmd = ""
        self.raw_query = None
        self.params.clear()

def group_consecutive(nums):
    # Sort the list in ascending order.
    nums = sorted(nums)
    groups = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            # Continue the consecutive group.
            prev = n
        else:
            # End of a group.
            groups.append([start, prev])
            start = prev = n
    groups.append([start, prev])
    return groups

def format_runlumiquery(runlumiquery_output, format="compactList"):
    """
    Parameters
    ----------
    format: Available options: compactList, runsAndLumis [1].

    Refs
    ----
    [1]: Ref: https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideGoodLumiSectionsJSONFile
    """
    
    lines = runlumiquery_output.split('\n')
    lumiDict = dict()
    for line in lines[:-1]:
        key,value = line.split()
        listOfLumis = ast.literal_eval(value)
        if format=="compactList":
            lumiDict[key] = group_consecutive(listOfLumis)
        elif format=="runsAndLumis":
            lumiDict[key] = listOfLumis
        else:
            raise ValueError("Choose correct format!")
    return lumiDict



# Create a default instance so users can simply do:
#    import das_api
#    das_api.DASAPI.dataset = "..."
#    result = das_api.DASAPI.query
DASAPI = DASAPIClass()

if __name__ == "__main__":
    # A simple test/demo (this will run if you execute this script directly)
    DASAPI.reset()
    DASAPI.query_type = "run,lumi"
    DASAPI.dataset = "/JetMET1/aguven-Run2023D1_part1_nano_v1-00000000000000000000000000000000/USER"
    DASAPI.instance = "prod/phys03"
    result = DASAPI.query
    print("Command executed:")
    print(" ".join(["dasgoclient", f"-query={DASAPI.query_type} dataset={DASAPI.dataset} instance={DASAPI.instance}"]))
    print("Output:")
    
    
    lumiDict = format_runlumiquery(result.stdout)
    print(lumiDict)