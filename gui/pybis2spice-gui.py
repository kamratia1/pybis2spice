# ---------------------------------------------------------------------------
# Author: Kishan Amratia
# Date: 02-Jan-2022
# Module Name: pybis2spice-gui.py
"""
A tkinter GUI for helping users to convert IBIS models into SPICE models
"""
# ---------------------------------------------------------------------------
import matplotlib.pyplot as plt

from pybis2spice import pybis2spice
from pybis2spice import plot
from pybis2spice import version
from pybis2spice import subcircuit
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tktooltip import ToolTip
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import time
import logging
import webbrowser
import urllib.request
import img
import re
import os

_width = 740
_height = 480
logging.basicConfig(level=logging.INFO)
ibis_model = None  # The ecdtools ibis_model object


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def check_latest_version():
    latest_version = version.get_version()

    url = "https://raw.githubusercontent.com/kamratia1/pybis2spice/main/pybis2spice/version.txt"
    try:
        version_source = urllib.request.urlopen(url)
        latest_version = version_source.read()
    except:
        pass

    return latest_version


def check_supported_model_type(ibis_data):
    # Check that model type is supported by this tool
    # Check if model_type is supported
    model_type = ""
    try:
        model_type = ibis_data.model_type
    except:
        pass

    supported = False
    supported_model_types_list = ["input", "output", "i/o", "3-state", "open_drain", "i/o_open_drain"]
    for item in supported_model_types_list:
        if item == model_type.lower():
            supported = True

    return supported


def validate_type(ibis_data, io_type):
    # Check that io type selected matches the model_type
    # Returns True if it passes validation

    model_type = ""
    try:
        model_type = ibis_data.model_type
    except:
        pass

    supported = check_supported_model_type(ibis_data)
    if not supported:
        message = f"Model type \"{ibis_data.model_type}\" not supported."
        messagebox.showwarning(title="Model type not supported", message=message)
        logging.error(message)

    io_validate = False
    model_types_list = ["input", "i/o", "i/o_open_drain"]
    if io_type == "Input":
        for item in model_types_list:
            if item == model_type.lower():
                io_validate = True

    model_types_list = ["output", "i/o", "3-state", "open_drain", "i/o_open_drain"]
    if io_type == "Output":
        for item in model_types_list:
            if item == model_type.lower():
                io_validate = True

    if supported and not io_validate:
        message = f"I/O Select is invalid with IBIS model type.\n"
        message += f"Selected Model Type: {ibis_data.model_type}\n"
        if io_type == "Input":
            message += "Please select the Output I/O type"
        elif io_type == "Output":
            message += "Please select the Input I/O type"

        messagebox.showwarning(title="I/O mismatch", message=message)
        logging.error(message)

    ret_val = supported and io_validate
    return ret_val


# ---------------------------------------------------------------------------
# Callback Functions from Buttons or other actions
# ---------------------------------------------------------------------------
def help_url_callback(url):
    webbrowser.open_new(url)


def help_message_callback():
    help_window = tk.Toplevel(main_window)
    help_window.title(f" Help")
    help_window.minsize(550, 350)
    help_window.resizable(False, False)
    help_window.grab_set()
    help_window.geometry(f"+{main_window.winfo_rootx() + 50}+{main_window.winfo_rooty() + 50}")
    help_window.iconphoto(False, _icon_img)

    message1 = f"\n\nIBIS to SPICE Converter\n" \
               f"Version: {version.get_version()}\n" \
               f"Release Date: {version.get_date()}\n\n\n" \
               f"Please report any bugs and issues at the link below.\n" \
               f"Detailed information on how the issue can be reproduced should be provided including \n" \
               f"any IBIS files used and version number of this program."

    url1 = "https://github.com/kamratia1/pybis2spice/issues/"
    lbl_message1 = tk.Label(help_window, text=f"{message1}")
    link1 = tk.Label(help_window, text=url1, fg='#0000EE')
    link1.bind("<Button-1>", lambda e: help_url_callback(url1))

    message2 = "Help on how to use this tool can be found within the README at "
    url2 = "https://github.com/kamratia1/pybis2spice/"
    lbl_message2 = tk.Label(help_window, text=f"\n\n{message2}")
    link2 = tk.Label(help_window, text=url2, fg='#0000EE')
    link2.bind("<Button-1>", lambda e: help_url_callback(url2))

    lbl_message1.pack(side=tk.TOP)
    link1.pack(side=tk.TOP)
    lbl_message2.pack(side=tk.TOP)
    link2.pack(side=tk.TOP)

    latest_version = check_latest_version()
    latest_version_float = float(latest_version)
    current_version_float = float(version.get_version())

    if latest_version_float > current_version_float:
        url3 = "https://github.com/kamratia1/pybis2spice/"
        message3 = f"Version {latest_version} available to download from"
        lbl_message3 = tk.Label(help_window, text=f"\n\n{message3}", font='Helvetica 12 bold')
        link3 = tk.Label(help_window, text=url3, fg='#0000EE')
        link3.bind("<Button-1>", lambda e: help_url_callback(url2))
        lbl_message3.pack(side=tk.TOP)
        link3.pack(side=tk.TOP)


