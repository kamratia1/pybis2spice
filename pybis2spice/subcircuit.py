# ----------------------------------------------------------------------------
# Author: Kishan Amratia
# Module Name: subcircuit.py
#
# Module Description:
# Companion functions for the pybis2spice module to create the SPICE subcircuit file
#
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import numpy as np
from pybis2spice import pybis2spice
from pybis2spice import version


def generate_spice_model(io_type, subcircuit_type, ibis_data, corner, output_filepath):
    """
    Wrapper around the subcircuit file creation functions. Calls the relevant function i.e. LTSpice or Generic

        Parameters:
            io_type - "Input" or "Output"
            subcircuit_type - "LTSpice" or "Generic"
            ibis_data - a DataModel object (defined in pybis2spice.py)
            corner - "Weak-Slow" or "Typical" or "Fast-Strong"
            output_filepath - path of output file

        Returns:
            The path of the created file
    """
    ret = None
    if io_type == "Output":
        if subcircuit_type == "Generic":
            ret = create_generic_output_model(ibis_data, corner, output_filepath)

        if subcircuit_type == "LTSpice":
            ret = create_ltspice_output_model(ibis_data, corner, output_filepath)

    if io_type == "Input":
        ret = create_input_model(ibis_data, corner, output_filepath)

    return ret


def convert_corner_str_to_index(corner):
    index = 1
    if corner == "Weak-Slow":
        index = 0
    if corner == "Typical":
        index = 1
    if corner == "Fast-Strong":
        index = 2

    return index


def create_input_model(ibis_data, corner, output_filepath):
    """
    Creates a SPICE generic subcircuit model.
    Generic models are simple and only supports a single oscillation pulse with a given frequency

    Parameters:
        ibis_data - a DataModel object (defined in pybis2spice.py)
        corner - "Weak-Slow" or "Typical" or "Fast-Strong"
        output_filepath - path of output file
    """

    _INDEX = convert_corner_str_to_index(corner)
    _CORNER_INDEX = _INDEX + 1

    vcc = ibis_data.v_range[_INDEX]
    pwr_clamp_ref = pybis2spice.get_reference(ibis_data.pwr_clamp_ref, ibis_data.v_range, _CORNER_INDEX)
    gnd_clamp_ref = pybis2spice.get_reference(ibis_data.gnd_clamp_ref, 0, _CORNER_INDEX)

    with open(output_filepath, 'w') as file:
        file.write(f'.SUBCKT {ibis_data.model_name}-{corner} IN\n\n')

        # Write some comments to help Identify the file
        file.write(f'* Component: {ibis_data.component_name}\n')
        file.write(f'* Model: {ibis_data.model_name}\n')
        file.write(f'* Model Type: Input\n')
        file.write(f'* Corner: {corner}\n')

        # Add some model characteristics - Voltage...etc
        file.write(f'* SPICE model created with pybis2spice version {version.get_version()}\n')
        file.write(f'* For more info, visit https://github.com/kamratia1/pybis2spice/\n\n')

        file.write(f'.param C_pkg = {ibis_data.c_pkg[_INDEX]}\n')
        file.write(f'.param L_pkg = {ibis_data.l_pkg[_INDEX]}\n')
        file.write(f'.param R_pkg = {ibis_data.r_pkg[_INDEX]}\n')
        file.write(f'.param C_comp = {ibis_data.c_comp[_INDEX]}\n')
        file.write(f'.param V_supply = {vcc}\n\n')

        file.write(f'R1 IN MID {{R_pkg}}\n')
        file.write(f'L1 DIE MID {{L_pkg}}\n')
        file.write(f'C1 IN 0 {{C_pkg}}\n')
        file.write(f'C2 DIE 0 {{C_comp}}\n')
        file.write(f'V1 VCC 0 {{V_supply}}\n\n')

        # Arbitrary Source definition for power and ground clamp
        if ibis_data.iv_pwr_clamp is not None:
            pwr_clamp_table_str = convert_iv_table_to_str(np.flip(pwr_clamp_ref - ibis_data.iv_pwr_clamp[:, 0]),
                                                          np.flip(ibis_data.iv_pwr_clamp[:, _CORNER_INDEX]))
            file.write(f'B1 die VCC I = table(V(DIE), {pwr_clamp_table_str})\n')

        if ibis_data.iv_gnd_clamp is not None:
            gnd_clamp_table_str = convert_iv_table_to_str(ibis_data.iv_gnd_clamp[:, 0] - gnd_clamp_ref,
                                                          ibis_data.iv_gnd_clamp[:, _CORNER_INDEX])
            file.write(f'B2 die 0 I = table(V(DIE), {gnd_clamp_table_str})\n\n')

        file.write(f'.ends\n')

    return 0


