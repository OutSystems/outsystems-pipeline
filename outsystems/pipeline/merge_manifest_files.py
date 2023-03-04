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
def merge_json_files(manifests_folder: str):

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

    result = {
        "ApplicationVersions": [],
        "ConfigurationItems": [],
        "EnvironmentDefinitions": [],
        "PipelineParameters": [],
        "DeploymentNotes": "",
        "TriggeredBy": {}
    }

    json_pattern = os.path.join(manifests_folder, '*.json')
    json_files = glob2.glob(json_pattern)

    merger = jsonmerge.Merger(schema)

    if json_files:
        print("The following manifests will be merged:", flush=True)
    else:
        raise NotImplementedError("Please make sure the manifests files exist in '{}' dir".format(manifests_folder))

    for json_file in json_files:
        print(" -> {}".format(json_file), flush=True)
        with open(json_file) as file_item:
            read_data = json.load(file_item)
            result = merger.merge(result, read_data)

    return result


def main(manifests_folder: str):

    merged_data = merge_json_files(manifests_folder)

    with open('merged_manifests.json', 'w') as merge_file:
        json.dump(merged_data, merge_file, indent=4)

# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--manifests_folder", type=str, required=True,
                        help="manifests folder dir")

    args = parser.parse_args()

    # Parse the artifact directory
    manifests_folder = args.manifests_folder

    # Calls the main script
    main(manifests_folder)
