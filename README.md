# DSR Consolidation: Inbond ↔ Exbond Merge Logic

## 1. Problem Statement

In **Logisys**, a single bonded warehousing shipment is split into **two separate Job records**:

| Phase | BE Type (Pre-Alert) / Type Of B/E (ERP) | Example Job | Purpose |
|-------|------------------------------------------|-------------|---------|
| **Inbond** (Arrival) | `SEZ-Z` | 51725 | Arrival → Customs → Warehousing |
| **Exbond** (Dispatch) | `SEZ-T` | 51749 | Dispatch → Exit → Delivery |

**Goal:** Merge both into **one row per transaction** in the Daily Status Report (DSR).

---

## 2. Data Sources in Zoho Creator

### Source A: `View_All_Jobs` (Pre-Alert Form Report)
Contains **operational & workflow** data — dates, status flags, TAT, checklist progress, billing milestones.

### Source B: `View_ERP_data` (Logisys ERP Data)
Contains **financial & customs** data — duties, assessable values, CTH, description, supplier, invoice details.

---

## 3. Linking Logic (3-Layer)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LINKING ARCHITECTURE                              │
│                                                                            │
│  LAYER 1: ERP ↔ ERP (Inbond + Exbond within View_ERP_data)                │
│  ─────────────────────────────────────────────────────────                  │
│  FK: Invoice Number (both records share "250903089")                       │
│  Differentiator: Type Of B/E = "SEZ-Z" vs "SEZ-T"                         │
│                                                                            │
│  LAYER 2: Pre-Alert ↔ Pre-Alert (within View_All_Jobs)                    │
│  ───────────────────────────────────────────────────────                    │
│  FK: Inbond HAWB/HBL = Exbond "Tracking No / Client Ref No"               │
│      (both = "4840736353")                                                 │
│  Differentiator: BE Type = "SEZ-Z" vs "SEZ-T"                             │
│                                                                            │
│  LAYER 3: Pre-Alert ↔ ERP (Cross-Source)                                  │
│  ────────────────────────────────────────                                   │
│  FK: BE No (same value in both sources)                                    │
│      Inbond: 5085962 in both Pre-Alert and ERP                             │
│      Exbond: 5132432 in both Pre-Alert and ERP                             │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Visual Flow

```
  View_ERP_data                               View_All_Jobs (Pre-Alert)
  ┌─────────────────┐                         ┌──────────────────────┐
  │ Inbond (SEZ-Z)  │                         │  Inbond (SEZ-Z)      │
  │ Invoice: 250903 │◄─── BE No: 5085962 ───►│  Job No: 51725       │
  │ BE No: 5085962  │                         │  BE No: 5085962      │
  │ Duties, Values  │                         │  HAWB: 4840736353    │
  └────────┬────────┘                         └──────────┬───────────┘
           │                                              │
   Invoice │ Number                              HAWB/HBL │ = Client Ref
   (same)  │                                              │
           │                                              │
  ┌────────┴────────┐                         ┌──────────┴───────────┐
  │ Exbond (SEZ-T)  │                         │  Exbond (SEZ-T)      │
  │ Invoice: 250903 │◄─── BE No: 5132432 ───►│  Job No: 51749       │
  │ BE No: 5132432  │                         │  BE No: 5132432      │
  │ Duties, Values  │                         │  Client Ref: 4840... │
  └─────────────────┘                         └──────────────────────┘
```

---

## 4. Complete Field Inventory

### 4.1 Pre-Alert Fields (View_All_Jobs) — Operational

#### Core Identification
| Field | Inbond Example | Exbond Example |
|-------|---------------|----------------|
| Job No | 51725 | 51749 |
| Importer | BHARTI AIRTEL LIMITED | BHARTI AIRTEL LIMITED |
| Tracking No / Client Ref No | 250903089 | 4840736353 |
| Mode | Air | Sea (LCL) |
| Branch | MUMBAI | MUMBAI |
| MAWB/MBL | 607-51010433 | *(empty)* |
| HAWB/HBL | 4840736353 | *(empty)* |
| BE No | 5085962 | 5132432 |
| BE Type | SEZ-Z | SEZ-T |
| BE Date | 14-Oct-2025 | 16-Oct-2025 |

