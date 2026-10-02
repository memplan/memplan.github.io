import csv, json, os, re, sys
from urllib.request import urlopen, Request

script_dir = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(script_dir, 'lehrplan_merged.csv')
with open(csv_path, newline='', encoding='utf-8') as f:
    our_hks = set(r['ID HK'] for r in csv.DictReader(f))

base_url = 'https://skills.futuremem.swiss/de/data/2000_hkp_'
pages = [f'{base_url}{i:02d}/' for i in range(12)]

h2_pat = re.compile(
    r'<h2[^>]*>(\d+ [a-d]\.\d+)</h2>\s*'
    r'<p><strong>(.+?)</strong></p>\s*'
    r'<p>(.+?)</p>',
    re.DOTALL
)

result = {}
missing_copy = our_hks.copy()

for url in pages:
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode()
    except Exception as e:
        print(f'Failed {url}: {e}', file=sys.stderr)
        continue

    for m in h2_pat.finditer(html):
        hk_id = m.group(1)
        name = m.group(2).strip()
        beschreibung = re.sub(r'<[^>]+>', '', m.group(3)).strip()
        if hk_id in result:
            continue
        result[hk_id] = {
            'Name': name,
            'Beschreibung': beschreibung
        }
        missing_copy.discard(hk_id)

out_path = os.path.join(script_dir, 'hk_beschreibung.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'Found {len(result)} of {len(our_hks)} HKs.')
if missing_copy:
    print(f'Missing: {sorted(missing_copy)}')
