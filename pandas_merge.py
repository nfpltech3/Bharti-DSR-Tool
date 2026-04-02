"""
DSR CONSOLIDATION — Python Pandas Script (Production)
======================================================
Merges Inbond (SEZ-Z) and Exbond (SEZ-T) records from:
  - View_All_Jobs (Pre-Alert) — operational/workflow data
  - View_ERP_data (Logisys) — financial/customs data

Into a single Master Transaction row per shipment.

Linking Logic:
  Pre-Alert: Inbond HAWB/HBL = Exbond "Tracking No / Client Ref No"
  ERP: Invoice Number (same for both Inbond and Exbond)
  Cross-source: BE No (same in Pre-Alert and ERP)

Usage:
    # With separate Pre-Alert and ERP files:
    python pandas_merge.py --prealert "all_jobs.csv" --erp "erp_data.csv" --output "master_dsr.xlsx"

    # With Pre-Alert only (no ERP enrichment):
    python pandas_merge.py --prealert "all_jobs.csv" --output "master_dsr.xlsx"

Author: Auto-generated for Nagarkot / ACCS Logistics
"""

import pandas as pd
import numpy as np
import argparse
import logging
from datetime import datetime
from pathlib import Path

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DSR_Consolidation")

# ─── Constants ────────────────────────────────────────────────────────────────
INBOND_TYPE = "SEZ-Z"
EXBOND_TYPE = "SEZ-T"

# Pre-Alert field names (as they appear in View_All_Jobs export)
PA_JOB_NO = "Job No"
PA_IMPORTER = "Importer"
PA_CLIENT_REF = "Tracking No / Client Ref No"
PA_MODE = "Mode"
PA_BRANCH = "Branch"
PA_MAWB = "MAWB/MBL"
PA_HAWB = "HAWB/HBL"
PA_BE_NO = "BE No"
PA_BE_TYPE = "BE Type"
PA_BE_DATE = "BE Date"
PA_ETA = "ETA"
PA_ATA = "ATA"
PA_SEGREGATION = "Segregation time"
PA_OOC = "OOC date"
PA_DISPATCH = "Dispatch Date"
PA_DELIVERY = "Actual Delivery Date"
PA_ASSESSMENT = "Assessment By"
PA_TAT = "Total TAT"
PA_ATA_TO_OOC = "ATA to OOC"
PA_STATUS = "Shipment Status"
PA_BE_FILED = "BE filed on"
PA_DUTY_PAID = "Duty paid by client on"
PA_PURCHASE_BOOKING = "Purchase booking done on"
PA_INVOICE_PREPARED = "Invoice prepared on"
PA_LATE_FILING = "Late BE Filing"

# ERP field names (as they appear in View_ERP_data export)
ERP_INVOICE_NO = "Invoice Number"
ERP_TYPE_BE = "Type Of B/E"
ERP_BE_NO = "BE No"
ERP_BE_DATE = "BE Date"
ERP_SUPPLIER = "Supplier/Exporter"
ERP_DESCRIPTION = "Description"
ERP_CTH = "CTH No"
ERP_CUSTOM_HOUSE = "Custom House"
ERP_INV_CURRENCY = "Inv Currency"
ERP_TOTAL_INV_VALUE = "Total Inv Value"
ERP_ASSBL_VALUE = "Assbl. Value"
ERP_BASIC_DUTY = "Total Basic Duty"
ERP_SWS_DUTY = "Total SWS Duty"
ERP_IGST = "IGST Amount"
ERP_IGST_ASSBL = "IGST Assessable Value"
ERP_JOB_OWNER = "Job Owner"
ERP_VESSEL = "Vessel/Flight"
ERP_NO_PKGS = "No Of Pkgs"
ERP_PORT_SHIPMENT = "Port of Shipment"
ERP_HAWB = "HAWB/HBL No"
ERP_AWB_NO = "AWB/BL No."
ERP_GROSS_WEIGHT = "Gross Weight"
ERP_CHARGEABLE_WEIGHT = "Chargeable Weight"
ERP_MODE = "Mode"