def create_subcircuit_file_callback():
    ibis_file_path = entry.get()
    component_name = list_component.get(tk.ACTIVE)
    model_name = list_model.get(tk.ACTIVE)
    io_type = radio_var3.get()
    subcircuit_type = radio_var1.get()  # LTSpice or Generic
    corner = radio_var2.get()

    main_window.config(cursor="wait")
    global ibis_model
    ibis_data = pybis2spice.DataModel(ibis_model, model_name, component_name)
    main_window.update()
    time.sleep(0.01)
    main_window.config(cursor="")

    logging.info("Creating subcircuit file button pressed")

    if not(hasattr(ibis_data, 'model')):  # Check that model has been selected
        logging.error("No model Selected. Please select a valid IBIS file and model")
        messagebox.showwarning(title="No model Selected", message="Please select a valid IBIS file and model")
    else:
        if validate_type(ibis_data, io_type):
            logging.info(f"IBIS File: {ibis_file_path}")
            logging.info(f"Component Selected: {component_name}")
            logging.info(f"Model Selected: {model_name}")
            logging.info(f"Subcircuit Type: {subcircuit_type}")
            logging.info(f"Corner: {corner}")
            logging.info(f"I/O Select: {io_type}")
            create_subcircuit_file(ibis_data, subcircuit_type, corner, io_type)


def get_warnings_from_file(filepaths):
    # Check file for any "WARNINGS and add to the warnings string"
    # Filepaths is a list of file paths
    warnings = ""
    pattern = re.compile("WARNING")
    for _file in filepaths:
        for line in open(_file):
            for _ in re.finditer(pattern, line):
                warnings += line

    return warnings


def create_subcircuit_file(ibis_data, subcircuit_type, corner, io_type):

    if corner == "All":
        file = filedialog.askdirectory(parent=main_window)
    else:
        filename = f'{ibis_data.model_name}-{io_type}-{corner}.sub'
        file = filedialog.asksaveasfile(parent=main_window,
                                        title='Choose a file',
                                        filetypes=[("Subcircuit Files", ".sub")],
                                        initialfile=f"{filename}")

    # If file/directory was chosen by user
    if file:
        if corner == "All":
            logging.info(f"Chosen Directory: {file}")

            corners = ["WeakSlow", "Typical", "FastStrong"]
            filepaths = []
            generate_model_status = 0
            for _corner in corners:
                filename = f'{ibis_data.model_name}-{io_type}-{_corner}.sub'
                filepath = os.path.join(file, filename)
                filepaths.append(filepath)
                logging.info(f"Creating subcircuit for {_corner} corner at {filepath}")
                ret_val = subcircuit.generate_spice_model(io_type=io_type,
                                                          subcircuit_type=subcircuit_type,
                                                          ibis_data=ibis_data,
                                                          corner=_corner,
                                                          output_filepath=filepath)
                generate_model_status += ret_val

            if generate_model_status == 0:
                message_success = f"SPICE subcircuit models successfully created at:\n{file}"

                # Create symbol
                if subcircuit_type == "LTSpice":
                    symbol_file1 = subcircuit.create_ltspice_symbol(ibis_data, "WeakSlow", filepaths[0], io_type)
                    symbol_file2 = subcircuit.create_ltspice_symbol(ibis_data, "Typical", filepaths[1], io_type)
                    symbol_file3 = subcircuit.create_ltspice_symbol(ibis_data, "FastStrong", filepaths[2], io_type)

                    logging.info(f"LTSpice Symbol created at: {symbol_file1}")
                    logging.info(f"LTSpice Symbol created at: {symbol_file2}")
                    logging.info(f"LTSpice Symbol created at: {symbol_file3}")
                    message_success += f"\n\nLTSpice symbols also created successfully at:\n{file}\n"

                warnings = get_warnings_from_file(filepaths)
                if warnings != "":
                    message_success += f"\n\nWARNINGS within the SPICE subcircuit file: \n"
                    message_success += f"{warnings}"

                messagebox.showinfo(title="Success", message=message_success)
                logging.info(message_success)
            else:
                message_error = f"SPICE subcircuit model generation failed."
                messagebox.showerror(title="Failed to create model", message=message_error)
                logging.error(message_error)

        else:  # If a specific corner was chosen
            logging.info(f"Chosen File: {file.name}")
            # Create the subcircuit file
            generate_model_status = subcircuit.generate_spice_model(io_type=io_type,
                                                                    subcircuit_type=subcircuit_type,
                                                                    ibis_data=ibis_data,
                                                                    corner=corner,
                                                                    output_filepath=file.name)
            if generate_model_status == 0:
                message_success = f"SPICE subcircuit model successfully created at:\n{file.name}"

                # Create symbol
                if subcircuit_type == "LTSpice":
                    symbol_file = subcircuit.create_ltspice_symbol(ibis_data, corner, file.name, io_type)
                    logging.info(f"LTSpice Symbol created at: {symbol_file}")
                    message_success += f"\n\nLTSpice symbol also created successfully at:\n{symbol_file}\n"

                warnings = get_warnings_from_file([file.name])
                if warnings != "":
                    message_success += f"\n\nWARNINGS within the SPICE subcircuit file: \n"
                    message_success += f"{warnings}"

                messagebox.showinfo(title="Success", message=message_success)
                logging.info(message_success)

            else:
                message_error = f"SPICE subcircuit model generation failed."
                messagebox.showerror(title="Failed to create model", message=message_error)
                logging.error(message_error)


