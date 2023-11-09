from distutils.core import setup
import os

NAME = 'outsystems-pipeline'
DESCRIPTION = 'Python package to accelerate the integration of OutSystems with third-party CI/CD tools'
LONG_DESCRIPTION = '''The outsystems-pipeline Python package provides functions to support the creation of OutSystems CI/CD pipelines using your DevOps automation tool of choice.

Visit the `project repository <https://github.com/OutSystems/outsystems-pipeline>`_ on GitHub for instructions on how to build example OutSystems CI/CD pipelines with common DevOps automation tools, as well as documentation that will help you adapt the examples to your particular scenarios.


What's new
==========

**Config File Support**
 Load configuration values from a custom file to override default values. To use this feature, use the new `--config_file` parameter to specify the configuration file path.
 This enhancement is available in the following scripts:

 * `apply_configuration_values_to_target_env.py`
 * `continue_deployment_to_target_env.py`
 * `deploy_apps_to_target_env_with_airgap.py`
 * `deploy_latest_tags_to_target_env.py`
 * `deploy_tags_to_target_env_with_manifest.py`
 * `evaluate_test_results.py`
 * `fetch_apps_packages.py`
 * `fetch_lifetime_data.py`
 * `scan_test_endpoints.py`
 * `start_deployment_to_target_env.py`
 * `tag_apps_based_on_manifest_data.py`
 * `tag_modified_apps.py`

**SSL Certificate Verification**
 The Python `requests` module verifies SSL certificates for HTTPS requests.
 Now there's a flag to enable (default value) or disable SSL certificate verification.


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
    'python-dateutil==2.8.2',
    'requests==2.31.0',
    'unittest-xml-reporting==3.2.0',
    'xunitparser==1.3.4',
    'toposort==1.10',
    'python-dotenv==1.0.0'
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
