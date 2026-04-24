"""Inspect the rest of the sheets we haven't looked at yet."""
import xlrd
from pathlib import Path
XLS = r"C:/Users/Riz/Desktop/rclea/Resouces/RCLEA_software_application.xls"

def dump(sheet, start=0, end=None):
    end = end or sheet.nrows
    for r in range(start, min(end, sheet.nrows)):
        row = []
        for c in range(sheet.ncols):
            v = sheet.cell_value(r, c)
            if isinstance(v, str):
                v = v.strip() or None
            row.append(v)
        print(r, row)

wb = xlrd.open_workbook(XLS)

# EffectiveDose — look past the ingestion/inhalation section for external dose coefficients
print("\n=== EffectiveDose full (nrows =", wb.sheet_by_name("EffectiveDose").nrows, ") ===")
eff = wb.sheet_by_name("EffectiveDose")
dump(eff, 0, eff.nrows)