def browse_ibis_file_callback():

    logging.info("Browse button pressed")

    file = filedialog.askopenfile(parent=main_window,
                                  title='Choose a file',
                                  filetypes=[("IBIS files", ".ibs"), ("All files", "*")])

    if file:
        ibis_filepath = file.name

        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, ibis_filepath)
        entry.config(state='disabled')

        main_window.config(cursor="")
        time.sleep(0.1)

        list_component.delete(0, tk.END)
        list_model.delete(0, tk.END)

        global ibis_model
        ibis_model = pybis2spice.get_ibis_model_ecdtools(ibis_filepath)
        logging.info(f"Parsing ibis file from {ibis_filepath}")

        component_names = pybis2spice.list_components(ibis_model)
        for index, component in enumerate(component_names, start=1):
            list_component.insert(index, component)

        model_names = pybis2spice.list_models(ibis_model)
        for index, model in enumerate(model_names, start=1):
            list_model.insert(index, model)

        # Set default selection to first item
        list_component.select_set(0)
        list_model.select_set(0)
        list_component.event_generate("<<ListboxSelect>>")
        list_model.event_generate("<<ListboxSelect>>")

        main_window.update()
        main_window.config(cursor="")


def check_model_callback():
    plt.close("all")  # close any previous matplotlib figures to avoid consuming excess memory
    component_name = list_component.get(tk.ACTIVE)
    model_name = list_model.get(tk.ACTIVE)
    logging.info(f"Check Model button pressed - {component_name} - {model_name}")

    main_window.config(cursor="wait")

    global ibis_model
    ibis_data = pybis2spice.DataModel(ibis_model, model_name, component_name)

    main_window.update()
    time.sleep(0.1)
    main_window.config(cursor="")

    if hasattr(ibis_data, 'model'):
        check_model_window(ibis_data)
    else:
        messagebox.showinfo(title="No model Selected", message="Please select a valid IBIS file and model")
        logging.error("No model Selected. Please select a valid IBIS file and model")


# ---------------------------------------------------------------------------
# Check Model Window
# ---------------------------------------------------------------------------

