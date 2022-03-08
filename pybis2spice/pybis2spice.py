# ----------------------------------------------------------------------------
# Author: Kishan Amratia
# Date: XX-Jan-2022 (UPDATE)
# Module Name: pybis2spice.py
# Version: XX (UPDATE)
# 
# Module Description:
# A python package to help convert an ibis model to a spice model
# 
# References:
# https://www.analog.com/media/en/technical-documentation/application-notes/AN-715.pdf
#
# Ying Wang and Han Ngee Tan, "The development of analog SPICE behavioral model based on IBIS model,"
# Proceedings Ninth Great Lakes Symposium on VLSI, 1999, pp. 101-104,
# doi: 10.1109/GLSV.1999.757386.
# 
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import sys
import ecdtools
import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Create some data model classes for convenient data referencing
# ---------------------------------------------------------------------------


class Waveform(object):
    """
    A data container for a single waveform with a given v_fixture and r_fixture condition
    Used by the DataModel object

        Parameters:
            waveform_obj: the waveform object from the ecdtools library

        Contains 3 attributes:
            data: numpy array with the waveform data in 3 columns [time, v_typ, v_min, v_max]
            v_fix: numpy array with the v_fixture conditions for the 3 corners. Organised in 3 columns [typ, min, max]
            r_fix: the r_fixture resistance for the waveform
    """

    def __init__(self, waveform_obj):
        self.data = np.asarray(waveform_obj.table.samples, dtype='float64')  # Time, Typ, Min, Max
        self.v_fix = np.asarray([float(waveform_obj.v_fixture.typical), float(waveform_obj.v_fixture.minimum),
                                 float(waveform_obj.v_fixture.maximum)])
        self.r_fix = float(waveform_obj.r_fixture)

    def __repr__(self):
        return f"> v_fixture:{self.v_fix}\n" \
               f"> r_fixture: {self.r_fix}\n" \
               f"> waveform_size: {np.shape(self.data)}"


class DataModel(object):
    """
    A data container for the various data tables in the ibis model
    """

    def __init__(self, file_path, model_name, component_name):
        """
        Populate the attributes of the DataModel object

            Parameters:
                file_path: path to the ibis file
                model_name: model name as defined in ibis model
                component_name: component name as defined in ibis model

            All Data is stored in numpy arrays organised in columns as typical, min and max:
                For parasitics, it is typ, min, max
                For IV tables, it is voltage, typ, min, max
                For VT tables, it is time, typ, min max

            If a table or parameter doesn't exist, then it will have a None value
        """
        self.model_name = model_name
        self.component_name = component_name

        try:
            # Load IBIS file. Transform=True converts numerical numbers from strings to decimal
            ibis = ecdtools.ibis.load_file(file_path, transform=True)

            self.file = ibis
            self.model = ibis.get_model_by_name(model_name)
            self.component = ibis.get_component_by_name(component_name)
            self.model_type = self.model.model_type

            self.r_pkg = extract_range_param(self.component.package.r_pkg)
            self.l_pkg = extract_range_param(self.component.package.l_pkg)
            self.c_pkg = extract_range_param(self.component.package.c_pkg)
            self.c_comp = extract_range_param(self.model.c_comp)
            self.v_range = extract_range_param(self.model.voltage_range)
            self.pullup_ref = extract_range_param(self.model.pullup_reference)
            self.pulldown_ref = extract_range_param(self.model.pulldown_reference)
            self.pwr_clamp_ref = extract_range_param(self.model.power_clamp_reference)
            self.gnd_clamp_ref = extract_range_param(self.model.gnd_clamp_reference)

            self.iv_pullup = extract_iv_table(self.model.pullup)
            self.iv_pulldown = extract_iv_table(self.model.pulldown)
            self.iv_pwr_clamp = extract_iv_table(self.model.power_clamp)
            self.iv_gnd_clamp = extract_iv_table(self.model.gnd_clamp)

            self.vt_rising = [Waveform(data) for data in self.model.rising_waveforms]
            self.vt_falling = [Waveform(data) for data in self.model.falling_waveforms]

        except Exception as error:
            print(error)

    def __repr__(self):
        st = f'----------------------------------------------------------------------\n\n'
        st += f'model name: {self.model_name}\n' \
              f'component name: {self.component_name}\n' \
              f'model type: {self.model_type}\n\n'

        st += f'v_range: {self.v_range}\n'
        st += f'pullup_ref: {self.pullup_ref}\n'
        st += f'pulldown_ref: {self.pulldown_ref}\n'
        st += f'pwr_clamp_ref: {self.pwr_clamp_ref}\n'
        st += f'gnd_clamp_ref: {self.gnd_clamp_ref}\n\n'

        # Package parasitics
        st += f'package parameters [Typ, Min, Max]:\n'
        st += f'> r_pkg: {self.r_pkg}\n' \
              f'> l_pkg: {self.l_pkg}\n' \
              f'> c_pkg: {self.c_pkg}\n' \
              f'> c_comp: {self.c_comp}\n\n'

        st += f'iv data:\n'
        st += f'> pullup data size: {np.shape(self.iv_pullup)}\n' \
              f'> pulldown data size: {np.shape(self.iv_pulldown)}\n'
        st += f'> pwr clamp data size: {np.shape(self.iv_pwr_clamp)}\n' \
              f'> gnd clamp data size: {np.shape(self.iv_gnd_clamp)}\n\n'

        if self.vt_rising:
            rising_str = ""
            for waveform in self.vt_rising:
                rising_str += f'{waveform}\n'

            st += f'rising waveform vt data:\n{rising_str}\n'

        if self.vt_falling:
            falling_str = ""
            for waveform in self.vt_falling:
                falling_str += f'{waveform}\n'

            st += f'falling waveform vt data:\n{falling_str}\n'

        st += f'----------------------------------------------------------------------\n'

        return st


