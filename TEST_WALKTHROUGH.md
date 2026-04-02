# DSR Consolidation — Test Setup Walkthrough

## Overview

We will create **3 test forms** in Zoho Creator, import sample data, run the merge script, and verify the output.

```
┌─────────────────┐   ┌────────────────┐
│ Test_PreAlert   │   │ Test_ERP       │   ← You import sample data into these
│ (6 records)     │   │ (6 records)    │
└────────┬────────┘   └───────┬────────┘
         │                    │
         └────────┬───────────┘
                  ▼
         ┌────────────────┐
         │ Test_Master_DSR│   ← Script writes merged data here
         │ (4 records)    │
         └────────────────┘
```

Expected result: 6+6 input records → **4 merged output rows**

---

## STEP 1: Create Form "Test_PreAlert"

Go to: **Your App → Create New → Form → Blank**

Form Name: `Test_PreAlert`

Add these fields (in order):

| # | Field Name | Field Type
|---|-----------|-----------|
| 1 | `Job_No` | Number 
| 2 | `Importer` | dropdown 
| 3 | `Client_Ref_No` | Single Line 
| 4 | `Mode` | radio 
| 6 | `MAWB_No` | Single Line 
| 7 | `HAWB_No` | Single Line 
| 8 | `BE_No` | Number 
| 9 | `BE_Type` | radio 
| 10 | `BE_Date` | Date 
| 11 | `ETA` | Date
Parent Inbond Job (Lookup Field)
----------new-------------
'Invoice_Number' - single line (from Checklist)
'Invoice_Date' - date (from Checklist)
'Total_Inv_Value' - single line (from Checklist)
'Supplier_Exporter' - single line (from Checklist)
'Model' - single line (from Checklist)
'Qty' - number (from Checklist)
'Description' - multi line (from Checklist)
'Port' - single line (from Checklist)
'ATA' - datetime
'Container No' - single line
'DO Amount' - decimal (?)
'Pre alert Recd On' - added time of pre-alert
'Checklist verified on' - date
'Checklist Verified By Client On' - date
'OOC date' - date-time
'Duty called on' - datetime
'Duty paid by client on' - datetime
'Dispatch date' - date-time
'Vehicle No' - single line (?)
'Vehicle Type'  (?)

> 💡 **Tip:** After creating the form, go to Form Properties and **uncheck** "Show Add Notes" and "Show Approval" to keep it clean.

---

## STEP 2: Create Form "Test_ERP"

Form Name: `Test_ERP`

| # | Field Name | Field Type
|---|-----------|-----------
| 1 | `Invoice_Number` | Single Line - 
| 2 | `BE_Type` | dropdown 
| 3 | `BE_No` | number 
| 4 | `BE_Date` | Date 
| 5 | `Supplier_Exporter` | Single Line 
| 6 | `Description` | multi Line 
| 11 | `Total_Basic_Duty` | Decimal 
'Job_No' lookup to test pre-alert
'Importer' single line
'Assbl_Value' decimal
'HAWB_No' single line
'Invoice_Date' date
----------new-------------
'Invoice_Date' - date
'Container No' - single line
'Total_Inv_Value' - single line
'Model' - single line (add in ERP)
'Qty' - number (add in ERP) (?)
'Demurrage/Detention' -  decimal (add in ERP)
'IGM Date' - date (add in ERP)
'Inward Date' - date
'Chargeable Weight' - decimal
'Customs Duty' - decimal
'No of Pkgs' - number

---

## STEP 3: Create Form "Test_Master_DSR"

Form Name: `Test_Airtel_DSR`

| # | Field Name | Field Type 
|---|-----------|-----------|
| **Core** | | | |
| 1 | `Invoice_Number` | Single Line - from Pre-Alert Checklist (previously ERP)
| 5 | `Mode` | Single Line - from pre-alert DELETED
| 3 | `Supplier_Exporter` | Single Line - from Pre-Alert Checklist
| 4 | `Description` | multi Line  - from Pre-Alert Checklist (previously ERP)
Current Status - single line - manual
| 14 | `ETA` | Date  - from pre-alert DELETED
| 9 | `Inbond_Job_No` | Single Line 
| 12 | `Inbond_BE_No` | Single Line DELETED
| 13 | `Inbond_BE_Date` | Date DELETED
| 21 | `Exbond_Job_No` | Single Line 
| 22 | `Exbond_BE_No` | Single Line DELETED
| 23 | `Exbond_BE_Date` | Date DELETED
MAWB_No - single line - from pre-alert as well as ERP DELETED
HAWB_No - single line - from pre-alert as well as ERP DELETED
Assbl_Value - decimal - of exbond job no DELETED 
Duty - decimal - Customs Duty from ERP (rounded) of Exbond job no DELETED
----------new-------------
'Invoice_Date' - date - from Pre-Alert Checklist
'Total_Inv_Value' - single line (remove currency) - from Pre-Alert Checklist
'Model_No' - single line - from Pre-Alert Checklist
'Qty' - number - from Pre-Alert Checklist
'Port' - dropdown (MUM, NHAVA SHEVA) - from Pre-Alert Checklist
'Demurrage/Detention' -  decimal - from ERP
'WPC_Expiry_Date' - date - manual
'TAT_Inbond' - number (?)
'TAT_Outbond' - number (?)
'FTWZ Storage Approx' - single line - manual
'Duty Interest' - decimal - manual
'PO No' - single line - manual
'Circle' - dropdown (need to fill up the dropdown once)
'Concern Person' - dropdown (based on Circle)
'FTA No' - single line - manual
'FTA Date' - date - manual 
'Original FTA Recd Date' - date - manual
'IGM Date' - date - from ERP
'BE Type' - single line (?)
'ATA' - datetime - from pre-alert
'Arrived at FTWZ' - date - manual
'Pkgs' - number - from ERP No of Pkgs
'Chargeable Weight' - decimal - from ERP
'Container No' - single line - from pre-alert as well as ERP (update after updated in any)
'Line / Forwarder' - dropdown - manual (need to fill up dropdown list)
'DO Amount' - from pre-alert (?)
'Pre-alert recd on' - Added time of pre-alert (?)
'Inbond Checklist sent on' - checklist verified on of pre-alert
'Inbond Checklist approved on' - Checklist verified by Client on of pre-alert
'Req ID Inbond' - single line - manual
'Inbond Cleared On' - date-time - OOC of pre-alert
'Remarks Inbond' - multiline

