from distutils.core import setup
import os

NAME = 'outsystems-pipeline'
DESCRIPTION = 'Python package to accelerate the integration of OutSystems with third-party CI/CD tools'
LONG_DESCRIPTION = '''The outsystems-pipeline Python package provides functions to support the creation of OutSystems CI/CD pipelines using your DevOps automation tool of choice.

Visit the `project repository <https://github.com/OutSystems/outsystems-pipeline>`_ on GitHub for instructions on how to build example OutSystems CI/CD pipelines with common DevOps automation tools, as well as documentation that will help you adapt the examples to your particular scenarios.


What's new
==========

**Config File Support**

 Added support for loading configuration values from a custom configuration file to the `generate_manifest_file.py` script, completing the configuration file support across the pipeline scripts.

 To use this feature, use the `--config_file` parameter to specify the configuration file path.

**Updated Package Dependencies**

The package dependencies have been updated to their latest supported versions:

 * `requests` to version 2.34.2
 * `python-dotenv` to version 1.2.3
 * `unittest-xml-reporting` to version 4.0.0
 * `packaging` to version 26.3

 The minimum supported Python version is now 3.10.


Installing and upgrading
========================

Install or upgrade outsystems-pipeline to the latest available version as follows:
::

    pip install -U outsystems-pipeline

'''
AUTHOR = u'OutSystems'
EMAIL = u'cicd.integrations@outsystems.com'
URL = 'https://github.com/OutSystems/outsystems-pipeline'
LICENSE = 'Apache License 2.0'
PYTHON_REQUIRES = '>=3.10'
KEYWORDS = [
    '',
]

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python',
    'Topic :: Software Development :: Build Tools',
    'Topic :: Software Development :: Quality Assurance',
    'Topic :: Software Development :: Testing',
    'Topic :: Software Development :: Testing :: Acceptance',
    'Topic :: Software Development :: Testing :: BDD',
    'Topic :: Software Development :: Testing :: Unit',
    'Topic :: System :: Software Distribution'
]

REQUIREMENTS = [
    'python-dateutil==2.9.0.post0',
    'requests==2.34.2',
    'unittest-xml-reporting==4.0.0',
    'xunitparser==1.3.4',
    'toposort==1.10',
    'python-dotenv==1.2.3',
    'packaging==26.3'
]

PACKAGES = [
    'outsystems',
    'outsystems.architecture_dashboard',
    'outsystems.bdd_framework',
    'outsystems.cicd_probe',
    'outsystems.exceptions',
    'outsystems.file_helpers',
    'outsystems.lifetime',
    'outsystems.manifest',
    'outsystems.osp_tool',
    'outsystems.pipeline',
    'outsystems.properties',
    'outsystems.vars'
]

if __name__ == '__main__':  # Do not run setup() when we import this module.
    if os.path.isfile("VERSION"):
        with open("VERSION", 'r') as version_file:
            version = version_file.read().replace('\n', '')
    else:
        # dummy version
        version = '1.0.0'

    setup(
        name=NAME,
        version='<version>',
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        keywords=' '.join(KEYWORDS),
        author=AUTHOR,
        author_email=EMAIL,
        url=URL,
        license=LICENSE,
        python_requires=PYTHON_REQUIRES,
        classifiers=CLASSIFIERS,
        packages=PACKAGES,
        install_requires=REQUIREMENTS
    )