def check_model_window(ibis_data):
    data_window = tk.Toplevel(main_window)
    data_window.geometry(f"+{main_window.winfo_rootx() + 50}+{main_window.winfo_rooty() + 50}")
    data_window.title(f"Check IBIS Model - {ibis_data.model_name}")
    data_window.minsize(700, 700)
    data_window.grab_set()
    data_window.iconphoto(False, _icon_img)
    data_window.resizable(False, False)

    tab_parent = ttk.Notebook(data_window)

    # Summary Tab
    tab1 = ttk.Frame(tab_parent)
    tab_parent.add(tab1, text="Summary")

    model_summary_table = create_model_summary_table(ibis_data, tab1)
    model_parameter_table = create_model_parameters_table(ibis_data, tab1)

    tab0_lbl0 = tk.Label(tab1, text="\nIBIS Model Parameters")
    tab0_lbl0.pack()  # Heading for the Tables
    model_summary_table.pack()  # Add the Model Summary Table
    tk.Label(tab1, text="\n").pack()  # Empty Line
    model_parameter_table.pack()  # Add the Model Parameter Table
    tk.Label(tab1, text="\n").pack()  # Empty Line

    supported = check_supported_model_type(ibis_data)
    if supported:
        circuit_canvas = tk.Canvas(tab1, bg='white', height=220, width=650)
        create_circuit_image(ibis_data, circuit_canvas, tab1)
        circuit_canvas.pack()
    else:
        tab0_lbl1 = tk.Label(tab1, bg="red", text=f"Model Type \"{ibis_data.model_type}\" is invalid or currently unsupported")
        tab0_lbl1.pack()

    # Adding markers on graphs in check model window
    marker_state = marker_var.get()
    if marker_state == 1:
        marker = "."
    else:
        marker = ""

    # Pullup Tab
    if ibis_data.iv_pullup is not None:
        fig1 = plot.plot_iv_data_single(ibis_data.iv_pullup, "Pullup device IV data", marker=marker)
        device_lbl = "\n1. Device configured to switch on pullup transistor.\n" \
                     "2. Current through pin is measured while voltage source is swept from (-VCC) to (2 x VCC)"
        add_check_window_plot_tab(ibis_data, tab_parent, fig1, "Pullup", tab_text=device_lbl)

    # Pulldown Tab
    if ibis_data.iv_pulldown is not None:
        fig2 = plot.plot_iv_data_single(ibis_data.iv_pulldown, "Pulldown device IV data", marker=marker)
        device_lbl = "\n1. Device configured to switch on pulldown transistor.\n" \
                     "2. Current through pin is measured while voltage source is swept from (-VCC) to (2 x VCC)"
        add_check_window_plot_tab(ibis_data, tab_parent, fig2, "Pulldown", tab_text=device_lbl)

    # Power Clamp Tab
    if ibis_data.iv_pwr_clamp is not None:
        fig3 = plot.plot_iv_data_single(ibis_data.iv_pwr_clamp, "Power clamp IV data", marker=marker)
        clamp_lbl = "\n1. Device transistors are switched off.\n" \
                    "2. Current through pin is measured while voltage source is swept from (VCC) to (2 x VCC)"
        add_check_window_plot_tab(ibis_data, tab_parent, fig3, "Power Clamp", tab_text=clamp_lbl)

    # Ground Clamp Tab
    if ibis_data.iv_gnd_clamp is not None:
        fig4 = plot.plot_iv_data_single(ibis_data.iv_gnd_clamp, "Ground clamp IV data", marker=marker)
        clamp_lbl = "\n1. Device transistors are switched off.\n" \
                    "2. Current through pin is measured while voltage source is swept from (-VCC) to (VCC)"
        add_check_window_plot_tab(ibis_data, tab_parent, fig4, "Ground Clamp", tab_text=clamp_lbl)

    # Rising Waveform Tab
    if ibis_data.vt_rising:
        fig5 = plot.plot_vt_rising_waveform_data(ibis_data, marker=marker)
        plt.subplots_adjust(top=0.86, wspace=0.3)
        rising_waveform_lbl = "\n1. Device transistors configured to switch output from low to high.\n" \
                              "2. Voltage at the pin is measured with respect to time."
        add_check_window_plot_tab(ibis_data, tab_parent, fig5, "Rising Waveforms", tab_text=rising_waveform_lbl)

    # Falling Waveform Tab
    if ibis_data.vt_falling:
        fig6 = plot.plot_vt_falling_waveform_data(ibis_data, marker=marker)
        plt.subplots_adjust(top=0.86, wspace=0.3)
        falling_waveform_lbl = "\n1. Device transistors configured to switch output from high to low.\n" \
                               "2. Voltage at the pin is measured with respect to time."
        add_check_window_plot_tab(ibis_data, tab_parent, fig6, "Falling Waveforms", tab_text=falling_waveform_lbl)

    tab_parent.pack(expand=1, fill=tk.BOTH)


def add_check_window_plot_tab(ibis_data, tab_parent_obj, fig, tab_title, tab_text=""):
    tab = ttk.Frame(tab_parent_obj)
    tab_parent_obj.add(tab, text=tab_title)

    if tab_text != "":
        tab_lbl = tk.Label(tab, text=tab_text)
        tab_lbl.pack()

    setup_circuit_canvas = tk.Canvas(tab, bg='white', height=220, width=450)
    create_circuit_setup_image(ibis_data, tab_title, setup_circuit_canvas, tab)
    setup_circuit_canvas.pack()

    plot_canvas = FigureCanvasTkAgg(fig, master=tab)
    plot_canvas.draw()
    plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    toolbar = NavigationToolbar2Tk(plot_canvas, tab)
    toolbar.update()
    plot_canvas.get_tk_widget().pack()


