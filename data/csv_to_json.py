import csv, json, os, re
from collections import defaultdict

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'lehrplan_merged.csv')

with open(csv_path, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

hkb_path = os.path.join(script_dir, 'hkb_beschreibung.json')
with open(hkb_path, encoding='utf-8') as f:
    hkb_data = json.load(f)

hk_path = os.path.join(script_dir, 'hk_beschreibung.json')
with open(hk_path, encoding='utf-8') as f:
    hk_data = json.load(f)

lk_groups = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for r in rows:
    lk_groups[r['BPL']][r['ID HK']][(r['ID LK'], r['Lernort'])].append(r)

# Determine which ID LK appear in multiple Lernort (per BPL/HK)
multi_lk = set()
for bpl, hks in lk_groups.items():
    for hk, lks in hks.items():
        lk_learnort_count = defaultdict(set)
        for lk_id, lernort in lks.keys():
            lk_learnort_count[lk_id].add(lernort)
        for lk_id, lernorts in lk_learnort_count.items():
            if len(lernorts) > 1:
                for lernort in lernorts:
                    multi_lk.add((bpl, hk, lk_id, lernort))

result = {}
for bpl, hks in lk_groups.items():
    hkb_groups = defaultdict(list)
    for hk, lks in hks.items():
        m = re.match(r'(\d+ [a-z])', hk)
        hkb_id = m.group(1) if m else ''
        hkb_groups[hkb_id].append((hk, lks))

    bpl_entry = {'handlungskompetenzbereiche': []}
    for hkb_id in sorted(hkb_groups):
        hkb_name = hkb_data.get(hkb_id, '')
        hkb_entry = {
            'ID HKB': hkb_id,
            'Name': hkb_name,
            'handlungskompetenzen': []
        }
        for hk, lks in hkb_groups[hkb_id]:
            hk_entry = {
                'ID HK': hk,
                'Name': hk_data.get(hk, {}).get('Name', ''),
                'Beschreibung': hk_data.get(hk, {}).get('Beschreibung', ''),
                'NQR': lks[list(lks.keys())[0]][0]['NQR'],
                'P/W': lks[list(lks.keys())[0]][0]['P/W'],
                'lernkriterien': []
            }
            for (lk_id, lernort), lz_rows in lks.items():
                postfix = f' ({lernort})' if (bpl, hk, lk_id, lernort) in multi_lk else ''

                raw_sems = set()
                for r in lz_rows:
                    m = re.search(r'\d+', r['Semester'])
                    if m:
                        raw_sems.add(m.group())
                semesters = sorted(raw_sems, key=int)

                lk_entry = {
                    'ID LK': lk_id + postfix,
                    'LN': lz_rows[0]['LN'],
                    'Lernort': lernort,
                    'Beschreibung LK': lz_rows[0]['Beschreibung LK'],
                    'Semester': semesters,
                    'lernziele': []
                }
                for r in lz_rows:
                    if not r['ID LZ'] or r['ID LZ'] == '-':
                        continue
                    lk_entry['lernziele'].append({
                        'ID LZ': r['ID LZ'],
                        'Beschreibung LZ': r['Beschreibung LZ'],
                        'Taxonomie LZ': r['Taxonomie LZ'],
                        'Semester': re.search(r'\d+', r['Semester']).group() if re.search(r'\d+', r['Semester']) else r['Semester'],
                        'ID LFE': r['ID LFE'],
                        'Handlungsnotwendiges Wissen': r['Handlungsnotwendiges Wissen'],
                        'Abfolge': r['Abfolge'],
                        'Lektionen': r['Lektionen'],
                        'Note zu HKB': r['Note zu HKB']
                    })
                hk_entry['lernkriterien'].append(lk_entry)
            hkb_entry['handlungskompetenzen'].append(hk_entry)
        bpl_entry['handlungskompetenzbereiche'].append(hkb_entry)
    result[bpl] = bpl_entry

out_paths = []
for bpl, bpl_entry in result.items():
    out_path = os.path.join(script_dir, f'lehrplan_{bpl}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({bpl: bpl_entry}, f, ensure_ascii=False, indent=2)
    out_paths.append(out_path)

print(f'Done. {len(result)} BPLs, JSON written to:')
for p in out_paths:
    print(f'  {p}')
