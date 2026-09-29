"""Reproduce the visual-review exclusions without modifying the original ZIP."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

# IDs refer to inventory.json and the numbered contact sheets, visually reviewed.
# Excluded material includes non-food subjects and unsuitable diagrams/graphics.
EXCLUDED_RANGES = [
    (113,113),(115,125),(282,287),(347,499),(528,609),(635,738),
    (740,740),(745,745),(765,919),(952,1049),(1075,1226),
    (1306,1432),(1456,1699),(1727,1855),(1883,1883),
    (1986,1986),(1988,2057),(2143,2186),
]
EXCLUDED_IDS = {183,212,315}
# Entire food-containing groups visibly contain wrong preparations/ingredients.
LABEL_REVIEW_RANGES = [(0,56),(90,112),(114,114),(155,216),(288,346),
                       (1250,1273),(1433,1455),(1856,1886),(1939,1985),
                       (1987,1987),(2085,2142)]

def in_ranges(index, ranges):
    return any(low <= index <= high for low, high in ranges)

def classify(index):
    if index in EXCLUDED_IDS or in_ranges(index, EXCLUDED_RANGES):
        return 'excluded_unrelated', 'Non-food subject or unsuitable graphic; contact-sheet visual review'
    if in_ranges(index, LABEL_REVIEW_RANGES):
        return 'label_review', 'Food present, but class contains visibly incorrect dishes or ingredients'
    return 'food_candidate', 'Food visible; exact recipe/label still requires verification before training'

def clean(archive, output):
    inventory_path = Path(__file__).with_name('inventory.json')
    inventory = json.loads(inventory_path.read_text())
    output = Path(output).resolve()
    # New output only; do not silently mix results with a previous dataset.
    output.mkdir(parents=True, exist_ok=False)
    records = []
    with ZipFile(archive) as source:
        for item in inventory:
            name = PurePosixPath(item['archive_path'])
            if '..' in name.parts or name.is_absolute():
                raise ValueError('Unsafe archive path')
            state, reason = classify(item['id'])
            payload = source.read(item['archive_path'])
            relative = Path(state) / name.parts[-2] / name.name
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            records.append(dict(item, status=state, reason=reason,
                                path=relative.as_posix(),
                                sha256=hashlib.sha256(payload).hexdigest()))
    counts = Counter(r['status'] for r in records)
    (output / 'manifest.json').write_text(json.dumps(records, indent=2))
    class_counts = {}
    for row in records:
        label = PurePosixPath(row['archive_path']).parts[-2]
        class_counts.setdefault(label, Counter())[row['status']] += 1
    (output / 'summary.json').write_text(json.dumps(dict(total=len(records), counts=counts, classes=class_counts), indent=2))
    print(json.dumps(dict(total=len(records), counts=counts)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive')
    parser.add_argument('output')
    args = parser.parse_args()
    clean(args.archive, args.output)
