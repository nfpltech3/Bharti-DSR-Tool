import pandas as pd
import re
import warnings
from datetime import datetime

warnings.filterwarnings('ignore') # Hide openpyxl warnings

# ---------------------------------------------------------
# TARGET COLUMNS & THEIR POSSIBLE HEADER NAMES ACROSS SHEETS
# ---------------------------------------------------------
# Key: The exact column name in your Zoho Export
# Value: List of possible header names in the Manual Excel sheets (case-insensitive)
COLUMN_ALIASES = {
    "Job_No":                 ["Job No", "Job Number", "Job_No", "Job", "Inbond Job"],
    "Current Status":         ["Current Status", "Status", "Latest Status", "Curent status"],
    "WPC Expiry Date":        ["WPC Expiry Date", "WPC Expiry", "WPC Expiry date", "WPC Expiry\n date"],
    "FTWZ Storage Approx":    ["FTWZ Storage Approx", "FTWZ Storage", "Storage Approx", "FTWZ Storage\nApprox"],
    "Duty Interest":          ["Duty Interest", "Interest", "Interest Rs.", "Interest                        Rs."],
    "Penalty":                ["Penalty", "Fine", "Late Fee"],
    "PO Number":              ["PO Number", "PO No", "PO No.", "PO NO", "Airtel PO No."],
    "Circle":                 ["Circle", "Region", "Circle Name"],
    "Concern Person":         ["Concern Person", "Contact Person", "Concern", "Person"],
    "FTA No":                 ["FTA No", "FTA Number", "FTA"],
    "FTA Date":               ["FTA Date", "FTA Dt"],
    "Original FTA Recd Date": ["Original FTA Recd Date", "Original FTA rcd date", "Original FTA\n rcd date"],
    "Arrived at FTWZ":        ["Arrived at FTWZ", "Arrival at FTWZ", "Arrived at\n FTWZ"],
    "Line / Forwarder":       ["Line / Forwarder", "Line/Forwarder", "Forwarder", "Line / forwarder"],
    "IB Remarks":             ["IB Remarks", "Remarks", "Inbond Remarks", "Notes"],
    "Outbond Process":        ["Outbond Process", "OB Process", "Out bond Process", "Out bond\n Process"],
    "Demurrage Mail Sent On": ["Demurrage Mail Sent On", "Demurrage\napproval\n mail sent on", "Demurrage \nmail sent date", "Demurrage\n mail sent date", "Demurrage mail sent date"],
    "Demurrage Approved Date": ["Demurrage Approved Date", "Demurrage \nApproved \nrecd on", "Demurrage\n Approved date", "Demurrage Approved date"]
}

def find_all_columns(df_columns, aliases):
    """Fuzzy search for all columns based on possible aliases (handles Pandas duplicate .1, .2 suffixes)."""
    matched = []
    norm_map = {re.sub(r'\s+', ' ', str(c)).strip().lower(): c for c in df_columns}
    for alias in aliases:
        norm_alias = re.sub(r'\s+', ' ', alias).strip().lower()
        # Direct match
        if norm_alias in norm_map and norm_map[norm_alias] not in matched:
            matched.append(norm_map[norm_alias])
        
        # Duplicate columns mapped by pandas (.1, .2, etc)
        for i in range(1, 5):
            dup_alias = f"{norm_alias}.{i}"
            if dup_alias in norm_map and norm_map[dup_alias] not in matched:
                matched.append(norm_map[dup_alias])
                
    return matched

def find_column(df_columns, aliases):
    cols = find_all_columns(df_columns, aliases)
    return cols[0] if cols else None

