# Python Modules
import sys
import os
import argparse
import json
import jsonmerge
import glob2

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())


# ############################################################# SCRIPT ##############################################################
def merge_json_files(manifest_folder: str):

    # jsonmerge schema to define the merge strategy for each trigger manifest's dataset
    schema = {
        "properties": {
            "ApplicationVersions": {
                "mergeStrategy": "append"
            },
            "ConfigurationItems": {
                "mergeStrategy": "append"
            },
            "EnvironmentDefinitions": {
                "mergeStrategy": "overwrite"
            },
            "PipelineParameters": {
                "mergeStrategy": "append"
            },
            "DeploymentNotes": {
                "type": "string",
                "mergeStrategy": "discard"
            },
            "TriggeredBy": {
                "mergeStrategy": "discard"
            }
        }
    }

    # Vanilla trigger manifest dataset
    result = {
        "ApplicationVersions": [],
        "ConfigurationItems": [],
        "EnvironmentDefinitions": [],
        "PipelineParameters": [],
        "DeploymentNotes": "",
        "TriggeredBy": {}
    }

    # Get all json files from dir
    json_pattern = os.path.join(manifest_folder, '*.json')
    json_files = glob2.glob(json_pattern)

    if json_files:
        print("The following manifest files are going to be merged:", flush=True)
    else:
        raise NotImplementedError("Make sure that the manifest files exist in the '{}' directory".format(manifest_folder))

    merger = jsonmerge.Merger(schema)
    deployment_notes = ""

    # Merge json files using the specified schema
    for json_file in json_files:
        print(" -> {}".format(os.path.basename(json_file)), flush=True)
        with open(json_file) as file_item:
            read_data = json.load(file_item)
            result = merger.merge(result, read_data)
            # workaround for DeploymentNotes
            deployment_notes += os.path.basename(json_file) + ": " + read_data["DeploymentNotes"] + "\n"

    result["DeploymentNotes"] = deployment_notes
    return result


def main(manifest_folder: str):

    merged_data = merge_json_files(manifest_folder)

    merged_manifest_file = 'merged_manifest.json'
    with open(merged_manifest_file, 'w') as merge_file:
        json.dump(merged_data, merge_file, indent=4)

    print("File '{}' has been successfully generated.".format(merged_manifest_file), flush=True)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--manifest_folder", type=str, required=True,
                        help="Directory in which the manifest files are located")

    args = parser.parse_args()

    # Parse the artifact directory
    manifest_folder = args.manifest_folder

    # Calls the main script
    main(manifest_folder)