#### Key Dates (Operational)
| Field | Inbond | Exbond | Notes |
|-------|--------|--------|-------|
| ETA | 14-Oct-2025 | 16-Oct-2025 | |
| ATA | 13-Oct-2025 19:29 | 16-Oct-2025 13:20 | |
| Segregation time | 13-Oct-2025 23:25 | | |
| OOC date | 15-Oct-2025 20:51 | 17-Oct-2025 13:34 | |
| Dispatch Date | 15-Oct-2025 21:52 | 18-Oct-2025 13:35 | |
| Actual Delivery Date | | | |

#### Workflow / Billing Milestones
| Field | Inbond | Exbond |
|-------|--------|--------|
| All docs received confirmation on | 13-Oct-2025 13:35 | 16-Oct-2025 13:13 |
| BE filed on | 14-Oct-2025 10:54 | 16-Oct-2025 13:14 |
| Duty paid by client on | 14-Oct-2025 | 16-Oct-2025 |
| Purchase booking done on | 04-Nov-2025 | 30-Oct-2025 |
| Invoice prepared on | 04-Nov-2025 | 01-Nov-2025 |
| Shipment Status | Closed | Closed |
| Total TAT | 2 | 1 |
| ATA to OOC | 2 | 1 |

### 4.2 ERP Fields (View_ERP_data) — Financial

| Field | Inbond | Exbond | Notes |
|-------|--------|--------|-------|
| Invoice Number | 250903089 | 250903089 | **FK — same for both** |
| Type Of B/E | SEZ-Z | SEZ-T | |
| BE No | 5085962 | 5132432 | Cross-source link |
| Assbl. Value | 1629473.16 | 1629473.16 | |
| CTH No | 85176290 | 85176290 | |
| Description | CWSSFTA01 WAVELENGTH... | CWSSFTA01 WAVELENGTH... | |
| Custom House | JNPT SEZ, NAVI MUMBAI | JNPT SEZ, NAVI MUMBAI | |
| Supplier/Exporter | CIENA COMMUNICATIONS | CIENA COMMUNICATIONS | |
| IGST Amount | 357832.30 | 293305.20 | **Different!** |
| Total Basic Duty | 325894.60 | 0.00 | **Different!** |
| Total SWS Duty | 32589.50 | 0.00 | **Different!** |
| Total Inv Value | 18165.81 USD | 18165.81 USD | |
| Job Owner | VINOD TAWADE | VINOD TAWADE | |

---

## 5. Master Transaction Output Schema

### Client-Facing DSR Row

