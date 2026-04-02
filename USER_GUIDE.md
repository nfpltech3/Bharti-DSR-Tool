# Bharti DSR Consolidation System User Guide

## Introduction
The Bharti DSR Consolidation System is a comprehensive data management suite used to automate the extraction, synchronization, and manipulation of shipping and customs data for Nagarkot Forwarders. It includes a Checklist Parser to extract Job Data from PDFs and push it directly into the Zoho "Shakti Pre-Alert", as well as robust Excel formatting and merging tools for manual DSR reports.

## How to Use

### 1. Launching the App
Run the pre-compiled applications directly from the generated `.exe` files located in the `dist/` directory.
Double-click `Checklist_Parser_App.exe` or `standalone_excel_import.exe`. No further Python installation is required when running the executables. Ensure they run from a directory containing the `.env` file since it stores API secure keys.

### 2. The Workflow (Step-by-Step)

#### Phase A: Checklist Parsing & Push to Zoho
1. **Launch**: Open `Checklist_Parser_App.exe`.
2. **UPLOAD CHECKLIST(S)**: Go to the Checklist Parser tab, click the upload button, and select one or more `.pdf` files.
3. **Review & Edit**: The system automatically pulls details (Job Number, HBL, MBL, Mode, Port, Subform lines) from the PDF. You can modify any parsed fields or manual inputs (ETA, Branch). 
   - *Note: If ETA is invalid, it will revert your input or ignore it till correctly entered.*
4. **PUSH TO SHAKTI PRE-ALERT**: Clicks send the visible Job Number and sub-details directly into the centralized Zoho Creator database.
5. **Next File**: If multiple files were uploaded, it will automatically parse the next file and cue it for pushing.

#### Phase B: Manual DSR Merging (Standalone Excel App)
1. **Launch**: Open `standalone_excel_import.exe`.
2. **Tab 1 - Merge Manual Fields**: Hit "SELECT FILES & MERGE". Upload the exported Zoho DSR report, then the Manual DSR Excel file.
   - *Note: The system automatically matches 20+ columns aliases to merge specific field data accurately.*
3. **Tab 2 - Import Airtel Subforms**: Switch tabs, click "SELECT SUBFORM EXCEL & PUSH" to selectively patch subform items directly into Zoho Pre-Alert rows.

## Interface Reference

### Checklist Parser Controls
| Control / Input | Description | Expected Format |
| :--- | :--- | :--- |
| **UPLOAD CHECKLIST(S)** | Main button to select source `.pdf` files. | PDF files |
| **Job No** | Scraped job identifier. Can be manually altered to update a specific un-parsed record instead. | Numeric Job Number |
| **ETA Date Picker** | Visual calendar or manual entry field for ship arrival times. | DD-MMM-YYYY |
| **MAWB / MBL** | Master Air/Bill of Lading tracking value. | String / Dash Separated |
| **Importer** | Determines customer branch lookup. Required for pushing to Zoho. | Dropdown Selection |
| **BE Type / Mode / Port** | Shipment identifiers matched from PDF context. | Dropdown Selection |

## Troubleshooting & Validations

If you see an error, check this table:

| Message | What it means | Solution |
| :--- | :--- | :--- |
| `Use dd-mm-yyyy` | The ETA date format does not conform to the required layout. | Select the date using the Calendar `🗓` icon, or manually type in `DD-MM-YYYY` format. |
| `For Air mode, MAWB must be exactly 11 numeric digits` | You have selected the Mode "Air" which demands an 11-digit AWB, but the input contained invalid characters/lengths. | Re-verify your Master Air Waybill tracking format and remove trailing spaces. |
| `Could not find Job No column in the Zoho Export!` | The Excel file uploaded to the Merging tool is missing a recognized Job reference column. | Ensure the report export includes a `Job No`, `Job Number`, or `Inbond Job` column Header. |
| `Parse failed: [error log]` | The PDF is illegible or structurally completely unrecognized by the text reader. | Choose "Skip" and process that specific order manually, then notify an admin. |
| `Missing required columns: • [Field Name]` | The Subform patch Excel is lacking a vital constraint field layout (e.g. `Invoice No`). | Format the source Excel subform to include headers matching `Invoice No`, `Date`, etc. |