def create_generic_output_model(ibis_data, corner, output_filepath):
    """
    Creates a SPICE generic subcircuit model.
    Generic models are simple and only supports a single oscillation pulse with a given frequency

    Parameters:
        ibis_data - a DataModel object (defined in pybis2spice.py)
        corner - "Weak-Slow" or "Typical" or "Fast-Strong"
        output_filepath - path of output file

    Returns 0 if there are no errors in the creation
    """
    _INDEX = convert_corner_str_to_index(corner)
    _CORNER_INDEX = _INDEX + 1

    vcc = ibis_data.v_range[_INDEX]
    pwr_clamp_ref = pybis2spice.get_reference(ibis_data.pwr_clamp_ref, ibis_data.v_range, _CORNER_INDEX)
    gnd_clamp_ref = pybis2spice.get_reference(ibis_data.gnd_clamp_ref, 0, _CORNER_INDEX)
    pullup_ref = pybis2spice.get_reference(ibis_data.pullup_ref, ibis_data.v_range, corner)
    pulldown_ref = pybis2spice.get_reference(ibis_data.pulldown_ref, 0, corner)

    return 0


def create_ltspice_output_model(ibis_data, corner, output_filepath):
    """
    Creates a SPICE generic subcircuit model.
    LTSpice specific models provide extra functionality to manipulate the waveform stimulus of the output

    Parameters:
        ibis_data - a DataModel object (defined in pybis2spice.py)
        corner - "Weak-Slow" or "Typical" or "Fast-Strong"
        output_filepath - path of output file

    Returns 0 if there are no errors in the creation
    """
    return 1  # Setting this to 1 to ensure GUI can't proceed


def convert_iv_table_to_str(voltage, current):
    """
    Creates the IV table of values for the current sources modelling the devices and clamps

        Parameters:
            voltage - numpy voltage array
            current - corresponding numpy current array

        Returns:
            str_val: the string that goes into subcircuit table
    """
    str_val = f'{voltage[0]}, {current[0]}'
    for i in range(1, len(voltage)):
        str_val = str_val + f', {voltage[i]}, {current[i]}'
    return str_val


def create_edge_waveform_pwl(time, k_param):
    """
    Creates the PWL value string for the oscillation waveform
    Only valid for LTSpice subcircuit

        Parameters:
            time - numpy time array for k parameter waveform
            k_param - numpy array for k_r or k_f waveform

        Returns:
            str_val: the string that goes into PWL source for the edge
    """
    str_val = f'{{delay}}, {k_param[0]}'
    for i in range(1, len(time)):
        str_val = str_val + f', {{delay+{time[i]}}}, {k_param[i]}'
    return str_val


def create_osc_waveform_pwl(t_r, k_r, t_f, k_f):
    """
    Creates the PWL value string for the oscillation waveform

        Parameters:
            t_r - numpy time array for k_r waveform
            t_f - numpy time array for k_f waveform
            k_r - numpy ku or kd array for k_r waveform
            k_f - numpy ku or kd array for k_f waveform

        Returns:
            str_val: the string that goes into the oscillator PWL source
    """

    # Rising Edge
    # the +0.01p fudge is for Simetrix as it seems to have a bug in its PWLS source
    # where it cannot start at any value other than 0 regardless of the k_r[0] value
    str_val = f'0 {k_r[0]} +0.01p {k_r[0]}'
    for i in range(1, len(t_r)):
        dt = t_r[i] - t_r[i - 1]
        str_val = str_val + f' +{dt} {k_r[i]}'

    str_val = str_val + f' +{{gap_pos}} {k_r[-1]} +{t_f[0]} {k_f[0]}'

    # Falling Edge
    for i in range(1, len(t_f)):
        dt = t_f[i] - t_f[i - 1]
        str_val = str_val + f' +{dt} {k_f[i]}'

    str_val = str_val + f' +{{gap_neg}} {k_f[-1]}'

    # gap_pos and gap_neg are parameters calculated within SPICE to oscillate at the right frequency and duty

    return str_val