def run_merge():
    print("\n--- ZOHO DSR BULK MERGER ---")
    
    zoho_export = input("Enter exactly what you named the Zoho Export Excel (e.g. zoho.xlsx): ").strip().strip('"').strip("'")
    manual_excel = input("Enter exactly what the manual Excel is named (e.g. nagarkot dsr.xlsx): ").strip().strip('"').strip("'")
    
    try:
        zoho_df = pd.read_excel(zoho_export, dtype=str)
    except Exception as e:
        print(f"❌ Could not strictly read {zoho_export}: {e}")
        return

    # Find the Job No column in the Zoho file
    zoho_job_col = find_column(zoho_df.columns, COLUMN_ALIASES["Job_No"])
    if not zoho_job_col:
        print("❌ Could not find Job No column in the Zoho Export!")
        return

    # Dictionary to hold the extracted manual data { '53298': { 'PO Number': 'PO123', 'Penalty': '500' } }
    master_job_data = {}
    
    print(f"\nScanning all sheets inside {manual_excel}...")
    try:
        excel_file = pd.ExcelFile(manual_excel)
    except Exception as e:
        print(f"❌ Could not read {manual_excel}: {e}")
        return

    # Sweep through EVERY SHEET
    for sheet in excel_file.sheet_names:
        print(f"  > Checking sheet: '{sheet}'")
        df_sheet = pd.read_excel(excel_file, sheet_name=sheet, dtype=str)
        
        # Look for Job No first
        job_col = find_column(df_sheet.columns, COLUMN_ALIASES["Job_No"])
        if not job_col:
            print(f"    - Skipped! No Job No column found.")
            continue
            
        # Figure out which of our target columns exist in this specific sheet
        sheet_mapping = {}
        for target_field, aliases in COLUMN_ALIASES.items():
            if target_field == "Job_No": continue
            cols_found = find_all_columns(df_sheet.columns, aliases)
            if cols_found:
                sheet_mapping[target_field] = cols_found
                
        if not sheet_mapping:
            print(f"    - Skipped! Found Job Nos, but no target fields matched.")
            continue
            
        print(f"    - Found fields: {list(sheet_mapping.keys())}")
        
        # Extract row by row
        for _, row in df_sheet.iterrows():
            j_num = str(row.get(job_col, "")).strip().replace('.0', '')
            if j_num == "nan" or not j_num:
                continue
                
            if j_num not in master_job_data:
                master_job_data[j_num] = {}
                
            for target_field, sheet_cols in sheet_mapping.items():
                vals = []
                for c in sheet_cols:
                    val = str(row.get(c, "")).strip()
                    if val and val != "nan":
                        # Clean decimals from potential numbers
                        if val.endswith(".0"): val = val[:-2]
                        
                        # Catch and cleanup pandas datetime strings unconditionally
                        if re.match(r'^\d{4}-\d{2}-\d{2}', val):
                            try:
                                dt = datetime.strptime(val[:10], "%Y-%m-%d")
                                val = dt.strftime("%d-%b-%Y")
                            except:
                                pass
                                
                        # Date Field Sanitizer: remove "awaiting", "pending", etc. from Date columns
                        if target_field in ["WPC Expiry Date", "FTA Date", "Original FTA Recd Date", "Arrived at FTWZ", "Demurrage Mail Sent On", "Demurrage Approved Date"]:
                            v_low = val.lower()
                            if "awaiting" in v_low or "pending" in v_low or v_low in ["na", "n/a", "-", "tbd", ".", "na ", "none"]:
                                val = ""
                                
                        # Dropdown Field Sanitizer: Handle specific casing rules
                        if val:
                            if target_field == "Concern Person":
                                val = val.title()
                            elif target_field == "Circle":
                                val = val.title()
                                # Specific acronym overrides that .title() breaks
                                val = val.replace("Lds Nld", "LDS NLD")
                                val = val.replace("Nesa", "NESA")
                                
                                # NCR mappings
                                if val == "Ncr" or val == "Ncr ":
                                    val = "Delhi NCR"
                                else:
                                    val = val.replace("Ncr", "NCR")
                                
                        vals.append(val)
                
                if vals:
                    # If multiple columns hold data (like 2 Remarks columns), join them
                    final_val = " | ".join(vals)
                    # Only overwrite if it wasn't already populated by a previous sheet for this job
                    if target_field not in master_job_data[j_num]:
                        master_job_data[j_num][target_field] = final_val

    print(f"\n✔ Successfully harvested data for {len(master_job_data)} separate Job Numbers.")
    
    # Ensure Zoho dataframe has all these columns (even if empty) so we can populate them
    for target_field in COLUMN_ALIASES.keys():
        if target_field == "Job_No": continue
        if target_field not in zoho_df.columns:
            zoho_df[target_field] = ""
            
    # Clean Zoho Job Nos for matching
    zoho_df['_clean_job'] = zoho_df[zoho_job_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    
    print("\nMerging data into Zoho file...")
    updated_count = 0
    for idx, row in zoho_df.iterrows():
        job_no = row['_clean_job']
        if job_no in master_job_data:
            job_updates = master_job_data[job_no]
            has_updates = False
            for field, val in job_updates.items():
                if field in zoho_df.columns:
                    # Prevent overwriting good zoho data with blank manual data
                    if val != "":
                        zoho_df.at[idx, field] = val
                        has_updates = True
            if has_updates:
                updated_count += 1
                
    # Cleanup and filter columns
    zoho_df.drop(columns=['_clean_job'], inplace=True, errors='ignore')
    
    # We only want ID, Job_No, and the target fields
    cols_to_keep = ["ID", zoho_job_col]
    for k in COLUMN_ALIASES.keys():
        if k != "Job_No" and k in zoho_df.columns:
            cols_to_keep.append(k)
            
    final_zoho_df = zoho_df[[c for c in cols_to_keep if c in zoho_df.columns]]
    
    out_file = "ready_to_upload.xlsx"
    final_zoho_df.to_excel(out_file, index=False)
    
    print(f"\n🎉 DONE! {updated_count} rows were successfully updated with manual data.")
    print(f"The final file has been saved as: {out_file}")
    print("You can now upload this directly to the Zoho Creator Import Data screen!")

if __name__ == "__main__":
    run_merge()
