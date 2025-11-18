
import numpy as np
import pandas as pd
from tkinter import filedialog
import importlib
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tabulate import tabulate

# File path for Excel data
file_path = "/Users/averyfleming/Documents/DPL_data.xlsx"

# Load Excel data
data = pd.read_excel(file_path, sheet_name="Master Table")
data.set_index("ID", inplace=True)  # Set index for efficient lookup

input_columns = ["input 1", "input 2", "input 3", "input 4", "input 5", "input 6", "input 7", "input 8"]
output_columns = ["output 1", "output 2", "output 3", "output 4", "output 5", "output 6", "output 7", "output 8", "output 9", "output 10"]

# Global lists to keep track of widgets and log
input_widgets = []
input_entries = []
output_widgets = []
calculation_log = []

unit_mode = "standard"  # Default mode
is_metric_mode = False  # Internal toggle flag

def convert_input_units(key, value):
    if is_metric_mode:
        key = key.lower()
        if "diameter" in key or "thickness" in key or "length" in key:
            return value / 25.4  # mm → in
        elif "velocity" in key:
            return value * 3.28084  # m/s → ft/s
        elif "flow" in key or "cfm" in key:
            return value / 1.699  # m³/hr → cfm
    return value

def convert_output_units(label, value):
    if not is_metric_mode or value is None:
        return value, label

    label_lower = label.lower()
    if "velocity" in label_lower:
        value = value / 196.8504  # ft/min → m/s
        label = label.replace("ft/min", "m/s").replace("ft/s", "m/s")
    elif "pressure" in label_lower and "in w.c." in label_lower:
        value = value * 249.08891  # in. w.c. → Pa
        label = label.replace("in w.c.", "Pa")

    return value, label

# Function to save calculation log to Excel
def save_log_to_excel():
    if not calculation_log:
        print("[INFO] No calculations to save.")
        return

    df = pd.DataFrame(calculation_log)

    # Group inputs before outputs
    input_keywords = ["entry_", "Duct ID"]
    input_cols = [col for col in df.columns if any(k in col for k in input_keywords)]
    output_cols = [col for col in df.columns if col not in input_cols]
    df = df[input_cols + output_cols]

    # Prompt user for save location
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel files", "*.xlsx")],
                                             title="Save Calculation Log As")
    if file_path:
        df.to_excel(file_path, index=False)
        print(f"[INFO] Calculation log saved to {file_path}")

def view_log_popup():
    if not calculation_log:
        print("[INFO] Log is empty.")
        return

    popup = Toplevel(root)
    popup.title("Calculation Log Preview")
    popup.geometry("1100x600")

    frame = Frame(popup, bg="white")
    frame.pack(fill=BOTH, expand=True)

    text_widget = Text(frame, wrap=NONE, bg="white", fg="black",
                       font=("Courier New", 10), padx=10, pady=10)
    text_widget.pack(side=LEFT, fill=BOTH, expand=True)

    vsb = Scrollbar(frame, orient=VERTICAL, command=text_widget.yview)
    vsb.pack(side=RIGHT, fill=Y)
    text_widget.config(yscrollcommand=vsb.set)

    hsb = Scrollbar(popup, orient=HORIZONTAL, command=text_widget.xview)
    hsb.pack(side=BOTTOM, fill=X)
    text_widget.config(xscrollcommand=hsb.set)

    try:
        df = pd.DataFrame(calculation_log)
        log_text = tabulate(df, headers='keys', tablefmt='grid', showindex=False)
    except Exception as e:
        log_text = f"[ERROR] Could not render log: {e}"

    text_widget.insert(END, log_text)
    text_widget.config(state=DISABLED)


