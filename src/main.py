import numpy as np
import pandas as pd
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps
from tabulate import tabulate
import datetime
import sys
import os
from pathlib import Path
import traceback
import scipy
import importlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # needed for 3D projection

# --- Path setup so the app behaves like before, even after repo re-org ---
SCRIPT_DIR = Path(__file__).resolve().parent

# Make sure src/, duct_functions/, and special_cases/ are importable like before
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

DUCT_FUNCTIONS_DIR = SCRIPT_DIR / "duct_functions"
SPECIAL_CASES_DIR = SCRIPT_DIR / "special_cases"
for p in (DUCT_FUNCTIONS_DIR, SPECIAL_CASES_DIR):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Use shared config + local modules
from config import EXCEL_FILE_PATH, FIGURES_DIR, get_data_file_path
from interpolation_manager import preload_all_case_interpolators, get_case_interpolator
from data_access import get_case_table

# --- Configuration ---
IMAGE_FOLDER = FIGURES_DIR  # Path object; points at repo_root/duct_figures
DEFAULT_IMAGE = "jacobs_smacna_logos.png"

# --- Unit Conversion Class ---
class UnitConverter:
    # Conversion Factors (Standard <-> Metric)
    MM_PER_IN = 25.4
    FT_PER_M = 3.28084
    CFM_PER_M3HR = 0.588578 # 1 / 1.699...
    M_PER_S_PER_FTMIN = 0.00508 # 1 / 196.85...
    PA_PER_INWC = 249.08891

    # Input: Convert Display Unit -> Standard Base Unit for Calculation
    def input_to_standard(self, display_label_text, value_as_entered):
        """Converts a value entered in display units (potentially metric)
           to standard units based on the display label."""
        label_lower = display_label_text.lower()
        if "(mm)" in label_lower:
            return value_as_entered / self.MM_PER_IN  # mm -> in
        elif "(m/s)" in label_lower:
             # Assuming m/s display corresponds to ft/min or ft/s standard internally
             # Let's assume calculations use ft/s for velocity IF (ft/s) is standard
             # If calc uses ft/min, adjust here. Currently handles ft/min -> m/s display
             # Let's assume input m/s should become ft/min for consistency with outputs?
             # This needs clarification based on calculation function needs.
             # For now: convert m/s input to ft/min standard
             return value_as_entered / self.M_PER_S_PER_FTMIN # m/s -> ft/min
        elif "(m³/h)" in label_lower:
            return value_as_entered / self.CFM_PER_M3HR # m³/hr -> cfm
        elif "(pa)" in label_lower:
            return value_as_entered / self.PA_PER_INWC # Pa -> in w.c.
        return value_as_entered # Assume standard if no recognized metric unit detected

    # Output: Format Standard Value/Label -> Display Unit based on mode
    def format_output_for_display(self, standard_label, standard_value, is_metric):
        """Converts standard result value and label to the appropriate display format."""
        if standard_value is None or standard_value == "N/A":
            display_label = self.get_display_label(standard_label, is_metric)
            return display_label, "N/A"

        standard_label = str(standard_label) if standard_label else ""

        if not is_metric:
            return standard_label, f"{standard_value:.3f}" if isinstance(standard_value, (int, float, np.number)) else str(standard_value)

        # Begin conversion logic
        label_lower = standard_label.lower()
        display_value_num = standard_value
        display_label = standard_label

        if "velocity" in label_lower:
            if "(ft/min)" in label_lower:
                display_value_num = standard_value * self.M_PER_S_PER_FTMIN  # ft/min -> m/s
                display_label = standard_label.replace("(ft/min)", "(m/s)")
            elif "(ft/s)" in label_lower:
                display_value_num = standard_value / self.FT_PER_M  # ft/s -> m/s
                display_label = standard_label.replace("(ft/s)", "(m/s)")

        if "pressure" in label_lower:
            if "(in w.c.)" in label_lower:
                display_value_num = standard_value * self.PA_PER_INWC  # in. w.c. -> Pa
                display_label = display_label.replace("(in w.c.)", "(Pa)")

        if any(k in label_lower for k in ["diameter", "length", "thickness", "width", "height"]):
            if "(in)" in label_lower:
                display_value_num = standard_value * self.MM_PER_IN  # in -> mm
                display_label = display_label.replace("(in)", "(mm)")
            elif "(ft)" in label_lower:
                display_value_num = standard_value / self.FT_PER_M  # ft -> m
                display_label = display_label.replace("(ft)", "(m)")

        if "flow" in label_lower or "cfm" in label_lower:
            if "(cfm)" in label_lower:
                display_value_num = standard_value * self.CFM_PER_M3HR  # cfm -> m³/hr
                display_label = display_label.replace("(cfm)", "(m³/h)")

        try:
            formatted_value = f"{float(display_value_num):.3f}" if isinstance(display_value_num, (int, float, np.number)) else str(display_value_num)
        except (ValueError, TypeError):
            formatted_value = str(display_value_num)

        return display_label, formatted_value


    # Label Text Conversion Only
    def get_display_label(self, standard_label, is_metric):
        """Converts only the label text based on the mode."""
        if not standard_label: return ""
        standard_label = str(standard_label) # Ensure string
        if not is_metric:
            return standard_label

        metric_label = standard_label
        metric_label = metric_label.replace("(in w.c.)", "(Pa)")
        metric_label = metric_label.replace("(in)", "(mm)")
        metric_label = metric_label.replace("(ft/min)", "(m/s)")
        metric_label = metric_label.replace("(ft/s)", "(m/s)")
        metric_label = metric_label.replace("(cfm)", "(m³/h)")
        metric_label = metric_label.replace("(ft)", "(m)")
        return metric_label

# --- Global Variables & Setup ---
data = pd.DataFrame()  # global placeholder; will be loaded after Tk exists

def load_excel_data():
    """Load the main Excel data into the global `data` DataFrame."""
    global data
    try:
        if not EXCEL_FILE_PATH.exists():
            raise FileNotFoundError(f"Excel file not found at resolved path: {EXCEL_FILE_PATH}")
        data = pd.read_excel(str(EXCEL_FILE_PATH), sheet_name="Master Table")
        data.set_index("ID", inplace=True)
        print(f"[INFO] Successfully loaded Excel data from: {EXCEL_FILE_PATH}")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        messagebox.showerror(
            "Error",
            f"Could not find the Excel data file:\n{EXCEL_FILE_PATH}\nPlease ensure it's in the correct location."
        )
        data = pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Could not load Excel data: {e}")
        messagebox.showerror(
            "Error",
            f"Failed to load data from Excel file:\n{e}"
        )
        data = pd.DataFrame()

input_columns = ["input 1", "input 2", "input 3", "input 4", "input 5", "input 6", "input 7", "input 8"]

# --- Widget and State Tracking ---
input_widgets = []
input_entries = [] # List of tuples: [(widget, standard_label_key), ...]
output_widgets = []
calculation_log = []
last_standard_results = {} # Store {standard_label: standard_value} from last calculation (mapped from raw)
current_duct_id = None
current_case_function = None
details_btn = None  # will be created in __main__ and enabled when a case is selected
is_metric_mode = False
converter = UnitConverter()

# --- Theme / Dark Mode ---
is_dark_mode = False

LIGHT_THEME = {
    "bg": "#f0f0f0",
    "fg": "#000000",

    "ribbon_bg": "#e0e0e0",

    "tree_bg": "#ffffff",
    "tree_fg": "#000000",
    "tree_sel_bg": "#cce5ff",

    "input_bg": "#eaf4ff",
    "output_bg": "#ffffe0",
    "panel_bg": "#ffffff",
    "image_bg": "#ffffff",
    "canvas_bg": "#ffffff",

    "entry_bg": "#ffffff",
    "entry_fg": "#000000",

    "button_bg": "#f0f0f0",
    "button_fg": "#333333",
    "button_active_bg": "#d9d9d9",

    "button_danger_bg": "#f0d0d0",
    "button_danger_active_bg": "#e0b0b0",
}

DARK_THEME = {
    "bg": "#020617",           # overall window background (very dark)
    "fg": "#e5e7eb",

    "ribbon_bg": "#020617",

    "tree_bg": "#020617",
    "tree_fg": "#e5e7eb",
    "tree_sel_bg": "#111827",

    "input_bg": "#111827",
    "output_bg": "#111827",
    "panel_bg": "#020617",
    "image_bg": "#000000",
    "canvas_bg": "#000000",

    "entry_bg": "#020617",
    "entry_fg": "#e5e7eb",

    # darker buttons, light text
    "button_bg": "#020617",
    "button_fg": "#e5e7eb",
    "button_active_bg": "#111827",

    "button_danger_bg": "#450a0a",
    "button_danger_active_bg": "#7f1d1d",
}

current_theme = LIGHT_THEME

# --- Widget Animation: Shake Inline Error Labels ---
def shake_widget(widget, shake_distance=10, shake_times=6, interval=40):
    """Shakes a widget (typically an error label) side to side for attention."""
    if not widget or not widget.winfo_ismapped():
        return
    grid_info = widget.grid_info()
    row = grid_info['row']
    column = grid_info['column']
    padx_orig = grid_info.get('padx', (0, 0))
    if isinstance(padx_orig, int):
        padx_orig = (padx_orig, padx_orig)
    elif isinstance(padx_orig, tuple) and len(padx_orig) == 1:
        padx_orig = (padx_orig[0], padx_orig[0])

    def shake_cycle(count=0):
        if count >= shake_times:
            widget.grid_configure(padx=padx_orig)
            return
        offset = shake_distance if count % 2 == 0 else -shake_distance
        widget.grid_configure(padx=(padx_orig[0] + offset, padx_orig[1] - offset))
        widget.after(interval, lambda: shake_cycle(count + 1))

    shake_cycle()

# --- Style helper (for buttons) ---
def style_button(btn, variant="normal"):
    if variant == "danger":
        bg_color = current_theme["button_danger_bg"]
        active_bg = current_theme["button_danger_active_bg"]
    else:
        bg_color = current_theme["button_bg"]
        active_bg = current_theme["button_active_bg"]

    btn.configure(
        font=("Segoe UI", 10),
        relief="groove",
        bd=1,
        padx=10,
        pady=4,
        bg=bg_color,
        fg=current_theme["button_fg"],
        activebackground=active_bg,
        activeforeground=current_theme["fg"],
        cursor="hand2"
    )

# --- GUI Functions ---

def save_log_to_excel():
    if not calculation_log:
        print("[INFO] No calculations to save.")
        messagebox.showinfo("Log Empty", "There are no calculations in the log to save.")
        return
    try:
        df = pd.DataFrame(calculation_log)
        cols = list(df.columns)
        ordered_cols = []
        if "Timestamp" in cols: ordered_cols.append(cols.pop(cols.index("Timestamp")))
        if "Duct ID" in cols: ordered_cols.append(cols.pop(cols.index("Duct ID")))
        # Identify inputs (raw entered values, keys are standard labels)
        input_cols = [c for c in cols if "(" in c or any(k in c.lower() for k in ["ratio", "type", "angle", "diameter", "thickness", "width", "height", "length"]) and c not in ordered_cols]
        ordered_cols.extend(sorted(input_cols))
        # Identify outputs (raw returned keys like 'Output X: ...')
        output_cols = [c for c in cols if "Output " in c and ":" in c and c not in ordered_cols]
        ordered_cols.extend(sorted(output_cols))
        # Add any remaining columns (like Error)
        remaining_cols = [c for c in cols if c not in ordered_cols]
        ordered_cols.extend(remaining_cols)

        df = df[ordered_cols]
    except Exception as e:
         print(f"[ERROR] Failed to prepare log DataFrame: {e}")
         messagebox.showerror("Log Error", f"Failed to prepare log data for saving:\n{e}")
         return

    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                                             title="Save Calculation Log As")
    if file_path:
        try:
            df.to_excel(file_path, index=False, float_format="%.4f")
            print(f"[INFO] Calculation log saved to {file_path}")
            messagebox.showinfo("Log Saved", f"Calculation log successfully saved to:\n{file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save log to Excel: {e}")
            messagebox.showerror("Save Error", f"Failed to save log to Excel file:\n{e}")

