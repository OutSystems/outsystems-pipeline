from distutils.core import setup
import os

NAME = 'outsystems-pipeline'
DESCRIPTION = 'Python package to accelerate the integration of OutSystems with third-party CI/CD tools'
LONG_DESCRIPTION = '''The outsystems-pipeline Python package provides functions to support the creation of OutSystems CI/CD pipelines using your DevOps automation tool of choice.

Visit the `project repository <https://github.com/OutSystems/outsystems-pipeline>`_ on GitHub for instructions on how to build example OutSystems CI/CD pipelines with common DevOps automation tools, as well as documentation that will help you adapt the examples to your particular scenarios.


What's new
==========

**Download Application Source Code**

 A new script was added to download platform-generated source code:

 * `fetch_apps_source_code.py`

 Use the following parameters to generate more human-readable outputs and facilitate the compilation of the source code:

 * --friendly_package_names: source code packages with user-friendly names.
 * --include_all_refs: adds to .csproj file all assemblies in the bin folder as references.
 * --remove_resources_files: removes references to embedded resources files from the.csproj file.

**Solution Download and Deploy**

 Added new functions to leverage the recently released/improved APIs to download and deploy outsystems packages:

 * `fetch_lifetime_solution_from_manifest.py` - downloads a solution file based on manifest data.
 * `deploy_package_to_target_env.py` - deploys an outsystems package (solution or application) to a target environment.
 * `deploy_package_to_target_env_with_osptool.py` - deploys an outsystems package (solution or application) using OSP Tool.

**Improved OSPTool Operations**

 OSPTool command line calls now have live output callback and catalog mapping support.

**Updated Package Dependencies**

 * Updated python-dateutil dependency to version 2.9.0.post0
 * Updated python-dotenv dependency to version 1.0.1

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
PYTHON_REQUIRES = '>=3.8'
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
    'requests==2.31.0',
    'unittest-xml-reporting==3.2.0',
    'xunitparser==1.3.4',
    'toposort==1.10',
    'python-dotenv==1.0.1'
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
