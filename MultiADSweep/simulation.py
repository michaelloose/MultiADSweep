"""
simulation.py

This Module contains handler functions for running paralellized ADS Simuiations using the ADS CLI Interface

Author: Michael Loose
Date: 18. Sep. 2023
Institution: Friedrich-Alexander-Universität Erlangen, Lehrstuhl für technische Elektronik
License: MIT

"""


import os
import multiprocessing
import subprocess
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from itertools import product
from typing import Union, List
from _collections_abc import Iterable

import keysight.pwdatatools as pwdt
from .utilities import fast_copy_dir, modify_netlist, get_cell_name_from_netlist, robust_byte_decode
from .logging import LogFileHandler



class SimulationManager(object):
    """
    Manages the execution and coordination of a simulation pool.

    This class is responsible for initializing the simulation environment, managing simulation parameters,
    conducting simulations, and collecting results.

    Parameters:
    ---


    - workspace_dir (Path): Path to the simulation workspace directory.
    - sim_name (str): Name of the simulation.
    - vars: Simulation variables, either as a Pandas MultiIndex or as an Iterable.
    - var_names: Names of the simulation variables if 'vars' is passed as an Iterable.
    - netlist_filename (str): Name of the netlist file. Default is "netlist.log"
    - ads_install_dir (Path): Installation path of ADS.
    - ads_startup_cmd (list/str): Optional command(s) to configure the environment for ADS (e.g., module load commands). Only necessary if specific environment setup is required to make the 'adssim' command available.
    - max_workers (int): Maximum number of parallel workers. Make sure to have a suficcient ads licence count available
    - keep_temp_files (bool): Whether to keep temporary files after simulation.
    - write_logs (bool): Whether to write log files.

    Methods:
    ---
    - run: Starts the simulations and collects the results. Will override previous simulation data
    - set_static_vars:  Sets static variables for the simulation, useful for iterative simulations where subsequent runs depend on previous results.
    - write_output_files: Writes the simulation results to a file.
    - get_results: Returns the collected simulation results as a pwdt group.

    Default Paths:
    ---
    The default paths for storing temporary files, results, and logs are constructed based on the 'workspace_dir':
    - A directory with the suffix '_mas' is created in the same location as the workspace directory.
    - Within this '_mas' directory, subdirectories for temporary files, results, and logs are created.
    """    
    
    def __init__(self, workspace_dir: Path, sim_name: str, vars, var_names=None, netlist_filename: str = "netlist.log", ads_install_dir: Path = Path("/opt/keysight/ADS2023_Update2"), ads_startup_cmd: Union[None, str, List[str]] = None, max_workers : int = 10, keep_temp_files:bool = False, write_logs: bool = True):    
    
    
    
    #Checking and typecasting of passed vars/names
        if isinstance(vars, pd.MultiIndex):
            if None in vars.names:
                raise ValueError("Names are missing for some elements in the MultiIndex.")
            self.newSweepingVars = vars
        elif isinstance(vars, Iterable):
            if all(isinstance(item, (Iterable, int, float)) for item in vars):
                if isinstance(vars[0], Iterable):
                    if var_names is None:
                        raise ValueError("The 'names' argument must be provided when passing a list of tuples.")
                    self.newSweepingVars = pd.MultiIndex.from_tuples(vars, names=var_names)
                elif isinstance(vars[0], (int, float)):
                    if not isinstance(var_names, str):
                        raise ValueError("The 'names' argument must be a string when passing a list of numbers.")
                    self.newSweepingVars = pd.MultiIndex.from_tuples([(item,) for item in vars], names=[var_names])
                else:
                    raise ValueError("Unsupported data type for elements within 'vars'.")
            else:
                raise ValueError("Unsupported data type for 'vars'. Please pass a MultiIndex, an iterable of tuples, or an iterable of numbers.")
        else:
            raise ValueError("Unsupported data type for 'vars'.")
        
        #reversing order of sweeping indices to have a consistent behavior to ads which appends to the front
        self.newSweepingVars = self.newSweepingVars.reorder_levels(reversed(range(len(self.newSweepingVars.names))))
        self.simName = sim_name
        self.writeLogs = write_logs
        self.logFileHandler = LogFileHandler()
        workspace_dir = Path(workspace_dir)
        
        # Check if Netlist exists

        if not os.path.isfile(workspace_dir / netlist_filename):
            raise FileNotFoundError(f"Netlist not found at specified Path \"{workspace_dir / netlist_filename}\"")
        # Entferne die letzten 4 Zeichen ("_wrk")
        if workspace_dir.name.endswith("_wrk"):
            workspaceName = workspace_dir.name[:-4]
        else: 
            workspaceName = workspace_dir
        #
        if ads_startup_cmd is None:
            self.ads_startup_cmd = []
        elif isinstance(ads_startup_cmd, str):
            self.ads_startup_cmd  = [ads_startup_cmd]
        elif not (isinstance(self.ads_startup_cmd , list) and all(isinstance(item, str) for item in self.ads_startup_cmd )):
            raise ValueError('Invalid argument for ads_startup_cmd. Please supply a string, list of strings or None')

        
        self.dirs = {
        "ADS_installDir":Path(ads_install_dir),
        "ADS_workspaceDir": workspace_dir,
        "ADS_workspaceName": workspaceName,
        "ADS_cellName": get_cell_name_from_netlist(workspace_dir / netlist_filename),
        "netlistFileName": netlist_filename,
        "MAS_workspaceDir": workspace_dir.parent / (workspaceName +"_mas"),
        "simName": sim_name,
        "MAS_outFileDir": workspace_dir.parent / (workspaceName +"_mas") /"data",
        "MAS_logFileDir": workspace_dir.parent / (workspaceName +"_mas") /"log"
        }

        print(f"Sucessfully found Netlist for Cell \"{self.dirs['ADS_cellName']}\" at \"{self.dirs['ADS_workspaceDir']}\"")

        for dir_name, dir_path in self.dirs.items():
            if dir_name.startswith("MAS"):
                os.makedirs(dir_path, exist_ok=True)

        self.maxPoolSize = max_workers
        self.keepTempFiles = keep_temp_files

        self.simResults = None
        self.staticVars = {}


    def run(self):
        
        finishedWorkers = []
        concatBlocks = []
        concatBlocksMetadata = []
    
        pool = multiprocessing.Pool(self.maxPoolSize)
        print(f"Starting process pool. {len(self.newSweepingVars)} Simulations, Maximum {self.maxPoolSize} Workers")
        if self.staticVars:  
            print("Static Simulation Variables")
            for key, value in self.staticVars.items():
                print(f"{key}={value}")

        isFirstValidWorker = True
        for retvals in tqdm(pool.imap(self._sim_worker_fcn, self.newSweepingVars), total=len(self.newSweepingVars)):

            finishedWorkers.append(retvals["fw"])
        
            if retvals["data"] is not None:
            #Has the Worker produced a readable Output File?
                if isFirstValidWorker:
                    # Building the file structure based on the first blocks. All subsequent workers data is apended to each block
                    concatBlocksMetadata = retvals["metadata"]
                    for block in retvals["data"]:
                        concatBlocks.append(block)
                    isFirstValidWorker = False
    

                else:
                    for b, block in enumerate(retvals["data"]):
                        # Only append sim data to blocks that contain dependent variables.
                        if type(block) == pd.DataFrame:
                            #Type clash handling here (Worker data is another datatype than initial data)

                            concatBlocks[b] = pd.concat([concatBlocks[b], block])
        self.logFileHandler.read_finished_workers(finishedWorkers)
        self.logFileHandler.print_summary()
        if self.writeLogs :
            logPath = self.dirs["MAS_logFileDir"]/(self.dirs["simName"]+".log.json")
            self.logFileHandler.write_logfile(logPath)
            print(f"Logs written to {logPath}")

        print("Processing Simulation Data")
        #Convert Dataframes back into Blocks
        for nBlock, block in enumerate(concatBlocks):
            # only convert touched Blocks
            if type(block) == pd.DataFrame:
                ivarnames = block.index.names
                #Reindexing to make output Data regular in case some simulations contain less blocks than others. This happend e.g when HB doesnt converge above a certain compression
                #Sweeping values which have not been filled by hpeesofsim are being filled with NaN to achieve this
                orig_ivarnames =[name for name in ivarnames if name not in self.newSweepingVars.names]
                unique_values = [block.index.get_level_values(name).unique() for name in orig_ivarnames]
                reindexedOrigIvars = pd.MultiIndex.from_product(unique_values, names=orig_ivarnames)

                newIndex = pd.MultiIndex.from_tuples([tuple(a + b) for a, b in product(self.newSweepingVars, reindexedOrigIvars)], names=self.newSweepingVars.names + reindexedOrigIvars.names)
                block = block.reindex(newIndex)

                        
                blk = pwdt.Block(block.reset_index())
                blk.name = concatBlocksMetadata[nBlock]["name"]
                concatBlocksMetadata[nBlock]["metadata"]["__ivarnames__"] = ivarnames
                blk.metadata = concatBlocksMetadata[nBlock]["metadata"]
                blk.ivarnames = ivarnames
                #ltst = list(lt.members[nBlock].ivarnames)+list(fw["vars"].keys())
                concatBlocks[nBlock] = blk

        #Add Blocks to Group
        self.simResults = pwdt.Group(concatBlocks)
        self.simResults.name = self.dirs["simName"]
        #self.simResults.metadata =

        print("Done")

    def set_static_vars(self, static_vars):
        """
        Sets static variables for a simulation run. These variables are used to modify the netlist but are not part of the parameter sweep.

        Parameters:
        - staticVars (dict): A dictionary of variables that remain constant for a single simulation run. These variables are useful for iterative simulations where each iteration depends on the results of the previous one. Setting 'keep_temp_files' to True is recommended when using staticVars, as it avoids the need to re-copy directories between iterations.

        This method allows for more efficient simulations, especially when dealing with iterative processes or when certain parameters need to remain fixed across multiple simulation runs.
        """
        self.staticVars = static_vars

    def write_output_files(self, path = None, dst_type = 'pwdt'):
        """
        Writes the simulation results to a file.

        Parameters:
        ---
        - path (Path, optional): The path where the output file will be saved. If not provided, a default path is used.
        - dst_type (str): The format of the output file. Default is 'pwdt'. Allowed Datatypes are 'pwdt, ads, ads_text, citi, mdif, smatrixio and touchstone'

        Raises:
        ---
        - ValueError: If an unsupported file format is specified.
        - AttributeError: If there are no simulation results to write.
        """
        #Raise an Error if a wrong output type is requested
        if dst_type not in pwdt.options.files.writeable_types:
            allowed_types = ", ".join(pwdt.options.files.writeable_types[:-1]) + " and " + pwdt.options.files.writeable_types[-1]
            raise ValueError(f"Invalid value for 'dst_type'. Allowed values are: {allowed_types}.")
        
        if self.simResults is None:
            raise AttributeError("No Simulation Data available yet")
        

        if not path:
            try:
                fileExt = pwdt.options.files.writeable_type_to_ext_map[dst_type][0]
            except:
                fileExt = ""
            staticVarApdx = ""
            for var_name, var_value in self.staticVars.items():
                staticVarApdx += f"_{var_name}_{var_value}".replace('.', 'p')

            path = self.dirs["MAS_outFileDir"]/(self.dirs["simName"]+staticVarApdx+fileExt)

        pwdt.write_file(self.simResults, path, dst_mode="w", dst_type = dst_type)
        print(f"Output written to {path}")

    def get_results(self):
        """
        Retrieves the simulation results.

        Returns:
        - pwdt.Group
        """
        return self.simResults
    

    
    def _sim_worker_fcn(self, vars):
        vars = {name: value for name, value in zip(self.newSweepingVars.names, vars)}
        handler = SimulationHandler(vars=vars, dirs = self.dirs, static_vars = self.staticVars, ads_startup_cmd = self.ads_startup_cmd, keep_temp_files=self.keepTempFiles, use_existing_temp_files=bool(self.set_static_vars))
        fw = handler.run()

        # Has an Output File been produced?
        if not os.path.isfile(fw["origDataFilePath"]):
            e = FileNotFoundError(f"Output File not found in expected location {fw['origDataFilePath']}")
            error_type = e.__class__.__name__
            fw["readError"] = [e, "No output file generated: Please check workspace settings, available license count and simulator convergence", error_type, str(e)]
            return {"fw":fw, "data": None, "metadata":None}


        # Handling of unreadable Datasets
        try:
            simData = pwdt.read_file(fw["origDataFilePath"])
        #This happens presumably only when not enough licenses are available 
        except ChildProcessError as e:
            error_type = e.__class__.__name__
            fw["readError"] = ["Output File unreadable: Please check available license count and simulator convergence", error_type, str(e)]
            #f"Error reading simulation data - {error_type}: {e}\n"
            return {"fw":fw, "data": None, "metadata":None}

        except StopIteration as e:
            error_type = e.__class__.__name__
            fw["readError"] = ["Output File unreadable: Please check available license count and simulator convergence", error_type, str(e)]
            return {"fw":fw, "data": None, "metadata":None}

        processedBlocks = []
        metadata = []
        for block in simData.members:
            metadata.append({"name":block.name,
                             "metadata": block.metadata})
            #If a block has no independent variables then it can be left as is
            if(len(block.ivarnames)):
                # Combining existing independent variables in Block with new independent variables which have been swept in this program 
                # Appending new variables to the front, as ADS would handle this on a param sweep
                ivarnames = list(vars.keys()) + list(block.ivarnames)
                #combined_multiindex = pd.MultiIndex.from_tuples(combined_tuples, names=ivarnames)
                for newIndep in vars:
                    block.data[newIndep] = vars[newIndep]
                #print(block.data.set_index(ivarnames))
                processedBlocks.append(block.data.set_index(ivarnames))
            
            else:
                #Blocks without indep are passed as they are
                processedBlocks.append(block)

        return {"fw":fw, "data": processedBlocks, "metadata":metadata}

    
