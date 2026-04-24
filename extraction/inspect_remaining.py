"""Inspect SoilAndPlant, IntermediateCalcs, LandUse rest, Contamination, GuidelineValues."""
import xlrd
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

for name in ["SoilAndPlant", "LandUse", "IntermediateCalcs", "Contamination", "GuidelineValues", "CalculationParams"]:
    print(f"\n=== {name} (nrows={wb.sheet_by_name(name).nrows}) ===")
    dump(wb.sheet_by_name(name))
