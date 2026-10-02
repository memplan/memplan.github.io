import csv, json, os, re, sys
from urllib.request import urlopen, Request

script_dir = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(script_dir, 'lehrplan_merged.csv')
with open(csv_path, newline='', encoding='utf-8') as f:
    our_hks = set(r['ID HK'] for r in csv.DictReader(f))

hkb_needed = set()
for hk in our_hks:
    m = re.match(r'(\d+ [a-z])', hk)
    if m:
        hkb_needed.add(m.group(1))

url = 'https://skills.futuremem.swiss/de/data/1000_hkb/'
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urlopen(req, timeout=15) as resp:
    html = resp.read().decode()

h2_pat = re.compile(
    r'<h2[^>]*>([^<]+)</h2>\s*<p><strong>(.+?)</strong></p>',
    re.DOTALL
)

result = {}
missing_copy = hkb_needed.copy()

for m in h2_pat.finditer(html):
    hkb_id = m.group(1).strip()
    name = m.group(2).strip()
    if hkb_id not in hkb_needed:
        continue
    if hkb_id in result:
        continue
    result[hkb_id] = name
    missing_copy.discard(hkb_id)

out_path = os.path.join(script_dir, 'hkb_beschreibung.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'Found {len(result)} of {len(hkb_needed)} HKBs.')
if missing_copy:
    print(f'Missing: {sorted(missing_copy)}')