class SimulationHandler(object):
    """
    Manages the execution of a single ADS simulation

    This class is responsible for initializing simulation parameters, executing the simulation,
    and returning the simulation results.

    Parameters:
    - vars (dict): Dictionary of simulation variables.
    - dirs (dict): Dictionary of directory paths.
    - static_vars (dict): Static variables for the simulation.
    - ads_startup_cmd (list): Optional command(s) to configure the environment for ADS. Only necessary if specific environment setup is required to make the 'adssim' command available.
    - keep_temp_files (bool): Whether to keep temporary files after simulation.
    - use_existing_temp_files (bool): Whether to reuse existing temporary files.

    Methods:
    - run: Executes the simulation and returns the results.
    """
    def __init__(self, vars:dict, dirs:dict, static_vars:dict = {}, ads_startup_cmd:list = [], keep_temp_files:bool = False, use_existing_temp_files:bool = False) -> None:
        self.vars = vars
        self.staticVars = static_vars
        self.keepTempFiles = keep_temp_files
        self.ads_startup_cmd = ads_startup_cmd
        self.dirs = dirs
        self.update_environment(dirs["ADS_installDir"])

        # Neuer Verzeichnisname basierend auf den Variablen
        self.workerName = self.dirs["ADS_workspaceName"]
        for var_name, var_value in self.vars.items():
            self.workerName += f"_{var_name}_{var_value}".replace('.', 'p')

        # Hinzufügen der _wrk-Endung
        sim_dir_name = self.workerName + f"_wrk" 

        # Zielpfad für das kopierte und umbenannte Verzeichnis
        self.tempWorkspaceDir = self.dirs["MAS_workspaceDir"] / "temp"/ sim_dir_name

        if not (use_existing_temp_files and os.path.isdir(self.tempWorkspaceDir)):
            fast_copy_dir(src=self.dirs["ADS_workspaceDir"], dst=self.tempWorkspaceDir)

        modify_netlist(self.tempWorkspaceDir/self.dirs["netlistFileName"], {**vars, **static_vars})

    def __del__(self):
        # temporären Workspace löschen
        if not self.keepTempFiles:
            subprocess.run(["rm", "-rf", self.tempWorkspaceDir])

    def update_environment(self, ADSInstallationDir:str):
        os.environ['HPEESOF_DIR']=str(ADSInstallationDir)
        path = os.environ["PATH"]
        path_strings = path.split(";")
        path_strings.append(os.path.join(ADSInstallationDir,'bin'))
        path_strings = sorted(list(set(path_strings))) # only unique paths
        os.environ["PATH"] = ";".join(path_strings)+";."

    def run(self, outFileDir:Path = None):
        os.chdir(self.tempWorkspaceDir)
        commands = self.ads_startup_cmd+[f"adssim {self.dirs['netlistFileName']}"]
        #commands = [
        #"module load ads/2023.02",
        #f"adssim {self.dirs['netlistFileName']}"
        #] 

        combined_cmd = " && ".join(commands)

        process = subprocess.Popen(combined_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_bytes, stderr_bytes = process.communicate()
        stdout_str = robust_byte_decode(stdout_bytes)
        stderr_str = robust_byte_decode(stderr_bytes)
        outFilePath = None
        dsPath = self.tempWorkspaceDir/(self.dirs["ADS_cellName"]+".ds")

        #Convert the Output file converted to pwdt. Only makes sense for testing. This slows down simulation heavily
        if outFileDir:
            # Überprüfen ob die Ausgabedatei erzeugt wurde
            if not os.path.isfile(dsPath):
                raise(FileNotFoundError(f"Output File not found in expected location {dsPath}"))
            
            #Zieldatei festlegen und Ausgabeordner erstellen
            outFilePath = self.outFileDir / (self.workerName + ".pwdt")
            os.makedirs(self.outFileDir, exist_ok=True)

            # Erzeugten Datensatz in hdf5 konvertieren
            pwdt.translate_file(dsPath, outFilePath, dst_type='pwdt', dst_mode='w')


        return {"returnCode":process.returncode,"workerName": self.workerName,  "dirs": self.dirs,  "vars":self.vars, "staticVars":self.staticVars, "logStr": stdout_str, "errStr": stderr_str, "origDataFilePath": dsPath, "convDataFilePath":outFilePath}