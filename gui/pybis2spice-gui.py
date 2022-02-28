# ---------------------------------------------------------------------------
# Author: Kishan Amratia
# Date: 02-Jan-2022
# Module Name: pybis2spice-gui.py
"""
A tkinter GUI for helping users to convert IBIS models into SPICE models
"""
# ---------------------------------------------------------------------------

from pybis2spice import pybis2spice
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import time
import logging

_width = 740
_height = 450
_gui_version = '0.1.0'
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Callback Functions
# ---------------------------------------------------------------------------
def help_message():
    messagebox.showinfo(title="Help", message="Hello")


def browse():
    file = filedialog.askopenfile(parent=window,
                                  title='Choose a file',
                                  filetypes=[("IBIS files", ".ibs"), ("All files", "*")])
    logging.info(file.name)


def load_components_and_models():

    file = filedialog.askopenfile(parent=window,
                                  title='Choose a file',
                                  filetypes=[("IBIS files", ".ibs"),("All files", "*")])
    ibis_filepath = file.name
    entry.delete(0, tk.END)
    entry.insert(0, ibis_filepath)

    logging.info(f"Subcircuit Option: {radio_var1.get()}")
    logging.info(f"Component Selected: {list_component.get(tk.ACTIVE)}")
    logging.info(f"Model Selected: {list_model.get(tk.ACTIVE)}")

    window.config(cursor="")
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

    window.update()
    window.config(cursor="")


def check_model():
    file_path = entry.get()
    component_name = list_component.get(tk.ACTIVE)
    model_name = list_model.get(tk.ACTIVE)

    window.config(cursor="wait")

    ibis_data = pybis2spice.DataModel(file_path, model_name, component_name)

    window.update()
    time.sleep(0.1)
    window.config(cursor="")

    if hasattr(ibis_data, 'model'):
        new_window(ibis_data)
    else:
        dialog = messagebox.showinfo(title="No model Selected", message="Please select a valid IBIS file and model")


def new_window(ibis_data_model):
    data_window = tk.Toplevel(window)
    data_window.title(f"Check IBIS Model - {ibis_data_model.model_name}")
    data_window.minsize(700, 700)
    data_window.grab_set()
    data_window.geometry(f"+{window.winfo_rootx() + 50}+{window.winfo_rooty() + 50}")
    # data_window.resizable(True, True)

    tab_parent = ttk.Notebook(data_window)
    tab1 = ttk.Frame(tab_parent)
    tab2 = ttk.Frame(tab_parent)
    tab3 = ttk.Frame(tab_parent)
    tab4 = ttk.Frame(tab_parent)
    tab5 = ttk.Frame(tab_parent)
    tab6 = ttk.Frame(tab_parent)
    tab7 = ttk.Frame(tab_parent)
    tab_parent.add(tab1, text="Summary")

    if ibis_data_model.iv_pullup is not None:
        tab_parent.add(tab2, text="Pullup")
    if ibis_data_model.iv_pulldown is not None:
        tab_parent.add(tab3, text="Pulldown")
    if ibis_data_model.iv_pwr_clamp is not None:
        tab_parent.add(tab4, text="Power Clamp")
    if ibis_data_model.iv_gnd_clamp is not None:
        tab_parent.add(tab5, text="Ground Clamp")

    if ibis_data_model.vt_rising:
        tab_parent.add(tab6, text="Rising Waveforms")
    if ibis_data_model.vt_falling:
        tab_parent.add(tab7, text="Falling Waveforms")

    tab1_lbl = tk.Label(tab1, text=f"{ibis_data_model}")
    tab1_lbl.pack(side=tk.TOP)

    tab2_lbl = tk.Label(tab2, text="Pullup voltage data referenced to pullup reference or voltage rail")
    tab2_lbl.pack()

    tab4_lbl = tk.Label(tab4, text="Power clamp voltage data referenced to power clamp reference or voltage rail")
    tab4_lbl.pack()

    tab_parent.pack(expand=1, fill=tk.BOTH)

    fig1 = pybis2spice.plot_iv_data_single(ibis_data_model.iv_pullup, "Pullup device IV data")
    fig2 = pybis2spice.plot_iv_data_single(ibis_data_model.iv_pulldown, "Pulldown device IV data")
    fig3 = pybis2spice.plot_iv_data_single(ibis_data_model.iv_pwr_clamp, "Power clamp IV data")
    fig4 = pybis2spice.plot_iv_data_single(ibis_data_model.iv_gnd_clamp, "Ground clamp IV data")

    fig5 = pybis2spice.plot_vt_rising_waveform_data(ibis_data_model)
    fig6 = pybis2spice.plot_vt_falling_waveform_data(ibis_data_model)

    canvas1 = FigureCanvasTkAgg(fig1, master=tab2)
    canvas2 = FigureCanvasTkAgg(fig2, master=tab3)
    canvas3 = FigureCanvasTkAgg(fig3, master=tab4)
    canvas4 = FigureCanvasTkAgg(fig4, master=tab5)
    canvas5 = FigureCanvasTkAgg(fig5, master=tab6)
    canvas6 = FigureCanvasTkAgg(fig6, master=tab7)

    canvas1.draw()
    canvas2.draw()
    canvas3.draw()
    canvas4.draw()
    canvas5.draw()
    canvas6.draw()

    canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas3.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas4.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas5.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas6.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar1 = NavigationToolbar2Tk(canvas1, tab2)
    toolbar2 = NavigationToolbar2Tk(canvas2, tab3)
    toolbar3 = NavigationToolbar2Tk(canvas3, tab4)
    toolbar4 = NavigationToolbar2Tk(canvas4, tab5)
    toolbar5 = NavigationToolbar2Tk(canvas5, tab6)
    toolbar6 = NavigationToolbar2Tk(canvas6, tab7)

    toolbar1.update()
    toolbar2.update()
    toolbar3.update()
    toolbar4.update()
    toolbar5.update()
    toolbar6.update()

    canvas1.get_tk_widget().pack()
    canvas2.get_tk_widget().pack()
    canvas3.get_tk_widget().pack()
    canvas4.get_tk_widget().pack()
    canvas5.get_tk_widget().pack()
    canvas6.get_tk_widget().pack()


