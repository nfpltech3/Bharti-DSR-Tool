# Zoho Creator Setup Guide — DSR Consolidation

## 1. Prerequisites

You need these existing data sources in your Zoho Creator app:
- **`View_All_Jobs`** — Report from the Pre-Alert form (operational/workflow data)
- **`View_ERP_data`** — Report from Logisys ERP import (financial/customs data)

---

## 2. Create the `Master_DSR` Form

In **Zoho Creator → Your App → Forms**, create a new form called **`Master_DSR`**.

### 2.1 Core Identification Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Invoice_Number` | Single Line | **Unique** — this is the Inbond's "Tracking No / Client Ref No" |
| `Importer` | Single Line | e.g., BHARTI AIRTEL LIMITED |
| `Supplier_Exporter` | Single Line | From ERP |
| `Description` | Multi Line | Product description from ERP |
| `CTH_No` | Single Line | Customs Tariff Heading |
| `Mode` | Dropdown | Air / Sea (FCL) / Sea (LCL) |
| `Branch` | Single Line | MUMBAI, DELHI, etc. |
| `Custom_House` | Single Line | From ERP |
| `Job_Owner` | Single Line | From ERP |

### 2.2 Inbond Phase Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Inbond_Job_No` | Number | Job No from Pre-Alert (SEZ-Z) |
| `MAWB_MBL` | Single Line | Master AWB / Master BL |
| `HAWB_HBL` | Single Line | House AWB / House BL — **also the link to Exbond** |
| `Inbond_BE_No` | Single Line | Bill of Entry number |
| `Inbond_BE_Date` | Date | |
| `ETA` | Date | Estimated Time of Arrival |
| `ATA` | Date-Time | Actual Time of Arrival |
| `Segregation_Time` | Date-Time | |
| `Inbond_OOC_Date` | Date-Time | Out of Charge |
| `Inbond_Dispatch_Date` | Date-Time | Port → Warehouse |
| `Inbond_Assessment_By` | Single Line | APR / RMS |
| `Inbond_TAT` | Number | Total Turnaround Time (days) |
| `Inbond_ATA_to_OOC` | Number | Days from arrival to clearance |
| `Inbond_Shipment_Status` | Dropdown | Open / Closed |
| `Inbond_BE_Filed_On` | Date-Time | |
| `Inbond_Duty_Paid_On` | Date | |
| `Inbond_Purchase_Booking` | Date-Time | |
| `Inbond_Invoice_Prepared` | Date-Time | |

### 2.3 Exbond Phase Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Exbond_Job_No` | Number | Job No from Pre-Alert (SEZ-T), nullable |
| `Exbond_BE_No` | Single Line | |
| `Exbond_BE_Date` | Date | |
| `Exbond_ATA` | Date-Time | |
| `Exbond_OOC_Date` | Date-Time | |
| `Exbond_Dispatch_Date` | Date-Time | Final dispatch from warehouse |
| `Actual_Delivery_Date` | Date | Final delivery to client |
| `Exbond_Assessment_By` | Single Line | |
| `Exbond_TAT` | Number | |
| `Exbond_ATA_to_OOC` | Number | |
| `Exbond_Shipment_Status` | Dropdown | Open / Closed |
| `Exbond_BE_Filed_On` | Date-Time | |
| `Exbond_Duty_Paid_On` | Date | |
| `Exbond_Purchase_Booking` | Date-Time | |
| `Exbond_Invoice_Prepared` | Date-Time | |

### 2.4 Financial Fields (from ERP)

| Field Name | Type | Notes |
|------------|------|-------|
| `Inv_Currency` | Single Line | USD / EUR / INR |
| `Total_Inv_Value` | Single Line | e.g., "18165.81 USD" |
| `Assbl_Value` | Decimal | Assessable Value |
| `Inbond_Basic_Duty` | Currency | |
| `Inbond_SWS_Duty` | Currency | Social Welfare Surcharge |
| `Inbond_IGST` | Currency | |
| `Exbond_Basic_Duty` | Currency | |
| `Exbond_SWS_Duty` | Currency | |
| `Exbond_IGST` | Currency | |
| `Total_Duties_Combined` | Currency | Auto-computed sum |

### 2.5 Derived Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Master_Status` | Single Line | Auto-derived by script |
| `Vessel_Flight` | Single Line | From ERP |
| `No_Of_Pkgs` | Number | From ERP |
| `Port_of_Shipment` | Single Line | From ERP |

### 2.6 Master Status Picklist Values

```
Inbond In Progress
In Transit - ETA Set
Arrived - Clearance Pending
Inbond Cleared (OOC)
In Bond / Warehoused
Inbond Closed - Awaiting Exbond
Exbond In Progress
Exbond BE Filed
Exbond Arrived - Clearance Pending
Exbond Cleared (OOC)
In Transit (Final Dispatch)
Delivered
Fully Closed & Delivered
Fully Closed (No POD)
Orphan Exbond (No Inbond Found)
```

---

## 3. How the Linking Works