| # | Column | Source | Phase | Notes |
|---|--------|--------|-------|-------|
| **Identification** | | | | |
| 1 | Invoice Number | ERP | Common | Primary FK |
| 2 | Importer | Pre-Alert | Common | |
| 3 | Supplier / Exporter | ERP | Common | |
| 4 | Description | ERP | Common | Product description |
| 5 | CTH No | ERP | Common | |
| 6 | Mode | Pre-Alert | Inbond | Air / Sea |
| 7 | Branch | Pre-Alert | Common | |
| **Inbond Phase** | | | | |
| 8 | Inbond Job No | Pre-Alert | Inbond | Job No (SEZ-Z) |
| 9 | MAWB/MBL | Pre-Alert | Inbond | |
| 10 | HAWB/HBL | Pre-Alert | Inbond | Also links to Exbond |
| 11 | Inbond BE No | Pre-Alert/ERP | Inbond | 5085962 |
| 12 | Inbond BE Date | Pre-Alert | Inbond | |
| 13 | ETA | Pre-Alert | Inbond | |
| 14 | ATA | Pre-Alert | Inbond | |
| 15 | Inbond OOC Date | Pre-Alert | Inbond | Out of Charge |
| 16 | Inbond Dispatch Date | Pre-Alert | Inbond | Port → Warehouse |
| 17 | Bonding Date | Derived | Inbond | (if tracked separately) |
| 18 | Inbond Total TAT | Pre-Alert | Inbond | |
| 19 | Inbond ATA to OOC | Pre-Alert | Inbond | Days |
| **Exbond Phase** | | | | |
| 20 | Exbond Job No | Pre-Alert | Exbond | Job No (SEZ-T) |
| 21 | Exbond BE No | Pre-Alert/ERP | Exbond | 5132432 |
| 22 | Exbond BE Date | Pre-Alert | Exbond | |
| 23 | Exbond OOC Date | Pre-Alert | Exbond | |
| 24 | Exbond Dispatch Date | Pre-Alert | Exbond | Final dispatch |
| 25 | Actual Delivery Date | Pre-Alert | Exbond | |
| 26 | Exbond Total TAT | Pre-Alert | Exbond | |
| 27 | Exbond ATA to OOC | Pre-Alert | Exbond | Days |
| **Financial (from ERP)** | | | | |
| 28 | Total Inv Value | ERP | Common | |
| 29 | Inv Currency | ERP | Common | |
| 30 | Assbl. Value | ERP | Inbond | |
| 31 | Inbond Basic Duty | ERP | Inbond | 325894.60 |
| 32 | Inbond SWS Duty | ERP | Inbond | 32589.50 |
| 33 | Inbond IGST | ERP | Inbond | 357832.30 |
| 34 | Exbond Basic Duty | ERP | Exbond | 0.00 |
| 35 | Exbond SWS Duty | ERP | Exbond | 0.00 |
| 36 | Exbond IGST | ERP | Exbond | 293305.20 |
| 37 | Total Duties (Combined) | Derived | — | Sum of all duties |
| **Billing & Workflow** | | | | |
| 38 | Inbond Invoice Prepared | Pre-Alert | Inbond | |
| 39 | Exbond Invoice Prepared | Pre-Alert | Exbond | |
| 40 | Shipment Status Inbond | Pre-Alert | Inbond | |
| 41 | Shipment Status Exbond | Pre-Alert | Exbond | |
| 42 | **Master Status** | **Derived** | — | See logic below |

---

## 6. Status Derivation Logic

```
IF Exbond Pre-Alert record does NOT exist:
    IF Inbond Dispatch Date exists     → "📦 In Bond / Warehoused"
    ELIF Inbond OOC date exists        → "✅ Inbond Cleared"
    ELIF ATA exists                    → "🛬 Arrived — Clearance Pending"
    ELIF ETA exists                    → "🕐 In Transit — ETA Set"
    ELSE                               → "📝 Inbond Filing In Progress"

IF Exbond Pre-Alert record EXISTS:
    IF Actual Delivery Date exists     → "✅ Delivered"
    ELIF Exbond Dispatch Date exists   → "🚚 In Transit (Final Dispatch)"
    ELIF Exbond OOC date exists        → "✅ Exbond Cleared"
    ELIF Exbond ATA exists             → "🛬 Exbond Arrived — Clearance Pending"
    ELSE                               → "📝 Exbond In Progress"

SPECIAL:
    IF both Shipment Status = "Closed" → "✅ Fully Closed"
```

---

## 7. Algorithm (Pseudocode)