# ─── Status Derivation ──────────────────────────────────────────────────────
def derive_status(row: pd.Series) -> str:
    """
    Derive Master Status based on Pre-Alert operational fields.

    Checks both Inbond and Exbond side for lifecycle position.
    """
    has_exbond = pd.notna(row.get("Exbond_Job_No"))

    if has_exbond:
        # Check if both sides are closed
        inb_status = str(row.get("Inbond_Shipment_Status", "")).strip()
        exb_status = str(row.get("Exbond_Shipment_Status", "")).strip()

        if inb_status == "Closed" and exb_status == "Closed":
            if pd.notna(row.get("Actual_Delivery_Date")):
                return "Fully Closed & Delivered"
            else:
                return "Fully Closed (No POD)"

        if pd.notna(row.get("Actual_Delivery_Date")):
            return "Delivered"
        elif pd.notna(row.get("Exbond_Dispatch_Date")):
            return "In Transit (Final Dispatch)"
        elif pd.notna(row.get("Exbond_OOC_Date")):
            return "Exbond Cleared (OOC)"
        elif pd.notna(row.get("Exbond_ATA")):
            return "Exbond Arrived - Clearance Pending"
        elif pd.notna(row.get("Exbond_BE_Date")):
            return "Exbond BE Filed"
        else:
            return "Exbond In Progress"
    else:
        inb_status = str(row.get("Inbond_Shipment_Status", "")).strip()

        if inb_status == "Closed":
            return "Inbond Closed - Awaiting Exbond"
        elif pd.notna(row.get("Inbond_Dispatch_Date")):
            return "In Bond / Warehoused"
        elif pd.notna(row.get("Inbond_OOC_Date")):
            return "Inbond Cleared (OOC)"
        elif pd.notna(row.get("ATA")):
            return "Arrived - Clearance Pending"
        elif pd.notna(row.get("ETA")):
            return "In Transit - ETA Set"
        else:
            return "Inbond In Progress"