def determine_crossover_offsets(k_param):
    """
    returns the approximate crossover point between the rising and falling k_param waveforms
        offset_neg: Time offset between beginning of k_param to crossover point
        offset_neg: Time offset between crossover point to end of k_param
    """

    # crossover time point (x_t)
    index = np.argmin(np.absolute(k_param[:, 1] - k_param[:, 2]))
    x_t = k_param[index, 0]

    # Time offset
    offset_neg = x_t - k_param[0][0]
    offset_pos = k_param[:, 0][-1] - x_t

    return offset_neg, offset_pos


# This is an OLD function - to be removed
def create_output_subcircuit_file(ibis_data, output_filepath, k_param_rise, k_param_fall):
    _TYP = 0
    _MIN = 1
    _MAX = 2
    _INDEX = _TYP
    _CORNER_INDEX = _INDEX + 1

    simulation_tool = ''
    corner_str = 'Typ'
    subcircuit_name = f'{ibis_data.model_name}-{ibis_data.component_name}-{corner_str}-Output'

    k_ur_str = create_edge_waveform_pwl(k_param_rise[:, 0], k_param_rise[:, 1])
    k_uf_str = create_edge_waveform_pwl(k_param_fall[:, 0], k_param_fall[:, 1])
    k_u_osc_str = create_osc_waveform_pwl(k_param_rise[:, 0], k_param_rise[:, 1], k_param_fall[:, 0],
                                          k_param_fall[:, 1])

    k_dr_str = create_edge_waveform_pwl(k_param_rise[:, 0], k_param_rise[:, 2])
    k_df_str = create_edge_waveform_pwl(k_param_fall[:, 0], k_param_fall[:, 2])
    k_d_osc_str = create_osc_waveform_pwl(k_param_rise[:, 0], k_param_rise[:, 2], k_param_fall[:, 0],
                                          k_param_fall[:, 2])

    with open(output_filepath, 'w') as file:
        file.write(f'.SUBCKT {subcircuit_name} OUT params: stimulus=0 edge=0 delay=10n freq=10Meg duty=0.5\n\n')

        # TODO use pullup/pulldown ref and clamp references where available

        vcc = ibis_data.v_range[_INDEX]

        file.write(f'.param C_pkg = {ibis_data.c_pkg[_INDEX]}\n')
        file.write(f'.param L_pkg = {ibis_data.l_pkg[_INDEX]}\n')
        file.write(f'.param R_pkg = {ibis_data.r_pkg[_INDEX]}\n')
        file.write(f'.param C_comp = {ibis_data.c_comp[_INDEX]}\n')
        file.write(f'.param V_supply = {vcc}\n\n')

        # Calculations to define the oscillation stimulus
        (offset_neg_r, offset_pos_r) = determine_crossover_offsets(k_param_rise)
        (offset_neg_f, offset_pos_f) = determine_crossover_offsets(k_param_fall)
        file.write(f'.param calc_gap_pos = {{(duty/freq) - {offset_pos_r} - {offset_neg_f}}}\n')
        file.write(f'.param calc_gap_neg = {{((1-duty)/freq) - {offset_pos_f} - {offset_neg_r}}}\n\n')

        file.write(f'.param gap_pos = {{if(calc_gap_pos <= 0, 0.1p, calc_gap_pos)}}\n')
        file.write(f'.param gap_neg = {{if(calc_gap_neg <= 0, 0.1p, calc_gap_neg)}}\n\n')

        file.write(f'R3 OUT N001 {{R_pkg}}\n')
        file.write(f'L1 Vdie N001 {{L_pkg}}\n')
        file.write(f'C1 OUT 0 {{C_pkg}}\n')
        file.write(f'C2 Vdie 0 {{C_comp}}\n')
        file.write(f'V13 VCC 0 {{V_supply}}\n\n')

        # Arbitrary Source definition for power and ground clamp
        if ibis_data.iv_pwr_clamp is not None:
            pwr_clamp_table_str = convert_iv_table_to_str(np.flip(vcc - ibis_data.iv_pwr_clamp[:, 0]),
                                                          np.flip(ibis_data.iv_pwr_clamp[:, _CORNER_INDEX]))
            file.write(f'B4 Vdie VCC I = table(v(Vdie), {pwr_clamp_table_str})\n')

        if ibis_data.iv_gnd_clamp is not None:
            gnd_clamp_table_str = convert_iv_table_to_str(ibis_data.iv_gnd_clamp[:, 0],
                                                          ibis_data.iv_gnd_clamp[:, _CORNER_INDEX])
            file.write(f'B3 Vdie 0 I = table(V(Vdie), {gnd_clamp_table_str})\n')

        # Arbitrary Source definition for pullup and pulldown devices
        if ibis_data.iv_pullup is not None:
            pullup_table_str = convert_iv_table_to_str(np.flip(vcc - ibis_data.iv_pullup[:, 0]),
                                                       np.flip(ibis_data.iv_pullup[:, _CORNER_INDEX]))
            file.write(f'B1 Vdie VCC I={{V(Ku)* table(v(Vdie), {pullup_table_str})}}\n')

        if ibis_data.iv_pulldown is not None:
            pulldown_table_str = convert_iv_table_to_str(ibis_data.iv_pulldown[:, 0],
                                                         ibis_data.iv_pulldown[:, _CORNER_INDEX])
            file.write(f'B5 Vdie 0 I={{V(Kd)*table(V(vdie), {pulldown_table_str})}}\n\n')

        # Adding some comments in the subcircuit for reference
        file.write(f'* Stimulus --> Oscillator=0, Edge=1\n')
        file.write(f'* Edge --> Rising=0, Falling=1\n\n')

        file.write(f'.model SW SW(Ron=1n Roff=1G Vt=0.5)\n\n')

        # Pullup Device K-parameter Definition
        file.write(f'* Pullup Device\n')
        file.write(f'S1 Ku rising_pu Au 0 SW\n')
        file.write(f'S2 Ku falling_pu Bu 0 SW\n')
        file.write(f'S3 Ku oscillation_pu Cu 0 SW\n\n')

        file.write(f'V3 Au 0 {{if(stimulus==1, if(edge==0,1,0), 0)}}\n')
        file.write(f'V7 Cu 0 {{if(stimulus==0,1,0)}}\n')
        file.write(f'V8 Bu 0 {{if(stimulus==1, if(edge==1,1,0), 0)}}\n\n')

        # For the oscillation PWL sources, Simetrix and LTSpice implement this in a subtly different way.
        # LTSpice uses a simple PWL source, whereas Simetrix uses a PWLS source

        # Insert Pullup transistor PWL Sources here
        file.write(f'V4 rising_pu 0 PWL({k_ur_str})\n')
        file.write(f'V5 falling_pu 0 PWL({k_uf_str})\n')
        if simulation_tool is not None:
            file.write(f'V6 oscillation_pu 0 PWL REPEAT FOREVER ({k_u_osc_str}) ENDREPEAT\n\n')
        else:
            file.write(f'V6 oscillation_pu 0 PWL({k_ur_str})\n\n')

        # Pulldown Device K-parameter Definition
        file.write(f'* Pulldown Device\n')
        file.write(f'S4 Kd rising_pd Ad 0 SW\n')
        file.write(f'S5 Kd falling_pd Bd 0 SW\n')
        file.write(f'S6 Kd oscillation_pd Cd 0 SW\n\n')

        file.write(f'V1 Ad 0 {{if(stimulus==1, if(edge==0,1,0), 0)}}\n')
        file.write(f'V11 Cd 0 {{if(stimulus==0,1,0)}}\n')
        file.write(f'V12 Bd 0 {{if(stimulus==1, if(edge==1,1,0), 0)}}\n\n')

        # Insert Pulldown transistor PWL Sources here
        file.write(f'V2 rising_pd 0 PWL({k_dr_str})\n')
        file.write(f'V9 falling_pd 0 PWL({k_df_str})\n')
        if simulation_tool is not None:
            file.write(f'V10 oscillation_pd 0 PWL REPEAT FOREVER ({k_d_osc_str}) ENDREPEAT\n\n')
        else:
            file.write(f'V10 oscillation_pd 0 PWL({k_dr_str})\n\n')

        file.write(f'.ends\n')