'Outbond Process' - date (?)
'Outbond Checklist sent on' - checklist verified on of pre-alert
'Outbond Checklist approved on' - Checklist verified by Client on of pre-alert
'Duty req sent on' - datetime - from pre-alert Duty called on
'Duty received' - datetime - from pre-alert Duty paid by client on
'Duty TAT' - number (?)
'BE ooc date' - date - OOC of pre-alert (?)
'Cleared / dispatched' - date-time - Dispatch date from pre-alert
'Vehicle No' - single line - from pre-alert (?)
'move by' - single line - manual
'Vehicle type' -  single line - from pre-alert
'Tpt fright' - single line - manual
'Delivery date' - date - manual
'Remarks' - manual - multi line
'Other charges' - manual - single line
'Demurrage mail sent date' - date - manual
'Demurrage approved date'- date - manual
'Form i req date' - date - manual
'Form i recd date' - date - manual

---

## STEP 4: Import Sample Data

### 4a. Import into Test_PreAlert

Go to: **Test_PreAlert report → (⋮) More → Import Data**

Upload the file: `test_import_prealert.csv` (provided in this folder)

Map the columns:
- Job_No → Job_No
- Importer → Importer
- Client_Ref_No → Client_Ref_No
- ... (all should auto-map if names match)

**Expected: 6 records imported**

### 4b. Import into Test_ERP

Go to: **Test_ERP report → (⋮) More → Import Data**

Upload the file: `test_import_erp.csv` (provided in this folder)

Map columns similarly.

**Expected: 6 records imported**

---

## STEP 5: Add the Deluge Script

Go to: **Settings → Workflow → Functions → + New Function**

- **Function Name:** `consolidate_DSR_Test`
- **Namespace:** (leave default)
- **Workflow:** Standalone

Paste the contents of `zoho_deluge_test.dg` (provided in this folder).

Click **Save**.

---

## STEP 6: Run the Script

Go to: **Settings → Workflow → Functions → consolidate_DSR_Test**

Click **Execute** (the play ▶ button).

Check the execution log (click on the function's log icon).

---

## STEP 7: Verify the Output

Go to: **Test_Master_DSR report → View All Records**

### Expected Results: 4 Records

| # | Invoice Number | Importer | Inbond Job | Exbond Job | Master Status |
|---|---------------|----------|------------|------------|---------------|
| 1 | 250903089 | BHARTI AIRTEL LIMITED | 51725 | 51749 | Fully Closed (No POD) |
| 2 | TEL-INV-001 | TESLA MOTORS INDIA | 51800 | 51830 | Fully Closed (No POD) |
| 3 | BMW-INV-001 | BMW INDIA PVT LTD | 51900 | *(empty)* | In Bond / Warehoused |
| 4 | SIE-INV-001 | SIEMENS INDIA | 51950 | *(empty)* | Arrived - Clearance Pending |

### What to Check:
- [ ] **Row count:** Should be 4 (not 6 or 8)
- [ ] **BHARTI AIRTEL:** Has BOTH Job 51725 and 51749 in the same row
- [ ] **TESLA:** Has BOTH Job 51800 and 51830 in the same row
- [ ] **BMW:** Has only Inbond Job 51900, Exbond columns are empty
- [ ] **SIEMENS:** Has only Inbond Job 51950, Exbond columns are empty
- [ ] **Financial data:** BHARTI AIRTEL shows Inbond Duty = 325894.60, Exbond Duty = 0.00
- [ ] **Status:** Each row has a correct Master_Status value

---

## Troubleshooting

### "Function failed with error"
- Check the **execution log** for the specific error line
- Most common issue: **field name mismatch** — verify the form field link names match the script
- In Zoho Creator, the field LINK name (used in scripts) may differ from the DISPLAY name
  - Go to Form → Field Properties → check "Field Link Name"

### "0 records in Master_DSR"
- Check that Test_PreAlert has records with `BE_Type` = "SEZ-Z"
- Check the script's report names match your actual form/report names

### "Records created but financial data is empty"
- Verify Test_ERP has records
- Check that `BE_No` values match between Test_PreAlert and Test_ERP
- Both should have: 5085962, 5132432, 5200001, 5200045, 5300001, 5400001

### "Exbond not matching"
- Verify the Inbond's `HAWB_HBL` value matches the Exbond's `Client_Ref_No`
- BHARTI AIRTEL: Inbond HAWB = `4840736353`, Exbond Client Ref = `4840736353` ✓
- TESLA: Inbond HAWB = `9876543210`, Exbond Client Ref = `9876543210` ✓