# ---------------------------------------------------------------------------
# Main Calculation Helper Functions
# ---------------------------------------------------------------------------

def extract_range_param(obj):
    """
    takes a TypMinMax object from the ecdtools and returns a numpy array organised as [Typ, Min, Max]
    """
    try:
        typ = obj.typical
        minimum = obj.minimum
        maximum = obj.maximum
        arr = np.asarray([typ, minimum, maximum])

        # Only convert to float if value is not None
        for i, val in enumerate(arr):
            if val is not None:
                arr[i] = float(val)

        # Check if all values within arr are None
        if (arr[0] is None) and (arr[1] is None) and (arr[2] is None):
            arr = None

    except:
        arr = None

    return arr


def extract_iv_table(iv_data):
    """
    returns a IV numpy array of the ecdtools object model-iv data
    """
    arr = None
    if iv_data is not None:
        arr = np.asarray(iv_data, dtype='float64')

    return arr


def get_ibis_model_ecdtools(ibis_filename):
    """
    returns the ibis object from the ecdtools library
    """
    ibis = ecdtools.ibis.load_file(ibis_filename, transform=True)
    return ibis


def list_components(ibis_model_ecdtools):
    """
    returns a list of all the components within the ibis file
    """
    return ibis_model_ecdtools.component_names


def list_models(ibis_data_model):
    """
    returns a list of all the models within the ibis file
    """
    return ibis_data_model.model_names


def adjust_device_data(iv_device, iv_clamp):
    """
    The pullup and pulldown data in the IBIS model is captured with clamps still present.
    This function can adjust the device data using the clamp data.

        Parameters:
            iv_device: pull-up or pull-down device iv table
            iv_clamp: power-clamp or ground clamp iv table

        Returns:
            iv_adj: The adjusted iv table
    """
    array_size = np.shape(iv_device[:, 0])[0]  # Get size of the table data
    iv_adj = np.zeros([array_size, 4])
    # populate the first column of the new adjusted table with the voltage in the device table
    iv_adj[:, 0] = iv_device[:, 0]

    # Subtract the clamp data for the typical(1), minimum(2) and maximum(3).
    # The clamp data and device data may not be lined up in the voltage axis
    # so the subtraction should be handled with an interpolation
    iv_adj[:, 1] = iv_device[:, 1] - np.interp(iv_adj[:, 0], iv_clamp[:, 0], iv_clamp[:, 1])
    iv_adj[:, 2] = iv_device[:, 2] - np.interp(iv_adj[:, 0], iv_clamp[:, 0], iv_clamp[:, 2])
    iv_adj[:, 3] = iv_device[:, 3] - np.interp(iv_adj[:, 0], iv_clamp[:, 0], iv_clamp[:, 3])

    return iv_adj


def increasing(arr):
    """
    returns True if arr is increasing with equal values allowed. Otherwise returns False
    """
    return all(x <= y for x, y in zip(arr, arr[1:]))