def create_circuit_setup_image(ibis_data, tab_title, canvas, tab):
    tab.pullup_iv_setup = pullup_iv_setup = tk.PhotoImage(data=img.get_pullup_iv_circuit())
    tab.pulldown_iv_setup = pulldown_iv_setup = tk.PhotoImage(data=img.get_pulldown_iv_circuit())
    tab.vt_fixture = vt_fixture = tk.PhotoImage(data=img.get_vt_fixture())
    tab.pwr_clamp = pwr_clamp = tk.PhotoImage(data=img.get_pwr_clamp())  # 71 x 120 px
    tab.gnd_clamp = gnd_clamp = tk.PhotoImage(data=img.get_gnd_clamp())  # 71 x 120 px
    tab.pullup_device = pullup_device = tk.PhotoImage(data=img.get_pullup_device())  # 68 x 120 px
    tab.pulldown_device = pulldown_device = tk.PhotoImage(data=img.get_pulldown_device())  # 68 x 120 px
    tab.net_segment = net_segment = tk.PhotoImage(data=img.get_net_segment())  # 54 x 12 px

    x_offset = 100
    device_xpos = x_offset
    clamp_xpos = x_offset + 55
    setup_xpos = x_offset + 130
    up_ypos = 0
    down_ypos = 100 + 5
    setup_ypos = 52
    vt_fixture_ypos = 34

    if tab_title == "Pulldown":
        canvas.create_image((device_xpos, down_ypos), image=pulldown_device, anchor='nw')
        canvas.create_image((setup_xpos, setup_ypos), image=pulldown_iv_setup, anchor='nw')
        if ibis_data.iv_pwr_clamp is not None:
            canvas.create_image((clamp_xpos-1, up_ypos), image=pwr_clamp, anchor='nw')
        if ibis_data.iv_gnd_clamp is not None:
            canvas.create_image((clamp_xpos, down_ypos), image=gnd_clamp, anchor='nw')
        canvas.create_image((device_xpos + 33, setup_ypos + 54), image=net_segment, anchor='nw')
        canvas.create_image((clamp_xpos + 25, setup_ypos + 54), image=net_segment, anchor='nw')

    if tab_title == "Pullup":
        canvas.create_image((device_xpos, up_ypos), image=pullup_device, anchor='nw')
        if ibis_data.iv_pwr_clamp is not None:
            canvas.create_image((clamp_xpos-1, up_ypos), image=pwr_clamp, anchor='nw')
        if ibis_data.iv_gnd_clamp is not None:
            canvas.create_image((clamp_xpos, down_ypos), image=gnd_clamp, anchor='nw')
        canvas.create_image((setup_xpos, setup_ypos), image=pullup_iv_setup, anchor='nw')
        canvas.create_image((device_xpos + 33, setup_ypos + 54), image=net_segment, anchor='nw')
        canvas.create_image((clamp_xpos + 25, setup_ypos + 54), image=net_segment, anchor='nw')

    if tab_title == "Power Clamp":
        canvas.create_image((clamp_xpos-1, up_ypos), image=pwr_clamp, anchor='nw')
        if ibis_data.iv_gnd_clamp is not None:
            canvas.create_image((clamp_xpos, down_ypos), image=gnd_clamp, anchor='nw')
        canvas.create_image((setup_xpos, setup_ypos), image=pullup_iv_setup, anchor='nw')
        canvas.create_image((device_xpos + 33, setup_ypos + 54), image=net_segment, anchor='nw')
        canvas.create_image((clamp_xpos + 25, setup_ypos + 54), image=net_segment, anchor='nw')

    if tab_title == "Ground Clamp":
        if ibis_data.iv_pwr_clamp is not None:
            canvas.create_image((clamp_xpos-1, up_ypos), image=pwr_clamp, anchor='nw')
        canvas.create_image((clamp_xpos, down_ypos), image=gnd_clamp, anchor='nw')
        canvas.create_image((setup_xpos, setup_ypos), image=pulldown_iv_setup, anchor='nw')
        canvas.create_image((device_xpos + 33, setup_ypos + 54), image=net_segment, anchor='nw')
        canvas.create_image((clamp_xpos + 25, setup_ypos + 54), image=net_segment, anchor='nw')

    if tab_title == "Rising Waveforms" or tab_title == "Falling Waveforms":
        if ibis_data.iv_pullup is not None:
            canvas.create_image((device_xpos+1, up_ypos), image=pullup_device, anchor='nw')
        if ibis_data.iv_pulldown is not None:
            canvas.create_image((device_xpos, down_ypos), image=pulldown_device, anchor='nw')
        if ibis_data.iv_pwr_clamp is not None:
            canvas.create_image((clamp_xpos-1, up_ypos), image=pwr_clamp, anchor='nw')
        if ibis_data.iv_gnd_clamp is not None:
            canvas.create_image((clamp_xpos, down_ypos), image=gnd_clamp, anchor='nw')
        canvas.create_image((setup_xpos, vt_fixture_ypos), image=vt_fixture, anchor='nw')
        canvas.create_image((device_xpos + 33, setup_ypos + 54), image=net_segment, anchor='nw')
        canvas.create_image((clamp_xpos + 25, setup_ypos + 54), image=net_segment, anchor='nw')


