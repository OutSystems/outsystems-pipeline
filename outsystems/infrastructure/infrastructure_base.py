import subprocess

# Custom functions
from vars.os_vars import LOCAL_DRIVE, REMOTE_DRIVE


def connect_shared_drive(host: str, fileshare_user: str, fileshare_pass: str):
    # Disconnect anything on SHARED_DRIVE
    subprocess.call(r'net use {} /del'.format(LOCAL_DRIVE), shell=True)

    # Connect to shared drive, use drive letter SHARED_DRIVE
    subprocess.call(r'net use {} "\\{}\{}" /user:\{} {}'.format(LOCAL_DRIVE, host, REMOTE_DRIVE, fileshare_user, fileshare_pass), shell=True)


def disconnect_shared_drive():
    # Disconnect anything on SHARED_DRIVE
    subprocess.call(r'net use {} /del'.format(LOCAL_DRIVE), shell=True)