def get_current_data_from_iv_data(voltage, iv_data, vcc_ref, corner, iv_data_adjust=None):
    """
    Generates an array of current values that interpolate the iv_data from the voltage array given.
    If parameter iv_data_adjust is provided, then the returned array will provide an adjusted iv_data array.
    adj_array = iv_data - iv_data_adjust.
    This is useful for the pullup/pulldown devices, which need to be adjusted with the power/ground clamp currents.
    The returned current array is given as zero values if the IV_data parameter has value of "None"

    Parameters:
        voltage: a numpy array of voltage values
        iv_data: numpy array in the form [voltage, I_typ, I_min, I_max]
        vcc_ref: defines the reference voltage for the iv_data
        corner: value of either 1, 2 or 3 to signify the typical , slow-weak (min) and fast-strong (max) corners
        iv_data_adjust: numpy array in the form [voltage, I_typ, I_min, I_max]

    Returns:
        i_arr: A current array interpolated from the given voltage array and adjusted if necessary
    """

    # Define some constants to help with readability. This represents the column indexes for the relevant data
    _VOLTAGE = 0

    # Check if iv_data is valid parameter, otherwise provide a zero-valued array
    if iv_data is not None:

        if iv_data_adjust is not None:
            iv_data = adjust_device_data(iv_data, iv_data_adjust)

        # If reference is not zero, then make the values ground referenced. 
        if vcc_ref != 0:
            iv_data_ref = vcc_ref - iv_data[:, _VOLTAGE]

            # The interpolation function requires the x values to be monotonically increasing
            if increasing(iv_data_ref) is False:
                i_arr = np.interp(voltage, np.flip(iv_data_ref), np.flip(iv_data[:, corner]))
            else:
                i_arr = np.interp(voltage, iv_data_ref, iv_data[:, corner])

        else:
            i_arr = np.interp(voltage, iv_data[:, _VOLTAGE], iv_data[:, corner])

    else:
        i_arr = np.zeros(np.shape(voltage)[0])  # zero-valued array

    return i_arr


def get_reference(ref, v_range, corner):
    """
    Returns ref if it is not None, otherwise returns v_range
    """
    if ref is None:
        if isinstance(v_range, int):
            value = v_range
        else:
            value = v_range[corner-1]
    else:
        value = ref[corner-1]

    return value


def generating_current_data(ibis_data, time, corner, waveform_obj):
    """
    Generates the current waveforms for the devices and clamps with respect to the given time array

    Parameters:
        ibis_data: a DataModel object
        time: a numpy array of time values
        corner: value of either 1, 2 or 3 to signify the typical , slow-weak (min) and fast-strong (max) corners
        waveform_obj: the relevant Waveform object

    Returns:
        tuple of values (i_pu, i_pd, i_pc, i_gc, i_out, i_c_comp)
        each value is a numpy array of a current with respect to the given time array
            i_pu - pullup device current
            i_pd - pulldown device current
            i_pc - power clamp device current
            i_gc - ground clamp device current
            i_rfix - current through the r_fix
            i_c_comp - current through the die-capacitance (c_comp)
    """

    # Define some constants to help with readability. This represents the column indexes for the relevant data
    _TIME = 0

    # Get the voltage waveform corresponding to the given time array
    vt = np.interp(time, waveform_obj.data[:, _TIME], waveform_obj.data[:, corner])

    pullup_ref = get_reference(ibis_data.pullup_ref, ibis_data.v_range, corner)
    pulldown_ref = get_reference(ibis_data.pulldown_ref, 0, corner)
    pwr_clamp_ref = get_reference(ibis_data.pwr_clamp_ref, ibis_data.v_range, corner)
    gnd_clamp_ref = get_reference(ibis_data.gnd_clamp_ref, 0, corner)

    # Pullup and pulldown device current
    i_pu = get_current_data_from_iv_data(vt, ibis_data.iv_pullup, pullup_ref, corner,
                                         iv_data_adjust=ibis_data.iv_pwr_clamp)
    i_pd = get_current_data_from_iv_data(vt, ibis_data.iv_pulldown, pulldown_ref, corner,
                                         iv_data_adjust=ibis_data.iv_gnd_clamp)

    # Power and ground clamp current
    i_pc = get_current_data_from_iv_data(vt, ibis_data.iv_pwr_clamp, pwr_clamp_ref, corner, iv_data_adjust=None)
    i_gc = get_current_data_from_iv_data(vt, ibis_data.iv_gnd_clamp, gnd_clamp_ref, corner, iv_data_adjust=None)

    # Current through r_fixture
    i_rfix = (waveform_obj.v_fix[corner - 1] - vt) / waveform_obj.r_fix

    # Current through the die capacitance (c_comp) --> i_c_comp = c_comp * dvt/dt
    i_c_comp = ibis_data.c_comp[corner - 1] * differentiate(vt, time)

    return i_pu, i_pd, i_pc, i_gc, i_rfix, i_c_comp


