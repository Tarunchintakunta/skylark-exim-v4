"""Rebuild the asset rows of docs/LICENSES.md from assets-src/tex/LICENSES.tsv (written by the Blender library and workers).
Usage: python3 scripts/licenses-from-tsv.py   (keeps the hand-written rows above the ASSET-ROWS marker)"""
import csv, pathlib
doc = pathlib.Path('docs/LICENSES.md'); tsv = pathlib.Path('assets-src/tex/LICENSES.tsv')
head = doc.read_text().split('<!-- ASSET-ROWS -->')[0].rstrip('\n')
rows, seen = [], set()
for r in csv.DictReader(tsv.open(), delimiter='\t'):
    if r['slug'] in seen: continue
    seen.add(r['slug'])
    lic = r['license']; by = lic.upper().startswith('CC-BY')
    kind = 'scan' if r['slug'].startswith('scan:') else 'texture/HDRI/data'
    rows.append(f"| {r['slug'].replace('scan:', '')} | Blender renders ({kind}) | {r['url']} | {r['authors']} | {lic} | {'**yes: credit ' + r['authors'] + ', ' + lic + '**' if by else 'no'} | {'cleaned, re-skinned' if kind == 'scan' else 'used as material'} |")
doc.write_text(head + '\n<!-- ASSET-ROWS -->\n' + '\n'.join(rows) + '\n')
print(len(rows), 'asset rows')
