# ----------------------------------------------------------------------------
# Author: Kishan Amratia
# Module Name: plot.py
#
# Module Description:
# Companion functions for the pybis2spice module to provide plotting functionality
#
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import numpy as np
import matplotlib.pyplot as plt


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