def solve_k_params_output(ibis_data, corner=1, waveform_type="Rising"):
    """
    Solves the k-parameters for the ibis model for any 2 or 3-state output buffer

        Parameters:
            ibis_data: a DataModel object
            corner: value of either 1, 2 or 3 to signify the typical , slow-weak (min) and fast-strong (max) corners
            waveform_type: Either "Rising" or "Falling" to select the waveform to solve the k-parameters for

        Returns:
            k_param: numpy array with 3 columns [time, k_u, k_d]
    """
    # Input 
    if waveform_type == "Rising":
        waveform1 = ibis_data.vt_rising[0]
        waveform2 = ibis_data.vt_rising[1]
    elif waveform_type == "Falling":
        waveform1 = ibis_data.vt_falling[0]
        waveform2 = ibis_data.vt_falling[1]
    else:
        sys.exit(f"Error in waveform_type parameter. Expected 'Rising' or 'Falling', got {waveform_type}")

    # Combine the time samples to obtain a single time-series for both waveforms 1 and 2
    time = np.concatenate((waveform1.data[:, 0], waveform2.data[:, 0]))

    # Sort the time samples to be monotonic and remove any duplicate time samples
    time = np.sort(time)
    time = np.unique(time)
    array_size = np.shape(time)[0]

    # Getting the device and clamp current waveforms based on the new time series
    (i_pu1, i_pd1, i_pc1, i_gc1, i_rfix1, i_c_comp1) = generating_current_data(ibis_data, time, corner, waveform1)
    (i_pu2, i_pd2, i_pc2, i_gc2, i_rfix2, i_c_comp2) = generating_current_data(ibis_data, time, corner, waveform2)

    # creating a k-parameters array with columns [time, k_u, k_d]
    k_param = np.zeros([array_size, 3])
    k_param[:, 0] = time

    # Rearrange equation and solve for k_u and kd parameters
    i1 = i_gc1 + i_pc1 + i_rfix1 - i_c_comp1
    i2 = i_gc2 + i_pc2 + i_rfix2 - i_c_comp2

    for n in range(0, array_size):
        a = np.array([[i_pu1[n], i_pd1[n]], [i_pu2[n], i_pd2[n]]])
        b = np.array([i1[n], i2[n]])
        x = np.linalg.solve(a, b)
        k_param[:, 1][n] = x[0]  # k_u
        k_param[:, 2][n] = x[1]  # k_d

    return k_param


#TODO add function to solve k_param for open-drain type models

def differentiate(y, x):
    """
    Performs a piecewise derivative of y with respect to x

        Parameters:
            y: numpy array
            x: numpy array

        Returns:
            dy_dx: The piecewise derivative returned as a numpy array
    """
    dy = np.diff(y)
    dx = np.diff(x)
    dy_dx = np.divide(dy, dx)
    dy_dx = np.append(dy_dx, dy_dx[-1])  # returned array is made to equal the same length as original x and y arrays

    return dy_dx


def compress_param(k_param, threshold=1e-6):
    """
    Compresses the k_parameter waveform by removing redundant samples
    Remove any samples that do not change in value between subsequent samples by more than the given threshold

        Parameters:
            k_param: numpy array - 2 or 3 columns: [time, Ku, Kd] or [time, K]
            threshold: threshold value to decide if sample is redundant

        Returns:
            k_comp: The compressed waveform
    """
    k_comp = None
    num_rows = np.shape(k_param)[0]
    num_columns = np.shape(k_param)[1]

    # Differentiate the ku and kd waveforms with respect to time
    diff_k = np.zeros([num_rows, num_columns])
    diff_k[:, 0] = k_param[:, 0]  # column 0 is the time

    for i in range(1, num_columns):
        diff_k[:, i] = np.absolute(np.diff(np.append(k_param[:, i], k_param[:, i][-1])))

    if num_columns == 3:  # There are two k parameters, Ku and Kd
        # Extract samples that have very small differences between time samples
        c1 = (diff_k[:, 1] <= threshold)
        c2 = (diff_k[:, 2] <= threshold)
        condition = np.logical_not(np.logical_and(c1, c2))

        k_comp = np.extract(condition, k_param[:, 0])
        k_comp = np.column_stack((k_comp, np.extract(condition, k_param[:, 1])))
        k_comp = np.column_stack((k_comp, np.extract(condition, k_param[:, 2])))

    if num_columns == 2:  # There is only a single k-parameter as it is an open-drain type output
        condition = (diff_k[:, 1] <= threshold)
        k_comp = np.extract(condition, k_param[:, 0])
        k_comp = np.column_stack((k_comp, np.extract(condition, k_param[:, 1])))

    return k_comp