def view_log_popup():
    if not calculation_log:
        print("[INFO] Log is empty.")
        messagebox.showinfo("Log Empty", "There are no calculations in the log.")
        return
    popup = Toplevel(root)
    popup.title("Calculation Log Preview")
    popup.geometry("1200x600")
    frame = Frame(popup)
    frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
    text_widget = Text(frame, wrap=NONE, font=("Courier New", 9), padx=10, pady=10, borderwidth=0, highlightthickness=0)
    text_widget.pack(side=LEFT, fill=BOTH, expand=True)
    vsb = Scrollbar(frame, orient=VERTICAL, command=text_widget.yview)
    vsb.pack(side=RIGHT, fill=Y)
    text_widget.config(yscrollcommand=vsb.set)
    hsb = Scrollbar(popup, orient=HORIZONTAL, command=text_widget.xview)
    hsb.pack(side=BOTTOM, fill=X, padx=5, pady=(0,5))
    text_widget.config(xscrollcommand=hsb.set)
    try:
        df = pd.DataFrame(calculation_log)
        log_text = tabulate(df, headers='keys', tablefmt='grid', showindex=False, floatfmt=".3f", missingval="N/A")
    except Exception as e:
        log_text = f"[ERROR] Could not render log: {e}\n\nLog Data:\n{calculation_log}"
        print(f"[ERROR] Could not render log for popup: {e}")
    text_widget.insert(END, log_text)
    text_widget.config(state=DISABLED)

def toggle_units():
    """Switches between Standard and Metric units and updates the UI."""
    global is_metric_mode
    is_metric_mode = not is_metric_mode
    mode_str = "Metric" if is_metric_mode else "Standard"
    print(f"[INFO] Unit mode toggled to: {mode_str}")
    mode_label.config(text=f"Mode: {mode_str}", fg="#007acc" if is_metric_mode else "#cc0000")

    # Update Input Labels
    for entry_widget, standard_label_key in input_entries:
        try:
            widget_index = input_widgets.index(entry_widget)
            if widget_index > 0 and isinstance(input_widgets[widget_index - 1], Label):
                label_widget = input_widgets[widget_index - 1]
                new_display_label = converter.get_display_label(standard_label_key, is_metric_mode)
                label_widget.config(text=f"{new_display_label}:")
            else:
                print(f"[WARN] No label found for input: {standard_label_key}")
        except (ValueError, IndexError):
            print(f"[WARN] Widget not found for input: {standard_label_key}")
        except Exception as e:
            print(f"[ERROR] Updating input label '{standard_label_key}': {e}")

    # Update Output Labels (already-prepopulated outputs)
    for widget in output_widgets:
        if isinstance(widget, Label) and hasattr(widget, 'original_standard_label'):
            original_label = widget.original_standard_label
            new_label = converter.get_display_label(original_label, is_metric_mode)
            widget.config(text=f"{new_label}:")

    # Update Output Values if Available
    if last_standard_results:
        print("[DEBUG] Re-displaying outputs with new units using last standard results.")
        display_outputs_from_standard(last_standard_results)

    print(f"[INFO] UI updated for {mode_str} mode.")

def clear_inputs():
    """Fully clears all widgets in the input frame and resets tracking lists."""
    global input_widgets, input_entries

    # Destroy ALL widgets inside input_frame (not just tracked ones)
    for widget in input_frame.winfo_children():
        widget.destroy()

    input_widgets.clear()
    input_entries.clear()

    # Safe unbind
    try:
        root.unbind("<Return>")
    except Exception as e:
        print(f"[WARN] Failed to unbind <Return>: {e}")

    print("[INFO] Input fields fully cleared (visual and logic).")

def clear_outputs():
    """Destroys all widgets in the output frame and clears tracking lists."""
    global output_widgets, last_standard_results
    for widget in output_widgets: widget.destroy()
    output_widgets.clear(); last_standard_results.clear()
    print("[INFO] Output fields cleared.")

def bind_navigation(entry_widget, entry_list_index):
    """Binds Up/Down arrow keys for navigating between input entries."""
    def focus_next(event):
        next_index = entry_list_index + 1
        if next_index < len(input_entries): input_entries[next_index][0].focus_set()
        return "break"
    def focus_prev(event):
        prev_index = entry_list_index - 1
        if prev_index >= 0: input_entries[prev_index][0].focus_set()
        return "break"
    entry_widget.bind("<Down>", focus_next); entry_widget.bind("<Key-Return>", focus_next)
    entry_widget.bind("<Up>", focus_prev)

# --- Helper: Map Raw Output Keys to Standard Labels ---
OUTPUT_KEY_TO_STANDARD_LABEL_MAP = {
    # Standard cases
    "Output 1: Velocity": "Velocity (ft/min)",
    "Output 2: Vel. Pres @ V0 (in w.c.)": "Velocity Pressure (in w.c.)",
    "Output 3: Loss Coefficient": "Loss Coefficient",
    "Output 4: Pressure Loss (in w.c.)": "Total Pressure Loss (in w.c.)",

    # Interpolation / diagnostic variants (e.g., A8H)
    "Output 3: Loss Coefficient (nearest)": "Loss Coefficient (nearest)",
    "Output 4: Loss Coefficient (bilinear)": "Loss Coefficient (bilinear)",
    "Output 5: Pressure Loss (in w.c., bilinear)": "Total Pressure Loss (in w.c., bilinear)",

    # Branch-Main cases
    "Branch Velocity (ft/min)": "Branch Velocity (ft/min)",
    "Branch Velocity Pressure (in w.c.)": "Branch Velocity Pressure (in w.c.)",
    "Branch Loss Coefficient": "Branch Loss Coefficient",
    "Branch Pressure Loss (in w.c.)": "Branch Pressure Loss (in w.c.)",
    "Main, Source Velocity (ft/min)": "Main, Source Velocity (ft/min)",
    "Main, Converged Velocity (ft/min)": "Main, Converged Velocity (ft/min)",
    "Main, Source Velocity Pressure (in w.c.)": "Main, Source Velocity Pressure (in w.c.)",
    "Main, Converged Velocity Pressure (in w.c.)": "Main, Converged Velocity Pressure (in w.c.)",
    "Main Loss Coefficient": "Main Loss Coefficient",
    "Main Pressure Loss (in w.c.)": "Main Pressure Loss (in w.c.)",

    # Dual-Branch cases
    "Branch 1 Velocity (ft/min)": "Branch 1 Velocity (ft/min)",
    "Branch 1 Velocity Pressure (in w.c.)": "Branch 1 Velocity Pressure (in w.c.)",
    "Branch 1 Loss Coefficient": "Branch 1 Loss Coefficient",
    "Branch 1 Pressure Loss (in w.c.)": "Branch 1 Pressure Loss (in w.c.)",
    "Branch 2 Velocity (ft/min)": "Branch 2 Velocity (ft/min)",
    "Branch 2 Velocity Pressure (in w.c.)": "Branch 2 Velocity Pressure (in w.c.)",
    "Branch 2 Loss Coefficient": "Branch 2 Loss Coefficient",
    "Branch 2 Pressure Loss (in w.c.)": "Branch 2 Pressure Loss (in w.c.)",
}

