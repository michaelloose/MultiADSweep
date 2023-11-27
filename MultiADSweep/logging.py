"""
logging.py


Author: Michael Loose
Date: 18. Sep. 2023
Institution: Friedrich-Alexander-Universität Erlangen, Lehrstuhl für technische Elektronik
License: MIT

"""

import re
import json

class LogFileHandler(object):
    def __init__(self):
        self.data = {}

    def read_finished_workers(self, finishedWorkers):
        self.__process_worker_logs(finishedWorkers)

    def read_logfile(self, filePath):
        with open(filePath, "r") as file:
            json_data = json.load(file)

        workers = []
        for workerName, data in json_data.items():
            worker = {
                "returnCode": data["returnCode"],
                "workerName": workerName,
                "logStr": data["logContent"],
                "errStr": data["errlogContent"],
                "dirs": data["handlerData"]["dirs"],
                "vars":data["handlerData"]["vars"],
                "staticVars":data["handlerData"]["staticVars"],
            }
            workers.append(worker)
        self.__process_worker_logs(workers)

    def write_logfile(self, filePath):
        with open(filePath, 'w') as file:
            json.dump(self.data, file, indent=4) 

    def print_summary(self):
        cumulatedCpuTime = 0
        for sim in self.data:
            cumulatedCpuTime += float(self.data.get(sim).get("simulatorData").get("Total CPU time"))

        print(f"Cumulated CPU Time: {cumulatedCpuTime:.1f}s ({self.__format_time(cumulatedCpuTime)})")

        warnings, errors, readErrors = self.__summarize_logfiles(self.data)

        print(f"Read {readErrors['totalSims']-readErrors['readErrorCount']}/{readErrors['totalSims']} Files sucessfully ")
        if readErrors['readErrorCount']:
            print("Read Errors:")
            print('-' * 40)
            for readError in readErrors['errors']:
                print(readError)
            print()

        print("Simulation Errors:")
        print('-' * 40)
        if errors:
            for error, simulation_list in errors.items():
                if len(simulation_list) == len(self.data):
                    print(f"{error}")
                    print(f"{len(simulation_list)} occurrences (All Simulations)")
                else:
                    print(f"{error}")
                    print(f"{len(simulation_list)} {'occurrence' if  len(simulation_list) == 1 else 'occurrences'}:")
                    for simulation in simulation_list:
                        print(f"    {simulation}")
                print("\n")

        else:
            print("No errors occurred.")
            print("\n")

        print("Simulation Warnings:")
        print('-' * 40)
        if warnings:
            for warning, simulation_list in warnings.items():
                if len(simulation_list) == len(self.data):
                    print(f"{warning}")
                    print(f"{len(simulation_list)} occurrences (All Simulations)")
                else:
                    print(f"{warning}")
                    print(f"{len(simulation_list)} {'occurrence' if  len(simulation_list) == 1 else 'occurrences'}:")
                    for simulation in simulation_list:
                        print(f"    {simulation}")
                print("\n")
        else:
            print("No warnings occurred.")

    def __process_worker_logs(self, finishedWorkers):
        self.data = {}


        for fw in finishedWorkers:
            workerName = fw["workerName"]
            logContent = fw["logStr"]
            errlogContent = fw["errStr"]

            readError = fw.get("readError")
            simulatorErrors = self.__extract_warnings_errors(logContent, r"(Error detected .+?)\n(.+?\n\n)")
            simulatorWarnings = self.__extract_warnings_errors(logContent, r"(Warning detected .+?)\n(.+?\n\n)")

            # Parsen des Log-Inhalts
            simulatorData = {
                "Simulation Start Time": self.__extract_value(logContent, "Simulation started at (.+?)\n"),
                "Simulation End Time": self.__extract_value(logContent, "Simulation finished at (.+?)\n"),
                "Host": self.__extract_value(logContent, 'Running on host: "(.+?)"'),
                "Directory": self.__extract_value(logContent, 'In Directory: "(.+?)"'),
                "User": self.__extract_value(logContent, 'User: "(.+?)"'),
                "Process ID": self.__extract_value(logContent, 'Process ID: (.+?)\n'),
                "Total CPU time": self.__extract_value(logContent, 'Total CPU time +?= +?(.+?) seconds.'),
                "Total stopwatch time": self.__extract_value(logContent, 'Total stopwatch time +?= +?(.+?) seconds.'),
            }

            self.data[workerName] = {
                "returnCode": fw["returnCode"],
                "readError":readError,
                "logContent": logContent,
                "errlogContent": errlogContent,
                "handlerData":{
                    "dirs":  {key: str(value) for key, value in fw["dirs"].items()},
                    "vars":fw["vars"],
                    "staticVars":fw["staticVars"],
                },
                "simulatorData": simulatorData,
                "simulatorErrors": simulatorErrors,
                "simulatorWarnings": simulatorWarnings
            }
    
    @staticmethod
    def __extract_value(content, pattern):
        import re
        match = re.search(pattern, content)
        # Return the matched value if found, otherwise return None
        return match.group(1).strip() if match else None

    @staticmethod
    def __extract_warnings_errors(content, pattern):
        matches = re.findall(pattern, content, re.DOTALL)
        
        # Dictionary to store grouped warnings
        groupedWarnings = {}
        
        for match in matches:
            # Extract the header and content of the warning
            header, warningContent = match
            
            # Add the warning to the corresponding key in the dictionary
            if header not in groupedWarnings:
                groupedWarnings[header] = []
            groupedWarnings[header].append(warningContent.strip().lstrip(header).strip())
        
        for warning in groupedWarnings:
            groupedWarnings[warning] = LogFileHandler.__summarize_list_duplicates(groupedWarnings[warning])
        
        return groupedWarnings

    @staticmethod
    def __summarize_logfiles(jsonData):
        warningsSummary = {}
        errorsSummary = {}
        readErrorsSummary = {"totalSims":0,
                             "readErrorCount":0,
                             "errors":[]}

        for key, value in jsonData.items():
            simWarnings = value.get("simulatorWarnings", [])
            simErrors = value.get("simulatorErrors", [])
            readError = value.get("readError")

            readErrorsSummary["totalSims"] = readErrorsSummary["totalSims"]+1
            if readError:
                readErrorsSummary["readErrorCount"] = readErrorsSummary["readErrorCount"]+1
            
                if readError[0] not in readErrorsSummary["errors"] :
                    readErrorsSummary["errors"].append(readError[0])
        

            # Group warnings by their content
            for warning in simWarnings:
                if warning not in warningsSummary:
                    warningsSummary[warning] = []
                warningsSummary[warning].append(key)

            # Group errors by their content
            for error in simErrors:
                if error not in errorsSummary:
                    errorsSummary[error] = []
                errorsSummary[error].append(key)

        return warningsSummary, errorsSummary, readErrorsSummary
        
    @staticmethod
    def __summarize_list_duplicates(inputList):
        countDict = {}
        for item in inputList:
            countDict[item] = countDict.get(item, 0) + 1   
        return [f"{key}\n({value} Occurences)" if value > 1 else key for key, value in sorted(countDict.items(), key=lambda x: x[1], reverse=True)]
     
    @staticmethod
    def __format_time(seconds):
        days = seconds // 86400
        remainingSeconds = seconds % 86400
        hours = remainingSeconds // 3600
        remainingSeconds %= 3600
        minutes = remainingSeconds // 60
        secondsRest = remainingSeconds % 60

        formattedString = ""
        
        if days > 0:
            formattedString += f"{days:.0f}d, "
        if hours > 0:
            formattedString += f"{hours:.0f}h, "
        if minutes > 0:
            formattedString += f"{minutes:.0f}min, "
        if secondsRest > 0:
            formattedString += f"{secondsRest:.1f}s"
        return formattedString.rstrip(", ")