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

# Create the version txt file
version.create_version_txt_file()

# MAKE SURE THE WORKING DIRECTORY IS CLOSED BEFORE RUNNING THESE SCRIPTS

if os.path.exists('pybis2spice-gui.exe'):
    os.remove('pybis2spice-gui.exe')

PyInstaller.__main__.run([
    'pybis2spice-gui.py',
    '--noconsole',
    '-iicon.ico',
    '--onefile'
])

shutil.copy(os.path.join('dist', 'pybis2spice-gui.exe'), os.getcwd())

# Remove the files
#shutil.rmtree('build')
#os.remove('pybis2spice-gui.spec')

# Move the exe file
#shutil.move(os.path.join('dist', 'pybis2spice-gui.exe'), os.getcwd())
#shutil.rmtree('dist')