def create_circuit_image(ibis_data, canvas, tab):
    model_type = ibis_data.model_type.lower()

    tab.pwr_clamp = pwr_clamp = tk.PhotoImage(data=img.get_pwr_clamp())  # 71 x 120 px
    tab.gnd_clamp = gnd_clamp = tk.PhotoImage(data=img.get_gnd_clamp())  # 71 x 120 px
    tab.pullup_device = pullup_device = tk.PhotoImage(data=img.get_pullup_device())  # 68 x 120 px
    tab.pulldown_device = pulldown_device = tk.PhotoImage(data=img.get_pulldown_device())  # 68 x 120 px
    tab.net_segment = net_segment = tk.PhotoImage(data=img.get_net_segment())  # 54 x 12 px
    tab.input_img = input_img = tk.PhotoImage(data=img.get_input())  # 297 x 128 px
    tab.output = output = tk.PhotoImage(data=img.get_output())  # 297 x 128 px
    tab.io = io = tk.PhotoImage(data=img.get_io())  # 284 x 130 px

    if model_type == "input":
        x_offset = 100
        canvas.create_image((x_offset, 76), image=input_img, anchor='nw')
        if ibis_data.iv_pwr_clamp is not None:
            canvas.create_image((x_offset + 295, 3), image=pwr_clamp, anchor='nw')
            canvas.create_image((x_offset + 285, 101), image=net_segment, anchor='nw')
        if ibis_data.iv_gnd_clamp is not None:
            canvas.create_image((x_offset + 295, 100), image=gnd_clamp, anchor='nw')
            canvas.create_image((x_offset + 285, 101), image=net_segment, anchor='nw')

    else:
        x_offset = 100
        device_xpos = x_offset + 34
        new_xpos = device_xpos
        if ibis_data.iv_pullup is not None:
            canvas.create_image((x_offset, 0), image=pullup_device, anchor='nw')
            canvas.create_image((device_xpos, 101), image=net_segment, anchor='nw')
            new_xpos = device_xpos + 54
        if ibis_data.iv_pulldown is not None:
            canvas.create_image((x_offset, 100), image=pulldown_device, anchor='nw')
            canvas.create_image((device_xpos, 101), image=net_segment, anchor='nw')
            new_xpos = device_xpos + 54

        clamp_xpos = new_xpos
        if ibis_data.iv_pwr_clamp is not None:
            canvas.create_image((clamp_xpos, 3), image=pwr_clamp, anchor='nw')
            canvas.create_image((clamp_xpos + 30, 101), image=net_segment, anchor='nw')
            canvas.create_image((clamp_xpos - 10, 101), image=net_segment, anchor='nw')
            new_xpos = clamp_xpos + 30 + 54
        if ibis_data.iv_gnd_clamp is not None:
            canvas.create_image((clamp_xpos, 100), image=gnd_clamp, anchor='nw')
            canvas.create_image((clamp_xpos + 30, 101), image=net_segment, anchor='nw')
            canvas.create_image((clamp_xpos - 10, 101), image=net_segment, anchor='nw')
            new_xpos = clamp_xpos + 30 + 54

        if model_type == "i/o" or model_type == "io_open_drain":
            canvas.create_image((new_xpos, 77), image=io, anchor='nw')
        else:
            canvas.create_image((new_xpos, 76), image=output, anchor='nw')


def create_model_summary_table(ibis_data, tab_obj):
    table = ttk.Treeview(tab_obj, height=4, selectmode="none")
    table["columns"] = ("Item", "Value")
    table.column("#0", width=0, stretch=tk.NO)
    table.column("Item", anchor=tk.W, width=150)
    table.column("Value", anchor=tk.W, width=400)
    table.bind('<Motion>', 'break')  # Prevent resizing of table columns: https://stackoverflow.com/a/71710427

    table.heading("Item", text="Item", anchor=tk.W)
    table.heading("Value", text="Value", anchor=tk.W)

    table.insert(parent="", index="end", iid=0, text="", values=("IBIS File", f"{ibis_data.file_name}"))
    table.insert(parent="", index="end", iid=1, text="", values=("Component Name", f"{ibis_data.component_name}"))
    table.insert(parent="", index="end", iid=2, text="", values=("Model Name", f"{ibis_data.model_name}"))
    table.insert(parent="", index="end", iid=3, text="", values=("Model Type", f"{ibis_data.model_type}"))

    return table


def inset_model_parameter_row(table_obj, _id, param, symbol, data_item, multiplier, _format, units):
    if data_item is not None:

        typical = f"{data_item[0] * multiplier:{_format}}"
        try:
            minimum = f"{min(data_item[1], data_item[2]) * multiplier:{_format}}"
        except:
            minimum = "N/A"

        try:
            maximum = f"{max(data_item[1], data_item[2]) * multiplier:{_format}}"
        except:
            maximum = "N/A"

        table_obj.insert(parent="", index="end", iid=_id, text="",
                         values=(param, symbol, minimum, typical, maximum, units))