if __name__ == "__main__":
    # Initialize the main window
    root = Tk()
    root.title("Duct Pressure Loss Calculator")
    root.lift()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)
    root.focus_force()
    root.geometry("1400x800")  # Window size

    # Maximize the window
    root.state("zoomed")  # Makes the window full screen

    # Top ribbon UI (clean modern look)
    top_ribbon = Frame(root, bg="#f0f0f0", bd=1, relief="groove")
    top_ribbon.grid(row=0, column=0, columnspan=3, sticky="ew")

    def style_button(btn):
        btn.configure(
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=7,
            bg="#ffffff",
            fg="#333333",
            activebackground="#e6e6e6",
            activeforeground="#000000",
            cursor="hand2"
        )

    save_btn = Button(top_ribbon, text="Save Log to Excel", command=save_log_to_excel)
    style_button(save_btn)
    save_btn.pack(side="left", padx=10, pady=5)

    clear_btn = Button(top_ribbon, text="Clear Log", command=lambda: calculation_log.clear())
    style_button(clear_btn)
    clear_btn.pack(side="left", padx=5, pady=5)
    view_btn = Button(top_ribbon, text="View Log", command=view_log_popup)
    def toggle_units():
        global is_metric_mode
        is_metric_mode = not is_metric_mode
        mode_label.config(text=f"Mode: {'Metric' if is_metric_mode else 'Standard'}")
        print(f"[DEBUG] Unit mode toggled to: {'Metric' if is_metric_mode else 'Standard'}")

        # Update input labels
        for widget in input_widgets:
            if isinstance(widget, Label):
                original_text = widget.cget("text")
                updated = original_text
                if is_metric_mode:
                    updated = (
                        updated.replace("(in)", "(mm)")
                            .replace("(cfm)", "(m³/h)")
                            .replace("(ft/s)", "(m/s)")
                            .replace("(ft/min)", "(m/s)")
                            .replace("(in w.c.)", "(Pa)")
                    )
                else:
                    updated = (
                        updated.replace("(mm)", "(in)")
                            .replace("(m³/h)", "(cfm)")
                            .replace("(m/s)", "(ft/min)")
                            .replace("(Pa)", "(in w.c.)")
                    )
                if updated != original_text:
                    widget.config(text=updated)
                    print(f"[DEBUG] Input label updated: '{original_text}' → '{updated}'")

        # Update output labels
        for widget in output_widgets:
            if isinstance(widget, Label):
                label_text = widget.cget("text").strip().rstrip(":")
                value = None
                try:
                    value = float(widget.cget("text"))
                except ValueError:
                    pass  # It's a label, not a value

                _, updated_label = convert_output_units(label_text, None)
                new_text = f"{updated_label}:"
                if widget.cget("text") != new_text:
                    widget.config(text=new_text)
                    print(f"[DEBUG] Output label updated: '{label_text}' → '{new_text}'")

    # Refresh output labels (if any are present)
    for widget in output_widgets:
        if isinstance(widget, Label):
            label_text = widget.cget("text")
            if ":" in label_text:
                name, unit = label_text.split(":", 1)
                new_value, new_label = convert_output_units(name.strip(), None)
                widget.config(text=f"{new_label}:")


    mode_label = Label(top_ribbon, text="Mode: Standard", bg="#f0f0f0", fg="#333333", font=("Segoe UI", 10, "bold"))
    mode_label.pack(side="right", padx=10)

    unit_toggle = Button(top_ribbon, text="Toggle Units", command=toggle_units)
    style_button(unit_toggle)
    unit_toggle.pack(side="right", padx=5)

    style_button(view_btn)
    view_btn.pack(side="left", padx=5, pady=5)

    # Frame for the Treeview on the left
    tree_frame = Frame(root, bg="lightgrey", width=350, height=800)
    tree_frame.grid(row=1, column=0, rowspan=2, sticky="nsew")
    tree_frame.grid_propagate(False)  # Prevent resizing of the frame based on its content

    tree = ttk.Treeview(tree_frame)
    tree.heading("#0", text="Categories", anchor=W)
    tree.column("#0", width=200)

    # Scrollbars for the Treeview
    tree_scrollbar_vertical = Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
    tree_scrollbar_horizontal = Scrollbar(tree_frame, orient=HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=tree_scrollbar_vertical.set, xscrollcommand=tree_scrollbar_horizontal.set)

    tree.grid(row=0, column=0, sticky="nsew")
    tree_scrollbar_vertical.grid(row=0, column=1, sticky="ns")
    tree_scrollbar_horizontal.grid(row=1, column=0, sticky="ew")

    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # Frame for the inputs on the right top
    input_frame = Frame(root, bg="lightblue", width=600, height=300)
    input_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
    input_frame.grid_propagate(False)

    # Frame for the outputs on the right top
    output_frame = Frame(root, bg="lightyellow", width=600, height=300)
    output_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
    output_frame.grid_propagate(False)

    # Frame for the image on the right bottom
    image_frame = Frame(root, bg="white", width=1200, height=600)
    image_frame.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=10, pady=10)
    image_frame.grid_propagate(False)

    # Adjust the row weights to allocate more space to the canvas
    root.grid_rowconfigure(0, weight=0)  # Top ribbon
    root.grid_rowconfigure(1, weight=1)  # Top row with input/output
    root.grid_rowconfigure(2, weight=2)  # Bottom row with canvas

    # Adjust column weights to ensure consistency
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=2)
    root.grid_columnconfigure(2, weight=2)

    # Function to clear input widgets
    def clear_inputs():
        global input_widgets, input_entries
        for widget in input_widgets:
            widget.destroy()
        input_widgets.clear()
        input_entries.clear()

    # Function to clear output widgets
    def clear_outputs():
        global output_widgets
        for widget in output_widgets:
            widget.destroy()
        output_widgets.clear()

    # Function to handle key navigation
    def bind_navigation(entry, idx):
        def focus_next(event):
            if idx + 1 < len(input_entries):
                input_entries[idx + 1].focus_set()
            return "break"

        def focus_prev(event):
            if idx - 1 >= 0:
                input_entries[idx - 1].focus_set()
            return "break"

        entry.bind("<Down>", focus_next)
        entry.bind("<Up>", focus_prev)

    # Function to store and process inputs
    def store_inputs(case_module, case_function):
        """
        Stores the values entered in input fields or selected in dropdowns.
        Dynamically generates outputs and separates them into "branch" and "main" sections when applicable.
        Supports standard, branch-main, and dual-branch-main cases.
        """
        global input_entries, output_widgets
        stored_values = {}

        try:
            for idx, entry in enumerate(input_entries):
                key = f"entry_{idx + 1}"

                if isinstance(entry, ttk.Combobox):
                    value = entry.get()
                    # Try to convert to float if it's a number; otherwise, store as string
                    try:
                        stored_values[key] = float(value)
                    except ValueError:
                        stored_values[key] = value.strip() if value else None
                else:
                    value = entry.get()
                    stored_values[key] = convert_input_units(key, float(value)) if value else None

            # Debug output for stored values
            print("[DEBUG] Stored input values:")
            for k, v in stored_values.items():
                print(f"  {k} = {v}")

            # Call the appropriate case function
            output_results = case_function(stored_values, data)

            # Clear old outputs
            clear_outputs()

            if "Error" in output_results:
                error_label = Label(
                    output_frame,
                    text=output_results["Error"],
                    bg="lightyellow",
                    fg="red",
                    font=("Arial", 12, "bold"),
                    wraplength=400,
                    justify=LEFT
                )
                error_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=10)
                output_widgets.append(error_label)
                return

            # Output Title
            title_label = Label(
                output_frame,
                text="Output",
                bg="lightyellow",
                font=("Arial", 14, "bold"),
                fg="black"
            )
            title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
            output_widgets.append(title_label)

            row_counter = 1

            # Case type detection
            output_type = getattr(case_function, "output_type", None)
            is_dual_branch_case = output_type == "dual_branch"
            is_branch_main_case = output_type == "branch_main"

            def add_output(label_text, value):
                nonlocal row_counter
                display_value, display_label = convert_output_units(label_text, value)
                output_label = Label(output_frame, text=f"{display_label}:", bg="lightyellow", fg="black", anchor="w")
                output_label.grid(row=row_counter, column=0, sticky="w", padx=10, pady=2)
                output_value = Label(output_frame, text=f"{display_value:.2f}" if display_value is not None else "N/A",
                                    bg="white", fg="black", width=20, anchor="w", relief="sunken", borderwidth=2)
                output_value.grid(row=row_counter, column=1, sticky="w", padx=10, pady=2)
                output_widgets.extend([output_label, output_value])
                row_counter += 1

            if is_dual_branch_case:
                for section in ["Branch 1", "Branch 2", "Main"]:
                    header = Label(output_frame, text=section, bg="lightyellow", font=("Arial", 12, "bold"), fg="black")
                    header.grid(row=row_counter, column=0, columnspan=2, sticky="w", padx=10, pady=5)
                    output_widgets.append(header)
                    row_counter += 1
                    for label, val in output_results.items():
                        if label.startswith(section):
                            add_output(label, val)

            elif is_branch_main_case:
                for section in ["Branch", "Main"]:
                    header = Label(output_frame, text=section, bg="lightyellow", font=("Arial", 12, "bold"), fg="black")
                    header.grid(row=row_counter, column=0, columnspan=2, sticky="w", padx=10, pady=5)
                    output_widgets.append(header)
                    row_counter += 1
                    for label, val in output_results.items():
                        if label.startswith(section):
                            add_output(label, val)

            else:
                for label, val in output_results.items():
                    if label != "Error":
                        add_output(label, val)

            # Step 3: Log inputs and outputs
            try:
                import datetime
                log_entry = {"Timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                log_entry.update(stored_values)
                log_entry.update({k: v for k, v in output_results.items() if k != "Error"})
                if "calculation_log" in globals():
                    calculation_log.append(log_entry)
                else:
                    globals()["calculation_log"] = [log_entry]
            except Exception as log_err:
                print(f"[ERROR] Failed to append to calculation_log: {log_err}")

        except Exception as e:
            print(f"[ERROR] Exception during input storage: {e}")

    def prepopulate_outputs(case_function, output_frame_ref, output_widgets_ref, clear_outputs_func):
        clear_outputs_func()

        title_label = Label(
            output_frame_ref, text="Output", bg="lightyellow",
            font=("Arial", 14, "bold"), fg="black"
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        output_widgets_ref.append(title_label)

        row_counter = 1
        output_type = getattr(case_function, "output_type", None)

        def unit(label):
            if not is_metric_mode:
                return label
            return (
                label.replace("ft/min", "m/s")
                    .replace("ft/s", "m/s")
                    .replace("in w.c.", "Pa")
            )

        section_map = {
            "dual_branch": [
                ("Branch 1", [
                    "Branch 1 Velocity (ft/min):",
                    "Branch 1 Velocity Pressure (in w.c.):",
                    "Branch 1 Loss Coefficient:",
                    "Branch 1 Pressure Loss (in w.c.):"
                ]),
                ("Branch 2", [
                    "Branch 2 Velocity (ft/min):",
                    "Branch 2 Velocity Pressure (in w.c.):",
                    "Branch 2 Loss Coefficient:",
                    "Branch 2 Pressure Loss (in w.c.):"
                ]),
                ("Main", [
                    "Main, Converged Velocity (ft/min):",
                    "Main, Converged Velocity Pressure (in w.c.):"
                ])
            ],
            "branch_main": [
                ("Branch", [
                    "Branch Velocity (ft/min):",
                    "Branch Velocity Pressure (in w.c.):",
                    "Branch Loss Coefficient:",
                    "Branch Pressure Loss (in w.c.):"
                ]),
                ("Main", [
                    "Main, Source Velocity (ft/min):",
                    "Main, Converged Velocity (ft/min):",
                    "Main, Source Velocity Pressure (in w.c.):",
                    "Main, Converged Velocity Pressure (in w.c.):",
                    "Main Loss Coefficient:",
                    "Main Pressure Loss (in w.c.):"
                ])
            ],
            "standard": [
                ("Standard", [
                    "Output 1: Velocity (ft/min):",
                    "Output 2: Velocity Pressure (in w.c.):",
                    "Output 3: Loss Coefficient:",
                    "Output 4: Pressure Loss (in w.c.):"
                ])
            ]
        }

        headers = section_map.get(output_type, section_map["standard"])

        for section_title, labels in headers:
            header = Label(output_frame_ref, text=section_title, bg="lightyellow", font=("Arial", 12, "bold"), fg="black")
            header.grid(row=row_counter, column=0, columnspan=2, sticky="w", padx=10, pady=5)
            output_widgets_ref.append(header)
            row_counter += 1

            for label in labels:
                lbl = Label(output_frame_ref, text=unit(label), bg="lightyellow", fg="black", anchor="w")
                lbl.grid(row=row_counter, column=0, sticky="w", padx=10, pady=2)
                val = Label(output_frame_ref, text="N/A", bg="white", fg="black", width=20,
                            anchor="w", relief="sunken", borderwidth=2)
                val.grid(row=row_counter, column=1, sticky="w", padx=10, pady=2)
                output_widgets_ref.extend([lbl, val])
                row_counter += 1

    def update_inputs(duct_id):
        global input_entries, input_widgets, root, data, output_frame

        print(f"[DEBUG] update_inputs() called with duct_id = {duct_id}")
        print(f"[DEBUG] Metric mode currently {'ON' if is_metric_mode else 'OFF'}")

        clear_inputs()

        # EXTRA CLEANUP if switching away from A12G
        try:
            from A12G_dynamic_inputs import clear_dynamic_inputs
            clear_dynamic_inputs(input_frame, input_entries, input_widgets)
        except Exception as e:
            print(f"[DEBUG] Skipped A12G cleanup: {e}")

        try:
            if duct_id == "A12G":
                print("[DEBUG] A12G selected — calling build_A12G_inputs()")
                from A12G_dynamic_inputs import build_A12G_inputs
                build_A12G_inputs(
                    input_frame=input_frame,
                    input_entries=input_entries,
                    input_widgets=input_widgets,
                    bind_navigation=bind_navigation,
                    store_inputs=store_inputs,
                    data=data,
                    output_frame=output_frame,
                    output_widgets=output_widgets,
                    root=root,
                    prepopulate_outputs=prepopulate_outputs,
                    clear_outputs=clear_outputs
                )
                return
        except Exception as e:
            print(f"[ERROR] A12G build failed: {e}")
            return

        try:
            if duct_id in data.index:
                print(f"[DEBUG] Loading data for {duct_id} from Excel index.")
                filtered_data = data.loc[duct_id]
                first_row = filtered_data if not isinstance(filtered_data, pd.DataFrame) else filtered_data.iloc[0]

                title_label = Label(input_frame, text="Input", bg="lightblue", fg="black", font=("Arial", 14, "bold"))
                title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
                input_widgets.append(title_label)

                entry_n_label = entry_n_field = None
                entry_t_label = entry_t_field = None
                entry_d_label = entry_d_field = None

                def place_calculate_button():
                    for widget in input_widgets:
                        if isinstance(widget, Button) and widget.cget("text") == "Calculate":
                            widget.destroy()
                            input_widgets.remove(widget)

                    calculate_row = input_frame.grid_size()[1]
                    calculate_button = Button(
                        input_frame,
                        text="Calculate",
                        command=lambda: store_inputs(case_module, case_function),
                        bg="darkblue", fg="black", font=("Arial", 14, "bold"),
                        relief="raised", bd=3, padx=5, pady=5,
                        activebackground="blue", activeforeground="blue", cursor="hand2"
                    )
                    calculate_button.grid(row=calculate_row, column=0, columnspan=2, pady=10)
                    input_widgets.append(calculate_button)
                    print("[DEBUG] Calculate button placed.")

                for idx, col in enumerate(input_columns):
                    if col in first_row and not pd.isna(first_row[col]):
                        input_label_text = str(first_row[col]).strip().lower()
                        label_display = first_row[col]

                        if is_metric_mode:
                            label_display = (
                                label_display.replace("(in)", "(mm)")
                                            .replace("(cfm)", "(m³/h)")
                                            .replace("(ft/s)", "(m/s)")
                                            .replace("(ft/min)", "(m/s)")
                                            .replace("(in w.c.)", "(Pa)")
                            )

                        print(f"[DEBUG] Creating input field: {label_display}")
                        lbl = Label(input_frame, text=f"{label_display}:", bg="lightblue", fg="black", anchor="w")
                        lbl.grid(row=idx + 1, column=0, sticky="e", padx=10, pady=2)
                        input_widgets.append(lbl)

                        dropdown_values = (
                            filtered_data[f"dropdown {idx + 1}"].dropna().unique().tolist()
                            if f"dropdown {idx + 1}" in filtered_data
                            else None
                        )

                        if dropdown_values:
                            print(f"[DEBUG] Found dropdown for input {idx + 1}: {dropdown_values}")
                            dropdown = ttk.Combobox(input_frame, values=dropdown_values, state="readonly", width=20)
                            dropdown.grid(row=idx + 1, column=1, sticky="w", padx=10, pady=2)
                            bind_navigation(dropdown, len(input_entries))
                            input_widgets.append(dropdown)
                            input_entries.append(dropdown)

                            if "obstruction" in input_label_text:
                                def on_obstruction_change(event):
                                    nonlocal entry_n_label, entry_n_field
                                    nonlocal entry_t_label, entry_t_field
                                    nonlocal entry_d_label, entry_d_field

                                    selected = dropdown.get().strip().lower()
                                    print(f"[DEBUG] Obstruction type selected: {selected}")

                                    for widget in [entry_n_label, entry_n_field, entry_t_label, entry_t_field, entry_d_label, entry_d_field]:
                                        if widget:
                                            widget.destroy()
                                            if widget in input_widgets:
                                                input_widgets.remove(widget)
                                            if widget in input_entries:
                                                input_entries.remove(widget)

                                    entry_n_label = entry_n_field = None
                                    entry_t_label = entry_t_field = None
                                    entry_d_label = entry_d_field = None

                                    row_index = input_frame.grid_size()[1]

                                    if selected == "screen":
                                        print("[DEBUG] Adding free area ratio input for screen.")
                                        entry_n_label = Label(input_frame, text="n, free area ratio:", bg="lightblue", fg="black")
                                        entry_n_label.grid(row=row_index, column=0, sticky="e", padx=10, pady=2)
                                        entry_n_field = Entry(input_frame, width=20, relief="solid", borderwidth=2,
                                                            bg="white", fg="black", highlightthickness=2,
                                                            highlightbackground="black", highlightcolor="blue")
                                        entry_n_field.grid(row=row_index, column=1, sticky="w", padx=10, pady=2)
                                        bind_navigation(entry_n_field, len(input_entries))
                                        input_widgets.extend([entry_n_label, entry_n_field])
                                        input_entries.append(entry_n_field)

                                    elif selected == "perforated plate":
                                        print("[DEBUG] Adding fields for perforated plate inputs.")
                                        widgets = [
                                            ("n, free area ratio:", entry_n_label, entry_n_field),
                                            ("plate thickness (in):", entry_t_label, entry_t_field),
                                            ("hole diameter (in):", entry_d_label, entry_d_field),
                                        ]
                                        entries = []
                                        for i, (text, label, field) in enumerate(widgets):
                                            label = Label(input_frame, text=text, bg="lightblue", fg="black")
                                            field = Entry(input_frame, width=20, relief="solid", borderwidth=2,
                                                        bg="white", fg="black", highlightthickness=2,
                                                        highlightbackground="black", highlightcolor="blue")
                                            label.grid(row=row_index + i, column=0, sticky="e", padx=10, pady=2)
                                            field.grid(row=row_index + i, column=1, sticky="w", padx=10, pady=2)
                                            bind_navigation(field, len(input_entries))
                                            input_widgets.extend([label, field])
                                            input_entries.append(field)

                                        entry_n_label, entry_n_field = widgets[0][1:]
                                        entry_t_label, entry_t_field = widgets[1][1:]
                                        entry_d_label, entry_d_field = widgets[2][1:]

                                    place_calculate_button()

                                dropdown.bind("<<ComboboxSelected>>", on_obstruction_change)

                        else:
                            print(f"[DEBUG] Adding regular entry field for: {first_row[col]}")
                            entry = Entry(input_frame, width=20, relief="solid", borderwidth=2,
                                        bg="white", fg="black",
                                        highlightthickness=2, highlightbackground="black", highlightcolor="blue")
                            entry.grid(row=idx + 1, column=1, sticky="w", padx=10, pady=2)
                            bind_navigation(entry, len(input_entries))
                            input_widgets.append(entry)
                            input_entries.append(entry)

                if input_entries:
                    print(f"[DEBUG] Total inputs created: {len(input_entries)}")
                    input_entries[0].focus_set()

                import sys
                case_module_name = f"{duct_id}_outputs"
                try:
                    if case_module_name in sys.modules:
                        importlib.reload(sys.modules[case_module_name])
                        case_module = sys.modules[case_module_name]
                    else:
                        case_module = importlib.import_module(case_module_name)

                    case_function = getattr(case_module, f"{duct_id}_outputs")

                    print(f"[DEBUG] Loaded function: {case_function.__name__}, output_type = {getattr(case_function, 'output_type', None)}")
                    prepopulate_outputs(case_function, output_frame, output_widgets, clear_outputs)
                    place_calculate_button()

                    for widget in input_widgets:
                        if isinstance(widget, Button) and widget.cget("text") == "Calculate":
                            root.unbind("<Return>")
                            root.bind("<Return>", lambda event: widget.invoke())
                            break

                except (ImportError, AttributeError) as e:
                    print(f"[ERROR] Unable to load module or function for {duct_id}: {e}")
                    return
        except Exception as e:
            print(f"[ERROR] update_inputs(): {e}")


    # Updated duct map and category structure
    duct_map = {
        # Round > Elbows
        "A7A": {"case": "Smooth Radius (Die Stamped)", "image": "smooth_radius_90_deg.png"},
        "A7B": {"case": "3 to 5 Piece, 90°", "image": "3_to_5_piece_90_deg.png"},
        "A7C": {"case": "Mitered Round", "image": "mitered_round.png"},
        # Round > Transitions (Diverging Flow)
        "A8A": {"case": "Conical Expansion", "image": "conical_expansion.png"},
        "A8C": {"case": "Round to Rectangular", "image": "round_to_rectangular_expansion.png"},
        # Round > Transitions (Converging Flow)
        "A9A1": {"case": "Conical Contraction", "image": "conical_contraction.png"},
        "A9B1": {"case": "Stepped Conical Contraction", "image": "stepped_conical_contraction.png"},
        # Round > Converging Junctions (Tees, Wyes)
        "A10A1": {"case": "Round Converging Wye", "image": "round_converging_wye.png"},
        "A10B": {"case": "Converging Tee, 90°", "image": "round_converging_tee.png"},
        "A10E": {"case": "Converging Wye, Conical", "image": "round_converging_wye_conical.png"},
        "A10I1": {"case": "Symmetrical Wye", "image": "round_converging_sym_wye.png"},
        # Round > Diverging Junctions (Tees, Wyes)
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
        # Round > Entries
        "A12A1": {"case": "Duct Mounted in Wall", "image": "entry_round_duct_mounted_in_wall.png"}, 
        "A12B": {"case": "Smooth Converging Bellmouth, without End Wall", "image": "entry_round_smooth_converging_bellmouth_without_end_wall.png"},
        "A12C": {"case": "Smooth Converging Bellmouth, with End Wall", "image": "entry_round_smooth_converging_bellmouth_with_end_wall.png"},
        "A12D1": {"case": "Conical Converging Bellmouth, without End Wall", "image": "rectangular_entry_45_bevel.png"},
        "A12E1": {"case": "Conical Converging Bellmouth, with End Wall", "image": "rectangular_entry_conical_with_end_wall.png"},
        "A12F": {"case": "Intake Hood", "image": "rectangular_entry_45_bevel.png"},
        "A12G": {"case": "Hood, Tapered, Flanged or Unflanged", "image": "entry_hood_tapered_flanged_unflanged.png"},

        # Rectangular > Elbows
        "A7D": {"case": "Mitered Rectangular", "image": "mitered_rectangular.png"},
        "A7E": {"case": "Mitered, with Converging/Diverging Flow", "image": "mitered_with_converging_diverging_flow.png"},
        "A7F": {"case": "Smooth Radius without Vanes, 90°", "image": "smooth_radius_without_vanes_90.png"},
        "A7G": {"case": "Smooth Radius with Splitter Vanes", "image": "smooth_radius_with_splitter_vanes.png"},
        "A7H1": {"case": "Mitered with Single Thickness Turning Vanes", "image": "mitered_with_single_thickness_turning_vanes.png"},
        "A7H2": {"case": "Mitered with Double Thickness Turning Vanes", "image": "mitered_with_double_thickness_turning_vanes.png"},
        "A7I": {"case": "Z-Shaped (W/H=1)", "image": "z_shaped.png"},
        "A7J": {"case": "Different Planes", "image": "different_planes.png"},
        "A7L": {"case": "Wye or Tee Shape", "image": "tee_wye_elbow.png"},
        # Rectangular > Transitions (Diverging Flow)
        "A8B": {"case": "Pyramidal Expansion", "image": "pyramidal_expansion.png"},
        "A8D": {"case": "Rectangular to Round", "image": "rectangular_to_round_expansion.png"},
        "A8E": {"case": "Rectangular, Sides Straight", "image": "rectangular_sides_straight.png"},
        "A8F": {"case": "Symmetric at Fan with Duct Sides Straight", "image": "symmetric_at_fan_with_duct_sides_straight.png"},
        "A8G": {"case": "Asymmetric at Fan with Sides Straight, Top Level", "image": "asymmetric_at_fan_with_duct_sides_straight_top_level.png"},
        "A8H": {"case": "Asymmetric at Fan with Sides Straight, Top 10° Down", "image": "asymmetric_at_fan_with_duct_sides_straight_top_10_down.png"},
        "A8I": {"case": "Asymmetric at Fan with Sides Straight, Top 10° Up", "image": "asymmetric_at_fan_with_duct_sides_straight_top_10_up.png"},
        "A8J": {"case": "Pyramidal at Fan with Duct", "image": "pyramidal_at_fan_with_duct.png"},
        # Rectangular > Transitions (Converging Flow)
        "A9A2": {"case": "Pyramidal Contraction", "image": "pyramidal_contraction.png"},
        "A9B2": {"case": "Stepped Pyramidal Contraction", "image": "stepped_pyramidal_contraction.png"},
        "A9C": {"case": "Rectangular Slot to Round", "image": "rectangular_slot_to_round.png"},
        # Rectangular > Converging Junctions (Tees, Wyes)
        "A10C": {"case": "Tee, Round Branch to Rectangular Main", "image": "converging_tee_round_branch_to_rect_main.png"},
        "A10D": {"case": "Tee, Rectangular Main & Branch", "image": "converging_tee_rect_main_and_branch.png"},
        "A10F": {"case": "Tee, 45° Entry Branch to Rectangular Main", "image": "converging_tee_rect_45_entry_branch_to_main.png"},
        "A10G": {"case": "Symmetrical Wye, Dovetail", "image": "rect_converging_wye_symmetrical_dovetail.png"},
        "A10H": {"case": "Converging Rectangular Wye", "image": "converging_curved_wye_rect.png"},
        "A10I2": {"case": "Symmetrical Wye", "image": "converging_rectangular_wye.png"},
        # Rectangular > Diverging Junctions (Tees, Wyes)
        "A11N": {"case": "Tee, 45° Rectangular Main & Branch", "image": "diverging_tee_45entry_rect_main_and_branch.png"},
        "A11O": {"case": "Tee, 45° Entry, Rectangular Main & Branch with Damper", "image": "diverging_tee_45entry_rect_main_and_branch_with_damper.png"},
        "A11P": {"case": "Tee, Rectangular Main & Branch", "image": "diverging_tee_rect_main_and_branch.png"},
        "A11Q": {"case": "Tee, Rectangular Main & Branch with Damper", "image": "diverging_tee_rect_main_and_branch_with_damper.png"},
        "A11R": {"case": "Tee, Rectangular Main & Branch with Extractor", "image": "diverging_tee_rect_main_and_branch_with_extractor.png"},
        "A11S": {"case": "Tee, Rectangular Main to Round Branch", "image": "diverging_tee_rect_main_round_branch.png"},
        "A11T": {"case": "Rectangular Wye, Main Straight", "image": "diverging_wye_rect.png"},
        "A11U": {"case": "Tee, Rectangular Main to Conical Branch", "image": "diverging_tee_rect_main_conical_branch.png"},
        "A11V": {"case": "90° Curved Rectangular Wye", "image": "diverging_wye_rect_curved_branch.png"},
        "A11W": {"case": "Symmetrical Wye, Dovetail", "image": "diverging_wye_symmetrical.png"},
        "A11X": {"case": "Symmetrical Wye", "image": "diverging_wye_symmetrical.png"},
        "A11Y": {"case": "Tee, Reducing, 45° Entry Branch", "image": "diverging_tee_rect_reducing_45entry_branch.png"},
        # Rectangular > Entries
        "A12A2": {"case": "Duct Mounted in Wall", "image": "entry_rect_duct_mounted_in_wall.png"},
        "A12D2": {"case": "Smooth Converging Bellmouth, without End Wall", "image": "entry_rect_smooth_converging_bellmouth_without_end_wall.png"},
        "A12E2": {"case": "Smooth Converging Bellmouth, with End Wall", "image": "entry_rect_smooth_converging_bellmouth_with_end_wall.png"},
    }

    categories_map = {
        "Round": {
            "Elbows": ["A7A", "A7B", "A7C"],
            "Transitions (Diverging Flow)": ["A8A", "A8C"],
            "Transitions (Converging Flow)": ["A9A1", "A9B1"],
            "Converging Junctions (Tees, Wyes)": ["A10A1", "A10B", "A10E", "A10I1"],
            "Diverging Junctions (Tees, Wyes)": ["A11A", "A11B", "A11C", "A11D", "A11E", "A11F", "A11G", "A11H", "A11I", "A11J", "A11K", "A11L", "A11M"],
            "Entries": ["A12A1", "A12B", "A12C", "A12D1", "A12E1", "A12F", "A12G"],
        },
        "Rectangular": {
            "Elbows": ["A7D", "A7E", "A7F", "A7G", "A7H1", "A7H2", "A7I", "A7J", "A7L"],
            "Transitions (Diverging Flow)": ["A8B", "A8D", "A8E", "A8F", "A8G", "A8H", "A8I", "A8J"],
            "Transitions (Converging Flow)": ["A9A2", "A9B2", "A9C"],
            "Converging Junctions (Tees, Wyes)": ["A10C", "A10D", "A10F", "A10G", "A10H", "A10I2"],
            "Diverging Junctions (Tees, Wyes)": ["A11N", "A11O", "A11P", "A11Q", "A11R", "A11S", "A11T", "A11U", "A11V", "A11W", "A11X", "A11Y"],
            "Entries": ["A12A2", "A12D2", "A12E2"],
        },
    }

    # Populate the TreeView
    for shape, subcategories in categories_map.items():
        shape_node = tree.insert("", "end", text=shape, open=False)  # Add shape node
        for category, ids in subcategories.items():
            category_node = tree.insert(shape_node, "end", text=category, open=False)  # Add category node
            for duct_id in ids:
                details = duct_map[duct_id]
                tree.insert(category_node, "end", text=details["case"], values=(duct_id,))  # Add duct case

    # Function to display images
    def display_image(image_file="jacobs_smacna_logos.png"):
        """
        Displays the specified image in the canvas. Defaults to a placeholder image.
        Dynamically centers the image in the canvas while maintaining the aspect ratio.
        """
        canvas.delete("all")  # Clear the canvas
        try:
            # Load the image
            img_path = f"/Users/averyfleming/Desktop/tkinter_proj/duct_figures/{image_file}"
            img = Image.open(img_path)

            # Get canvas dimensions
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()

            # Calculate the aspect ratio of the image and canvas
            img_width, img_height = img.size
            img_aspect_ratio = img_width / img_height
            canvas_aspect_ratio = canvas_width / canvas_height

            # Determine new dimensions while maintaining aspect ratio
            if img_aspect_ratio > canvas_aspect_ratio:
                # Image is wider than the canvas
                new_width = canvas_width
                new_height = int(new_width / img_aspect_ratio)
            else:
                # Image is taller than the canvas
                new_height = canvas_height
                new_width = int(new_height * img_aspect_ratio)

            # Resize the image
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create the PhotoImage object
            photo = ImageTk.PhotoImage(img_resized)

            # Center the image on the canvas
            x_center = (canvas_width - new_width) // 2
            y_center = (canvas_height - new_height) // 2

            canvas.create_image(x_center, y_center, image=photo, anchor=NW)
            canvas.image = photo  # Prevent garbage collection
        except Exception as e:
            # Display an error message if the image cannot be loaded
            canvas.create_text(canvas.winfo_width() // 2, canvas.winfo_height() // 2,
                            text=f"Error loading image:\n{e}", fill="red", font=("Arial", 12))

    def on_tree_select(event):
        """
        Handles the TreeView selection event. Updates the displayed image and input fields
        based on the selected duct.
        """
        selected_item = tree.focus()
        duct_id = tree.item(selected_item, "values")
        if duct_id:
            duct_id = duct_id[0]
            if duct_id in duct_map:
                display_image(duct_map[duct_id]["image"])
                update_inputs(duct_id)
        else:
            display_image("jacobs_smacna_logos.png")  # Show placeholder on invalid selection

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    # Canvas for image display
    canvas = Canvas(image_frame, bg="white")
    canvas.pack(fill=BOTH, expand=True)

    root.update_idletasks()  # Ensures the canvas dimensions are initialized
    display_image()          # Display the placeholder
    root.mainloop()          # Start the main loop