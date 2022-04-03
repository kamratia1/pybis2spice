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
import base64
import img
import re
import os

_width = 740
_height = 480
logging.basicConfig(level=logging.INFO)


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


def validate_io_type(ibis_data, io_type):
    # Check that io type selected matches the model_type
    # Returns True if it passes validation

    model_type = ""
    try:
        model_type = ibis_data.model_type
    except:
        pass

    result = False
    model_types_list = ["input", "i/o"]
    if io_type == "Input":
        for item in model_types_list:
            if item == model_type.lower():
                result = True

    model_types_list = ["output", "i/o", "3-state", "open_drain"]
    if io_type == "Output":
        for item in model_types_list:
            if item == model_type.lower():
                result = True

    return result


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

    # latest_version = check_latest_version()
    latest_version = '0.2'  # TODO - For Testing
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
    subcircuit_type = radio_var1.get()  # LTSpice or Generic
    corner = radio_var2.get()
    io_type = radio_var3.get()

    main_window.config(cursor="wait")

    ibis_data = pybis2spice.DataModel(ibis_file_path, model_name, component_name)

    main_window.update()
    time.sleep(0.1)
    main_window.config(cursor="")

    _PROCEED = False
    if not(hasattr(ibis_data, 'model')):  # Check that model has been selected
        messagebox.showwarning(title="No model Selected", message="Please select a valid IBIS file and model")

    else:
        io_type_validation = validate_io_type(ibis_data, io_type)
        if io_type_validation:
            _PROCEED = True
        else:
            message = f"I/O Select is invalid with IBIS model type. \n\n"
            message += f"{ibis_data.model_name} Type: {ibis_data.model_type}\n\n"
            if io_type == "Input":
                message += "Please select the Output I/O type"
            else:
                message += "Please select the Input I/O type"
            messagebox.showwarning(title="I/O mismatch", message=message)

        if _PROCEED:
            logging.info(f"IBIS File: {ibis_file_path}")
            logging.info(f"Component Selected: {component_name}")
            logging.info(f"Model Selected: {model_name}")
            logging.info(f"Subcircuit Type: {subcircuit_type}")
            logging.info(f"Corner: {corner}")
            logging.info(f"I/O Select: {io_type}")

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

                    _corner = "WeakSlow"
                    filename1 = f'{ibis_data.model_name}-{io_type}-{_corner}.sub'
                    filepath1 = os.path.join(file, filename1)
                    ret1 = subcircuit.generate_spice_model(io_type=io_type,
                                                           subcircuit_type=subcircuit_type,
                                                           ibis_data=ibis_data,
                                                           corner=_corner,
                                                           output_filepath=filepath1)

                    _corner = "Typical"
                    filename2 = f'{ibis_data.model_name}-{io_type}-{_corner}.sub'
                    filepath2 = os.path.join(file, filename2)
                    ret2 = subcircuit.generate_spice_model(io_type=io_type,
                                                           subcircuit_type=subcircuit_type,
                                                           ibis_data=ibis_data,
                                                           corner=_corner,
                                                           output_filepath=filepath2)

                    _corner = "FastStrong"
                    filename3 = f'{ibis_data.model_name}-{io_type}-{_corner}.sub'
                    filepath3 = os.path.join(file, filename3)
                    ret3 = subcircuit.generate_spice_model(io_type=io_type,
                                                           subcircuit_type=subcircuit_type,
                                                           ibis_data=ibis_data,
                                                           corner=_corner,
                                                           output_filepath=filepath3)

                    ret = ret1 + ret2 + ret3

                    if ret == 0:
                        message_success = ""

                        # Check file for any "WARNINGS and add to the message"
                        warnings = ""
                        pattern = re.compile("WARNING")
                        files = [filepath1, filepath2, filepath3]
                        for _file in files:
                            for line in open(_file):
                                for _ in re.finditer(pattern, line):
                                    warnings += line

                        message_success += f"SPICE subcircuit models successfully created at:\n{file}"

                        # Create symbol
                        if subcircuit_type == "LTSpice":
                            symbol_file1 = subcircuit.create_ltspice_symbol(ibis_data, "WeakSlow", filepath1, io_type)
                            symbol_file2 = subcircuit.create_ltspice_symbol(ibis_data, "Typical", filepath2, io_type)
                            symbol_file3 = subcircuit.create_ltspice_symbol(ibis_data, "FastStrong", filepath3, io_type)

                            logging.info(f"LTSpice Symbol created at: {symbol_file1}")
                            logging.info(f"LTSpice Symbol created at: {symbol_file2}")
                            logging.info(f"LTSpice Symbol created at: {symbol_file3}")

                            message_success += f"\n\nLTSpice symbols also created successfully at:\n{file}\n"

                        if warnings != "":
                            message_success += f"\n\nWARNINGS within the SPICE subcircuit file: \n"
                            message_success += f"{warnings}"

                        messagebox.showinfo(title="Success", message=message_success)
                    else:
                        message_error = f"SPICE subcircuit model generation failed."
                        messagebox.showerror(title="Failed to create model", message=message_error)

                else:
                    logging.info(f"Chosen File: {file.name}")
                    # Create the subcircuit file
                    ret = subcircuit.generate_spice_model(io_type=io_type,
                                                          subcircuit_type=subcircuit_type,
                                                          ibis_data=ibis_data,
                                                          corner=corner,
                                                          output_filepath=file.name)
                    if ret == 0:
                        message_success = ""

                        # Check file for any "WARNINGS and add to the message"
                        warnings = ""
                        pattern = re.compile("WARNING")
                        for line in open(file.name):
                            for _ in re.finditer(pattern, line):
                                warnings += line

                        message_success += f"SPICE subcircuit model successfully created at:\n{file.name}"

                        # Create symbol
                        if subcircuit_type == "LTSpice":
                            symbol_file = subcircuit.create_ltspice_symbol(ibis_data, corner, file.name, io_type)
                            message_success += f"\n\nLTSpice symbol also created successfully at:\n{symbol_file}\n"

                        if warnings != "":
                            message_success += f"\n\nWARNINGS within the SPICE subcircuit file: \n"
                            message_success += f"{warnings}"

                        messagebox.showinfo(title="Success", message=message_success)

                    else:
                        message_error = f"SPICE subcircuit model generation failed."
                        messagebox.showerror(title="Failed to create model", message=message_error)


