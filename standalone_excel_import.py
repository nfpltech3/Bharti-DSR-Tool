import os
import json
import re
from datetime import datetime
import pandas as pd
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dotenv import load_dotenv
import warnings
import sys

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')
warnings.filterwarnings("ignore", category=UserWarning, message=".*Could not infer format.*")

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

class ExcelToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NAGARKOT EXCEL TOOLS")
        self.root.geometry("800x600")
        
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
        
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=self.WHITE, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📊 NAGARKOT EXCEL TOOLS", font=("Arial", 20, "bold"),
                 fg=self.BRAND_BLUE, bg=self.WHITE).pack(side=tk.LEFT, padx=30)
                 
        # ── Tab Styles ────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[20, 8])

        body = tk.Frame(self.root, bg=self.LIGHT_BG, padx=40, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(body)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Merge Manual Fields
        self.tab_merge = tk.Frame(self.notebook, bg=self.LIGHT_BG, padx=40, pady=40)
        self.notebook.add(self.tab_merge, text="🔀 Merge Manual Fields")

        # Tab 2: Export Subform Import
        self.tab_subform = tk.Frame(self.notebook, bg=self.LIGHT_BG, padx=40, pady=40)
        self.notebook.add(self.tab_subform, text="📦 Import Airtel Subforms")
        
        self.build_merge_tab()
        self.build_subform_tab()

    def build_merge_tab(self):
        lbl_merge = tk.Label(self.tab_merge, text="MERGE MANUAL EXCEL FIELDS", font=("Arial", 14, "bold"), fg=self.BRAND_BLUE, bg=self.LIGHT_BG)
        lbl_merge.pack(anchor="w", pady=(0, 10))

        tk.Label(self.tab_merge, bg=self.LIGHT_BG, fg=self.MUTED_GRAY, font=("Arial", 10), justify="left",
                 text="Select exported Zoho DSR, then select Manual DSR. Generates ready_to_upload.xlsx").pack(anchor="w", pady=(0, 15))

        self.btn_merge_manual = tk.Button(self.tab_merge, text="🔀  SELECT FILES & MERGE", font=("Arial", 12, "bold"),
                                          bg=self.BRAND_BLUE, fg=self.WHITE, command=self.merge_manual_fields,
                                          pady=12, relief=tk.FLAT, activebackground=self.HOVER_BLUE, activeforeground=self.WHITE)
        self.btn_merge_manual.pack(fill=tk.X, pady=(0, 10))

        self.merge_result_label = tk.Label(self.tab_merge, text="Status: Ready", font=("Arial", 10), fg=self.MUTED_GRAY, bg=self.LIGHT_BG, anchor="w")
        self.merge_result_label.pack(anchor="w", pady=(0, 20))

    def build_subform_tab(self):
        lbl_subform = tk.Label(self.tab_subform, text="IMPORT AIRTEL SUBFORMS", font=("Arial", 14, "bold"), fg=self.BRAND_BLUE, bg=self.LIGHT_BG)
        lbl_subform.pack(anchor="w", pady=(0, 10))

        tk.Label(self.tab_subform, bg=self.LIGHT_BG, fg=self.MUTED_GRAY, font=("Arial", 10), justify="left",
                 text="Directly patches Subform data into existing Pre-Alert records in Zoho Creator.\nSelect the raw Excel Subform export.").pack(anchor="w", pady=(0, 15))

        self.btn_import_subform = tk.Button(self.tab_subform, text="📦  SELECT SUBFORM EXCEL & PUSH", font=("Arial", 12, "bold"),
                                          bg=self.BRAND_RED, fg=self.WHITE, command=self.run_subform_import,
                                          pady=12, relief=tk.FLAT, activebackground=self.HOVER_RED, activeforeground=self.WHITE)
        self.btn_import_subform.pack(fill=tk.X, pady=(0, 10))

        self.subform_result_label = tk.Label(self.tab_subform, text="Status: Ready", font=("Arial", 10), fg=self.MUTED_GRAY, bg=self.LIGHT_BG, anchor="w")
        self.subform_result_label.pack(anchor="w", pady=(0, 20))

    # ── Merge Manual Fields Logic ─────────────────────────────────────────────
    def merge_manual_fields(self):
        zoho_export = filedialog.askopenfilename(title="Select Zoho Export Excel", filetypes=[("Excel", "*.xlsx *.xls")])
        if not zoho_export: return
        
        manual_excel = filedialog.askopenfilename(title="Select Manual DSR Excel", filetypes=[("Excel", "*.xlsx *.xls")])
        if not manual_excel: return
        
        self.btn_merge_manual.config(state=tk.DISABLED, text="MERGING...")
        self.merge_result_label.config(text="Status: Reading files...", fg=self.WARN_AMBER)
        self.root.update()
        
        COLUMN_ALIASES = {
            "Job_No":                  ["Job No", "Job Number", "Job_No", "Job", "Inbond Job", "JOB", "Nagarkot Job"],
            "Current status":          ["Current Status", "Status", "Curent status"],
            "WPC Expiry Date":         ["WPC Expiry Date", "WPC Expiry", "WPC Expiry date", "WPC Expiry\n date"],
            "FTWZ Storage Approx":     ["FTWZ Storage Approx", "FTWZ Storage", "Storage Approx", "FTWZ Storage\nApprox"],
            "Duty Interest":           ["Duty Interest", "Interest", "Interest Rs."],
            "Penalty":                 ["Penalty"],
            "PO Number":               ["PO Number", "PO No", "PO No.", "PO NO", "Airtel PO No."],
            "Circle":                  ["Circle", "Region", "Circle Name"],
            "Concern Person":          ["Concern Person", "Person"],
            "FTA No":                  ["FTA No", "FTA Number", "FTA"],
            "FTA Date":                ["FTA Date", "FTA Dt"],
            "Original FTA Recd Date":  ["Original FTA Recd Date", "Original FTA rcd date", "Original FTA\n rcd date"],
            "Arrived at FTWZ":         ["Arrived at FTWZ", "Arrival at FTWZ", "Arrived at\n FTWZ"],
            "Line / Forwarder":        ["Line / Forwarder", "Line/Forwarder", "Forwarder", "Line / forwarder"],
            "Req ID Inbond":           ["Req ID Inbond", "Inbond Req ID", "RQ ID", "Req ID \nInbond"],
            "IB Remarks":              ["IB Remarks", "Remarks", "Inbond Remarks"],
            "Outbond Process":         ["Outbond Process", "OB Process", "Out bond Process", "Out bond\n Process"],
            "Req ID Outbond":          ["Req ID Outbond", "Outbond Req ID", "OB Req ID", "Req ID OB"],
            "Tpt Fright":              ["Tpt Fright", "Tpt Freight"],
            "OB Remarks":              ["OB Remarks", "Outbond Remarks"],
            "Other Charges":           ["Other Charges", "other charges"],
            "Demurrage Mail Sent On":  ["Demurrage Mail Sent On", "Demurrage\napproval\n mail sent on", "Demurrage \nmail sent date", "Demurrage\n mail sent date", "Demurrage mail sent date"],
            "Demurrage Approved Date": ["Demurrage Approved Date", "Demurrage \nApproved \nrecd on", "Demurrage\n Approved date", "Demurrage Approved date"],
            "Form i req date":         ["Form i req date", "Form I Req Date", "Form 1 req date", "Form I req date"],
            "Form i recd date":        ["Form i recd date", "Form I Recd Date", "Form 1 recd date", "Form i recd dt"],
            "Bill Done On":            ["Bill Done On", "Bill Done Date"],
            "Billing Status":          ["Billing Status"]
        }

        def find_all_columns(df_columns, aliases):
            matched = []
            norm_map = {re.sub(r'\s+', ' ', str(c)).strip().lower(): c for c in df_columns}
            for alias in aliases:
                norm_alias = re.sub(r'\s+', ' ', alias).strip().lower()
                if norm_alias in norm_map and norm_map[norm_alias] not in matched:
                    matched.append(norm_map[norm_alias])
                for i in range(1, 5):
                    dup_alias = f"{norm_alias}.{i}"
                    if dup_alias in norm_map and norm_map[dup_alias] not in matched:
                        matched.append(norm_map[dup_alias])
            return matched

        def find_column(df_columns, aliases):
            cols = find_all_columns(df_columns, aliases)
            return cols[0] if cols else None

        try:
            zoho_df = pd.read_excel(zoho_export, dtype=str)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read Zoho export:\n{e}")
            self.btn_merge_manual.config(state=tk.NORMAL, text="🔀  SELECT FILES & MERGE")
            self.merge_result_label.config(text="Status: Error loading Zoho Export.", fg=self.BRAND_RED)
            return

        zoho_job_col = find_column(zoho_df.columns, COLUMN_ALIASES["Job_No"])
        if not zoho_job_col:
            messagebox.showerror("Error", "Could not find Job No column in the Zoho Export!")
            self.btn_merge_manual.config(state=tk.NORMAL, text="🔀  SELECT FILES & MERGE")
            self.merge_result_label.config(text="Status: Job No col missing.", fg=self.BRAND_RED)
            return

        master_job_data = {}
        try:
            excel_file = pd.ExcelFile(manual_excel)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read Manual DSR Excel:\n{e}")
            self.btn_merge_manual.config(state=tk.NORMAL, text="🔀  SELECT FILES & MERGE")
            self.merge_result_label.config(text="Status: Error loading Manual DSR.", fg=self.BRAND_RED)
            return

        # Map manual DSR sheet names to standardized FTWZ Status values
        SHEET_TO_FTWZ_STATUS = {
            "fta pending": "FTA Pending",
            "fta cleared": "FTA Cleared",
            "normal shipment": "Normal Shipment",
            "normal cleared": "Normal Cleared",
        }

        for sheet in excel_file.sheet_names:
            df_sheet = pd.read_excel(excel_file, sheet_name=sheet, dtype=str)
            job_col = find_column(df_sheet.columns, COLUMN_ALIASES["Job_No"])
            if not job_col: continue
                
            sheet_mapping = {}
            for target_field, aliases in COLUMN_ALIASES.items():
                if target_field == "Job_No": continue
                cols_found = find_all_columns(df_sheet.columns, aliases)
                if cols_found: sheet_mapping[target_field] = cols_found
                    
            if not sheet_mapping: continue

            # Derive FTWZ Status from the sheet name
            ftwz_status = SHEET_TO_FTWZ_STATUS.get(sheet.strip().lower(), "")
            
            for _, row in df_sheet.iterrows():
                j_num = str(row.get(job_col, "")).strip().replace('.0', '')
                if j_num == "nan" or not j_num: continue
                    
                if j_num not in master_job_data:
                    master_job_data[j_num] = {}

                # Store FTWZ Status from the sheet name (first match wins)
                if ftwz_status and "FTWZ Status" not in master_job_data[j_num]:
                    master_job_data[j_num]["FTWZ Status"] = ftwz_status
                    
                for target_field, sheet_cols in sheet_mapping.items():
                    vals = []
                    for c in sheet_cols:
                        val = str(row.get(c, "")).strip()
                        if val and val != "nan":
                            if val.endswith(".0"): val = val[:-2]
                            if re.match(r'^\d{4}-\d{2}-\d{2}', val):
                                try:
                                    dt = datetime.strptime(val[:10], "%Y-%m-%d")
                                    val = dt.strftime("%d-%b-%Y")
                                except: pass
                            if target_field in ["WPC Expiry Date", "FTA Date", "Original FTA Recd Date", "Arrived at FTWZ", "Demurrage Mail Sent On", "Demurrage Approved Date", "Form i req date", "Form i recd date", "Bill Done On"]:
                                v_low = val.lower()
                                if "awaiting" in v_low or "pending" in v_low or v_low in ["na", "n/a", "-", "tbd", ".", "na ", "none"]:
                                    val = ""
                            if val:
                                if target_field == "Concern Person": val = val.title()
                                elif target_field == "Circle":
                                    val = val.title().replace("Lds Nld", "LDS NLD").replace("Nesa", "NESA")
                                    if val == "Ncr" or val == "Ncr ": val = "Delhi NCR"
                                    else: val = val.replace("Ncr", "NCR")
                            vals.append(val)
                    if vals:
                        final_val = " | ".join(vals)
                        if target_field not in master_job_data[j_num]:
                            master_job_data[j_num][target_field] = final_val

        for target_field in COLUMN_ALIASES.keys():
            if target_field == "Job_No": continue
            if target_field not in zoho_df.columns:
                zoho_df[target_field] = ""
        if "FTWZ Status" not in zoho_df.columns:
            zoho_df["FTWZ Status"] = ""
                
        self.merge_result_label.config(text="Status: Merging data...")
        self.root.update()

        zoho_df['_clean_job'] = zoho_df[zoho_job_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        updated_count = 0
        for idx, row in zoho_df.iterrows():
            job_no = row['_clean_job']
            if job_no in master_job_data:
                job_updates = master_job_data[job_no]
                has_updates = False
                for field, val in job_updates.items():
                    if field in zoho_df.columns and val != "":
                        zoho_df.at[idx, field] = val
                        has_updates = True
                if has_updates: updated_count += 1
                    
        zoho_df.drop(columns=['_clean_job'], inplace=True, errors='ignore')
        cols_to_keep = ["ID", zoho_job_col]
        for k in COLUMN_ALIASES.keys():
            if k != "Job_No" and k in zoho_df.columns:
                cols_to_keep.append(k)
        if "FTWZ Status" in zoho_df.columns and "FTWZ Status" not in cols_to_keep:
            cols_to_keep.append("FTWZ Status")
                
        final_zoho_df = zoho_df[[c for c in cols_to_keep if c in zoho_df.columns]]
        
        dir_name = os.path.dirname(zoho_export)
        out_file = filedialog.asksaveasfilename(
            title="Save Ready to Upload Excel",
            initialdir=dir_name,
            initialfile="ready_to_upload.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx")]
        )
        if out_file:
            final_zoho_df.to_excel(out_file, index=False)
            self.merge_result_label.config(text=f"✔ Saved: {os.path.basename(out_file)} | {updated_count} jobs updated", fg=self.SUCCESS_GRN)
            messagebox.showinfo("Merge Complete", f"Successfully updated {updated_count} jobs.\nFile saved to:\n{out_file}")
        else:
            self.merge_result_label.config(text="Status: Save cancelled.", fg=self.MUTED_GRAY)

        self.btn_merge_manual.config(state=tk.NORMAL, text="🔀  SELECT FILES & MERGE")


    # ── Subform Import Logic ──────────────────────────────────────────────────
    def _find_col(self, df, variants):
        norm_map = {re.sub(r'\s+', ' ', str(c)).strip(): c for c in df.columns}
        for v in variants:
            if v in df.columns: return v
            norm_v = re.sub(r'\s+', ' ', v).strip()
            if norm_v in norm_map: return norm_map[norm_v]
        return None

    def _split_lines(self, val):
        if not val or str(val) == "nan": return []
        return [v.strip() for v in str(val).split("\n") if v.strip()]

    def _clean_date(self, val):
        for fmt in ("%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"):
            try: return datetime.strptime(str(val).strip(), fmt).strftime("%d-%b-%Y").upper()
            except ValueError: continue
        return str(val)

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

    def run_subform_import(self):
        file_path = filedialog.askopenfilename(title="Select Subform Excel", filetypes=[("Excel", "*.xlsx *.xls")])
        if not file_path:
            return

        self.btn_import_subform.config(state=tk.DISABLED, text="READING...")
        self.subform_result_label.config(text=f"Status: Loading '{os.path.basename(file_path)}'...", fg=self.WARN_AMBER)
        self.root.update()

        try:
            df = pd.read_excel(file_path, dtype=str)
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read Excel:\n{e}")
            self.btn_import_subform.config(state=tk.NORMAL, text="📦  SELECT SUBFORM EXCEL & PUSH")
            self.subform_result_label.config(text="Status: Error loading Excel.", fg=self.BRAND_RED)
            return

        col_inv_no = self._find_col(df, ["Invoice No", "Inv No", "Invoice Number"])
        col_date   = self._find_col(df, ["INV DATE", "Date", "Invoice Date", "Inv Date"])
        col_value  = self._find_col(df, ["Invoice Value", "Inv Value", "Total Inv Value"])
        col_model  = self._find_col(df, ["Model No.", "Model No", "Model"])
        col_desc   = self._find_col(df, ["Item Description", "Description", "Desc"])
        col_qty    = self._find_col(df, ["QTY", "Qty", "Product Qty", "Quantity"])
        col_job    = self._find_col(df, ["Job No", "Job_No", "Job Number"])
        col_port   = self._find_col(df, ["Port", "Port_Airtel", "Port Airtel"])

        missing = []
        if not col_inv_no: missing.append("Invoice No")
        if not col_date:   missing.append("Date / INV DATE")
        if not col_value:  missing.append("Invoice Value")
        if not col_model:  missing.append("Model No.")
        if not col_desc:   missing.append("Item Description")
        if not col_qty:    missing.append("QTY")
        if not col_job:    missing.append("Job No")

        if missing:
            messagebox.showerror("Column Error", f"Could not find columns:\n• " + "\n• ".join(missing) + f"\n\nFound columns: {list(df.columns)}")
            self.btn_import_subform.config(state=tk.NORMAL, text="📦  SELECT SUBFORM EXCEL & PUSH")
            self.subform_result_label.config(text="Status: Missing required columns.", fg=self.BRAND_RED)
            return

        df[col_job] = df[col_job].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        grouped = df.groupby(col_job, dropna=False)
        job_count = len(grouped)

        if not messagebox.askyesno("Excel Import", f"Found {len(df)} rows across {job_count} jobs.\n\nThis will PATCH the subform into existing Pre-Alert records in Zoho.\n\nProceed?"):
            self.btn_import_subform.config(state=tk.NORMAL, text="📦  SELECT SUBFORM EXCEL & PUSH")
            self.subform_result_label.config(text="Status: User cancelled.", fg=self.MUTED_GRAY)
            return

        owner = os.environ.get("ZOHO_ACCOUNT_OWNER")
        app = os.environ.get("ZOHO_APP_NAME")
        report_url = f"https://creator.zoho.in/api/v2/{owner}/{app}/report/View_All_Jobs"

        token = None
        if os.path.exists("zoho_token.json"):
            with open("zoho_token.json") as f:
                token = json.load(f).get("access_token")
        if not token:
            token = self.refresh_zoho_token()
        if not token:
            messagebox.showerror("Auth Error", "Could not get Zoho access token.")
            self.btn_import_subform.config(state=tk.NORMAL, text="📦  SELECT SUBFORM EXCEL & PUSH")
            self.subform_result_label.config(text="Status: Auth failed.", fg=self.BRAND_RED)
            return

        updated = 0
        not_found = 0
        errors = []

        self.btn_import_subform.config(text="PUSHING TO ZOHO...")
        for i, (job_no, rows) in enumerate(grouped, 1):
            job_no = str(job_no).strip()
            if not job_no or job_no == "nan":
                continue

            self.subform_result_label.config(text=f"Status: Processing Job {job_no} ({i}/{job_count})...")
            self.root.update()

            job_port = ""
            if col_port:
                val = str(rows.iloc[0].get(col_port, "")).strip()
                if val and val != "nan":
                    job_port = "MUM" if val.lower() == "mumbai air cargo" else val

            subform_rows = []
            for _, row in rows.iterrows():
                invoices = self._split_lines(row.get(col_inv_no, ""))
                dates    = self._split_lines(row.get(col_date, ""))
                values   = self._split_lines(row.get(col_value, ""))
                models   = self._split_lines(row.get(col_model, ""))
                descs    = self._split_lines(row.get(col_desc, ""))
                qtys     = self._split_lines(row.get(col_qty, ""))

                block_count = max(len(invoices), len(models), len(descs), len(qtys), 1)
                inv_count   = max(len(invoices), 1)

                for idx in range(block_count):
                    inv_idx = idx * inv_count // block_count if inv_count > 0 else 0
                    inv_no  = invoices[inv_idx] if inv_idx < len(invoices) else (invoices[-1] if invoices else "")
                    inv_dt  = dates[inv_idx] if inv_idx < len(dates) else (dates[-1] if dates else "")
                    inv_val = values[inv_idx] if inv_idx < len(values) else (values[-1] if values else "")
                    model   = models[idx] if idx < len(models) else ""
                    desc    = descs[idx] if idx < len(descs) else ""
                    qty     = qtys[idx] if idx < len(qtys) else (qtys[-1] if qtys else "")

                    if inv_dt: inv_dt = self._clean_date(inv_dt)
                    for v in [inv_val, qty]:
                        if v.endswith(".0"): v = v[:-2]
                    if inv_val.endswith(".0"):  inv_val = inv_val[:-2]
                    if inv_val.endswith(".00"): inv_val = inv_val[:-3]
                    if qty.endswith(".0"):      qty = qty[:-2]

                    subform_rows.append({
                        "Invoice_Number":  inv_no,
                        "Invoice_Date":    inv_dt,
                        "Total_Inv_Value": inv_val,
                        "Model_No":        model,
                        "Item_Description": desc,
                        "Product_Qty":     qty,
                    })

            try:
                search_params = {"criteria": f'Job_No == "{job_no}"'}
                search_resp = requests.get(report_url, headers={"Authorization": f"Zoho-oauthtoken {token}"}, params=search_params)

                if search_resp.status_code == 401:
                    token = self.refresh_zoho_token()
                    search_resp = requests.get(report_url, headers={"Authorization": f"Zoho-oauthtoken {token}"}, params=search_params)

                existing_id = None
                if search_resp.status_code == 200:
                    s_data = search_resp.json().get("data", [])
                    if s_data: existing_id = s_data[0].get("ID")

                if not existing_id:
                    not_found += 1
                    continue

                patch_payload = {"data": {"Airtel_DSR": subform_rows}}
                if job_port: patch_payload["data"]["Port_Airtel"] = job_port
                    
                patch_url = f"{report_url}/{existing_id}"
                resp = requests.patch(patch_url, headers={"Authorization": f"Zoho-oauthtoken {token}"}, json=patch_payload, timeout=15)

                if resp.status_code in (200, 201) and resp.json().get("code") == 3000:
                    updated += 1

            except Exception as e:
                errors.append(f"ERROR: Job {job_no} — {e}")

        summary = f"EXCEL IMPORT COMPLETE\n\nTotal Jobs: {job_count}\nUpdated:    {updated}\nNot Found:  {not_found}\n"
        if errors: summary += f"\n--- DETAILS ---\n" + "\n".join(errors)

        self.btn_import_subform.config(state=tk.NORMAL, text="📦  SELECT SUBFORM EXCEL & PUSH")
        self.subform_result_label.config(text=f"✔ Push Complete: {updated} jobs updated.", fg=self.SUCCESS_GRN)
        messagebox.showinfo("Excel Import Summary", summary)


if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToolsApp(root)
    root.mainloop()
