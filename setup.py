from distutils.core import setup
import os

NAME = 'outsystems-pipeline'
DESCRIPTION = 'Python package to accelerate the integration of OutSystems with third-party CI/CD tools'
LONG_DESCRIPTION = '''The outsystems-pipeline Python package provides functions to support the creation of OutSystems CI/CD pipelines using your DevOps automation tool of choice.

Visit the `project repository <https://github.com/OutSystems/outsystems-pipeline>`_ on GitHub for instructions on how to build example OutSystems CI/CD pipelines with common DevOps automation tools, as well as documentation that will help you adapt the examples to your particular scenarios.


What's new
==========

**Fetch Application Source Code**
 * New function to extract the source code of LifeTime applications.
 
=========


**LifeTime Deployment Operations**
 * New function to resume the execution of a deployment plan on a target environment where 2-stage deployments are enabled.

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
PYTHON_REQUIRES = '>=3.0'
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
    'python-dateutil==2.7.5',
    'requests==2.20.1',
    'unittest-xml-reporting==2.2.1',
    'xunitparser==1.3.3',
    'pytest==4.3.0',
    'toposort==1.5'
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
