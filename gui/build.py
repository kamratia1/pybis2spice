# ---------------------------------------------------------------------------
# Author: Kishan Amratia
# Date: 02-Jan-2022
# Module Name: build.py
"""
A build script to create executable versions of the cli and gui
"""
# ---------------------------------------------------------------------------

import PyInstaller.__main__
import shutil
import os
from pybis2spice import version
import fnmatch

_GENERATE_EXE_GUI = True


def create_gui_exe():
    # MAKE SURE THE WORKING DIRECTORY IS CLOSED BEFORE RUNNING THESE SCRIPTS

    if os.path.exists(f'pybis2spice-gui_v{version.get_version()}.exe'):
        os.remove(f'pybis2spice-gui_v{version.get_version()}.exe')

    PyInstaller.__main__.run([
        'pybis2spice-gui.py',
        '--noconsole',
        '-iicon.ico',
        '--onefile'
    ])

    shutil.copy(os.path.join('dist', 'pybis2spice-gui.exe'), os.getcwd())

    path = os.path.join(os.getcwd(), 'pybis2spice-gui.exe')
    return path


def recursively_delete_files_with_pattern(directory_path, pattern):
    # Get a list of all files in directory
    for root_dir, subdirs, filenames in os.walk(directory_path):
        # Find the files that matches the given pattern
        for filename in fnmatch.filter(filenames, pattern):
            try:
                os.remove(os.path.join(root_dir, filename))
            except OSError:
                print("Error while deleting file")


def folder_mopup():
    # Check if version folder already exists within bin and delete it
    folder_path = os.path.join(os.path.dirname(os.getcwd()), "bin", f"pybis2spice-v{version.get_version()}")
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    # Create the version number folder (pybis2spice_vX.Y)
    os.mkdir(folder_path)

    # Check if zip exists and delete
    zip_path = os.path.join(os.path.dirname(os.getcwd()), "bin", f"pybis2spice-v{version.get_version()}.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Copy the executable and the examples directory into the version number folder
    src_gui_filepath = os.path.join(os.getcwd(), f'pybis2spice-gui_v{version.get_version()}.exe')
    shutil.copy(src_gui_filepath, folder_path)

    src_examples_dir = os.path.join(os.path.dirname(os.getcwd()), "examples")
    dest_examples_dir = os.path.join(folder_path, "examples")
    shutil.copytree(src_examples_dir, dest_examples_dir)

    # Remove all SPICE generated .log and .raw files
    recursively_delete_files_with_pattern(dest_examples_dir, "*.raw")
    recursively_delete_files_with_pattern(dest_examples_dir, "*.log")


if __name__ == '__main__':

    version.create_version_txt_file()  # Create the version txt file

    if _GENERATE_EXE_GUI:
        gui_filepath = create_gui_exe()
    else:
        gui_filepath = os.path.join(os.getcwd(), 'pybis2spice-gui.exe')

    # Rename the GUI file to include the version number
    if os.path.exists(gui_filepath):
        try:
            os.rename(gui_filepath, os.path.join(os.getcwd(), f'pybis2spice-gui_v{version.get_version()}.exe'))
        except:
            pass

    # Creates folder in bin directory and copies executable and example files
    folder_mopup()

    # Zip up the contents
    base_path = os.path.join(os.path.dirname(os.getcwd()), "bin", f"pybis2spice-v{version.get_version()}")
    shutil.make_archive(base_name=base_path,
                        format='zip',
                        root_dir=os.path.dirname(base_path),
                        base_dir=f"pybis2spice-v{version.get_version()}")
