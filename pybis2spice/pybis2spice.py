# ----------------------------------------------------------------------------
# Author: Kishan Amratia
# Module Name: pybis2spice.py
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
            self.file_name = ibis.file_name
            self.model = ibis.get_model_by_name(model_name)
            self.component = ibis.get_component_by_name(component_name)
            self.model_type = self.model.model_type

            self.r_pkg = extract_range_param(self.component.package.r_pkg)
            self.l_pkg = extract_range_param(self.component.package.l_pkg)
            self.c_pkg = extract_range_param(self.component.package.c_pkg)
            self.c_comp = extract_range_param(self.model.c_comp)
            self.v_range = extract_range_param(self.model.voltage_range)
            self.temp_range = extract_range_param(self.model.temperature_range)
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
        st += f'temp_range: {self.temp_range}\n'
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


def solve_k_params_output_open_drain(ibis_data, corner=1, waveform_type="Rising"):
    """
    Solves the k-parameters for the ibis model for any 2 or 3-state output buffer

        Parameters:
            ibis_data: a DataModel object
            corner: value of either 1, 2 or 3 to signify the typical , slow-weak (min) and fast-strong (max) corners
            waveform_type: Either "Rising" or "Falling" to select the waveform to solve the k-parameters for

        Returns:
            k_param: numpy array with 2 columns [time, k_d]
    """
    # Input
    if waveform_type == "Rising":
        waveform1 = ibis_data.vt_rising[0]
    elif waveform_type == "Falling":
        waveform1 = ibis_data.vt_falling[0]
    else:
        sys.exit(f"Error in waveform_type parameter. Expected 'Rising' or 'Falling', got {waveform_type}")

    # Get only unique samples for time array
    time = np.unique(waveform1.data[:, 0])
    array_size = np.shape(time)[0]

    # Getting the device and clamp current waveforms based on the new time series
    (i_pu1, i_pd1, i_pc1, i_gc1, i_rfix1, i_c_comp1) = generating_current_data(ibis_data, time, corner, waveform1)

    # creating a k-parameters array with columns [time, k_d]
    k_param = np.zeros([array_size, 2])
    k_param[:, 0] = time

    # Rearrange equation and solve for k_u and kd parameters
    i1 = i_gc1 + i_pc1 + i_rfix1 - i_c_comp1
    k_param[:, 1] = np.divide(i1, i_pd1)

    return k_param


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
