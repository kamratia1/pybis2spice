#----------------------------------------------------------------------------
# Author: Kishan Amratia
# Date: 02-Jan-2022
# Module Name: pybis2spice-cli.py
"""
A command-line interface tool for helping users to convert IBIS models into SPICE models
OBSOLETE - No longer planned to be developed. Kept here for reference.
"""
# ---------------------------------------------------------------------------

# Import the library
import pybis2spice
import os
import argparse
import version


def validate_inputs():
    pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="ibis file path")
    parser.add_argument("cmp", help="ibis component name")
    parser.add_argument("mod", help="ibis model name")
    parser.add_argument("out", help="output subcircuit file path")

    parser.add_argument("-v", action="version",
                        version=f'pybis2spice version {version.__version__} (released {version.__date__})')
    parser.add_argument("-s", nargs=1,
                        help="subcircuit option. 1 is for a LTSpice subcircuit model, 2 is a generic subcircuit model",
                        choices=[1, 2], default=1)

    args = parser.parse_args()
    print(f"input file:         {args.input}")
    print(f"component name:     {args.cmp}")
    print(f"model name:         {args.mod}")
    print(f"output file:        {args.out}")
    print(f"subcircuit option:  {args.s}")


# Validate the inputs
# Check that input file name is acceptable
# Check that output file directory exists and file is not being overridden
# Check that component exists in the input file
# Check that model exists in the input ibis file

# Run the IBIS model converter program

#directory = os.path.dirname(os.getcwd())

#file_path = os.path.join(directory, 'test/ibis/stm32g031_041_ufqfpn32.ibs')
#model_name = 'io6_ft_3v3_highspeed'
#component_name = 'stm32g031_041_ufqfpn32'

# Loads the IBIS model with the user input parameters
#ibis_data = pybis2spice.DataModel(file_path, model_name, component_name)

# printing the output allows the user to scan and check that the right data has been loaded
#print(ibis_data)