def store_inputs_and_calculate():
    global input_entries, calculation_log, current_case_function, current_duct_id

    if not current_case_function:
        messagebox.showerror("Error", "No calculation case loaded. Select a duct type first.")
        return
    if not input_entries:
        messagebox.showwarning("Warning", "No input fields generated for this case.")
        return

    # --- Load constraints from "Constraints" sheet if available ---
    constraints = {}
    try:
        constraints_df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="Constraints")
        constraints_df = constraints_df[constraints_df["Duct ID"] == current_duct_id]
        for _, row in constraints_df.iterrows():
            key = row["Entry Key"]
            constraints[key] = {
                "type": row["Constraint Type"],
                "op": row["Operator"],
                "value": row["Value"],
                "message": row["Message"]
            }
    except Exception as e:
        print(f"[WARN] Constraints sheet not loaded or missing: {e}")

    # Clear any old inline errors
    for widget in input_frame.grid_slaves():
        if isinstance(widget, Label) and getattr(widget, "is_error", False):
            widget.destroy()

    # Dictionary for calculation function (entry_X keys)
    calc_function_inputs = {}
    standard_label_values = {}
    raw_inputs_for_log = {"Duct ID": current_duct_id}
    valid_inputs = True

    print("[INFO] --- Starting Calculation ---")

    for idx, (entry_widget, standard_label_key) in enumerate(input_entries):
        entry_key = f"entry_{idx + 1}"
        raw_value_str = entry_widget.get().strip()
        raw_inputs_for_log[standard_label_key] = raw_value_str

        if isinstance(entry_widget, ttk.Combobox):
            try:
                value_for_calc = float(raw_value_str)
            except ValueError:
                value_for_calc = raw_value_str  # Leave as-is if it's not numeric
        else:
            # --- FIX for A7H1 / A7H2: allow blank R or S ---
            if (
                raw_value_str == "" 
                and current_duct_id in ("A7H1", "A7H2")
                and standard_label_key in ("R (in)", "S (in)")
            ):
                value_for_calc = None   # <-- safe placeholder, UI untouched
            else:
                try:
                    entered_value = float(raw_value_str)
                    label_text = ""
                    try:
                        widget_index = input_widgets.index(entry_widget)
                        if widget_index > 0 and isinstance(input_widgets[widget_index - 1], Label):
                            label_text = input_widgets[widget_index - 1].cget("text")
                    except:
                        pass

                    value_for_calc = converter.input_to_standard(label_text, entered_value)
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Invalid numeric input: {raw_value_str}")
                    entry_widget.focus_set()
                    return

        calc_function_inputs[entry_key] = value_for_calc
        standard_label_values[standard_label_key] = value_for_calc

        # Reset background if previously red
        try:
            if entry_widget.winfo_class() == "Entry" and entry_widget.cget("bg") == "#ffcccc":
                entry_widget.config(bg=current_theme["entry_bg"])
        except tk.TclError:
            pass  # This widget doesn’t support "bg"

    # --- Constraint Check ---
    for key, rule in constraints.items():
        val = calc_function_inputs.get(key)
        if val is None:
            continue

        op = rule["op"]
        ctype = rule["type"]
        try:
            if ctype == "compare_to_entry":
                expression = rule["value"]
                local_env = {k: calc_function_inputs.get(k) for k in calc_function_inputs}
                condition = eval(f"{val} {op} {eval(expression, {}, local_env)}")
            else:
                target = float(rule["value"])
                condition = eval(f"{val} {op} {target}")

            if not condition:
                idx = int(key.split("_")[1]) - 1
                offending_widget = input_entries[idx][0]
                offending_widget.config(bg="#ffcccc")
                error_lbl = Label(
                    input_frame,
                    text=rule["message"],
                    fg="red",
                    bg=input_frame["bg"],
                    font=("Segoe UI", 9, "italic"),
                )
                error_lbl.grid(row=idx + 1, column=2, sticky="w", padx=5)
                error_lbl.is_error = True
                shake_widget(error_lbl)  # <--- Animate the error message
                valid_inputs = False

        except Exception as e:
            print(f"[ERROR] Evaluating constraint on {key}: {e}")
            continue

    if not valid_inputs:
        print("[WARN] Constraint check failed. Aborting calculation.")
        return

    print("[DEBUG] Input values prepared for calculation function (Std Units):")
    for k, v in calc_function_inputs.items():
        print(f"  '{k}': {v} (Type: {type(v)})")

    try:
        output_results_raw = current_case_function(calc_function_inputs, data)
        print(f"[DEBUG] Raw results returned from {current_case_function.__name__}: {output_results_raw}")
        if not isinstance(output_results_raw, dict):
            display_outputs_raw({"Error": "Calculation returned no valid data."})
            return
        display_outputs_raw(output_results_raw)

        if "Error" not in output_results_raw:
            log_entry = {"Timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            log_entry.update(raw_inputs_for_log)
            log_entry.update(output_results_raw)
            calculation_log.append(log_entry)
            print("[INFO] Calculation successfully logged.")

    except Exception as calc_err:
        print(f"[ERROR] Error during calculation: {calc_err}")
        traceback.print_exc()
        display_outputs_raw({"Error": f"Calculation failed: {calc_err}"})

def display_outputs_raw(raw_results_dict):
    """Displays outputs based on the RAW dictionary returned by the calculation function.
       Uses OUTPUT_KEY_TO_STANDARD_LABEL_MAP to find standard labels for unit conversion."""
    global output_widgets, last_standard_results
    clear_outputs()  # Clears widgets and last_standard_results

    processed_results_for_display = []  # List of (standard_label, standard_value)

    if not raw_results_dict:
        print("[DEBUG] display_outputs_raw called with empty results.")
        return

    output_frame.configure(bg=current_theme["output_bg"])

    if "Error" in raw_results_dict:
        error_message = raw_results_dict["Error"]
        error_label = Label(
            output_frame,
            text=error_message,
            bg=output_frame["bg"],
            fg="red",
            font=("Segoe UI", 10, "bold"),
            wraplength=output_frame.winfo_width() - 40,
            justify=LEFT,
        )
        error_label.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        output_widgets.append(error_label)
        output_frame.grid_rowconfigure(0, weight=1)
        print(f"[ERROR] Calculation Error Displayed: {error_message}")
        return

    # Process raw results using the map to get standard labels and store for toggling
    for raw_key, raw_value in raw_results_dict.items():
        standard_label = OUTPUT_KEY_TO_STANDARD_LABEL_MAP.get(raw_key)
        if standard_label:
            # Assume raw_value is in standard units as returned by function
            last_standard_results[standard_label] = raw_value  # Store for toggling
            processed_results_for_display.append((standard_label, raw_value))
        else:
            print(f"[WARN] Output key '{raw_key}' not found in MAP. Cannot process for display/toggle.")
            # Optionally display raw key/value without conversion if desired
            # processed_results_for_display.append((raw_key, raw_value))

    # Now display using the processed list of (standard_label, standard_value)
    display_outputs_from_standard(last_standard_results)

def display_outputs_from_standard(standard_results_dict):
    """Displays outputs given a dictionary of {standard_label: standard_value}.
       Used directly by toggle_units and potentially by display_outputs_raw after mapping."""
    global output_widgets  # Don't clear last_standard_results here
    # Clear only widgets
    for widget in output_widgets:
        widget.destroy()
    output_widgets.clear()

    if not standard_results_dict:
        print("[DEBUG] display_outputs_from_standard called empty.")
        return

    output_frame.configure(bg=current_theme["output_bg"])
    # Assuming no "Error" key here, as this is called with processed/stored data

    title_label = Label(
        output_frame,
        text="Output Results",
        bg=output_frame["bg"],
        font=("Segoe UI", 14, "bold"),
        fg=current_theme["fg"],
    )
    title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 10))
    output_widgets.append(title_label)

    row_counter = 1
    output_type = getattr(current_case_function, "output_type", "standard")  # Infer type

    # --- Grouping and Sectioning logic (using standard_label) ---
    sections = {}
    processed_keys = set()
    order = []
    if output_type == "dual_branch":
        order = ["Branch 1", "Branch 2", "Main"]
    elif output_type == "branch_main":
        order = ["Branch", "Main"]
    else:
        order = ["Results"]

    for std_label, std_value in standard_results_dict.items():
        found_section = False
        for section_prefix in order:
            # Use lower case for robust prefix matching
            if std_label and std_label.lower().startswith(section_prefix.lower()):
                if section_prefix not in sections:
                    sections[section_prefix] = []
                sections[section_prefix].append((std_label, std_value))
                processed_keys.add(std_label)
                found_section = True
                break
        if not found_section:
            fallback_section = "Results" if "Results" in order else "Other Results"
            if fallback_section not in sections:
                sections[fallback_section] = []
            sections[fallback_section].append((std_label, std_value))
            processed_keys.add(std_label)
            if fallback_section not in order:
                order.append(fallback_section)

    # --- Rendering Sections ---
    for section_title in order:
        if section_title not in sections or not sections[section_title]:
            continue
        results_list = sections[section_title]
        if len(order) > 1 or section_title != "Results":
            header = Label(
                output_frame,
                text=section_title,
                bg=output_frame["bg"],
                font=("Segoe UI", 11, "bold"),
                fg=current_theme["fg"],
            )
            header.grid(row=row_counter, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 3))
            output_widgets.append(header)
            row_counter += 1

        for standard_label, standard_value in results_list:
            # Use the standard_label with the converter
            display_label_text, display_value_str = converter.format_output_for_display(
                standard_label, standard_value, is_metric_mode
            )

            # Render label and value widgets
            output_label = Label(
                output_frame,
                text=f"{display_label_text}:",
                bg=output_frame["bg"],
                fg=current_theme["fg"],
                anchor="w",
                font=("Segoe UI", 10),
            )
            output_label.grid(row=row_counter, column=0, sticky="w", padx=(20, 5), pady=1)
            output_label.original_standard_label = standard_label  # Store standard label
            output_widgets.append(output_label)

            output_value_label = Label(
                output_frame,
                text=display_value_str,
                bg=current_theme["entry_bg"],
                fg=current_theme["entry_fg"],
                width=15,
                anchor="w",
                relief="sunken",
                borderwidth=1,
                font=("Segoe UI", 10),
            )
            output_value_label.grid(row=row_counter, column=1, sticky="w", padx=(5, 10), pady=1)
            output_value_label.original_standard_value = standard_value  # Store standard value
            output_widgets.append(output_value_label)
            row_counter += 1

    output_frame.grid_columnconfigure(0, weight=0)
    output_frame.grid_columnconfigure(1, weight=1)

def prepopulate_outputs_for_case(case_function, output_frame_ref, output_widgets_ref, clear_outputs_fn):
    """
    Wrapper to prepopulate outputs for a given case function, used for A12G and similar.
    """
    global current_case_function, output_frame, output_widgets
    current_case_function = case_function
    output_frame = output_frame_ref
    output_widgets = output_widgets_ref
    clear_outputs_fn()
    try:
        prepopulate_outputs()
    except Exception as e:
        print(f"[ERROR] prepopulate_outputs_for_case: Failed to prepopulate outputs: {e}")

def prepopulate_outputs():
    """Clears and populates the output frame with labels based on the expected function output."""
    global output_widgets, current_case_function
    clear_outputs()
    if not current_case_function:
        return

    output_frame.configure(bg=current_theme["output_bg"])
    title_label = Label(
        output_frame,
        text="Output",
        bg=output_frame["bg"],
        font=("Segoe UI", 14, "bold"),
        fg=current_theme["fg"],
    )
    title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 5))
    output_widgets.append(title_label)

    row_counter = 1
    output_type = getattr(current_case_function, "output_type", "standard")

    # Define standard labels (already mapped, no need to look up from raw keys)
    section_map = {
        "standard": [
            ("Standard", [
                "Velocity (ft/min)",
                "Velocity Pressure (in w.c.)",
                "Loss Coefficient",
                "Pressure Loss (in w.c.)",
            ])
        ],
        "branch_main": [
            ("Branch", [
                "Branch Velocity (ft/min)",
                "Branch Velocity Pressure (in w.c.)",
                "Branch Loss Coefficient",
                "Branch Pressure Loss (in w.c.)",
            ]),
            ("Main", [
                "Main, Source Velocity (ft/min)",
                "Main, Converged Velocity (ft/min)",
                "Main, Source Velocity Pressure (in w.c.)",
                "Main, Converged Velocity Pressure (in w.c.)",
                "Main Loss Coefficient",
                "Main Pressure Loss (in w.c.)",
            ]),
        ],
        "dual_branch": [
            ("Branch 1", [
                "Branch 1 Velocity (ft/min)",
                "Branch 1 Velocity Pressure (in w.c.)",
                "Branch 1 Loss Coefficient",
                "Branch 1 Pressure Loss (in w.c.)",
            ]),
            ("Branch 2", [
                "Branch 2 Velocity (ft/min)",
                "Branch 2 Velocity Pressure (in w.c.)",
                "Branch 2 Loss Coefficient",
                "Branch 2 Pressure Loss (in w.c.)",
            ]),
            ("Main", [
                "Main, Converged Velocity (ft/min)",
                "Main, Converged Velocity Pressure (in w.c.)",
            ]),
        ],
    }

    sections = section_map.get(output_type, section_map["standard"])
    print(f"[DEBUG] Pre-populating outputs for type '{output_type}'.")

    for section_title, labels in sections:
        if section_title:  # Header
            header = Label(
                output_frame,
                text=section_title,
                bg=output_frame["bg"],
                font=("Segoe UI", 11, "bold"),
                fg=current_theme["fg"],
            )
            header.grid(row=row_counter, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 3))
            output_widgets.append(header)
            row_counter += 1

        for std_label in labels:
            display_label_text = converter.get_display_label(std_label, is_metric_mode)
            lbl = Label(
                output_frame,
                text=f"{display_label_text}:",
                bg=output_frame["bg"],
                fg=current_theme["fg"],
                anchor="w",
                font=("Segoe UI", 10),
            )
            lbl.grid(row=row_counter, column=0, sticky="w", padx=(20, 5), pady=1)
            lbl.original_standard_label = std_label
            output_widgets.append(lbl)

            val = Label(
                output_frame,
                text="N/A",
                bg=current_theme["entry_bg"],
                fg="#666666",
                width=15,
                anchor="w",
                relief="sunken",
                borderwidth=1,
                font=("Segoe UI", 10),
            )
            val.grid(row=row_counter, column=1, sticky="w", padx=(5, 10), pady=1)
            val.original_standard_label = std_label
            output_widgets.append(val)

            row_counter += 1

    print(f"[DEBUG] Output fields prepopulated: {len(output_widgets) // 2}")
    output_frame.grid_columnconfigure(0, weight=0)
    output_frame.grid_columnconfigure(1, weight=1)

