import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pdfplumber
import re
import os
import json
import requests
import warnings
from dotenv import load_dotenv
from PIL import Image, ImageTk
from tkcalendar import Calendar
from datetime import datetime
import pandas as pd
from openpyxl.styles import Alignment

# Load .env file side-by-side with the executable
import sys
import os
if getattr(sys, 'frozen', False):
    # Running as compiled PyInstaller executable
    app_dir = os.path.dirname(sys.executable)
else:
    # Running directly as Python script
    app_dir = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(app_dir, ".env")
load_dotenv(env_path)

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.styles.stylesheet")
warnings.filterwarnings("ignore", category=UserWarning, message=".*Could not infer format.*")

class ChecklistParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BHARTI CHECKLIST PARSER & DSR SYNC")
        
        # Maximized window with borders
        self.root.state('zoomed')

        # Nagarkot Brand Design System
        self.BRAND_BLUE  = "#1F3F6E"
        self.BRAND_RED   = "#D8232A"
        self.DARK_TEXT   = "#1E1E1E"
        self.MUTED_GRAY  = "#6B7280"
        self.LIGHT_BG    = "#F4F6F8"
        self.WHITE       = "#FFFFFF"
        self.BORDER_GRAY = "#E5E7EB"
        self.HOVER_BLUE  = "#2A528F"
        self.HOVER_RED   = "#B21D23"
        self.SUCCESS_GRN = "#15803D"
        self.WARN_AMBER  = "#B45309"

        self.root.configure(bg=self.LIGHT_BG)
        self.parsed_data = {}
        self._cal_popup  = None
        self.canvas      = None

        self.importer_options = ["BHARTI AIRTEL LIMITED", "BHARTI HEXACOM LIMITED"]
        self.importer_id_map  = {
            "BHARTI AIRTEL LIMITED":  "340763000000121483",
            "BHARTI HEXACOM LIMITED": "340763000000121527",
        }
        self.branch_options  = ["MUMBAI", "GUJARAT", "CHENNAI", "DELHI"]
        self.mode_options    = ["Air", "Sea (LCL)", "Sea (FCL)", "Sea (BB)"]
        self.port_options    = ["MUM", "NHAVA SHEVA"]
        self.be_type_options = ["SEZ-Z", "SEZ-T", "Home"]

        self.parsed_entries = {}
        self._mandatory_combos = {}
        
        # Queue state
        self.pending_checklists = []
        self.current_checklist_idx = 0

        self.setup_gui()

    # ─────────────────────────────────────────────────────────────────────────
    # GUI Setup
    # ─────────────────────────────────────────────────────────────────────────
    def setup_gui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=self.WHITE, height=80,
                          highlightthickness=1, highlightbackground=self.BORDER_GRAY)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Locate logo correctly in PyInstaller exe or dev mode
        logo_path = "logo.png"
        import sys
        if hasattr(sys, '_MEIPASS'):
            logo_path = os.path.join(sys._MEIPASS, logo_path)
            
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                ratio = 20.0 / float(img.size[1])
                w_size = max(1, int(img.size[0] * ratio))
                # Strictly enforce 20 units height per brand standard
                img = img.resize((w_size, 20), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(header, image=self.logo_img, bg=self.WHITE).place(x=30, rely=0.5, anchor=tk.W)
            except Exception as e:
                print(f"Warning: Logo failed: {e}")

        # Title Block (Absolute Center)
        title_block = tk.Frame(header, bg=self.WHITE)
        title_block.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(title_block, text="BHARTI CHECKLIST PARSER & DSR SYNC",
                 font=("Arial", 20, "bold"), fg=self.BRAND_BLUE, bg=self.WHITE).pack()

        # ── Footer ────────────────────────────────────────────────────────────
        footer = tk.Frame(self.root, bg=self.WHITE, height=40,
                          highlightthickness=1, highlightbackground=self.BORDER_GRAY)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="Nagarkot Forwarders Pvt Ltd. \u00A9",
                 font=("Arial", 10), fg=self.MUTED_GRAY, bg=self.WHITE).pack(side=tk.LEFT, padx=30)

        # ── Body Container ────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=self.LIGHT_BG, padx=40, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(body)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ── Tab Styles ────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[20, 8])

        # Tab 1: Checklist Parser
        self.tab_parser = tk.Frame(self.notebook, bg=self.LIGHT_BG)
        self.notebook.add(self.tab_parser, text="🧾 Checklist Parser")

        # Tab 2: Format DSR
        self.tab_tools = tk.Frame(self.notebook, bg=self.LIGHT_BG, padx=40, pady=30)
        self.notebook.add(self.tab_tools, text="📊 Format DSR")

        # ── Tab 1 Content ─────────────────────────────────────────────────────
        self.status_label = tk.Label(self.tab_parser, text="● Ready — upload checklist PDF(s) to begin",
                                     font=("Arial", 11), fg=self.MUTED_GRAY, bg=self.LIGHT_BG, anchor="w")
        self.status_label.pack(fill=tk.X, pady=(0, 10))

        # Upload Bar
        action_bar = tk.Frame(self.tab_parser, bg=self.LIGHT_BG)
        action_bar.pack(fill=tk.X, pady=(0, 20))

        self.btn_upload = tk.Button(action_bar, text="📁  UPLOAD CHECKLIST(S)",
                                    font=("Arial", 12, "bold"), bg=self.BRAND_BLUE, fg=self.WHITE,
                                    command=self.upload_checklists, padx=30, pady=12,
                                    borderwidth=0, relief=tk.FLAT,
                                    activebackground=self.HOVER_BLUE, activeforeground=self.WHITE)
        self.btn_upload.pack(side=tk.LEFT, expand=False)
        
        self.btn_skip = tk.Button(action_bar, text="⏭  SKIP FILE",
                                  font=("Arial", 12, "bold"), bg=self.MUTED_GRAY, fg=self.WHITE,
                                  command=self.skip_checklist, padx=30, pady=12, state=tk.DISABLED,
                                  borderwidth=0, relief=tk.FLAT,
                                  activebackground=self.BORDER_GRAY, activeforeground=self.DARK_TEXT)
        self.btn_skip.pack(side=tk.RIGHT, expand=False, padx=(15, 0))

        # Scrollable Form
        form_wrapper = tk.Frame(self.tab_parser, bg=self.LIGHT_BG)
        form_wrapper.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(form_wrapper, bg=self.LIGHT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_wrapper, orient="vertical", command=self.canvas.yview)
        
        # The form content frame (with white background like a card)
        self.form_frame = tk.Frame(self.canvas, bg=self.WHITE, padx=40, pady=30,
                                   highlightthickness=1, highlightbackground=self.BORDER_GRAY)
        self.form_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Center the form_frame inside the canvas
        canvas_frame_id = self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        def resize_frame(e):
            self.canvas.itemconfig(canvas_frame_id, width=e.width)
        self.canvas.bind("<Configure>", resize_frame)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.build_form_content()

    def build_form_content(self):
        row = 0
        self.form_frame.columnconfigure(1, weight=1)
        self.form_frame.columnconfigure(3, weight=1)

        # ── Section: Parsed Checklist Data ────────────────────────────────────
        self._section_label(row, "PARSED CHECKLIST DATA")
        row += 1

        left_fields  = [("Job_No", "Job No:"), ("Invoice_Number", "Invoice No(s):"),
                        ("Total_Inv_Value", "Total Inv Value:"), ("Model", "Model(s):")]
        right_fields = [("BE_Type", "BE Type:"), ("Invoice_Date", "Invoice Date(s):"),
                        ("Supplier_Exporter", "Supplier / Exporter:"), ("Product_Qty", "Qty(s):")]

        style = ttk.Style()
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)
        # Prevents grayed-out look on disabled/readonly comboboxes
        style.map('TCombobox', fieldbackground=[('readonly', self.WHITE)], selectbackground=[('readonly', self.WHITE)], selectforeground=[('readonly', self.DARK_TEXT)])
        
        # Globally disable mousewheel scrolling on comboboxes to prevent accidental changes
        self.root.bind_class("TCombobox", "<MouseWheel>", lambda e: "break")

        for (lk, ll), (rk, rl) in zip(left_fields, right_fields):
            tk.Label(self.form_frame, text=ll, bg=self.WHITE, font=("Arial", 10, "bold")).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=8)
            le = ttk.Entry(self.form_frame, font=("Arial", 10))
            le.grid(row=row, column=1, sticky="we", padx=(0, 30), pady=8)
            self.parsed_entries[lk] = le

            tk.Label(self.form_frame, text=rl, bg=self.WHITE, font=("Arial", 10, "bold")).grid(
                row=row, column=2, sticky="w", padx=(0, 10), pady=8)
            if rk == "BE_Type":
                rw = ttk.Combobox(self.form_frame, values=self.be_type_options, state="readonly", font=("Arial", 10))
            else:
                rw = ttk.Entry(self.form_frame, font=("Arial", 10))
            rw.grid(row=row, column=3, sticky="we", pady=8)
            self.parsed_entries[rk] = rw
            row += 1

        tk.Label(self.form_frame, text="Description:", bg=self.WHITE, font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="nw", pady=8)
        desc_frame = tk.Frame(self.form_frame, bg=self.WHITE)
        desc_frame.grid(row=row, column=1, columnspan=3, sticky="we", pady=8)
        desc_widget = tk.Text(desc_frame, height=4, width=80, font=("Arial", 10), bd=1, relief=tk.SOLID)
        desc_scroll = ttk.Scrollbar(desc_frame, command=desc_widget.yview)
        desc_widget.configure(yscrollcommand=desc_scroll.set)
        desc_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.parsed_entries["Description"] = desc_widget
        row += 1

        self._separator(row); row += 1

        # ── Section: Manual Fields ────────────────────────────────────────────
        self._section_label(row, "MANUAL FIELDS")
        row += 1

        # HAWB / HBL
        tk.Label(self.form_frame, text="HAWB / HBL:", bg=self.WHITE, font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=(8, 10))
        self.entry_hawb = ttk.Entry(self.form_frame, font=("Arial", 10))
        self.entry_hawb.grid(row=row, column=1, sticky="we", padx=(0, 30), pady=(8, 10))

        tk.Label(self.form_frame, text="MAWB / MBL:", bg=self.WHITE, font=("Arial", 10, "bold")).grid(
            row=row, column=2, sticky="w", padx=(0, 10), pady=(8, 10))
        self.entry_mawb = ttk.Entry(self.form_frame, font=("Arial", 10))
        self.entry_mawb.grid(row=row, column=3, sticky="we", pady=(8, 10))
        row += 1

        # ETA
        self._mandatory_label("ETA:", row, 0)
        
        eta_outer = tk.Frame(self.form_frame, bg=self.WHITE, highlightthickness=1, highlightbackground=self.BORDER_GRAY, bd=0)
        eta_outer.grid(row=row, column=1, sticky="we", padx=(0, 30), pady=10)
        
        self.entry_eta = tk.Entry(eta_outer, font=("Arial", 10), bd=0, highlightthickness=0, bg=self.WHITE)
        self.entry_eta.insert(0, "dd-MMM-yyyy")
        self.entry_eta.config(fg="#A0AAB5")
        
        def handle_eta_focus_in(e):
            if self.entry_eta.get() == "dd-MMM-yyyy":
                self.entry_eta.delete(0, tk.END)
                self.entry_eta.config(fg=self.DARK_TEXT)
        def handle_eta_focus_out(e):
            if not self.entry_eta.get().strip():
                self.entry_eta.insert(0, "dd-MMM-yyyy")
                self.entry_eta.config(fg="#A0AAB5")
                
        self.entry_eta.bind("<FocusIn>", handle_eta_focus_in)
        self.entry_eta.bind("<FocusOut>", handle_eta_focus_out)
        self.entry_eta.bind("<Button-1>", lambda e: self._toggle_calendar(force_open=True), add="+")
        self.entry_eta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        self.btn_cal = tk.Button(eta_outer, text="🗓", font=("Arial", 12), bg=self.WHITE, fg=self.BRAND_BLUE,
                                 activebackground=self.WHITE, bd=0, highlightthickness=0, relief=tk.FLAT,
                                 cursor="hand2", command=self._toggle_calendar)
        self.btn_cal.pack(side=tk.RIGHT, padx=4)
        row += 1

        # Importer + Branch
        self._mandatory_label("Importer:", row, 0)
        self.combo_importer = ttk.Combobox(self.form_frame, values=self.importer_options, state="readonly", font=("Arial", 10))
        self.combo_importer.grid(row=row, column=1, sticky="we", padx=(0, 30), pady=10)
        self._mandatory_combos["Importer"] = self.combo_importer

        self._mandatory_label("Branch:", row, 2)
        self.combo_branch = ttk.Combobox(self.form_frame, values=self.branch_options, state="readonly", font=("Arial", 10))
        self.combo_branch.grid(row=row, column=3, sticky="we", pady=10)
        self._mandatory_combos["Branch"] = self.combo_branch
        row += 1

        # Mode + Port
        self._mandatory_label("Mode:", row, 0)
        self.combo_mode = ttk.Combobox(self.form_frame, values=self.mode_options, state="readonly", font=("Arial", 10))
        self.combo_mode.grid(row=row, column=1, sticky="we", padx=(0, 30), pady=10)
        self._mandatory_combos["Mode"] = self.combo_mode

        self._mandatory_label("Port:", row, 2)
        self.combo_port = ttk.Combobox(self.form_frame, values=self.port_options, font=("Arial", 10))
        self.combo_port.set("MUM")
        self.combo_port.grid(row=row, column=3, sticky="we", pady=10)
        self._mandatory_combos["Port"] = self.combo_port
        row += 1

        # Push button summary & action
        self.summary_label = tk.Label(self.form_frame, text="", font=("Arial", 10), fg=self.MUTED_GRAY, bg=self.WHITE, anchor="w")
        self.summary_label.grid(row=row, column=0, columnspan=4, sticky="we", pady=(15, 5))
        row += 1

        self.btn_send = tk.Button(self.form_frame, text="PUSH TO SHAKTI PRE-ALERT", font=("Arial", 12, "bold"),
                                  bg=self.BRAND_BLUE, fg=self.WHITE, command=self.send_to_zoho, state=tk.DISABLED,
                                  pady=12, relief=tk.FLAT, activebackground=self.HOVER_BLUE, activeforeground=self.WHITE)
        self.btn_send.grid(row=row, column=0, columnspan=4, pady=(0, 15), sticky="we")
        row += 1

        self.build_tools_content()

    def build_tools_content(self):
        # ── Section: DSR Excel Formatter ──────────────────────────────────────
        lbl_dsr = tk.Label(self.tab_tools, text="DSR EXCEL FORMATTER", font=("Arial", 14, "bold"), fg=self.BRAND_BLUE, bg=self.LIGHT_BG)
        lbl_dsr.pack(anchor="w", pady=(0, 10))

        tk.Label(self.tab_tools, bg=self.LIGHT_BG, fg=self.MUTED_GRAY, font=("Arial", 10), justify="left",
                 text="Formats standard exported Zoho tabular reports into the required column layout\nwith safe DD-MMM-YYYY date parsing.").pack(anchor="w", pady=(0, 15))

        self.btn_format_dsr = tk.Button(self.tab_tools, text="⬇  SELECT & FORMAT DSR EXCEL", font=("Arial", 12, "bold"),
                                        bg=self.BRAND_RED, fg=self.WHITE, command=self.format_dsr_excel,
                                        pady=12, relief=tk.FLAT, activebackground=self.HOVER_RED, activeforeground=self.WHITE)
        self.btn_format_dsr.pack(fill=tk.X, pady=(0, 10))

        self.dsr_result_label = tk.Label(self.tab_tools, text="Last formatted: —", font=("Arial", 10), fg=self.MUTED_GRAY, bg=self.LIGHT_BG, anchor="w")
        self.dsr_result_label.pack(anchor="w", pady=(0, 20))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _section_label(self, row, text):
        tk.Label(self.form_frame, text=text, font=("Arial", 14, "bold"), fg=self.BRAND_BLUE, bg=self.WHITE).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(15, 10))

    def _separator(self, row):
        f = tk.Frame(self.form_frame, bg=self.BORDER_GRAY, height=2)
        f.grid(row=row, column=0, columnspan=4, sticky="we", pady=20)

    def _mandatory_label(self, text, r, c):
        frm = tk.Frame(self.form_frame, bg=self.WHITE)
        frm.grid(row=r, column=c, sticky="w", padx=(0, 10), pady=10)
        tk.Label(frm, text=text, bg=self.WHITE, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(frm, text=" *", bg=self.WHITE, font=("Arial", 14, "bold"), fg=self.BRAND_RED).pack(side=tk.LEFT)

    def _set_status(self, text, colour=None):
        self.status_label.config(text=text, fg=colour or self.MUTED_GRAY)
        self.root.update_idletasks()

    def _reset_form(self):
        for key, widget in self.parsed_entries.items():
            if isinstance(widget, tk.Text): widget.delete("1.0", tk.END)
            elif isinstance(widget, ttk.Combobox): widget.set("")
            else: widget.delete(0, tk.END)
        self.entry_hawb.delete(0, tk.END)
        self.entry_mawb.delete(0, tk.END)
        
        self.entry_eta.delete(0, tk.END)
        self.entry_eta.insert(0, "dd-MMM-yyyy")
        self.entry_eta.config(fg="#A0AAB5")
        
        self.parsed_data = {}
        self.summary_label.config(text="")
        if self.current_checklist_idx < len(self.pending_checklists) - 1 and self.pending_checklists:
            self.btn_send.config(state=tk.DISABLED, text=f"PUSH & NEXT ({self.current_checklist_idx+1}/{len(self.pending_checklists)})")
        else:
            self.btn_send.config(state=tk.DISABLED, text="PUSH TO SHAKTI PRE-ALERT")

        if not self.pending_checklists:
            self.btn_upload.config(text="📁  UPLOAD CHECKLIST(S)", bg=self.BRAND_BLUE)
            self.btn_skip.config(state=tk.DISABLED)
        else:
            self.btn_skip.config(state=tk.NORMAL)

        self.canvas.yview_moveto(0)

    def _toggle_calendar(self, force_open=False):
        if self._cal_popup and self._cal_popup.winfo_exists():
            if force_open:
                return
            self._cal_popup.destroy()
            self._cal_popup = None
            if hasattr(self, '_cal_click_id'):
                try: self.root.unbind("<Button-1>", self._cal_click_id)
                except: pass
            return

        top = tk.Toplevel(self.root)
        self._cal_popup = top
        top.overrideredirect(True)
        top.attributes("-topmost", True)

        x = self.btn_cal.winfo_rootx()
        y = self.btn_cal.winfo_rooty() + self.btn_cal.winfo_height() + 5
        top.geometry(f"+{x}+{y}")

        cal_bg = tk.Frame(top, bg=self.BORDER_GRAY, padx=1, pady=1)
        cal_bg.pack()

        cal_kwargs = {
            'selectmode': 'day', 'date_pattern': 'dd-mm-yyyy',
            'headersbackground': self.BRAND_BLUE, 'headersforeground': self.WHITE,
            'selectbackground': self.BRAND_RED, 'selectforeground': self.WHITE
        }

        existing = self.entry_eta.get().strip()
        if existing:
            try:
                dt = datetime.strptime(existing, "%d-%m-%Y")
                cal_kwargs.update(year=dt.year, month=dt.month, day=dt.day)
            except ValueError: pass

        cal = Calendar(cal_bg, **cal_kwargs)
        cal.pack()

        def on_date_selected(e):
            self.entry_eta.delete(0, tk.END)
            self.entry_eta.insert(0, cal.get_date())
            self.entry_eta.config(fg=self.DARK_TEXT)
            top.destroy()
            self._cal_popup = None
            if hasattr(self, '_cal_click_id'):
                try: self.root.unbind("<Button-1>", self._cal_click_id)
                except: pass
        cal.bind("<<CalendarSelected>>", on_date_selected)

        def on_click_outside(e):
            if not (self._cal_popup and self._cal_popup.winfo_exists()):
                return
            if str(e.widget).startswith(str(top)): return
            if e.widget == self.entry_eta or e.widget == self.btn_cal: return
            
            top.destroy()
            self._cal_popup = None
            if hasattr(self, '_cal_click_id'):
                try: self.root.unbind("<Button-1>", self._cal_click_id)
                except: pass
                
        self._cal_click_id = self.root.bind("<Button-1>", on_click_outside, add="+")

    # ── PDF Parsing ───────────────────────────────────────────────────────────
    def upload_checklists(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if not files: return
        self.pending_checklists = list(files)
        self.current_checklist_idx = 0
        self.load_next_checklist()

    def load_next_checklist(self):
        if self.current_checklist_idx >= len(self.pending_checklists):
            self.pending_checklists = []
            self.current_checklist_idx = 0
            self._reset_form()
            self._set_status("✔ All checklists processed!", self.SUCCESS_GRN)
            messagebox.showinfo("Done", "All checklists in the queue have been processed.")
            return

        file_path = self.pending_checklists[self.current_checklist_idx]
        fname = os.path.basename(file_path)
        self._reset_form()
        
        status_text = f" ({self.current_checklist_idx+1}/{len(self.pending_checklists)})"
        self._set_status(f"● Parsing {fname}{status_text}...", self.WARN_AMBER)
        self.btn_upload.config(text=f"📁 Queue: {len(self.pending_checklists)} file(s)", bg=self.MUTED_GRAY)
        self.btn_skip.config(state=tk.NORMAL)
        self.root.update()

        try:
            data = self.extract_data(file_path)
            self.parsed_data = data

            for key, widget in self.parsed_entries.items():
                if key in data and key != "Description":
                    val = str(data[key])
                    if isinstance(widget, ttk.Combobox): widget.set(val)
                    else: 
                        widget.delete(0, tk.END)
                        widget.insert(0, val)

            if "Subform_Rows" in data:
                invoices, dates, vals, models, qtys, descs = [], [], [], [], [], []
                for r in data["Subform_Rows"]:
                    if r["Invoice_Number"] not in invoices:
                        invoices.append(r["Invoice_Number"])
                        dates.append(r["Invoice_Date"])
                        vals.append(r["Total_Inv_Value"])
                    models.append(r["Model_No"])
                    qtys.append(str(r["Product_Qty"]))
                    descs.append(r["Item_Description"])

                self.parsed_entries["Invoice_Number"].delete(0, tk.END)
                self.parsed_entries["Invoice_Number"].insert(0, ", ".join(invoices))
                self.parsed_entries["Invoice_Date"].delete(0, tk.END)
                self.parsed_entries["Invoice_Date"].insert(0, ", ".join(dates))
                self.parsed_entries["Total_Inv_Value"].delete(0, tk.END)
                self.parsed_entries["Total_Inv_Value"].insert(0, ", ".join(vals))
                self.parsed_entries["Model"].delete(0, tk.END)
                self.parsed_entries["Model"].insert(0, ", ".join(list(set(models))))
                self.parsed_entries["Product_Qty"].delete(0, tk.END)
                self.parsed_entries["Product_Qty"].insert(0, ", ".join(qtys))
                self.parsed_entries["Description"].delete("1.0", tk.END)
                self.parsed_entries["Description"].insert("1.0", "\n".join(descs))

            self.entry_hawb.delete(0, tk.END)
            self.entry_hawb.insert(0, data.get("HAWB_HBL", ""))
            self.entry_mawb.delete(0, tk.END)
            self.entry_mawb.insert(0, data.get("MAWB_MBL", ""))
            # Removed Mode autofill per user request
            
            imp = data.get("Checklist_Importer_Raw", "").upper()
            if "AIRTEL" in imp: self.combo_importer.set("BHARTI AIRTEL LIMITED")
            elif "HEXACOM" in imp: self.combo_importer.set("BHARTI HEXACOM LIMITED")

            self.summary_label.config(text=f"Ready to send: Job {data.get('Job_No','—')} | {len(data.get('Subform_Rows',[]))} items", fg=self.DARK_TEXT)
            
            btn_txt = f"PUSH & NEXT{status_text}" if self.current_checklist_idx < len(self.pending_checklists) - 1 else "PUSH TO SHAKTI PRE-ALERT"
            self.btn_send.config(state=tk.NORMAL, text=btn_txt)
            self.canvas.yview_moveto(0)
            self._set_status(f"✔ Parsed: {fname} — Job {data.get('Job_No','—')}", self.SUCCESS_GRN)

        except Exception as e:
            self._set_status(f"✖ Parse failed: {e}", self.BRAND_RED)
            ans = messagebox.askyesno("Parse Error", f"Failed to parse {fname}\nError: {e}\n\nSkip to next file?")
            if ans:
                self.current_checklist_idx += 1
                self.load_next_checklist()
            else:
                self.btn_send.config(state=tk.DISABLED)

    def skip_checklist(self):
        self.current_checklist_idx += 1
        self.load_next_checklist()

    def extract_data(self, pdf_path):
        page_texts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_texts.append(page.extract_text() or "")
        text_all = "\n".join(page_texts)

        job_no = ""
        m = re.search(r'Job\s*No\s+(?:[A-Z]+/)?(\d+)/[\d\-]+', text_all, re.IGNORECASE)
        if m: job_no = m.group(1)

        be_type = ""
        m = re.search(r'BILL\s+OF\s+ENTRY\s+FOR\s+([A-Z\-]+)', text_all, re.IGNORECASE)
        if m: 
            be_type = m.group(1).upper()
            if be_type == "HOME": be_type = "Home"

        mode, port = "", "MUM"
        m = re.search(r'Port\s+of\s+Reporting\s+(.+)', text_all, re.IGNORECASE)
        if m:
            rep = m.group(1).upper()
            if "NHAVA" in rep or "MUMBAI" in rep: port = "MUM"
            if "AIR" in rep: mode = "Air"
            elif re.search(r'\bFCL\b', text_all): mode = "Sea (FCL)"
            elif re.search(r'\bLCL\b', text_all): mode = "Sea (LCL)"
            elif re.search(r'\bBB\b',  text_all): mode = "Sea (BB)"
            else: mode = "Sea (LCL)"

        supplier = ""
        m = re.search(r'Supplier\s*Name\s+(.+)', text_all, re.IGNORECASE)
        if m: supplier = m.group(1).strip()

        hawb = mawb = ""
        m_h = re.search(r'(?:HAWB|HBL)\s*(?:No\.?)?\s*[:\s]\s*(\S+)', text_all, re.IGNORECASE)
        if m_h and re.search(r'\d', m_h.group(1)): hawb = m_h.group(1).strip()
        m_m = re.search(r'(?:MAWB|MBL)\s*(?:No\.?)?\s*[:\s]\s*(\S+)', text_all, re.IGNORECASE)
        if m_m and re.search(r'\d', m_m.group(1)): mawb = m_m.group(1).strip()
        if not mawb:
            m = re.search(r'(?<!H)(?<!M)BL\s*No\.?\s*[:\s]\s*(\S+)', text_all, re.IGNORECASE)
            if m and re.search(r'\d', m.group(1)): mawb = m.group(1).strip()

        if mode == "Air" and mawb:
            clean = re.sub(r'[^0-9]', '', mawb)
            if len(clean) == 11: mawb = f"{clean[:3]}-{clean[3:]}"

        importer_raw = ""
        m = re.search(r'M/S\.\s+(.+)', text_all)
        if m: importer_raw = m.group(1).strip()

        invoice_headers = []
        idx = 1
        for block in text_all.split("Invoice Detail")[1:]:
            m_nd = re.search(r'Inv\s*No\s*&\s*Date\s+(\S+)\s+dt\.\s+(\S+)', block, re.IGNORECASE)
            m_v  = re.search(r'Invoice\s*Value\s+([\d,]+\.[\d]+)', block, re.IGNORECASE)
            if m_nd:
                invoice_headers.append({
                    "idx": str(idx), "num": m_nd.group(1), "date": m_nd.group(2),
                    "val": m_v.group(1).replace(",","").split(".")[0] if m_v else "0"
                })
                idx += 1

        sw_items = []
        sw_match = re.search(r'SINGLE\s+WINDOW\s*-\s*Additional\s+Product\s+Information(.*?)DUTY\s+Details', text_all, re.DOTALL | re.IGNORECASE)
        if sw_match:
            for m2 in re.finditer(r'(\d+)\s+(\d+)\s+Item\s+Characteristics\s+Standard\s+UQC\s+([\d\.]+)\s+NOS', sw_match.group(1), re.IGNORECASE):
                sw_items.append({"inv_idx": m2.group(1), "item_idx": m2.group(2), "qty": int(float(m2.group(3)))})

        item_desc_map = {}
        for m2 in re.finditer(r'^\s*(\d+)\s+\d{8}\s+(.+?)(?=\n\s*[\d\.]+\s+[\d\.]+\s+\d{8}|\n\s*AIDC)', text_all, re.MULTILINE | re.DOTALL):
            slot = m2.group(1)
            desc = re.sub(r'\s+', ' ', m2.group(2)).strip()
            item_desc_map[slot] = desc

        subform_rows = []
        for sw in sw_items:
            inv = next((i for i in invoice_headers if i["idx"] == sw["inv_idx"]), None)
            if inv:
                full_desc = item_desc_map.get(sw["item_idx"], "")
                model = full_desc.split()[0] if full_desc else ""
                try:
                    formatted_date = datetime.strptime(inv["date"], "%d-%b-%Y").strftime("%d-%b-%Y").upper()
                except: formatted_date = inv["date"]
                subform_rows.append({
                    "Invoice_Number": inv["num"], "Invoice_Date": formatted_date,
                    "Total_Inv_Value": str(inv["val"]), "Product_Qty": str(sw["qty"]),
                    "Model_No": model, "Item_Description": full_desc
                })

        return {
            "Job_No": job_no, "HAWB_HBL": hawb, "MAWB_MBL": mawb,
            "Checklist_Importer_Raw": importer_raw, "Supplier_Exporter": supplier,
            "Mode": mode, "BE_Type": be_type, "Port": port, "Subform_Rows": subform_rows
        }

    # ── Zoho & API ───────────────────────────────────────────────────────────
    def refresh_zoho_token(self):
        r = requests.post("https://accounts.zoho.in/oauth/v2/token", params={
            "refresh_token": os.environ.get("ZOHO_REFRESH_TOKEN"),
            "client_id": os.environ.get("ZOHO_CLIENT_ID"),
            "client_secret": os.environ.get("ZOHO_CLIENT_SECRET"),
            "grant_type": "refresh_token"})
        if r.status_code == 200 and "access_token" in r.json():
            token = r.json()["access_token"]
            with open("zoho_token.json", "w") as f:
                json.dump({"access_token": token, "refresh_token": os.environ.get("ZOHO_REFRESH_TOKEN")}, f, indent=4)
            return token
        return None



    def send_to_zoho(self):
        eta_str = self.entry_eta.get().strip()
        if eta_str == "dd-MMM-yyyy":
            eta_str = ""
            
        eta_formatted = ""
        if eta_str:
            try:
                eta_formatted = datetime.strptime(eta_str, "%d-%m-%Y").strftime("%d-%b-%Y").upper()
            except:
                messagebox.showwarning("Invalid ETA", "Use dd-mm-yyyy")
                return

        importer = self.combo_importer.get()
        branch   = self.combo_branch.get()
        mode     = self.combo_mode.get()
        port     = self.combo_port.get()

        # GUI validations removed so users can leave fields blank when updating existing jobs.

        # Zoho Validation & Sanitization
        raw_hawb = self.entry_hawb.get().strip()
        raw_mawb = self.entry_mawb.get().strip()

        hawb_clean = re.sub(r'[^A-Za-z0-9,]', '', raw_hawb).strip(',')

        if mode == "Air":
            mawb_clean = re.sub(r'[^0-9]', '', raw_mawb)
            if len(mawb_clean) == 11:
                mawb_clean = f"{mawb_clean[:3]}-{mawb_clean[3:]}"
            elif len(mawb_clean) == 12 and raw_mawb[3] == '-':
                mawb_clean = raw_mawb
            elif raw_mawb:
                messagebox.showwarning("Invalid MAWB Format", "For Air mode, MAWB must be exactly 11 numeric digits (e.g. 123-98765432).")
                return
        else:
            mawb_clean = re.sub(r'[^A-Za-z0-9]', '', raw_mawb)

        payload = {
            "data": {
                "Job_No": self.parsed_entries["Job_No"].get().strip(),
                "HAWB_HBL": hawb_clean,
                "MAWB_MBL": mawb_clean,
                "ETA": eta_formatted,
                "Importer": self.importer_id_map.get(importer, ""),
                "Branch": branch, "Mode": mode, "Port_Airtel": port,
                "BE_Type": self.parsed_entries["BE_Type"].get(),
                "Supplier_Exporter": self.parsed_entries["Supplier_Exporter"].get().strip(),
                "Added_By": os.getlogin(),
                "Airtel_DSR": self.parsed_data.get("Subform_Rows", [])
            }
        }

        self._set_status("● Sending to Zoho...", self.WARN_AMBER)
        self.btn_send.config(text="SENDING...", state=tk.DISABLED)
        self.root.update()
        
        # DEBUG LOGGING: Save the exact payload to a text file for inspection
        with open("last_zoho_payload.json", "w") as dbg_file:
            json.dump(payload, dbg_file, indent=4)
        
        try:
            owner = os.environ.get("ZOHO_ACCOUNT_OWNER")
            app = os.environ.get("ZOHO_APP_NAME")
            url = f"https://creator.zoho.in/api/v2/{owner}/{app}/form/Pre_Alert"
            report_url = f"https://creator.zoho.in/api/v2/{owner}/{app}/report/View_All_Jobs"
            
            token = None
            if os.path.exists("zoho_token.json"):
                with open("zoho_token.json") as f: token = json.load(f).get("access_token")
            if not token: token = self.refresh_zoho_token()
            
            if token:
                # Normalization helper for insensitive/punctuation-free matching
                def normalize_str(s):
                    return re.sub(r'[^A-Za-z0-9]', '', str(s)).upper() if s else ""

                parsed_hawb_norm = normalize_str(raw_hawb)
                parsed_mawb_norm = normalize_str(raw_mawb)
                parsed_job_norm = normalize_str(payload["data"]["Job_No"])

                # Build OR search using exact == matches (proven Zoho V2 API syntax).
                # Python-side normalization handles case/punctuation differences.
                criteria_parts = []
                if hawb_clean:
                    criteria_parts.append(f'(HAWB_HBL == "{hawb_clean}")')
                if mawb_clean:
                    criteria_parts.append(f'(MAWB_MBL == "{mawb_clean}")')
                if payload["data"]["Job_No"]:
                    criteria_parts.append(f'(Job_No == {payload["data"]["Job_No"]})')
                
                if not criteria_parts:
                    criteria_str = '(Job_No == "")'
                else:
                    criteria_str = " || ".join(criteria_parts)

                search_params = {"criteria": criteria_str}
                
                self._set_status(f"● Searching Zoho for matching record...", self.WARN_AMBER)
                self.root.update()
                
                # DEBUG: Log the criteria being sent
                print(f"[DEBUG] Search criteria: {criteria_str}")
                
                search_resp = requests.get(report_url, headers={"Authorization": f"Zoho-oauthtoken {token}"}, params=search_params)
                if search_resp.status_code == 401:
                    token = self.refresh_zoho_token()
                    search_resp = requests.get(report_url, headers={"Authorization": f"Zoho-oauthtoken {token}"}, params=search_params)
                
                # DEBUG: Log search response for diagnosis
                print(f"[DEBUG] Search HTTP {search_resp.status_code}: {search_resp.text[:500]}")
                
                existing_id = None
                existing_record = {}
                
                if search_resp.status_code == 200:
                    s_data = search_resp.json().get("data", [])
                    # Python-side matching: Case insensitive, punctuation removed.
                    # Priority 1: HAWB match. Priority 2: MAWB match. Priority 3: Job No match.
                    for record in s_data:
                        z_hawb = normalize_str(record.get("HAWB_HBL"))
                        z_mawb = normalize_str(record.get("MAWB_MBL"))
                        z_job  = normalize_str(record.get("Job_No"))
                        
                        if parsed_hawb_norm and parsed_hawb_norm == z_hawb:
                            existing_record = record
                            existing_id = record.get("ID")
                            print(f"[DEBUG] Matched by HAWB: {parsed_hawb_norm} == {z_hawb}")
                            break
                        elif parsed_mawb_norm and parsed_mawb_norm == z_mawb:
                            existing_record = record
                            existing_id = record.get("ID")
                            print(f"[DEBUG] Matched by MAWB: {parsed_mawb_norm} == {z_mawb}")
                            break
                        elif parsed_job_norm and parsed_job_norm == z_job:
                            existing_record = record
                            existing_id = record.get("ID")
                            print(f"[DEBUG] Matched by Job No: {parsed_job_norm} == {z_job}")
                            break
                    
                    if not existing_id:
                        print(f"[DEBUG] No Python-side match found. Candidates returned: {len(s_data)}")
                elif search_resp.status_code != 200:
                    # Surface the search error visually instead of silently creating a new record
                    print(f"[WARN] Zoho search failed with HTTP {search_resp.status_code}")
                    self._set_status(f"⚠ Search returned HTTP {search_resp.status_code} — falling through to create", self.WARN_AMBER)
                    self.root.update()

                if existing_id:
                    matched_by = "HAWB/MAWB" if not existing_record.get("Job_No") else "Job No"
                    self._set_status(f"● Updating Record {existing_id} ({matched_by} match)...", self.WARN_AMBER)
                    self.root.update()
                    
                    # Create a non-destructive payload
                    safe_payload_data = {}
                    for key, val in payload["data"].items():
                        if key == "Airtel_DSR":
                            safe_payload_data[key] = val
                            continue
                            
                        # Check what Zoho already has
                        z_val = existing_record.get(key)
                        
                        # If the value in Zoho is completely empty, it is safe to push our new value
                        # This ensures the Job_No gets pushed if it was missing!
                        if not z_val or z_val == "null" or str(z_val).strip() == "":
                            safe_payload_data[key] = val
                            
                    safe_payload = {"data": safe_payload_data}
                    
                    patch_url = f"{report_url}/{existing_id}"
                    resp = requests.patch(patch_url, headers={"Authorization": f"Zoho-oauthtoken {token}"}, json=safe_payload, timeout=15)
                    action_msg = "Updated existing record in"
                else:
                    self._set_status(f"● Creating new Job record...", self.WARN_AMBER)
                    self.root.update()
                    resp = requests.post(url, headers={"Authorization": f"Zoho-oauthtoken {token}"}, json=payload, timeout=15)
                    action_msg = "Created new record in"

                if resp.status_code in (200, 201) and resp.json().get("code") == 3000:
                    self._set_status(f"✔ {action_msg} Shakti Pre-Alert", self.SUCCESS_GRN)
                    
                    # Log successful submission to CSV locally
                    log_file = "prealert_submission_log.csv"
                    file_exists = os.path.isfile(log_file)
                    try:
                        import csv
                        with open(log_file, "a", newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(["Timestamp", "Job_No", "HAWB_HBL", "MAWB_MBL", "Importer", "ETA", "Mode"])
                            writer.writerow([
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                payload["data"]["Job_No"],
                                payload["data"]["HAWB_HBL"],
                                payload["data"]["MAWB_MBL"],
                                importer,  # log the human-readable importer name from the UI
                                payload["data"]["ETA"],
                                payload["data"]["Mode"]
                            ])
                    except Exception as e: print(f"Log Error: {e}")
                    
                    messagebox.showinfo("Success", f"{action_msg} Shakti Pre-Alert.")
                    self.current_checklist_idx += 1
                    self.load_next_checklist()
                else:
                    self._set_status(f"✖ Zoho Error: {resp.status_code}", self.BRAND_RED)
                    messagebox.showerror("Zoho Error", f"HTTP {resp.status_code}\n{resp.text}")
                    self.btn_send.config(state=tk.NORMAL)
            else:
                self.btn_send.config(state=tk.NORMAL)
        except Exception as e:
            self._set_status(f"✖ System Error: {e}", self.BRAND_RED)
            messagebox.showerror("System Error", str(e))
            self.btn_send.config(state=tk.NORMAL)

    # ── DSR Formatter ────────────────────────────────────────────────────────
    def format_dsr_excel(self):
        file_path = filedialog.askopenfilename(title="Select Input DSR Excel", filetypes=[("Excel", "*.xlsx *.xls")])
        if not file_path: return

        dir_name = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        out_file = filedialog.asksaveasfilename(
            title="Save Formatted DSR As",
            initialdir=dir_name,
            initialfile=f"{base_name} - Formatted.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx")]
        )
        if not out_file: return

        self._set_status("● Formatting Excel DSR...", self.WARN_AMBER)
        self.btn_format_dsr.config(state=tk.DISABLED, text="FORMATTING...")
        self.root.update()

        try:
            df = pd.read_excel(file_path)
            status_col = next((c for c in df.columns if c.replace("_"," ").upper() == "FTWZ STATUS"), None)
            if not status_col:
                self._set_status("✖ FTWZ Status column not found.", self.BRAND_RED)
                messagebox.showerror("Error", "Could not find 'FTWZ Status' column.")
                return

            date_col_keywords = ['date', 'on', 'eta', 'ata', 'expiry', 'cleared', 'sent', 'recd', 'approved', 'received']
            for col in df.columns:
                if str(df[col].dtype).startswith('datetime'):
                    df[col] = df[col].dt.strftime('%d-%b-%Y')
                elif df[col].dtype == 'object' or str(df[col].dtype) == 'string':
                    # Global date string cleaner: Strips trailing " 10:00:00" from exported Zoho timestamps
                    df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None', '<NA>', 'NaT'], '')
                    df[col] = df[col].str.replace(r'\s+\d{2}:\d{2}:\d{2}.*', '', regex=True)
                    
                    col_lower = col.lower()
                    if any(k in col_lower for k in date_col_keywords) and 'tat' not in col_lower and 'action' not in col_lower and 'person' not in col_lower and 'reason' not in col_lower:
                        # Attempt to parse any valid dates and enforce dd-MMM-yyyy format
                        parsed = pd.to_datetime(df[col].replace('', pd.NaT), errors='coerce', dayfirst=True)
                        mask = parsed.notnull()
                        df[col] = df[col].astype(object) # Force object dtype to avoid native Pandas datetime conversion overriding us
                        df.loc[mask, col] = parsed[mask].dt.strftime('%d-%b-%Y')

            # Unpack Subform
            if 'Airtel DSR' in df.columns and not any(c.startswith('Airtel DSR -') for c in df.columns):
                inv_nums, inv_dates, inv_vals, mod_nos, item_descs, qtys = [], [], [], [], [], []
                for val in df['Airtel DSR'].fillna(''):
                    parts = [p.strip() for p in str(val).split(';')]
                    if not parts or parts == ['']:
                        for lst in [inv_nums, inv_dates, inv_vals, mod_nos, item_descs, qtys]: lst.append('')
                        continue

                    r_nums, r_dates, r_vals, r_mods, r_descs, r_qtys = [], [], [], [], [], []
                    curr_p = 0
                    while curr_p + 4 < len(parts):
                        r_nums.append(parts[curr_p])
                        r_dates.append(parts[curr_p+1])
                        r_vals.append(parts[curr_p+2])
                        r_mods.append(parts[curr_p+3])
                        r_descs.append(parts[curr_p+4])
                        if curr_p + 5 < len(parts):
                            qty_part = parts[curr_p + 5]
                            if ',' in qty_part:
                                q, next_inv = qty_part.split(',', 1)
                                r_qtys.append(q)
                                parts[curr_p + 5] = next_inv.strip()
                                curr_p += 5
                            else:
                                r_qtys.append(qty_part)
                                curr_p += 6
                        else: curr_p += 6 

                    for lst in (r_nums, r_dates, r_vals):
                        last_v = None
                        for i in range(len(lst)):
                            if lst[i] == last_v: lst[i] = ""
                            else: last_v = lst[i]

                    inv_nums.append('\n'.join([x for x in r_nums if x]))
                    inv_dates.append('\n'.join([x for x in r_dates if x]))
                    inv_vals.append('\n'.join([x for x in r_vals if x]))
                    
                    mod_nos.append('\n'.join(r_mods))
                    item_descs.append('\n'.join(r_descs))
                    qtys.append('\n'.join(r_qtys))
                    
                df['Airtel DSR - Invoice Number'] = inv_nums
                df['Airtel DSR - Invoice Date']   = inv_dates
                df['Airtel DSR - Total Inv Value'] = inv_vals
                df['Airtel DSR - Model No']       = mod_nos
                df['Airtel DSR - Item Description'] = item_descs
                df['Airtel DSR - Product Qty']     = qtys

            subform_cols = [c for c in df.columns if 'Airtel DSR -' in c]
            main_cols = [c for c in df.columns if c not in subform_cols and c != 'Airtel DSR']
            
            # Use astype(str) then replace 'nan' to avoid dtype incompatibility warnings
            df = df.astype(str).replace(['nan', 'NaN', 'None', '<NA>'], '')

            def join_items(series):
                items = []
                for x in series:
                    val = str(x).replace('.0','')
                    if val.strip() and val != 'nan':
                        # Flatten existing newlines for clean deduplication
                        items.extend(val.split('\n'))
                        
                if series.name in ['Airtel DSR - Invoice Number', 'Airtel DSR - Invoice Date', 'Airtel DSR - Total Inv Value']:
                    deduped = []
                    last_val = None
                    for it in items:
                        if it == last_val and it != "": deduped.append("")
                        elif it != "": 
                            deduped.append(it)
                            last_val = it
                        else: deduped.append("")
                    return '\n'.join(deduped)
                return '\n'.join(items)
            df = df.groupby(main_cols, as_index=False, dropna=False)[subform_cols].agg(join_items)

            normal_shipment_map = [
                ('S.N.', ''), ('Job No', 'Job No'), ('Invoice No', 'Airtel DSR - Invoice Number'),
                ('Invoice Date', 'Airtel DSR - Invoice Date'), ('Invoice Value', 'Airtel DSR - Total Inv Value'),
                ('Port', 'Port'), ('Mode', 'Mode'), ('Supplier', 'Supplier / Exporter'),
                ('Current Status', 'Current Status'), ('TAT', 'TAT Inbond'), ('PO No', 'PO Number'),
                ('Demurrage Amnt', 'Demurrage / Detention charges'), ('Interest', 'Duty Interest'),
                ('Penalty', 'Penalty'), ('Concern Person', 'Concern Person'), ('Circle', 'Circle'),
                ('MAWB', 'MAWB/MBL'), ('HAWB', 'HAWB/HBL'), ('DO Amount', 'DO Amount'),
                ('Forwarder', 'Line / Forwarder'), ('Pkgs', 'No Of Pkgs'), ('Ch. Wt.', 'Chargeable Weight'),
                ('SI Rcd. Date', 'IB Pre-alert recd on'), ('C.List send on', 'IB Checklist Sent On'),
                ('C.List approved on', 'IB Checklist Approved On'), ('Req ID', 'Req ID Inbond'),
                ('BE No', 'IB BE No'), ('BE Date', 'IB BE Date'), ('ETA', 'ETA'),
                ('Assbl. Value ', 'IB Assbl. Value'), ('Duty', 'IB Duty'), ('Duty Req. On', 'IB Duty req sent on'),
                ('Duty Recd On', 'IB Duty received'), ('OOC Date', 'IB OOC Date'),
                ('Cleared / dispatch', 'IB Dispatch Date'), ('Vehicle no', 'IB Vehicle No'),
                ('move by', ('IB Move By', '__DEFAULT__NAGARKOT')), ('Vehicles type', 'IB Vehicle Type'),
                ('Tpt Fright', 'Tpt Fright'), ('Delivered to WH on', 'IB Delivery Date'),
                ('Interest', 'Duty Interest'), ('Penalty', 'Penalty'), 
                ('Demmurrage', 'Demurrage / Detention charges'),
                ('WPC/ETA/Letter/ remarks', 'WPC Expiry Date'), ('Remarks', 'IB Remarks'),
                ('Bill Done On', 'Bill Done On'), ('Demurrage mail sent date', 'Demurrage Mail Sent On'),
                ('Demurrage Approved date', 'Demurrage Approved Date')
            ]

            normal_cleared_map = [
                ('S.N', ''), ('Job No', 'Job No'), ('Invoice No', 'Airtel DSR - Invoice Number'),
                ('Invoice Date', 'Airtel DSR - Invoice Date'), ('Invoice Value', 'Airtel DSR - Total Inv Value'),
                ('Port of Clearence', 'Port'), ('Mode', 'Mode'), ('Supplier', 'Supplier / Exporter'),
                ('Status', 'Current Status'), ('TAT', 'TAT Inbond'), ('PO No', 'PO Number'),
                ('Demurrage Amnt', 'Demurrage / Detention charges'), ('Interest', 'Duty Interest'),
                ('Penalty', 'Penalty'), ('Concern Person', 'Concern Person'), ('Circle', 'Circle'),
                ('MAWB', 'MAWB/MBL'), ('HAWB', 'HAWB/HBL'), ('DO Amount', 'DO Amount'),
                ('Container No', 'Container No'), ('No. of Pkgs', 'No Of Pkgs'), ('Gr. Wt.', 'Chargeable Weight'),
                ('SI Rcd. Date', 'IB Pre-alert recd on'), ('C.List send on', 'IB Checklist Sent On'),
                ('C.List approved on', 'IB Checklist Approved On'), ('Req ID', 'Req ID Inbond'),
                ('BOE No', 'IB BE No'), ('BOE Date', 'IB BE Date'), ('ATA', 'ETA'),
                ('Ass Value ', 'IB Assbl. Value'), ('Total Duty', 'IB Duty'), ('Duty req. on', 'IB Duty req sent on'),
                ('Duty Recd on', 'IB Duty received'), ('OOC Date', 'IB OOC Date'),
                ('Cleared / dispatch', 'IB Dispatch Date'), ('Vehicle No', 'IB Vehicle No'),
                ('move by', ('IB Move By', '__DEFAULT__NAGARKOT')), ('Vehicle Type', 'IB Vehicle Type'),
                ('Tpt Fright ', 'Tpt Fright'), ('Delivered to WH on', 'IB Delivery Date'),
                ('Interest', 'Duty Interest'), ('Penalty', 'Penalty'), 
                ('Demmurrage', 'Demurrage / Detention charges'),
                ('WPC/ETA/ Declaration/ Letter', 'WPC Expiry Date'), ('Remarks', 'IB Remarks'),
                ('Delivery date', 'IB Delivery Date'), ('Demurrage mail sent date', 'Demurrage Mail Sent On'),
                ('Demurrage Approved date', 'Demurrage Approved Date'), ('Billing Status', 'Billing Status')
            ]

            fta_map = [
                ('S.N', ''), ('Invoice No', 'Airtel DSR - Invoice Number'),
                ('Invoice Date', 'Airtel DSR - Invoice Date'), ('Invoice Value', 'Airtel DSR - Total Inv Value'),
                ('Supplier', 'Supplier / Exporter'), ('Model No.', 'Airtel DSR - Model No'),
                ('Item Description', 'Airtel DSR - Item Description'), ('QTY', 'Airtel DSR - Product Qty'),
                ('Job No', 'Job No'), ('Mode', 'Mode'), ('BE Type', 'BE Type'),
                ('Port', 'Port'), ('ETA', 'ETA'), ('Current Status', 'Current Status'),
                ('Demurrage', 'Demurrage / Detention charges'),
                ('WPC Expiry date', 'WPC Expiry Date'), ('TAT Inbond', 'TAT Inbond'),
                ('TAT Outbond', 'TAT Outbond'), ('FTWZ Storage Approx', 'FTWZ Storage Approx'),
                ('Duty Interest', 'Duty Interest'), ('PO No', 'PO Number'), ('Circle', 'Circle'),
                ('Concern Person', 'Concern Person'), ('FTA No', 'FTA No'), ('FTA Date', 'FTA Date'),
                ('Original FTA Recd Date', 'Original FTA Recd Date'), ('IGM Date', 'IGM Date'),
                ('Inward Date', 'Inward Date'), ('Arrived at FTWZ', 'Arrived at FTWZ'),
                ('MAWB', 'MAWB/MBL'), ('HAWB', 'HAWB/HBL'), ('Pkgs', 'No Of Pkgs'),
                ('Ch.Wt.', 'Chargeable Weight'), ('Container No', 'Container No'),
                ('Line / Forwarder', 'Line / Forwarder'), ('DO Amount', 'DO Amount'),
                ('Pre-alert Recd On', 'IB Pre-alert recd on'), ('Checklist Sent On', 'IB Checklist Sent On'),
                ('Checklist Approved On', 'IB Checklist Approved On'), ('Req ID Inbond', 'Req ID Inbond'),
                ('BE No', 'IB BE No'), ('BE Date', 'IB BE Date'),
                ('Inbond Cleared On', 'Inbond Cleared On'), ('Remarks', 'IB Remarks'),
                ('Outbond Process', 'Outbond Process'), ('Job No', 'OB Job No'),
                ('BE Type', 'OB BE Type'), ('Checklist Sent On', 'OB Checklist Sent On'),
                ('Checklist Approved On', 'OB Checklist Approved On'), ('Req ID OB', 'Req ID Outbond'),
                ('BE No', 'OB BE No'), ('BE Date', 'OB BE Date'),
                ('Assbl. Value', 'OB Assbl. Value'), ('Duty', 'OB Duty'), ('Duty Req. Sent on', 'OB Duty req sent on'),
                ('Duty paid', 'OB Duty received'), ('Duty TAT', 'Duty TAT'), ('BE ooc date', 'OB OOC Date'),
                ('Cleared / Dispatched', 'OB Dispatch Date'), ('Vehicle no', 'OB Vehicle No'),
                ('move by', ('OB Move By', '__DEFAULT__NAGARKOT')), ('Vehicle type', 'OB Vehicle Type'), ('Tpt Fright', 'Tpt Fright'),
                ('Delivery date', 'OB Delivery Date'), ('Remarks', 'OB Remarks'),
                ('Other Charges', 'Other Charges'), ('Demurrage approval mail sent on', 'Demurrage Mail Sent On'),
                ('Demurrage Approved recd on', 'Demurrage Approved Date'), ('Form I req date', 'Form i req date'),
                ('Form I recd dt', 'Form i recd date')
            ]

            def map_columns(subset_df, mapping_list):
                final_data = {}
                final_headers = []
                for i, (out_col, in_col) in enumerate(mapping_list):
                    col_id = f"col_{i}"  # Unique ID prevents duplicate headers from overwriting data
                    final_headers.append(out_col)
                    
                    if out_col in ('S.N', 'S.N.'):
                        out_vals = list(range(1, 1 + len(subset_df)))
                    else:
                        if isinstance(in_col, str): sources = [in_col]
                        else: sources = list(in_col)

                        out_vals = [''] * len(subset_df)
                        for src in sources:
                            if src.startswith('__DEFAULT__'):
                                default_str = src.split('__DEFAULT__')[1]
                                for j in range(len(out_vals)):
                                    if not out_vals[j] or out_vals[j] == 'nan':
                                        out_vals[j] = default_str
                            elif src in subset_df.columns:
                                for j, val in enumerate(subset_df[src].values):
                                    if not out_vals[j] or out_vals[j] == 'nan':
                                        val_str = str(val).strip()
                                        if val_str.endswith('.0') and val_str != '.0':
                                            val_str = val_str[:-2]
                                        if val_str and val_str.lower() != 'nan':
                                            out_vals[j] = val_str
                    final_data[col_id] = out_vals
                
                res_df = pd.DataFrame(final_data).replace('nan', '')
                
                # Ultimate Post-Processor for Dates
                date_kws = ['date', 'on', 'eta', 'ata', 'expiry', 'cleared', 'sent', 'recd', 'approved', 'received']
                for c in res_df.columns:
                    header_str = final_headers[int(c.split('_')[1])] if c.startswith('col_') else c
                    h_low = header_str.lower()
                    if any(k in h_low for k in date_kws) and 'tat' not in h_low and 'action' not in h_low and 'person' not in h_low and 'reason' not in h_low:
                        # 1) Force to string and completely scrub time signatures
                        res_df[c] = res_df[c].astype(str).str.replace(r'\s*\d{2}:\d{2}:\d{2}.*', '', regex=True)
                        # 2) Parse to pure datetime to normalize
                        parsed = pd.to_datetime(res_df[c].replace(['', 'nan', 'None'], pd.NaT), errors='coerce', dayfirst=True)
                        mask = parsed.notnull()
                        # 3) Assign string output
                        res_df[c] = res_df[c].astype(object)
                        res_df.loc[mask, c] = parsed[mask].dt.strftime('%d-%b-%Y')
                
                res_df.columns = final_headers  # Apply the descriptive duplicate headers at the final step
                return res_df



            sheet_map = {
                "FTA Pending": "FTA Pending", "FTA Cleared": "FTA Cleared",
                "Normal Shipment": "Normal Shipment", "Normal Cleared": "Normal Cleared"
            }
            sheets_written = total_rows = 0

            with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
                for status_val, sheet_name in sheet_map.items():
                    subset = df[df[status_col] == status_val].copy()
                    if not subset.empty:
                        if sheet_name == "Normal Shipment": mp = normal_shipment_map
                        elif sheet_name == "Normal Cleared": mp = normal_cleared_map
                        else: mp = fta_map
                        mapped_df = map_columns(subset, mp)
                        mapped_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        ws = writer.sheets[sheet_name]
                        for idx, col in enumerate(mapped_df.columns):
                            col_letter = chr(65 + idx) if idx < 26 else f"{chr(64+idx//26)}{chr(65+idx%26)}"
                            max_len = 10
                            for cell in ws[col_letter]:
                                if cell.row == 1: continue
                                cell.alignment = Alignment(wrap_text=True, vertical='top')
                                if cell.value:
                                    lens = [len(x) for x in str(cell.value).split('\n')]
                                    max_len = max(max_len, max(lens)) if lens else max_len
                            ws.column_dimensions[col_letter].width = min(max_len + 2, 45)
                        sheets_written += 1
                        total_rows += len(mapped_df)

                known = list(sheet_map.keys())
                other = df[~df[status_col].isin(known)].copy()
                if not other.empty:
                    other.to_excel(writer, sheet_name="Other", index=False)
                    sheets_written += 1

                if sheets_written == 0:
                    df.to_excel(writer, sheet_name="Raw Data", index=False)
                    sheets_written = 1

            self.dsr_result_label.config(text=f"✔ Saved: {os.path.basename(out_file)}\n{sheets_written} sheets | {len(df)} rows", fg=self.SUCCESS_GRN)
            self._set_status(f"✔ DSR Formatted", self.SUCCESS_GRN)
            messagebox.showinfo("Format Complete", f"Excel saved to:\n{out_file}")

        except Exception as e:
            self._set_status(f"✖ Format failed: {e}", self.BRAND_RED)
            messagebox.showerror("Format Error", str(e))
        finally:
            self.btn_format_dsr.config(state=tk.NORMAL, text="⬇  SELECT & FORMAT DSR EXCEL")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChecklistParserApp(root)
    root.mainloop()