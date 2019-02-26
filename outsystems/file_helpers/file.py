# Python Modules
import json
import os
import errno

# Custom Modules
from outsystems.vars.file_vars import ARTIFACT_FOLDER

def store_data(filename :str, data :str):
  filename = ARTIFACT_FOLDER + '\\' + filename
  # Remove the spaces in the filename
  filename = filename.replace(" ", "_")
  # Makes sure that, if a directory is in the filename, that directory exists
  os.makedirs(os.path.dirname(filename), exist_ok=True) 
  with open(filename, 'w') as outfile:
    json.dump(data, outfile, indent=4)

def load_data(filename :str):
  # Remove the spaces in the filename
  filename = filename.replace(" ", "_")
  if check_file(filename):
    filename = ARTIFACT_FOLDER + '\\' + filename
    with open(filename, 'r') as infile:
      return json.load(infile)
  raise FileNotFoundError("The file with filename {} does not exist.".format(filename))

def check_file(filename :str):
  filename = ARTIFACT_FOLDER + '\\' + filename
  return os.path.isfile(filename)

def clear_cache(filename :str):
  if not check_file(filename):
    return
  filename = ARTIFACT_FOLDER + '\\' + filename
  os.remove(filename)