def show_details_window():
    """Opens a subwindow showing source table & plot(s) for the current duct case.

    Modes (per CASE_PLOT_CONFIG):
      - surface_3d:       single 3D surface from case table (x_col, y_col, z_col)
      - compare_nearest_bilinear: two 3D surfaces (nearest vs bilinear) using the
                                  case's _loss_coeff_nearest/_loss_coeff_bilinear
      - dual_2d:          two 2D plots from separate table relationships
                          (for legacy cases like A7A: ANGLE–K and R/D–C)
    """
    if not current_duct_id:
        messagebox.showinfo("Details", "No duct case selected.")
        return

    if current_duct_id not in CASE_PLOT_CONFIG:
        messagebox.showinfo(
            "Details",
            f"No details view configured yet for case '{current_duct_id}'.\n\n"
            "We can add this case to CASE_PLOT_CONFIG later."
        )
        return

    cfg = CASE_PLOT_CONFIG[current_duct_id]
    mode = cfg.get("mode", "surface_3d")

    try:
        df = get_case_table(current_duct_id).copy()
    except Exception as e:
        messagebox.showerror("Details Error", f"Failed to load case table for {current_duct_id}:\n{e}")
        return

    case_name = duct_map.get(current_duct_id, {}).get("case", "")

    # --- Build Details window ---
    win = tk.Toplevel(root)
    win.title(f"Details – {current_duct_id} {('– ' + case_name) if case_name else ''}")
    win.geometry("900x600")

    left_frame = tk.Frame(win, bg="white")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)

    right_frame = tk.Frame(win, bg="white")
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Left: information + data preview ---
    # Describe which columns we're using, based on mode
    if mode in ("surface_3d", "compare_nearest_bilinear"):
        x_col = cfg["x_col"]
        y_col = cfg["y_col"]
        z_col = cfg["z_col"]
        src_label_text = (
            f"Source case table\n"
            f"  via: data_access.get_case_table('{current_duct_id}')\n"
            f"  (typically 'Data set {current_duct_id}' in the main workbook\n"
            f"   or an override in data/case_tables/{current_duct_id}.xlsx)\n\n"
            f"Case ID: {current_duct_id}\n"
            f"Case Name: {case_name or 'N/A'}\n\n"
            f"Columns used:\n"
            f"  X → {x_col}\n"
            f"  Y → {y_col}\n"
            f"  C → {z_col}\n"
        )
        needed_cols = [c for c in (x_col, y_col, z_col) if c in df.columns]
    elif mode == "dual_2d":
        angle_col = cfg["angle_col"]
        k_col = cfg["k_col"]
        rd_col = cfg["rd_col"]
        c_col = cfg["c_col"]
        src_label_text = (
            f"Source case table\n"
            f"  via: data_access.get_case_table('{current_duct_id}')\n"
            f"  (typically 'Data set {current_duct_id}' in the main workbook\n"
            f"   or an override in data/case_tables/{current_duct_id}.xlsx)\n\n"
            f"Case ID: {current_duct_id}\n"
            f"Case Name: {case_name or 'N/A'}\n\n"
            f"Columns used:\n"
            f"  ANGLE → {angle_col}, K → {k_col}\n"
            f"  R/D   → {rd_col}, C → {c_col}\n"
        )
        needed_cols = [c for c in (angle_col, k_col, rd_col, c_col) if c in df.columns]
    else:
        src_label_text = (
            f"Source case table\n"
            f"  via: data_access.get_case_table('{current_duct_id}')\n\n"
            f"Case ID: {current_duct_id}\n"
            f"Case Name: {case_name or 'N/A'}\n\n"
            f"(Unknown mode '{mode}' – using raw table preview only.)"
        )
        needed_cols = list(df.columns)

    src_label = tk.Label(
        left_frame,
        text=src_label_text,
        bg="white",
        fg="#333333",
        justify="left",
        font=("Segoe UI", 9),
    )
    src_label.pack(anchor="nw", padx=5, pady=(5, 10))

    preview_frame = tk.Frame(left_frame, bg="white")
    preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    preview_text = tk.Text(
        preview_frame,
        wrap=tk.NONE,
        font=("Courier New", 9),
        bg="#f7f7f7",
        fg="#000000",
        height=20,
        borderwidth=1,
        relief="sunken",
    )
    preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    vsb = tk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_text.yview)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    preview_text.config(yscrollcommand=vsb.set)

    # Restrict to columns we actually care about
    try:
        if needed_cols:
            df_preview = df[needed_cols].dropna(how="all")
        else:
            df_preview = df
        from tabulate import tabulate
        table_str = tabulate(df_preview, headers="keys", tablefmt="psql", showindex=False, floatfmt=".4f")
    except Exception:
        table_str = df.to_string(index=False)

    preview_text.insert("1.0", table_str)
    preview_text.config(state=tk.DISABLED)

    # --- Right: plot(s) ---
    bg_color = "#000000" if is_dark_mode else "#ffffff"
    fg_color = "#ffffff" if is_dark_mode else "#000000"

    fig = Figure(figsize=(6.8, 4.6), dpi=100, facecolor=bg_color)

    elev = 30
    azim = 135

    def style_axes3d(ax, title=None):
        ax.set_facecolor(bg_color)
        if title is not None:
            ax.set_title(title, fontsize=9, color=fg_color)
        ax.tick_params(colors=fg_color)
        ax.xaxis.label.set_color(fg_color)
        ax.yaxis.label.set_color(fg_color)
        ax.zaxis.label.set_color(fg_color)

    def style_axes2d(ax, title=None):
        ax.set_facecolor(bg_color)
        if title is not None:
            ax.set_title(title, fontsize=9, color=fg_color)
        ax.tick_params(colors=fg_color)
        ax.xaxis.label.set_color(fg_color)
        ax.yaxis.label.set_color(fg_color)
        for spine in ax.spines.values():
            spine.set_color(fg_color)

    def style_colorbar(cbar, label_text):
        cbar.set_label(label_text, color=fg_color)
        cbar.ax.yaxis.set_tick_params(color=fg_color)
        for tick in cbar.ax.get_yticklabels():
            tick.set_color(fg_color)

    # --- Mode: nearest vs bilinear comparison (A8G, A8H, etc.) ---
    if mode == "compare_nearest_bilinear":
        # Import helpers from the case's outputs module dynamically
        try:
            module_name = f"duct_functions.{current_duct_id}_outputs"
            case_module = importlib.import_module(module_name)
            _loss_coeff_nearest = getattr(case_module, "_loss_coeff_nearest")
            _loss_coeff_bilinear = getattr(case_module, "_loss_coeff_bilinear")
        except Exception as e:
            messagebox.showerror(
                "Details Error",
                f"Could not import interpolation helpers for {current_duct_id}:\n{e}"
            )
            win.destroy()
            return

        x_col = cfg["x_col"]
        y_col = cfg["y_col"]
        z_col = cfg["z_col"]

        angle_data = df[[x_col, y_col, z_col]].dropna().copy()
        angle_data = angle_data.rename(columns={x_col: "ANGLE", y_col: "A1/A", z_col: "C"})

        # Build a grid over ANGLE and A1/A
        angles = np.linspace(angle_data["ANGLE"].min(), angle_data["ANGLE"].max(), 45)
        ratios = np.linspace(angle_data["A1/A"].min(), angle_data["A1/A"].max(), 45)
        A_grid, R_grid = np.meshgrid(angles, ratios)

        C_nearest_grid = np.zeros_like(A_grid, dtype=float)
        C_bilinear_grid = np.zeros_like(A_grid, dtype=float)

        for i in range(R_grid.shape[0]):
            for j in range(R_grid.shape[1]):
                a = A_grid[i, j]
                r = R_grid[i, j]
                C_nearest_grid[i, j] = _loss_coeff_nearest(angle_data, a, r)
                C_bilinear_grid[i, j] = _loss_coeff_bilinear(angle_data, a, r)

        # Left: original nearest-grid method
        ax1 = fig.add_subplot(1, 2, 1, projection="3d")
        ax1.view_init(elev=elev, azim=azim)
        ax1.set_xlabel(cfg["x_label"])
        ax1.set_ylabel(cfg["y_label"])
        ax1.set_zlabel(cfg["z_label"])
        style_axes3d(ax1, title="Original: nearest grid point")

        surf1 = ax1.plot_surface(
            A_grid, R_grid, C_nearest_grid,
            cmap="viridis",
            linewidth=0,
            antialiased=True,
        )
        ax1.scatter(
            angle_data["ANGLE"], angle_data["A1/A"], angle_data["C"],
            c="w" if is_dark_mode else "k", s=12, alpha=0.9, label="Table points"
        )
        ax1.legend(loc="upper left", fontsize=8, facecolor=bg_color, edgecolor=fg_color)
        cbar1 = fig.colorbar(surf1, ax=ax1, shrink=0.6, pad=0.08)
        style_colorbar(cbar1, cfg["z_label"])

        # Right: new bilinear interpolation method
        ax2 = fig.add_subplot(1, 2, 2, projection="3d")
        ax2.view_init(elev=elev, azim=azim)
        ax2.set_xlabel(cfg["x_label"])
        ax2.set_ylabel(cfg["y_label"])
        ax2.set_zlabel(cfg["z_label"])
        style_axes3d(ax2, title="New: bilinear interpolation")

        surf2 = ax2.plot_surface(
            A_grid, R_grid, C_bilinear_grid,
            cmap="viridis",
            linewidth=0,
            antialiased=True,
        )
        ax2.scatter(
            angle_data["ANGLE"], angle_data["A1/A"], angle_data["C"],
            c="w" if is_dark_mode else "k", s=12, alpha=0.9, label="Table points"
        )
        ax2.legend(loc="upper left", fontsize=8, facecolor=bg_color, edgecolor=fg_color)
        cbar2 = fig.colorbar(surf2, ax=ax2, shrink=0.6, pad=0.08)
        style_colorbar(cbar2, cfg["z_label"])

        fig.suptitle(cfg["title"], fontsize=11, color=fg_color)
        fig.subplots_adjust(left=0.05, right=0.97, top=0.88, bottom=0.08, wspace=0.28)

    # --- Mode: generic 3D surface from table (A13C, etc.) ---
    elif mode == "surface_3d":
        x_col = cfg["x_col"]
        y_col = cfg["y_col"]
        z_col = cfg["z_col"]

        if not {x_col, y_col, z_col}.issubset(df.columns):
            ax = fig.add_subplot(111)
            style_axes2d(ax)
            ax.text(
                0.5, 0.5,
                f"Case table for {current_duct_id} is missing\n"
                f"required columns {x_col}, {y_col}, {z_col}.",
                ha="center", va="center", color=fg_color, transform=ax.transAxes,
            )
        else:
            ax = fig.add_subplot(111, projection="3d")
            ax.view_init(elev=elev, azim=azim)
            ax.set_xlabel(cfg["x_label"])
            ax.set_ylabel(cfg["y_label"])
            ax.set_zlabel(cfg["z_label"])
            style_axes3d(ax, title=cfg["title"])

            try:
                pivot = df[[x_col, y_col, z_col]].dropna().pivot(
                    index=y_col, columns=x_col, values=z_col
                )
                pivot = pivot.sort_index().sort_index(axis=1)

                x_vals = pivot.columns.values
                y_vals = pivot.index.values
                X, Y = np.meshgrid(x_vals, y_vals)
                Z = pivot.values

                surf = ax.plot_surface(
                    X, Y, Z,
                    cmap="viridis",
                    linewidth=0,
                    antialiased=True,
                )

                ax.scatter(
                    df[x_col], df[y_col], df[z_col],
                    c="w" if is_dark_mode else "k", s=12, alpha=0.9, label="Table points"
                )
                ax.legend(loc="upper left", fontsize=8, facecolor=bg_color, edgecolor=fg_color)
                cbar = fig.colorbar(surf, ax=ax, shrink=0.7, pad=0.1)
                style_colorbar(cbar, cfg["z_label"])
                fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.1)
            except Exception as e:
                ax.text(
                    0.5, 0.5,
                    f"Could not generate 3D plot:\n{e}",
                    ha="center", va="center",
                    transform=ax.transAxes,
                    color=fg_color,
                )
                ax.set_axis_off()

    # --- Mode: dual 2D plots (legacy A7A) ---
    elif mode == "dual_2d":
        angle_col = cfg["angle_col"]
        k_col = cfg["k_col"]
        rd_col = cfg["rd_col"]
        c_col = cfg["c_col"]

        ax1 = fig.add_subplot(2, 1, 1)
        style_axes2d(ax1, title="Angle correction factor K vs Angle")
        try:
            df_angle = df[[angle_col, k_col]].dropna().sort_values(by=angle_col)
            ax1.plot(df_angle[angle_col], df_angle[k_col], "o-")
            ax1.set_xlabel(cfg["angle_label"])
            ax1.set_ylabel(cfg["k_label"])
        except Exception as e:
            ax1.text(
                0.5, 0.5,
                f"Could not plot K vs Angle:\n{e}",
                ha="center", va="center", transform=ax1.transAxes, color=fg_color,
            )

        ax2 = fig.add_subplot(2, 1, 2)
        style_axes2d(ax2, title="Base loss coefficient C vs R/D")
        try:
            df_rd = df[[rd_col, c_col]].dropna().sort_values(by=rd_col)
            ax2.plot(df_rd[rd_col], df_rd[c_col], "o-")
            ax2.set_xlabel(cfg["rd_label"])
            ax2.set_ylabel(cfg["c_label"])
        except Exception as e:
            ax2.text(
                0.5, 0.5,
                f"Could not plot C vs R/D:\n{e}",
                ha="center", va="center", transform=ax2.transAxes, color=fg_color,
            )

        fig.suptitle(cfg["title"], fontsize=11, color=fg_color)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1, hspace=0.4)

    else:
        ax = fig.add_subplot(111)
        style_axes2d(ax)
        ax.text(
            0.5, 0.5,
            f"No plotting logic for mode '{mode}'.",
            ha="center", va="center", transform=ax.transAxes, color=fg_color,
        )

    # Embed the figure in the Tk window
    canvas_fig = FigureCanvasTkAgg(fig, master=right_frame)
    canvas_widget = canvas_fig.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)
    canvas_fig.draw()

