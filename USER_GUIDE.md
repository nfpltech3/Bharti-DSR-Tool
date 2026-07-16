# Bharti DSR Consolidation System: User Guide

## Introduction
This tool automates shipping and customs data entry for Nagarkot Forwarders. It performs two main tasks: 
1. **Checklist Parser:** Extracts job data from PDFs and pushes it to Zoho (Shakti Pre-Alert).
2. **Excel Importer:** Merges and formats Excel data for manual DSR reports.

## Setup & Launch
* Keep the application files (`.exe`) and the `.env` file in the same folder. *(The `.env` file is required as it securely stores connection keys).*
* Double-click `Checklist_Parser_App.exe` or `standalone_excel_import.exe` to open the tools. No Python installation is required.

## Step-by-Step Workflow

### Phase A: PDF Parsing & Zoho Sync
1. **Launch:** Open `Checklist_Parser_App.exe`.
2. **Upload:** Click **UPLOAD CHECKLIST(S)** and select your `.pdf` file(s).
3. **Review & Edit:** The app automatically extracts the job details (Job Number, HBL, Mode, Port, etc.) and item quantities. 
   * *Note:* You can manually edit any field. If the ETA date format is invalid, the system will reject it until corrected.
4. **Sync:** Click **PUSH TO SHAKTI PRE-ALERT** to send the displayed record to Zoho.
5. **Next File:** If you uploaded multiple PDFs, the app will automatically load the next one in the queue.

### Phase B: Excel Merging & Imports
1. **Launch:** Open `standalone_excel_import.exe`.
2. **Merge DSRs (Tab 1):** Click **SELECT FILES & MERGE**. Upload the exported Zoho DSR report first, followed by your Manual DSR Excel file. The tool will automatically match the columns.
3. **Import Subforms (Tab 2):** Click **SELECT SUBFORM EXCEL & PUSH** to upload an Excel file and push subform items directly into Zoho.

## Interface Guide (Checklist Parser)

| Field / Button | What it does | Required Format |
| :--- | :--- | :--- |
| **UPLOAD CHECKLIST(S)** | Selects the source files. | `.pdf` files only |
| **Job No** | The extracted job identifier. Can be manually edited. | Numeric digits |
| **ETA Date Picker** | The ship's arrival date. | `DD-MMM-YYYY` |
| **MAWB / MBL** | The master tracking number. | Text with dashes |
| **Importer** | The customer branch (Required for Zoho push). | Dropdown selection |
| **BE Type / Mode / Port** | Shipment details extracted from the PDF. | Dropdown selection |

## Troubleshooting

| Error Message | Cause | Solution |
| :--- | :--- | :--- |
| `Use dd-mm-yyyy` | The ETA date is in the wrong format. | Use the Calendar icon to select the date, or type it exactly as `DD-MM-YYYY`. |
| `For Air mode, MAWB must be exactly 11 numeric digits` | Air shipments require a strict 11-digit tracking number. | Fix the tracking number and remove any accidental spaces. |
| `Could not find Job No column...` | The uploaded Excel file is missing a Job reference column. | Check the source Excel file and ensure a `Job No` or `Job Number` column exists. |
| `Missing required columns: [Field]` | The Subform Excel file is missing a mandatory column. | Add the missing header (e.g., `Invoice No`, `Date`) to the Excel file. |
| `Parse failed: [error log]` | The PDF text is illegible or the layout is unrecognized. | Skip this file, process the record manually, and notify the admin. |