# ---------------------------------------------------------------------------
# Plot Helper Functions 
# ---------------------------------------------------------------------------

def plot_iv_data_single(data, title):
    """
    Plots the data in a single figure

    Parameters:
        data: numpy array with data organised as [x-data, y-data_1, y-data_2..., y-data_n]
        title: Plot title
    """
    fig = plot_single(data,
                      data_labels=['Typ', 'Min', 'Max'],
                      xlabel='Voltage (V)',
                      ylabel='Current (A)',
                      title=title)

    return fig


def plot_iv_device_data(ibis_data):
    """
    takes the ibis_data DataModel object and plots the iv device data in 2 graphs laid out horizontally.
    left graph - Pull up device IV curve. right graph - Pull down device IV curve
    """

    # Check that the both pullup and pulldown data is available before plotting
    fig = plot_dual(ibis_data.iv_pullup,
                    ibis_data.iv_pulldown,
                    data_labels=['Typ', 'Min', 'Max'],
                    xlabel='Voltage (V)',
                    ylabel='Current (A)',
                    title1='Pullup IV',
                    title2='Pulldown IV')
    return fig


def plot_iv_clamp_data(ibis_data):
    """
    takes the ibis_data DataModel object and plots the clamp data in 2 graphs laid out horizontally
    left graph - Power Clamp IV curve. right graph - Ground Clamp IV curve
    """
    fig = plot_dual(ibis_data.iv_pwr_clamp,
                    ibis_data.iv_gnd_clamp,
                    data_labels=['Typ', 'Min', 'Max'],
                    xlabel='Voltage (V)',
                    ylabel='Current (A)',
                    title1='Power Clamp IV',
                    title2='Ground Clamp IV')
    return fig


def generate_vt_plot_title(waveform_type_str, waveform_obj):
    """
    helper function to generate a comprehensive plot title for the VT waveforms.

    Parameters:
        waveform_type_str - text to signify the waveform type i.e. "Rising Edge" or "Falling Edge"
        waveform_obj - Waveform object

    Returns:
        title_str - A comprehensive title string that can be use in the plot titles.

    """
    title_str = f'{waveform_type_str}\n'
    title_str += f'R_fixture={waveform_obj.r_fix}\n'
    title_str += f'V_fixture typ={waveform_obj.v_fix[0]}\n'
    title_str += f'V_fixture min={waveform_obj.v_fix[1]}\n'
    title_str += f'V_fixture max={waveform_obj.v_fix[2]}'

    return title_str


def plot_vt_rising_waveform_data(ibis_data):
    """
    takes the ibis_data DataModel object and plots the rising waveform data in 2 graphs laid out horizontally
    left graph - Rising Waveform 1. right graph - Rising Waveform 2
    """
    if ibis_data.vt_rising:  # Check that rising waveform data is available
        title1 = generate_vt_plot_title("Rising Waveform", ibis_data.vt_rising[0])
        title2 = generate_vt_plot_title("Rising Waveform", ibis_data.vt_rising[1])
        fig = plot_dual(ibis_data.vt_rising[0].data,
                        ibis_data.vt_rising[1].data,
                        data_labels=['Typ', 'Min', 'Max'],
                        xlabel='Time (s)',
                        ylabel='Voltage (V)',
                        title1=title1,
                        title2=title2)
        return fig


def plot_vt_falling_waveform_data(ibis_data):
    """
    takes the ibis_data DataModel object and plots the falling waveform data in 2 graphs laid out horizontally
    left graph - Rising Waveform 1. right graph - Rising Waveform 2
    """
    if ibis_data.vt_falling:  # Check that falling waveform data is available
        title1 = generate_vt_plot_title("Falling Waveform", ibis_data.vt_falling[0])
        title2 = generate_vt_plot_title("Falling Waveform", ibis_data.vt_falling[1])
        fig = plot_dual(ibis_data.vt_falling[0].data,
                        ibis_data.vt_falling[1].data,
                        data_labels=['Typ', 'Min', 'Max'],
                        xlabel='Time (s)',
                        ylabel='Voltage (V)',
                        title1=title1,
                        title2=title2)
        return fig


