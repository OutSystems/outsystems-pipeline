# Sample script to validate TechDebt level and number of security findings
# Python modules
import argparse
import json
import os


# Custom exceptions
class TechDebtAnalysisException(Exception):
    pass


# Local vars
cat_security_guid = "6c87e98f-2ece-4df2-b791-d0c7eae15914"
cat_architecture_guid = "f7fdbb75-f2f3-4199-9761-ae0fd08f0998"
cat_performance_guid = "da5489cc-0102-4de7-8788-a5de6c4b297c"

# Argument menu / parsing
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--manifest_file", type=str, required=True,
                    help="Manifest file (with JSON format).")
parser.add_argument("-d", "--techdebt_data", type=str, required=True,
                    help="Technical debt data folder.")
parser.add_argument("-l", "--max_techdebt_level", type=str, default="Medium",
                    help="Technical debt level threshold (per application).")
parser.add_argument("-s", "--max_security_findings", type=int, default=0,
                    help="Number of security findings threshold (per application).")
args = parser.parse_args()

techdebt_data_folder = args.techdebt_data
max_techdebt_lvl = args.max_techdebt_level
max_sec_findings_count = args.max_security_findings
trigger_manifest = json.load(open(args.manifest_file, "r"))
levels = json.load(open("{}/TechDebt.levels.cache".format(techdebt_data_folder), "r"))

print(
    '''Checking thresholds (per application) for technical debt data:
    >>> Tech Debt Level = {}
    >>> Security Findings (Count) = {}'''.format(max_techdebt_lvl, max_sec_findings_count), flush=True
)

# Get max tech debt level index
max_techdebt_lvl_info = next(filter(lambda x: x["Name"] == max_techdebt_lvl, levels["Levels"]), None)
if max_techdebt_lvl_info is None:
    raise TechDebtAnalysisException("Unknown tech debt level: {}".format(max_techdebt_lvl))
max_techdebt_idx = levels["Levels"].index(max_techdebt_lvl_info)

# Check if tech debt level of each app in the pipeline scope is below defined threshold
for manifest_app in trigger_manifest["ApplicationVersions"]:
    app_name = manifest_app["ApplicationName"].replace(' ', '_')

    findings_file = "{}/TechDebt.{}.application.cache".format(techdebt_data_folder, app_name)
    findings = {}

    if os.path.isfile(findings_file):
        findings = json.load(open(findings_file, "r"))
    else:
        print("Validation skipped for {}: No technical debt data found.".format(app_name), flush=True)
        break

    for app in findings["Applications"]:
        techdebt_lvl_info = next(filter(lambda x: x["GUID"] == app["LevelGUID"], levels["Levels"]), None)
        techdebt_lvl_idx = levels["Levels"].index(techdebt_lvl_info)
        if techdebt_lvl_idx > max_techdebt_idx:
            raise TechDebtAnalysisException("Technical debt level of application {} is above defined threshold ({}).".format(app["Name"], techdebt_lvl_info["Name"]))

        # Check if security findings count of each app in the pipeline scope is below defined threshold
        sec_findings_count = 0
        for module in app["Modules"]:
            sec_findings_only = filter(lambda x: x.get("CategoryGUID") == cat_security_guid, module.get("Findings", []))
            for finding in sec_findings_only:
                sec_findings_count += finding["Count"]
        if sec_findings_count > max_sec_findings_count:
            raise TechDebtAnalysisException("Security findings count of application {} is above defined threshold ({}).".format(app["Name"], sec_findings_count))

print("Technical debt findings are below predefined thresholds.", flush=True)
