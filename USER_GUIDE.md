# Bharti DSR Consolidation System: User Guide

## Introduction
This toolset automates shipping and customs data entry for Nagarkot Forwarders. It consists of two standalone applications:
1. **Checklist Parser (`Checklist_Parser_App.exe`):** A dual-purpose application that extracts job data from PDFs to push into Zoho (Shakti Pre-Alert), and formats raw Zoho DSR reports into clean, client-ready Excel sheets.
2. **Excel Importer (`standalone_excel_import.exe`):** A tool for merging Excel data for manual DSR reports and pushing subform items into Zoho.

## Setup & Launch
* Keep the application files (`.exe`) and the `.env` file in the same folder. *(The `.env` file is required as it securely stores connection keys).*
* Double-click the desired `.exe` to open the tools. No Python installation is required.

---

## 🧾 Checklist Parser App Workflow (`Checklist_Parser_App.exe`)

The Checklist Parser app features two main tabs for handling Pre-Alert data extraction and DSR Excel formatting.

### Tab 1: Checklist Parser (PDF to Zoho)
This tab allows you to parse customs checklist PDFs and push the extracted information to the Zoho CRM (Shakti Pre-Alert system).

1. **Upload:** Click **UPLOAD CHECKLIST(S)** and select one or more `.pdf` files.
2. **Review Extracted Data:** The app automatically parses the PDF for:
   * Job No, Invoice Number, Total Inv Value, Model(s)
   * BE Type, Invoice Date, Supplier / Exporter, Qty, Description
   *(Note: The parser intelligently falls back to alternate headers like "Custom stn:" if standard headers are missing, and handles various quantity units like KGS, MTR).*
3. **Fill Manual Fields:** Complete the mandatory fields before submission:
   * **HAWB / HBL & MAWB / MBL**
   * **ETA:** Use the Calendar icon to strictly enforce a `DD-MMM-YYYY` format.
   * **Importer, Branch, Mode, Port**
   * **Assigned To:** You can type to search for an employee name.
4. **Push to Zoho:** Click **PUSH TO SHAKTI PRE-ALERT**. The app will create a new record or update an existing one if a matching Job No / HAWB is found. Successful submissions are logged locally in `prealert_submission_log.csv`.
5. **Next File:** The app will automatically queue the next PDF for review. You can also use **SKIP FILE** to bypass a PDF.

### Tab 2: Format DSR (Zoho Excel to Client DSR)
This tab transforms raw Zoho CRM exported tabular reports into neatly formatted, multi-sheet Excel reports ready for the client (Bharti).

1. **Format:** Click **SELECT & FORMAT DSR EXCEL** and choose your raw Zoho exported Excel file.
2. **Automated Processing:** The tool will automatically:
   * Strip trailing time signatures from dates and format all dates to a standard `DD-MMM-YYYY`.
   * Unpack the compressed "Airtel DSR" subform data into discrete columns (Invoice No, Date, Value, Model, Description, Qty).
   * Rename internal Zoho headers to standard client-facing headers based on the job's **FTWZ STATUS**.
   * Split the data into specific sheets: `FTA Pending`, `FTA Cleared`, `Normal Shipment`, and `Normal Cleared`.
   * Apply clean formatting, text wrapping, and auto-adjusted column widths.
3. **Output:** A new Excel file is saved in the same folder as the original, appended with ` - Formatted.xlsx`.

---

## 📊 Excel Importer Workflow (`standalone_excel_import.exe`)

1. **Launch:** Open `standalone_excel_import.exe`.
2. **Merge DSRs (Tab 1):** Click **SELECT FILES & MERGE**. Upload the exported Zoho DSR report first, followed by your Manual DSR Excel file. The tool will automatically match the columns.
3. **Import Subforms (Tab 2):** Click **SELECT SUBFORM EXCEL & PUSH** to upload an Excel file and push subform items directly into Zoho.

---

## Troubleshooting

| Error Message | Cause | Solution |
| :--- | :--- | :--- |
| `HTTP 401 / 403` | Zoho token expired or missing. | Ensure your `.env` is correct. The app will auto-refresh the token if configured properly. |
| `Use dd-mm-yyyy` or Date Error | The ETA date is in the wrong format. | Use the Calendar icon to select the date in `DD-MMM-YYYY` format. |
| `For Air mode, MAWB must be exactly 11 numeric digits` | Air shipments require a strict 11-digit tracking number. | Fix the tracking number and remove any accidental spaces. |
| `Could not find 'FTWZ Status' column` | DSR formatting failed. | Ensure the Zoho export includes the "FTWZ Status" column. |
| `Missing required columns: [Field]` | The Subform Excel file is missing a mandatory column. | Add the missing header (e.g., `Invoice No`, `Date`) to the Excel file. |
| `Parse failed` | The PDF text is illegible or layout unrecognized. | Ensure you are uploading a valid Customs Checklist PDF. |