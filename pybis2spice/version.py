
# This version is for both the GUI and the main pybis2spice module
__version__ = '0.1.0'
__date__ = '15 March 2022'

import os


def get_version():
    return __version__


def get_date():
    return __date__


def create_version_txt_file():
    version_txt_file = os.path.join(os.path.dirname(os.getcwd()), "pybis2spice", "version.txt")
    with open(version_txt_file, 'w') as file:
        file.write(f'{get_version()}')