def update_inputs_and_outputs(duct_id):
    """Main function called on tree select. Updates inputs, loads function, prepopulates outputs."""
    global input_entries, input_widgets, root, data, output_frame
    global current_duct_id, current_case_function

    current_duct_id = duct_id
    print(f"\n[INFO] === Selecting Duct ID: {duct_id} ===")
    clear_inputs()
    clear_outputs()
    input_entries.clear()  # 🔧 Clear global tracking lists explicitly
    input_widgets.clear()
    current_case_function = None
    input_frame.configure(bg=current_theme["input_bg"])

    # --- Special Handling (e.g., A12G) ---
    if duct_id == "A12G":
        try:
            # Load the special dynamic-inputs module from special_cases
            a12g_module_name = "special_cases.A12G_dynamic_inputs"
            a12g_module = importlib.import_module(a12g_module_name)
            print("[DEBUG] A12G: Calling build_A12G_inputs()")

            a12g_module.build_A12G_inputs(
                input_frame=input_frame,
                input_entries=input_entries,
                input_widgets=input_widgets,
                bind_navigation=bind_navigation,
                store_inputs=store_inputs_and_calculate,
                data=data,
                output_frame=output_frame,
                output_widgets=output_widgets,
                root=root,
                prepopulate_outputs=prepopulate_outputs,
                clear_outputs=clear_outputs,
            )

            # Load the corresponding outputs function from duct_functions
            from duct_functions.A12G_outputs import A12G_outputs

            current_case_function = A12G_outputs
            print("[DEBUG] A12G inputs built.")
        except Exception as e:
            error_msg = f"Failed during A12G setup: {e}"
            print(f"[ERROR] {error_msg}")
            traceback.print_exc()
            messagebox.showerror("A12G Error", error_msg)
            lbl = Label(
                input_frame,
                text=error_msg,
                fg="red",
                bg=input_frame["bg"],
                wraplength=input_frame.winfo_width() - 20,
            )
            lbl.pack(padx=10, pady=10)
            input_widgets.append(lbl)
            return  # Stop if A12G fails

    # --- Standard Input Handling ---
    else:
        if data.empty:
            messagebox.showerror("Data Error", "Excel data is not loaded.")
            return
        if duct_id not in data.index:
            error_msg = f"Duct ID '{duct_id}' not found in Excel data."
            messagebox.showwarning("Data Missing", error_msg)
            lbl = Label(input_frame, text=error_msg, fg="orange", bg="#eaf4ff")
            lbl.pack(padx=10, pady=10)
            input_widgets.append(lbl)
            return

        try:
            print(f"[DEBUG] Loading standard inputs for {duct_id}.")
            duct_data_row = data.loc[[duct_id]]
            first_row = duct_data_row.iloc[0]

            # duct_functions/ is on sys.path, so modules are just A10C_outputs, etc.
            module_name = f"{duct_id}_outputs"
            func_name = module_name

            if module_name in sys.modules:
                case_module = importlib.reload(sys.modules[module_name])
            else:
                case_module = importlib.import_module(module_name)

            if hasattr(case_module, func_name):
                current_case_function = getattr(case_module, func_name)
            else:
                raise AttributeError(f"Function '{func_name}' not found.")
            print(
                f"[DEBUG] Loaded function: {func_name}, "
                f"Type: {getattr(current_case_function, 'output_type', 'standard')}"
            )

            title_label = Label(
                input_frame,
                text=f"Input Parameters ({duct_id})",
                bg=input_frame["bg"],
                fg=current_theme["fg"],
                font=("Segoe UI", 14, "bold"),
            )
            title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 10))
            input_widgets.append(title_label)
            grid_row_idx = 1
            dynamic_widgets_ref = {}
            calculate_button = None

            # --- Special coupling for A7A1 / A7A2 (R-S paired dropdowns) ---
            special_rs_case = duct_id in ("A7A1", "A7A2")
            rs_pairs = []
            r_values_ordered = []
            s_values_ordered = []
            r_combo = None
            s_combo = None

            if special_rs_case:
                try:
                    # Build list of (R, S) pairs from dropdown 3 / dropdown 4 in Excel rows
                    for _, row in duct_data_row.iterrows():
                        rv = row.get("dropdown 3", np.nan)
                        sv = row.get("dropdown 4", np.nan)
                        if pd.notna(rv) and pd.notna(sv):
                            r_val = str(rv).strip()
                            s_val = str(sv).strip()
                            rs_pairs.append((r_val, s_val))
                    if rs_pairs:
                        r_values_ordered = [p[0] for p in rs_pairs]
                        s_values_ordered = [p[1] for p in rs_pairs]
                    print(f"[DEBUG] A7A R/S pairs from Excel for {duct_id}: {rs_pairs}")
                except Exception as e:
                    print(f"[ERROR] Failed to build R/S pairs for {duct_id}: {e}")
                    rs_pairs = []
                    r_values_ordered = []
                    s_values_ordered = []

            def place_calculate_button(button_row):
                nonlocal calculate_button
                if calculate_button and calculate_button in input_widgets:
                    input_widgets.remove(calculate_button)
                    calculate_button.destroy()
                root.unbind("<Return>")
                calculate_button = Button(
                    input_frame,
                    text="Calculate",
                    command=store_inputs_and_calculate,
                    bg="#d0e0d0",
                    fg="black",
                    font=("Segoe UI", 11, "bold"),
                    relief="raised",
                    bd=2,
                    padx=15,
                    pady=4,
                    activebackground="#b0c0b0",
                    cursor="hand2",
                )
                calculate_button.grid(row=button_row, column=0, columnspan=2, pady=15, ipady=2)
                input_widgets.append(calculate_button)
                root.bind("<Return>", lambda event, b=calculate_button: b.invoke())
                print(f"[DEBUG] Calculate button placed/moved to row {button_row}.")

            def update_dynamic_fields(trigger_widget, selected_value, base_row_after_trigger):
                nonlocal grid_row_idx
                trigger_key = trigger_widget.standard_label_key
                if trigger_key in dynamic_widgets_ref:
                    for widget in dynamic_widgets_ref[trigger_key]:
                        if widget in input_widgets:
                            input_widgets.remove(widget)
                        input_entries[:] = [item for item in input_entries if item[0] != widget]
                        widget.destroy()
                    del dynamic_widgets_ref[trigger_key]
                    for i, (entry_w, _) in enumerate(input_entries):
                        bind_navigation(entry_w, i)

                dynamic_row = base_row_after_trigger
                dynamic_widgets_ref[trigger_key] = []
                fields_to_add = []
                if selected_value == "screen":
                    fields_to_add = [("n, free area ratio:", "ratio_n")]
                elif selected_value == "perforated plate":
                    fields_to_add = [
                        ("n, free area ratio:", "ratio_n"),
                        ("Plate thickness (in):", "plate_t"),
                        ("Hole diameter (in):", "hole_d"),
                    ]

                if not fields_to_add:
                    place_calculate_button(dynamic_row)
                    return

                print(f"[DEBUG] Adding {len(fields_to_add)} dynamic fields for '{selected_value}'.")
                new_entries_to_bind = []
                for label_std, key_suffix in fields_to_add:
                    label_display = converter.get_display_label(label_std, is_metric_mode)
                    lbl = Label(
                        input_frame,
                        text=f"{label_display}:",
                        bg="#eaf4ff",
                        fg="black",
                        anchor="e",
                        font=("Segoe UI", 10),
                    )
                    lbl.grid(row=dynamic_row, column=0, sticky="e", padx=(10, 5), pady=1)
                    input_widgets.append(lbl)
                    dynamic_widgets_ref[trigger_key].append(lbl)

                    entry = Entry(
                        input_frame,
                        width=20,
                        relief="solid",
                        borderwidth=1,
                        bg="white",
                        fg="black",
                        highlightthickness=1,
                        highlightbackground="grey",
                        highlightcolor="blue",
                        font=("Segoe UI", 10),
                    )
                    entry.grid(row=dynamic_row, column=1, sticky="w", padx=(5, 10), pady=1)
                    input_widgets.append(entry)
                    dynamic_widgets_ref[trigger_key].append(entry)
                    new_entries_to_bind.append((entry, label_std))
                    dynamic_row += 1

                try:
                    trigger_index = next(
                        i for i, (widget, _) in enumerate(input_entries) if widget == trigger_widget
                    )
                    for i, new_item in enumerate(new_entries_to_bind):
                        input_entries.insert(trigger_index + 1 + i, new_item)
                    for i in range(trigger_index, len(input_entries)):
                        bind_navigation(input_entries[i][0], i)
                except Exception as e:
                    print(f"[ERROR] Binding dynamic fields: {e}. Appending.")
                    start_idx = len(input_entries)
                    input_entries.extend(new_entries_to_bind)
                    for i, item in enumerate(new_entries_to_bind):
                        bind_navigation(item[0], start_idx + i)

                grid_row_idx = dynamic_row
                place_calculate_button(grid_row_idx)

            # --- Build static inputs from Excel definition ---
            for idx, excel_col_name in enumerate(input_columns):
                if excel_col_name in first_row and pd.notna(first_row[excel_col_name]):
                    input_label_standard = str(first_row[excel_col_name]).strip()
                    label_display_text = converter.get_display_label(input_label_standard, is_metric_mode)
                    print(
                        f"[DEBUG] Creating input row {grid_row_idx}: "
                        f"'{input_label_standard}' (Display: '{label_display_text}')"
                    )
                    lbl = Label(
                        input_frame,
                        text=f"{label_display_text}:",
                        bg="#eaf4ff",
                        fg="black",
                        anchor="e",
                        font=("Segoe UI", 10),
                    )
                    lbl.grid(row=grid_row_idx, column=0, sticky="e", padx=(10, 5), pady=1)
                    input_widgets.append(lbl)

                    dropdown_col_lookup = f"dropdown {idx + 1}"
                    dropdown_values = []
                    if dropdown_col_lookup in duct_data_row.columns:
                        col_series = duct_data_row[dropdown_col_lookup].dropna()

                        # --- Special handling of R/S dropdowns for A7A1/A7A2 ---
                        if (
                            special_rs_case
                            and dropdown_col_lookup == "dropdown 3"
                            and input_label_standard.strip().upper().startswith("R")
                            and r_values_ordered
                        ):
                            dropdown_values = list(r_values_ordered)
                            print(f"[DEBUG] Using ordered R values for {duct_id}: {dropdown_values}")
                        elif (
                            special_rs_case
                            and dropdown_col_lookup == "dropdown 4"
                            and input_label_standard.strip().upper().startswith("S")
                            and s_values_ordered
                        ):
                            dropdown_values = list(s_values_ordered)
                            print(f"[DEBUG] Using ordered S values for {duct_id}: {dropdown_values}")
                        else:
                            dropdown_values = [
                                str(v).strip()
                                for v in col_series.unique()
                                if str(v).strip()
                            ]

                    current_widget = None
                    if dropdown_values:
                        combo = ttk.Combobox(
                            input_frame,
                            values=dropdown_values,
                            state="readonly",
                            width=18,
                            font=("Segoe UI", 10),
                        )
                        combo.grid(row=grid_row_idx, column=1, sticky="w", padx=(5, 10), pady=1)
                        input_widgets.append(combo)
                        input_entries.append((combo, input_label_standard))
                        current_widget = combo
                        combo.standard_label_key = input_label_standard

                        # Track R/S comboboxes for A7A1/A7A2
                        if special_rs_case:
                            label_upper = input_label_standard.strip().upper()
                            if label_upper.startswith("R"):
                                r_combo = combo
                            elif label_upper.startswith("S"):
                                s_combo = combo

                        if "obstruction type" in input_label_standard.lower():
                            print(
                                f"[DEBUG] Binding dynamic update to dropdown: "
                                f"'{input_label_standard}'"
                            )
                            callback = lambda event, w=combo, r=grid_row_idx + 1: update_dynamic_fields(
                                w, w.get().strip().lower(), r
                            )
                            combo.bind("<<ComboboxSelected>>", callback)
                    else:
                        entry = Entry(
                            input_frame,
                            width=20,
                            relief="solid",
                            borderwidth=1,
                            bg="white",
                            fg="black",
                            highlightthickness=1,
                            highlightbackground="grey",
                            highlightcolor="blue",
                            font=("Segoe UI", 10),
                        )
                        entry.grid(row=grid_row_idx, column=1, sticky="w", padx=(5, 10), pady=1)
                        input_widgets.append(entry)
                        input_entries.append((entry, input_label_standard))
                        current_widget = entry

                    if current_widget:
                        bind_navigation(current_widget, len(input_entries) - 1)

                    grid_row_idx += 1

            # --- Bind coupling behavior for A7A1/A7A2 R/S dropdowns ---
            if special_rs_case and r_combo is not None and s_combo is not None:
                if len(r_values_ordered) == len(s_values_ordered) and len(r_values_ordered) > 0:
                    print(
                        f"[DEBUG] Binding R/S coupling for {duct_id} "
                        f"(n={len(r_values_ordered)} pairs)."
                    )

                    def on_r_selected(event):
                        idx_sel = r_combo.current()
                        if 0 <= idx_sel < len(s_values_ordered):
                            try:
                                s_combo.unbind("<<ComboboxSelected>>")
                            except Exception:
                                pass
                            s_combo.current(idx_sel)
                            # Re-bind S handler after programmatic update
                            s_combo.bind("<<ComboboxSelected>>", on_s_selected)

                    def on_s_selected(event):
                        idx_sel = s_combo.current()
                        if 0 <= idx_sel < len(r_values_ordered):
                            try:
                                r_combo.unbind("<<ComboboxSelected>>")
                            except Exception:
                                pass
                            r_combo.current(idx_sel)
                            # Re-bind R handler after programmatic update
                            r_combo.bind("<<ComboboxSelected>>", on_r_selected)

                    r_combo.bind("<<ComboboxSelected>>", on_r_selected)
                    s_combo.bind("<<ComboboxSelected>>", on_s_selected)
                else:
                    print(
                        f"[WARN] R/S value lists for {duct_id} are inconsistent; "
                        f"coupling not applied. R list len={len(r_values_ordered)}, "
                        f"S list len={len(s_values_ordered)}"
                    )

            place_calculate_button(grid_row_idx)
            if input_entries:
                input_entries[0][0].focus_set()
            print(f"[DEBUG] Total static input fields created: {len(input_entries)}")

        except Exception as e:
            error_msg = f"Error during input generation for {duct_id}: {e}"
            print(f"[ERROR] {error_msg}")
            traceback.print_exc()
            messagebox.showerror("Input Generation Error", error_msg)
            lbl = Label(
                input_frame,
                text=f"Error displaying inputs for '{duct_id}'.",
                fg="red",
                bg=input_frame["bg"],
            )
            lbl.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
            input_widgets.append(lbl)

    if current_case_function:
        try:
            prepopulate_outputs()
        except Exception as e:
            print(f"[ERROR] Failed pre-populating outputs for {duct_id}: {e}")
            traceback.print_exc()
    else:
        print("[WARN] No case function loaded, cannot pre-populate outputs.")

