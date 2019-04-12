# Dependencies to run / test locally

In order to be able to test locally, there's a few things you'll have to install. For the pipeline itself, you won't need to do this. That is assured by the pipeline code.

## Install Python

* Go to <https://www.python.org/downloads/>
* Install Python v3.7.x (the code was tested with v3.7.1)

## Install Python dependencies

To install all the dependencies you'll need:

* **Pip**
  * Download Pip: <https://bootstrap.pypa.io/get-pip.py>
  * Run the script to install pip: `python get-pip.py`

* **Dependencies**
  * To install the dependencies needed, you just need to install the requirements with pip.
  * On the root dir run: `pip install -q -I -r cd_pipelines/requirements.txt`