def create_model_parameters_table(ibis_data, tab_obj):
    table = ttk.Treeview(tab_obj, height=10, selectmode="none")
    table["columns"] = ("Parameter", "Symbol", "Min", "Typ", "Max", "Unit")
    table.column("#0", width=0, stretch=tk.NO)
    table.column("Parameter", anchor=tk.W, width=150)
    table.column("Symbol", anchor=tk.CENTER, width=100)
    table.column("Min", anchor=tk.CENTER, width=80)
    table.column("Typ", anchor=tk.CENTER, width=80)
    table.column("Max", anchor=tk.CENTER, width=80)
    table.column("Unit", anchor=tk.CENTER, width=60)
    table.bind('<Motion>', 'break')  # Prevent resizing of table columns: https://stackoverflow.com/a/71710427

    table.heading("Parameter", text="Parameter", anchor=tk.CENTER)
    table.heading("Symbol", text="Symbol", anchor=tk.CENTER)
    table.heading("Min", text="Min", anchor=tk.CENTER)
    table.heading("Typ", text="Typ", anchor=tk.CENTER)
    table.heading("Max", text="Max", anchor=tk.CENTER)
    table.heading("Unit", text="Unit", anchor=tk.CENTER)

    inset_model_parameter_row(table, 0, "Package Resistance", "r_pkg", ibis_data.r_pkg, 1e3, ".2f", u"m\u03A9")
    inset_model_parameter_row(table, 1, "Package Inductance", "l_pkg", ibis_data.l_pkg, 1e9, ".4f", "nH")
    inset_model_parameter_row(table, 2, "Package Capacitance", "c_pkg", ibis_data.c_pkg, 1e12, ".3f", "pF")
    inset_model_parameter_row(table, 3, "Die Capacitance", "c_comp", ibis_data.c_comp, 1e12, ".3f", "pF")
    table.insert(parent="", index="end", iid=4, text="", values=("", "", "", "", "", ""))  # Empty Line in the table

    inset_model_parameter_row(table, 5, "Voltage Range", "v_range", ibis_data.v_range, 1, "", "V")
    inset_model_parameter_row(table, 6, "Temperature Range", "temp_range", ibis_data.temp_range, 1, "", u"\u00B0C")

    inset_model_parameter_row(table, 7, "Pullup Reference", "pullup_ref", ibis_data.pullup_ref, 1, "", "V")
    inset_model_parameter_row(table, 8, "Pulldown Reference", "pulldown_ref", ibis_data.pulldown_ref, 1, "", "V")
    inset_model_parameter_row(table, 9, "Power Clamp Reference", "pwr_clamp_ref", ibis_data.pwr_clamp_ref, 1, "", "V")
    inset_model_parameter_row(table, 10, "Ground Clamp Reference", "gnd_clamp_ref", ibis_data.gnd_clamp_ref, 1, "", "V")

    return table


