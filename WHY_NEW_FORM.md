# Why You Need a New Form — And Why It's Simpler Than You Think

## The Core Problem

You're right — whether you duplicate the ERP report or the Pre-Alert report, you'll always have **two rows** because that's how Logisys stores the data. There's no way around it within the existing forms.

```
                     CURRENT STATE
    ┌──────────────────────────────────────────────────┐
    │  View_ERP_data (or View_All_Jobs)                │
    │                                                   │
    │  Row 1: Job 51725 | SEZ-Z | Inbond stuff...     │ ← Client sees this
    │  Row 2: Job 51749 | SEZ-T | Exbond stuff...     │ ← AND this 😩
    │                                                   │
    │  Even with Importer filter = "BHARTI AIRTEL"     │
    │  → Still 2 rows!                                  │
    └──────────────────────────────────────────────────┘
```

## Why a New Form Is the Only Clean Solution

In Zoho Creator: **1 record in a form = 1 row in a report**. That's a hard rule.

To show ONE row per shipment, you need ONE record per shipment. The only way to achieve that is to create a new form where the merge script writes a single combined record.

## But Here's the Good News — It's Very Little Work

### What You Actually Need to Do:

| Step | What | Effort |
|------|------|--------|
| 1 | Create `Master_DSR` form in Zoho Creator | 10 minutes (copy field list below) |
| 2 | Paste the Deluge script | 5 minutes |
| 3 | Schedule it to run daily | 2 minutes |
| 4 | Create a report on Master_DSR form | 5 minutes |
| | **Total** | **~22 minutes** |

### What You DON'T Need to Do:
- ❌ No manual data entry — the script fills the form automatically
- ❌ No changes to existing Pre-Alert or ERP forms
- ❌ No changes to existing reports or workflows
- ❌ No API setup — it reads from existing Zoho forms directly

## Quick-Start: Minimal Form Fields

You don't need 40+ fields. Start with just these **20 essential fields**:

```
FORM NAME: Master_DSR

── SECTION 1: Identification ──
1.  Invoice_Number     (Single Line, Unique)
2.  Importer           (Single Line)
3.  Supplier_Exporter  (Single Line)
4.  Description        (Multi Line)
5.  Mode               (Single Line)

── SECTION 2: Inbond Phase ──
6.  Inbond_Job_No      (Single Line)
7.  HAWB_HBL           (Single Line)
8.  Inbond_BE_No       (Single Line)
9.  ETA                (Date)
10. ATA                (Date-Time)
11. Inbond_OOC_Date    (Date-Time)
12. Inbond_Dispatch_Date (Date-Time)

── SECTION 3: Exbond Phase ──
13. Exbond_Job_No      (Single Line)    ← Empty until Exbond is filed
14. Exbond_BE_No       (Single Line)
15. Exbond_OOC_Date    (Date-Time)
16. Exbond_Dispatch_Date (Date-Time)
17. Actual_Delivery_Date (Date)

── SECTION 4: Status ──
18. Master_Status      (Single Line)
19. Inbond_Shipment_Status (Single Line)
20. Exbond_Shipment_Status (Single Line)
```

**That's it.** You can always add more fields later (duties, TAT, etc.) without breaking anything.

## What the Client Sees (After Setup)

```
Master DSR Report (filtered by Importer = BHARTI AIRTEL)
┌─────────────┬───────────┬───────────┬───────────┬────────────┬──────────────────────┐
│ Invoice No  │ Inbond    │ Exbond    │ Inbond    │ Exbond     │ Status               │
│             │ Job No    │ Job No    │ OOC Date  │ Dispatch   │                      │
├─────────────┼───────────┼───────────┼───────────┼────────────┼──────────────────────┤
│ 250903089   │ 51725     │ 51749     │ 15-Oct    │ 18-Oct     │ Fully Closed (No POD)│
│ 250903102   │ 51800     │ —         │ 20-Oct    │ —          │ In Bond / Warehoused │
└─────────────┴───────────┴───────────┴───────────┴────────────┴──────────────────────┘

↑ One row per shipment! Both Job Numbers visible! ✅
```

## The Alternative You Were Considering (And Why It Doesn't Work)

> "Maybe we can have two job number fields — inbond and exbond but then we will have to create a new form."

You're exactly right — **and that's the correct approach**. There's no way to add "Exbond Job No" to the ERP report without a new form because:

1. ERP report is tied to the ERP form
2. The ERP form has one `Job No` field per record
3. You can't combine two records' fields into one row within the same form's report

**The new form IS the solution.** The Deluge script just automates filling it.

## Data Flow Summary

```
    Existing (untouched)                    New (automated)
    ┌──────────────┐                       ┌──────────────────┐
    │ Pre_Alert    │──┐                    │  Master_DSR      │
    │ (View_All_   │  │    Deluge Script   │  (ONE row per    │
    │  Jobs)       │  ├───────────────────►│   shipment)      │
    │              │  │   Runs nightly     │                  │
    │ 2 rows per   │  │   or on-demand     │  Client sees     │
    │ shipment     │  │                    │  this report     │
    └──────────────┘  │                    └──────────────────┘
    ┌──────────────┐  │
    │ View_ERP_data│──┘
    │              │
    │ 2 rows per   │
    │ shipment     │
    └──────────────┘

    Nothing changes       →      Everything merges here
    here!                         automatically!
```
