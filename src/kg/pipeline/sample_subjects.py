# src/kg/pipeline/sample_subjects.py
from __future__ import annotations
from pathlib import Path
import csv
import yaml
import argparse
from time import time, sleep
from urllib.error import URLError
import unicodedata

from SPARQLWrapper import SPARQLWrapper, JSON, POST

# Resolver de país desde el módulo central
from kg.wd.country import resolve_country_id, get_country_from_project

ENDPOINT = "https://query.wikidata.org/sparql"

# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------
def _slugify(s: str) -> str:
    """Quita tildes/diacríticos, minúsculas y reemplaza espacios por guiones."""
    return (
        unicodedata.normalize("NFD", s)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .replace(" ", "-")
    )

def find_project_root(start: Path) -> Path:
    cur = start
    for _ in range(6):
        if (cur / "config" / "classes.yml").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start

HERE = Path(__file__).resolve()
PROJECT_ROOT = find_project_root(HERE.parents[3] if "kg" in str(HERE) else HERE.parents[1])

CFG_CLASSES = PROJECT_ROOT / "config" / "classes.yml"

# --------------------------------------------------------------------------------------
# SPARQL de muestreo por ocupación + ciudadanía (parametrizado por país e idioma wiki)
# --------------------------------------------------------------------------------------
SPARQL_TEMPLATE = """
SELECT ?person ?personLabel ?article WHERE {{
  VALUES ?occupation {{ {occupations} }}
  ?person wdt:P31 wd:Q5 ;          # humano
          wdt:P27 wd:{country_qid} ;
          wdt:P106 ?occupation .
  OPTIONAL {{
    ?article schema:about ?person ;
             schema:isPartOf <https://{wiki_lang}.wikipedia.org/> .
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
LIMIT {limit}
"""

def run_sparql(query: str, sleep_s=0.0):
    sparql = SPARQLWrapper(ENDPOINT, agent="kg-country-agnostic/0.1 (mailto:example@example.com)")
    sparql.setMethod(POST)              # evita URLs largas
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    # manejo básico de rate limit
    for attempt in range(6):
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
        data = yaml.safe_load(f) or {}
    # admite claves "clases" o "classes"
    clases = data.get("clases") or data.get("classes")
    if not clases:
        raise ValueError(f"No se encontraron clases en {CFG_CLASSES}")
    return clases

def sample_per_class(country_qid: str, wiki_lang: str = "es",
                     limit_per_class: int = 30, sleep_s: float = 0.2):
    clases = load_classes()
    rows = []
    print("\nMuestreando sujetos por clase...")
    print(f"País objetivo: {country_qid} | Idioma Wikipedia: {wiki_lang}")
    print(f"Clases cargadas: {list(clases.keys())}\n")

    for key, meta in clases.items():
        start = time()
        print("- Clase:", key)
        occs = meta.get("ocupaciones") or meta.get("occupations") or []
        if not occs:
            print("  (sin ocupaciones definidas)")
            continue

        occ_str = " ".join(f"wd:{q}" for q in occs)
        q = SPARQL_TEMPLATE.format(
            occupations=occ_str,
            country_qid=country_qid,
            wiki_lang=wiki_lang,
            limit=limit_per_class
        )
        data = run_sparql(q, sleep_s=sleep_s)

        n_bind = 0
        for b in data["results"]["bindings"]:
            qid = b["person"]["value"].split("/")[-1]
            art = b.get("article", {}).get("value")
            # si hay artículo en ese idioma, usamos el título; si no, dejamos vacío
            local_title = ""
            if art:
                local_title = art.split("/")[-1]  # título codificado
            rows.append((qid, local_title, key))
            n_bind += 1

        elapsed = time() - start
        print(f"  → Encontrados: {n_bind} (en {elapsed:.1f}s)")
    return rows

def write_csv(rows, out_csv: Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["qid", "wiki_title", "clase"])
        # dedup por qid (si aparece en varias ocupaciones)
        seen = set()
        for qid, title, clase in rows:
            if qid in seen:
                continue
            seen.add(qid)
            w.writerow([qid, title, clase])

def main():
    ap = argparse.ArgumentParser(description="Muestreo de sujetos por clase desde Wikidata.")
    ap.add_argument("--country", help="QID, ISO-2/3 o nombre del país (según config/countries.yml). Ej: Q183, de, germany, alemania.")
    ap.add_argument("--wiki-lang", default="es", help="Idioma del artículo de Wikipedia (default: es).")
    ap.add_argument("--limit-per-class", type=int, default=50, help="Máximo de sujetos por clase (default: 50).")
    ap.add_argument("--sleep", type=float, default=0.12, help="Sleep entre llamadas SPARQL (default: 0.12s).")
    args = ap.parse_args()

    # Resolver país: si pasan --country, se respeta; si no, se toma desde project.yml
    if args.country:
        try:
            country_qid = resolve_country_id(args.country)
        except Exception as e:
            raise SystemExit(f"[error] No fue posible resolver el país '{args.country}': {e}")
        # slug del nombre para el archivo: si es QID, usamos el QID; si es nombre/código, slug del argumento
        country_slug = _slugify(args.country) if not args.country.upper().startswith("Q") else country_qid.lower()
    else:
        # Lee (nombre, QID) desde config/project.yml
        try:
            country_name, country_qid = get_country_from_project()
        except Exception as e:
            raise SystemExit(f"[error] No fue posible leer el país desde config/project.yml: {e}")
        country_slug = _slugify(country_name)

    out_csv = PROJECT_ROOT / "data" / f"subjects_{country_slug}.csv"

    rows = sample_per_class(
        country_qid=country_qid,
        wiki_lang=args.wiki_lang,
        limit_per_class=args.limit_per_class,
        sleep_s=args.sleep
    )
    write_csv(rows, out_csv)
    print(f"\n✅ Guardado: {out_csv} ({len(rows)} filas antes de eliminar duplicados.)")

if __name__ == "__main__":
    main()