```
ALGORITHM: MergeDSR_ThreeLayerLink

INPUT:
    pre_alert_records[] — from View_All_Jobs
    erp_records[]       — from View_ERP_data
OUTPUT:
    master_dsr[]        — merged single-row records

═══════════════════════════════════════════════════════════
STEP 1: PARTITION Pre-Alert by BE Type
═══════════════════════════════════════════════════════════
    pa_inbond[]  ← FILTER pre_alert_records WHERE BE_Type == "SEZ-Z"
    pa_exbond[]  ← FILTER pre_alert_records WHERE BE_Type == "SEZ-T"

═══════════════════════════════════════════════════════════
STEP 2: PARTITION ERP by Type Of B/E
═══════════════════════════════════════════════════════════
    erp_inbond[] ← FILTER erp_records WHERE Type_Of_BE == "SEZ-Z"
    erp_exbond[] ← FILTER erp_records WHERE Type_Of_BE == "SEZ-T"

═══════════════════════════════════════════════════════════
STEP 3: BUILD LOOKUP MAPS
═══════════════════════════════════════════════════════════
    // Map Pre-Alert Exbond by "Tracking No / Client Ref No"
    pa_exbond_by_ref = {}
    FOR EACH ex IN pa_exbond:
        pa_exbond_by_ref[ex.Tracking_No_Client_Ref_No] = ex

    // Map ERP records by BE No
    erp_by_beno = {}
    FOR EACH e IN erp_records:
        erp_by_beno[e.BE_No] = e

    // Map ERP Exbond by Invoice Number
    erp_exbond_by_invoice = {}
    FOR EACH ex IN erp_exbond:
        erp_exbond_by_invoice[ex.Invoice_Number] = ex

═══════════════════════════════════════════════════════════
STEP 4: MERGE — Inbond is the anchor
═══════════════════════════════════════════════════════════
    master_dsr = []
    consumed_exbond_jobs = SET()

    FOR EACH inb IN pa_inbond:
        master = NEW MasterRow()

        // ── Populate Inbond Pre-Alert fields ──
        master.Invoice_Number      = inb.Tracking_No_Client_Ref_No
        master.Importer            = inb.Importer
        master.Mode                = inb.Mode
        master.Branch              = inb.Branch
        master.Inbond_Job_No       = inb.Job_No
        master.MAWB_MBL            = inb.MAWB_MBL
        master.HAWB_HBL            = inb.HAWB_HBL
        master.Inbond_BE_No        = inb.BE_No
        master.Inbond_BE_Date      = inb.BE_Date
        master.ETA                 = inb.ETA
        master.ATA                 = inb.ATA
        master.Inbond_OOC_Date     = inb.OOC_date
        master.Inbond_Dispatch     = inb.Dispatch_Date
        master.Inbond_TAT          = inb.Total_TAT
        master.Inbond_ATA_to_OOC   = inb.ATA_to_OOC
        master.Inbond_Status       = inb.Shipment_Status

        // ── Enrich with Inbond ERP data (via BE No) ──
        IF inb.BE_No IN erp_by_beno:
            erp_inb = erp_by_beno[inb.BE_No]
            master.Supplier           = erp_inb.Supplier_Exporter
            master.Description        = erp_inb.Description
            master.CTH_No             = erp_inb.CTH_No
            master.Custom_House       = erp_inb.Custom_House
            master.Inv_Currency       = erp_inb.Inv_Currency
            master.Total_Inv_Value    = erp_inb.Total_Inv_Value
            master.Assbl_Value        = erp_inb.Assbl_Value
            master.Inbond_Basic_Duty  = erp_inb.Total_Basic_Duty
            master.Inbond_SWS_Duty    = erp_inb.Total_SWS_Duty
            master.Inbond_IGST        = erp_inb.IGST_Amount
            master.Job_Owner          = erp_inb.Job_Owner

        // ── Match Exbond Pre-Alert (HAWB/HBL link) ──
        hawb = inb.HAWB_HBL
        IF hawb IN pa_exbond_by_ref:
            exb = pa_exbond_by_ref[hawb]
            consumed_exbond_jobs.ADD(exb.Job_No)

            master.Exbond_Job_No       = exb.Job_No
            master.Exbond_BE_No        = exb.BE_No
            master.Exbond_BE_Date      = exb.BE_Date
            master.Exbond_OOC_Date     = exb.OOC_date
            master.Exbond_Dispatch     = exb.Dispatch_Date
            master.Delivery_Date       = exb.Actual_Delivery_Date
            master.Exbond_TAT          = exb.Total_TAT
            master.Exbond_ATA_to_OOC   = exb.ATA_to_OOC
            master.Exbond_Status       = exb.Shipment_Status

            // ── Enrich with Exbond ERP data (via BE No) ──
            IF exb.BE_No IN erp_by_beno:
                erp_exb = erp_by_beno[exb.BE_No]
                master.Exbond_Basic_Duty  = erp_exb.Total_Basic_Duty
                master.Exbond_SWS_Duty    = erp_exb.Total_SWS_Duty
                master.Exbond_IGST        = erp_exb.IGST_Amount

            master.Has_Exbond = TRUE
        ELSE:
            master.Has_Exbond = FALSE

        // ── Derive Master Status ──
        master.Master_Status = DeriveStatus(master)

        // ── Compute Total Duties ──
        master.Total_Duties_Combined = SUM(
            master.Inbond_Basic_Duty,
            master.Inbond_SWS_Duty,
            master.Inbond_IGST,
            master.Exbond_Basic_Duty,
            master.Exbond_SWS_Duty,
            master.Exbond_IGST
        )

        APPEND master TO master_dsr

═══════════════════════════════════════════════════════════
STEP 5: Handle Orphan Exbonds
═══════════════════════════════════════════════════════════
    FOR EACH exb IN pa_exbond:
        IF exb.Job_No NOT IN consumed_exbond_jobs:
            LOG WARNING "Orphan Exbond: Job " + exb.Job_No
            // Create partial master with Exbond-only data
            ...

    RETURN master_dsr
```