# Run the main main_window
if __name__ == '__main__':

    # Main Window Top Level Config
    main_window = tk.Tk()
    main_window.geometry(f"{_width}x{_height}")
    main_window.resizable(False, False)
    main_window.title(f" IBIS to SPICE Converter - Version {version.get_version()}")

    # Set up the Icon
    # Using a base 64 image within a python file so that the exe build does not depend on an external icon file
    # _icon_data = base64.b64decode(img.get_icon())
    _icon_img = tk.PhotoImage(data=img.get_icon())
    main_window.iconphoto(False, _icon_img)

    # ---------------------------------------------------------------------------
    # Frame 1: Browse for IBIS file
    # ---------------------------------------------------------------------------
    frame1 = tk.Frame(main_window, height=50, width=_width)
    frame1.pack(padx=10, pady=10)
    label1 = tk.Label(master=frame1, text="IBIS File Select", padx=10)
    label1.pack(side=tk.LEFT)

    entry = tk.Entry(master=frame1, width=80)
    entry.pack(side=tk.LEFT)
    entry.config(state='disabled')

    btn1 = tk.Button(master=frame1, text="Browse", padx=10, command=browse_ibis_file_callback)
    btn1.pack(side=tk.LEFT)

    # ---------------------------------------------------------------------------
    # Frame 2: IBIS Component and Model Selection
    # ---------------------------------------------------------------------------
    frame2 = tk.Frame(main_window, height=240, width=_width, relief=tk.SUNKEN, borderwidth=1)
    frame2.pack(padx=10, pady=10)
    label1 = tk.Label(master=frame2, text="IBIS Component Select")
    label1.place(x=10, y=10)

    label2 = tk.Label(master=frame2, text="IBIS Model Select")
    label2.place(x=_width / 2, y=10)

    list_component = tk.Listbox(master=frame2, exportselection=0, width=45, height=10)
    list_component.place(x=10, y=35)

    list_model = tk.Listbox(master=frame2, exportselection=0, width=45, height=10)
    list_model.place(x=_width / 2, y=35)

    btn2 = tk.Button(master=frame2, text="Check Model", command=check_model_callback)
    btn2.place(x=10, y=205)
    ToolTip(btn2, msg="view the I-V and Voltage-Time characteristic graphs of the model", delay=0.2)

    marker_var = tk.IntVar()
    marker_check = tk.Checkbutton(master=frame2, text="Enable marker", variable=marker_var)
    marker_check.select()
    marker_check.place(x=110, y=205)
    ToolTip(marker_check, msg="Place data point markers on the graphs within the check model window", delay=0.2)

    # ---------------------------------------------------------------------------
    # Frame 3: SPICE subcircuit options
    # ---------------------------------------------------------------------------
    frame3 = tk.Frame(main_window, height=150, width=_width, relief=tk.SUNKEN, borderwidth=1)
    frame3.pack(padx=10, pady=10)
    label3 = tk.Label(master=frame3, text="Spice Subcircuit Options")
    label3.place(x=10, y=10)

    # Radio Buttons for LTSpice vs Generic
    radio_var1 = tk.StringVar()
    radio1 = tk.Radiobutton(master=frame3, text="LTSpice", variable=radio_var1, value="LTSpice")
    radio2 = tk.Radiobutton(master=frame3, text="Generic", variable=radio_var1, value="Generic")
    radio1.select()  # Select LTSpice as default type
    radio1.place(x=170, y=10)
    radio2.place(x=250, y=10)
    ToolTip(radio1, msg="produces a subcircuit file containing special syntax specific to LTSpice", delay=0.2)
    ToolTip(radio2, msg="produces a subcircuit file that most Spice simulators should be able to parse", delay=0.2)

    # Radio Buttons for Corner Select
    label4 = tk.Label(master=frame3, text="Corner Select")
    label4.place(x=10, y=40)
    radio_var2 = tk.StringVar()
    radio3 = tk.Radiobutton(master=frame3, text="Weak-Slow", variable=radio_var2, value="WeakSlow")
    radio4 = tk.Radiobutton(master=frame3, text="Typical", variable=radio_var2, value="Typical")
    radio5 = tk.Radiobutton(master=frame3, text="Fast-Strong", variable=radio_var2, value="FastStrong")
    radio6 = tk.Radiobutton(master=frame3, text="All", variable=radio_var2, value="All")
    radio4.select()
    radio3.place(x=170, y=40)
    radio4.place(x=270, y=40)
    radio5.place(x=350, y=40)
    radio6.place(x=450, y=40)

    ToolTip(radio3, msg="combines the minimum (weak) I-V curves and minimum (slow) V-T waveforms", delay=0.2)
    ToolTip(radio4, msg="combines the typical I-V curves and typical V-T waveforms", delay=0.2)
    ToolTip(radio5, msg="combines the maximum (strong) I-V curves and maximum (fast) V-T waveforms", delay=0.2)
    ToolTip(radio6, msg="creates the SPICE subcircuit files for all corners", delay=0.2)

    # Radio Buttons for Selecting Input or Output Model Type
    label5 = tk.Label(master=frame3, text="I/O Type")
    label5.place(x=10, y=70)
    radio_var3 = tk.StringVar()
    radio7 = tk.Radiobutton(master=frame3, text="Input", variable=radio_var3, value="Input")
    radio8 = tk.Radiobutton(master=frame3, text="Output", variable=radio_var3, value="Output")
    radio7.select()
    radio7.place(x=170, y=70)
    radio8.place(x=250, y=70)

    label5_tooltip = "SPICE Subcircuit file can only be created for an input OR an output pin. " \
                     "\nThis option selects the SPICE model type to generate when the IBIS model is of I/O type"
    ToolTip(label5, msg=label5_tooltip, delay=0.2)
    ToolTip(radio7, msg="subcircuit will be created for the input pin - no pullup/pulldown transistors", delay=0.2)
    ToolTip(radio8, msg="subcircuit will be created for the output pin - with pullup/pulldown transistors", delay=0.2)

    btn3 = tk.Button(master=frame3, text="Help", command=help_message_callback)
    btn3.place(x=10, y=110)

    btn4 = tk.Button(master=frame3, text="Create SPICE Subcircuit", command=create_subcircuit_file_callback)
    btn4.place(x=50, y=110)

    main_window.mainloop()