def print_values():
    logging.info(entry.get())
    logging.info(list_component.get(tk.ACTIVE))
    logging.info(list_model.get(tk.ACTIVE))
    logging.info(radio_var1.get())
    logging.info(radio_var2.get())


# ---------------------------------------------------------------------------
# Window Options
# ---------------------------------------------------------------------------
window = tk.Tk()
window.geometry(f"{_width}x{_height}")
window.resizable(False, False)
window.title(f"IBIS to SPICE converter - v{_gui_version}")

# ---------------------------------------------------------------------------
# Frame 1: Browse for IBIS file
# ---------------------------------------------------------------------------
frame1 = tk.Frame(window, height=50, width=_width)
frame1.pack(padx=10, pady=10)
label1 = tk.Label(master=frame1, text="IBIS File Select", padx=10)
label1.pack(side=tk.LEFT)

entry = tk.Entry(master=frame1, width=80)
entry.pack(side=tk.LEFT)

btn1 = tk.Button(master=frame1, text="Browse", padx=10, command=load_components_and_models)
btn1.pack(side=tk.LEFT)


# ---------------------------------------------------------------------------
# Frame 2: IBIS Component and Model Selection
# ---------------------------------------------------------------------------
frame2 = tk.Frame(window, height=240, width=_width, relief=tk.SUNKEN, borderwidth=1)
frame2.pack(padx=10, pady=10)
label1 = tk.Label(master=frame2, text="IBIS Component Select")
label1.place(x=10, y=10)

label2 = tk.Label(master=frame2, text="IBIS Model Select")
label2.place(x=_width/2, y=10)

list_component = tk.Listbox(master=frame2, exportselection=0, width=45, height=10)
list_component.place(x=10, y=35)

list_model = tk.Listbox(master=frame2, exportselection=0, width=45, height=10)
list_model.place(x=_width/2, y=35)

#scrollbar = tk.Scrollbar(frame2, orient=tk.VERTICAL, command=list_model.yview)
#scrollbar.place(x=620, y=35, width=15, height=165)

btn2 = tk.Button(master=frame2, text="Check Model", command=check_model)
btn2.place(x=10, y=205)

# ---------------------------------------------------------------------------
# Frame 3: SPICE subcircuit options
# ---------------------------------------------------------------------------
frame3 = tk.Frame(window, height=120, width=_width, relief=tk.SUNKEN, borderwidth=1)
frame3.pack(padx=10, pady=10)
label3 = tk.Label(master=frame3, text="Spice Subcircuit Options")
label3.place(x=10, y=10)

radio_var1 = tk.StringVar()
radio1 = tk.Radiobutton(master=frame3, text="LTSpice", variable=radio_var1, value="LTSpice")
radio2 = tk.Radiobutton(master=frame3, text="Generic", variable=radio_var1, value="Generic")
radio1.select()
radio1.place(x=170, y=10)
radio2.place(x=250, y=10)

label4 = tk.Label(master=frame3, text="Corner Select")
label4.place(x=10, y=40)
radio_var2 = tk.IntVar()
radio3 = tk.Radiobutton(master=frame3, text="Weak-Slow", variable=radio_var2, value=0)
radio4 = tk.Radiobutton(master=frame3, text="Typical", variable=radio_var2, value=1)
radio5 = tk.Radiobutton(master=frame3, text="Fast-Strong", variable=radio_var2, value=2)
radio4.select()
radio3.place(x=170, y=40)
radio4.place(x=270, y=40)
radio5.place(x=350, y=40)

btn3 = tk.Button(master=frame3, text="Help", command=help_message)
btn3.place(x=10, y=80)

btn4 = tk.Button(master=frame3, text="Create SPICE Subcircuit", command=print_values)
btn4.place(x=50, y=80)

# Run
window.mainloop()