# --- Duct Map and Categories ---
# (Your existing duct_map and categories_map - ensure images exist)
duct_map = {
    "A7A": {"case": "Smooth Radius (Die Stamped)", "image": "smooth_radius_90_deg.png"},
    "A7B": {"case": "3 to 5 Piece, 90°", "image": "3_to_5_piece_90_deg.png"},
    "A7C": {"case": "Mitered Round", "image": "mitered_round.png"},
    "A7D": {"case": "Mitered Rectangular", "image": "mitered_rectangular.png"},
    "A7E": {"case": "Mitered, with Converging/Diverging Flow", "image": "mitered_with_converging_diverging_flow.png"},
    "A7F": {"case": "Smooth Radius without Vanes, 90°", "image": "smooth_radius_without_vanes_90.png"},
    "A7G": {"case": "Smooth Radius with Splitter Vanes", "image": "smooth_radius_with_splitter_vanes.png"},
    "A7H1": {"case": "Mitered with Single Thickness Turning Vanes", "image": "mitered_with_single_thickness_turning_vanes.png"},
    "A7H2": {"case": "Mitered with Double Thickness Turning Vanes", "image": "mitered_with_double_thickness_turning_vanes.png"},
    "A7I": {"case": "Z-Shaped (W/H=1)", "image": "z_shaped.png"},
    "A7J": {"case": "Different Planes", "image": "different_planes.png"},
    "A7K": {"case": "30° Offset", "image": "30_deg_offset.png"},
    "A7L": {"case": "Wye or Tee Shape", "image": "tee_wye_elbow.png"},

    "A8A": {"case": "Conical Expansion", "image": "conical_expansion.png"},
    "A8B": {"case": "Pyramidal Expansion", "image": "pyramidal_expansion.png"},
    "A8C": {"case": "Round to Rectangular", "image": "round_to_rectangular_expansion.png"},
    "A8D": {"case": "Rectangular to Round", "image": "rectangular_to_round_expansion.png"},
    "A8E": {"case": "Rectangular, Sides Straight", "image": "rectangular_sides_straight.png"},
    "A8F": {"case": "Symmetric at Fan with Duct Sides Straight", "image": "symmetric_at_fan_with_duct_sides_straight.png"},
    "A8G": {"case": "Asymmetric at Fan with Sides Straight, Top Level", "image": "asymmetric_at_fan_with_duct_sides_straight_top_level.png"},
    "A8H": {"case": "Asymmetric at Fan with Sides Straight, Top 10° Down", "image": "asymmetric_at_fan_with_duct_sides_straight_top_10_down.png"},
    "A8I": {"case": "Asymmetric at Fan with Sides Straight, Top 10° Up", "image": "asymmetric_at_fan_with_duct_sides_straight_top_10_up.png"},
    "A8J": {"case": "Pyramidal at Fan with Duct", "image": "pyramidal_at_fan_with_duct.png"},

    "A9A1": {"case": "Conical Contraction", "image": "conical_contraction.png"},
    "A9A2": {"case": "Pyramidal Contraction", "image": "pyramidal_contraction.png"},
    "A9B1": {"case": "Stepped Conical Contraction", "image": "stepped_conical_contraction.png"},
    "A9B2": {"case": "Stepped Pyramidal Contraction", "image": "stepped_pyramidal_contraction.png"},
    "A9C": {"case": "Rectangular Slot to Round", "image": "rectangular_slot_to_round.png"},

    "A10A1": {"case": "Round Converging Wye", "image": "round_converging_wye.png"},
    "A10B": {"case": "Converging Tee, 90°", "image": "round_converging_tee.png"},
    "A10C": {"case": "Tee, Round Branch to Rectangular Main", "image": "converging_tee_round_branch_to_rect_main.png"},
    "A10D": {"case": "Tee, Rectangular Main & Branch", "image": "converging_tee_rect_main_and_branch.png"},
    "A10E": {"case": "Converging Wye, Conical", "image": "round_converging_wye_conical.png"},
    "A10F": {"case": "Tee, 45° Entry Branch to Rectangular Main", "image": "converging_tee_rect_45_entry_branch_to_main.png"},
    "A10G": {"case": "Symmetrical Wye, Dovetail", "image": "rect_converging_wye_symmetrical_dovetail.png"},
    "A10H": {"case": "Converging Rectangular Wye", "image": "converging_curved_wye_rect.png"},
    "A10I1": {"case": "Symmetrical Wye", "image": "round_converging_sym_wye.png"},
    "A10I2": {"case": "Symmetrical Wye", "image": "converging_rectangular_wye.png"},

    "A11A": {"case": "Tee or Wye, 30° to 90°", "image": "diverging_wye_30_to_90.png"},
    "A11B": {"case": "Conical Tee, 90°", "image": "diverging_conical_tee_90.png"},
    "A11C": {"case": "Conical Wye, 45°", "image": "diverging_conical_wye_45.png"},
    "A11D": {"case": "90° Tee, Rolled 45° with 45° Elbow, Branch 90° to Main", "image": "diverging_tee_rolled_45_with_45_elbow.png"},
    "A11E": {"case": "90° Tee, with 90° Elbow, Branch 90° to Main", "image": "diverging_tee_90_elbow_branch_90_to_main.png"},
    "A11F": {"case": "90° Tee, Rolled 45° with 60° Elbow, Branch 45° to Main", "image": "diverging_tee_rolled45_60elbow_branch45.png"},
    "A11G": {"case": "90° Conical Tee, Rolled 45° with 45° Elbow, Branch 90° to Main", "image": "diverging_conical_tee_rolled45_45elbow_branch90.png"},
    "A11H": {"case": "90° Conical Tee, Rolled 45° with 60° Elbow, Branch 45° to Main", "image": "diverging_conical_tee_rolled45_60elbow_branch45.png"},
    "A11I": {"case": "45° Wye, Rolled 45° with 60° Elbow, Branch 90° to Main", "image": "diverging_wye_45_rolled45_60elbow_branch90.png"},
    "A11J": {"case": "45° Conical Wye, Rolled 45° with 60° Elbow, Branch 90° to Main", "image": "diverging_conical_wye_45_rolled45_60elbow_branch90.png"},
    "A11K": {"case": "45° Wye, Rolled 45° with 30° Elbow, Branch 45° to Main", "image": "diverging_wye_45_rolled45_30elbow_branch45.png"},
    "A11L": {"case": "45° Conical Wye, Rolled 45° with 30° Elbow, Branch 45° to Main", "image": "diverging_conical_wye_45_rolled45_30elbow_branch45.png"},
    "A11M": {"case": "45° Conical Main & Branch with 45° Elbow, Branch 90° to Main", "image": "diverging_conical_main_branch_45elbow_branch90.png"},
    "A11N": {"case": "Tee, 45° Rectangular Main & Branch", "image": "diverging_tee_45entry_rect_main_and_branch.png"},
    "A11O": {"case": "Tee, 45° Entry, Rectangular Main & Branch with Damper", "image": "diverging_tee_45entry_rect_main_and_branch_with_damper.png"},
    "A11P": {"case": "Tee, Rectangular Main & Branch", "image": "diverging_tee_rect_main_and_branch.png"},
    "A11Q": {"case": "Tee, Rectangular Main & Branch with Damper", "image": "diverging_tee_rect_main_and_branch_with_damper.png"},
    "A11R": {"case": "Tee, Rectangular Main & Branch with Extractor", "image": "diverging_tee_rect_main_and_branch_with_extractor.png"},
    "A11S": {"case": "Tee, Rectangular Main to Round Branch", "image": "diverging_tee_rect_main_round_branch.png"},
    "A11T": {"case": "Rectangular Wye, Main Straight", "image": "diverging_wye_rect.png"},
    "A11U": {"case": "Tee, Rectangular Main to Conical Branch", "image": "diverging_tee_rect_main_conical_branch.png"},
    "A11V": {"case": "90° Curved Rectangular Wye", "image": "diverging_wye_rect_curved_branch.png"},
    "A11W": {"case": "Symmetrical Wye, Dovetail", "image": "diverging_rect_wye_dovetail.png"},
    "A11X": {"case": "Symmetrical Wye", "image": "diverging_wye_symmetrical.png"},
    "A11Y": {"case": "Tee, Reducing, 45° Entry Branch", "image": "diverging_tee_rect_reducing_45entry_branch.png"},

    "A12A1": {"case": "Duct Mounted in Wall", "image": "entry_round_duct_mounted_in_wall.png"},
    "A12A2": {"case": "Duct Mounted in Wall", "image": "entry_rect_duct_mounted_in_wall.png"},
    "A12B": {"case": "Smooth Converging Bellmouth, without End Wall", "image": "entry_round_smooth_converging_bellmouth_without_end_wall.png"},
    "A12C": {"case": "Smooth Converging Bellmouth, with End Wall", "image": "entry_round_smooth_converging_bellmouth_with_end_wall.png"},
    "A12D1": {"case": "Conical Converging Bellmouth, without End Wall", "image": "entry_round_conical_converging_bellmouth_without_end_wall.png"},
    "A12D2": {"case": "Smooth Converging Bellmouth, without End Wall", "image": "entry_rect_smooth_converging_bellmouth_without_end_wall.png"},
    "A12E1": {"case": "Conical Converging Bellmouth, with End Wall", "image": "entry_round_conical_converging_bellmouth_with_end_wall.png"},
    "A12E2": {"case": "Smooth Converging Bellmouth, with End Wall", "image": "entry_rect_smooth_converging_bellmouth_with_end_wall.png"},
    "A12F": {"case": "Intake Hood", "image": "entry_round_intake_hood.png"},
    "A12G": {"case": "Hood, Tapered, Flanged or Unflanged", "image": "entry_hood_tapered_flanged_unflanged.png"},

    # --- A13 series (exits) ---

    # Existing
    "A13A": {"case": "Rectangular Flat Exit", "image": "rect_flat_exit.png"},
    "A13C": {"case": "Rectangular Conical Exit with/without Wall", "image": "rect_conical_exit_with_without_wall.png"},
    "A13D": {"case": "Rectangular to Round Exit", "image": "rect_to_round_exit.png"},
    "A13E2": {"case": "Rectangular Slot Exit", "image": "rect_slot_exit.png"},
    "A13F1": {"case": "Rectangular to Round Conical Exit", "image": "rect_to_round_conical_exit.png"},

    # New additions with placeholders
    "A13B": {"case": "Case A13B", "image": "A13B.png"},
    "A13E1": {"case": "Case A13E1", "image": "A13E1.png"},
    "A13F2": {"case": "Case A13F2", "image": "A13F2.png"},
    "A13G": {"case": "Case A13G", "image": "A13G.png"},
    "A13H": {"case": "Case A13H", "image": "A13H.png"},
    "A13I": {"case": "Case A13I", "image": "A13I.png"},
    "A13J1": {"case": "Case A13J1", "image": "A13J1.png"},
    "A13J2": {"case": "Case A13J2", "image": "A13J2.png"},

    # --- A14 series (screens / perforated plates) ---

    "A14A1": {"case": "Case A14A1", "image": "A14A1.png"},
    "A14A2": {"case": "Case A14A2", "image": "A14A2.png"},
    "A14B1": {"case": "Case A14B1", "image": "A14B1.png"},
    "A14B2": {"case": "Case A14B2", "image": "A14B2.png"},

    # --- A15 series (obstructions) ---

    "A15A": {"case": "Case A15A", "image": "A15A.png"},
    "A15B": {"case": "Case A15B", "image": "A15B.png"},
    "A15C": {"case": "Case A15C", "image": "A15C.png"},
    "A15D": {"case": "Case A15D", "image": "A15D.png"},
    "A15E": {"case": "Case A15E", "image": "A15E.png"},
    "A15F": {"case": "Case A15F", "image": "A15F.png"},
    "A15G": {"case": "Case A15G", "image": "A15G.png"},
    "A15H1": {"case": "Case A15H1", "image": "A15H1.png"},
    "A15H2": {"case": "Case A15H2", "image": "A15H2.png"},
    "A15I": {"case": "Case A15I", "image": "A15I.png"},
    "A15J": {"case": "Case A15J", "image": "A15J.png"},
    "A15K": {"case": "Case A15K", "image": "A15K.png"},
    "A15L": {"case": "Case A15L", "image": "A15L.png"},
}

