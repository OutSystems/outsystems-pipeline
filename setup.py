import argparse, sys
from distutils.core import setup

NAME = 'outsystems-pipeline'
DESCRIPTION = 'Python pipeline to enable continuous testing using OutSystems.'
AUTHOR = u'João Furtado, Miguel Afonso, Rui Mendes'
EMAIL = u'joao.furtado@outsystems.com, miguel.afonso@outsystems.com, rui.mendes@outsystems.com'
URL = 'https://github.com/OutSystems/outsystems-pipeline'
KEYWORDS = [
    '',
]

with open('build-requirements.txt') as f:
    requirements = f.read().splitlines()

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", help="Toggle if you're doing a revision version.", action="store_true")
    parser.add_argument("--minor", help="Toggle if you're doing a minor version.", action="store_true")
    parser.add_argument("sdist")
    args = parser.parse_args()

    with open("VERSION", 'r') as version_file:
        version = version_file.read().replace('\n','')
        version_array = version.split('.')

    if args.revision:
        if len(version_array) > 2: # Increments the previous beta version
            revision_version = int(version_array[-1])
            version_array[-1] = str(revision_version + 1)
        else: # no beta version, creates one with 1
            version_array.extend("1")
    elif args.minor:
        if len(version_array) > 2: # Removes the previous beta version
            version_array[-1] = "0" # remove revision
        else: # forces 3 part release versions
            while len(version_array) < 3:
                version_array.extend("0")
        minor_version = int(version_array[-2])
        version_array[-2] = str(minor_version + 1)
    else:
        major_version = int(version_array[0])
        version_array = [str(major_version + 1), "0", "0"]

    version = ".".join(version_array)

    if "--revision" in sys.argv:
        sys.argv.remove("--revision")
    if "--minor" in sys.argv:
        sys.argv.remove("--minor")
    
    with open("VERSION", 'w') as version_file:
        version_file.write(version)

    setup(
        name=NAME,
        version=version,
        description=DESCRIPTION,
        keywords=' '.join(KEYWORDS),
        author=AUTHOR,
        author_email=EMAIL,
        url=URL,
        packages=PACKAGES,
        install_requires=requirements
    )