# pybis2spice
A python tool that converts IBIS models to SPICE models

## Features
* SPICE model creation for input models
* SPICE model creation for 2-state and 3-state output models
* _SPICE model creation for open drain outputs (Under development)_

## Usage
The gui folder contains an executable that can be run standalone.
![](/img/gui-window.png)

### The executable program allows the user to:
* Browse for an ibis model file
* Select the component and the model
* Create the SPICE subcircuit with some options 
* Check the selected model (view the graphs for the I-V and Voltage-Time characteristics)
![](/img/gui-check-model.png)


### Spice Subcircuit option: 
* LTSpice: LTSpice option produces a subcircuit file containing special syntax specific to LTSpice
* Generic: generic option produces a subcircuit file that most Spice simulators should be able to parse. Tested with Simetrix version 8.x

### Corner Select: 
* Weak-Slow: Combining the minimum I-V curves and slow Voltage-Time waveforms   
* Typical: Combining the typical I-V curves and typical Voltage-Time corners
* Fast-Strong: Combining the maximum I-V curves and typical Voltage-Time corners

## Examples
LTSpice and Simetrix examples are given to highlight the different options available. 
These are available in the examples folder

## Contribution
Developers can contribute to the tool by forking the repository, creating changes and submitting appropriate pull requests.

## References
The tool would not be possible without the ecdtools library. This parses the ibis file into python data structures.
https://ecdtools.readthedocs.io/en/latest/#

