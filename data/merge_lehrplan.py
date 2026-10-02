import csv, openpyxl, argparse, os, sys

parser = argparse.ArgumentParser()
parser.add_argument('--bpl', help='Filter by BPL value (e.g. ET)')
args = parser.parse_args()

script_dir = os.path.dirname(os.path.abspath(__file__))

files = [
    os.path.join(script_dir, 'export_lernfelder_BFS.xlsx'),
    os.path.join(script_dir, 'export_lernfelder_üK.xlsx'),
    os.path.join(script_dir, 'export_umsetzung_BE.xlsx'),
]

out_path = os.path.join(script_dir, 'lehrplan_merged.csv')

with open(out_path, 'w', newline='', encoding='utf-8') as fout:
    writer = None
    for f in files:
        wb = openpyxl.load_workbook(f)
        ws = wb['Lehrplan']
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        if writer is None:
            writer = csv.writer(fout)
            writer.writerow(rows[0])
            if args.bpl:
                writer.writerows(r for r in rows[1:] if r[0] == args.bpl)
            else:
                writer.writerows(rows[1:])
        else:
            if args.bpl:
                writer.writerows(r for r in rows[1:] if r[0] == args.bpl)
            else:
                writer.writerows(rows[1:])

with open(out_path, 'r', newline='', encoding='utf-8') as f:
    rows = list(csv.reader(f))

cleaned = [[cell.replace('\n', ' ').replace('\r', ' ').replace('_x000D_', '') for cell in row] for row in rows]

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerows(cleaned)

print(f"Done. {len(cleaned)} rows written.")
