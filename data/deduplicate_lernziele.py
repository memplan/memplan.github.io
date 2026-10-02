import argparse, json, os
from collections import OrderedDict

parser = argparse.ArgumentParser(
    description='Deduplicate Lernziele in a single per-job lehrplan JSON file.')
parser.add_argument('path', nargs='?', default='lehrplan.json',
                    help='Path to a per-job lehrplan JSON (default: lehrplan.json).')
args = parser.parse_args()

script_dir = os.path.dirname(os.path.abspath(__file__))
src_path = args.path if os.path.isabs(args.path) else os.path.join(script_dir, args.path)
dst_path = src_path

with open(src_path, encoding='utf-8') as f:
    data = json.load(f)

MERGE_FIELDS = ['Beschreibung LZ', 'Taxonomie LZ', 'ID LFE',
                'Handlungsnotwendiges Wissen', 'Abfolge', 'Lektionen', 'Note zu HKB']

def flatten_semester(val):
    if isinstance(val, list):
        result = []
        for v in val:
            result.extend(flatten_semester(v))
        return result
    return [str(val)]

def normalize_semester(val):
    flat = flatten_semester(val)
    seen = []
    for s in flat:
        if s not in seen:
            seen.append(s)
    return seen

for beruf, bdata in data.items():
    for hkb in bdata['handlungskompetenzbereiche']:
        for hk in hkb['handlungskompetenzen']:
            for lk in hk['lernkriterien']:
                merged = OrderedDict()
                for lz in lk['lernziele']:
                    lz_id = lz['ID LZ']
                    sems = normalize_semester(lz['Semester'])
                    if lz_id not in merged:
                        lz_copy = {k: lz[k] for k in lz if k not in ('Semester', 'duplicated')}
                        lz_copy['Semester'] = sems
                        merged[lz_id] = lz_copy
                    else:
                        existing = merged[lz_id]
                        for s in sems:
                            if s not in existing['Semester']:
                                existing['Semester'].append(s)
                        for field in MERGE_FIELDS:
                            old_val = existing[field]
                            new_val = lz[field]
                            if old_val != new_val:
                                parts = [v for v in [old_val, new_val] if v]
                                combined = ', '.join(OrderedDict.fromkeys(parts))
                                existing[field] = combined
                lk['lernziele'] = list(merged.values())

lz_to_lks = {}
for beruf, bdata in data.items():
    for hkb in bdata['handlungskompetenzbereiche']:
        for hk in hkb['handlungskompetenzen']:
            for lk in hk['lernkriterien']:
                seen_in_lk = set()
                for lz in lk['lernziele']:
                    lz_id = lz['ID LZ']
                    if lz_id in seen_in_lk:
                        continue
                    seen_in_lk.add(lz_id)
                    if lz_id not in lz_to_lks:
                        lz_to_lks[lz_id] = set()
                    lz_to_lks[lz_id].add(lk['ID LK'])

for beruf, bdata in data.items():
    for hkb in bdata['handlungskompetenzbereiche']:
        for hk in hkb['handlungskompetenzen']:
            for lk in hk['lernkriterien']:
                for lz in lk['lernziele']:
                    lz_id = lz['ID LZ']
                    all_lks = lz_to_lks.get(lz_id, set())
                    if len(all_lks) > 1:
                        others = sorted(all_lks - {lk['ID LK']})
                        lz['duplicated'] = others

with open(dst_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Done.')
