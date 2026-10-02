import csv, json, os, re, sys
from urllib.request import urlopen, Request

script_dir = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(script_dir, 'lehrplan_merged.csv')
with open(csv_path, newline='', encoding='utf-8') as f:
    our_lks = set(r['ID LK'] for r in csv.DictReader(f))

base_url = 'https://skills.futuremem.swiss/de/data/3000_lkn_'
pages = [f'{base_url}{i:02d}/' for i in range(21)]

lk_pat = re.compile(
    r'<h2[^>]*>(?:(?:<abbr[^>]*>(\w+)</abbr>\s*(.+?))|([^<]+))</h2>\s*'
    r'<p><strong>(.+?)</strong></p>',
    re.DOTALL
)

result = {}
missing_copy = our_lks.copy()

for url in pages:
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode()
    except Exception as e:
        print(f'Failed {url}: {e}', file=sys.stderr)
        continue

    for m in lk_pat.finditer(html):
        if m.group(1):
            full_id = m.group(1) + ' ' + m.group(2).strip()
        else:
            full_id = m.group(3).strip()
        beschreibung = m.group(4).strip()
        if full_id not in our_lks or full_id in result:
            continue
        result[full_id] = beschreibung
        missing_copy.discard(full_id)

out_path = os.path.join(script_dir, 'lk_beschreibung.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'Found {len(result)} of {len(our_lks)} LKs.')
if missing_copy:
    print(f'Missing: {sorted(missing_copy)}')
