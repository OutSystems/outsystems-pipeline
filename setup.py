from distutils.core import setup
import os

NAME = 'outsystems-pipeline'
DESCRIPTION = 'Python pipeline to enable continuous testing using OutSystems.'
AUTHOR = u'João Furtado, Miguel Afonso, Rui Mendes, Mário Pires'
EMAIL = u'cicd.integrations@outsystems.com'
URL = 'https://github.com/OutSystems/outsystems-pipeline'
KEYWORDS = [
    '',
]

REQUIREMENTS = [
    'python-dateutil==2.7.5',
    'requests==2.20.1',
    'unittest-xml-reporting==2.2.1',
    'xunitparser==1.3.3',
    'pytest==4.3.0'
]

PACKAGES = [
    'outsystems',
    'outsystems.bdd_framework',
    'outsystems.cicd_probe',
    'outsystems.exceptions',
    'outsystems.file_helpers',
    'outsystems.lifetime',
    'outsystems.pipeline',
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
        keywords=' '.join(KEYWORDS),
        author=AUTHOR,
        author_email=EMAIL,
        url=URL,
        packages=PACKAGES,
        install_requires=REQUIREMENTS
    )