---

## 8. Edge Cases

| # | Scenario | Handling |
|---|----------|----------|
| 1 | **Inbond exists, Exbond not yet created** | Normal. Exbond columns are null. Status = "In Bond / Warehoused" |
| 2 | **Exbond exists, no matching Inbond** | Flagged as "Orphan Exbond". Logged. Included with warning. |
| 3 | **HAWB/HBL is empty on Inbond** | Fallback: try matching via ERP Invoice Number |
| 4 | **BE No not found in ERP** | Financial columns stay null. Operational data still shown. |
| 5 | **Duplicate Exbonds for same HAWB** | Keep latest by BE Date, log warning. |
| 6 | **Importer mismatch** | Log warning, still merge, flag record. |
| 7 | **Tracking No / Client Ref No is null** | Skip Exbond matching via this field; try ERP fallback. |
| 8 | **Both Shipment Status = Closed but no Delivery Date** | Master Status = "Closed (No POD)" |
| 9 | **Mode differs (Air vs Sea LCL)** | Use Inbond Mode as primary. Note: Exbond may show "Sea (LCL)" for intra-SEZ movement. |

---

## 9. Architecture Flow

```
    ┌──────────────────┐         ┌──────────────────┐
    │  View_All_Jobs   │         │  View_ERP_data   │
    │  (Pre-Alert)     │         │  (Logisys ERP)   │
    │  Operational     │         │  Financial       │
    └────────┬─────────┘         └────────┬─────────┘
             │                             │
     ┌───────┴───────┐            ┌────────┴────────┐
     ▼               ▼            ▼                 ▼
  ┌───────┐     ┌────────┐   ┌───────┐       ┌────────┐
  │ SEZ-Z │     │ SEZ-T  │   │ SEZ-Z │       │ SEZ-T  │
  │Inbond │     │Exbond  │   │Inbond │       │Exbond  │
  └───┬───┘     └───┬────┘   └───┬───┘       └───┬────┘
      │             │             │               │
      │  HAWB/HBL = │             │   Invoice No  │
      │  Client Ref │             │   (same)      │
      │      ┌──────┘             │      ┌────────┘
      │      │                    │      │
      ▼      ▼                    ▼      ▼
  ┌──────────────┐           ┌──────────────┐
  │ Pre-Alert    │           │   ERP        │
  │ Inbond+      │◄─ BE No ─►│  Inbond+     │
  │ Exbond Pair  │           │  Exbond Pair │
  └──────┬───────┘           └──────┬───────┘
         │                          │
         └──────────┬───────────────┘
                    ▼
           ┌────────────────┐
           │ MASTER DSR ROW │
           │ (One per       │
           │  shipment)     │
           └────────────────┘
```
