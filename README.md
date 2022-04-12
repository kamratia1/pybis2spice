# pybis2spice
A python tool that converts IBIS models to SPICE models. The ibis model types currently supported are: 
* Input
* Output
* 3-State
* Open_Drain
* I/O

## Usage
The bin folder holds a zipped file for each released version containing a windows executable program that can be run standalone.
![](/img/gui-window.png)

### The executable program allows the user to:
* Browse for an ibis model file
* Select the component and the model
* Create the SPICE subcircuit files
* View the ibis model characteristics (I-V and Voltage-Time graphs)
![](/img/gui-check-model.png)


### Spice Subcircuit option: 
* LTSpice: LTSpice option produces a subcircuit file and corresponding LTSpice symbol file. 
This option creates a subcircuit that is specifically intended to be used with LTSpice. 
This is the recommended option as it provides the most flexibility for output model stimulus sources. 
* Generic: generic option produces a subcircuit file that most Spice simulators should be able to parse.

### Corner Select: 
* Weak-Slow: Combines the minimum (weak) I-V curves and minimum (slow) Voltage-Time waveforms   
* Typical: Combines the typical I-V curves and typical Voltage-Time waveforms
* Fast-Strong: Combines the maximum (strong) I-V curves and maximum (fast) Voltage-Time waveforms
* All: Creates the subcircuit files for all corners simultaneously

## Examples
LTSpice examples are given to highlight the different options available. 
These are available in the examples folder

## Contribution
Developers can contribute to the tool by forking the repository and submitting pull requests.

## Issues and Feature Requests
* Please record any bugs, issues and feature requests here: https://github.com/kamratia1/pybis2spice/issues
* Detailed information on how any issue can be reproduced should be provided including any IBIS files used and version number of the program. Screenshots would also help.


## References
The tool would not be possible without the ecdtools library. This parses the ibis file into python data structures.
https://ecdtools.readthedocs.io/en/latest/#

