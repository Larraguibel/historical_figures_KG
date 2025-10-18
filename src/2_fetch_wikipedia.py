# src/fetch_wikipedia.py
from pathlib import Path
import json
import time
import urllib.parse as ul
import wptools
import csv
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBJECTS_CSV = PROJECT_ROOT / "data" / "subjects.csv"
CACHE_DIR    = PROJECT_ROOT / "data" / "cache_wiki"

def load_subjects():
    with SUBJECTS_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)

def fetch_page(qid: str, es_title: str):
    # decodificar título por si viene con %20 etc.
    title = ul.unquote(es_title)
    page = wptools.page(title=title, lang="es", wikibase=qid, silent=True)
    # get_parse trae infobox + links + basic data (sin cargar imágenes pesadas)
    page.get_parse(show=False)
    # Extraer info relevante
    data = {
        "qid": qid,
        "title": page.data.get("title"),
        "pageid": page.data.get("pageid"),
        "wikibase": page.data.get("wikibase"),
        "modified": page.data.get("modified"),
        "infobox": page.data.get("infobox") or {},
        "links": [ln.get("title") for ln in (page.data.get("links") or []) if ln.get("title")],
        "iwlinks": page.data.get("iwlinks") or [],
        "url": page.data.get("url"),
        "exrest": page.data.get("exrest"),  # resumen
        "extract": page.data.get("extract"), # texto
        "claims": page.data.get("claims") or {},
    }
    return data

def main(rate_sleep=0.2):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    subjects = load_subjects()
    for row in tqdm(subjects, desc="Wikipedia ES"):
        qid = row["qid"]
        out = CACHE_DIR / f"{qid}.json"
        if out.exists():
            continue
        try:
            data = fetch_page(qid, row["eswiki_title"])
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(rate_sleep)
        except Exception as e:
            print(f"[warn] {qid}: {e}")

if __name__ == "__main__":
    main(rate_sleep=0.3)
