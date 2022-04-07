import argparse
import fileinput
import xmlrpc.client

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", help="Toggle if you're doing a revision version.", action="store_true")
    parser.add_argument("--minor", help="Toggle if you're doing a minor version.", action="store_true")
    args = parser.parse_args()

    client = xmlrpc.client.ServerProxy('https://pypi.org/pypi')
    version = client.package_releases('outsystems-pipeline')[0]
    version_array = version.split('.')

    if args.revision:
        if len(version_array) > 2:
            # Increments the previous beta version
            revision_version = int(version_array[-1])
            version_array[-1] = str(revision_version + 1)
        else:
            # no beta version, creates one with 1
            version_array.extend("1")
    elif args.minor:
        if len(version_array) > 2:
            # Removes the previous beta version
            version_array[-1] = "0"
        else:
            # forces 3 part release versions
            while len(version_array) < 3:
                version_array.extend("0")
        minor_version = int(version_array[-2])
        version_array[-2] = str(minor_version + 1)
    else:
        major_version = int(version_array[0])
        version_array = [str(major_version + 1), "0", "0"]

    version = ".".join(version_array)

    with fileinput.FileInput("setup.py", inplace=True, backup='.bak') as setup_file:
        for line in setup_file:
            print(line.replace("version='<version>'", "version='{}'".format(version)), end='')
#    with open("VERSION", 'w') as version_file:
#        version_file.write(version)
