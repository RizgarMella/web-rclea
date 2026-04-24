"""Full audit of every sheet in the workbook — what's implemented vs. missing."""
import xlrd
XLS = r"C:/Users/Riz/Desktop/rclea/Resouces/RCLEA_software_application.xls"

wb = xlrd.open_workbook(XLS)
for name in wb.sheet_names():
    sh = wb.sheet_by_name(name)
    print(f"\n{'='*80}\n=== {name} (nrows={sh.nrows}, ncols={sh.ncols}) ===\n{'='*80}")
    for r in range(sh.nrows):
        row = []
        for c in range(sh.ncols):
            v = sh.cell_value(r, c)
            if isinstance(v, str):
                v = v.strip() or None
            row.append(v)
        # Skip fully-empty rows
        if all(x is None or x == "" for x in row):
            continue
        print(f"  {r:3d}: {row}")
