import pdfplumber, re
from datetime import datetime

class TestParser:
    def extract_data(self, pdf_path):
        page_texts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_texts.append(page.extract_text() or "")
        text_all = "\n".join(page_texts)

        invoice_headers = []
        idx = 1
        for block in text_all.split("Invoice Detail")[1:]:
            m_nd = re.search(r'Inv\s*No\s*&\s*Date\s+(\S+)\s+dt\.\s+(\S+)', block, re.IGNORECASE)
            m_v  = re.search(r'Invoice\s*Value\s+([\d,]+\.[\d]+)', block, re.IGNORECASE)
            if m_nd:
                invoice_headers.append({
                    "idx": str(idx), "num": m_nd.group(1), "date": m_nd.group(2),
                    "val": m_v.group(1).replace(",","").split(".")[0] if m_v else "0"
                })
                idx += 1

        print("Invoices:", invoice_headers)

        sw_items = []
        sw_match = re.search(r'SINGLE\s+WINDOW\s*-\s*Additional\s+Product\s+Information(.*?)DUTY\s+Details', text_all, re.DOTALL | re.IGNORECASE)
        if sw_match:
            print("FOUND SINGLE WINDOW BLOCK")
            for m2 in re.finditer(r'(\d+)\s+(\d+)\s+Item\s+Characteristics\s+Standard\s+UQC\s+([\d\.]+)\s+NOS', sw_match.group(1), re.IGNORECASE):
                sw_items.append({"inv_idx": m2.group(1), "item_idx": m2.group(2), "qty": int(float(m2.group(3)))})
        else:
            print("NO SINGLE WINDOW BLOCK FOUND")

        print("SW Items:", sw_items)

        item_desc_map = {}
        for m2 in re.finditer(r'^\s*(\d+)\s+\d{8}\s+(.+?)(?=\n\s*[\d\.]+\s+[\d\.]+\s+\d{8}|\n\s*AIDC)', text_all, re.MULTILINE | re.DOTALL):
            slot = m2.group(1)
            desc = re.sub(r'\s+', ' ', m2.group(2)).strip()
            item_desc_map[slot] = desc

        subform_rows = []
        for sw in sw_items:
            inv = next((i for i in invoice_headers if i["idx"] == sw["inv_idx"]), None)
            if inv:
                full_desc = item_desc_map.get(sw["item_idx"], "")
                model = full_desc.split()[0] if full_desc else ""
                try:
                    formatted_date = datetime.strptime(inv["date"], "%d-%b-%Y").strftime("%d-%b-%Y").upper()
                except: formatted_date = inv["date"]
                subform_rows.append({
                    "Invoice_Number": inv["num"], "Invoice_Date": formatted_date,
                    "Total_Inv_Value": inv["val"], "Product_Qty": sw["qty"],
                    "Model_No": model, "Item_Description": full_desc
                })

        return subform_rows

print(TestParser().extract_data(r'c:\projects\DOCS\dsr_consolidation\Import CheckList-IR5330725-26-13-FEB-2026_08_05_PM.pdf'))