def plot_all_ibis_data(ibis_data):
    """
    plots all the ibis data in sequence - IV device data, IV clamp data, Rising Waveforms, Falling Waveforms.
    """
    plot_iv_device_data(ibis_data)
    plot_iv_clamp_data(ibis_data)
    plot_vt_rising_waveform_data(ibis_data)
    plot_vt_falling_waveform_data(ibis_data)


def plot_dual(data1, data2, data_labels, xlabel, ylabel, title1, title2):
    """
    Plots 2 graphs laid out horizontally with given input data (Graph 1 - Left, Graph 2 - Right)

        Parameters:
            data1 - numpy array with data organised as [x-data, y-data_1, y-data_2..., y-data_n]. Plots on Graph 1
            data2 - numpy array with data organised as [x-data, y-data_1, y-data_2..., y-data_n]. Plots on Graph 2
            data_labels - assigns a name to each line on the graph
            x_label - x-axis label
            y_label - y-axis label
            title1 - title of graph 1
            title1 - title of graph 2

    """
    fig, (ax1, ax2) = plt.subplots(1, 2)

    if data1 is not None:
        num_columns = np.shape(data1)[1]
        for i in range(1, num_columns):
            # Remove nan's before plotting
            nan = np.isnan(data1[:, i])
            not_nan = ~nan
            x = data1[:, 0][not_nan]
            y = data1[:, i][not_nan]

            ax1.plot(x, y, label=data_labels[i - 1])

        ax1.legend()
        ax1.grid(color='0.9')
        ax1.set_xlim(data1[:, 0][0], data1[:, 0][-1])

    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel)
    ax1.set_title(title1)

    if data2 is not None:
        num_columns = np.shape(data2)[1]
        for i in range(1, num_columns):
            # Remove nan's before plotting
            nan = np.isnan(data2[:, i])
            not_nan = ~nan
            x = data2[:, 0][not_nan]
            y = data2[:, i][not_nan]

            ax2.plot(x, y, label=data_labels[i - 1])

        ax2.legend()
        ax2.grid(color='0.9')
        ax2.set_xlim(data2[:, 0][0], data2[:, 0][-1])

    ax2.set_xlabel(xlabel)
    ax2.set_ylabel(ylabel)
    ax2.set_title(title2)

    fig.tight_layout(w_pad=5, h_pad=2)

    return fig


def plot_single(data, data_labels, xlabel, ylabel, title):
    """
    Plots a graph with given input data

        Parameters:
            data - numpy array with data organised as [x-data, y-data_1, y-data_2..., y-data_n].
            data_labels - assigns a name to each line on the graph
            x_label - x-axis label
            y_label - y-axis label
            title - title of graph
    """

    fig, ax1 = plt.subplots()

    if data is not None:
        num_columns = np.shape(data)[1]
        for i in range(1, num_columns):

            # Remove nan's before plotting
            nan = np.isnan(data[:, i])
            not_nan = ~nan
            x = data[:, 0][not_nan]
            y = data[:, i][not_nan]

            ax1.plot(x, y, label=data_labels[i - 1])

        ax1.legend()
        ax1.grid(color='0.9')
        ax1.set_xlim(data[:, 0][0], data[:, 0][-1])

    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel)
    ax1.set_title(title)

    return fig


# ---------------------------------------------------------------------------
# Functions to assist with subcircuit creation
# ---------------------------------------------------------------------------

def convert_iv_table_to_str(voltage, current):
    """
    Creates the IV table of values for the current sources modelling the devices and clamps

        Parameters:
            voltage - numpy time array for k_r waveform
            current - numpy time array for k_f waveform

        Returns:
            str_val: the string that goes into subcircuit table
    """
    str_val = f'{voltage[0]}, {current[0]}'
    for i in range(1, len(voltage)):
        str_val = str_val + f', {voltage[i]}, {current[i]}'
    return str_val


def create_edge_waveform_pwl(time, k_param):
    """
    Creates the PWM value string for the oscillation waveform

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
    returns the approx. crossover offsets between the k_param waveforms
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
