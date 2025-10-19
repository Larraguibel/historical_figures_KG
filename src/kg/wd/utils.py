# src/kg/wd/utils.py
from __future__ import annotations
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib, json, time, random

ENDPOINT = "https://query.wikidata.org/sparql"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache_wd"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _cache_path(query: str) -> Path:
    h = hashlib.sha1(query.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.json"

def run_sparql(query: str, use_cache: bool = True, sleep_s: float = 0.12, retries: int = 7):
    p = _cache_path(query)
    if use_cache and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))

    backoff = 0.8
    last_err = None
    for attempt in range(retries):
        try:
            sp = SPARQLWrapper(ENDPOINT, agent="kg-us-es/0.1 (mailto:example@example.com)")
            sp.setReturnFormat(JSON)
            sp.setQuery(query)
            sp.setTimeout(120)  # subimos a 120s
            res = sp.query().convert()
            if sleep_s:
                time.sleep(sleep_s)  # cortesía
            if use_cache:
                p.write_text(json.dumps(res), encoding="utf-8")
            return res
        except Exception as e:
            last_err = e
            # backoff exponencial + jitter
            time.sleep(backoff + random.uniform(0, 0.6))
            backoff = min(backoff * 1.9, 10.0)
    raise last_err

def labels_es(qids: list[str]) -> dict[str, str]:
    """
    Devuelve etiquetas en español (fallback a inglés) para una lista de QIDs.
    """
    if not qids:
        return {}
    # dedup
    qids = list(dict.fromkeys([q for q in qids if q and q.startswith("Q")]))
    values = " ".join(f"wd:{q}" for q in qids)
    q = f"""
    SELECT ?x ?xLabel WHERE {{
      VALUES ?x {{ {values} }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }}
    """
    res = run_sparql(q)
    out = {}
    for b in res["results"]["bindings"]:
        qid = b["x"]["value"].split("/")[-1]
        out[qid] = b.get("xLabel", {}).get("value", qid)
    return out