```
PRE-ALERT (View_All_Jobs)          ERP (View_ERP_data)
┌──────────────────────┐           ┌───────────────────────┐
│ Inbond (SEZ-Z)       │           │ Inbond (SEZ-Z)        │
│ Job No: 51725        │           │ Invoice No: 250903089 │
│ Client Ref: 250903089│←── FK ───→│ BE No: 5085962        │
│ HAWB: 4840736353     │    BE No  │ Duties: 716,316.40    │
└─────────┬────────────┘           └───────────────────────┘
          │ HAWB = Client Ref
┌─────────┴────────────┐           ┌───────────────────────┐
│ Exbond (SEZ-T)       │           │ Exbond (SEZ-T)        │
│ Job No: 51749        │           │ Invoice No: 250903089 │
│ Client Ref: 484073.. │←── FK ───→│ BE No: 5132432        │
│                      │    BE No  │ Duties: 293,305.20    │
└──────────────────────┘           └───────────────────────┘
```

**Key Insight:** The Inbond's `HAWB/HBL` field value (`4840736353`) becomes the Exbond's `Tracking No / Client Ref No`. This is the primary link within Pre-Alert data.

---

## 4. Create Reports

### 4.1 Master DSR Report

1. Go to **Reports → New Report**
2. Source Form: `Master_DSR`
3. Report Name: `DSR_Master_View`
4. Suggested column groups:

**Group 1: Overview**
- Invoice Number | Importer | Supplier | Description | Mode | Master Status

**Group 2: Inbond Timeline**
- Inbond Job No | ETA | ATA | Inbond OOC Date | Inbond Dispatch Date | Inbond TAT

**Group 3: Exbond Timeline**
- Exbond Job No | Exbond OOC Date | Exbond Dispatch Date | Actual Delivery Date | Exbond TAT

**Group 4: Financial**
- Total Inv Value | Inbond Duties (Basic + SWS + IGST) | Exbond Duties | Total Combined

5. **Conditional formatting** for Master Status:
   - `Fully Closed & Delivered` → 🟢 Green
   - `In Bond / Warehoused` / `Inbond Closed - Awaiting Exbond` → 🟡 Yellow
   - `In Transit` → 🔵 Blue
   - `Arrived - Clearance Pending` → 🟠 Orange
   - `Orphan Exbond` → 🔴 Red

### 4.2 Client-Facing Report (Filtered by Importer)

For client-specific views:
1. Clone `DSR_Master_View`
2. Add criteria: `Importer == zoho.loginuserrecord.Importer`
3. Hide financial columns (duties) if clients shouldn't see them

---

## 5. Schedule the Script

### 5.1 Daily Full Rebuild

1. **Settings → Workflow → Schedules**
2. Create new schedule:
   - **Name:** `DSR_Nightly_Consolidation`
   - **Frequency:** Daily at 2:00 AM (after Logisys data sync)
   - **Function:** `mergeDSR_InbondExbond`

### 5.2 Real-Time Incremental

1. Go to **Pre_Alert** form → **Workflow → Form Actions**
2. On **Record Create** and **Record Edit**, add:

```deluge
// Trigger incremental DSR update
job_no = input.Job_No;
be_type = input.BE_Type;
be_no = input.BE_No;

if (job_no != null && be_type != null)
{
    runDSR_Incremental(job_no, be_type, be_no);
}
```

---

## 6. Dashboard Cards

### Card 1: Total Active Shipments
```deluge
count = Master_DSR[Master_Status != "Fully Closed & Delivered" && Master_Status != "Fully Closed (No POD)"].count();
return count;
```

### Card 2: In Bond / Awaiting Exbond
```deluge
count = Master_DSR[Master_Status == "In Bond / Warehoused" || Master_Status == "Inbond Closed - Awaiting Exbond"].count();
return count;
```

### Card 3: In Transit
```deluge
count = Master_DSR[Master_Status == "In Transit (Final Dispatch)"].count();
return count;
```

### Card 4: Delivered This Week
```deluge
week_start = zoho.currentdate.subDay(7);
count = Master_DSR[Master_Status == "Fully Closed & Delivered" && Actual_Delivery_Date >= week_start].count();
return count;
```

### Card 5: Total Duties This Month
```deluge
month_start = zoho.currentdate.toStartOfMonth();
records = Master_DSR[Inbond_BE_Date >= month_start];
total = 0;
for each rec in records
{
    total = total + ifnull(rec.Total_Duties_Combined, 0);
}
return total;
```

---

## 7. Testing Checklist

Before going live, verify:

- [ ] Import sample Pre-Alert data into Pre_Alert form
- [ ] Import sample ERP data into View_ERP_data source
- [ ] Run `mergeDSR_InbondExbond()` manually (Settings → Functions → Execute)
- [ ] Check `Master_DSR` report shows 4 merged rows (2 merged + 2 inbond-only)
- [ ] Verify BHARTI AIRTEL: shows both Job 51725 (Inbond) and 51749 (Exbond)
- [ ] Verify BMW: shows only Inbond, Exbond columns are empty
- [ ] Verify ERP enrichment: duties, supplier, description populated
- [ ] Verify status derivation:
  - BHARTI AIRTEL → "Fully Closed (No POD)" (both Closed but no delivery date)
  - SIEMENS → "Arrived - Clearance Pending" (has ATA but no OOC)
- [ ] Add a new Exbond record for BMW → verify merge updates
- [ ] Check client-facing report filtering works
- [ ] Test Dashboard cards show correct counts

---

## 8. Maintenance Notes

- **Data freshness:** The full rebuild clears and recreates all records. This ensures consistency but means the Master_DSR form's `Added_User` and timestamps reset nightly.
- **Performance:** For >1000 records, consider batching the ERP lookup or using Zoho's built-in join features.
- **Form permissions:** Make Master_DSR read-only for all users except the scheduled script.