categories_map = {
    "Round": {
        "Elbows": ["A7A", "A7B", "A7C", "A7K"],
        "Transitions (Diverging Flow)": ["A8A", "A8C"],
        "Transitions (Converging Flow)": ["A9A1", "A9B1"],
        "Converging Junctions (Tees, Wyes)": ["A10A1", "A10B", "A10E", "A10I1"],
        "Diverging Junctions (Tees, Wyes)": ["A11A", "A11B", "A11C", "A11D", "A11E", "A11F", "A11G", "A11H", "A11I", "A11J", "A11K", "A11L", "A11M"],
        "Entries": ["A12A1", "A12B", "A12C", "A12D1", "A12E1", "A12F", "A12G"],
        "Exits": ["A13A", "A13B", "A13E1", "A13F2", "A13J1"],
        "Screens and Perforated Plates": ["A14A1", "A14B1"],
        "Obstructions": ["A15A", "A15C", "A15H1", "A15I"]
    },
    "Rectangular": {
        "Elbows": ["A7D", "A7E", "A7F", "A7G", "A7H1", "A7H2", "A7I", "A7J", "A7L"],
        "Transitions (Diverging Flow)": ["A8B", "A8D", "A8E", "A8F", "A8G", "A8H", "A8I", "A8J"],
        "Transitions (Converging Flow)": ["A9A2", "A9B2", "A9C"],
        "Converging Junctions (Tees, Wyes)": ["A10C", "A10D", "A10F", "A10G", "A10H", "A10I2"],
        "Diverging Junctions (Tees, Wyes)": ["A11N", "A11O", "A11P", "A11Q", "A11R", "A11S", "A11T", "A11U", "A11V", "A11W", "A11X", "A11Y"],
        "Entries": ["A12A2", "A12D2", "A12E2"],
        "Exits": ["A13C", "A13D", "A13E2", "A13F1","A13G", "A13H", "A13I", "A13J2"],
        "Screens and Perforated Plates": ["A14A2", "A14B2"],
        "Obstructions": ["A15B", "A15D", "A15E", "A15F", "A15G", "A15H2", "A15J", "A15K", "A15L"]
    },
}

CATEGORY_SERIES_PREFIX = {
    "Elbows": "A7 Series: ",
    "Transitions (Diverging Flow)": "A8 Series: ",
    "Transitions (Converging Flow)": "A9 Series: ",
    "Converging Junctions (Tees, Wyes)": "A10 Series: ",
    "Diverging Junctions (Tees, Wyes)": "A11 Series: ",
    "Entries": "A12 Series: ",
    "Exits": "A13 Series: ",
    "Screens and Perforated Plates": "A14 Series: ",
    "Obstructions": "A15 Series: ",
}

# --- Case plot configuration (for Details window) ---
CASE_PLOT_CONFIG = {
    # Rectangular Conical Exit
    "A13C": {
        "title": "A13C: Rectangular Conical Exit with/without Wall",
        "x_col": "As/A",      # area ratio column in case table
        "y_col": "ANGLE",     # degrees
        "z_col": "C",         # loss coefficient
        "x_label": "Area Ratio As/A (-)",
        "y_label": "Angle (deg)",
        "z_label": "Loss Coefficient C (-)",
        "mode": "surface_3d",  # <<< explicit
    },
    # Golden example: A8H with nearest vs bilinear comparison
    "A8H": {
        "title": "A8H: Asymmetric at Fan with Sides Straight Top 10° Down",
        "x_col": "ANGLE",
        "y_col": "A1/A",
        "z_col": "C",
        "x_label": "Angle (deg)",
        "y_label": "Area Ratio A1/A (-)",
        "z_label": "Loss Coefficient C (-)",
        "mode": "compare_nearest_bilinear",  # <<< explicit
    },
    "A8G": {
        "title": "A8G: Asymmetric at Fan with Sides Straight, Top Level",
        "x_col": "ANGLE",
        "y_col": "A1/A",
        "z_col": "C",
        "x_label": "Angle (deg)",
        "y_label": "Area Ratio A1/A (-)",
        "z_label": "Loss Coefficient C (-)",
        "mode": "compare_nearest_bilinear",  # or "surface_3d" if you prefer
    },
}