def browse_ibis_file_callback():

    file = filedialog.askopenfile(parent=main_window,
                                  title='Choose a file',
                                  filetypes=[("IBIS files", ".ibs"), ("All files", "*")])

    if file:
        logging.info(file.name)
        ibis_filepath = file.name

        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, ibis_filepath)
        entry.config(state='disabled')

        main_window.config(cursor="")
        time.sleep(0.1)

        list_component.delete(0, tk.END)
        list_model.delete(0, tk.END)

        ibis_model = pybis2spice.get_ibis_model_ecdtools(ibis_filepath)

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
    file_path = entry.get()
    component_name = list_component.get(tk.ACTIVE)
    model_name = list_model.get(tk.ACTIVE)

    main_window.config(cursor="wait")

    ibis_data = pybis2spice.DataModel(file_path, model_name, component_name)

    main_window.update()
    time.sleep(0.1)
    main_window.config(cursor="")

    if hasattr(ibis_data, 'model'):
        check_model_window(ibis_data)
    else:
        messagebox.showinfo(title="No model Selected", message="Please select a valid IBIS file and model")


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

    model_table = ttk.Treeview(tab1, height=4, selectmode="none")
    model_table["columns"] = ("Item", "Value")
    model_table.column("#0", width=0, stretch=tk.NO)
    model_table.column("Item", anchor=tk.W, width=150)
    model_table.column("Value", anchor=tk.W, width=400)
    model_table.bind('<Motion>', 'break')  # Stop users from resizing table: https://stackoverflow.com/a/71710427

    model_table.heading("Item", text="Item", anchor=tk.W)
    model_table.heading("Value", text="Value", anchor=tk.W)

    model_table.insert(parent="", index="end", iid=0, text="", values=("IBIS File", f"{ibis_data.file_name}"))
    model_table.insert(parent="", index="end", iid=1, text="", values=("Component Name", f"{ibis_data.component_name}"))
    model_table.insert(parent="", index="end", iid=2, text="", values=("Model Name", f"{ibis_data.model_name}"))
    model_table.insert(parent="", index="end", iid=3, text="", values=("Model Type", f"{ibis_data.model_type}"))

    summary_table = ttk.Treeview(tab1, height=7, selectmode="none")
    summary_table["columns"] = ("Parameter", "Symbol", "Min", "Typ", "Max", "Unit")
    summary_table.column("#0", width=0, stretch=tk.NO)
    summary_table.column("Parameter", anchor=tk.W, width=150)
    summary_table.column("Symbol", anchor=tk.CENTER, width=100)
    summary_table.column("Min", anchor=tk.CENTER, width=80)
    summary_table.column("Typ", anchor=tk.CENTER, width=80)
    summary_table.column("Max", anchor=tk.CENTER, width=80)
    summary_table.column("Unit", anchor=tk.CENTER, width=60)
    summary_table.bind('<Motion>', 'break')  # Stop people from resizing: https://stackoverflow.com/a/71710427

    summary_table.heading("Parameter", text="Parameter", anchor=tk.CENTER)
    summary_table.heading("Symbol", text="Symbol", anchor=tk.CENTER)
    summary_table.heading("Min", text="Min", anchor=tk.CENTER)
    summary_table.heading("Typ", text="Typ", anchor=tk.CENTER)
    summary_table.heading("Max", text="Max", anchor=tk.CENTER)
    summary_table.heading("Unit", text="Unit", anchor=tk.CENTER)

    # Package Resistance
    summary_table.insert(parent="", index="end", iid=0, text="",
                         values=("Package Resistance", "R_pkg",
                                 f"{ibis_data.r_pkg[1]*1e3:.2f}",
                                 f"{ibis_data.r_pkg[0]*1e3:.2f}",
                                 f"{ibis_data.r_pkg[2]*1e3:.2f}", u"m\u03A9"))
    # Package Inductance
    summary_table.insert(parent="", index="end", iid=1, text="",
                         values=("Package Inductance", "L_pkg",
                                 f"{ibis_data.l_pkg[1]*1e9:.4f}",
                                 f"{ibis_data.l_pkg[0]*1e9:.4f}",
                                 f"{ibis_data.l_pkg[2]*1e9:.4f}", "nH"))
    # Package Capacitance
    summary_table.insert(parent="", index="end", iid=2, text="",
                         values=("Package Capacitance", "C_pkg",
                                 f"{ibis_data.c_pkg[1]*1e12:.3f}",
                                 f"{ibis_data.c_pkg[0]*1e12:.3f}",
                                 f"{ibis_data.c_pkg[2]*1e12:.3f}", "pF"))
    # Die Capacitance
    summary_table.insert(parent="", index="end", iid=3, text="",
                         values=("Die Capacitance", "C_comp",
                                 f"{ibis_data.l_pkg[1]*1e12:.3f}",
                                 f"{ibis_data.l_pkg[0]*1e12:.3f}",
                                 f"{ibis_data.l_pkg[2]*1e12:.3f}", "pF"))
    # Empty Line
    summary_table.insert(parent="", index="end", iid=4, text="", values=("", "", "", "", "", ""))

    # Voltage Range
    if ibis_data.v_range is not None:
        summary_table.insert(parent="", index="end", iid=5, text="",
                             values=("Voltage Range", "V_range",
                                     f"{ibis_data.v_range[1]}",
                                     f"{ibis_data.v_range[0]}",
                                     f"{ibis_data.v_range[2]}", "V"))
    # Temperature Range
    if ibis_data.temp_range is not None:
        summary_table.insert(parent="", index="end", iid=6, text="",
                             values=("Temperature Range", "Temp_range",
                                     f"{ibis_data.temp_range[1]}",
                                     f"{ibis_data.temp_range[0]}",
                                     f"{ibis_data.temp_range[2]}", u"\u00B0C"))

    tab0_lbl0 = tk.Label(tab1, text="\nIBIS Model Parameters")
    tab0_lbl0.pack()
    model_table.pack()

    tab0_lbl1 = tk.Label(tab1, text="\n")
    tab0_lbl1.pack()
    summary_table.pack()

    # Pullup Tab
    if ibis_data.iv_pullup is not None:
        tab2 = ttk.Frame(tab_parent)
        tab_parent.add(tab2, text="Pullup")
        fig1 = plot.plot_iv_data_single(ibis_data.iv_pullup, "Pullup device IV data")
        tab2_lbl = tk.Label(tab2, text="Pullup voltage data referenced to pullup reference or voltage rail")
        tab2_lbl.pack()
        canvas1 = FigureCanvasTkAgg(fig1, master=tab2)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar1 = NavigationToolbar2Tk(canvas1, tab2)
        toolbar1.update()
        canvas1.get_tk_widget().pack()

    # Pulldown Tab
    if ibis_data.iv_pulldown is not None:
        tab3 = ttk.Frame(tab_parent)
        tab_parent.add(tab3, text="Pulldown")
        fig2 = plot.plot_iv_data_single(ibis_data.iv_pulldown, "Pulldown device IV data")
        canvas2 = FigureCanvasTkAgg(fig2, master=tab3)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar2 = NavigationToolbar2Tk(canvas2, tab3)
        toolbar2.update()
        canvas2.get_tk_widget().pack()

    # Power Clamp Tab
    if ibis_data.iv_pwr_clamp is not None:
        tab4 = ttk.Frame(tab_parent)
        tab_parent.add(tab4, text="Power Clamp")
        fig3 = plot.plot_iv_data_single(ibis_data.iv_pwr_clamp, "Power clamp IV data")
        tab4_lbl = tk.Label(tab4, text="Power clamp voltage data referenced to power clamp reference or voltage rail")
        tab4_lbl.pack()
        canvas3 = FigureCanvasTkAgg(fig3, master=tab4)
        canvas3.draw()
        canvas3.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar3 = NavigationToolbar2Tk(canvas3, tab4)
        toolbar3.update()
        canvas3.get_tk_widget().pack()

    # Ground Clamp Tab
    if ibis_data.iv_gnd_clamp is not None:
        tab5 = ttk.Frame(tab_parent)
        tab_parent.add(tab5, text="Ground Clamp")
        fig4 = plot.plot_iv_data_single(ibis_data.iv_gnd_clamp, "Ground clamp IV data")
        canvas4 = FigureCanvasTkAgg(fig4, master=tab5)
        canvas4.draw()
        canvas4.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar4 = NavigationToolbar2Tk(canvas4, tab5)
        toolbar4.update()
        canvas4.get_tk_widget().pack()

    # Rising Waveform Tab
    if ibis_data.vt_rising:
        tab6 = ttk.Frame(tab_parent)
        tab_parent.add(tab6, text="Rising Waveforms")
        fig5 = plot.plot_vt_rising_waveform_data(ibis_data)
        plt.subplots_adjust(top=0.8)
        canvas5 = FigureCanvasTkAgg(fig5, master=tab6)
        canvas5.draw()
        canvas5.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar5 = NavigationToolbar2Tk(canvas5, tab6)
        toolbar5.update()
        canvas5.get_tk_widget().pack()

    # Falling Waveform Tab
    if ibis_data.vt_falling:
        tab7 = ttk.Frame(tab_parent)
        tab_parent.add(tab7, text="Falling Waveforms")
        fig6 = plot.plot_vt_falling_waveform_data(ibis_data)
        plt.subplots_adjust(top=0.8)
        canvas6 = FigureCanvasTkAgg(fig6, master=tab7)
        canvas6.draw()
        canvas6.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar6 = NavigationToolbar2Tk(canvas6, tab7)
        toolbar6.update()
        canvas6.get_tk_widget().pack()

    tab_parent.pack(expand=1, fill=tk.BOTH)


# Run the main main_window
if __name__ == '__main__':

    # Main Window Top Level Config
    main_window = tk.Tk()
    main_window.geometry(f"{_width}x{_height}")
    main_window.resizable(False, False)
    main_window.title(f" IBIS to SPICE Converter - Version {version.get_version()}")

    # Set up the Icon
    # Using a base 64 image within a python file so that the exe build does not depend on an external icon file
    _icon_data = base64.b64decode(img.get_icon())
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
