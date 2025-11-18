from tkinter import Label, Entry, Button, ttk
import importlib
from A12G_outputs import A12G_outputs
from DPL_calc_gemini import prepopulate_outputs_for_case, style_button

def clear_dynamic_inputs(frame, input_entries, input_widgets):
    for widget in frame.winfo_children():
        widget.destroy()
    input_entries.clear()
    input_widgets.clear()

def build_A12G_inputs(input_frame, input_entries, input_widgets, bind_navigation, store_inputs,
                      data, output_frame, output_widgets, root, prepopulate_outputs, clear_outputs):

    clear_dynamic_inputs(input_frame, input_entries, input_widgets)

    def show_fields_for_profile(profile):
        clear_dynamic_inputs(input_frame, input_entries, input_widgets)
        row = 0

        label_font = ("Segoe UI", 10)
        entry_font = ("Segoe UI", 10)
        label_fg = "black"
        label_bg = "#eaf4ff"
        entry_bg = "white"
        entry_border = 1

        title_label = Label(input_frame, text="Input Parameters (A12G)", bg=label_bg,
                            fg="black", font=("Segoe UI", 14, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 10))
        input_widgets.append(title_label)
        row += 1

        Label(input_frame, text="Hood Profile:", bg=label_bg, fg=label_fg,
              font=label_font).grid(row=row, column=0, sticky="e", padx=10, pady=2)
        profile_box = ttk.Combobox(input_frame, values=["round hood", "square or rectangular hood"],
                                   state="readonly", width=20, font=entry_font)
        profile_box.set(profile)
        profile_box.grid(row=row, column=1, sticky="w", padx=10, pady=2)
        input_widgets.append(profile_box)
        input_entries.append((profile_box, "Hood Profile"))
        row += 1

        if profile == "round hood":
            fields = ["D₁ (in)", "D (in)", "angle", "Q (cfm)"]
        else:
            fields = ["H₁ (in)", "W₁ (in)", "D (in)", "angle", "Q (cfm)"]

        for label_text in fields:
            Label(input_frame, text=f"{label_text}:", bg=label_bg, fg=label_fg,
                  font=label_font).grid(row=row, column=0, sticky="e", padx=10, pady=2)

            if label_text == "angle":
                angle_box = ttk.Combobox(input_frame, values=[0, 20, 40, 60, 80, 100, 120, 140, 160, 180],
                                         state="readonly", width=20, font=entry_font)
                angle_box.grid(row=row, column=1, sticky="w", padx=10, pady=2)
                input_widgets.append(angle_box)
                input_entries.append((angle_box, "angle"))
            else:
                entry = Entry(input_frame, width=20, font=entry_font, bg=entry_bg,
                              relief="solid", borderwidth=entry_border,
                              fg="black", highlightthickness=1,
                              highlightbackground="grey", highlightcolor="blue")
                entry.grid(row=row, column=1, sticky="w", padx=10, pady=2)
                bind_navigation(entry, len(input_entries))
                input_widgets.append(entry)
                input_entries.append((entry, label_text))
            row += 1

        Label(input_frame, text="Obstruction:", bg=label_bg, fg=label_fg,
              font=label_font).grid(row=row, column=0, sticky="e", padx=10, pady=2)
        obstruction_box = ttk.Combobox(input_frame, values=["none (open)", "screen"],
                                       state="readonly", width=20, font=entry_font)
        obstruction_box.grid(row=row, column=1, sticky="w", padx=10, pady=2)
        input_widgets.append(obstruction_box)
        input_entries.append((obstruction_box, "Obstruction"))
        row += 1

        n_label = Label(input_frame, text="n, free area ratio:", bg=label_bg, fg=label_fg, font=label_font)
        n_field = Entry(input_frame, width=20, font=entry_font, bg=entry_bg,
                        relief="solid", borderwidth=entry_border,
                        fg="black", highlightthickness=1,
                        highlightbackground="grey", highlightcolor="blue")

        def on_obstruction_change(event):
            if obstruction_box.get() == "screen":
                n_label.grid(row=row, column=0, sticky="e", padx=10, pady=2)
                n_field.grid(row=row, column=1, sticky="w", padx=10, pady=2)
                if (n_field, "n, free area ratio") not in input_entries:
                    input_widgets.extend([n_label, n_field])
                    input_entries.append((n_field, "n, free area ratio"))
            else:
                n_label.grid_forget()
                n_field.grid_forget()
                if (n_field, "n, free area ratio") in input_entries:
                    input_entries.remove((n_field, "n, free area ratio"))
                    input_widgets.remove(n_label)
                    input_widgets.remove(n_field)

        obstruction_box.bind("<<ComboboxSelected>>", on_obstruction_change)

        def calculate():
            store_inputs(importlib.import_module("A12G_outputs"), A12G_outputs)

        calculate_button = Button(input_frame, text="Calculate", command=calculate)
        style_button(calculate_button, bg_color="#d0e0d0", active_bg="#b0c0b0")
        calculate_button.grid(row=row + 2, column=0, columnspan=2, pady=15, ipady=2)
        input_widgets.append(calculate_button)

        profile_box.bind("<<ComboboxSelected>>", lambda e: show_fields_for_profile(profile_box.get()))

    show_fields_for_profile("round hood")
    prepopulate_outputs_for_case(A12G_outputs, output_frame, output_widgets, clear_outputs)