import concurrent.futures
import csv
import hashlib
import json
import subprocess
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'work/datasheets/part-specs'


def fetch(mpn):
    host = 'www.yageogroup.com' if mpn.startswith(('RC', 'RT')) else 'search.kemet.com'
    url = 'https://' + host + '/component-documentation/download/specsheet/' + mpn
    path = CACHE / (mpn + '.pdf')
    if not path.exists():
        result = subprocess.run(['curl', '--silent', '--show-error', '--location', '--fail',
                                 '--max-time', '20', '--output', str(path), url], capture_output=True, text=True)
        if result.returncode:
            return {'mpn': mpn, 'url': url, 'status': 'retrieval_failed', 'error': result.stderr.strip()}
    try:
        reader = PdfReader(path)
        text = '\n'.join(p.extract_text() for p in reader.pages)
    except Exception as exc:
        return {'mpn': mpn, 'url': url, 'status': 'not_a_readable_pdf', 'error': str(exc)}
    exact = mpn.replace(' ', '').upper() in text.replace(' ', '').replace('\n', '').upper()
    return {'mpn': mpn, 'url': url, 'status': 'exact_part_document' if exact else 'part_not_found',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'text': text}


if __name__ == '__main__':
    CACHE.mkdir(parents=True, exist_ok=True)
    parts = sorted({r['MPN'] for r in csv.DictReader((ROOT / 'engineering/schematic_bom.csv').open())
                    if r['MPN'].startswith(('RC', 'RT', 'C0603C', 'C0805C', 'C1206C'))})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(fetch, parts):
            result.pop('text', None)
            print(json.dumps(result), flush=True)