# --- Treeview Selection Handler ---
def display_image(image_file=DEFAULT_IMAGE):
    """Displays the specified image, centered and aspect-ratio preserved.
       In dark mode, show a color-inverted (negative) version on a dark canvas."""
    canvas.delete("all")
    img_path = IMAGE_FOLDER / image_file  # Path object
    status_text = ""
    try:
        if not img_path.exists():
            status_text = f"Image file not found:\n{image_file}"
            print(f"[ERROR] {status_text}")
            if image_file != DEFAULT_IMAGE:
                img_path = IMAGE_FOLDER / DEFAULT_IMAGE
                if not img_path.exists():
                    status_text += f"\n\nDefault image missing:\n{DEFAULT_IMAGE}"
                    raise FileNotFoundError(status_text)
                else:
                    print(f"[WARN] Displaying default image: {DEFAULT_IMAGE}")
            else:
                raise FileNotFoundError(status_text)

        img = Image.open(img_path).convert("RGB")

        # --- Dark mode: show negative image for better contrast ---
        if is_dark_mode:
            img = ImageOps.invert(img)

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            canvas.after(150, lambda: display_image(image_file))
            return

        img_width, img_height = img.size
        img_aspect = img_width / img_height
        canvas_aspect = canvas_width / canvas_height

        pad_factor = 0.95
        if img_aspect > canvas_aspect:
            new_width = int(canvas_width * pad_factor)
            new_height = int(new_width / img_aspect)
        else:
            new_height = int(canvas_height * pad_factor)
            new_width = int(new_height * img_aspect)

        if new_width < 1 or new_height < 1:
            status_text = "Image display error:\nCalculated size too small."
            raise ValueError(status_text)

        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img_resized)

        x_center = (canvas_width - new_width) // 2
        y_center = (canvas_height - new_height) // 2
        canvas.create_image(x_center, y_center, image=photo, anchor=NW)
        canvas.image = photo

    except FileNotFoundError as e:
        print(f"[ERROR] Image file missing: {e}")
        canvas.create_text(
            canvas.winfo_width() / 2,
            canvas.winfo_height() / 2,
            text=status_text,
            fill="red",
            font=("Segoe UI", 12),
            justify="center",
        )
    except Exception as e:
        print(f"[ERROR] Failed to display image '{image_file}': {e}")
        traceback.print_exc()
        status_text = (
            f"Error loading image:\n{os.path.basename(image_file)}\n\nDetails in console."
        )
        canvas.create_text(
            canvas.winfo_width() / 2,
            canvas.winfo_height() / 2,
            text=status_text,
            fill="red",
            font=("Segoe UI", 12),
            justify="center",
        )

def apply_theme():
    """Apply current_theme colors to main widgets and ttk styles."""
    global style

    # Root window
    root.configure(bg=current_theme["bg"])

    # Top ribbon
    top_ribbon.configure(bg=current_theme["ribbon_bg"])
    mode_label.configure(
        bg=current_theme["ribbon_bg"],
        fg="#4ade80" if is_metric_mode else "#f87171"
    )

    # Frames
    tree_frame.configure(bg=current_theme["panel_bg"])
    right_top_frame.configure(bg=current_theme["panel_bg"])
    input_frame.configure(bg=current_theme["input_bg"])
    output_frame.configure(bg=current_theme["output_bg"])
    image_frame.configure(bg=current_theme["image_bg"])

    # Canvas
    canvas.configure(bg=current_theme["canvas_bg"])

    # Buttons (re-style with current theme)
    for btn in (save_btn, view_btn, clear_btn, details_btn, unit_toggle, theme_toggle):
        style_button(btn, variant="danger" if btn is clear_btn else "normal")

    # ttk Treeview style
    style.configure(
        "Treeview",
        rowheight=28,
        font=('Segoe UI', 10),
        background=current_theme["tree_bg"],
        fieldbackground=current_theme["tree_bg"],
        foreground=current_theme["tree_fg"],
    )
    style.map("Treeview", background=[('selected', current_theme["tree_sel_bg"])])

    style.configure(
        "Treeview.Heading",
        font=('Segoe UI', 11, 'bold'),
        background=current_theme["ribbon_bg"],
        relief="flat",
        foreground=current_theme["fg"],
    )

    # Existing labels/entries inside input/output frames created so far
    for frame in (input_frame, output_frame):
        for w in frame.winfo_children():
            cls = w.winfo_class()
            try:
                if cls == "Label":
                    w.configure(
                        bg=frame["bg"],
                        fg=current_theme["fg"]
                    )
                elif cls == "Entry":
                    w.configure(
                        bg=current_theme["entry_bg"],
                        fg=current_theme["entry_fg"],
                        insertbackground=current_theme["entry_fg"],  # caret color
                    )
                elif cls == "TCombobox":
                    # ttk widgets take theme from ttk style; often fine to leave as-is,
                    # or create a custom Combobox style if you want them fully dark.
                    pass
            except tk.TclError:
                pass  # some ttk widgets may not accept direct bg/fg   

def toggle_theme():
    global is_dark_mode, current_theme
    is_dark_mode = not is_dark_mode
    current_theme = DARK_THEME if is_dark_mode else LIGHT_THEME
    print(f"[INFO] Theme toggled to: {'Dark' if is_dark_mode else 'Light'}")
    apply_theme()

def maximize_window(root):
    """Try to maximize the window in a cross-platform way."""
    try:
        # Works on most Windows and some macOS/Linux Tk builds
        root.state("zoomed")
        return
    except tk.TclError:
        pass

    # Fallback: manually resize to full screen
    try:
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+0+0")
    except Exception as e:
        print(f"[WARN] Could not maximize window: {e}")

# --- Treeview Selection Handler ---
def on_tree_select(event):
    """Handle selection in the duct tree: load inputs/outputs, image, and enable Details."""
    selected_item = tree.focus()
    if not selected_item:
        return

    item = tree.item(selected_item)
    values = item.get("values", ())

    # Non-leaf nodes (Round / Rectangular / category) have no values
    if not values:
        # Disable Details if user just clicks a folder node
        details_btn.config(state="disabled")
        return

    duct_id = values[0]

    if duct_id not in duct_map:
        print(f"[WARN] Selected duct_id '{duct_id}' not found in duct_map.")
        details_btn.config(state="disabled")
        return

    # Update inputs & outputs for this duct
    update_inputs_and_outputs(duct_id)

    # Update image for this duct
    image_file = duct_map[duct_id].get("image", DEFAULT_IMAGE)
    display_image(image_file)

    # Enable/disable Details button depending on whether we have a plot config
    if duct_id in CASE_PLOT_CONFIG:
        details_btn.config(state="normal")
    else:
        details_btn.config(state="disabled")

    print(f"[INFO] Tree selection changed to duct '{duct_id}'")
 
# --- Main GUI Construction ---
# --- Main GUI Construction ---
if __name__ == "__main__":
    # Preload all interpolation surfaces (A13C etc.) once at startup
    preload_all_case_interpolators()

    root = Tk()
    root.title("Duct Pressure Loss Calculator (SMACNA)")
    root.minsize(1200, 700)
    root.geometry("1400x850")
    maximize_window(root)
    root.lift()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)
    root.focus_force()

    style = ttk.Style()
    available_themes = style.theme_names()
    preferred_themes = ['clam', 'vista', 'xpnative', 'default']
    for theme in preferred_themes:
        if theme in available_themes:
            try:
                style.theme_use(theme)
                print(f"[INFO] Using theme: {theme}")
                break
            except TclError:
                continue

    style.configure(
        "Treeview",
        rowheight=28,
        font=('Segoe UI', 10),
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground="#000000",
    )
    style.map("Treeview", background=[('selected', '#cce5ff')])
    style.configure(
        "Treeview.Heading",
        font=('Segoe UI', 11, 'bold'),
        background="#e0e0e0",
        relief="flat",
    )
    style.map("Treeview.Heading", relief=[('active', 'groove'), ('pressed', 'sunken')])

    top_ribbon = Frame(root, bg="#e0e0e0", bd=1, relief="raised")
    top_ribbon.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))

    # --- Log buttons ---
    save_btn = Button(top_ribbon, text="Save Log", command=save_log_to_excel)
    style_button(save_btn)  # normal
    save_btn.pack(side="left", padx=5, pady=5)

    view_btn = Button(top_ribbon, text="View Log", command=view_log_popup)
    style_button(view_btn)  # normal
    view_btn.pack(side="left", padx=5, pady=5)

    clear_btn = Button(
        top_ribbon,
        text="Clear Log",
        command=lambda: (
            calculation_log.clear(),
            print("[INFO] Log Cleared"),
            messagebox.showinfo("Log Cleared", "Calculation log has been cleared.")
        )
    )
    style_button(clear_btn, variant="danger")
    clear_btn.pack(side="left", padx=5, pady=5)

    # --- Details button (enabled only when a supported case is selected) ---
    details_btn = Button(
        top_ribbon,
        text="Details",
        command=show_details_window,
        state="disabled",
    )
    style_button(details_btn)
    details_btn.pack(side="left", padx=5, pady=5)

    # --- Mode / unit + theme controls on the right ---
    mode_label = Label(
        top_ribbon,
        text="Mode: Standard",
        bg="#e0e0e0",
        fg="#cc0000",
        font=("Segoe UI", 10, "bold")
    )
    mode_label.pack(side="right", padx=(20, 10))

    unit_toggle = Button(top_ribbon, text="Toggle Units", command=toggle_units)
    style_button(unit_toggle)
    unit_toggle.pack(side="right", padx=5)

    theme_toggle = Button(top_ribbon, text="Toggle Theme", command=toggle_theme)
    style_button(theme_toggle)
    theme_toggle.pack(side="right", padx=5)

    main_pane = PanedWindow(root, orient=HORIZONTAL, sashrelief=RAISED, sashwidth=6, bg='lightgrey')
    main_pane.grid(row=1, column=0, columnspan=3, rowspan=2, sticky="nsew", padx=5, pady=5)

    tree_frame = Frame(main_pane, bg="lightgrey", width=350)
    main_pane.add(tree_frame, stretch="never")

    right_pane_container = PanedWindow(
        main_pane,
        orient=VERTICAL,
        sashrelief=RAISED,
        sashwidth=6,
        bg='white'
    )
    main_pane.add(right_pane_container, stretch="always")

    tree = ttk.Treeview(tree_frame, selectmode="browse")
    tree.heading("#0", text="Duct Fitting Cases", anchor=W)
    tree.column("#0", width=320, anchor=W, stretch=YES)

    tree_vsb = Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
    tree_hsb = Scrollbar(tree_frame, orient=HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=tree_vsb.set, xscrollcommand=tree_hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    tree_vsb.grid(row=0, column=1, sticky="ns")
    tree_hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    right_top_frame = Frame(right_pane_container, height=350, bg="white")
    right_top_frame.pack_propagate(False)
    right_pane_container.add(right_top_frame, stretch="never")

    input_frame = Frame(right_top_frame, width=450, bg="#eaf4ff", bd=1, relief="sunken")
    input_frame.grid_propagate(False)
    input_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 2), pady=5)

    output_frame = Frame(right_top_frame, width=450, bg="#ffffe0", bd=1, relief="sunken")
    output_frame.grid_propagate(False)
    output_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(2, 5), pady=5)

    image_frame = Frame(right_pane_container, bg="white", bd=1, relief="groove")
    right_pane_container.add(image_frame, stretch="always")

    canvas = Canvas(image_frame, bg="#ffffff", highlightthickness=0)
    canvas.pack(fill=BOTH, expand=True, padx=5, pady=5)

    root.grid_rowconfigure(0, weight=0)
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # >>> NEW: load Excel data once at startup <<<
    load_excel_data()

    if data.empty:
        tree.insert("", "end", text="Error: Excel data not loaded.")
    else:
        # Preserve insertion order from categories_map (no sorting),
        # and prepend "A## Series:" to each category label.
        for shape, subcategories in categories_map.items():
            shape_node = tree.insert("", "end", text=shape, open=False)

            for category, ids in subcategories.items():
                prefix = CATEGORY_SERIES_PREFIX.get(category, "")
                category_label = f"{prefix}{category}"
                category_node = tree.insert(
                    shape_node, "end", text=category_label, open=False
                )

                for duct_id in ids:
                    if duct_id in duct_map:
                        details = duct_map[duct_id]
                        tree.insert(
                            category_node,
                            "end",
                            text=details["case"],
                            values=(duct_id,),
                        )
                    else:
                        print(
                            f"[WARN] Duct ID '{duct_id}' in categories_map "
                            f"but not in duct_map."
                        )

    tree.bind("<<TreeviewSelect>>", on_tree_select)
    root.update_idletasks()
    display_image()
    print("[INFO] Application started. Select a duct fitting from the list.")
    root.mainloop()
