# src/wd_utils.py
from __future__ import annotations
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib, json, time

ENDPOINT = "https://query.wikidata.org/sparql"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache_wd"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _cache_path(query: str) -> Path:
    h = hashlib.sha1(query.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.json"

def run_sparql(query: str, use_cache: bool = True, sleep_s: float = 0.1):
    p = _cache_path(query)
    if use_cache and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    sp = SPARQLWrapper(ENDPOINT, agent="kg-us-es/0.1 (mailto:example@example.com)")
    sp.setReturnFormat(JSON)
    sp.setQuery(query)
    res = sp.query().convert()
    if sleep_s:
        time.sleep(sleep_s)
    if use_cache:
        p.write_text(json.dumps(res), encoding="utf-8")
    return res

def labels_es(qids: list[str]) -> dict[str, str]:
    if not qids:
        return {}
    values = " ".join(f"wd:{q}" for q in qids)
    q = f"""
    SELECT ?x ?xLabel WHERE {{
      VALUES ?x {{ {values} }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }}
    """
    res = run_sparql(q)
    lab = {}
    for b in res["results"]["bindings"]:
        qid = b["x"]["value"].split("/")[-1]
        lab[qid] = b.get("xLabel", {}).get("value", qid)
    return lab
