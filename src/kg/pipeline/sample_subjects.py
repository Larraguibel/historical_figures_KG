# src/sample_subjects.py
from pathlib import Path
import csv
import yaml
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.error import URLError
from time import time, sleep

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CFG_CLASSES = PROJECT_ROOT / "config" / "classes.yml"
OUT_CSV     = PROJECT_ROOT / "data" / "subjects.csv"

ENDPOINT = "https://query.wikidata.org/sparql"

# Dame las personas con nacionalidad estadounidense, 
# con ocupación X, y que tengan artículo en Wikipedia en español.
SPARQL_TEMPLATE = """
SELECT ?person ?personLabel ?esArticle WHERE {{
  VALUES ?occupation {{ {occupations} }}
  ?person wdt:P31 wd:Q5 ;                # humano
          wdt:P27 wd:Q30 ;               # ciudadanía USA
          wdt:P106 ?occupation .
  ?esArticle schema:about ?person ;
             schema:isPartOf <https://es.wikipedia.org/> .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
LIMIT {limit}
"""

def run_sparql(query: str, sleep_s=0.0):
    sparql = SPARQLWrapper(ENDPOINT, agent="kg-us-es/0.1 (mailto:dlarraguibel@uc.cl)")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    # manejo básico de rate limit
    for attempt in range(5):
        try:
            res = sparql.query().convert()
            if sleep_s > 0:
                sleep(sleep_s)
            return res
        except URLError:
            sleep(2 + attempt)
        except Exception as e:
            if "rate limit" in str(e).lower():
                sleep(2 + attempt)
                continue
            raise

def load_classes():
    with CFG_CLASSES.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)["clases"]

def sample_per_class(limit_per_class=30, sleep_s=0.2):
    clases = load_classes()
    rows = []
    print("\nMuestreando sujetos por clase...")
    print(f"Clases cargadas: {list(clases.keys())}\n")
    for key, meta in clases.items():
        start = time()
        print("- Clase:", key)
        occs = meta.get("ocupaciones", [])
        if not occs:
            continue
        occ_str = " ".join(f"wd:{q}" for q in occs)
        q = SPARQL_TEMPLATE.format(occupations=occ_str, limit=limit_per_class)
        data = run_sparql(q, sleep_s=sleep_s)
        for b in data["results"]["bindings"]:
            qid = b["person"]["value"].split("/")[-1]
            es_url = b["esArticle"]["value"]
            es_title = es_url.split("/")[-1]  # título codificado
            rows.append((qid, es_title, key))
        elapsed = time() - start
        print("  → Encontrados:", len(data["results"]["bindings"]), f"(en {elapsed:.1f}s)")
    return rows

def write_csv(rows):
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["qid", "eswiki_title", "clase"])
        # dedup por qid (si aparece en varias ocupaciones)
        seen = set()
        for qid, title, clase in rows:
            if qid in seen:
                continue
            seen.add(qid)
            w.writerow([qid, title, clase])

if __name__ == "__main__":
    rows = sample_per_class(limit_per_class=50, sleep_s=0.1)
    write_csv(rows)
    print(f"\n✅ Guardado: {OUT_CSV} ({len(rows)} filas antes de eliminar duplicados.)")