# ─── Core Merge Logic ────────────────────────────────────────────────────────
def merge_dsr(
    pa_df: pd.DataFrame,
    erp_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Main consolidation function.

    Parameters:
        pa_df:  Pre-Alert data (View_All_Jobs export)
        erp_df: ERP data (View_ERP_data export), optional

    Returns:
        Master DSR DataFrame with one row per shipment
    """
    logger.info(f"Total Pre-Alert records: {len(pa_df)}")

    # ══════════════════════════════════════════════════════════════
    # STEP 1: PARTITION Pre-Alert by BE Type
    # ══════════════════════════════════════════════════════════════
    pa_df[PA_BE_TYPE] = pa_df[PA_BE_TYPE].astype(str).str.strip()
    pa_inbond = pa_df[pa_df[PA_BE_TYPE] == INBOND_TYPE].copy()
    pa_exbond = pa_df[pa_df[PA_BE_TYPE] == EXBOND_TYPE].copy()

    logger.info(f"Pre-Alert Inbond (SEZ-Z): {len(pa_inbond)}")
    logger.info(f"Pre-Alert Exbond (SEZ-T): {len(pa_exbond)}")

    # Check for other BE Types
    other = pa_df[~pa_df[PA_BE_TYPE].isin([INBOND_TYPE, EXBOND_TYPE])]
    if len(other) > 0:
        logger.warning(
            f"Found {len(other)} records with other BE Types: "
            f"{other[PA_BE_TYPE].unique().tolist()}"
        )

    # ══════════════════════════════════════════════════════════════
    # STEP 2: BUILD EXBOND LOOKUP (Client Ref → Exbond record)
    # ══════════════════════════════════════════════════════════════
    # Key: Exbond's "Tracking No / Client Ref No" = Inbond's "HAWB/HBL"
    pa_exbond[PA_CLIENT_REF] = pa_exbond[PA_CLIENT_REF].astype(str).str.strip()

    # Handle duplicates: keep latest BE Date
    pa_exbond_deduped = pa_exbond.sort_values(PA_BE_DATE, ascending=False, na_position="last")
    pa_exbond_deduped = pa_exbond_deduped.drop_duplicates(subset=[PA_CLIENT_REF], keep="first")

    dupes = len(pa_exbond) - len(pa_exbond_deduped)
    if dupes > 0:
        logger.warning(f"Removed {dupes} duplicate Exbond records (kept latest BE Date)")

    exbond_lookup = pa_exbond_deduped.set_index(PA_CLIENT_REF)

    # ══════════════════════════════════════════════════════════════
    # STEP 3: BUILD ERP LOOKUP (BE No → ERP record)
    # ══════════════════════════════════════════════════════════════
    erp_lookup = None
    if erp_df is not None and len(erp_df) > 0:
        logger.info(f"Total ERP records: {len(erp_df)}")
        erp_df[ERP_BE_NO] = erp_df[ERP_BE_NO].astype(str).str.strip()
        erp_lookup = erp_df.drop_duplicates(subset=[ERP_BE_NO], keep="first").set_index(ERP_BE_NO)
        logger.info(f"ERP lookup built: {len(erp_lookup)} unique BE Numbers")

    # ══════════════════════════════════════════════════════════════
    # STEP 4: MERGE — Iterate Inbonds and match Exbonds
    # ══════════════════════════════════════════════════════════════
    master_rows = []
    consumed_exbond_refs = set()

    for _, inb in pa_inbond.iterrows():
        row = {}
        hawb = str(inb.get(PA_HAWB, "")).strip()
        invoice_number = str(inb.get(PA_CLIENT_REF, "")).strip()
        inb_beno = str(inb.get(PA_BE_NO, "")).strip()

        if not invoice_number or invoice_number == "nan":
            logger.warning(f"Inbond Job {inb.get(PA_JOB_NO)} has no Client Ref. Skipping.")
            continue

        # ── Core Identification ──
        row["Invoice_Number"] = invoice_number
        row["Importer"] = inb.get(PA_IMPORTER)
        row["Mode"] = inb.get(PA_MODE)
        row["Branch"] = inb.get(PA_BRANCH)

        # ── Inbond Pre-Alert Fields ──
        row["Inbond_Job_No"] = inb.get(PA_JOB_NO)
        row["MAWB_MBL"] = inb.get(PA_MAWB)
        row["HAWB_HBL"] = hawb
        row["Inbond_BE_No"] = inb_beno
        row["Inbond_BE_Date"] = inb.get(PA_BE_DATE)
        row["ETA"] = inb.get(PA_ETA)
        row["ATA"] = inb.get(PA_ATA)
        row["Segregation_Time"] = inb.get(PA_SEGREGATION)
        row["Inbond_OOC_Date"] = inb.get(PA_OOC)
        row["Inbond_Dispatch_Date"] = inb.get(PA_DISPATCH)
        row["Inbond_Assessment_By"] = inb.get(PA_ASSESSMENT)
        row["Inbond_TAT"] = inb.get(PA_TAT)
        row["Inbond_ATA_to_OOC"] = inb.get(PA_ATA_TO_OOC)
        row["Inbond_Shipment_Status"] = inb.get(PA_STATUS)
        row["Inbond_BE_Filed_On"] = inb.get(PA_BE_FILED)
        row["Inbond_Duty_Paid_On"] = inb.get(PA_DUTY_PAID)
        row["Inbond_Purchase_Booking"] = inb.get(PA_PURCHASE_BOOKING)
        row["Inbond_Invoice_Prepared"] = inb.get(PA_INVOICE_PREPARED)

        # ── Enrich with Inbond ERP data (via BE No) ──
        if erp_lookup is not None and inb_beno in erp_lookup.index:
            erp_inb = erp_lookup.loc[inb_beno]
            row["Supplier_Exporter"] = erp_inb.get(ERP_SUPPLIER)
            row["Description"] = erp_inb.get(ERP_DESCRIPTION)
            row["CTH_No"] = erp_inb.get(ERP_CTH)
            row["Custom_House"] = erp_inb.get(ERP_CUSTOM_HOUSE)
            row["Inv_Currency"] = erp_inb.get(ERP_INV_CURRENCY)
            row["Total_Inv_Value"] = erp_inb.get(ERP_TOTAL_INV_VALUE)
            row["Assbl_Value"] = erp_inb.get(ERP_ASSBL_VALUE)
            row["Inbond_Basic_Duty"] = erp_inb.get(ERP_BASIC_DUTY)
            row["Inbond_SWS_Duty"] = erp_inb.get(ERP_SWS_DUTY)
            row["Inbond_IGST"] = erp_inb.get(ERP_IGST)
            row["Job_Owner"] = erp_inb.get(ERP_JOB_OWNER)
            row["Vessel_Flight"] = erp_inb.get(ERP_VESSEL)
            row["No_Of_Pkgs"] = erp_inb.get(ERP_NO_PKGS)
            row["Port_of_Shipment"] = erp_inb.get(ERP_PORT_SHIPMENT)

        # ══════════════════════════════════════════════════════════
        # MATCH EXBOND — HAWB/HBL = Exbond's Client Ref No
        # ══════════════════════════════════════════════════════════
        if hawb and hawb != "nan" and hawb in exbond_lookup.index:
            exb = exbond_lookup.loc[hawb]
            consumed_exbond_refs.add(hawb)
            exb_beno = str(exb.get(PA_BE_NO, "")).strip()

            # Sanity check
            exb_importer = str(exb.get(PA_IMPORTER, "")).strip()
            inb_importer = str(inb.get(PA_IMPORTER, "")).strip()
            if exb_importer and inb_importer and exb_importer != inb_importer:
                logger.warning(
                    f"Importer mismatch for Invoice {invoice_number}: "
                    f"Inbond='{inb_importer}' vs Exbond='{exb_importer}'"
                )

            # ── Exbond Pre-Alert Fields ──
            row["Exbond_Job_No"] = exb.get(PA_JOB_NO)
            row["Exbond_BE_No"] = exb_beno
            row["Exbond_BE_Date"] = exb.get(PA_BE_DATE)
            row["Exbond_ATA"] = exb.get(PA_ATA)
            row["Exbond_OOC_Date"] = exb.get(PA_OOC)
            row["Exbond_Dispatch_Date"] = exb.get(PA_DISPATCH)
            row["Actual_Delivery_Date"] = exb.get(PA_DELIVERY)
            row["Exbond_Assessment_By"] = exb.get(PA_ASSESSMENT)
            row["Exbond_TAT"] = exb.get(PA_TAT)
            row["Exbond_ATA_to_OOC"] = exb.get(PA_ATA_TO_OOC)
            row["Exbond_Shipment_Status"] = exb.get(PA_STATUS)
            row["Exbond_BE_Filed_On"] = exb.get(PA_BE_FILED)
            row["Exbond_Duty_Paid_On"] = exb.get(PA_DUTY_PAID)
            row["Exbond_Purchase_Booking"] = exb.get(PA_PURCHASE_BOOKING)
            row["Exbond_Invoice_Prepared"] = exb.get(PA_INVOICE_PREPARED)

            # ── Enrich with Exbond ERP data ──
            if erp_lookup is not None and exb_beno in erp_lookup.index:
                erp_exb = erp_lookup.loc[exb_beno]
                row["Exbond_Basic_Duty"] = erp_exb.get(ERP_BASIC_DUTY)
                row["Exbond_SWS_Duty"] = erp_exb.get(ERP_SWS_DUTY)
                row["Exbond_IGST"] = erp_exb.get(ERP_IGST)

            row["Merge_Type"] = "Merged (Inbond + Exbond)"
            logger.info(
                f"MERGED: Invoice {invoice_number} | "
                f"Inbond Job: {inb.get(PA_JOB_NO)} <-> Exbond Job: {exb.get(PA_JOB_NO)}"
            )
        else:
            row["Merge_Type"] = "Inbond Only (Exbond Pending)"
            logger.info(
                f"INBOND ONLY: Invoice {invoice_number} | "
                f"Job: {inb.get(PA_JOB_NO)}"
            )

        master_rows.append(row)

    # ══════════════════════════════════════════════════════════════
    # STEP 5: ORPHAN EXBONDS
    # ══════════════════════════════════════════════════════════════
    for ref, exb in exbond_lookup.iterrows():
        if ref not in consumed_exbond_refs:
            logger.warning(
                f"ORPHAN EXBOND: Client Ref {ref} | Job: {exb.get(PA_JOB_NO)}"
            )
            orphan_row = {
                "Invoice_Number": ref,
                "Importer": exb.get(PA_IMPORTER),
                "Exbond_Job_No": exb.get(PA_JOB_NO),
                "Exbond_BE_No": exb.get(PA_BE_NO),
                "Exbond_BE_Date": exb.get(PA_BE_DATE),
                "Exbond_OOC_Date": exb.get(PA_OOC),
                "Exbond_Dispatch_Date": exb.get(PA_DISPATCH),
                "Actual_Delivery_Date": exb.get(PA_DELIVERY),
                "Exbond_Shipment_Status": exb.get(PA_STATUS),
                "Merge_Type": "Orphan Exbond (No Inbond)",
            }
            master_rows.append(orphan_row)

    # ══════════════════════════════════════════════════════════════
    # STEP 6: BUILD FINAL DATAFRAME
    # ══════════════════════════════════════════════════════════════
    master_df = pd.DataFrame(master_rows)

    # Derive status
    if len(master_df) > 0:
        master_df["Master_Status"] = master_df.apply(derive_status, axis=1)

        # Compute total duties
        duty_cols = [
            "Inbond_Basic_Duty", "Inbond_SWS_Duty", "Inbond_IGST",
            "Exbond_Basic_Duty", "Exbond_SWS_Duty", "Exbond_IGST",
        ]
        for col in duty_cols:
            if col in master_df.columns:
                master_df[col] = pd.to_numeric(master_df[col], errors="coerce")

        existing_duty_cols = [c for c in duty_cols if c in master_df.columns]
        if existing_duty_cols:
            master_df["Total_Duties_Combined"] = master_df[existing_duty_cols].sum(axis=1)

    # ── Column ordering ──
    output_order = [
        # Core
        "Invoice_Number", "Importer", "Supplier_Exporter", "Description",
        "CTH_No", "Mode", "Branch", "Custom_House", "Job_Owner",
        # Inbond
        "Inbond_Job_No", "MAWB_MBL", "HAWB_HBL", "Inbond_BE_No",
        "Inbond_BE_Date", "ETA", "ATA", "Segregation_Time",
        "Inbond_OOC_Date", "Inbond_Dispatch_Date",
        "Inbond_Assessment_By", "Inbond_TAT", "Inbond_ATA_to_OOC",
        "Inbond_Shipment_Status",
        "Inbond_BE_Filed_On", "Inbond_Duty_Paid_On",
        "Inbond_Purchase_Booking", "Inbond_Invoice_Prepared",
        # Exbond
        "Exbond_Job_No", "Exbond_BE_No", "Exbond_BE_Date",
        "Exbond_ATA", "Exbond_OOC_Date", "Exbond_Dispatch_Date",
        "Actual_Delivery_Date",
        "Exbond_Assessment_By", "Exbond_TAT", "Exbond_ATA_to_OOC",
        "Exbond_Shipment_Status",
        "Exbond_BE_Filed_On", "Exbond_Duty_Paid_On",
        "Exbond_Purchase_Booking", "Exbond_Invoice_Prepared",
        # Financial
        "Inv_Currency", "Total_Inv_Value", "Assbl_Value",
        "Inbond_Basic_Duty", "Inbond_SWS_Duty", "Inbond_IGST",
        "Exbond_Basic_Duty", "Exbond_SWS_Duty", "Exbond_IGST",
        "Total_Duties_Combined",
        # Meta
        "Vessel_Flight", "No_Of_Pkgs", "Port_of_Shipment",
        "Master_Status", "Merge_Type",
    ]
    existing_cols = [c for c in output_order if c in master_df.columns]
    extra_cols = [c for c in master_df.columns if c not in output_order]
    master_df = master_df[existing_cols + extra_cols]

    logger.info(f"Final Master DSR records: {len(master_df)}")

    # ── Log breakdown ──
    if "Merge_Type" in master_df.columns:
        for mt, count in master_df["Merge_Type"].value_counts().items():
            logger.info(f"  {mt}: {count}")
    if "Master_Status" in master_df.columns:
        for st, count in master_df["Master_Status"].value_counts().items():
            logger.info(f"  Status '{st}': {count}")

    return master_df


# ─── Summary Report ──────────────────────────────────────────────────────────
def generate_summary(master_df: pd.DataFrame) -> str:
    """Generate a human-readable summary of the consolidation."""
    lines = [
        "=" * 65,
        "  DSR CONSOLIDATION SUMMARY",
        "=" * 65,
        f"  Run Date:           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Total Master Rows:  {len(master_df)}",
        "",
        "  -- Merge Breakdown --",
    ]
    if "Merge_Type" in master_df.columns:
        for mt, count in master_df["Merge_Type"].value_counts().items():
            lines.append(f"    {mt}: {count}")
    lines.append("")
    lines.append("  -- Status Breakdown --")
    if "Master_Status" in master_df.columns:
        for st, count in master_df["Master_Status"].value_counts().items():
            lines.append(f"    {st}: {count}")
    lines.append("")
    if "Importer" in master_df.columns:
        lines.append(f"  -- Unique Importers: {master_df['Importer'].nunique()} --")
        for imp in master_df["Importer"].dropna().unique()[:10]:
            count = len(master_df[master_df["Importer"] == imp])
            lines.append(f"    {imp}: {count} shipments")
    if "Total_Duties_Combined" in master_df.columns:
        total = master_df["Total_Duties_Combined"].sum()
        lines.append("")
        lines.append(f"  -- Total Combined Duties: Rs. {total:,.2f} --")
    lines.append("=" * 65)
    return "\n".join(lines)


# ─── File I/O ─────────────────────────────────────────────────────────────────
def load_data(filepath: str) -> pd.DataFrame:
    """Load data from CSV or Excel."""
    path = Path(filepath)
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(filepath)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    logger.info(f"Loaded {len(df)} records from {filepath}")
    return df


def save_output(master_df: pd.DataFrame, filepath: str):
    """Save the Master DSR to Excel with formatting."""
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        master_df.to_excel(writer, sheet_name="Master DSR", index=False)

        summary_text = generate_summary(master_df)
        summary_df = pd.DataFrame({"Summary": summary_text.split("\n")})
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    logger.info(f"Master DSR saved to: {filepath}")
    logger.info(f"Total rows: {len(master_df)}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="DSR Consolidation: Merge Inbond (SEZ-Z) and Exbond (SEZ-T) records"
    )
    parser.add_argument(
        "--prealert", "-p",
        required=True,
        help="Path to Pre-Alert data (View_All_Jobs export — CSV or Excel)",
    )
    parser.add_argument(
        "--erp", "-e",
        default=None,
        help="Path to ERP data (View_ERP_data export — CSV or Excel). Optional.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output Excel file path. Default: master_dsr_<timestamp>.xlsx",
    )
    args = parser.parse_args()

    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"master_dsr_{timestamp}.xlsx"

    # ── Load ──
    pa_df = load_data(args.prealert)

    erp_df = None
    if args.erp:
        erp_df = load_data(args.erp)

    # ── Merge ──
    master_df = merge_dsr(pa_df, erp_df)

    # ── Summary ──
    print(generate_summary(master_df))

    # ── Save ──
    save_output(master_df, args.output)


if __name__ == "__main__":
    main()
